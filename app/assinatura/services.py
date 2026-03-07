from datetime import datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.assinatura.models import Assinatura, AssinaturaStatus
from app.assinatura.schemas import AssinaturaUpdate
from app.database import AsyncDBSession


class AssinaturaService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Assinatura]:
        result = await self.session.execute(select(Assinatura).order_by(Assinatura.id))
        return list(result.scalars().all())

    async def get_all_admin(self) -> list[Assinatura]:
        result = await self.session.execute(
            select(Assinatura)
            .options(selectinload(Assinatura.tenant), selectinload(Assinatura.plano))
            .order_by(Assinatura.id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, assinatura_id: int) -> Assinatura | None:
        return await self.session.get(Assinatura, assinatura_id)

    async def get_by_tenant(self, tenant_id: int) -> Assinatura | None:
        result = await self.session.execute(
            select(Assinatura).where(Assinatura.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def get_by_stripe_subscription_id(
        self, stripe_subscription_id: str
    ) -> Assinatura | None:
        result = await self.session.execute(
            select(Assinatura).where(
                Assinatura.stripe_subscription_id == stripe_subscription_id
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        tenant_id: int,
        plano_id: int,
        stripe_subscription_id: str | None = None,
        stripe_customer_id: str | None = None,
        data_inicio: datetime | None = None,
        data_proxima_cobranca: datetime | None = None,
        status: AssinaturaStatus = AssinaturaStatus.ATIVA,
    ) -> Assinatura:
        assinatura = Assinatura(
            tenant_id=tenant_id,
            plano_id=plano_id,
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id,
            data_inicio=data_inicio,
            data_proxima_cobranca=data_proxima_cobranca,
            status=status,
        )
        self.session.add(assinatura)
        await self.session.flush()
        await self.session.refresh(assinatura)
        return assinatura

    async def update(
        self, assinatura_id: int, data: AssinaturaUpdate
    ) -> Assinatura | None:
        assinatura = await self.get_by_id(assinatura_id)
        if not assinatura:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(assinatura, key, value)
        await self.session.flush()
        await self.session.refresh(assinatura)
        return assinatura


def get_assinatura_service(session: AsyncDBSession) -> AssinaturaService:
    return AssinaturaService(session)


AssinaturaServiceDep = Annotated[AssinaturaService, Depends(get_assinatura_service)]
