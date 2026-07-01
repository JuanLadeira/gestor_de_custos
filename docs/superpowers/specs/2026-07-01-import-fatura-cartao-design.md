# Importação de fatura de cartão de crédito (CSV Nubank)

Data: 2026-07-01
Branch base: `feat/rbac-tenant-isolation`

## Objetivo

Permitir que o usuário importe a fatura do cartão de crédito (export CSV do
Nubank) e gerar automaticamente um `Custo` por compra, categorizado como custo
de cartão de crédito, no mês de referência correspondente à data de cada compra,
sem duplicar quando o mesmo CSV (ou linhas repetidas) for reimportado.

## Fonte de dados

Export CSV do Nubank com 3 colunas:

```
date,title,amount
2026-07-01,Uber Uber *Trip Help.U,"4,28"
2026-06-28,Ouse Shoes - Parcela 1/2,"50,00"
2026-06-24,Estorno de pagamento (Reembolso Pix ...),"- 21,80"
```

- `date`: ISO `YYYY-MM-DD`.
- `title`: descrição/estabelecimento (pode conter "Parcela 1/2").
- `amount`: decimal BR (vírgula, aspas). Negativo = estorno/reembolso.
- Sem coluna de categoria → a categoria é fixa: cartão de crédito.

PDF da fatura foi descartado como fonte: o CSV é estável e trivial de parsear,
sem OCR/regex frágil.

## Decisões de design

1. **Granularidade:** um `Custo` por linha de compra.
2. **Categoria:** tipo fixo novo `TipoCusto.CARTAO_CREDITO`.
3. **Mês destino:** o mês de referência da **data de cada compra** (um import
   pode tocar vários meses).
4. **Estornos (valores negativos):** importados como `Custo` de valor negativo
   (soma dos custos = total líquido da fatura).
5. **Criação de mês:** reusa o contrato get-or-create atual — um mês novo criado
   durante o import nasce com os custos fixos ativos importados.
6. **Dedup:** idempotência por fingerprint por mês (ver abaixo).
7. **Execução:** endpoint síncrono (arquivo pequeno, ~100 linhas). Sem Celery.

## Arquitetura

Unidades isoladas, cada uma com uma responsabilidade e testável sozinha:

### 1. Parser puro — `app/custo/importacao_nubank.py`

```python
@dataclass
class LinhaFatura:
    data: date
    titulo: str
    valor: Decimal          # negativo p/ estornos
    ocorrencia: int         # índice entre linhas idênticas no mesmo arquivo (0,1,2...)

def parse_nubank_csv(conteudo: bytes) -> list[LinhaFatura]: ...
```

- Converte `amount` BR ("- 21,80", "4,28") para `Decimal`.
- `ocorrencia` = quantas linhas idênticas (mesma data+titulo+valor) vieram antes
  no arquivo; distingue duplicatas reais de reimport.
- Sem acesso a banco. Erros de formato → exceção de parsing dedicada.

### 2. Modelo de dados

- `TipoCusto` ganha `CARTAO_CREDITO = "CARTAO_CREDITO"`.
- `Custo` ganha `import_fingerprint: str | None` (nullable, indexado).
- Constraint único `(mes_referencia_id, import_fingerprint)` — base da dedup.
- Migration Alembic: add valor de enum (`ALTER TYPE ... ADD VALUE`) + coluna +
  índice único parcial (só onde `import_fingerprint IS NOT NULL`).
  - Gotcha: `ADD VALUE` não pode ser usado na mesma transação em que o valor é
    referenciado. Como a migration só adiciona o valor e a coluna (não insere
    dados com o novo enum), é seguro; se der problema de transação, usar
    `op.execute("COMMIT")` antes do `ADD VALUE` ou migration separada.

### 3. Helper de mês — `MesReferenciaService.get_or_create(tenant_id, ano, mes)`

- Extraído da lógica hoje embutida em `obter_ou_criar_mes_atual` (que passa a
  chamar `get_or_create(tenant, hoje.year, hoje.month)`).
- Mantém o import de custos fixos ao criar mês novo.

### 4. Service — `CustoService.importar_fatura(conteudo, tenant_id)`

```python
@dataclass
class ResultadoImport:
    criados: int
    ignorados: int
    meses_afetados: int

async def importar_fatura(self, conteudo: bytes, tenant_id: int) -> ResultadoImport: ...
```

Fluxo:
1. `linhas = parse_nubank_csv(conteudo)`.
2. Para cada linha: deriva `(ano, mes)` de `linha.data`.
3. `mes = await mes_service.get_or_create(tenant_id, ano, mes)`.
4. `fp = fingerprint(linha)` (ver abaixo).
5. Se já existe `Custo` com `(mes.id, fp)` → conta em `ignorados`, pula.
6. Senão insere `Custo(descricao=titulo, valor=valor, data_vencimento=data,
   tipo=CARTAO_CREDITO, status=PENDENTE, mes_referencia_id=mes.id,
   import_fingerprint=fp)` → conta em `criados`.
7. Retorna `ResultadoImport`.

**Fingerprint:**
`sha256(f"{data.isoformat()}|{titulo}|{valor}|{ocorrencia}")` (hex).
- Reimport do mesmo CSV → mesmos fingerprints → tudo ignorado.
- Duas compras idênticas reais no mesmo arquivo → `ocorrencia` diferente →
  ambas preservadas.

### 5. Endpoint — `POST /api/custos/importar`

- Multipart: `file` (UploadFile). Sem `mes_referencia_id`.
- Dependência de permissão: nova `custo:import`.
- `tenant_id = current_user.tenant_id`.
- Lê bytes, chama `service.importar_fatura`, retorna
  `{ "criados": int, "ignorados": int, "meses_afetados": int }`.
- Erro de parsing → HTTP 422 com mensagem clara.

### 6. Permissão — `app/authz/catalog.py`

- Add `("custo:import", "custos", "Importar fatura de cartão")`.
- Incluir `custo:import` nos papéis default que já têm `custo:create`
  (ex.: papel financeiro / perfil Dono).

### 7. Frontend — `CustosView.vue`

- Botão "Importar fatura" (gated `authStore.can('custo:import')`).
- Abre file picker (`.csv`) → `POST /custos/importar` (multipart) via api client.
- Toast/resumo: "X custos criados, Y ignorados em N meses".
- Recarrega a lista de custos do mês atual após sucesso.
- Novo método no api client: `importarFatura(file)`.

## Fluxo de dados

```
CSV bytes
  → parse_nubank_csv           (app/custo/importacao_nubank.py, puro)
  → [LinhaFatura]
  → CustoService.importar_fatura
       ├─ MesReferenciaService.get_or_create(tenant, ano, mes)   (por compra)
       ├─ fingerprint + dedup query por (mes_id, fp)
       └─ insere Custo(tipo=CARTAO_CREDITO, ...)
  → ResultadoImport → JSON → toast no front
```

## Tratamento de erro

- CSV sem cabeçalho esperado / colunas erradas → exceção de parsing → 422.
- Valor não parseável → 422 com a linha problemática.
- Mês inexistente → criado via get_or_create (não é erro).
- Sem permissão `custo:import` → 403 (via `require`).
- Tenant scoping: import só cria/usa meses do `current_user.tenant_id`.

## Testes

- **Parser (unit, isolado):** BR decimal, negativos, aspas, `ocorrencia` de
  duplicatas, cabeçalho inválido.
- **Service:** import cria N custos nos meses certos; reimport do mesmo conteúdo
  → 0 criados / N ignorados; duplicata real preservada; estorno vira custo
  negativo; mês novo criado dispara import de fixos.
- **Router:** happy path multipart; 403 sem permissão; 422 CSV inválido;
  isolamento por tenant.
- Runner: `docker exec custos_test sh -c 'cd /app && uv run pytest <args>'`.

## Fora de escopo (YAGNI)

- Parse de PDF de fatura.
- Categorização por categoria do Nubank (CSV não traz categoria).
- Import assíncrono / progresso.
- Casar estorno com a compra original para abater.
- Seleção manual de mês no upload.
