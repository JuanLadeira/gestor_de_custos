# Módulos da API

[[Índice|← Índice]]

Base URL: `http://localhost:8000`
Todos os endpoints (exceto `/auth/login` e `/health`) requerem `Authorization: Bearer <token>`.

---

## Health Check

| Método | Endpoint | Resposta |
|--------|----------|---------|
| GET | `/health` | `{"status": "healthy"}` |

---

## Auth

| Método | Endpoint | Corpo | Resposta |
|--------|----------|-------|---------|
| POST | `/auth/login` | form-data: `username`, `password` | `{access_token, token_type}` |

---

## Tenant `/api/tenants`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/tenants/` | Lista todos os tenants |
| GET | `/api/tenants/{id}` | Busca por ID |
| POST | `/api/tenants/` | Cria tenant → 201 |
| PUT | `/api/tenants/{id}` | Atualiza tenant |
| DELETE | `/api/tenants/{id}` | Remove tenant → 204 |

**Schemas:**
```json
// Create
{ "nome": "República Alpha", "descricao": "Casa na Vila Madalena" }

// Public
{ "id": 1, "nome": "...", "descricao": "...", "created_at": "...", "updated_at": "..." }
```

---

## Usuario `/api/usuarios`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/usuarios/?tenant_id=1` | Lista usuários (filtro opcional) |
| GET | `/api/usuarios/{id}` | Busca por ID |
| POST | `/api/usuarios/` | Cria usuário (valida username/email únicos) |
| PUT | `/api/usuarios/{id}` | Atualiza usuário |
| DELETE | `/api/usuarios/{id}` | Remove usuário |

**Schemas:**
```json
// Create
{
  "username": "joao",
  "email": "joao@email.com",
  "nome": "João Silva",
  "password": "senha123",
  "tenant_id": 1
}

// Public (sem password)
{ "id": 1, "username": "joao", "email": "...", "nome": "...", "ativo": true, "tenant_id": 1 }
```

**Erros comuns:**
- `400` — username ou email já existem

---

## MesReferencia `/api/meses`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/meses/?tenant_id=1` | Lista meses |
| **GET** | **`/api/meses/tenant/{tenant_id}/atual`** | **Obtém ou cria o mês atual (auto-importa fixos)** |
| GET | `/api/meses/{id}` | Busca por ID |
| POST | `/api/meses/` | Cria mês manualmente |
| PUT | `/api/meses/{id}` | Atualiza status (ABERTO/FECHADO) |
| DELETE | `/api/meses/{id}` | Remove mês |
| POST | `/api/meses/{id}/importar-custos-fixos` | Re-importa custos fixos manualmente |

**Resposta do endpoint `/atual`:**
```json
{
  "mes_referencia": { "id": 3, "ano": 2026, "mes": 3, "status": "ABERTO", ... },
  "custos_importados": 2,
  "foi_criado": true
}
```

**Validações de schema:**
- `mes`: 1-12
- `ano`: 2000-2100

---

## CustoFixo `/api/custos-fixos`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/custos-fixos/?tenant_id=1` | Lista templates |
| GET | `/api/custos-fixos/{id}` | Busca por ID |
| POST | `/api/custos-fixos/` | Cria template |
| PUT | `/api/custos-fixos/{id}` | Atualiza (ex: mudar valor ou desativar) |
| DELETE | `/api/custos-fixos/{id}` | Remove template |

**Schemas:**
```json
// Create
{
  "descricao": "Aluguel",
  "valor": 1200.00,
  "dia_vencimento": 5,
  "tenant_id": 1
}

// Public
{ "id": 1, "descricao": "Aluguel", "valor": "1200.00", "dia_vencimento": 5, "ativo": true, ... }
```

**Validações:**
- `valor` > 0
- `dia_vencimento`: 1-31

---

## Custo `/api/custos`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/custos/?mes_referencia_id=3` | Lista custos do mês |
| GET | `/api/custos/{id}` | Busca por ID (com rateios carregados) |
| POST | `/api/custos/` | Cria custo variável |
| PUT | `/api/custos/{id}` | Atualiza (ex: marcar como PAGO) |
| DELETE | `/api/custos/{id}` | Remove custo |

**Schemas:**
```json
// Create (custo variável)
{
  "descricao": "Encanador",
  "valor": 350.00,
  "data_vencimento": "2026-03-15",
  "tipo": "VARIAVEL",
  "mes_referencia_id": 3
}

// Tipos: FIXO | VARIAVEL
// Status: PENDENTE | PAGO
```

**Ordenação:** por `data_vencimento` (ascendente)

---

## PagamentoRateio `/api/rateios`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/rateios/?custo_id=1` | Lista rateios de um custo |
| GET | `/api/rateios/?usuario_id=2` | Lista rateios de um usuário |
| GET | `/api/rateios/{id}` | Busca por ID |
| POST | `/api/rateios/` | Cria rateio (valida ≤ 100%) |
| PUT | `/api/rateios/{id}` | Atualiza porcentagem (re-valida) |
| DELETE | `/api/rateios/{id}` | Remove rateio |

**Schemas:**
```json
// Create
{ "custo_id": 1, "usuario_id": 2, "porcentagem": 40 }

// Public
{
  "id": 5,
  "custo_id": 1,
  "usuario_id": 2,
  "porcentagem": "40.00",
  "valor_calculado": "480.00",  // calculado automaticamente
  "status": "PENDENTE"
}
```

**Erro 400 — excede 100%:**
```json
{
  "detail": "Soma das porcentagens excede 100%. Atual: 60%, Tentando adicionar: 55%, Total seria: 115%"
}
```

---

## Documentação Interativa

FastAPI gera automaticamente:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

---

Ver também: [[Regras de Negócio]] | [[Autenticação]] | [[Modelos de Dados]]
