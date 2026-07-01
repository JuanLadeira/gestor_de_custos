import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


@pytest.mark.authz
async def test_owner_full_flow(client: AsyncClient, session):
    tenant, owner = await make_tenant_user(session, tenant_nome="Casa", username="dono")
    h = {"Authorization": f"Bearer {create_access_token({'sub': owner.username})}"}

    me = (await client.get("/api/usuarios/me", headers=h)).json()
    assert me["role_profile"]["nome"] == "Dono"
    assert "custo:create" in me["permissions"]

    perms = (await client.get("/api/authz/permissions", headers=h)).json()
    assert any(p["code"] == "rateio:pay" for p in perms)

    mes = (await client.post("/api/meses/", headers=h, json={"ano": 2026, "mes": 7})).json()
    custo = (await client.post("/api/custos/", headers=h,
             json={"descricao": "Luz", "valor": "90.00",
                   "data_vencimento": "2026-07-10", "mes_referencia_id": mes["id"]})).json()
    rateio = await client.post("/api/rateios/", headers=h,
             json={"porcentagem": "100.00", "custo_id": custo["id"], "usuario_id": owner.id})
    assert rateio.status_code == 201
