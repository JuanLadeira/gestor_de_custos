import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


@pytest.mark.authz
async def test_owner_creates_custom_role(client: AsyncClient, session):
    _, owner = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    token = create_access_token({"sub": owner.username})
    h = {"Authorization": f"Bearer {token}"}
    r = await client.post("/api/authz/roles", headers=h,
                          json={"nome": "Caixa", "permission_codes": ["custo:read", "rateio:pay"]})
    assert r.status_code == 201
    assert set(r.json()["permission_codes"]) == {"custo:read", "rateio:pay"}


@pytest.mark.authz
async def test_cannot_delete_system_role(client: AsyncClient, session):
    _, owner = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    token = create_access_token({"sub": owner.username})
    h = {"Authorization": f"Bearer {token}"}
    roles = (await client.get("/api/authz/roles", headers=h)).json()
    fin = next(r for r in roles if r["nome"] == "Financeiro")
    r = await client.delete(f"/api/authz/roles/{fin['id']}", headers=h)
    assert r.status_code == 409


@pytest.mark.authz
async def test_leitor_cannot_manage_roles(client: AsyncClient, session):
    _, leitor = await make_tenant_user(session, tenant_nome="A", username="leitor", profile_nome="Leitor")
    token = create_access_token({"sub": leitor.username})
    r = await client.post("/api/authz/roles", headers={"Authorization": f"Bearer {token}"},
                          json={"nome": "X", "permission_codes": []})
    assert r.status_code == 403
