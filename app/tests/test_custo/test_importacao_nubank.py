from datetime import date
from decimal import Decimal

import pytest

from app.custo.importacao_nubank import (
    CSVFaturaInvalido,
    LinhaFatura,
    parse_nubank_csv,
)

CSV_OK = (
    b"date,title,amount\n"
    b'2026-07-01,Uber Uber *Trip Help.U,"4,28"\n'
    b'2026-06-24,Estorno de pagamento (Reembolso Pix),"- 21,80"\n'
    b'2026-06-28,Dl *Uberrides,"5,52"\n'
    b'2026-06-28,Dl *Uberrides,"5,52"\n'
)


def test_parse_campos_basicos():
    linhas = parse_nubank_csv(CSV_OK)
    assert len(linhas) == 4
    assert linhas[0] == LinhaFatura(date(2026, 7, 1), "Uber Uber *Trip Help.U", Decimal("4.28"), 0)


def test_parse_valor_negativo():
    linhas = parse_nubank_csv(CSV_OK)
    assert linhas[1].valor == Decimal("-21.80")


def test_ocorrencia_distingue_duplicatas_reais():
    linhas = parse_nubank_csv(CSV_OK)
    # duas linhas idênticas (mesma data/titulo/valor) recebem ocorrencia 0 e 1
    iguais = [l for l in linhas if l.titulo == "Dl *Uberrides"]
    assert sorted(l.ocorrencia for l in iguais) == [0, 1]


def test_cabecalho_invalido_levanta():
    with pytest.raises(CSVFaturaInvalido):
        parse_nubank_csv(b"data;descricao;valor\n2026-07-01;x;1,00\n")


def test_valor_nao_parseavel_levanta():
    with pytest.raises(CSVFaturaInvalido):
        parse_nubank_csv(b'date,title,amount\n2026-07-01,x,"abc"\n')
