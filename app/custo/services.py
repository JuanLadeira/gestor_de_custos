from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.custo.models import Custo
from app.custo.schemas import CustoCreate, CustoUpdate
from app.database import AsyncDBSession


class CustoService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, mes_referencia_id: int | None = None) -> list[Custo]:
        query = select(Custo).order_by(Custo.data_vencimento)
        if mes_referencia_id:
            query = query.where(Custo.mes_referencia_id == mes_referencia_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, custo_id: int) -> Custo | None:
        return await self.session.get(Custo, custo_id)

    async def create(self, data: CustoCreate) -> Custo:
        custo = Custo(
            descricao=data.descricao,
            valor=data.valor,
            data_vencimento=data.data_vencimento,
            tipo=data.tipo,
            mes_referencia_id=data.mes_referencia_id,
            custo_fixo_origem_id=data.custo_fixo_origem_id,
        )
        self.session.add(custo)
        await self.session.flush()
        await self.session.refresh(custo)
        return custo

    async def update(self, custo_id: int, data: CustoUpdate) -> Custo | None:
        custo = await self.get_by_id(custo_id)
        if not custo:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(custo, key, value)

        await self.session.flush()
        await self.session.refresh(custo)
        return custo

    async def delete(self, custo_id: int) -> bool:
        custo = await self.get_by_id(custo_id)
        if not custo:
            return False

        await self.session.delete(custo)
        return True


def get_custo_service(session: AsyncDBSession) -> CustoService:
    return CustoService(session)


CustoServiceDep = Annotated[CustoService, Depends(get_custo_service)]
