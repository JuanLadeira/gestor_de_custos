# Gestor de Custos

Plataforma SaaS multi-tenant para gestão de custos compartilhados e comunicação via WhatsApp. Permite que grupos (tenants) registrem custos fixos, calculem rateios entre membros e se comuniquem em massa ou individualmente por WhatsApp por meio de campanhas automatizadas.

## Visão Geral

### Módulos principais

| Módulo | Descrição |
|--------|-----------|
| **Custos & Rateios** | Registro de custos fixos e variáveis por mês de referência, com cálculo automático de rateio entre os membros do tenant |
| **WhatsApp** | Integração com a [Evolution API](https://github.com/EvolutionAPI/evolution-api) para gerenciar instâncias WhatsApp por tenant (conectar, desconectar, enviar mensagens de texto e mídia) |
| **Campanhas** | Disparos em massa com rate limiting por instância, templates Jinja2 personalizados por contato, data sources externos (HTTP) para enriquecimento de variáveis e horários configuráveis |
| **Inbox** | Caixa de entrada para atendimento manual das conversas iniciadas pelas campanhas, com histórico de mensagens e status de atendimento |
| **Admin** | Painel global (sem tenant) para gerenciar tenants, planos de assinatura e assinaturas |
| **Assinaturas** | Planos e assinaturas por tenant com integração ao Stripe (checkout e webhooks) |

### Arquitetura

```
gestor_de_custos/
├── app/                        # Backend FastAPI
│   ├── admin/                  # Painel administrativo global
│   ├── assinatura/             # Assinaturas por tenant
│   ├── auth/                   # JWT, login, dependências (CurrentUser / CurrentOwner)
│   ├── campanha/               # Campanhas WhatsApp + Inbox (models, schemas, services, router, tasks)
│   ├── custo/                  # Custos por mês de referência (FIXO | VARIAVEL)
│   ├── custo_fixo/             # Templates de custos recorrentes
│   ├── database/               # Configuração do SQLAlchemy async (Base + sessão)
│   ├── mes_referencia/         # Meses de referência (auto-importa custos fixos)
│   ├── notificacao/            # E-mails + tarefas Celery (lembretes de vencimento)
│   ├── pagamento_rateio/       # Rateio por membro (% ≤ 100) + comprovantes
│   ├── plano/                  # Planos de assinatura
│   ├── stripe_webhooks/        # Checkout + webhooks do Stripe
│   ├── tenant/                 # Modelo de tenant
│   ├── usuario/                # Usuários (OWNER / MEMBER)
│   ├── whatsapp/               # Instâncias WhatsApp + webhook (Evolution API)
│   ├── celery_app.py           # App Celery + beat schedule
│   ├── main.py                 # Entrypoint FastAPI (registro de routers, CORS)
│   └── settings.py             # Configurações via env vars
├── alembic/                    # Migrações do banco de dados
├── frontend/                   # Frontend Vue 3 + TypeScript + Vite
│   └── src/
│       ├── views/              # Telas: Custos, Rateios, Campanhas, Inbox, Admin...
│       ├── router/             # Vue Router (rotas protegidas por auth)
│       └── api/                # Axios client com interceptor JWT
├── scripts/                    # Scripts utilitários (populate_data, etc.)
├── docker-compose.yml          # Ambiente de desenvolvimento
├── Taskfile.yml                # Atalhos de tarefas (task up, task head, task test...)
└── pyproject.toml              # Dependências Python (uv)
```

## Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy async, Alembic, PostgreSQL
- **Frontend:** Vue 3, TypeScript, Vite, Pinia, Axios, Tailwind CSS
- **Filas:** Celery + Redis (beat para campanhas a cada 60s)
- **WhatsApp:** Evolution API (self-hosted)
- **Pagamentos:** Stripe
- **Containers:** Docker + Docker Compose
- **Runtime Python:** `uv`

## Pré-requisitos

- [Docker](https://www.docker.com/get-started) e [Docker Compose](https://docs.docker.com/compose/install/)
- [Task](https://taskfile.dev/) (opcional, para usar os atalhos)

## Configuração

1. Copie o arquivo de variáveis de ambiente:

```bash
cp .env.example .env
```

2. Edite o `.env` com os valores do seu ambiente. Variáveis obrigatórias para funcionalidade completa:

| Variável | Descrição |
|----------|-----------|
| `SECRET_KEY` | Chave JWT (gere com `openssl rand -hex 32`) |
| `DATABASE_URL` | URL do PostgreSQL |
| `REDIS_URL` | URL do Redis |
| `EVOLUTION_API_URL` | URL da instância Evolution API |
| `EVOLUTION_API_KEY` | Chave de acesso à Evolution API |
| `STRIPE_SECRET_KEY` | Chave secreta do Stripe (opcional) |
| `STRIPE_WEBHOOK_SECRET` | Secret do webhook do Stripe (opcional) |

## Rodando em desenvolvimento

```bash
# Subir todos os serviços (app, postgres, redis, celery worker, celery beat)
task up

# Aplicar migrações
task head

# Ver logs
task logs

# Rodar testes
task test

# Abrir shell no container da app
task bash

# Parar tudo
task down
```

Sem o `task`, use diretamente:

```bash
docker compose up -d --build
docker compose exec app alembic upgrade head
```

## Acessos

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API (Swagger) | http://localhost:8000/docs |
| API (ReDoc) | http://localhost:8000/redoc |

## Multi-tenancy

Cada **Tenant** representa um grupo (empresa, república, condomínio, etc.). Usuários pertencem a um único tenant e têm papel de `OWNER` ou `MEMBER`. O admin global (sem tenant) gerencia planos e assinaturas.

## Campanhas WhatsApp

O módulo de campanhas permite:

1. **Criar uma campanha** com nome, horário de disparo e instâncias WhatsApp
2. **Configurar templates** Jinja2 — as variáveis `{{ numero }}` e `{{ nome }}` estão sempre disponíveis; outras vêm do Data Source
3. **Data Source** — enriquece cada contato com dados de uma API externa ou de endpoints internos do sistema (com injeção automática de token)
4. **Importar contatos** individualmente ou em massa
5. **Ativar** — o Celery beat processa a campanha a cada 60s, respeitando rate limit por instância e janela de horário
6. **Logs de envio** — acompanhe em tempo real o status de cada contato (Pendente → Enviando → Enviado / Falhou)
7. **Inbox** — respostas recebidas via webhook formam conversas para atendimento manual

## Estrutura de banco de dados

As migrações estão em `alembic/versions/`. A cadeia atual:

```
404af90b75eb  initial
  → b1a2c3d4e5f6  create_base_schema
  → c2d3e4f5a6b7  add_role_to_usuario
  → d3e4f5a6b7c8  add_saas_models
  → e4f5a6b7c8d9  add_status_to_mes_referencia
  → f5a6b7c8d9e0  rename_enum_types
  → g5h6i7j8k9l0  add_parcialmente_pago_and_comprovante
  → h6i7j8k9l0m1  add_whatsapp_instancia
  → i7j8k9l0m1n2  add_campanha_module
```
