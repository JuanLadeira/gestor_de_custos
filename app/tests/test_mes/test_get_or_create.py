import pytest

from app.mes_referencia.services import MesReferenciaService
from app.tests.conftest import make_tenant_user


@pytest.mark.authz
async def test_get_or_create_idempotente(session):
    tenant, _ = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    svc = MesReferenciaService(session)
    m1 = await svc.get_or_create(tenant.id, 2026, 5)
    m2 = await svc.get_or_create(tenant.id, 2026, 5)
    assert m1.id == m2.id
    assert (m1.ano, m1.mes) == (2026, 5)
