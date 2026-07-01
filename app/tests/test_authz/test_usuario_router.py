import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


@pytest.mark.authz
async def test_list_usuarios_requires_auth(client: AsyncClient):
    r = await client.get("/api/usuarios/")
    assert r.status_code == 401


@pytest.mark.authz
async def test_me_returns_permissions(client: AsyncClient, session):
    _, user = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    token = create_access_token({"sub": user.username})
    r = await client.get("/api/usuarios/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert "custo:create" in body["permissions"]
    assert body["role_profile"]["nome"] == "Dono"


@pytest.mark.authz
async def test_list_usuarios_scoped_to_tenant(client: AsyncClient, session):
    _, user_a = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    await make_tenant_user(session, tenant_nome="B", username="dono_b")
    token = create_access_token({"sub": user_a.username})
    r = await client.get("/api/usuarios/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    usernames = {u["username"] for u in r.json()}
    assert usernames == {"dono_a"}  # never sees tenant B


@pytest.mark.authz
async def test_create_usuario_forbidden_for_leitor(client: AsyncClient, session):
    _, leitor = await make_tenant_user(session, tenant_nome="A", username="leitor_a",
                                       profile_nome="Leitor")
    token = create_access_token({"sub": leitor.username})
    r = await client.post("/api/usuarios/", headers={"Authorization": f"Bearer {token}"},
                          json={"username": "x", "email": "x@e.com", "nome": "X", "password": "p"})
    assert r.status_code == 403
