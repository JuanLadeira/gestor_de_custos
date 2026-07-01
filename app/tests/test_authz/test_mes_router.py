import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


@pytest.mark.authz
async def test_meses_requires_auth(client: AsyncClient):
    r = await client.get("/api/meses/")
    assert r.status_code == 401


@pytest.mark.authz
async def test_create_mes_scoped_to_jwt_tenant(client: AsyncClient, session):
    tenant_a, user_a = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    token = create_access_token({"sub": user_a.username})
    r = await client.post("/api/meses/", headers={"Authorization": f"Bearer {token}"},
                          json={"ano": 2026, "mes": 7})
    assert r.status_code == 201
    assert r.json()["tenant_id"] == tenant_a.id


@pytest.mark.authz
async def test_cannot_read_other_tenant_mes(client: AsyncClient, session):
    tenant_a, user_a = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    _, user_b = await make_tenant_user(session, tenant_nome="B", username="dono_b")
    token_a = create_access_token({"sub": user_a.username})
    token_b = create_access_token({"sub": user_b.username})
    created = await client.post("/api/meses/", headers={"Authorization": f"Bearer {token_a}"},
                               json={"ano": 2026, "mes": 7})
    mes_id = created.json()["id"]
    r = await client.get(f"/api/meses/{mes_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 404
