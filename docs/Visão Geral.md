# Visão Geral

[[Índice|← Índice]]

## Objetivo

Gerenciar custos mensais compartilhados entre um grupo de pessoas. O sistema permite:

- Cadastrar **custos fixos** (templates) que se repetem todo mês automaticamente
- Adicionar **custos variáveis** manualmente quando necessário
- Definir o **rateio** de cada custo entre os membros do grupo (em %) com validação de que o total não ultrapasse 100%
- Receber **lembretes por email** quando vencimentos estão próximos

---

## Stack Tecnológica

| Camada | Tecnologia | Detalhe |
|--------|-----------|---------|
| Frontend | Vue.js 3 + TypeScript | Composition API, Pinia, Vue Router, Axios |
| Backend | FastAPI | 100% async, Pydantic v2, Python 3.12 |
| ORM | SQLAlchemy 2.0 async | Driver asyncpg para PostgreSQL |
| Banco | PostgreSQL | via Docker |
| Fila | Celery + Redis | Workers async, Beat scheduler |
| Email (dev) | Mailpit | Servidor SMTP fake com UI web |
| Migrations | Alembic | async-compatible |
| Build | Vite | Dev server em :5173 |

---

## Arquitetura em Camadas

```
┌─────────────────────────────────┐
│       Vue.js (SPA)              │  :5173
│  Pinia │ Vue Router │ Axios     │
└────────────────┬────────────────┘
                 │ HTTP/REST JSON
┌────────────────▼────────────────┐
│         FastAPI (ASGI)          │  :8000
│  Routers → Services → Models   │
│  JWT Auth │ CORS │ Pydantic     │
└────────────────┬────────────────┘
                 │ asyncpg
┌────────────────▼────────────────┐
│         PostgreSQL              │  :5432
└─────────────────────────────────┘

┌─────────────────────────────────┐
│  Celery Worker + Beat           │
│  Broker: Redis :6379            │
│  Tarefa diária às 09h           │
│  → envia emails de vencimento   │
└─────────────────────────────────┘
```

---

## Conceito de Multi-Tenancy

Cada **Tenant** representa um grupo (casa, república, família). Toda entidade principal tem um `tenant_id`, garantindo isolamento total dos dados entre grupos.

```
Tenant (ex: "República Alpha")
  ├── Usuários (João, Maria, Pedro)
  ├── Custos Fixos (Aluguel, Internet)
  └── Meses de Referência
        ├── 2026/01 → Custos → PagamentosRateio
        ├── 2026/02 → Custos → PagamentosRateio
        └── 2026/03 → Custos → PagamentosRateio
```

---

## Fluxo Típico de Uso

1. Admin cadastra o **Tenant** e os **Usuários**
2. Admin cadastra os **CustoFixo** (aluguel, internet, etc.)
3. Todo mês, ao acessar `/api/meses/tenant/{id}/atual`:
   - O sistema cria automaticamente o `MesReferencia` do mês corrente
   - Importa todos os `CustoFixo` ativos como `Custo` do tipo FIXO
4. Usuário adiciona eventuais **custos variáveis** (encanador, supermercado)
5. Usuário distribui cada custo entre os membros via **PagamentoRateio** (com validação de 100%)
6. Celery verifica diariamente vencimentos e **envia email** aos responsáveis

---

## Módulos do Projeto

```
app/
├── main.py              # FastAPI app, CORS, routers, health check
├── settings.py          # Configurações via .env (Pydantic Settings)
├── celery_app.py        # Celery config + beat schedule
├── auth/                # JWT, hashing, dependência CurrentUser
├── tenant/              # CRUD de tenants
├── usuario/             # CRUD de usuários
├── mes_referencia/      # Gestão de meses + importação automática
├── custo/               # Custos efetivos (FIXO ou VARIAVEL)
├── custo_fixo/          # Templates de custo recorrente
├── pagamento_rateio/    # Divisão de custo (validação ≤ 100%)
├── notificacao/         # Email service + tasks Celery
└── tests/               # Pytest + TestContainers + factories
```

---

Ver também: [[Modelos de Dados]] | [[Regras de Negócio]] | [[Módulos da API]]
