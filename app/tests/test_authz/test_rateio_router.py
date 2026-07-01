import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


async def _mes_and_custo(client, token):
    mes = (await client.post("/api/meses/", headers={"Authorization": f"Bearer {token}"},
                             json={"ano": 2026, "mes": 7})).json()
    custo = (await client.post("/api/custos/", headers={"Authorization": f"Bearer {token}"},
                               json={"descricao": "Luz", "valor": "100.00",
                                     "data_vencimento": "2026-07-10",
                                     "mes_referencia_id": mes["id"]})).json()
    return custo["id"]


@pytest.mark.authz
async def test_rateios_requires_auth(client: AsyncClient):
    assert (await client.get("/api/rateios/", params={"custo_id": 1})).status_code == 401


@pytest.mark.authz
async def test_create_rateio_own_tenant(client: AsyncClient, session):
    _, user_a = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    token = create_access_token({"sub": user_a.username})
    custo_id = await _mes_and_custo(client, token)
    r = await client.post("/api/rateios/", headers={"Authorization": f"Bearer {token}"},
                          json={"porcentagem": "50.00", "custo_id": custo_id, "usuario_id": user_a.id})
    assert r.status_code == 201


@pytest.mark.authz
async def test_cannot_rateio_other_tenant_custo(client: AsyncClient, session):
    _, user_a = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    _, user_b = await make_tenant_user(session, tenant_nome="B", username="dono_b")
    token_a = create_access_token({"sub": user_a.username})
    token_b = create_access_token({"sub": user_b.username})
    custo_a = await _mes_and_custo(client, token_a)
    r = await client.post("/api/rateios/", headers={"Authorization": f"Bearer {token_b}"},
                          json={"porcentagem": "50.00", "custo_id": custo_a, "usuario_id": user_b.id})
    assert r.status_code == 404
