import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz.models import RoleProfile
from app.authz.service import AuthzService
from app.tenant.schemas import TenantCreate
from app.tenant.services import TenantService


@pytest.mark.authz
async def test_tenant_create_seeds_authz(session: AsyncSession):
    await AuthzService(session).seed_global_permissions()
    tenant = await TenantService(session).create(TenantCreate(nome="Nova Casa"))
    profiles = (await session.execute(
        select(RoleProfile).where(RoleProfile.tenant_id == tenant.id)
    )).scalars().all()
    assert "Dono" in {p.nome for p in profiles}
