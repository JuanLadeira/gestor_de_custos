import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


@pytest.mark.authz
async def test_custos_fixos_requires_auth(client: AsyncClient):
    assert (await client.get("/api/custos-fixos/")).status_code == 401


@pytest.mark.authz
async def test_create_and_scope(client: AsyncClient, session):
    tenant_a, user_a = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    _, user_b = await make_tenant_user(session, tenant_nome="B", username="dono_b")
    token_a = create_access_token({"sub": user_a.username})
    token_b = create_access_token({"sub": user_b.username})
    created = await client.post("/api/custos-fixos/", headers={"Authorization": f"Bearer {token_a}"},
                               json={"descricao": "Aluguel", "valor": "1000.00", "dia_vencimento": 5})
    assert created.status_code == 201
    assert created.json()["tenant_id"] == tenant_a.id
    cf_id = created.json()["id"]
    # B cannot see A's custo fixo
    r = await client.get(f"/api/custos-fixos/{cf_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 404
