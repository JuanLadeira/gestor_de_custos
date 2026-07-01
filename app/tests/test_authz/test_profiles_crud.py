import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token, get_password_hash
from app.authz.service import AuthzService
from app.tests.conftest import make_tenant_user
from app.usuario.models import Usuario


@pytest.mark.authz
async def test_cannot_edit_dono_profile(client: AsyncClient, session):
    _, owner = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    h = {"Authorization": f"Bearer {create_access_token({'sub': owner.username})}"}
    profiles = (await client.get("/api/authz/profiles", headers=h)).json()
    dono = next(p for p in profiles if p["nome"] == "Dono")
    r = await client.put(f"/api/authz/profiles/{dono['id']}", headers=h, json={"nome": "Hack"})
    assert r.status_code == 409


@pytest.mark.authz
async def test_create_and_assign_profile(client: AsyncClient, session):
    tenant, owner = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    svc = AuthzService(session)
    membro = await svc.get_profile_by_nome(tenant.id, "Membro")
    u = Usuario(username="m1", email="m1@e.com", password=get_password_hash("x"), nome="M1",
                tenant_id=tenant.id, role_profile_id=membro.id)
    session.add(u)
    await session.flush()

    h = {"Authorization": f"Bearer {create_access_token({'sub': owner.username})}"}
    roles = (await client.get("/api/authz/roles", headers=h)).json()
    leitura = next(r for r in roles if r["nome"] == "Leitura")
    created = await client.post("/api/authz/profiles", headers=h,
                                json={"nome": "Especial", "role_ids": [leitura["id"]]})
    assert created.status_code == 201
    pid = created.json()["id"]
    r = await client.put(f"/api/authz/usuarios/{u.id}/profile", headers=h,
                         json={"role_profile_id": pid})
    assert r.status_code == 200
    assert r.json()["role_profile_id"] == pid


@pytest.mark.authz
async def test_cannot_remove_last_dono(client: AsyncClient, session):
    tenant, owner = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    svc = AuthzService(session)
    leitor = await svc.get_profile_by_nome(tenant.id, "Leitor")
    h = {"Authorization": f"Bearer {create_access_token({'sub': owner.username})}"}
    # owner is the only Dono; reassigning them away must fail
    r = await client.put(f"/api/authz/usuarios/{owner.id}/profile", headers=h,
                         json={"role_profile_id": leitor.id})
    assert r.status_code == 409
