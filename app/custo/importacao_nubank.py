import csv
import io
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

CABECALHO_ESPERADO = ["date", "title", "amount"]


class CSVFaturaInvalido(Exception):
    """CSV de fatura Nubank com formato inesperado."""


@dataclass(frozen=True)
class LinhaFatura:
    data: date
    titulo: str
    valor: Decimal
    ocorrencia: int


def _parse_valor(bruto: str) -> Decimal:
    # BR: "- 21,80" / "4,28" -> Decimal. Remove espaços e troca vírgula por ponto.
    limpo = bruto.strip().replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return Decimal(limpo)
    except (InvalidOperation, ValueError) as e:
        raise CSVFaturaInvalido(f"Valor inválido: {bruto!r}") from e


def parse_nubank_csv(conteudo: bytes) -> list[LinhaFatura]:
    texto = conteudo.decode("utf-8-sig")
    leitor = csv.reader(io.StringIO(texto))
    try:
        cabecalho = next(leitor)
    except StopIteration as e:
        raise CSVFaturaInvalido("CSV vazio") from e
    if [c.strip().lower() for c in cabecalho] != CABECALHO_ESPERADO:
        raise CSVFaturaInvalido(f"Cabeçalho inesperado: {cabecalho}")

    vistos: dict[tuple[str, str, str], int] = {}
    linhas: list[LinhaFatura] = []
    for row in leitor:
        if not row or all(not c.strip() for c in row):
            continue
        if len(row) != 3:
            raise CSVFaturaInvalido(f"Linha com colunas erradas: {row}")
        data_str, titulo, valor_str = row[0].strip(), row[1].strip(), row[2]
        try:
            data = datetime.strptime(data_str, "%Y-%m-%d").date()
        except ValueError as e:
            raise CSVFaturaInvalido(f"Data inválida: {data_str!r}") from e
        valor = _parse_valor(valor_str)
        chave = (data_str, titulo, valor_str.strip())
        ocorrencia = vistos.get(chave, 0)
        vistos[chave] = ocorrencia + 1
        linhas.append(LinhaFatura(data=data, titulo=titulo, valor=valor, ocorrencia=ocorrencia))
    return linhas
