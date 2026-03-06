# Testes

[[Índice|← Índice]]

---

## Stack de Testes

| Tecnologia | Uso |
|-----------|-----|
| `pytest` + `pytest-asyncio` | Framework + suporte async |
| `testcontainers` | PostgreSQL real em container isolado por teste |
| `pytest-factoryboy` | Integração de factories com fixtures |
| `factory_boy` | Geração de dados de teste |
| `httpx.AsyncClient` | Cliente HTTP assíncrono para testar endpoints |
| `freezegun` | Mock de tempo (para testar datas) |
| `pytest-cov` | Cobertura de código (mínimo 90%) |

---

## Configuração Base (conftest.py)

### Banco de dados isolado

```python
@pytest.fixture(scope="session")
async def async_engine():
    # Sobe um container PostgreSQL real via testcontainers
    # Cria todas as tabelas (Base.metadata.create_all)
    # Dropa ao final da sessão
    with PostgresContainer("postgres:latest") as postgres:
        engine = create_async_engine(postgres.get_connection_url())
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
```

### Fixtures principais

| Fixture | Escopo | O que provê |
|---------|--------|------------|
| `async_engine` | session | Engine com DB real em container |
| `session` | function | AsyncSession com rollback após cada teste |
| `client` | function | `AsyncClient` com override de dependências |
| `tenant` | function | Tenant criado via factory |
| `usuario` | function | Usuário criado via factory (no tenant acima) |
| `token` | function | JWT gerado via POST /auth/login |
| `auth_headers` | function | `{"Authorization": "Bearer <token>"}` |

---

## Factories

### TenantFactory

```python
class TenantFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Tenant

    nome = factory.Faker("company", locale="pt_BR")
    descricao = factory.Faker("catch_phrase", locale="pt_BR")
```

### UsuarioFactory

```python
class UsuarioFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Usuario

    username  = factory.Faker("user_name")
    email     = factory.Faker("email")
    password  = factory.Faker("password")
    nome      = factory.Faker("name", locale="pt_BR")
    ativo     = True
    tenant    = factory.SubFactory(TenantFactory)
    tenant_id = factory.LazyAttribute(lambda obj: obj.tenant.id)
```

---

## Suítes de Teste

### test_tenant — CRUD de Tenants

```python
@pytest.mark.tenant
class TestTenantEndpoints:
    async def test_create_tenant()          # POST → 201
    async def test_get_tenant()             # GET → 200
    async def test_get_tenant_not_found()   # GET → 404
    async def test_list_tenants()           # GET list → 200
    async def test_update_tenant()          # PUT → 200
    async def test_delete_tenant()          # DELETE → 204
```

### test_rateio — Validação de 100%

```python
@pytest.mark.rateio
class TestRateioValidation:
    async def test_create_rateio_success()
    # ✅ 60% de R$1000 = R$600 calculado corretamente

    async def test_create_multiple_rateios_within_limit()
    # ✅ 60% + 40% = 100% → ambos aceitos

    async def test_create_rateio_exceeds_100_percent()
    # ❌ 60% + 55% = 115% → 400 com mensagem detalhada

    async def test_update_rateio_exceeds_100_percent()
    # ❌ dois rateios de 50%, tentar atualizar um para 60% → 400

    async def test_update_rateio_within_limit()
    # ✅ 50% atualizado para 70% (único rateio) → aceito

    async def test_rateio_porcentagem_validation()
    # ❌ 0% → 422 (schema validation)
    # ❌ 101% → 422 (schema validation)
```

**Helper de setup:**
```python
async def _create_test_data(client):
    # Cria: tenant, 2 usuários, mes_referencia, custo (Aluguel R$1000 FIXO)
    # Retorna dict com todos os objetos criados
```

---

## Marcadores

```ini
# pyproject.toml
markers = [
    "tenant: testes de tenant",
    "usuario: testes de usuario",
    "custo: testes de custo",
    "rateio: testes de rateio",
]
```

**Executar por marcador:**
```bash
task test -m rateio
task test -m tenant
```

---

## Comandos

```bash
# Rodar todos os testes
task test

# Com cobertura (mínimo 90%)
task test-coverage

# Específico
task test -k "test_create_rateio"
task test -m rateio

# Verbose
task test -v
```

---

## Cobertura Mínima

O target é **90%** de cobertura. Configurado em:
```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-fail-under=90"
```

---

Ver também: [[Regras de Negócio]] | [[Módulos da API]] | [[Ambiente de Desenvolvimento]]
