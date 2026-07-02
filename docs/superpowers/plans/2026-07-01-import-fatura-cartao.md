# Import de Fatura de Cartão (CSV Nubank) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Importar o CSV da fatura do cartão Nubank gerando um `Custo` por compra (tipo `CARTAO_CREDITO`), no mês de cada compra, sem duplicar em reimport.

**Architecture:** Parser puro CSV → `CustoService.importar_fatura` que faz get-or-create de mês por compra, dedup por fingerprint e insere `Custo` ORM direto (bypass de schema, p/ permitir valores negativos de estorno). Endpoint síncrono multipart, gated por nova permissão `custo:import`. Botão de upload na CustosView.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, PostgreSQL, pytest, Vue 3 + TypeScript + Axios.

## Global Constraints

- Runtime Python via `uv`. Testes: `docker exec custos_test sh -c 'cd /app && uv run pytest <args>'`.
- Migrations: `docker exec custos_app_dev sh -c 'cd /app && uv run alembic ...'`. Head atual: `k9l0m1n2o3p4`.
- Enum PG do tipo de custo: `tipocusto` (labels atuais: `FIXO`, `VARIAVEL`).
- Custos de import podem ter `valor` negativo (estornos) → NÃO usar `CustoCreate` p/ inseri-los; construir `Custo` ORM direto.
- Tenant scoping: import só cria/usa meses do `current_user.tenant_id`.
- Fingerprint de dedup: `sha256(f"{data.isoformat()}|{titulo}|{valor}|{ocorrencia}")` hex.
- Categoria fixa: `TipoCusto.CARTAO_CREDITO`. Mês = data de cada compra. Mês novo criado mantém import de custos fixos (contrato get-or-create atual).

---

### Task 1: Camada de dados — enum, coluna de dedup, validador de valor

**Files:**
- Modify: `app/custo/models.py` (add `CARTAO_CREDITO` ao `TipoCusto`; add coluna `import_fingerprint`)
- Modify: `app/custo/schemas.py:8-30` (mover validação de `valor > 0` de `CustoBase` p/ `CustoCreate`)
- Create: `alembic/versions/l0m1n2o3p4q5_add_cartao_credito_import.py`
- Test: `app/tests/test_custo/test_import_schema.py`

**Interfaces:**
- Produces: `TipoCusto.CARTAO_CREDITO` (valor `"CARTAO_CREDITO"`); `Custo.import_fingerprint: str | None`; `CustoPublic` aceita `valor` negativo.

- [ ] **Step 1: Escrever teste que falha — CustoPublic serializa valor negativo + enum novo existe**

Create `app/tests/test_custo/__init__.py` (vazio) e `app/tests/test_custo/test_import_schema.py`:

```python
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
```

- [ ] **Step 2: Rodar — deve falhar**

Run: `docker exec custos_test sh -c 'cd /app && uv run pytest app/tests/test_custo/test_import_schema.py -v'`
Expected: FAIL (`AttributeError: CARTAO_CREDITO` e/ou `ValidationError: Valor deve ser maior que zero`).

- [ ] **Step 3: Add valor ao enum e coluna ao modelo**

Em `app/custo/models.py`, no enum:

```python
class TipoCusto(str, enum.Enum):
    FIXO = "FIXO"
    VARIAVEL = "VARIAVEL"
    CARTAO_CREDITO = "CARTAO_CREDITO"
```

E na classe `Custo`, após `custo_fixo_origem_id`:

```python
    import_fingerprint: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
```

- [ ] **Step 4: Mover validação de valor p/ CustoCreate**

Em `app/custo/schemas.py`, remover o `@field_validator("valor")` de `CustoBase` (deixando só os campos) e colocá-lo em `CustoCreate`:

```python
class CustoBase(BaseModel):
    descricao: str
    valor: Decimal
    data_vencimento: date
    tipo: TipoCusto = TipoCusto.VARIAVEL
    mes_referencia_id: int


class CustoCreate(CustoBase):
    # custo_fixo_origem_id é setado server-side pelo import de fixos, nunca do cliente.
    @field_validator("valor")
    @classmethod
    def validate_valor(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Valor deve ser maior que zero")
        return v
```

(`CustoUpdate` mantém seu próprio validador inalterado.)

- [ ] **Step 5: Rodar teste — deve passar**

Run: `docker exec custos_test sh -c 'cd /app && uv run pytest app/tests/test_custo/test_import_schema.py -v'`
Expected: PASS (2 passed).

- [ ] **Step 6: Criar migration**

Create `alembic/versions/l0m1n2o3p4q5_add_cartao_credito_import.py`:

```python
"""add_cartao_credito_import

Revision ID: l0m1n2o3p4q5
Revises: k9l0m1n2o3p4
Create Date: 2026-07-01 20:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "l0m1n2o3p4q5"
down_revision: Union[str, Sequence[str], None] = "k9l0m1n2o3p4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ADD VALUE não pode ser usado na mesma transação; roda em autocommit.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE tipocusto ADD VALUE IF NOT EXISTS 'CARTAO_CREDITO'")

    op.add_column("custo", sa.Column("import_fingerprint", sa.String(64), nullable=True))
    op.create_index("ix_custo_import_fingerprint", "custo", ["import_fingerprint"])
    # dedup: um fingerprint no máximo uma vez por mês
    op.create_index(
        "uq_custo_mes_fingerprint",
        "custo",
        ["mes_referencia_id", "import_fingerprint"],
        unique=True,
        postgresql_where=sa.text("import_fingerprint IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_custo_mes_fingerprint", table_name="custo")
    op.drop_index("ix_custo_import_fingerprint", table_name="custo")
    op.drop_column("custo", "import_fingerprint")
    # valor de enum não é removível sem recriar o tipo; downgrade deixa 'CARTAO_CREDITO'.
```

- [ ] **Step 7: Aplicar migration**

Run: `docker exec custos_app_dev sh -c 'cd /app && uv run alembic upgrade head'`
Expected: `Running upgrade k9l0m1n2o3p4 -> l0m1n2o3p4q5`.

- [ ] **Step 8: Commit**

```bash
git add app/custo/models.py app/custo/schemas.py alembic/versions/l0m1n2o3p4q5_add_cartao_credito_import.py app/tests/test_custo/
git commit -m "feat(custo): tipo CARTAO_CREDITO + import_fingerprint + migration"
```

---

### Task 2: Parser puro do CSV Nubank

**Files:**
- Create: `app/custo/importacao_nubank.py`
- Test: `app/tests/test_custo/test_importacao_nubank.py`

**Interfaces:**
- Produces:
  - `class LinhaFatura` (dataclass): `data: date`, `titulo: str`, `valor: Decimal`, `ocorrencia: int`.
  - `def parse_nubank_csv(conteudo: bytes) -> list[LinhaFatura]`.
  - `class CSVFaturaInvalido(Exception)` — cabeçalho/linha inválidos.

- [ ] **Step 1: Escrever testes que falham**

Create `app/tests/test_custo/test_importacao_nubank.py`:

```python
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
```

- [ ] **Step 2: Rodar — deve falhar**

Run: `docker exec custos_test sh -c 'cd /app && uv run pytest app/tests/test_custo/test_importacao_nubank.py -v'`
Expected: FAIL (`ModuleNotFoundError: app.custo.importacao_nubank`).

- [ ] **Step 3: Implementar parser**

Create `app/custo/importacao_nubank.py`:

```python
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
```

- [ ] **Step 4: Rodar — deve passar**

Run: `docker exec custos_test sh -c 'cd /app && uv run pytest app/tests/test_custo/test_importacao_nubank.py -v'`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add app/custo/importacao_nubank.py app/tests/test_custo/test_importacao_nubank.py
git commit -m "feat(custo): parser puro do CSV de fatura Nubank"
```

---

### Task 3: `MesReferenciaService.get_or_create`

**Files:**
- Modify: `app/mes_referencia/services.py:48-67` (extrair get-or-create genérico; `obter_ou_criar_mes_atual` passa a delegar)
- Test: `app/tests/test_mes/test_get_or_create.py`

**Interfaces:**
- Consumes: `importar_custos_fixos_para_mes` (já existe).
- Produces: `async def get_or_create(self, tenant_id: int, ano: int, mes: int) -> MesReferencia` — cria o mês (com import de custos fixos) se não existir; idempotente por `(tenant_id, ano, mes)`.

- [ ] **Step 1: Escrever teste que falha**

Create `app/tests/test_mes/__init__.py` (vazio) e `app/tests/test_mes/test_get_or_create.py`:

```python
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
```

- [ ] **Step 2: Rodar — deve falhar**

Run: `docker exec custos_test sh -c 'cd /app && uv run pytest app/tests/test_mes/test_get_or_create.py -v'`
Expected: FAIL (`AttributeError: get_or_create`).

- [ ] **Step 3: Implementar get_or_create e delegar**

Em `app/mes_referencia/services.py`, substituir o corpo de `obter_ou_criar_mes_atual` e adicionar `get_or_create`:

```python
    async def get_or_create(self, tenant_id: int, ano: int, mes: int) -> MesReferencia:
        """Get-or-create de um mês; importa custos fixos ao criar um mês novo."""
        existente = await self.get_by_tenant_ano_mes(tenant_id, ano, mes)
        if existente:
            return existente
        mes_ref = MesReferencia(tenant_id=tenant_id, ano=ano, mes=mes)
        self.session.add(mes_ref)
        await self.session.flush()
        await self.session.refresh(mes_ref)
        await self.importar_custos_fixos_para_mes(mes_ref.id, tenant_id)
        return mes_ref

    async def obter_ou_criar_mes_atual(self, tenant_id: int) -> MesReferencia:
        """Get or create the current month reference, importing fixed costs if new."""
        hoje = date.today()
        return await self.get_or_create(tenant_id, hoje.year, hoje.month)
```

- [ ] **Step 4: Rodar teste novo + regressão de mês**

Run: `docker exec custos_test sh -c 'cd /app && uv run pytest app/tests/test_mes/ app/tests/test_authz/test_mes_router.py -v'`
Expected: PASS (todos).

- [ ] **Step 5: Commit**

```bash
git add app/mes_referencia/services.py app/tests/test_mes/
git commit -m "refactor(mes): extrai get_or_create(tenant, ano, mes)"
```

---

### Task 4: `CustoService.importar_fatura`

**Files:**
- Modify: `app/custo/services.py` (add `importar_fatura`, `_fingerprint`, dataclass `ResultadoImport`; construtor passa a aceitar `MesReferenciaService`)
- Test: `app/tests/test_custo/test_importar_fatura.py`

**Interfaces:**
- Consumes: `parse_nubank_csv`, `LinhaFatura` (Task 2); `MesReferenciaService.get_or_create` (Task 3); `Custo`, `TipoCusto.CARTAO_CREDITO`, `Custo.import_fingerprint` (Task 1).
- Produces:
  - `@dataclass class ResultadoImport: criados: int; ignorados: int; meses_afetados: int`.
  - `async def importar_fatura(self, conteudo: bytes, tenant_id: int) -> ResultadoImport`.

- [ ] **Step 1: Escrever teste que falha**

Create `app/tests/test_custo/test_importar_fatura.py`:

```python
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
```

- [ ] **Step 2: Rodar — deve falhar**

Run: `docker exec custos_test sh -c 'cd /app && uv run pytest app/tests/test_custo/test_importar_fatura.py -v'`
Expected: FAIL (`TypeError` no construtor / `AttributeError: importar_fatura`).

- [ ] **Step 3: Implementar service**

Em `app/custo/services.py`, ajustar imports/topo e construtor, e adicionar os métodos:

```python
import hashlib
from dataclasses import dataclass

from sqlalchemy import select

from app.custo.importacao_nubank import LinhaFatura, parse_nubank_csv
from app.custo.models import Custo, TipoCusto
from app.mes_referencia.services import MesReferenciaService


@dataclass
class ResultadoImport:
    criados: int
    ignorados: int
    meses_afetados: int
```

Trocar o `__init__` e adicionar métodos na classe `CustoService`:

```python
    def __init__(self, session, mes_service: MesReferenciaService | None = None):
        self.session = session
        self.mes_service = mes_service or MesReferenciaService(session)

    @staticmethod
    def _fingerprint(linha: LinhaFatura) -> str:
        base = f"{linha.data.isoformat()}|{linha.titulo}|{linha.valor}|{linha.ocorrencia}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    async def importar_fatura(self, conteudo: bytes, tenant_id: int) -> "ResultadoImport":
        linhas = parse_nubank_csv(conteudo)
        criados = 0
        ignorados = 0
        meses: set[int] = set()
        for linha in linhas:
            mes = await self.mes_service.get_or_create(tenant_id, linha.data.year, linha.data.month)
            meses.add(mes.id)
            fp = self._fingerprint(linha)
            existe = await self.session.execute(
                select(Custo.id).where(
                    Custo.mes_referencia_id == mes.id, Custo.import_fingerprint == fp
                )
            )
            if existe.scalar_one_or_none() is not None:
                ignorados += 1
                continue
            self.session.add(Custo(
                descricao=linha.titulo,
                valor=linha.valor,
                data_vencimento=linha.data,
                tipo=TipoCusto.CARTAO_CREDITO,
                mes_referencia_id=mes.id,
                import_fingerprint=fp,
            ))
            await self.session.flush()
            criados += 1
        return ResultadoImport(criados=criados, ignorados=ignorados, meses_afetados=len(meses))
```

Nota: o `get_custo_service` (factory) precisa continuar funcionando — como `mes_service` tem default, nenhuma mudança é necessária lá.

- [ ] **Step 4: Rodar — deve passar**

Run: `docker exec custos_test sh -c 'cd /app && uv run pytest app/tests/test_custo/test_importar_fatura.py -v'`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add app/custo/services.py app/tests/test_custo/test_importar_fatura.py
git commit -m "feat(custo): CustoService.importar_fatura com dedup por fingerprint"
```

---

### Task 5: Permissão `custo:import` + endpoint `POST /api/custos/importar`

**Files:**
- Modify: `app/authz/catalog.py:23` (add `custo:import` ao catálogo)
- Modify: `app/custo/router.py` (add rota de import)
- Test: `app/tests/test_authz/test_import_fatura_router.py`

**Interfaces:**
- Consumes: `CustoService.importar_fatura` (Task 4); `require` de `app/authz/dependencies.py`; `CurrentUser`.
- Produces: `POST /api/custos/importar` (multipart `file`) → `200 {"criados": int, "ignorados": int, "meses_afetados": int}`.

- [ ] **Step 1: Escrever teste que falha**

Create `app/tests/test_authz/test_import_fatura_router.py`:

```python
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
```

- [ ] **Step 2: Rodar — deve falhar**

Run: `docker exec custos_test sh -c 'cd /app && uv run pytest app/tests/test_authz/test_import_fatura_router.py -v'`
Expected: FAIL (404 na rota inexistente).

- [ ] **Step 3: Add permissão ao catálogo**

Em `app/authz/catalog.py`, após a linha `("custo:delete", ...)`:

```python
    ("custo:import", "custo", "Importar fatura de cartão"),
```

(Como o grupo é `custo`, o papel default `Financeiro = codes_for_grupos("custo", ...)` já inclui automaticamente; `Dono` herda via `Financeiro`.)

- [ ] **Step 4: Add rota de import**

Em `app/custo/router.py`, ajustar imports do topo e adicionar a rota. Imports:

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.custo.importacao_nubank import CSVFaturaInvalido
```

Rota (após `create_custo`):

```python
@router.post("/importar", dependencies=[Depends(require("custo:import"))])
async def importar_fatura(
    file: UploadFile,
    current_user: CurrentUser,
    service: CustoServiceDep,
):
    conteudo = await file.read()
    try:
        resultado = await service.importar_fatura(conteudo, tenant_id=current_user.tenant_id)
    except CSVFaturaInvalido as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {
        "criados": resultado.criados,
        "ignorados": resultado.ignorados,
        "meses_afetados": resultado.meses_afetados,
    }
```

Nota de ordem de rota: `/importar` deve ser declarada ANTES de `/{custo_id}` para não colidir com o path param. Colocar logo após `create_custo` (que fica antes do bloco `/{custo_id}`) satisfaz isso.

- [ ] **Step 5: Rodar — deve passar**

Run: `docker exec custos_test sh -c 'cd /app && uv run pytest app/tests/test_authz/test_import_fatura_router.py -v'`
Expected: PASS (3 passed).

- [ ] **Step 6: Rodar catálogo (regressão de contagem de permissões)**

Run: `docker exec custos_test sh -c 'cd /app && uv run pytest app/tests/test_authz/test_catalog.py -v'`
Expected: PASS (ajustar contagem esperada no teste se ele fixar um número — se falhar por contagem, atualizar o número no teste de catálogo).

- [ ] **Step 7: Commit**

```bash
git add app/authz/catalog.py app/custo/router.py app/tests/test_authz/test_import_fatura_router.py
git commit -m "feat(custo): endpoint POST /custos/importar + permissao custo:import"
```

---

### Task 6: Frontend — api client + botão "Importar fatura" na CustosView

**Files:**
- Modify: `frontend/src/api/client.ts:123-130` (add `importarFatura`)
- Modify: `frontend/src/views/CustosView.vue` (botão + handler + input file)
- Test: manual (Vite/HMR) — sem suíte de front no projeto.

**Interfaces:**
- Consumes: `POST /api/custos/importar` (Task 5).
- Produces: `api.importarFatura(file: File)`; botão gated por `custo:import`.

- [ ] **Step 1: Add método ao api client**

Em `frontend/src/api/client.ts`, na seção Custos (após `deleteCusto`):

```ts
  importarFatura: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return apiClient.post<{ criados: number; ignorados: number; meses_afetados: number }>(
      '/custos/importar', form, { headers: { 'Content-Type': 'multipart/form-data' } },
    )
  },
```

- [ ] **Step 2: Add botão + input + handler na CustosView**

Em `frontend/src/views/CustosView.vue`, ao lado do botão "Novo custo" (perto da linha 21), adicionar:

```html
        <label
          v-if="authStore.can('custo:import')"
          style="display:inline-flex;align-items:center;gap:6px;background:#f1f5f9;color:#334155;font-size:13px;font-weight:600;padding:9px 14px;border-radius:9px;cursor:pointer;margin-right:8px;"
        >
          <input type="file" accept=".csv" @change="importarFatura" style="display:none;" />
          {{ importando ? 'Importando…' : 'Importar fatura' }}
        </label>
```

No `<script setup>`, add o estado e o handler (perto de `carregarCustos`):

```ts
const importando = ref(false)

async function importarFatura(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  importando.value = true
  try {
    const { data } = await api.importarFatura(file)
    alert(`${data.criados} custos criados, ${data.ignorados} ignorados em ${data.meses_afetados} mês(es).`)
    await carregarCustos()
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Falha ao importar fatura')
  } finally {
    importando.value = false
    input.value = ''
  }
}
```

(Garantir que `ref` está importado de `vue` — já está no arquivo.)

- [ ] **Step 3: Verificar HMR sem erro**

Run: `docker logs custos_frontend_dev --tail 8 2>&1 | grep -iE "error|hmr update"`
Expected: linha `[vite] hmr update /src/views/CustosView.vue` e nenhum `error`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api/client.ts frontend/src/views/CustosView.vue
git commit -m "feat(custo-fe): botao Importar fatura na CustosView"
```

---

### Task 7: Regressão completa + verificação com CSV real

**Files:**
- Test: suíte inteira.

- [ ] **Step 1: Rodar suíte completa**

Run: `docker exec custos_test sh -c 'cd /app && uv run pytest -q'`
Expected: todos passam (69 anteriores + os novos).

- [ ] **Step 2: Smoke com o CSV real (opcional, via app rodando)**

Login como `juan`/`senha123` no front, tela Custos → "Importar fatura" → escolher `Nubank_2026-07-13.csv` → conferir toast (criados > 0) e custos aparecendo em Junho e Julho/2026. Reimportar o mesmo arquivo → toast com `ignorados` = total, `criados` = 0.

- [ ] **Step 3: Commit final (se houver ajustes)**

```bash
git add -A
git commit -m "test: regressao completa do import de fatura"
```

---

## Self-Review (autor)

- **Cobertura do spec:** parser (T2), modelo/enum/fingerprint/migration (T1), get_or_create mantendo fixos (T3), service+dedup+estorno negativo (T4), endpoint+permissão+422 (T5), frontend sem seleção de mês (T6), regressão (T7). Estornos negativos cobertos por T1 (schema) + T4 (teste). ✓
- **Placeholders:** nenhum — todo passo tem código/comando concretos. ✓
- **Consistência de tipos:** `LinhaFatura(data,titulo,valor,ocorrencia)`, `ResultadoImport(criados,ignorados,meses_afetados)`, `get_or_create(tenant_id,ano,mes)`, `importar_fatura(conteudo,tenant_id)`, `_fingerprint(linha)` usados de forma idêntica entre T2→T4→T5. ✓
- **Risco conhecido:** `test_catalog.py` pode fixar contagem de permissões → passo T5.6 cobre o ajuste. `CustoService.__init__` ganhou 2º parâmetro opcional → factory `get_custo_service` intacto (default). ✓
