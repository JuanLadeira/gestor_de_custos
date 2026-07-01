import pytest
from httpx import AsyncClient

from app.admin.models import Admin
from app.auth.security import create_access_token, get_password_hash
from app.authz import catalog
from app.authz.service import AuthzService
from app.tenant.models import Tenant


@pytest.mark.authz
async def test_admin_lists_tenant_profiles(client: AsyncClient, session):
    admin = Admin(username="root", email="root@e.com",
                  password=get_password_hash("x"), nome="Root")
    session.add(admin)
    svc = AuthzService(session)
    await svc.seed_global_permissions()
    tenant = Tenant(nome="Casa")
    session.add(tenant)
    await session.flush()
    await svc.seed_tenant_defaults(tenant.id)

    token = create_access_token({"sub": f"admin:{admin.username}"})
    r = await client.get(f"/admin/tenants/{tenant.id}/profiles",
                         headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert {p["nome"] for p in r.json()} == set(catalog.DEFAULT_PROFILES)


@pytest.mark.authz
async def test_admin_profiles_requires_admin(client: AsyncClient):
    assert (await client.get("/admin/tenants/1/profiles")).status_code == 401
