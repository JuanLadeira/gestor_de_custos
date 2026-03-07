# Arquitetura de Containers

[[Índice|← Índice]]

---

## Serviços (docker-compose.yml)

| Serviço | Imagem | Porta(s) | Função |
|---------|--------|----------|--------|
| `db` | `postgres:latest` | 5432 | Banco de dados PostgreSQL |
| `redis` | `redis:7-alpine` | 6379 | Broker do Celery + backend de resultados |
| `mailpit` | `axllent/mailpit` | 1025 (SMTP), 8025 (UI) | SMTP fake para desenvolvimento |
| `app` | Custom | 8000 | FastAPI + Uvicorn |
| `celery-worker` | Custom | — | Processa tasks da fila |
| `celery-beat` | Custom | — | Agenda tasks periódicas |
| `frontend` | `node:20-alpine` | 5173 | Vue.js via Vite dev server |

---

## Dependências entre Serviços

```
db ──────────────┐
redis ───────────┼──▶ app (FastAPI)
                 │         └──▶ celery-worker
                 │         └──▶ celery-beat
mailpit ─────────┘

frontend ──▶ app (proxy via Vite)
```

---

## Health Checks

```yaml
db:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
    interval: 5s
    retries: 5

redis:
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 5s
    retries: 5
```

O serviço `app` aguarda `db` e `redis` estarem saudáveis antes de iniciar (via `depends_on: condition: service_healthy`).

---

## Entrypoint da Aplicação

**Arquivo:** `entrypoint.sh`

```bash
#!/bin/bash
1. python app/wait_for_db.py    # aguarda DB aceitar conexões
2. task migrate                 # executa migrações Alembic
3. uvicorn app.main:app \
     --host 0.0.0.0 \
     --port 8000 \
     --reload                  # hot reload em dev
```

---

## Volumes em Desenvolvimento

```yaml
app:
  volumes:
    - ./app:/code/app          # hot reload do código Python
    - /var/run/docker.sock:/var/run/docker.sock  # acesso ao Docker

frontend:
  volumes:
    - ./frontend/src:/app/src  # hot reload do Vue.js
```

---

## Produção

**Arquivo:** `docker-compose.production.yml`

Diferenças principais:
- Sem hot reload
- Variáveis de ambiente de produção
- Sem volumes de desenvolvimento
- Configurações SMTP reais

---

## Comandos Rápidos

```bash
# Iniciar ambiente
task up

# Parar ambiente
task down

# Ver logs de todos os serviços
task logs

# Acessar shell do container app
task bash

# Acessar psql do banco
task pysql

# Logs específicos do Celery
task celery-logs
```

---

## URLs de Desenvolvimento

| Serviço | URL |
|---------|-----|
| API FastAPI | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Frontend Vue.js | http://localhost:5173 |
| Mailpit (emails) | http://localhost:8025 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

---

Ver também: [[Ambiente de Desenvolvimento]] | [[Sistema de Notificações]]
