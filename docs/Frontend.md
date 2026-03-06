# Frontend

[[Índice|← Índice]]

---

## Stack

| Tecnologia | Versão | Uso |
|-----------|--------|-----|
| Vue.js 3 | latest | Framework SPA (Composition API) |
| TypeScript | — | Type safety |
| Vite | — | Build tool + dev server |
| Pinia | — | Gerenciamento de estado |
| Vue Router | — | Roteamento client-side |
| Axios | — | Cliente HTTP |

---

## Estrutura de Arquivos

```
frontend/
├── src/
│   ├── main.ts               # Inicializa Vue app, monta plugins
│   ├── App.vue               # Componente raiz
│   ├── api/
│   │   └── client.ts         # Instância Axios + interceptors + interfaces + métodos
│   ├── router/
│   │   └── index.ts          # Definição de rotas + navigation guard
│   ├── stores/
│   │   └── auth.ts           # Pinia store: token, username, login, logout
│   └── views/
│       ├── HomeView.vue
│       ├── LoginView.vue
│       ├── CustosView.vue    # Gestão de custos do mês
│       └── RateiosView.vue   # Gestão de rateios
├── package.json
├── vite.config.ts
└── tsconfig.json
```

---

## Rotas

| Path | Nome | Proteção |
|------|------|---------|
| `/` | `home` | Pública |
| `/login` | `login` | Pública |
| `/custos` | `custos` | `requiresAuth: true` |
| `/rateios` | `rateios` | `requiresAuth: true` |

**Navigation Guard:**
```typescript
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})
```

---

## Auth Store (Pinia)

```typescript
// stores/auth.ts
const token = ref<string | null>(localStorage.getItem('token'))
const username = ref<string | null>(localStorage.getItem('username'))
const isAuthenticated = computed(() => !!token.value)

async function login(username: string, password: string) {
  // POST /auth/login (form-data)
  // Salva token + username no localStorage
  // router.push('/')
}

function logout() {
  // Limpa state + localStorage
  // router.push('/login')
}
```

**Persistência:** localStorage — sobrevive a recargas de página.

---

## API Client

```typescript
// api/client.ts
const apiClient = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})
```

**Interceptors:**
- **Request:** injeta `Authorization: Bearer <token>` automaticamente
- **Response:** em erro 401 → limpa token e redireciona para `/login`

**Interfaces TypeScript:**

```typescript
interface Tenant      { id, nome, descricao, created_at, updated_at }
interface Usuario     { id, username, email, nome, ativo, tenant_id }
interface Custo       { id, descricao, valor, data_vencimento, tipo, status, mes_referencia_id, custo_fixo_origem_id }
interface PagamentoRateio { id, porcentagem, valor_calculado, status, custo_id, usuario_id }
```

**Métodos disponíveis:**

```typescript
api.login(username, password)
api.getTenants()
api.createTenant(data)
api.getUsuarios(tenantId?)
api.getCustos(mesReferenciaId?)
api.createCusto(data)
api.updateCusto(id, data)
api.deleteCusto(id)
api.getRateios(custoId?, usuarioId?)
api.createRateio(data)
api.updateRateio(id, data)
api.deleteRateio(id)
api.getMesAtual(tenantId)
```

---

## Comunicação com a API

O Vite em dev usa proxy para evitar CORS:

```typescript
// vite.config.ts (inferido)
server: {
  proxy: {
    '/api': 'http://app:8000'
  }
}
```

O backend também aceita origem `http://localhost:5173` e `http://frontend:5173` via CORS middleware.

---

## Status de Implementação

| Funcionalidade | Status |
|---------------|--------|
| Login / Logout | Implementado |
| Autenticação JWT | Implementado |
| API Client base | Implementado |
| Roteamento + guards | Implementado |
| Estado de auth | Implementado |
| UI de Custos | Estrutura básica |
| UI de Rateios | Estrutura básica |
| UI de Tenants | Pendente |
| UI de Usuários | Pendente |
| Gestão de meses | Pendente |
| Componentes de formulário | Pendente |
| Feedback de erro (UI) | Pendente |

---

Ver também: [[Autenticação]] | [[Módulos da API]] | [[Pendências e Issues]]
