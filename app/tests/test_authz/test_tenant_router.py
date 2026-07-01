import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


@pytest.mark.authz
async def test_get_my_tenant(client: AsyncClient, session):
    tenant_a, user_a = await make_tenant_user(session, tenant_nome="Casa A", username="dono_a")
    token = create_access_token({"sub": user_a.username})
    r = await client.get("/api/tenants/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["id"] == tenant_a.id


@pytest.mark.authz
async def test_public_tenant_create_removed(client: AsyncClient):
    # The old open POST /api/tenants/ must no longer create tenants unauthenticated.
    r = await client.post("/api/tenants/", json={"nome": "Hacker"})
    assert r.status_code in (401, 403, 404, 405)
