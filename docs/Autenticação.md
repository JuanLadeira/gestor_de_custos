# Autenticação

[[Índice|← Índice]]

---

## Stack

| Componente | Tecnologia |
|-----------|-----------|
| Token | JWT (PyJWT) |
| Algoritmo | HS256 |
| Hashing | Argon2 (pwdlib) |
| OAuth2 | `OAuth2PasswordBearer` do FastAPI |

---

## Fluxo de Login

```
1. POST /auth/login
   Body (form-data): username=joao, password=senha123

2. Backend:
   a. Busca usuario pelo username
   b. verify_password(plain, hashed) → Argon2
   c. Se inválido → 401 Unauthorized

3. create_access_token({ "sub": username })
   → exp = now + ACCESS_TOKEN_EXPIRE_MINUTES

4. Retorna:
   { "access_token": "<JWT>", "token_type": "bearer" }

5. Frontend armazena token no localStorage
```

---

## Dependências FastAPI

### `get_current_user` (current_user.py)

```python
async def get_current_user(token: str = Depends(oauth2_scheme)) -> Usuario:
    payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    user = await service.get_by_username(username)
    if not user:
        raise HTTPException(401, "Could not validate credentials")
    return user

# Alias usado nos routers:
CurrentUser = Annotated[Usuario, Depends(get_current_user)]
```

### Uso nos endpoints

```python
@router.get("/api/custos/")
async def list_custos(
    current_user: CurrentUser,   # ← injeta usuário autenticado
    service: CustoServiceDep,
):
    ...
```

---

## Configurações (.env)

```env
SECRET_KEY=sua-chave-secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## Segurança de Senhas

- Hash: **Argon2** (resistente a ataques de força bruta/GPU)
- Implementado via `pwdlib[argon2]`
- Funções em `app/auth/security.py`:
  - `get_password_hash(password: str) -> str`
  - `verify_password(plain: str, hashed: str) -> bool`

---

## Schemas

```python
# app/auth/schemas.py
class Token(BaseModel):
    acess_token: str   # ⚠️ typo conhecido: "acess" em vez de "access"
    token_type: str
```

> **Pendência:** corrigir o typo `acess_token` → `access_token`. Ver [[Pendências e Issues]].

---

## Frontend — Interceptor Axios

```typescript
// Adiciona token em todas as requisições
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Redireciona para login em 401
apiClient.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

---

Ver também: [[Módulos da API]] | [[Frontend]]
