import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz.models import Permission, Role, RoleProfile
from app.authz.service import AuthzService
from app.tenant.models import Tenant
from app.usuario.models import Usuario


@pytest.mark.authz
async def test_seed_global_permissions_idempotent(session: AsyncSession):
    svc = AuthzService(session)
    await svc.seed_global_permissions()
    await svc.seed_global_permissions()  # twice
    rows = (await session.execute(select(Permission))).scalars().all()
    codes = [r.code for r in rows]
    assert len(codes) == len(set(codes))
    assert "custo:create" in codes


@pytest.mark.xfail(reason="needs role_profile_id (Task 6)", strict=False)
@pytest.mark.authz
async def test_resolve_permissions_union(session: AsyncSession):
    svc = AuthzService(session)
    await svc.seed_global_permissions()

    tenant = Tenant(nome="T")
    session.add(tenant)
    await session.flush()

    p_read = (await session.execute(select(Permission).where(Permission.code == "custo:read"))).scalar_one()
    p_pay = (await session.execute(select(Permission).where(Permission.code == "rateio:pay"))).scalar_one()

    r1 = Role(tenant_id=tenant.id, nome="A")
    r1.permissions.append(p_read)
    r2 = Role(tenant_id=tenant.id, nome="B")
    r2.permissions.append(p_pay)
    session.add_all([r1, r2])
    await session.flush()

    profile = RoleProfile(tenant_id=tenant.id, nome="P")
    profile.roles.extend([r1, r2])
    session.add(profile)
    await session.flush()

    user = Usuario(username="u", email="u@e.com", password="x", nome="U",
                   tenant_id=tenant.id, role_profile_id=profile.id)
    session.add(user)
    await session.flush()

    perms = await svc.resolve_permissions(user)
    assert perms == {"custo:read", "rateio:pay"}
