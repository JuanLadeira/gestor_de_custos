import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz import catalog
from app.authz.models import RoleProfile
from app.authz.service import AuthzService
from app.tenant.models import Tenant


@pytest.mark.authz
async def test_seed_tenant_defaults_creates_profiles(session: AsyncSession):
    svc = AuthzService(session)
    await svc.seed_global_permissions()
    tenant = Tenant(nome="T")
    session.add(tenant)
    await session.flush()

    dono = await svc.seed_tenant_defaults(tenant.id)
    assert dono.nome == "Dono"
    assert dono.is_protected is True

    profiles = (await session.execute(
        select(RoleProfile).where(RoleProfile.tenant_id == tenant.id)
    )).scalars().all()
    assert {p.nome for p in profiles} == set(catalog.DEFAULT_PROFILES)


@pytest.mark.authz
async def test_seed_tenant_defaults_idempotent(session: AsyncSession):
    svc = AuthzService(session)
    await svc.seed_global_permissions()
    tenant = Tenant(nome="T")
    session.add(tenant)
    await session.flush()
    await svc.seed_tenant_defaults(tenant.id)
    await svc.seed_tenant_defaults(tenant.id)  # twice
    profiles = (await session.execute(
        select(RoleProfile).where(RoleProfile.tenant_id == tenant.id)
    )).scalars().all()
    assert len(profiles) == len(catalog.DEFAULT_PROFILES)


@pytest.mark.authz
@pytest.mark.xfail(reason="needs role_profile_id (Task 6)", strict=False)
async def test_seeded_dono_resolves_all_permissions(session: AsyncSession):
    from app.usuario.models import Usuario
    svc = AuthzService(session)
    await svc.seed_global_permissions()
    tenant = Tenant(nome="T")
    session.add(tenant)
    await session.flush()
    dono = await svc.seed_tenant_defaults(tenant.id)
    user = Usuario(username="o", email="o@e.com", password="x", nome="O",
                   tenant_id=tenant.id, role_profile_id=dono.id)
    session.add(user)
    await session.flush()
    perms = await svc.resolve_permissions(user)
    assert perms == set(catalog.all_codes())
