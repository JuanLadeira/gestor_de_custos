# Modelos de Dados

[[Índice|← Índice]]

Todas as entidades herdam de `Base` (`app/database/base.py`), que provê:
- `id`: Integer primary key (auto-increment)
- `created_at`: Timestamp com default `func.now()`
- `updated_at`: Timestamp com `onupdate` automático

---

## Diagrama de Entidades

```
┌──────────┐          ┌──────────┐
│  Tenant  │──1:N────▶│ Usuario  │
│ id       │          │ id       │
│ nome     │          │ username │
│ descricao│          │ email    │
└────┬─────┘          │ password │
     │                │ nome     │
     │ 1:N            │ ativo    │
     ▼                │ tenant_id│
┌────────────┐        └────┬─────┘
│MesRef.     │             │ 1:N
│ id         │             ▼
│ ano        │        ┌──────────────────┐
│ mes        │        │ PagamentoRateio  │
│ status     │        │ id               │
│ tenant_id  │        │ porcentagem      │
└────┬───────┘        │ valor_calculado  │
     │ 1:N            │ status           │
     ▼                │ custo_id  ◀──┐  │
┌──────────┐          │ usuario_id   │  │
│ Custo    │──1:N────▶└──────────────┘  │
│ id       │                            │
│ descricao│                            │
│ valor    │                            │
│ data_vec.│                            │
│ tipo     │ FIXO | VARIAVEL            │
│ status   │ PENDENTE | PAGO            │
│ mes_ref_id│                           │
│ custo_fixo│◀──────────────────────────┤
│ _origem_id│                           │
└──────────┘                            │
                                        │
┌──────────┐                            │
│CustoFixo │──────────────── gera ──────┘
│ id       │ (template)
│ descricao│
│ valor    │
│ dia_venc.│
│ ativo    │
│ tenant_id│
└──────────┘
```

---

## Tenant

**Tabela:** `tenant`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer PK | Auto-gerado |
| `nome` | String(100) | Nome do grupo/casa |
| `descricao` | String(500)? | Descrição opcional |
| `created_at` | DateTime | Auto-setado |
| `updated_at` | DateTime | Auto-atualizado |

**Relacionamentos:**
- `usuarios` → `list[Usuario]` (cascade delete, eager load)
- `meses_referencia` → `list[MesReferencia]` (cascade delete, eager load)
- `custos_fixos` → `list[CustoFixo]` (cascade delete, eager load)

---

## Usuario

**Tabela:** `usuario`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer PK | Auto-gerado |
| `username` | String(50) | Único, indexado |
| `email` | String(100) | Único, indexado |
| `password` | String(255) | Hash Argon2 |
| `nome` | String(100) | Nome de exibição |
| `ativo` | Boolean | Default `True` |
| `tenant_id` | FK → `tenant.id` | CASCADE delete |

**Relacionamentos:**
- `tenant` → `Tenant`
- `pagamentos_rateio` → `list[PagamentoRateio]` (cascade delete, eager load)

---

## MesReferencia

**Tabela:** `mes_referencia`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer PK | Auto-gerado |
| `ano` | Integer | Ex: 2026 |
| `mes` | Integer | 1-12 |
| `status` | Enum | `ABERTO` \| `FECHADO` |
| `tenant_id` | FK → `tenant.id` | CASCADE delete |

**Constraint único:** `(tenant_id, ano, mes)` — um mês por tenant por ano.

**Relacionamentos:**
- `tenant` → `Tenant`
- `custos` → `list[Custo]` (cascade delete, eager load)

---

## CustoFixo

**Tabela:** `custo_fixo`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer PK | Auto-gerado |
| `descricao` | String(200) | Ex: "Aluguel", "Internet" |
| `valor` | Numeric(10,2) | Valor padrão |
| `dia_vencimento` | Integer | Dia do mês (1-31), default 10 |
| `ativo` | Boolean | Se `False`, não é importado |
| `tenant_id` | FK → `tenant.id` | CASCADE delete |

**Relacionamentos:**
- `tenant` → `Tenant`
- `custos_gerados` → `list[Custo]` — custos que este template originou

---

## Custo

**Tabela:** `custo`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer PK | Auto-gerado |
| `descricao` | String(200) | Descrição do gasto |
| `valor` | Numeric(10,2) | Valor total (> 0) |
| `data_vencimento` | Date | Data de vencimento |
| `tipo` | Enum | `FIXO` \| `VARIAVEL` |
| `status` | Enum | `PENDENTE` \| `PAGO` |
| `mes_referencia_id` | FK → `mes_referencia.id` | CASCADE delete |
| `custo_fixo_origem_id` | FK → `custo_fixo.id`? | SET NULL se template deletado |

**Relacionamentos:**
- `mes_referencia` → `MesReferencia`
- `custo_fixo_origem` → `CustoFixo?`
- `pagamentos_rateio` → `list[PagamentoRateio]` (cascade delete, eager load)

---

## PagamentoRateio

**Tabela:** `pagamento_rateio`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer PK | Auto-gerado |
| `porcentagem` | Numeric(5,2) | % deste usuário (0 < p ≤ 100) |
| `valor_calculado` | Numeric(10,2) | Calculado: `valor * porcentagem / 100` |
| `status` | Enum | `PENDENTE` \| `PAGO` |
| `custo_id` | FK → `custo.id` | CASCADE delete |
| `usuario_id` | FK → `usuario.id` | CASCADE delete |

**Constraint único:** `(custo_id, usuario_id)` — um registro por usuário por custo.

**Relacionamentos:**
- `custo` → `Custo`
- `usuario` → `Usuario`

> Regra central: soma de `porcentagem` de todos os rateios de um mesmo `custo_id` nunca pode ultrapassar 100%.
> Ver [[Regras de Negócio#Validação de Rateio]].

---

## Base Model

```python
# app/database/base.py
class Base(DeclarativeBase):
    id: Mapped[intpk]       # Integer, primary_key=True, autoincrement
    created_at: Mapped[created_at]  # DateTime, server_default=func.now()
    updated_at: Mapped[updated_at]  # DateTime, server_default + onupdate
```

---

Ver também: [[Regras de Negócio]] | [[Módulos da API]]
