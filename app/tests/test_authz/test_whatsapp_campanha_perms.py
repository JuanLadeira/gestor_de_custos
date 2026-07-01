import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


@pytest.mark.authz
async def test_leitor_cannot_create_campanha(client: AsyncClient, session):
    _, leitor = await make_tenant_user(session, tenant_nome="A", username="leitor_a", profile_nome="Leitor")
    token = create_access_token({"sub": leitor.username})
    r = await client.post("/api/campanhas", headers={"Authorization": f"Bearer {token}"},
                          json={"nome": "C"})
    assert r.status_code == 403


@pytest.mark.authz
async def test_leitor_can_read_campanhas(client: AsyncClient, session):
    _, leitor = await make_tenant_user(session, tenant_nome="A", username="leitor_a", profile_nome="Leitor")
    token = create_access_token({"sub": leitor.username})
    r = await client.get("/api/campanhas", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
