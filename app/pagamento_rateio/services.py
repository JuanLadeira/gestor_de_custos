from decimal import Decimal
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.custo.models import Custo
from app.database import AsyncDBSession
from app.pagamento_rateio.models import PagamentoRateio
from app.pagamento_rateio.schemas import PagamentoRateioCreate, PagamentoRateioUpdate


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
        self, pagamento_id: int, data: PagamentoRateioUpdate
    ) -> PagamentoRateio | None:
        pagamento = await self.get_by_id(pagamento_id)
        if not pagamento:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # If percentage is being updated, validate and recalculate
        if "porcentagem" in update_data:
            nova_porcentagem = update_data["porcentagem"]
            await self.validar_porcentagem(
                pagamento.custo_id, nova_porcentagem, excluir_id=pagamento_id
            )
            update_data["valor_calculado"] = await self.calcular_valor(
                pagamento.custo_id, nova_porcentagem
            )

        for key, value in update_data.items():
            setattr(pagamento, key, value)

        await self.session.flush()
        await self.session.refresh(pagamento)
        return pagamento

    async def delete(self, pagamento_id: int) -> bool:
        pagamento = await self.get_by_id(pagamento_id)
        if not pagamento:
            return False

        await self.session.delete(pagamento)
        return True


def get_pagamento_rateio_service(session: AsyncDBSession) -> PagamentoRateioService:
    return PagamentoRateioService(session)


PagamentoRateioServiceDep = Annotated[
    PagamentoRateioService, Depends(get_pagamento_rateio_service)
]
