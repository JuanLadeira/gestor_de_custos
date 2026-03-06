# Ambiente de Desenvolvimento

[[Índice|← Índice]]

---

## Pré-requisitos

- Docker + Docker Compose
- Python 3.12+ (para rodar ferramentas localmente)
- `uv` (gerenciador de pacotes Python)
- Node.js 20+ (para o frontend)

---

## Setup Inicial

```bash
# 1. Clonar e entrar no projeto
cd gestor_de_custos

# 2. Copiar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# 3. Instalar dependências Python (para ferramentas locais)
uv sync

# 4. Subir todos os containers
task up
```

---

## Variáveis de Ambiente (.env)

```env
# Banco de dados
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/gestor_custos
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_DB=gestor_custos

# Autenticação
SECRET_KEY=chave-secreta-muito-segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Redis
REDIS_URL=redis://redis:6379/0

# Email
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_FROM_EMAIL=noreply@gestorcustos.local

# Notificações
DAYS_BEFORE_DUE_NOTIFICATION=3
```

---

## Tarefas Disponíveis (taskipy)

```bash
# Docker
task up              # docker compose up -d
task down            # docker compose down
task logs            # docker compose logs -f

# Desenvolvimento
task bash            # shell dentro do container app
task pysql           # psql direto no banco
task celery-logs     # logs do celery-worker e celery-beat

# Código
task lint            # ruff check app/
task format          # ruff format app/

# Testes
task test            # pytest
task test-coverage   # pytest com cobertura mínima de 90%

# Migrações
task revision -m "descrição"   # criar nova migration
task head                      # rodar todas as migrations
task migrate                   # alembic upgrade head (local)
```

---

## Migrações (Alembic)

Executadas automaticamente no startup do container via `entrypoint.sh`.

**Criar nova migration após alterar models:**
```bash
task bash
# dentro do container:
task revision -m "add campo X em custo"
```

**Rodar manualmente:**
```bash
task head   # aplica todas as migrations pendentes
```

**Arquivo de env:** `alembic/env.py` — usa engine async e importa todos os models.

> ⚠️ A migration atual (`404af90b75eb`) está desatualizada. Ver [[Pendências e Issues]].

---

## Gerenciamento de Dependências (uv)

```bash
# Adicionar dependência
uv add nome-pacote

# Adicionar dev dependency
uv add --dev nome-pacote

# Sincronizar ambiente
uv sync
```

Arquivo de lock: `uv.lock`
Configuração: `pyproject.toml`

---

## Linting e Formatação

```bash
task lint     # ruff check app/ → reporta problemas
task format   # ruff format app/ → formata código
```

Configurado em `pyproject.toml` com regras Ruff.

---

## Desenvolvimento do Frontend

O frontend é servido pelo container `frontend` via Vite em `:5173`. Alterações em `frontend/src/` são recarregadas automaticamente (hot reload).

Para rodar o frontend localmente (fora do Docker):
```bash
cd frontend
npm install
npm run dev
```

---

Ver também: [[Arquitetura de Containers]] | [[Testes]]
