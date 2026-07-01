import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


async def _make_mes(client, token):
    r = await client.post("/api/meses/", headers={"Authorization": f"Bearer {token}"},
                          json={"ano": 2026, "mes": 7})
    return r.json()["id"]


@pytest.mark.authz
async def test_custos_requires_auth(client: AsyncClient):
    assert (await client.get("/api/custos/")).status_code == 401


@pytest.mark.authz
async def test_create_custo_in_own_mes(client: AsyncClient, session):
    _, user_a = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    token = create_access_token({"sub": user_a.username})
    mes_id = await _make_mes(client, token)
    r = await client.post("/api/custos/", headers={"Authorization": f"Bearer {token}"},
                          json={"descricao": "Luz", "valor": "100.00",
                                "data_vencimento": "2026-07-10", "mes_referencia_id": mes_id})
    assert r.status_code == 201


@pytest.mark.authz
async def test_cannot_create_custo_in_other_tenant_mes(client: AsyncClient, session):
    _, user_a = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    _, user_b = await make_tenant_user(session, tenant_nome="B", username="dono_b")
    token_a = create_access_token({"sub": user_a.username})
    token_b = create_access_token({"sub": user_b.username})
    mes_a = await _make_mes(client, token_a)
    # B tries to attach a custo to A's mes
    r = await client.post("/api/custos/", headers={"Authorization": f"Bearer {token_b}"},
                          json={"descricao": "X", "valor": "1.00",
                                "data_vencimento": "2026-07-10", "mes_referencia_id": mes_a})
    assert r.status_code == 404
