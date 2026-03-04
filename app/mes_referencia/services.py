from datetime import date
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.custo.models import Custo, TipoCusto
from app.custo_fixo.models import CustoFixo
from app.database import AsyncDBSession
from app.mes_referencia.models import MesReferencia
from app.mes_referencia.schemas import MesReferenciaCreate, MesReferenciaUpdate


class MesReferenciaService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, tenant_id: int | None = None) -> list[MesReferencia]:
        query = select(MesReferencia).order_by(
            MesReferencia.ano.desc(), MesReferencia.mes.desc()
        )
        if tenant_id:
            query = query.where(MesReferencia.tenant_id == tenant_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, mes_referencia_id: int) -> MesReferencia | None:
        return await self.session.get(MesReferencia, mes_referencia_id)

    async def get_by_tenant_ano_mes(
        self, tenant_id: int, ano: int, mes: int
    ) -> MesReferencia | None:
        result = await self.session.execute(
            select(MesReferencia)
            .where(MesReferencia.tenant_id == tenant_id)
            .where(MesReferencia.ano == ano)
            .where(MesReferencia.mes == mes)
        )
        return result.scalar_one_or_none()

    async def obter_ou_criar_mes_atual(self, tenant_id: int) -> MesReferencia:
        """Get or create the current month reference, importing fixed costs if new."""
        hoje = date.today()
        ano = hoje.year
        mes = hoje.month

        mes_ref = await self.get_by_tenant_ano_mes(tenant_id, ano, mes)
        if mes_ref:
            return mes_ref

        # Create new month
        mes_ref = MesReferencia(tenant_id=tenant_id, ano=ano, mes=mes)
        self.session.add(mes_ref)
        await self.session.flush()
        await self.session.refresh(mes_ref)

        # Import fixed costs
        await self.importar_custos_fixos_para_mes(mes_ref.id, tenant_id)

        return mes_ref

    async def importar_custos_fixos_para_mes(
        self, mes_referencia_id: int, tenant_id: int
    ) -> list[Custo]:
        """Import active fixed costs as actual costs for the month."""
        # Get active fixed costs for tenant
        result = await self.session.execute(
            select(CustoFixo)
            .where(CustoFixo.tenant_id == tenant_id)
            .where(CustoFixo.ativo == True)  # noqa: E712
        )
        custos_fixos = result.scalars().all()

        mes_ref = await self.get_by_id(mes_referencia_id)
        if not mes_ref:
            return []

        custos_criados = []
        for custo_fixo in custos_fixos:
            # Calculate due date for this month
            try:
                data_vencimento = date(mes_ref.ano, mes_ref.mes, custo_fixo.dia_vencimento)
            except ValueError:
                # Handle months with fewer days (e.g., Feb 30 -> Feb 28)
                import calendar

                ultimo_dia = calendar.monthrange(mes_ref.ano, mes_ref.mes)[1]
                data_vencimento = date(
                    mes_ref.ano, mes_ref.mes, min(custo_fixo.dia_vencimento, ultimo_dia)
                )

            custo = Custo(
                descricao=custo_fixo.descricao,
                valor=custo_fixo.valor,
                data_vencimento=data_vencimento,
                tipo=TipoCusto.FIXO,
                mes_referencia_id=mes_referencia_id,
                custo_fixo_origem_id=custo_fixo.id,
            )
            self.session.add(custo)
            custos_criados.append(custo)

        await self.session.flush()
        return custos_criados

    async def create(self, data: MesReferenciaCreate) -> MesReferencia:
        mes_ref = MesReferencia(
            ano=data.ano,
            mes=data.mes,
            tenant_id=data.tenant_id,
        )
        self.session.add(mes_ref)
        await self.session.flush()
        await self.session.refresh(mes_ref)
        return mes_ref

    async def update(
        self, mes_referencia_id: int, data: MesReferenciaUpdate
    ) -> MesReferencia | None:
        mes_ref = await self.get_by_id(mes_referencia_id)
        if not mes_ref:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(mes_ref, key, value)

        await self.session.flush()
        await self.session.refresh(mes_ref)
        return mes_ref

    async def delete(self, mes_referencia_id: int) -> bool:
        mes_ref = await self.get_by_id(mes_referencia_id)
        if not mes_ref:
            return False

        await self.session.delete(mes_ref)
        return True


def get_mes_referencia_service(session: AsyncDBSession) -> MesReferenciaService:
    return MesReferenciaService(session)


MesReferenciaServiceDep = Annotated[
    MesReferenciaService, Depends(get_mes_referencia_service)
]
