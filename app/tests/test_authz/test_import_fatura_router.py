import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user

CSV = b'date,title,amount\n2026-07-01,Uber,"4,28"\n2026-06-28,Mercado,"10,00"\n'


@pytest.mark.authz
async def test_import_requer_auth(client: AsyncClient):
    r = await client.post("/api/custos/importar", files={"file": ("f.csv", CSV, "text/csv")})
    assert r.status_code == 401


@pytest.mark.authz
async def test_import_happy_path(client: AsyncClient, session):
    _, dono = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    token = create_access_token({"sub": dono.username})
    r = await client.post(
        "/api/custos/importar",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("fatura.csv", CSV, "text/csv")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["criados"] == 2
    assert body["ignorados"] == 0
    assert body["meses_afetados"] == 2


@pytest.mark.authz
async def test_import_csv_invalido_422(client: AsyncClient, session):
    _, dono = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    token = create_access_token({"sub": dono.username})
    r = await client.post(
        "/api/custos/importar",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("x.csv", b"col1,col2\n1,2\n", "text/csv")},
    )
    assert r.status_code == 422


@pytest.mark.authz
async def test_import_sem_permissao_403(client: AsyncClient, session):
    _, leitor = await make_tenant_user(
        session, tenant_nome="B", username="leitor_b", profile_nome="Leitor"
    )
    token = create_access_token({"sub": leitor.username})
    r = await client.post(
        "/api/custos/importar",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("fatura.csv", CSV, "text/csv")},
    )
    assert r.status_code == 403
