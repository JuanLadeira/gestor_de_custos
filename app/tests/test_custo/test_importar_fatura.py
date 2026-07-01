from decimal import Decimal

import pytest
from sqlalchemy import select

from app.custo.models import Custo, TipoCusto
from app.custo.services import CustoService
from app.mes_referencia.services import MesReferenciaService
from app.tests.conftest import make_tenant_user

CSV = (
    b"date,title,amount\n"
    b'2026-07-01,Uber,"4,28"\n'
    b'2026-06-28,Mercado,"10,00"\n'
    b'2026-06-24,Estorno,"- 21,80"\n'
)


def _svc(session):
    return CustoService(session, MesReferenciaService(session))


@pytest.mark.authz
async def test_importa_um_custo_por_compra_no_mes_da_data(session):
    tenant, _ = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    res = await _svc(session).importar_fatura(CSV, tenant.id)
    assert res.criados == 3
    assert res.ignorados == 0
    assert res.meses_afetados == 2  # junho e julho
    custos = (await session.execute(select(Custo))).scalars().all()
    assert all(c.tipo == TipoCusto.CARTAO_CREDITO for c in custos)


@pytest.mark.authz
async def test_estorno_vira_custo_negativo(session):
    tenant, _ = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    await _svc(session).importar_fatura(CSV, tenant.id)
    estorno = (await session.execute(
        select(Custo).where(Custo.descricao == "Estorno")
    )).scalar_one()
    assert estorno.valor == Decimal("-21.80")


@pytest.mark.authz
async def test_reimport_nao_duplica(session):
    tenant, _ = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    await _svc(session).importar_fatura(CSV, tenant.id)
    res2 = await _svc(session).importar_fatura(CSV, tenant.id)
    assert res2.criados == 0
    assert res2.ignorados == 3
    total = (await session.execute(select(Custo))).scalars().all()
    assert len(total) == 3
