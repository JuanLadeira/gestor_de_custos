import os
import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import Depends, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.custo.models import Custo, StatusPagamento
from app.database import AsyncDBSession
from app.pagamento_rateio.models import PagamentoRateio, StatusRateio
from app.pagamento_rateio.schemas import PagamentoRateioCreate, PagamentoRateioUpdate

UPLOAD_DIR = "/app/uploads/comprovantes"


class PagamentoRateioService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self, custo_id: int | None = None, usuario_id: int | None = None
    ) -> list[PagamentoRateio]:
        query = select(PagamentoRateio).order_by(PagamentoRateio.id)
        if custo_id:
            query = query.where(PagamentoRateio.custo_id == custo_id)
        if usuario_id:
            query = query.where(PagamentoRateio.usuario_id == usuario_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, pagamento_id: int) -> PagamentoRateio | None:
        return await self.session.get(PagamentoRateio, pagamento_id)

    async def get_scoped(self, pagamento_id: int, tenant_id: int) -> PagamentoRateio | None:
        from app.mes_referencia.models import MesReferencia

        result = await self.session.execute(
            select(PagamentoRateio)
            .join(Custo, Custo.id == PagamentoRateio.custo_id)
            .join(MesReferencia, MesReferencia.id == Custo.mes_referencia_id)
            .where(PagamentoRateio.id == pagamento_id, MesReferencia.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def custo_in_tenant(self, custo_id: int, tenant_id: int) -> bool:
        from app.mes_referencia.models import MesReferencia

        result = await self.session.execute(
            select(Custo.id)
            .join(MesReferencia, MesReferencia.id == Custo.mes_referencia_id)
            .where(Custo.id == custo_id, MesReferencia.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none() is not None

    async def usuario_in_tenant(self, usuario_id: int, tenant_id: int) -> bool:
        from app.usuario.models import Usuario

        result = await self.session.execute(
            select(Usuario.id).where(Usuario.id == usuario_id, Usuario.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none() is not None

    async def get_soma_porcentagem_custo(
        self, custo_id: int, excluir_id: int | None = None
    ) -> Decimal:
        """Get the sum of percentages already assigned to a cost."""
        query = select(func.coalesce(func.sum(PagamentoRateio.porcentagem), 0)).where(
            PagamentoRateio.custo_id == custo_id
        )
        if excluir_id:
            query = query.where(PagamentoRateio.id != excluir_id)
        result = await self.session.execute(query)
        return Decimal(str(result.scalar_one()))

    async def validar_porcentagem(
        self,
        custo_id: int,
        nova_porcentagem: Decimal,
        excluir_id: int | None = None,
    ) -> None:
        """Validate that total percentage doesn't exceed 100%."""
        soma_atual = await self.get_soma_porcentagem_custo(custo_id, excluir_id)
        total = soma_atual + nova_porcentagem

        if total > 100:
            raise HTTPException(
                status_code=400,
                detail=f"Soma das porcentagens excede 100%. "
                f"Atual: {soma_atual}%, Tentando adicionar: {nova_porcentagem}%, "
                f"Total seria: {total}%",
            )

    async def calcular_valor(self, custo_id: int, porcentagem: Decimal) -> Decimal:
        """Calculate the value based on cost total and percentage."""
        custo = await self.session.get(Custo, custo_id)
        if not custo:
            raise HTTPException(status_code=404, detail="Custo nao encontrado")
        return (custo.valor * porcentagem) / 100

    async def create(self, data: PagamentoRateioCreate) -> PagamentoRateio:
        # Validate percentage
        await self.validar_porcentagem(data.custo_id, data.porcentagem)

        # Calculate value
        valor_calculado = await self.calcular_valor(data.custo_id, data.porcentagem)

        pagamento = PagamentoRateio(
            porcentagem=data.porcentagem,
            valor_calculado=valor_calculado,
            custo_id=data.custo_id,
            usuario_id=data.usuario_id,
        )
        self.session.add(pagamento)
        await self.session.flush()
        await self.session.refresh(pagamento)
        return pagamento

    async def update(
        self, pagamento: PagamentoRateio, data: PagamentoRateioUpdate
    ) -> PagamentoRateio:
        update_data = data.model_dump(exclude_unset=True)

        # If percentage is being updated, validate and recalculate
        if "porcentagem" in update_data:
            nova_porcentagem = update_data["porcentagem"]
            await self.validar_porcentagem(
                pagamento.custo_id, nova_porcentagem, excluir_id=pagamento.id
            )
            update_data["valor_calculado"] = await self.calcular_valor(
                pagamento.custo_id, nova_porcentagem
            )

        for key, value in update_data.items():
            setattr(pagamento, key, value)

        await self.session.flush()
        await self.session.refresh(pagamento)
        return pagamento

    async def recalcular_status_custo(self, custo_id: int) -> None:
        rateios = await self.get_all(custo_id=custo_id)
        if not rateios:
            return
        pagos = [r for r in rateios if r.status == StatusRateio.PAGO]
        custo = await self.session.get(Custo, custo_id)
        if custo is None:
            return
        if len(pagos) == len(rateios):
            custo.status = StatusPagamento.PAGO
        elif pagos:
            custo.status = StatusPagamento.PARCIALMENTE_PAGO
        else:
            custo.status = StatusPagamento.PENDENTE

    async def salvar_comprovante(self, pagamento: PagamentoRateio, file: UploadFile) -> PagamentoRateio:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(file.filename or "")[1] or ".bin"
        filename = f"{uuid.uuid4()}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        contents = await file.read()
        with open(filepath, "wb") as f:
            f.write(contents)

        pagamento.comprovante_url = f"/uploads/comprovantes/{filename}"
        await self.session.flush()
        await self.session.refresh(pagamento)
        return pagamento

    async def delete(self, pagamento: PagamentoRateio) -> None:
        await self.session.delete(pagamento)


def get_pagamento_rateio_service(session: AsyncDBSession) -> PagamentoRateioService:
    return PagamentoRateioService(session)


PagamentoRateioServiceDep = Annotated[
    PagamentoRateioService, Depends(get_pagamento_rateio_service)
]
