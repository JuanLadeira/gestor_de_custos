from datetime import date, datetime
from decimal import Decimal

from app.custo.models import TipoCusto
from app.custo.schemas import CustoPublic


def test_tipo_cartao_credito_existe():
    assert TipoCusto.CARTAO_CREDITO.value == "CARTAO_CREDITO"


def test_custo_public_aceita_valor_negativo():
    # estorno importado tem valor negativo; a serialização de saída não pode barrar
    cp = CustoPublic(
        id=1,
        descricao="Estorno",
        valor=Decimal("-21.80"),
        data_vencimento=date(2026, 6, 24),
        tipo=TipoCusto.CARTAO_CREDITO,
        mes_referencia_id=1,
        status="PENDENTE",
        custo_fixo_origem_id=None,
        created_at=datetime(2026, 6, 24, 12, 0, 0),
        updated_at=datetime(2026, 6, 24, 12, 0, 0),
    )
    assert cp.valor == Decimal("-21.80")
