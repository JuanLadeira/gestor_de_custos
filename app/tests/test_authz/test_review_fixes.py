import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.campanha.models import Campanha, TemplateMensagem
from app.tests.conftest import make_tenant_user


# ── #1: deactivated user is denied access ────────────────────────────────────

@pytest.mark.authz
async def test_deactivated_user_is_denied(client: AsyncClient, session):
    _, user = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    token = create_access_token({"sub": user.username})
    # sanity: works while active
    assert (await client.get("/api/custos-fixos/", headers={"Authorization": f"Bearer {token}"})).status_code == 200
    user.ativo = False
    await session.flush()
    r = await client.get("/api/custos-fixos/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


# ── #2: anti-lockout on PUT /usuarios/{id} (deactivate / reassign last Dono) ──

@pytest.mark.authz
async def test_cannot_deactivate_last_dono(client: AsyncClient, session):
    _, owner = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    h = {"Authorization": f"Bearer {create_access_token({'sub': owner.username})}"}
    r = await client.put(f"/api/usuarios/{owner.id}", headers=h, json={"ativo": False})
    assert r.status_code == 409


# ── #4: cross-tenant template delete returns 404 (not 403) ───────────────────

@pytest.mark.authz
async def test_cross_tenant_template_delete_404(client: AsyncClient, session):
    tenant_a, _ = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    _, user_b = await make_tenant_user(session, tenant_nome="B", username="dono_b")

    campanha = Campanha(tenant_id=tenant_a.id, nome="C-A")
    session.add(campanha)
    await session.flush()
    tmpl = TemplateMensagem(campanha_id=campanha.id, conteudo="oi")
    session.add(tmpl)
    await session.flush()

    token_b = create_access_token({"sub": user_b.username})
    r = await client.delete(f"/api/templates/{tmpl.id}", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 404
