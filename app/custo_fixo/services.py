from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.custo_fixo.models import CustoFixo
from app.custo_fixo.schemas import CustoFixoCreate, CustoFixoUpdate
from app.database import AsyncDBSession


class CustoFixoService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, tenant_id: int | None = None) -> list[CustoFixo]:
        query = select(CustoFixo).order_by(CustoFixo.id)
        if tenant_id:
            query = query.where(CustoFixo.tenant_id == tenant_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_ativos_by_tenant(self, tenant_id: int) -> list[CustoFixo]:
        result = await self.session.execute(
            select(CustoFixo)
            .where(CustoFixo.tenant_id == tenant_id)
            .where(CustoFixo.ativo == True)  # noqa: E712
            .order_by(CustoFixo.id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, custo_fixo_id: int) -> CustoFixo | None:
        return await self.session.get(CustoFixo, custo_fixo_id)

    async def get_scoped(self, custo_fixo_id: int, tenant_id: int) -> CustoFixo | None:
        cf = await self.session.get(CustoFixo, custo_fixo_id)
        if cf is None or cf.tenant_id != tenant_id:
            return None
        return cf

    async def create(self, data: CustoFixoCreate, tenant_id: int) -> CustoFixo:
        custo_fixo = CustoFixo(
            descricao=data.descricao,
            valor=data.valor,
            dia_vencimento=data.dia_vencimento,
            tenant_id=tenant_id,
        )
        self.session.add(custo_fixo)
        await self.session.flush()
        await self.session.refresh(custo_fixo)
        return custo_fixo

    async def update(
        self, custo_fixo: CustoFixo, data: CustoFixoUpdate
    ) -> CustoFixo:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(custo_fixo, key, value)

        await self.session.flush()
        await self.session.refresh(custo_fixo)
        return custo_fixo

    async def delete(self, custo_fixo: CustoFixo) -> None:
        await self.session.delete(custo_fixo)


def get_custo_fixo_service(session: AsyncDBSession) -> CustoFixoService:
    return CustoFixoService(session)


CustoFixoServiceDep = Annotated[CustoFixoService, Depends(get_custo_fixo_service)]
