# RBAC + Tenant Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add role-based access control (permissions → roles → role-profiles, per tenant) and close the tenant-isolation hole so every cost-domain endpoint is authenticated, permission-checked, and scoped to the caller's tenant.

**Architecture:** New `app/authz/` package holds a global permission catalog (code), per-tenant `Role`/`RoleProfile` models, an `AuthzService` (resolve/seed/CRUD), and a `require(*codes)` FastAPI dependency. The open cost-domain routers gain `CurrentUser` + `require(...)` and derive `tenant_id` from the JWT instead of from client input. Frontend consumes `/me` permissions to gate UI.

**Tech Stack:** FastAPI, async SQLAlchemy 2.0, Alembic, PostgreSQL, Vue 3 + TS + Pinia, pytest (testcontainers).

## Global Constraints

- Python `>=3.11`; async SQLAlchemy only (`session.add` + `await session.flush()`; never sync commit in services).
- Tests: factory_boy does NOT work with async — use direct async fixtures (`session.add(obj); await session.flush()`). For 404-after-delete assertions: `await session.flush(); session.expunge_all()` before `session.get()`.
- Postgres enum gotcha (only relevant when dropping the old enum): use module-level `sa.Enum(..., name="usuariorole")` and drop the type explicitly after dropping the column.
- Permissions are resource-type level (`recurso:acao`); no own/any scoping.
- `tenant_id` is ALWAYS derived from `current_user.tenant_id`. Never accept it from query params or request bodies for scoping.
- Cross-tenant resource access returns **404** (not 403). Missing permission returns **403**.
- Migration chain head is `i7j8k9l0m1n2`; the new migration's `down_revision` is `"i7j8k9l0m1n2"`, `revision` is `"j8k9l0m1n2o3"`.
- Branch: `feat/rbac-tenant-isolation` (already created).
- Commit messages end with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

---

## File Structure

**New (`app/authz/`):**
- `__init__.py` — empty package marker
- `catalog.py` — pure data: permission list, default roles, default profiles + helpers
- `models.py` — `Permission`, `Role`, `RoleProfile`, association tables
- `service.py` — `AuthzService`
- `dependencies.py` — `get_current_permissions`, `require(*codes)`
- `schemas.py` — authz request/response models
- `router.py` — `/api/authz` OWNER CRUD + `GET /permissions`

**Modified:**
- `app/usuario/models.py`, `schemas.py`, `services.py`, `router.py`
- `app/auth/current_user.py` (remove `require_owner`/`CurrentOwner`)
- `app/tenant/services.py`, `router.py`
- `app/mes_referencia/services.py`, `router.py`
- `app/custo/services.py`, `router.py`
- `app/custo_fixo/services.py`, `router.py`
- `app/pagamento_rateio/services.py`, `router.py`
- `app/whatsapp/router.py`, `app/campanha/router.py` (add `require`)
- `app/stripe_webhooks/handlers.py`, `app/admin/router.py`, `scripts/populate_data.py`
- `app/main.py` (register authz router)
- `alembic/versions/j8k9l0m1n2o3_add_rbac.py` (new)
- `pyproject.toml` (add `authz` marker)
- Frontend: `api/client.ts`, `stores/auth.ts`, `router/index.ts`, `App.vue`, `views/UsuariosView.vue`, `views/RolesView.vue` (new), plus button gating in cost/campaign views.

---

# Phase 1 — Core authz

### Task 1: Permission catalog (pure data)

**Files:**
- Create: `app/authz/__init__.py`
- Create: `app/authz/catalog.py`
- Test: `app/tests/test_authz/__init__.py`, `app/tests/test_authz/test_catalog.py`

**Interfaces:**
- Produces:
  - `PERMISSIONS: list[tuple[str, str, str]]` — `(code, grupo, descricao)`
  - `all_codes() -> list[str]`
  - `codes_for_grupos(*grupos: str) -> list[str]`
  - `read_codes() -> list[str]` — every code ending in `:read`
  - `DEFAULT_ROLES: dict[str, list[str]]` — role name → permission codes
  - `DEFAULT_PROFILES: dict[str, dict]` — profile name → `{"roles": list[str], "is_protected": bool}`

- [ ] **Step 1: Write the failing test**

`app/tests/test_authz/__init__.py`: empty file.

`app/tests/test_authz/test_catalog.py`:
```python
import pytest

from app.authz import catalog


@pytest.mark.authz
def test_all_codes_unique_and_nonempty():
    codes = catalog.all_codes()
    assert len(codes) == len(set(codes))
    assert "custo:create" in codes
    assert "rateio:pay" in codes


@pytest.mark.authz
def test_codes_for_grupos_filters():
    custo_codes = catalog.codes_for_grupos("custo")
    assert "custo:create" in custo_codes
    assert "rateio:pay" not in custo_codes


@pytest.mark.authz
def test_read_codes_only_reads():
    assert all(c.endswith(":read") for c in catalog.read_codes())
    assert "custo:read" in catalog.read_codes()


@pytest.mark.authz
def test_default_roles_reference_real_codes():
    valid = set(catalog.all_codes())
    for role, codes in catalog.DEFAULT_ROLES.items():
        for c in codes:
            assert c in valid, f"role {role} references unknown code {c}"


@pytest.mark.authz
def test_default_profiles_reference_real_roles():
    role_names = set(catalog.DEFAULT_ROLES)
    assert "Dono" in catalog.DEFAULT_PROFILES
    assert catalog.DEFAULT_PROFILES["Dono"]["is_protected"] is True
    for profile, spec in catalog.DEFAULT_PROFILES.items():
        for r in spec["roles"]:
            assert r in role_names, f"profile {profile} references unknown role {r}"


@pytest.mark.authz
def test_dono_profile_covers_all_permissions():
    # The Dono profile's roles must union to the full catalog.
    dono_roles = catalog.DEFAULT_PROFILES["Dono"]["roles"]
    covered = set()
    for r in dono_roles:
        covered.update(catalog.DEFAULT_ROLES[r])
    assert covered == set(catalog.all_codes())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `task test -- app/tests/test_authz/test_catalog.py -v` (or `docker compose exec app pytest app/tests/test_authz/test_catalog.py -v`)
Expected: FAIL — `ModuleNotFoundError: app.authz`.

- [ ] **Step 3: Write the catalog**

`app/authz/__init__.py`: empty.

`app/authz/catalog.py`:
```python
"""Global permission catalog and per-tenant default roles/profiles.

Pure data — no imports of app models, so Alembic migrations can import it
without triggering circular imports.
"""

# (code, grupo, descricao)
PERMISSIONS: list[tuple[str, str, str]] = [
    ("tenant:read", "tenant", "Ver dados do tenant"),
    ("tenant:update", "tenant", "Editar dados do tenant"),
    ("usuario:read", "usuario", "Listar/ver usuários"),
    ("usuario:create", "usuario", "Convidar usuários"),
    ("usuario:update", "usuario", "Editar usuários"),
    ("usuario:delete", "usuario", "Remover usuários"),
    ("role:read", "authz", "Ver papéis"),
    ("role:manage", "authz", "Criar/editar/excluir papéis"),
    ("profile:read", "authz", "Ver perfis"),
    ("profile:manage", "authz", "Criar/editar/excluir perfis"),
    ("profile:assign", "authz", "Atribuir perfil a usuários"),
    ("custo:read", "custo", "Ver custos"),
    ("custo:create", "custo", "Criar custos"),
    ("custo:update", "custo", "Editar custos"),
    ("custo:delete", "custo", "Remover custos"),
    ("custo_fixo:read", "custo_fixo", "Ver custos fixos"),
    ("custo_fixo:create", "custo_fixo", "Criar custos fixos"),
    ("custo_fixo:update", "custo_fixo", "Editar custos fixos"),
    ("custo_fixo:delete", "custo_fixo", "Remover custos fixos"),
    ("mes:read", "mes", "Ver meses de referência"),
    ("mes:create", "mes", "Criar meses de referência"),
    ("mes:update", "mes", "Editar meses de referência"),
    ("mes:import_fixos", "mes", "Importar custos fixos no mês"),
    ("rateio:read", "rateio", "Ver rateios"),
    ("rateio:create", "rateio", "Criar rateios"),
    ("rateio:update", "rateio", "Editar rateios"),
    ("rateio:delete", "rateio", "Remover rateios"),
    ("rateio:pay", "rateio", "Marcar rateio como pago"),
    ("comprovante:upload", "rateio", "Enviar comprovante"),
    ("whatsapp:read", "whatsapp", "Ver instâncias WhatsApp"),
    ("whatsapp:manage", "whatsapp", "Criar/excluir instâncias WhatsApp"),
    ("whatsapp:send", "whatsapp", "Enviar mensagens WhatsApp"),
    ("campanha:read", "campanha", "Ver campanhas"),
    ("campanha:create", "campanha", "Criar campanhas"),
    ("campanha:update", "campanha", "Editar campanhas"),
    ("campanha:delete", "campanha", "Remover campanhas"),
    ("campanha:activate", "campanha", "Ativar/pausar/concluir campanhas"),
    ("inbox:read", "inbox", "Ver conversas"),
    ("inbox:reply", "inbox", "Responder conversas"),
    ("inbox:manage", "inbox", "Encerrar conversas"),
    ("assinatura:read", "assinatura", "Ver assinatura"),
]


def all_codes() -> list[str]:
    return [code for code, _, _ in PERMISSIONS]


def codes_for_grupos(*grupos: str) -> list[str]:
    wanted = set(grupos)
    return [code for code, grupo, _ in PERMISSIONS if grupo in wanted]


def read_codes() -> list[str]:
    return [code for code in all_codes() if code.endswith(":read")]


# role name -> permission codes
DEFAULT_ROLES: dict[str, list[str]] = {
    "Administração": codes_for_grupos("tenant", "usuario", "authz") + ["assinatura:read"],
    "Financeiro": codes_for_grupos("custo", "custo_fixo", "mes", "rateio"),
    "Atendimento": codes_for_grupos("whatsapp", "campanha", "inbox"),
    "Leitura": read_codes(),
    # auxiliary role so the Membro profile gets exactly the right grants
    "Membro Base": ["rateio:pay", "comprovante:upload", "inbox:reply", "campanha:read"],
    # auxiliary role for Gestor's lighter management grants
    "Gestão Leve": ["usuario:read", "profile:assign"],
}

# profile name -> roles + flags
DEFAULT_PROFILES: dict[str, dict] = {
    "Dono": {
        "roles": ["Administração", "Financeiro", "Atendimento", "Leitura",
                  "Membro Base", "Gestão Leve"],
        "is_protected": True,
    },
    "Gestor": {
        "roles": ["Financeiro", "Atendimento", "Leitura", "Gestão Leve"],
        "is_protected": False,
    },
    "Membro": {
        "roles": ["Leitura", "Membro Base"],
        "is_protected": False,
    },
    "Leitor": {
        "roles": ["Leitura"],
        "is_protected": False,
    },
}
```

> Note: the `Dono` profile lists every role, and `Administração ∪ Financeiro ∪ Atendimento ∪ Leitura ∪ Membro Base ∪ Gestão Leve` equals the full catalog, satisfying `test_dono_profile_covers_all_permissions`.

- [ ] **Step 4: Register the `authz` pytest marker**

Modify `pyproject.toml`, in `[tool.pytest.ini_options].markers`, add the line:
```toml
    "authz: testes de RBAC e isolamento de tenant",
```

- [ ] **Step 5: Run test to verify it passes**

Run: `task test -- app/tests/test_authz/test_catalog.py -v`
Expected: PASS (6 tests).

- [ ] **Step 6: Commit**

```bash
git add app/authz/__init__.py app/authz/catalog.py app/tests/test_authz/ pyproject.toml
git commit -m "feat(authz): permission catalog + default roles/profiles

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: authz models

**Files:**
- Create: `app/authz/models.py`
- Test: `app/tests/test_authz/test_models.py`

**Interfaces:**
- Consumes: `app.database.base.Base`.
- Produces:
  - `Permission(Base)` — `code: str`, `grupo: str`, `descricao: str | None`
  - `Role(Base)` — `tenant_id: int`, `nome: str`, `descricao: str | None`, `is_system: bool`, `permissions: list[Permission]`
  - `RoleProfile(Base)` — `tenant_id: int`, `nome: str`, `descricao: str | None`, `is_system: bool`, `is_protected: bool`, `roles: list[Role]`
  - association tables `role_permission`, `role_profile_role`

- [ ] **Step 1: Write the failing test**

`app/tests/test_authz/test_models.py`:
```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz.models import Permission, Role, RoleProfile
from app.tenant.models import Tenant


@pytest.mark.authz
async def test_profile_role_permission_chain(session: AsyncSession):
    tenant = Tenant(nome="T1")
    session.add(tenant)
    await session.flush()

    perm = Permission(code="custo:read", grupo="custo", descricao="x")
    session.add(perm)
    await session.flush()

    role = Role(tenant_id=tenant.id, nome="Leitura", is_system=True)
    role.permissions.append(perm)
    session.add(role)
    await session.flush()

    profile = RoleProfile(tenant_id=tenant.id, nome="Leitor", is_system=True)
    profile.roles.append(role)
    session.add(profile)
    await session.flush()
    await session.refresh(profile)

    assert profile.roles[0].permissions[0].code == "custo:read"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `task test -- app/tests/test_authz/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: app.authz.models`.

- [ ] **Step 3: Write the models**

`app/authz/models.py`:
```python
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    pass


role_permission = Table(
    "role_permission",
    Base.metadata,
    Column("role_id", ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permission.id", ondelete="CASCADE"), primary_key=True),
)

role_profile_role = Table(
    "role_profile_role",
    Base.metadata,
    Column("role_profile_id", ForeignKey("role_profile.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(Base):
    __tablename__ = "permission"

    code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    grupo: Mapped[str] = mapped_column(String(50), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Role(Base):
    __tablename__ = "role"
    __table_args__ = (UniqueConstraint("tenant_id", "nome", name="uq_role_tenant_nome"),)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    permissions: Mapped[list["Permission"]] = relationship(
        secondary=role_permission, lazy="selectin"
    )


class RoleProfile(Base):
    __tablename__ = "role_profile"
    __table_args__ = (UniqueConstraint("tenant_id", "nome", name="uq_profile_tenant_nome"),)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_protected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    roles: Mapped[list["Role"]] = relationship(
        secondary=role_profile_role, lazy="selectin"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `task test -- app/tests/test_authz/test_models.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/authz/models.py app/tests/test_authz/test_models.py
git commit -m "feat(authz): Permission/Role/RoleProfile models

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: AuthzService — seed_global_permissions + resolve_permissions

**Files:**
- Create: `app/authz/service.py`
- Test: `app/tests/test_authz/test_service_resolve.py`

**Interfaces:**
- Consumes: `app.authz.models`, `app.authz.catalog`, `app.usuario.models.Usuario`, `app.database.AsyncDBSession`.
- Produces (on `AuthzService`):
  - `async seed_global_permissions() -> None` — idempotent upsert of catalog into `permission`.
  - `async resolve_permissions(user: Usuario) -> set[str]` — effective permission codes via profile→roles→permissions.
  - `get_authz_service(session) -> AuthzService` and `AuthzServiceDep` annotated dependency.

- [ ] **Step 1: Write the failing test**

`app/tests/test_authz/test_service_resolve.py`:
```python
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz.models import Permission, Role, RoleProfile
from app.authz.service import AuthzService
from app.tenant.models import Tenant
from app.usuario.models import Usuario


@pytest.mark.authz
async def test_seed_global_permissions_idempotent(session: AsyncSession):
    svc = AuthzService(session)
    await svc.seed_global_permissions()
    await svc.seed_global_permissions()  # twice
    rows = (await session.execute(select(Permission))).scalars().all()
    codes = [r.code for r in rows]
    assert len(codes) == len(set(codes))
    assert "custo:create" in codes


@pytest.mark.authz
async def test_resolve_permissions_union(session: AsyncSession):
    svc = AuthzService(session)
    await svc.seed_global_permissions()

    tenant = Tenant(nome="T")
    session.add(tenant)
    await session.flush()

    p_read = (await session.execute(select(Permission).where(Permission.code == "custo:read"))).scalar_one()
    p_pay = (await session.execute(select(Permission).where(Permission.code == "rateio:pay"))).scalar_one()

    r1 = Role(tenant_id=tenant.id, nome="A")
    r1.permissions.append(p_read)
    r2 = Role(tenant_id=tenant.id, nome="B")
    r2.permissions.append(p_pay)
    session.add_all([r1, r2])
    await session.flush()

    profile = RoleProfile(tenant_id=tenant.id, nome="P")
    profile.roles.extend([r1, r2])
    session.add(profile)
    await session.flush()

    user = Usuario(username="u", email="u@e.com", password="x", nome="U",
                   tenant_id=tenant.id, role_profile_id=profile.id)
    session.add(user)
    await session.flush()

    perms = await svc.resolve_permissions(user)
    assert perms == {"custo:read", "rateio:pay"}
```

> This test references `Usuario.role_profile_id`, added in Task 6. Until then it fails to construct `Usuario`. Run order: implement Task 3's service code now; this resolve test will pass once Task 6 lands. To keep Task 3 green on its own, only the seed test must pass now — mark the resolve test `@pytest.mark.xfail(reason="needs role_profile_id (Task 6)", strict=False)` and remove the xfail in Task 6.

- [ ] **Step 2: Add the temporary xfail to `test_resolve_permissions_union`**

Prepend the decorator directly above `async def test_resolve_permissions_union`:
```python
@pytest.mark.xfail(reason="needs role_profile_id (Task 6)", strict=False)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `task test -- app/tests/test_authz/test_service_resolve.py -v`
Expected: `test_seed_global_permissions_idempotent` FAILs (`ModuleNotFoundError: app.authz.service`); resolve test xfails.

- [ ] **Step 4: Write the service**

`app/authz/service.py`:
```python
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz import catalog
from app.authz.models import Permission, Role, RoleProfile, role_permission, role_profile_role
from app.database import AsyncDBSession
from app.usuario.models import Usuario


class AuthzService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def seed_global_permissions(self) -> None:
        existing = {
            row.code
            for row in (await self.session.execute(select(Permission))).scalars().all()
        }
        for code, grupo, descricao in catalog.PERMISSIONS:
            if code not in existing:
                self.session.add(Permission(code=code, grupo=grupo, descricao=descricao))
        await self.session.flush()

    async def resolve_permissions(self, user: Usuario) -> set[str]:
        query = (
            select(Permission.code)
            .select_from(RoleProfile)
            .join(role_profile_role, role_profile_role.c.role_profile_id == RoleProfile.id)
            .join(Role, Role.id == role_profile_role.c.role_id)
            .join(role_permission, role_permission.c.role_id == Role.id)
            .join(Permission, Permission.id == role_permission.c.permission_id)
            .where(RoleProfile.id == user.role_profile_id)
            .distinct()
        )
        result = await self.session.execute(query)
        return {row[0] for row in result}


def get_authz_service(session: AsyncDBSession) -> AuthzService:
    return AuthzService(session)


AuthzServiceDep = Annotated[AuthzService, Depends(get_authz_service)]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `task test -- app/tests/test_authz/test_service_resolve.py -v`
Expected: `test_seed_global_permissions_idempotent` PASS; resolve test XFAIL.

- [ ] **Step 6: Commit**

```bash
git add app/authz/service.py app/tests/test_authz/test_service_resolve.py
git commit -m "feat(authz): AuthzService seed + resolve permissions

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: `require()` dependency

**Files:**
- Create: `app/authz/dependencies.py`
- Test: `app/tests/test_authz/test_dependencies.py`

**Interfaces:**
- Consumes: `app.auth.current_user.CurrentUser`, `app.authz.service.AuthzServiceDep`.
- Produces:
  - `async get_current_permissions(request, current_user, service) -> set[str]` — resolves once, caches on `request.state.permissions`.
  - `CurrentPermissions = Annotated[set[str], Depends(get_current_permissions)]`
  - `require(*codes: str) -> Callable` — FastAPI dependency raising 403 if any code missing.

- [ ] **Step 1: Write the failing test**

`app/tests/test_authz/test_dependencies.py`:
```python
import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from app.auth.security import create_access_token, get_password_hash
from app.authz.dependencies import require
from app.authz.service import AuthzService
from app.database.session import get_async_session
from app.tenant.models import Tenant
from app.usuario.models import Usuario


async def _seed_user_with_codes(session, codes: list[str]):
    from app.authz.models import Permission, Role, RoleProfile

    svc = AuthzService(session)
    await svc.seed_global_permissions()
    tenant = Tenant(nome="T")
    session.add(tenant)
    await session.flush()
    role = Role(tenant_id=tenant.id, nome="R")
    from sqlalchemy import select
    for code in codes:
        perm = (await session.execute(select(Permission).where(Permission.code == code))).scalar_one()
        role.permissions.append(perm)
    session.add(role)
    await session.flush()
    profile = RoleProfile(tenant_id=tenant.id, nome="P")
    profile.roles.append(role)
    session.add(profile)
    await session.flush()
    user = Usuario(username="dep_user", email="dep@e.com", password=get_password_hash("x"),
                   nome="Dep", tenant_id=tenant.id, role_profile_id=profile.id)
    session.add(user)
    await session.flush()
    return user


@pytest.fixture
def mini_app(session):
    app = FastAPI()

    @app.get("/needs-custo-create", dependencies=[Depends(require("custo:create"))])
    async def _ep():
        return {"ok": True}

    async def _override():
        yield session

    app.dependency_overrides[get_async_session] = _override
    return app


@pytest.mark.authz
async def test_require_allows_with_permission(mini_app, session):
    user = await _seed_user_with_codes(session, ["custo:create"])
    token = create_access_token({"sub": user.username})
    async with AsyncClient(transport=ASGITransport(app=mini_app), base_url="http://t") as c:
        r = await c.get("/needs-custo-create", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


@pytest.mark.authz
async def test_require_forbids_without_permission(mini_app, session):
    user = await _seed_user_with_codes(session, ["custo:read"])
    token = create_access_token({"sub": user.username})
    async with AsyncClient(transport=ASGITransport(app=mini_app), base_url="http://t") as c:
        r = await c.get("/needs-custo-create", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
```

> This test also constructs `Usuario(role_profile_id=...)` — mark both test functions `@pytest.mark.xfail(reason="needs role_profile_id (Task 6)", strict=False)` for now; remove in Task 6.

- [ ] **Step 2: Add xfail to both test functions** (decorator above each).

- [ ] **Step 3: Run test to verify it fails**

Run: `task test -- app/tests/test_authz/test_dependencies.py -v`
Expected: import error (`app.authz.dependencies` missing) → collection error.

- [ ] **Step 4: Write the dependency**

`app/authz/dependencies.py`:
```python
from collections.abc import Callable
from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, HTTPException, Request

from app.auth.current_user import CurrentUser
from app.authz.service import AuthzServiceDep


async def get_current_permissions(
    request: Request,
    current_user: CurrentUser,
    service: AuthzServiceDep,
) -> set[str]:
    cached = getattr(request.state, "permissions", None)
    if cached is not None:
        return cached
    perms = await service.resolve_permissions(current_user)
    request.state.permissions = perms
    return perms


CurrentPermissions = Annotated[set[str], Depends(get_current_permissions)]


def require(*codes: str) -> Callable:
    async def _checker(permissions: CurrentPermissions) -> None:
        missing = [c for c in codes if c not in permissions]
        if missing:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail=f"Permissão necessária: {', '.join(missing)}",
            )

    return _checker
```

- [ ] **Step 5: Run test to verify collection passes (tests xfail)**

Run: `task test -- app/tests/test_authz/test_dependencies.py -v`
Expected: both tests XFAIL (no collection error).

- [ ] **Step 6: Commit**

```bash
git add app/authz/dependencies.py app/tests/test_authz/test_dependencies.py
git commit -m "feat(authz): require() permission dependency

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

# Phase 2 — Per-tenant seeding + backfill

### Task 5: AuthzService.seed_tenant_defaults

**Files:**
- Modify: `app/authz/service.py`
- Test: `app/tests/test_authz/test_service_seed_tenant.py`

**Interfaces:**
- Produces (on `AuthzService`):
  - `async seed_tenant_defaults(tenant_id: int) -> RoleProfile` — creates default roles + profiles for the tenant (idempotent); returns the protected **Dono** profile.
  - `async get_profile_by_nome(tenant_id: int, nome: str) -> RoleProfile | None`

- [ ] **Step 1: Write the failing test**

`app/tests/test_authz/test_service_seed_tenant.py`:
```python
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz import catalog
from app.authz.models import RoleProfile
from app.authz.service import AuthzService
from app.tenant.models import Tenant


@pytest.mark.authz
async def test_seed_tenant_defaults_creates_profiles(session: AsyncSession):
    svc = AuthzService(session)
    await svc.seed_global_permissions()
    tenant = Tenant(nome="T")
    session.add(tenant)
    await session.flush()

    dono = await svc.seed_tenant_defaults(tenant.id)
    assert dono.nome == "Dono"
    assert dono.is_protected is True

    profiles = (await session.execute(
        select(RoleProfile).where(RoleProfile.tenant_id == tenant.id)
    )).scalars().all()
    assert {p.nome for p in profiles} == set(catalog.DEFAULT_PROFILES)


@pytest.mark.authz
async def test_seed_tenant_defaults_idempotent(session: AsyncSession):
    svc = AuthzService(session)
    await svc.seed_global_permissions()
    tenant = Tenant(nome="T")
    session.add(tenant)
    await session.flush()
    await svc.seed_tenant_defaults(tenant.id)
    await svc.seed_tenant_defaults(tenant.id)  # twice
    profiles = (await session.execute(
        select(RoleProfile).where(RoleProfile.tenant_id == tenant.id)
    )).scalars().all()
    assert len(profiles) == len(catalog.DEFAULT_PROFILES)


@pytest.mark.authz
async def test_seeded_dono_resolves_all_permissions(session: AsyncSession):
    from app.usuario.models import Usuario
    svc = AuthzService(session)
    await svc.seed_global_permissions()
    tenant = Tenant(nome="T")
    session.add(tenant)
    await session.flush()
    dono = await svc.seed_tenant_defaults(tenant.id)
    user = Usuario(username="o", email="o@e.com", password="x", nome="O",
                   tenant_id=tenant.id, role_profile_id=dono.id)
    session.add(user)
    await session.flush()
    perms = await svc.resolve_permissions(user)
    assert perms == set(catalog.all_codes())
```

> Mark `test_seeded_dono_resolves_all_permissions` with `@pytest.mark.xfail(reason="needs role_profile_id (Task 6)", strict=False)`; remove in Task 6. The first two tests must pass now.

- [ ] **Step 2: Add the xfail** to `test_seeded_dono_resolves_all_permissions`.

- [ ] **Step 3: Run test to verify it fails**

Run: `task test -- app/tests/test_authz/test_service_seed_tenant.py -v`
Expected: FAIL — `AuthzService` has no `seed_tenant_defaults`.

- [ ] **Step 4: Implement seed_tenant_defaults**

Add to `AuthzService` in `app/authz/service.py` (and add the needed import at top: `from app.authz.catalog import DEFAULT_ROLES, DEFAULT_PROFILES`):
```python
    async def get_profile_by_nome(self, tenant_id: int, nome: str) -> RoleProfile | None:
        result = await self.session.execute(
            select(RoleProfile).where(
                RoleProfile.tenant_id == tenant_id, RoleProfile.nome == nome
            )
        )
        return result.scalar_one_or_none()

    async def seed_tenant_defaults(self, tenant_id: int) -> RoleProfile:
        # Permissions by code (catalog already seeded globally).
        perms = {
            p.code: p
            for p in (await self.session.execute(select(Permission))).scalars().all()
        }

        # Roles (idempotent by tenant+nome).
        existing_roles = {
            r.nome: r
            for r in (await self.session.execute(
                select(Role).where(Role.tenant_id == tenant_id)
            )).scalars().all()
        }
        roles: dict[str, Role] = {}
        for nome, codes in DEFAULT_ROLES.items():
            role = existing_roles.get(nome)
            if role is None:
                role = Role(tenant_id=tenant_id, nome=nome, is_system=True)
                role.permissions = [perms[c] for c in codes]
                self.session.add(role)
            roles[nome] = role
        await self.session.flush()

        # Profiles (idempotent).
        existing_profiles = {
            p.nome
            for p in (await self.session.execute(
                select(RoleProfile).where(RoleProfile.tenant_id == tenant_id)
            )).scalars().all()
        }
        dono: RoleProfile | None = None
        for nome, spec in DEFAULT_PROFILES.items():
            if nome not in existing_profiles:
                profile = RoleProfile(
                    tenant_id=tenant_id,
                    nome=nome,
                    is_system=True,
                    is_protected=spec["is_protected"],
                )
                profile.roles = [roles[r] for r in spec["roles"]]
                self.session.add(profile)
                if nome == "Dono":
                    dono = profile
        await self.session.flush()

        if dono is None:
            dono = await self.get_profile_by_nome(tenant_id, "Dono")
        return dono
```

- [ ] **Step 5: Run test to verify it passes**

Run: `task test -- app/tests/test_authz/test_service_seed_tenant.py -v`
Expected: first two PASS, third XFAIL.

- [ ] **Step 6: Commit**

```bash
git add app/authz/service.py app/tests/test_authz/test_service_seed_tenant.py
git commit -m "feat(authz): seed_tenant_defaults (roles + profiles per tenant)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: Migrate Usuario from role enum to role_profile_id

**Files:**
- Modify: `app/usuario/models.py`
- Modify: `app/usuario/schemas.py`
- Modify: `app/usuario/services.py`
- Modify: `app/tests/test_authz/test_service_resolve.py`, `test_dependencies.py`, `test_service_seed_tenant.py` (remove xfails)
- Test: `app/tests/test_authz/test_usuario_profile.py`

**Interfaces:**
- Produces:
  - `Usuario.role_profile_id: int` (FK → `role_profile.id`, nullable in model for test flexibility but NOT NULL in DB after migration; tests always set it).
  - `Usuario` no longer has `role` / `UsuarioRole`.
  - `UsuarioCreate` drops `tenant_id` and `role`; adds optional `role_profile_id: int | None`.
  - `UsuarioService.create(data, tenant_id, role_profile_id)` — tenant + profile supplied by caller, not client body.

- [ ] **Step 1: Write the failing test**

`app/tests/test_authz/test_usuario_profile.py`:
```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz.service import AuthzService
from app.tenant.models import Tenant
from app.usuario.models import Usuario


@pytest.mark.authz
async def test_usuario_has_role_profile_id(session: AsyncSession):
    svc = AuthzService(session)
    await svc.seed_global_permissions()
    tenant = Tenant(nome="T")
    session.add(tenant)
    await session.flush()
    dono = await svc.seed_tenant_defaults(tenant.id)
    user = Usuario(username="u", email="u@e.com", password="x", nome="U",
                   tenant_id=tenant.id, role_profile_id=dono.id)
    session.add(user)
    await session.flush()
    await session.refresh(user)
    assert user.role_profile_id == dono.id
    assert not hasattr(user, "role")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `task test -- app/tests/test_authz/test_usuario_profile.py -v`
Expected: FAIL — `Usuario` has no `role_profile_id` (and still has `role`).

- [ ] **Step 3: Update the Usuario model**

Replace `app/usuario/models.py` entirely:
```python
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.authz.models import RoleProfile
    from app.pagamento_rateio.models import PagamentoRateio
    from app.tenant.models import Tenant


class Usuario(Base):
    """User within a tenant who shares costs."""

    __tablename__ = "usuario"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    ativo: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Foreign keys
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    role_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("role_profile.id", ondelete="RESTRICT"), nullable=True
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="usuarios")
    role_profile: Mapped["RoleProfile | None"] = relationship(lazy="selectin")
    pagamentos_rateio: Mapped[list["PagamentoRateio"]] = relationship(
        back_populates="usuario",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
```

> `role_profile_id` is nullable in the ORM (keeps unit tests flexible) but the migration adds a NOT NULL constraint for real data. `UsuarioRole` is removed entirely.

- [ ] **Step 4: Update usuario schemas**

In `app/usuario/schemas.py`: remove `from app.usuario.models import UsuarioRole` and every `role` field. Replace file with:
```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UsuarioCreate(BaseModel):
    """Owner-side create: tenant_id comes from the JWT, not the body."""

    username: str
    email: EmailStr
    nome: str
    password: str
    role_profile_id: int | None = None


class UsuarioUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    nome: str | None = None
    password: str | None = None
    ativo: bool | None = None
    role_profile_id: int | None = None


class UsuarioPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    nome: str
    ativo: bool
    role_profile_id: int | None
    tenant_id: int
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 5: Update UsuarioService.create signature**

In `app/usuario/services.py`, replace the `create` method and remove the `UsuarioCreate` reliance on `tenant_id`/`role`:
```python
    async def create(
        self, data: UsuarioCreate, tenant_id: int, role_profile_id: int
    ) -> Usuario:
        usuario = Usuario(
            username=data.username,
            email=data.email,
            password=get_password_hash(data.password),
            nome=data.nome,
            tenant_id=tenant_id,
            role_profile_id=role_profile_id,
        )
        self.session.add(usuario)
        await self.session.flush()
        await self.session.refresh(usuario)
        return usuario
```
Keep `get_all`, `get_by_id`, `get_by_username`, `get_by_email`, `update`, `delete` as-is. (The `update` already uses `model_dump(exclude_unset=True)`, so `role_profile_id` flows through.)

- [ ] **Step 6: Remove the xfail decorators** added in Tasks 3, 4, 5:
  - `app/tests/test_authz/test_service_resolve.py` → `test_resolve_permissions_union`
  - `app/tests/test_authz/test_dependencies.py` → both functions
  - `app/tests/test_authz/test_service_seed_tenant.py` → `test_seeded_dono_resolves_all_permissions`

- [ ] **Step 7: Run the authz suite**

Run: `task test -- app/tests/test_authz/ -v`
Expected: all PASS (including the previously-xfailed ones).

- [ ] **Step 8: Commit**

```bash
git add app/usuario/models.py app/usuario/schemas.py app/usuario/services.py app/tests/test_authz/
git commit -m "feat(authz): Usuario.role_profile_id replaces role enum

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 7: Update auth + tenant create + Stripe/admin/populate call-sites

**Files:**
- Modify: `app/auth/current_user.py`
- Modify: `app/tenant/services.py`
- Modify: `app/stripe_webhooks/handlers.py`
- Modify: `app/admin/router.py`
- Modify: `scripts/populate_data.py`
- Test: `app/tests/test_authz/test_tenant_seed_on_create.py`

**Interfaces:**
- Consumes: `AuthzService.seed_tenant_defaults`.
- Produces: `TenantService.create` seeds authz defaults; removes `require_owner`/`CurrentOwner`.

- [ ] **Step 1: Write the failing test**

`app/tests/test_authz/test_tenant_seed_on_create.py`:
```python
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz.models import RoleProfile
from app.authz.service import AuthzService
from app.tenant.schemas import TenantCreate
from app.tenant.services import TenantService


@pytest.mark.authz
async def test_tenant_create_seeds_authz(session: AsyncSession):
    await AuthzService(session).seed_global_permissions()
    tenant = await TenantService(session).create(TenantCreate(nome="Nova Casa"))
    profiles = (await session.execute(
        select(RoleProfile).where(RoleProfile.tenant_id == tenant.id)
    )).scalars().all()
    assert "Dono" in {p.nome for p in profiles}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `task test -- app/tests/test_authz/test_tenant_seed_on_create.py -v`
Expected: FAIL — only the tenant is created, no profiles.

- [ ] **Step 3: Seed authz in TenantService.create**

In `app/tenant/services.py`, update `create`:
```python
    async def create(self, data: TenantCreate) -> Tenant:
        tenant = Tenant(
            nome=data.nome,
            descricao=data.descricao,
        )
        self.session.add(tenant)
        await self.session.flush()
        await self.session.refresh(tenant)

        from app.authz.service import AuthzService

        await AuthzService(self.session).seed_tenant_defaults(tenant.id)
        return tenant
```
(Import is local to avoid a circular import at module load.)

- [ ] **Step 4: Remove require_owner / CurrentOwner from auth**

In `app/auth/current_user.py`, delete the `require_owner` function and the `CurrentOwner` annotation and the now-unused `UsuarioRole` import. Keep `get_current_user` and `CurrentUser`. The file ends after:
```python
CurrentUser = Annotated[Usuario, Depends(get_current_user)]
```

- [ ] **Step 5: Update Stripe checkout handler**

In `app/stripe_webhooks/handlers.py` `handle_checkout_completed`, replace the user-creation block (the `usuario = await usuario_service.create(UsuarioCreate(... role=UsuarioRole.OWNER ...))` call) with profile-based creation. After `tenant = await tenant_service.create(...)` (which now seeds authz), add:
```python
    from app.authz.service import AuthzService

    authz_service = AuthzService(session)
    dono = await authz_service.get_profile_by_nome(tenant.id, "Dono")

    senha_temporaria = secrets.token_urlsafe(16)

    usuario = await usuario_service.create(
        UsuarioCreate(
            username=username,
            email=email,
            nome=nome,
            password=senha_temporaria,
        ),
        tenant_id=tenant.id,
        role_profile_id=dono.id,
    )
```
Remove the old `from app.usuario.models import UsuarioRole` import and the old create call. Keep the rest (assinatura creation, welcome email) unchanged.

- [ ] **Step 6: Update admin create-user endpoint**

In `app/admin/router.py` `create_tenant_usuario`: the body uses `UsuarioCreateAdmin`. Replace its handling so the admin supplies a `role_profile_id` (defaulting to the tenant's Dono if omitted). Replace the function body:
```python
@router.post(
    "/tenants/{tenant_id}/usuarios",
    response_model=UsuarioPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_tenant_usuario(
    tenant_id: int,
    data: UsuarioCreateAdmin,
    _: CurrentAdmin,
    service: UsuarioServiceDep,
    authz: AuthzServiceDep,
):
    existing = await service.get_by_username(data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username já existe")
    profile_id = data.role_profile_id
    if profile_id is None:
        dono = await authz.get_profile_by_nome(tenant_id, "Dono")
        profile_id = dono.id
    create = UsuarioCreate(
        username=data.username, email=data.email, nome=data.nome, password=data.password
    )
    return await service.create(create, tenant_id=tenant_id, role_profile_id=profile_id)
```
Add imports at top of `app/admin/router.py`:
```python
from app.authz.service import AuthzServiceDep
```
Update `UsuarioCreateAdmin` in `app/usuario/schemas.py` to drop `role` and add `role_profile_id: int | None = None`:
```python
class UsuarioCreateAdmin(BaseModel):
    username: str
    email: EmailStr
    nome: str
    password: str
    role_profile_id: int | None = None
```
(Add this class to `app/usuario/schemas.py` — it was removed in Task 6's rewrite; re-add it here.)

- [ ] **Step 7: Update populate_data script**

In `scripts/populate_data.py`:
- Add import: `from app.authz.service import AuthzService`.
- Remove `from app.usuario.models import Usuario, UsuarioRole` → `from app.usuario.models import Usuario`.
- After `await svc...`/at the start of `main()` inside the transaction, before creating tenants, call `await AuthzService(session).seed_global_permissions()`.
- In `criar_tenant_juan` and `criar_tenant_luana`, after `await session.flush()` for the tenant, add:
  ```python
  authz = AuthzService(session)
  dono = await authz.seed_tenant_defaults(tenant.id)
  membro = await authz.get_profile_by_nome(tenant.id, "Membro")
  ```
- Replace each `Usuario(..., role=UsuarioRole.OWNER, ...)` with `role_profile_id=dono.id` and each `role=UsuarioRole.MEMBER` with `role_profile_id=membro.id`.

- [ ] **Step 8: Run the full test suite**

Run: `task test -- app/tests/ -v`
Expected: authz tests PASS; tenant-seed test PASS. (Router tests for the open routers still pass — they get auth in Phase 3. The existing `app/tests/test_tenant/test_tenant_endpoints.py` and `test_rateio` may now fail because they POST users with `tenant_id` in the body / rely on open endpoints — expect those to be addressed in Phase 3. If they fail now, note them; do not "fix" by reverting.)

> If `test_rateio` / `test_tenant` fail at this step due to schema changes, that is expected — Phase 3 rewrites those routers and their tests. Proceed.

- [ ] **Step 9: Commit**

```bash
git add app/auth/current_user.py app/tenant/services.py app/stripe_webhooks/handlers.py app/admin/router.py app/usuario/schemas.py scripts/populate_data.py app/tests/test_authz/test_tenant_seed_on_create.py
git commit -m "feat(authz): seed authz on tenant create; drop CurrentOwner; update call-sites

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 8: Alembic migration (tables + data + backfill + drop enum)

**Files:**
- Create: `alembic/versions/j8k9l0m1n2o3_add_rbac.py`

**Interfaces:**
- Consumes: `app.authz.catalog` (pure data) for seeding.

- [ ] **Step 1: Write the migration**

`alembic/versions/j8k9l0m1n2o3_add_rbac.py`:
```python
"""add rbac (permission, role, role_profile) + usuario.role_profile_id

Revision ID: j8k9l0m1n2o3
Revises: i7j8k9l0m1n2
Create Date: 2026-06-30
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.authz.catalog import DEFAULT_PROFILES, DEFAULT_ROLES, PERMISSIONS

revision: str = "j8k9l0m1n2o3"
down_revision: Union[str, Sequence[str], None] = "i7j8k9l0m1n2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    op.create_table(
        "permission",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("grupo", sa.String(50), nullable=False),
        sa.Column("descricao", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_permission_code", "permission", ["code"], unique=True)

    op.create_table(
        "role",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("descricao", sa.String(255), nullable=True),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "nome", name="uq_role_tenant_nome"),
    )

    op.create_table(
        "role_profile",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("descricao", sa.String(255), nullable=True),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_protected", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "nome", name="uq_profile_tenant_nome"),
    )

    op.create_table(
        "role_permission",
        sa.Column("role_id", sa.Integer, sa.ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", sa.Integer, sa.ForeignKey("permission.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "role_profile_role",
        sa.Column("role_profile_id", sa.Integer, sa.ForeignKey("role_profile.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
    )

    op.add_column("usuario", sa.Column("role_profile_id", sa.Integer, nullable=True))
    op.create_foreign_key(
        "fk_usuario_role_profile", "usuario", "role_profile",
        ["role_profile_id"], ["id"], ondelete="RESTRICT",
    )

    # ---- Seed global permissions ----
    perm_table = sa.table(
        "permission",
        sa.column("id", sa.Integer),
        sa.column("code", sa.String),
        sa.column("grupo", sa.String),
        sa.column("descricao", sa.String),
    )
    op.bulk_insert(
        perm_table,
        [{"code": c, "grupo": g, "descricao": d} for c, g, d in PERMISSIONS],
    )
    perm_ids = {row.code: row.id for row in bind.execute(sa.text("SELECT id, code FROM permission"))}

    # ---- Per-tenant defaults + backfill ----
    tenants = list(bind.execute(sa.text("SELECT id FROM tenant")))
    for (tenant_id,) in tenants:
        role_ids: dict[str, int] = {}
        for nome, codes in DEFAULT_ROLES.items():
            res = bind.execute(
                sa.text(
                    "INSERT INTO role (tenant_id, nome, is_system, created_at, updated_at) "
                    "VALUES (:t, :n, true, now(), now()) RETURNING id"
                ),
                {"t": tenant_id, "n": nome},
            )
            rid = res.scalar_one()
            role_ids[nome] = rid
            for code in codes:
                bind.execute(
                    sa.text("INSERT INTO role_permission (role_id, permission_id) VALUES (:r, :p)"),
                    {"r": rid, "p": perm_ids[code]},
                )

        profile_ids: dict[str, int] = {}
        for nome, spec in DEFAULT_PROFILES.items():
            res = bind.execute(
                sa.text(
                    "INSERT INTO role_profile (tenant_id, nome, is_system, is_protected, created_at, updated_at) "
                    "VALUES (:t, :n, true, :prot, now(), now()) RETURNING id"
                ),
                {"t": tenant_id, "n": nome, "prot": spec["is_protected"]},
            )
            pid = res.scalar_one()
            profile_ids[nome] = pid
            for role_nome in spec["roles"]:
                bind.execute(
                    sa.text("INSERT INTO role_profile_role (role_profile_id, role_id) VALUES (:pf, :r)"),
                    {"pf": pid, "r": role_ids[role_nome]},
                )

        # Backfill: OWNER -> Dono, MEMBER -> Membro (old enum still present here)
        bind.execute(
            sa.text("UPDATE usuario SET role_profile_id = :pf WHERE tenant_id = :t AND role = 'OWNER'"),
            {"pf": profile_ids["Dono"], "t": tenant_id},
        )
        bind.execute(
            sa.text("UPDATE usuario SET role_profile_id = :pf WHERE tenant_id = :t AND role = 'MEMBER'"),
            {"pf": profile_ids["Membro"], "t": tenant_id},
        )

    # Any remaining null (defensive) -> tenant Dono
    bind.execute(sa.text(
        "UPDATE usuario u SET role_profile_id = "
        "(SELECT id FROM role_profile p WHERE p.tenant_id = u.tenant_id AND p.nome = 'Dono') "
        "WHERE u.role_profile_id IS NULL"
    ))

    op.alter_column("usuario", "role_profile_id", nullable=False)
    op.drop_column("usuario", "role")
    sa.Enum(name="usuariorole").drop(bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    usuariorole = sa.Enum("OWNER", "MEMBER", name="usuariorole")
    usuariorole.create(bind, checkfirst=True)
    op.add_column("usuario", sa.Column("role", usuariorole, nullable=False, server_default="MEMBER"))
    op.drop_constraint("fk_usuario_role_profile", "usuario", type_="foreignkey")
    op.drop_column("usuario", "role_profile_id")
    op.drop_table("role_profile_role")
    op.drop_table("role_permission")
    op.drop_table("role_profile")
    op.drop_table("role")
    op.drop_index("ix_permission_code", table_name="permission")
    op.drop_table("permission")
```

- [ ] **Step 2: Apply the migration against the dev DB**

Run: `task head` (`docker compose exec app alembic upgrade head`)
Expected: completes with no error; `usuario.role` gone, `usuario.role_profile_id` present.

- [ ] **Step 3: Verify backfill on dev data**

Run: `docker compose exec app python -c "import asyncio; from sqlalchemy import text; from app.database.session import async_session_factory;
async def m():
    async with async_session_factory() as s:
        r = await s.execute(text('SELECT count(*) FROM usuario WHERE role_profile_id IS NULL')); print('null profiles:', r.scalar_one())
asyncio.run(m())"`
Expected: `null profiles: 0`.

- [ ] **Step 4: Re-seed demo data (optional sanity)**

Run: `docker compose exec app python scripts/populate_data.py`
Expected: completes; prints tenants/users created.

- [ ] **Step 5: Commit**

```bash
git add alembic/versions/j8k9l0m1n2o3_add_rbac.py
git commit -m "feat(authz): alembic migration for RBAC tables + backfill

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

# Phase 3 — Security fix (enforcement + tenant isolation)

> Each router task: add `CurrentUser` + `require(<perm>)`, derive `tenant_id` from the user, and validate nested ownership. Each ships with isolation tests proving a tenant-A user gets 404 on tenant-B resources and 403 without the permission.

Shared test helper used by Phase 3 tests — add once:

**Files:** Modify `app/tests/conftest.py`

- [ ] **Phase 3 Step 0: Add an authz-aware user fixture helper**

Append to `app/tests/conftest.py`:
```python
from app.authz.service import AuthzService as _AuthzService


async def make_tenant_user(session, *, tenant_nome: str, username: str,
                           profile_nome: str = "Dono"):
    """Create a tenant (seeded with authz) + a user on a given profile.

    Returns (tenant, user). Use in Phase 3 isolation/permission tests.
    """
    from app.auth.security import get_password_hash
    from app.tenant.models import Tenant
    from app.usuario.models import Usuario

    svc = _AuthzService(session)
    await svc.seed_global_permissions()
    tenant = Tenant(nome=tenant_nome)
    session.add(tenant)
    await session.flush()
    await svc.seed_tenant_defaults(tenant.id)
    profile = await svc.get_profile_by_nome(tenant.id, profile_nome)
    user = Usuario(
        username=username, email=f"{username}@e.com",
        password=get_password_hash("senha123"), nome=username,
        tenant_id=tenant.id, role_profile_id=profile.id,
    )
    session.add(user)
    await session.flush()
    return tenant, user
```

(No commit yet — bundled with Task 9.)

---

### Task 9: Secure the usuario router

**Files:**
- Modify: `app/usuario/router.py`
- Modify: `app/usuario/services.py` (add `get_all` tenant filter is already there; ensure scoping)
- Test: `app/tests/test_authz/test_usuario_router.py`

**Interfaces:**
- Produces: `GET /api/usuarios/me` returns `UsuarioMe` (adds `permissions: list[str]`, `role_profile`).

- [ ] **Step 1: Write the failing test**

`app/tests/test_authz/test_usuario_router.py`:
```python
import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


@pytest.mark.authz
async def test_list_usuarios_requires_auth(client: AsyncClient):
    r = await client.get("/api/usuarios/")
    assert r.status_code == 401


@pytest.mark.authz
async def test_me_returns_permissions(client: AsyncClient, session):
    _, user = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    token = create_access_token({"sub": user.username})
    r = await client.get("/api/usuarios/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert "custo:create" in body["permissions"]
    assert body["role_profile"]["nome"] == "Dono"


@pytest.mark.authz
async def test_list_usuarios_scoped_to_tenant(client: AsyncClient, session):
    _, user_a = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    await make_tenant_user(session, tenant_nome="B", username="dono_b")
    token = create_access_token({"sub": user_a.username})
    r = await client.get("/api/usuarios/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    usernames = {u["username"] for u in r.json()}
    assert usernames == {"dono_a"}  # never sees tenant B


@pytest.mark.authz
async def test_create_usuario_forbidden_for_leitor(client: AsyncClient, session):
    _, leitor = await make_tenant_user(session, tenant_nome="A", username="leitor_a",
                                       profile_nome="Leitor")
    token = create_access_token({"sub": leitor.username})
    r = await client.post("/api/usuarios/", headers={"Authorization": f"Bearer {token}"},
                          json={"username": "x", "email": "x@e.com", "nome": "X", "password": "p"})
    assert r.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

Run: `task test -- app/tests/test_authz/test_usuario_router.py -v`
Expected: FAIL — `/api/usuarios/` currently open (200 without auth), `/me` lacks permissions.

- [ ] **Step 3: Add the `UsuarioMe` schema**

Append to `app/usuario/schemas.py`:
```python
class RoleProfileBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class UsuarioMe(UsuarioPublic):
    role_profile: RoleProfileBrief | None = None
    permissions: list[str] = []
```

- [ ] **Step 4: Rewrite the usuario router**

Replace `app/usuario/router.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.current_user import CurrentUser
from app.authz.dependencies import CurrentPermissions, require
from app.authz.service import AuthzServiceDep
from app.usuario.schemas import (
    RoleProfileBrief,
    UsuarioCreate,
    UsuarioMe,
    UsuarioPublic,
    UsuarioUpdate,
)
from app.usuario.services import UsuarioServiceDep

router = APIRouter(
    prefix="/api/usuarios",
    tags=["Usuarios"],
    responses={404: {"description": "Nao encontrado"}},
)


@router.get("/me", response_model=UsuarioMe)
async def get_me(current_user: CurrentUser, permissions: CurrentPermissions):
    profile = current_user.role_profile
    return UsuarioMe(
        **UsuarioPublic.model_validate(current_user).model_dump(),
        role_profile=RoleProfileBrief.model_validate(profile) if profile else None,
        permissions=sorted(permissions),
    )


@router.get("/", response_model=list[UsuarioPublic], dependencies=[Depends(require("usuario:read"))])
async def list_usuarios(current_user: CurrentUser, service: UsuarioServiceDep):
    return await service.get_all(tenant_id=current_user.tenant_id)


@router.get("/{usuario_id}", response_model=UsuarioPublic, dependencies=[Depends(require("usuario:read"))])
async def get_usuario(usuario_id: int, current_user: CurrentUser, service: UsuarioServiceDep):
    usuario = await service.get_by_id(usuario_id)
    if not usuario or usuario.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    return usuario


@router.post("/", response_model=UsuarioPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require("usuario:create"))])
async def create_usuario(
    data: UsuarioCreate,
    current_user: CurrentUser,
    service: UsuarioServiceDep,
    authz: AuthzServiceDep,
):
    if await service.get_by_username(data.username):
        raise HTTPException(status_code=400, detail="Username ja existe")
    if await service.get_by_email(data.email):
        raise HTTPException(status_code=400, detail="Email ja existe")

    profile_id = data.role_profile_id
    if profile_id is None:
        membro = await authz.get_profile_by_nome(current_user.tenant_id, "Membro")
        profile_id = membro.id
    else:
        profile = await authz.get_profile(profile_id, current_user.tenant_id)
        if not profile:
            raise HTTPException(status_code=400, detail="Perfil inválido")
    return await service.create(data, tenant_id=current_user.tenant_id, role_profile_id=profile_id)


@router.put("/{usuario_id}", response_model=UsuarioPublic,
            dependencies=[Depends(require("usuario:update"))])
async def update_usuario(
    usuario_id: int, data: UsuarioUpdate, current_user: CurrentUser, service: UsuarioServiceDep
):
    usuario = await service.get_by_id(usuario_id)
    if not usuario or usuario.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    return await service.update(usuario_id, data)


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require("usuario:delete"))])
async def delete_usuario(usuario_id: int, current_user: CurrentUser, service: UsuarioServiceDep):
    usuario = await service.get_by_id(usuario_id)
    if not usuario or usuario.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    await service.delete(usuario_id)
```

> `authz.get_profile(profile_id, tenant_id)` is added in Task 16. For Task 9 it is only reached when a `role_profile_id` is supplied; the tests here omit it. Add a minimal `get_profile` stub now to avoid an import error:

In `app/authz/service.py`, add:
```python
    async def get_profile(self, profile_id: int, tenant_id: int) -> RoleProfile | None:
        result = await self.session.execute(
            select(RoleProfile).where(
                RoleProfile.id == profile_id, RoleProfile.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `task test -- app/tests/test_authz/test_usuario_router.py -v`
Expected: PASS (4 tests).

- [ ] **Step 6: Commit**

```bash
git add app/tests/conftest.py app/usuario/router.py app/usuario/schemas.py app/authz/service.py app/tests/test_authz/test_usuario_router.py
git commit -m "feat(authz): secure usuario router (auth+perms+tenant scope, /me permissions)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 10: Secure the mes_referencia router

**Files:**
- Modify: `app/mes_referencia/router.py`, `app/mes_referencia/services.py`
- Test: `app/tests/test_authz/test_mes_router.py`

**Interfaces:**
- Produces: `MesReferenciaService.get_by_id_scoped(id, tenant_id) -> MesReferencia | None`.

- [ ] **Step 1: Write the failing test**

`app/tests/test_authz/test_mes_router.py`:
```python
import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


@pytest.mark.authz
async def test_meses_requires_auth(client: AsyncClient):
    r = await client.get("/api/meses/")
    assert r.status_code == 401


@pytest.mark.authz
async def test_create_mes_scoped_to_jwt_tenant(client: AsyncClient, session):
    tenant_a, user_a = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    token = create_access_token({"sub": user_a.username})
    r = await client.post("/api/meses/", headers={"Authorization": f"Bearer {token}"},
                          json={"ano": 2026, "mes": 7})
    assert r.status_code == 201
    assert r.json()["tenant_id"] == tenant_a.id


@pytest.mark.authz
async def test_cannot_read_other_tenant_mes(client: AsyncClient, session):
    tenant_a, user_a = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    _, user_b = await make_tenant_user(session, tenant_nome="B", username="dono_b")
    token_a = create_access_token({"sub": user_a.username})
    token_b = create_access_token({"sub": user_b.username})
    created = await client.post("/api/meses/", headers={"Authorization": f"Bearer {token_a}"},
                               json={"ano": 2026, "mes": 7})
    mes_id = created.json()["id"]
    r = await client.get(f"/api/meses/{mes_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `task test -- app/tests/test_authz/test_mes_router.py -v`
Expected: FAIL — endpoints open + accept body `tenant_id`.

- [ ] **Step 3: Update the MesReferencia schema + service**

In `app/mes_referencia/schemas.py`, remove `tenant_id` from `MesReferenciaBase` (move to a server-injected field). New:
```python
class MesReferenciaBase(BaseModel):
    ano: int
    mes: int

    @field_validator("mes")
    @classmethod
    def validate_mes(cls, v: int) -> int:
        if not 1 <= v <= 12:
            raise ValueError("Mes deve estar entre 1 e 12")
        return v

    @field_validator("ano")
    @classmethod
    def validate_ano(cls, v: int) -> int:
        if v < 2000 or v > 2100:
            raise ValueError("Ano deve estar entre 2000 e 2100")
        return v


class MesReferenciaCreate(MesReferenciaBase):
    pass


class MesReferenciaPublic(MesReferenciaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    status: StatusMes
    created_at: datetime
    updated_at: datetime
```
In `app/mes_referencia/services.py`, change `create` to take `tenant_id` explicitly and add a scoped getter:
```python
    async def get_by_id_scoped(self, mes_referencia_id: int, tenant_id: int) -> MesReferencia | None:
        mes = await self.session.get(MesReferencia, mes_referencia_id)
        if mes is None or mes.tenant_id != tenant_id:
            return None
        return mes

    async def create(self, data: MesReferenciaCreate, tenant_id: int) -> MesReferencia:
        mes_ref = MesReferencia(ano=data.ano, mes=data.mes, tenant_id=tenant_id)
        self.session.add(mes_ref)
        await self.session.flush()
        await self.session.refresh(mes_ref)
        return mes_ref
```
(Leave `obter_ou_criar_mes_atual`, `importar_custos_fixos_para_mes`, `get_all`, `get_by_tenant_ano_mes`, `update`, `delete` intact — they already take `tenant_id`.)

- [ ] **Step 4: Rewrite the mes_referencia router**

Replace `app/mes_referencia/router.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.current_user import CurrentUser
from app.authz.dependencies import require
from app.mes_referencia.schemas import (
    MesReferenciaCreate,
    MesReferenciaPublic,
    MesReferenciaUpdate,
)
from app.mes_referencia.services import MesReferenciaServiceDep

router = APIRouter(
    prefix="/api/meses",
    tags=["Meses de Referencia"],
    responses={404: {"description": "Nao encontrado"}},
)


@router.get("/", response_model=list[MesReferenciaPublic], dependencies=[Depends(require("mes:read"))])
async def list_meses_referencia(current_user: CurrentUser, service: MesReferenciaServiceDep):
    return await service.get_all(tenant_id=current_user.tenant_id)


@router.get("/atual", response_model=MesReferenciaPublic, dependencies=[Depends(require("mes:read"))])
async def get_ou_criar_mes_atual(current_user: CurrentUser, service: MesReferenciaServiceDep):
    return await service.obter_ou_criar_mes_atual(current_user.tenant_id)


@router.get("/{mes_referencia_id}", response_model=MesReferenciaPublic, dependencies=[Depends(require("mes:read"))])
async def get_mes_referencia(mes_referencia_id: int, current_user: CurrentUser, service: MesReferenciaServiceDep):
    mes_ref = await service.get_by_id_scoped(mes_referencia_id, current_user.tenant_id)
    if not mes_ref:
        raise HTTPException(status_code=404, detail="Mes de referencia nao encontrado")
    return mes_ref


@router.post("/", response_model=MesReferenciaPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require("mes:create"))])
async def create_mes_referencia(
    data: MesReferenciaCreate, current_user: CurrentUser, service: MesReferenciaServiceDep
):
    existing = await service.get_by_tenant_ano_mes(current_user.tenant_id, data.ano, data.mes)
    if existing:
        raise HTTPException(status_code=400, detail="Mes de referencia ja existe para este tenant")
    return await service.create(data, tenant_id=current_user.tenant_id)


@router.put("/{mes_referencia_id}", response_model=MesReferenciaPublic,
            dependencies=[Depends(require("mes:update"))])
async def update_mes_referencia(
    mes_referencia_id: int, data: MesReferenciaUpdate, current_user: CurrentUser, service: MesReferenciaServiceDep
):
    mes_ref = await service.get_by_id_scoped(mes_referencia_id, current_user.tenant_id)
    if not mes_ref:
        raise HTTPException(status_code=404, detail="Mes de referencia nao encontrado")
    return await service.update(mes_referencia_id, data)


@router.post("/{mes_referencia_id}/importar-custos-fixos", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require("mes:import_fixos"))])
async def importar_custos_fixos(
    mes_referencia_id: int, current_user: CurrentUser, service: MesReferenciaServiceDep
):
    mes_ref = await service.get_by_id_scoped(mes_referencia_id, current_user.tenant_id)
    if not mes_ref:
        raise HTTPException(status_code=404, detail="Mes de referencia nao encontrado")
    custos = await service.importar_custos_fixos_para_mes(mes_referencia_id, current_user.tenant_id)
    return {"message": f"{len(custos)} custos fixos importados"}
```

> The old route `/tenant/{tenant_id}/atual` is replaced by `/atual` (tenant from JWT). Frontend `getMesAtual` is updated in Phase 5.

- [ ] **Step 5: Run test to verify it passes**

Run: `task test -- app/tests/test_authz/test_mes_router.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/mes_referencia/ app/tests/test_authz/test_mes_router.py
git commit -m "feat(authz): secure mes_referencia router (perms + tenant scope)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 11: Secure the custo router

**Files:**
- Modify: `app/custo/router.py`, `app/custo/services.py`
- Test: `app/tests/test_authz/test_custo_router.py`

**Interfaces:**
- Consumes: `MesReferenciaService.get_by_id_scoped`.
- Produces: `CustoService.get_scoped(custo_id, tenant_id) -> Custo | None` (join via mes_referencia); `CustoService.list_for_mes(mes_id)`.

- [ ] **Step 1: Write the failing test**

`app/tests/test_authz/test_custo_router.py`:
```python
import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


async def _make_mes(client, token):
    r = await client.post("/api/meses/", headers={"Authorization": f"Bearer {token}"},
                          json={"ano": 2026, "mes": 7})
    return r.json()["id"]


@pytest.mark.authz
async def test_custos_requires_auth(client: AsyncClient):
    assert (await client.get("/api/custos/")).status_code == 401


@pytest.mark.authz
async def test_create_custo_in_own_mes(client: AsyncClient, session):
    _, user_a = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    token = create_access_token({"sub": user_a.username})
    mes_id = await _make_mes(client, token)
    r = await client.post("/api/custos/", headers={"Authorization": f"Bearer {token}"},
                          json={"descricao": "Luz", "valor": "100.00",
                                "data_vencimento": "2026-07-10", "mes_referencia_id": mes_id})
    assert r.status_code == 201


@pytest.mark.authz
async def test_cannot_create_custo_in_other_tenant_mes(client: AsyncClient, session):
    _, user_a = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    _, user_b = await make_tenant_user(session, tenant_nome="B", username="dono_b")
    token_a = create_access_token({"sub": user_a.username})
    token_b = create_access_token({"sub": user_b.username})
    mes_a = await _make_mes(client, token_a)
    # B tries to attach a custo to A's mes
    r = await client.post("/api/custos/", headers={"Authorization": f"Bearer {token_b}"},
                          json={"descricao": "X", "valor": "1.00",
                                "data_vencimento": "2026-07-10", "mes_referencia_id": mes_a})
    assert r.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `task test -- app/tests/test_authz/test_custo_router.py -v`
Expected: FAIL — endpoints open, no nested ownership check.

- [ ] **Step 3: Add scoped helpers to CustoService**

In `app/custo/services.py` add (import `MesReferencia` and `select`/joins as needed):
```python
    async def get_scoped(self, custo_id: int, tenant_id: int) -> Custo | None:
        from app.mes_referencia.models import MesReferencia

        result = await self.session.execute(
            select(Custo)
            .join(MesReferencia, MesReferencia.id == Custo.mes_referencia_id)
            .where(Custo.id == custo_id, MesReferencia.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()
```
(Keep `get_all`, `create`, `update`, `delete`. `create` stays as-is; the router validates the mes ownership before calling it.)

- [ ] **Step 4: Rewrite the custo router**

Replace `app/custo/router.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.current_user import CurrentUser
from app.authz.dependencies import require
from app.custo.schemas import CustoCreate, CustoPublic, CustoUpdate
from app.custo.services import CustoServiceDep
from app.mes_referencia.services import MesReferenciaServiceDep

router = APIRouter(
    prefix="/api/custos",
    tags=["Custos"],
    responses={404: {"description": "Nao encontrado"}},
)


@router.get("/", response_model=list[CustoPublic], dependencies=[Depends(require("custo:read"))])
async def list_custos(
    current_user: CurrentUser,
    service: CustoServiceDep,
    mes_service: MesReferenciaServiceDep,
    mes_referencia_id: int,
):
    mes = await mes_service.get_by_id_scoped(mes_referencia_id, current_user.tenant_id)
    if not mes:
        raise HTTPException(status_code=404, detail="Mes de referencia nao encontrado")
    return await service.get_all(mes_referencia_id=mes_referencia_id)


@router.get("/{custo_id}", response_model=CustoPublic, dependencies=[Depends(require("custo:read"))])
async def get_custo(custo_id: int, current_user: CurrentUser, service: CustoServiceDep):
    custo = await service.get_scoped(custo_id, current_user.tenant_id)
    if not custo:
        raise HTTPException(status_code=404, detail="Custo nao encontrado")
    return custo


@router.post("/", response_model=CustoPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require("custo:create"))])
async def create_custo(
    data: CustoCreate,
    current_user: CurrentUser,
    service: CustoServiceDep,
    mes_service: MesReferenciaServiceDep,
):
    mes = await mes_service.get_by_id_scoped(data.mes_referencia_id, current_user.tenant_id)
    if not mes:
        raise HTTPException(status_code=404, detail="Mes de referencia nao encontrado")
    return await service.create(data)


@router.put("/{custo_id}", response_model=CustoPublic, dependencies=[Depends(require("custo:update"))])
async def update_custo(custo_id: int, data: CustoUpdate, current_user: CurrentUser, service: CustoServiceDep):
    custo = await service.get_scoped(custo_id, current_user.tenant_id)
    if not custo:
        raise HTTPException(status_code=404, detail="Custo nao encontrado")
    return await service.update(custo_id, data)


@router.delete("/{custo_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require("custo:delete"))])
async def delete_custo(custo_id: int, current_user: CurrentUser, service: CustoServiceDep):
    custo = await service.get_scoped(custo_id, current_user.tenant_id)
    if not custo:
        raise HTTPException(status_code=404, detail="Custo nao encontrado")
    await service.delete(custo_id)
```

> `mes_referencia_id` is now a **required** query param on `GET /api/custos/` (a tenant must request a specific owned month). Frontend already always passes it.

- [ ] **Step 5: Run test to verify it passes**

Run: `task test -- app/tests/test_authz/test_custo_router.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/custo/ app/tests/test_authz/test_custo_router.py
git commit -m "feat(authz): secure custo router (perms + nested tenant scope)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 12: Secure the custo_fixo router

**Files:**
- Modify: `app/custo_fixo/router.py`, `app/custo_fixo/services.py`, `app/custo_fixo/schemas.py`
- Test: `app/tests/test_authz/test_custo_fixo_router.py`

**Interfaces:**
- Produces: `CustoFixoService.get_scoped(id, tenant_id)`, `create(data, tenant_id)`.

- [ ] **Step 1: Write the failing test**

`app/tests/test_authz/test_custo_fixo_router.py`:
```python
import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


@pytest.mark.authz
async def test_custos_fixos_requires_auth(client: AsyncClient):
    assert (await client.get("/api/custos-fixos/")).status_code == 401


@pytest.mark.authz
async def test_create_and_scope(client: AsyncClient, session):
    tenant_a, user_a = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    _, user_b = await make_tenant_user(session, tenant_nome="B", username="dono_b")
    token_a = create_access_token({"sub": user_a.username})
    token_b = create_access_token({"sub": user_b.username})
    created = await client.post("/api/custos-fixos/", headers={"Authorization": f"Bearer {token_a}"},
                               json={"descricao": "Aluguel", "valor": "1000.00", "dia_vencimento": 5})
    assert created.status_code == 201
    assert created.json()["tenant_id"] == tenant_a.id
    cf_id = created.json()["id"]
    # B cannot see A's custo fixo
    r = await client.get(f"/api/custos-fixos/{cf_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `task test -- app/tests/test_authz/test_custo_fixo_router.py -v`
Expected: FAIL — open + body `tenant_id`.

- [ ] **Step 3: Update schema + service**

In `app/custo_fixo/schemas.py`, remove `tenant_id` from `CustoFixoBase` (keep validators), and add `tenant_id` to `CustoFixoPublic` only:
```python
class CustoFixoBase(BaseModel):
    descricao: str
    valor: Decimal
    dia_vencimento: int = 10

    @field_validator("dia_vencimento")
    @classmethod
    def validate_dia_vencimento(cls, v: int) -> int:
        if not 1 <= v <= 31:
            raise ValueError("Dia de vencimento deve estar entre 1 e 31")
        return v

    @field_validator("valor")
    @classmethod
    def validate_valor(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Valor deve ser maior que zero")
        return v


class CustoFixoCreate(CustoFixoBase):
    pass
```
And `CustoFixoPublic` adds `tenant_id: int`.
In `app/custo_fixo/services.py`:
```python
    async def get_scoped(self, custo_fixo_id: int, tenant_id: int) -> CustoFixo | None:
        cf = await self.session.get(CustoFixo, custo_fixo_id)
        if cf is None or cf.tenant_id != tenant_id:
            return None
        return cf

    async def create(self, data: CustoFixoCreate, tenant_id: int) -> CustoFixo:
        custo_fixo = CustoFixo(
            descricao=data.descricao,
            valor=data.valor,
            dia_vencimento=data.dia_vencimento,
            tenant_id=tenant_id,
        )
        self.session.add(custo_fixo)
        await self.session.flush()
        await self.session.refresh(custo_fixo)
        return custo_fixo
```

- [ ] **Step 4: Rewrite the custo_fixo router**

Replace `app/custo_fixo/router.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.current_user import CurrentUser
from app.authz.dependencies import require
from app.custo_fixo.schemas import CustoFixoCreate, CustoFixoPublic, CustoFixoUpdate
from app.custo_fixo.services import CustoFixoServiceDep

router = APIRouter(
    prefix="/api/custos-fixos",
    tags=["Custos Fixos"],
    responses={404: {"description": "Nao encontrado"}},
)


@router.get("/", response_model=list[CustoFixoPublic], dependencies=[Depends(require("custo_fixo:read"))])
async def list_custos_fixos(current_user: CurrentUser, service: CustoFixoServiceDep):
    return await service.get_all(tenant_id=current_user.tenant_id)


@router.get("/{custo_fixo_id}", response_model=CustoFixoPublic, dependencies=[Depends(require("custo_fixo:read"))])
async def get_custo_fixo(custo_fixo_id: int, current_user: CurrentUser, service: CustoFixoServiceDep):
    cf = await service.get_scoped(custo_fixo_id, current_user.tenant_id)
    if not cf:
        raise HTTPException(status_code=404, detail="Custo fixo nao encontrado")
    return cf


@router.post("/", response_model=CustoFixoPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require("custo_fixo:create"))])
async def create_custo_fixo(data: CustoFixoCreate, current_user: CurrentUser, service: CustoFixoServiceDep):
    return await service.create(data, tenant_id=current_user.tenant_id)


@router.put("/{custo_fixo_id}", response_model=CustoFixoPublic, dependencies=[Depends(require("custo_fixo:update"))])
async def update_custo_fixo(custo_fixo_id: int, data: CustoFixoUpdate, current_user: CurrentUser, service: CustoFixoServiceDep):
    cf = await service.get_scoped(custo_fixo_id, current_user.tenant_id)
    if not cf:
        raise HTTPException(status_code=404, detail="Custo fixo nao encontrado")
    return await service.update(custo_fixo_id, data)


@router.delete("/{custo_fixo_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require("custo_fixo:delete"))])
async def delete_custo_fixo(custo_fixo_id: int, current_user: CurrentUser, service: CustoFixoServiceDep):
    cf = await service.get_scoped(custo_fixo_id, current_user.tenant_id)
    if not cf:
        raise HTTPException(status_code=404, detail="Custo fixo nao encontrado")
    await service.delete(custo_fixo_id)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `task test -- app/tests/test_authz/test_custo_fixo_router.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/custo_fixo/ app/tests/test_authz/test_custo_fixo_router.py
git commit -m "feat(authz): secure custo_fixo router

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 13: Secure the pagamento_rateio router

**Files:**
- Modify: `app/pagamento_rateio/router.py`, `app/pagamento_rateio/services.py`
- Test: `app/tests/test_authz/test_rateio_router.py`

**Interfaces:**
- Produces: `PagamentoRateioService.get_scoped(id, tenant_id)`, and `assert_custo_in_tenant(custo_id, tenant_id)` / `assert_usuario_in_tenant(usuario_id, tenant_id)` helpers used by `create`.

- [ ] **Step 1: Write the failing test**

`app/tests/test_authz/test_rateio_router.py`:
```python
import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


async def _mes_and_custo(client, token):
    mes = (await client.post("/api/meses/", headers={"Authorization": f"Bearer {token}"},
                             json={"ano": 2026, "mes": 7})).json()
    custo = (await client.post("/api/custos/", headers={"Authorization": f"Bearer {token}"},
                               json={"descricao": "Luz", "valor": "100.00",
                                     "data_vencimento": "2026-07-10",
                                     "mes_referencia_id": mes["id"]})).json()
    return custo["id"]


@pytest.mark.authz
async def test_rateios_requires_auth(client: AsyncClient):
    assert (await client.get("/api/rateios/", params={"custo_id": 1})).status_code == 401


@pytest.mark.authz
async def test_create_rateio_own_tenant(client: AsyncClient, session):
    _, user_a = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    token = create_access_token({"sub": user_a.username})
    custo_id = await _mes_and_custo(client, token)
    r = await client.post("/api/rateios/", headers={"Authorization": f"Bearer {token}"},
                          json={"porcentagem": "50.00", "custo_id": custo_id, "usuario_id": user_a.id})
    assert r.status_code == 201


@pytest.mark.authz
async def test_cannot_rateio_other_tenant_custo(client: AsyncClient, session):
    _, user_a = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    _, user_b = await make_tenant_user(session, tenant_nome="B", username="dono_b")
    token_a = create_access_token({"sub": user_a.username})
    token_b = create_access_token({"sub": user_b.username})
    custo_a = await _mes_and_custo(client, token_a)
    r = await client.post("/api/rateios/", headers={"Authorization": f"Bearer {token_b}"},
                          json={"porcentagem": "50.00", "custo_id": custo_a, "usuario_id": user_b.id})
    assert r.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `task test -- app/tests/test_authz/test_rateio_router.py -v`
Expected: FAIL — open router.

- [ ] **Step 3: Add scoped helpers to the rateio service**

In `app/pagamento_rateio/services.py` add (import `MesReferencia`, `Custo`, `Usuario`):
```python
    async def get_scoped(self, pagamento_id: int, tenant_id: int) -> PagamentoRateio | None:
        from app.custo.models import Custo
        from app.mes_referencia.models import MesReferencia

        result = await self.session.execute(
            select(PagamentoRateio)
            .join(Custo, Custo.id == PagamentoRateio.custo_id)
            .join(MesReferencia, MesReferencia.id == Custo.mes_referencia_id)
            .where(PagamentoRateio.id == pagamento_id, MesReferencia.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def custo_in_tenant(self, custo_id: int, tenant_id: int) -> bool:
        from app.custo.models import Custo
        from app.mes_referencia.models import MesReferencia

        result = await self.session.execute(
            select(Custo.id)
            .join(MesReferencia, MesReferencia.id == Custo.mes_referencia_id)
            .where(Custo.id == custo_id, MesReferencia.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none() is not None

    async def usuario_in_tenant(self, usuario_id: int, tenant_id: int) -> bool:
        from app.usuario.models import Usuario

        result = await self.session.execute(
            select(Usuario.id).where(Usuario.id == usuario_id, Usuario.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none() is not None
```

- [ ] **Step 4: Rewrite the rateio router**

Replace `app/pagamento_rateio/router.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.auth.current_user import CurrentUser
from app.authz.dependencies import require
from app.pagamento_rateio.schemas import (
    PagamentoRateioCreate,
    PagamentoRateioPublic,
    PagamentoRateioUpdate,
)
from app.pagamento_rateio.services import PagamentoRateioServiceDep

router = APIRouter(
    prefix="/api/rateios",
    tags=["Pagamentos Rateio"],
    responses={404: {"description": "Nao encontrado"}},
)


@router.get("/", response_model=list[PagamentoRateioPublic], dependencies=[Depends(require("rateio:read"))])
async def list_pagamentos_rateio(
    current_user: CurrentUser,
    service: PagamentoRateioServiceDep,
    custo_id: int,
):
    if not await service.custo_in_tenant(custo_id, current_user.tenant_id):
        raise HTTPException(status_code=404, detail="Custo nao encontrado")
    return await service.get_all(custo_id=custo_id)


@router.get("/{pagamento_id}", response_model=PagamentoRateioPublic, dependencies=[Depends(require("rateio:read"))])
async def get_pagamento_rateio(pagamento_id: int, current_user: CurrentUser, service: PagamentoRateioServiceDep):
    pagamento = await service.get_scoped(pagamento_id, current_user.tenant_id)
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento rateio nao encontrado")
    return pagamento


@router.post("/", response_model=PagamentoRateioPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require("rateio:create"))])
async def create_pagamento_rateio(
    data: PagamentoRateioCreate, current_user: CurrentUser, service: PagamentoRateioServiceDep
):
    if not await service.custo_in_tenant(data.custo_id, current_user.tenant_id):
        raise HTTPException(status_code=404, detail="Custo nao encontrado")
    if not await service.usuario_in_tenant(data.usuario_id, current_user.tenant_id):
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    return await service.create(data)


@router.put("/{pagamento_id}", response_model=PagamentoRateioPublic)
async def update_pagamento_rateio(
    pagamento_id: int,
    data: PagamentoRateioUpdate,
    current_user: CurrentUser,
    service: PagamentoRateioServiceDep,
    permissions=Depends(__import__("app.authz.dependencies", fromlist=["get_current_permissions"]).get_current_permissions),
):
    pagamento = await service.get_scoped(pagamento_id, current_user.tenant_id)
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento rateio nao encontrado")
    needed = "rateio:pay" if data.status is not None else "rateio:update"
    if needed not in permissions:
        raise HTTPException(status_code=403, detail=f"Permissão necessária: {needed}")
    pagamento = await service.update(pagamento_id, data)
    if data.status is not None:
        await service.recalcular_status_custo(pagamento.custo_id)
    return pagamento


@router.post("/{pagamento_id}/comprovante", response_model=PagamentoRateioPublic,
             dependencies=[Depends(require("comprovante:upload"))])
async def upload_comprovante(
    pagamento_id: int, file: UploadFile, current_user: CurrentUser, service: PagamentoRateioServiceDep
):
    pagamento = await service.get_scoped(pagamento_id, current_user.tenant_id)
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento rateio nao encontrado")
    return await service.salvar_comprovante(pagamento_id, file)


@router.delete("/{pagamento_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require("rateio:delete"))])
async def delete_pagamento_rateio(pagamento_id: int, current_user: CurrentUser, service: PagamentoRateioServiceDep):
    pagamento = await service.get_scoped(pagamento_id, current_user.tenant_id)
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento rateio nao encontrado")
    await service.delete(pagamento_id)
```

> The `update` endpoint needs the resolved permission set to choose between `rateio:pay` and `rateio:update`. Replace the awkward `__import__` line with a clean import: add `from app.authz.dependencies import CurrentPermissions` at the top and change the param to `permissions: CurrentPermissions`. (Written explicitly to avoid a placeholder; prefer the clean import.)

Clean version of the import + signature:
```python
from app.authz.dependencies import CurrentPermissions, require
...
async def update_pagamento_rateio(
    pagamento_id: int,
    data: PagamentoRateioUpdate,
    current_user: CurrentUser,
    service: PagamentoRateioServiceDep,
    permissions: CurrentPermissions,
):
```

- [ ] **Step 5: Run test to verify it passes**

Run: `task test -- app/tests/test_authz/test_rateio_router.py -v`
Expected: PASS.

- [ ] **Step 6: Port the existing rateio validation tests**

The existing `app/tests/test_rateio/test_rateio_validation.py` uses open endpoints and body `tenant_id`. Update its `_create_test_data` helper to use `make_tenant_user` + bearer token + the new payloads (no `tenant_id` in mes/custo bodies; `mes_referencia_id` query param on custos). Concretely, replace `_create_test_data` and add an auth header to every request. Minimal rewrite:
```python
    async def _create_test_data(self, client, session):
        from app.auth.security import create_access_token
        from app.tests.conftest import make_tenant_user
        _, owner = await make_tenant_user(session, tenant_nome="Casa Rateio", username="dono_r")
        self.h = {"Authorization": f"Bearer {create_access_token({'sub': owner.username})}"}
        u1 = (await client.post("/api/usuarios/", headers=self.h,
              json={"username": "u1", "email": "u1@t.com", "password": "senha123", "nome": "U1"})).json()
        u2 = (await client.post("/api/usuarios/", headers=self.h,
              json={"username": "u2", "email": "u2@t.com", "password": "senha123", "nome": "U2"})).json()
        mes = (await client.post("/api/meses/", headers=self.h,
               json={"ano": 2024, "mes": 1})).json()
        custo = (await client.post("/api/custos/", headers=self.h,
                 json={"descricao": "Aluguel", "valor": "1000.00",
                       "data_vencimento": "2024-01-10", "mes_referencia_id": mes["id"]})).json()
        return {"usuario1": u1, "usuario2": u2, "mes": mes, "custo": custo}
```
Then update each test method signature to accept `session` and pass `self.h` as `headers=` on every `/api/rateios/` call. (Owner profile has all rateio permissions, so 201/200 paths hold; the 422 validation cases are unchanged.)

- [ ] **Step 7: Run the rateio suites**

Run: `task test -- app/tests/test_rateio/ app/tests/test_authz/test_rateio_router.py -v`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add app/pagamento_rateio/ app/tests/test_authz/test_rateio_router.py app/tests/test_rateio/
git commit -m "feat(authz): secure rateio router + port rateio validation tests

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 14: Secure the tenant router (read/update self; create/delete → admin only)

**Files:**
- Modify: `app/tenant/router.py`
- Test: `app/tests/test_authz/test_tenant_router.py`
- Modify: `app/tests/test_tenant/test_tenant_endpoints.py` (port/repurpose)

- [ ] **Step 1: Write the failing test**

`app/tests/test_authz/test_tenant_router.py`:
```python
import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


@pytest.mark.authz
async def test_get_my_tenant(client: AsyncClient, session):
    tenant_a, user_a = await make_tenant_user(session, tenant_nome="Casa A", username="dono_a")
    token = create_access_token({"sub": user_a.username})
    r = await client.get("/api/tenants/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["id"] == tenant_a.id


@pytest.mark.authz
async def test_public_tenant_create_removed(client: AsyncClient):
    # The old open POST /api/tenants/ must no longer create tenants unauthenticated.
    r = await client.post("/api/tenants/", json={"nome": "Hacker"})
    assert r.status_code in (401, 403, 404, 405)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `task test -- app/tests/test_authz/test_tenant_router.py -v`
Expected: FAIL — `/api/tenants/me` missing; public create still open.

- [ ] **Step 3: Rewrite the tenant router**

Replace `app/tenant/router.py` (drops public create/delete; adds `/me`; update scoped):
```python
from fastapi import APIRouter, Depends, HTTPException

from app.auth.current_user import CurrentUser
from app.authz.dependencies import require
from app.tenant.schemas import TenantPublic, TenantUpdate
from app.tenant.services import TenantServiceDep

router = APIRouter(
    prefix="/api/tenants",
    tags=["Tenants"],
    responses={404: {"description": "Nao encontrado"}},
)


@router.get("/me", response_model=TenantPublic, dependencies=[Depends(require("tenant:read"))])
async def get_my_tenant(current_user: CurrentUser, service: TenantServiceDep):
    tenant = await service.get_by_id(current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant nao encontrado")
    return tenant


@router.put("/me", response_model=TenantPublic, dependencies=[Depends(require("tenant:update"))])
async def update_my_tenant(data: TenantUpdate, current_user: CurrentUser, service: TenantServiceDep):
    tenant = await service.update(current_user.tenant_id, data)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant nao encontrado")
    return tenant
```

> Tenant create/delete are platform operations: they remain only on the admin router (`POST/DELETE /admin/tenants`, already `CurrentAdmin`-gated) and via Stripe checkout. The public `/api/tenants` create/delete/list are removed.

- [ ] **Step 4: Repurpose the old tenant endpoint test**

`app/tests/test_tenant/test_tenant_endpoints.py` currently tests the open CRUD. Replace its body with tests for the admin-side tenant CRUD (already `CurrentAdmin`-gated) OR delete the file if redundant with `test_tenant_router.py`. Minimal: replace its contents with a single guard test:
```python
import pytest
from httpx import AsyncClient


@pytest.mark.tenant
async def test_tenant_list_endpoint_removed(client: AsyncClient):
    r = await client.get("/api/tenants/")
    assert r.status_code in (401, 403, 404, 405)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `task test -- app/tests/test_authz/test_tenant_router.py app/tests/test_tenant/ -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/tenant/router.py app/tests/test_authz/test_tenant_router.py app/tests/test_tenant/
git commit -m "feat(authz): scope tenant router to self; remove public tenant CRUD

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 15: Add permission checks to whatsapp + campanha routers

**Files:**
- Modify: `app/whatsapp/router.py`, `app/campanha/router.py`
- Test: `app/tests/test_authz/test_whatsapp_campanha_perms.py`

> These routers already scope by `current_user.tenant_id`; this task adds `require(...)` so the new RBAC actually gates them.

- [ ] **Step 1: Write the failing test**

`app/tests/test_authz/test_whatsapp_campanha_perms.py`:
```python
import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


@pytest.mark.authz
async def test_leitor_cannot_create_campanha(client: AsyncClient, session):
    _, leitor = await make_tenant_user(session, tenant_nome="A", username="leitor_a", profile_nome="Leitor")
    token = create_access_token({"sub": leitor.username})
    r = await client.post("/api/campanhas", headers={"Authorization": f"Bearer {token}"},
                          json={"nome": "C"})
    assert r.status_code == 403


@pytest.mark.authz
async def test_leitor_can_read_campanhas(client: AsyncClient, session):
    _, leitor = await make_tenant_user(session, tenant_nome="A", username="leitor_a", profile_nome="Leitor")
    token = create_access_token({"sub": leitor.username})
    r = await client.get("/api/campanhas", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `task test -- app/tests/test_authz/test_whatsapp_campanha_perms.py -v`
Expected: FAIL — Leitor can currently create a campaign (no permission gate).

- [ ] **Step 3: Add `require(...)` to campanha endpoints**

In `app/campanha/router.py`, add `from fastapi import Depends` (already imported) and `from app.authz.dependencies import require`. Add `dependencies=[Depends(require("<code>"))]` per route:
- `GET /api/campanhas` → `campanha:read`
- `POST /api/campanhas` → `campanha:create`
- `GET /api/campanhas/{id}` → `campanha:read`
- `PUT /api/campanhas/{id}` → `campanha:update`
- `DELETE /api/campanhas/{id}` → `campanha:delete`
- `POST .../ativar|pausar|concluir` → `campanha:activate`
- templates GET → `campanha:read`; POST/DELETE → `campanha:update`
- contatos GET → `campanha:read`; POST/bulk/DELETE → `campanha:update`
- `GET /api/conversas` + `/mensagens` → `inbox:read`
- `POST /api/conversas/{id}/mensagens` → `inbox:reply`
- `PUT /api/conversas/{id}/status` → `inbox:manage`

Example for two routes (apply the same pattern to all):
```python
@router.get("/api/campanhas", response_model=list[CampanhaPublic],
            dependencies=[Depends(require("campanha:read"))])
async def listar_campanhas(current_user: CurrentUser, service: CampanhaServiceDep):
    ...

@router.post("/api/campanhas", response_model=CampanhaPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require("campanha:create"))])
async def criar_campanha(data: CampanhaCreate, current_user: CurrentUser, service: CampanhaServiceDep):
    ...
```

- [ ] **Step 4: Add `require(...)` to whatsapp endpoints**

In `app/whatsapp/router.py`, add `from app.authz.dependencies import require` and `from fastapi import Depends`:
- `GET /api/whatsapp/instancias` + `/status` → `whatsapp:read`
- `POST /api/whatsapp/instancias` + `DELETE` + `/qrcode` → `whatsapp:manage`
- `POST .../mensagens/texto|midia` → `whatsapp:send`
- `POST /api/whatsapp/webhook` → **no** auth (public webhook; leave as-is).

- [ ] **Step 5: Run test to verify it passes**

Run: `task test -- app/tests/test_authz/test_whatsapp_campanha_perms.py app/tests/test_whatsapp/ -v`
Expected: PASS. (The existing whatsapp service tests are unaffected; the router tests there create OWNER-profile users via `make_tenant_user` if they touched permissions — they don't, they test service/landing, so they pass. If `test_whatsapp/test_whatsapp_service.py` router tests fail because they build `Usuario` with the old `role=`, update those fixtures to `role_profile_id=` using `make_tenant_user`.)

- [ ] **Step 6: Run the FULL suite**

Run: `task test`
Expected: all PASS. This is the security-fix completion gate — every cost-domain and messaging endpoint is now authenticated, permission-checked, and tenant-scoped.

- [ ] **Step 7: Commit**

```bash
git add app/whatsapp/router.py app/campanha/router.py app/tests/
git commit -m "feat(authz): permission-gate whatsapp + campanha routers

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

# Phase 4 — authz CRUD + register router

### Task 16: Roles CRUD (service + schemas + router)

**Files:**
- Modify: `app/authz/service.py`, `app/authz/schemas.py` (create), `app/authz/router.py` (create)
- Modify: `app/main.py` (register router)
- Test: `app/tests/test_authz/test_roles_crud.py`

**Interfaces:**
- Produces on `AuthzService`:
  - `async list_roles(tenant_id) -> list[Role]`
  - `async create_role(tenant_id, nome, descricao, permission_codes: list[str]) -> Role`
  - `async update_role(role, nome, descricao, permission_codes) -> Role`
  - `async delete_role(role) -> None` (raises `HTTPException 409` if `is_system`)
  - `async get_role(role_id, tenant_id) -> Role | None`
  - `async list_permissions() -> list[Permission]`

- [ ] **Step 1: Write the failing test**

`app/tests/test_authz/test_roles_crud.py`:
```python
import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


@pytest.mark.authz
async def test_owner_creates_custom_role(client: AsyncClient, session):
    _, owner = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    token = create_access_token({"sub": owner.username})
    h = {"Authorization": f"Bearer {token}"}
    r = await client.post("/api/authz/roles", headers=h,
                          json={"nome": "Caixa", "permission_codes": ["custo:read", "rateio:pay"]})
    assert r.status_code == 201
    assert set(r.json()["permission_codes"]) == {"custo:read", "rateio:pay"}


@pytest.mark.authz
async def test_cannot_delete_system_role(client: AsyncClient, session):
    _, owner = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    token = create_access_token({"sub": owner.username})
    h = {"Authorization": f"Bearer {token}"}
    roles = (await client.get("/api/authz/roles", headers=h)).json()
    fin = next(r for r in roles if r["nome"] == "Financeiro")
    r = await client.delete(f"/api/authz/roles/{fin['id']}", headers=h)
    assert r.status_code == 409


@pytest.mark.authz
async def test_leitor_cannot_manage_roles(client: AsyncClient, session):
    _, leitor = await make_tenant_user(session, tenant_nome="A", username="leitor", profile_nome="Leitor")
    token = create_access_token({"sub": leitor.username})
    r = await client.post("/api/authz/roles", headers={"Authorization": f"Bearer {token}"},
                          json={"nome": "X", "permission_codes": []})
    assert r.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

Run: `task test -- app/tests/test_authz/test_roles_crud.py -v`
Expected: FAIL — `/api/authz/roles` not registered.

- [ ] **Step 3: Add the schemas**

`app/authz/schemas.py`:
```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PermissionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    grupo: str
    descricao: str | None


class RoleCreate(BaseModel):
    nome: str
    descricao: str | None = None
    permission_codes: list[str] = []


class RoleUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    permission_codes: list[str] | None = None


class RolePublic(BaseModel):
    id: int
    nome: str
    descricao: str | None
    is_system: bool
    permission_codes: list[str]
    created_at: datetime
    updated_at: datetime


class ProfileCreate(BaseModel):
    nome: str
    descricao: str | None = None
    role_ids: list[int] = []


class ProfileUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    role_ids: list[int] | None = None


class ProfilePublic(BaseModel):
    id: int
    nome: str
    descricao: str | None
    is_system: bool
    is_protected: bool
    role_ids: list[int]
    created_at: datetime
    updated_at: datetime


class AssignProfileRequest(BaseModel):
    role_profile_id: int
```

- [ ] **Step 4: Add the role CRUD service methods**

Add to `AuthzService` in `app/authz/service.py` (import `HTTPException` from fastapi, `Permission`, `Role`):
```python
    async def list_permissions(self) -> list[Permission]:
        result = await self.session.execute(select(Permission).order_by(Permission.code))
        return list(result.scalars().all())

    async def list_roles(self, tenant_id: int) -> list[Role]:
        result = await self.session.execute(
            select(Role).where(Role.tenant_id == tenant_id).order_by(Role.nome)
        )
        return list(result.scalars().all())

    async def get_role(self, role_id: int, tenant_id: int) -> Role | None:
        result = await self.session.execute(
            select(Role).where(Role.id == role_id, Role.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def _perms_by_codes(self, codes: list[str]) -> list[Permission]:
        if not codes:
            return []
        result = await self.session.execute(
            select(Permission).where(Permission.code.in_(codes))
        )
        return list(result.scalars().all())

    async def create_role(self, tenant_id: int, nome: str, descricao: str | None,
                          permission_codes: list[str]) -> Role:
        role = Role(tenant_id=tenant_id, nome=nome, descricao=descricao, is_system=False)
        role.permissions = await self._perms_by_codes(permission_codes)
        self.session.add(role)
        await self.session.flush()
        await self.session.refresh(role)
        return role

    async def update_role(self, role: Role, nome: str | None, descricao: str | None,
                          permission_codes: list[str] | None) -> Role:
        if nome is not None:
            role.nome = nome
        if descricao is not None:
            role.descricao = descricao
        if permission_codes is not None:
            role.permissions = await self._perms_by_codes(permission_codes)
        await self.session.flush()
        await self.session.refresh(role)
        return role

    async def delete_role(self, role: Role) -> None:
        if role.is_system:
            from fastapi import HTTPException
            raise HTTPException(status_code=409, detail="Papel de sistema não pode ser removido")
        await self.session.delete(role)
```

- [ ] **Step 5: Create the authz router (roles part)**

`app/authz/router.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.current_user import CurrentUser
from app.authz.dependencies import require
from app.authz.schemas import (
    PermissionPublic,
    RoleCreate,
    RolePublic,
    RoleUpdate,
)
from app.authz.service import AuthzServiceDep

router = APIRouter(prefix="/api/authz", tags=["Authz"])


def _role_public(role) -> RolePublic:
    return RolePublic(
        id=role.id, nome=role.nome, descricao=role.descricao, is_system=role.is_system,
        permission_codes=[p.code for p in role.permissions],
        created_at=role.created_at, updated_at=role.updated_at,
    )


@router.get("/permissions", response_model=list[PermissionPublic],
            dependencies=[Depends(require("role:read"))])
async def list_permissions(service: AuthzServiceDep):
    return await service.list_permissions()


@router.get("/roles", response_model=list[RolePublic], dependencies=[Depends(require("role:read"))])
async def list_roles(current_user: CurrentUser, service: AuthzServiceDep):
    roles = await service.list_roles(current_user.tenant_id)
    return [_role_public(r) for r in roles]


@router.post("/roles", response_model=RolePublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require("role:manage"))])
async def create_role(data: RoleCreate, current_user: CurrentUser, service: AuthzServiceDep):
    role = await service.create_role(current_user.tenant_id, data.nome, data.descricao, data.permission_codes)
    return _role_public(role)


@router.put("/roles/{role_id}", response_model=RolePublic, dependencies=[Depends(require("role:manage"))])
async def update_role(role_id: int, data: RoleUpdate, current_user: CurrentUser, service: AuthzServiceDep):
    role = await service.get_role(role_id, current_user.tenant_id)
    if not role:
        raise HTTPException(status_code=404, detail="Papel não encontrado")
    role = await service.update_role(role, data.nome, data.descricao, data.permission_codes)
    return _role_public(role)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require("role:manage"))])
async def delete_role(role_id: int, current_user: CurrentUser, service: AuthzServiceDep):
    role = await service.get_role(role_id, current_user.tenant_id)
    if not role:
        raise HTTPException(status_code=404, detail="Papel não encontrado")
    await service.delete_role(role)
```

- [ ] **Step 6: Register the router**

In `app/main.py`, add import `from app.authz import router as authz_router` and `app.include_router(authz_router.router)` after `usuario_router`.

- [ ] **Step 7: Run test to verify it passes**

Run: `task test -- app/tests/test_authz/test_roles_crud.py -v`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add app/authz/schemas.py app/authz/router.py app/authz/service.py app/main.py app/tests/test_authz/test_roles_crud.py
git commit -m "feat(authz): roles CRUD endpoints + register authz router

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 17: Profiles CRUD + assign + anti-lockout

**Files:**
- Modify: `app/authz/service.py`, `app/authz/router.py`
- Test: `app/tests/test_authz/test_profiles_crud.py`

**Interfaces:**
- Produces on `AuthzService`:
  - `list_profiles(tenant_id)`, `create_profile(...)`, `update_profile(...)`, `delete_profile(...)`
  - `assign_profile(user_id, profile_id, tenant_id) -> Usuario`
  - `count_active_dono(tenant_id) -> int`
  - 409 on editing/deleting protected Dono; 409 if assigning away the last Dono holder.

- [ ] **Step 1: Write the failing test**

`app/tests/test_authz/test_profiles_crud.py`:
```python
import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token, get_password_hash
from app.tests.conftest import make_tenant_user


@pytest.mark.authz
async def test_cannot_edit_dono_profile(client: AsyncClient, session):
    _, owner = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    h = {"Authorization": f"Bearer {create_access_token({'sub': owner.username})}"}
    profiles = (await client.get("/api/authz/profiles", headers=h)).json()
    dono = next(p for p in profiles if p["nome"] == "Dono")
    r = await client.put(f"/api/authz/profiles/{dono['id']}", headers=h, json={"nome": "Hack"})
    assert r.status_code == 409


@pytest.mark.authz
async def test_create_and_assign_profile(client: AsyncClient, session):
    from app.usuario.models import Usuario
    tenant, owner = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    # add a member to reassign
    membro_profile = (await __import__("app.authz.service", fromlist=["AuthzService"])
                      .AuthzService(session)).__class__
    from app.authz.service import AuthzService
    svc = AuthzService(session)
    membro = await svc.get_profile_by_nome(tenant.id, "Membro")
    u = Usuario(username="m1", email="m1@e.com", password=get_password_hash("x"), nome="M1",
                tenant_id=tenant.id, role_profile_id=membro.id)
    session.add(u)
    await session.flush()

    h = {"Authorization": f"Bearer {create_access_token({'sub': owner.username})}"}
    roles = (await client.get("/api/authz/roles", headers=h)).json()
    leitura = next(r for r in roles if r["nome"] == "Leitura")
    created = await client.post("/api/authz/profiles", headers=h,
                                json={"nome": "Especial", "role_ids": [leitura["id"]]})
    assert created.status_code == 201
    pid = created.json()["id"]
    r = await client.put(f"/api/authz/usuarios/{u.id}/profile", headers=h,
                         json={"role_profile_id": pid})
    assert r.status_code == 200
    assert r.json()["role_profile_id"] == pid


@pytest.mark.authz
async def test_cannot_remove_last_dono(client: AsyncClient, session):
    tenant, owner = await make_tenant_user(session, tenant_nome="A", username="dono_a")
    from app.authz.service import AuthzService
    svc = AuthzService(session)
    leitor = await svc.get_profile_by_nome(tenant.id, "Leitor")
    h = {"Authorization": f"Bearer {create_access_token({'sub': owner.username})}"}
    # owner is the only Dono; reassigning them away must fail
    r = await client.put(f"/api/authz/usuarios/{owner.id}/profile", headers=h,
                         json={"role_profile_id": leitor.id})
    assert r.status_code == 409
```

- [ ] **Step 2: Run test to verify it fails**

Run: `task test -- app/tests/test_authz/test_profiles_crud.py -v`
Expected: FAIL — profile endpoints missing.

- [ ] **Step 3: Add profile service methods**

Add to `AuthzService` (`app/authz/service.py`), importing `Usuario`, `func`:
```python
    async def list_profiles(self, tenant_id: int) -> list[RoleProfile]:
        result = await self.session.execute(
            select(RoleProfile).where(RoleProfile.tenant_id == tenant_id).order_by(RoleProfile.nome)
        )
        return list(result.scalars().all())

    async def _roles_by_ids(self, tenant_id: int, role_ids: list[int]) -> list[Role]:
        if not role_ids:
            return []
        result = await self.session.execute(
            select(Role).where(Role.tenant_id == tenant_id, Role.id.in_(role_ids))
        )
        return list(result.scalars().all())

    async def create_profile(self, tenant_id: int, nome: str, descricao: str | None,
                             role_ids: list[int]) -> RoleProfile:
        profile = RoleProfile(tenant_id=tenant_id, nome=nome, descricao=descricao,
                              is_system=False, is_protected=False)
        profile.roles = await self._roles_by_ids(tenant_id, role_ids)
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def update_profile(self, profile: RoleProfile, nome: str | None, descricao: str | None,
                             role_ids: list[int] | None) -> RoleProfile:
        from fastapi import HTTPException
        if profile.is_protected:
            raise HTTPException(status_code=409, detail="Perfil protegido não pode ser editado")
        if nome is not None:
            profile.nome = nome
        if descricao is not None:
            profile.descricao = descricao
        if role_ids is not None:
            profile.roles = await self._roles_by_ids(profile.tenant_id, role_ids)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def delete_profile(self, profile: RoleProfile) -> None:
        from fastapi import HTTPException
        if profile.is_protected or profile.is_system:
            raise HTTPException(status_code=409, detail="Perfil de sistema não pode ser removido")
        await self.session.delete(profile)

    async def count_active_dono(self, tenant_id: int) -> int:
        from sqlalchemy import func
        from app.usuario.models import Usuario
        dono = await self.get_profile_by_nome(tenant_id, "Dono")
        if not dono:
            return 0
        result = await self.session.execute(
            select(func.count())
            .select_from(Usuario)
            .where(Usuario.role_profile_id == dono.id, Usuario.ativo == True)  # noqa: E712
        )
        return int(result.scalar_one())

    async def assign_profile(self, user_id: int, profile_id: int, tenant_id: int) -> "Usuario":
        from fastapi import HTTPException
        from app.usuario.models import Usuario

        user = await self.session.get(Usuario, user_id)
        if not user or user.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        target = await self.get_profile(profile_id, tenant_id)
        if not target:
            raise HTTPException(status_code=404, detail="Perfil não encontrado")

        dono = await self.get_profile_by_nome(tenant_id, "Dono")
        removing_last_dono = (
            user.role_profile_id == dono.id
            and target.id != dono.id
            and await self.count_active_dono(tenant_id) <= 1
        )
        if removing_last_dono:
            raise HTTPException(status_code=409, detail="Não é possível remover o último Dono")

        user.role_profile_id = profile_id
        await self.session.flush()
        await self.session.refresh(user)
        return user
```

- [ ] **Step 4: Add profile routes**

Append to `app/authz/router.py` (import the profile schemas + `AssignProfileRequest`, `UsuarioPublic`):
```python
def _profile_public(p) -> ProfilePublic:
    return ProfilePublic(
        id=p.id, nome=p.nome, descricao=p.descricao, is_system=p.is_system,
        is_protected=p.is_protected, role_ids=[r.id for r in p.roles],
        created_at=p.created_at, updated_at=p.updated_at,
    )


@router.get("/profiles", response_model=list[ProfilePublic], dependencies=[Depends(require("profile:read"))])
async def list_profiles(current_user: CurrentUser, service: AuthzServiceDep):
    return [_profile_public(p) for p in await service.list_profiles(current_user.tenant_id)]


@router.post("/profiles", response_model=ProfilePublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require("profile:manage"))])
async def create_profile(data: ProfileCreate, current_user: CurrentUser, service: AuthzServiceDep):
    p = await service.create_profile(current_user.tenant_id, data.nome, data.descricao, data.role_ids)
    return _profile_public(p)


@router.put("/profiles/{profile_id}", response_model=ProfilePublic, dependencies=[Depends(require("profile:manage"))])
async def update_profile(profile_id: int, data: ProfileUpdate, current_user: CurrentUser, service: AuthzServiceDep):
    p = await service.get_profile(profile_id, current_user.tenant_id)
    if not p:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    p = await service.update_profile(p, data.nome, data.descricao, data.role_ids)
    return _profile_public(p)


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require("profile:manage"))])
async def delete_profile(profile_id: int, current_user: CurrentUser, service: AuthzServiceDep):
    p = await service.get_profile(profile_id, current_user.tenant_id)
    if not p:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    await service.delete_profile(p)


@router.put("/usuarios/{usuario_id}/profile", response_model=UsuarioPublic,
            dependencies=[Depends(require("profile:assign"))])
async def assign_profile(usuario_id: int, data: AssignProfileRequest, current_user: CurrentUser,
                         service: AuthzServiceDep):
    return await service.assign_profile(usuario_id, data.role_profile_id, current_user.tenant_id)
```
Add to the imports at the top of `app/authz/router.py`:
```python
from app.authz.schemas import (
    AssignProfileRequest,
    PermissionPublic,
    ProfileCreate,
    ProfilePublic,
    ProfileUpdate,
    RoleCreate,
    RolePublic,
    RoleUpdate,
)
from app.usuario.schemas import UsuarioPublic
```

- [ ] **Step 5: Run test to verify it passes**

Run: `task test -- app/tests/test_authz/test_profiles_crud.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/authz/service.py app/authz/router.py app/tests/test_authz/test_profiles_crud.py
git commit -m "feat(authz): profiles CRUD + assign + anti-lockout

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 18: Backend smoke gate

**Files:**
- Test: `app/tests/test_authz/test_smoke.py`

- [ ] **Step 1: Write a smoke test that wires the whole flow**

`app/tests/test_authz/test_smoke.py`:
```python
import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token
from app.tests.conftest import make_tenant_user


@pytest.mark.authz
async def test_owner_full_flow(client: AsyncClient, session):
    tenant, owner = await make_tenant_user(session, tenant_nome="Casa", username="dono")
    h = {"Authorization": f"Bearer {create_access_token({'sub': owner.username})}"}

    me = (await client.get("/api/usuarios/me", headers=h)).json()
    assert me["role_profile"]["nome"] == "Dono"
    assert "custo:create" in me["permissions"]

    perms = (await client.get("/api/authz/permissions", headers=h)).json()
    assert any(p["code"] == "rateio:pay" for p in perms)

    mes = (await client.post("/api/meses/", headers=h, json={"ano": 2026, "mes": 7})).json()
    custo = (await client.post("/api/custos/", headers=h,
             json={"descricao": "Luz", "valor": "90.00",
                   "data_vencimento": "2026-07-10", "mes_referencia_id": mes["id"]})).json()
    rateio = await client.post("/api/rateios/", headers=h,
             json={"porcentagem": "100.00", "custo_id": custo["id"], "usuario_id": owner["id"]
                   if isinstance(owner, dict) else owner.id})
    assert rateio.status_code == 201
```

- [ ] **Step 2: Run the full suite**

Run: `task test`
Expected: all PASS.

- [ ] **Step 3: Commit**

```bash
git add app/tests/test_authz/test_smoke.py
git commit -m "test(authz): end-to-end owner smoke flow

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

# Phase 5 — Frontend gating

> No frontend test harness exists; these tasks use manual verification (build + browser). Run the app with `task up` and the Vite dev server. Fix the docker frontend ownership first if needed: `docker exec custos_app_dev chmod -R 777 /app/frontend/`.

### Task 19: Auth store + API client (permissions, can())

**Files:**
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/stores/auth.ts`

- [ ] **Step 1: Extend the API client**

In `frontend/src/api/client.ts`:
- Change the `Usuario` interface: replace `role: 'OWNER' | 'MEMBER'` with `role_profile_id: number | null`.
- Add interfaces:
```typescript
export interface UsuarioMe extends Usuario {
  role_profile: { id: number; nome: string } | null
  permissions: string[]
}
export interface Permission { id: number; code: string; grupo: string; descricao: string | null }
export interface Role { id: number; nome: string; descricao: string | null; is_system: boolean; permission_codes: string[] }
export interface Profile { id: number; nome: string; descricao: string | null; is_system: boolean; is_protected: boolean; role_ids: number[] }
```
- Change `getMe` to `apiClient.get<UsuarioMe>('/usuarios/me')`.
- Change `getMesAtual` path to `apiClient.get<MesReferencia>('/meses/atual')` (no tenant in path).
- Change `getMeses` to `apiClient.get<MesReferencia[]>('/meses/')` (drop the `tenant_id` param).
- Change `getUsuarios` to `apiClient.get<Usuario[]>('/usuarios/')` (drop `tenant_id` param).
- Change `createUsuario` payload: drop `tenant_id`/`role`; add optional `role_profile_id`.
- Change `getCustos` to require `mesReferenciaId` (it already passes it).
- Add authz calls:
```typescript
  // Authz
  getPermissions: () => apiClient.get<Permission[]>('/authz/permissions'),
  getRoles: () => apiClient.get<Role[]>('/authz/roles'),
  createRole: (data: { nome: string; descricao?: string; permission_codes: string[] }) =>
    apiClient.post<Role>('/authz/roles', data),
  updateRole: (id: number, data: { nome?: string; descricao?: string; permission_codes?: string[] }) =>
    apiClient.put<Role>(`/authz/roles/${id}`, data),
  deleteRole: (id: number) => apiClient.delete(`/authz/roles/${id}`),
  getProfiles: () => apiClient.get<Profile[]>('/authz/profiles'),
  createProfile: (data: { nome: string; descricao?: string; role_ids: number[] }) =>
    apiClient.post<Profile>('/authz/profiles', data),
  updateProfile: (id: number, data: { nome?: string; descricao?: string; role_ids?: number[] }) =>
    apiClient.put<Profile>(`/authz/profiles/${id}`, data),
  deleteProfile: (id: number) => apiClient.delete(`/authz/profiles/${id}`),
  assignProfile: (usuarioId: number, profileId: number) =>
    apiClient.put<Usuario>(`/authz/usuarios/${usuarioId}/profile`, { role_profile_id: profileId }),
  getMyTenant: () => apiClient.get('/tenants/me'),
```

- [ ] **Step 2: Update the auth store**

In `frontend/src/stores/auth.ts`:
- Remove `role` state. Add:
```typescript
  const permissions = ref<string[]>(
    JSON.parse(sessionStorage.getItem('permissions') || '[]'),
  )
  function can(code: string): boolean {
    return permissions.value.includes(code)
  }
```
- In `login`, after `const me = await api.getMe()`:
```typescript
      tenantId.value = me.data.tenant_id
      userId.value = me.data.id
      permissions.value = me.data.permissions
      sessionStorage.setItem('tenant_id', String(me.data.tenant_id))
      sessionStorage.setItem('user_id', String(me.data.id))
      sessionStorage.setItem('permissions', JSON.stringify(me.data.permissions))
```
- Remove `role` and `isOwner`. In `logout`, also `sessionStorage.removeItem('permissions')` and `permissions.value = []`.
- Return `permissions, can` (drop `role, isOwner`).

- [ ] **Step 3: Manual verification**

Run `task up`; log in as `juan` (after `populate_data`). In browser devtools console: `JSON.parse(sessionStorage.permissions)` should list permission codes. Custos/Rateios pages still load (owner has all perms).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api/client.ts frontend/src/stores/auth.ts
git commit -m "feat(authz-fe): permissions in auth store + authz API client

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 20: Router guards + nav gating

**Files:**
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: Add permission meta + guard**

In `frontend/src/router/index.ts`:
- Add `meta: { requiresAuth: true, permission: 'campanha:read' }` to `/campanhas` and `/campanhas/:id`; `permission: 'inbox:read'` to `/inbox`; `permission: 'custo:read'` to `/custos`; `permission: 'usuario:read'` to `/membros`. Add a new route `/perfis` (Task 22) with `permission: 'role:read'`.
- Extend `beforeEach`:
```typescript
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const adminStore = useAdminAuthStore()

  if (to.meta.requiresAdmin && !adminStore.isAuthenticated) {
    next('/admin/login')
  } else if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.permission && !authStore.can(to.meta.permission as string)) {
    next('/custos')
  } else {
    next()
  }
})
```

- [ ] **Step 2: Gate the sidebar nav**

In `frontend/src/App.vue`:
- Add a `permission` field to each `navItems` entry: Custos→`custo:read`, Membros→`usuario:read`, Campanhas→`campanha:read`, Inbox→`inbox:read`. Add a "Perfis" item → `role:read` (route `/perfis`).
- In `<script setup>`, compute visible items:
```typescript
import { useAuthStore } from './stores/auth'
const authStore = useAuthStore()
const visibleNav = computed(() => navItems.filter(i => !i.permission || authStore.can(i.permission)))
```
- In the template `v-for`, iterate `visibleNav` instead of `navItems`.

- [ ] **Step 3: Manual verification**

Log in as a Leitor (create one via the new Perfis screen later, or temporarily assign via DB). Confirm nav hides Campanhas/Membros and visiting `/campanhas` redirects to `/custos`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/router/index.ts frontend/src/App.vue
git commit -m "feat(authz-fe): route guards + nav gating by permission

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 21: Gate action buttons + profile assignment in Membros

**Files:**
- Modify: `frontend/src/views/UsuariosView.vue`
- Modify: `frontend/src/views/CustosView.vue`
- Modify: `frontend/src/views/RateiosView.vue`
- Modify: `frontend/src/views/CampanhasView.vue`, `frontend/src/views/CampanhaDetalheView.vue`, `frontend/src/views/InboxView.vue`

- [ ] **Step 1: UsuariosView — profile dropdown + gating**

In `frontend/src/views/UsuariosView.vue`:
- Import store: `const authStore = useAuthStore()` (already there).
- Replace `v-if="authStore.isOwner"` on the "Convidar membro" button with `v-if="authStore.can('usuario:create')"`.
- Replace `v-if="authStore.isOwner && usuario.id !== authStore.userId && usuario.role !== 'OWNER'"` on the delete button with `v-if="authStore.can('usuario:delete') && usuario.id !== authStore.userId"`.
- Load profiles on mount: `const profiles = ref<Profile[]>([])` + `api.getProfiles().then(r => profiles.value = r.data)`.
- Add a profile `<select>` to the create form bound to `form.role_profile_id`, options from `profiles`.
- In `criarUsuario`, send `role_profile_id: form.role_profile_id` and drop `tenant_id`/`role`.
- Show each user's profile name: map `usuario.role_profile_id` → `profiles` name; render in the card. Add an inline "alterar perfil" `<select>` gated by `authStore.can('profile:assign')` that calls `api.assignProfile(usuario.id, pid)`.

- [ ] **Step 2: CustosView — gate buttons**

In `frontend/src/views/CustosView.vue` add `const authStore = useAuthStore()` (already imported) and:
- "Novo custo" button: `v-if="authStore.can('custo:create')"`.
- Edit button: `v-if="authStore.can('custo:update')"`; Delete: `v-if="authStore.can('custo:delete')"`.
- In the rateio drawer: "Adicionar rateio" form gated `authStore.can('rateio:create')`; "marcar pago" gated `authStore.can('rateio:pay')`; remove gated `authStore.can('rateio:delete')`; upload gated `authStore.can('comprovante:upload')`.

- [ ] **Step 3: RateiosView — gate buttons**

In `frontend/src/views/RateiosView.vue`: import `useAuthStore`; gate "marcar pago" with `authStore.can('rateio:pay')` and the delete button with `authStore.can('rateio:delete')`.

- [ ] **Step 4: Campaign + Inbox views**

- `CampanhasView.vue`: "Nova Campanha" button `v-if="authStore.can('campanha:create')"`.
- `CampanhaDetalheView.vue`: Ativar/Pausar/Concluir `v-if="authStore.can('campanha:activate')"`; "Salvar configurações"/templates/contatos edits `v-if="authStore.can('campanha:update')"`.
- `InboxView.vue`: message input + "Enviar" `v-if="authStore.can('inbox:reply')"`; "Encerrar conversa" `v-if="authStore.can('inbox:manage')"`.

(Import `useAuthStore` and instantiate `authStore` in each `<script setup>` that doesn't already have it.)

- [ ] **Step 5: Manual verification**

Log in as Membro (Membro profile lacks `custo:create`, `campanha:create`): confirm those buttons are hidden, but "marcar pago" (in Membro Base) is visible. Log in as Dono: everything visible.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/
git commit -m "feat(authz-fe): gate action buttons + profile assignment by permission

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 22: "Perfis & Papéis" management view

**Files:**
- Create: `frontend/src/views/RolesView.vue`
- Modify: `frontend/src/router/index.ts` (route added in Task 20 step 1 — wire component here)

- [ ] **Step 1: Create the management view**

`frontend/src/views/RolesView.vue` — two panels: Roles (left) and Profiles (right). Use the existing inline-style visual language of the app. Concretely:
```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, type Permission, type Role, type Profile } from '../api/client'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const permissions = ref<Permission[]>([])
const roles = ref<Role[]>([])
const profiles = ref<Profile[]>([])
const loading = ref(true)

const roleForm = ref<{ id: number | null; nome: string; permission_codes: string[] }>({ id: null, nome: '', permission_codes: [] })
const profileForm = ref<{ id: number | null; nome: string; role_ids: number[] }>({ id: null, nome: '', role_ids: [] })

async function carregar() {
  loading.value = true
  try {
    const [p, r, pr] = await Promise.all([api.getPermissions(), api.getRoles(), api.getProfiles()])
    permissions.value = p.data; roles.value = r.data; profiles.value = pr.data
  } finally { loading.value = false }
}

function togglePerm(code: string) {
  const i = roleForm.value.permission_codes.indexOf(code)
  if (i === -1) roleForm.value.permission_codes.push(code); else roleForm.value.permission_codes.splice(i, 1)
}
function toggleRole(id: number) {
  const i = profileForm.value.role_ids.indexOf(id)
  if (i === -1) profileForm.value.role_ids.push(id); else profileForm.value.role_ids.splice(i, 1)
}

async function salvarRole() {
  if (roleForm.value.id) await api.updateRole(roleForm.value.id, roleForm.value)
  else await api.createRole(roleForm.value)
  roleForm.value = { id: null, nome: '', permission_codes: [] }
  await carregar()
}
function editarRole(r: Role) { roleForm.value = { id: r.id, nome: r.nome, permission_codes: [...r.permission_codes] } }
async function removerRole(r: Role) { if (confirm(`Remover ${r.nome}?`)) { await api.deleteRole(r.id).catch(e => alert(e.response?.data?.detail)); await carregar() } }

async function salvarProfile() {
  if (profileForm.value.id) await api.updateProfile(profileForm.value.id, profileForm.value).catch(e => alert(e.response?.data?.detail))
  else await api.createProfile(profileForm.value)
  profileForm.value = { id: null, nome: '', role_ids: [] }
  await carregar()
}
function editarProfile(p: Profile) { profileForm.value = { id: p.id, nome: p.nome, role_ids: [...p.role_ids] } }
async function removerProfile(p: Profile) { if (confirm(`Remover ${p.nome}?`)) { await api.deleteProfile(p.id).catch(e => alert(e.response?.data?.detail)); await carregar() } }

onMounted(carregar)
</script>

<template>
  <div style="display:flex;flex-direction:column;height:100%;">
    <div style="height:64px;border-bottom:1px solid #e2e8f0;background:white;display:flex;align-items:center;padding:0 24px;flex-shrink:0;">
      <div>
        <h1 style="font-size:15px;font-weight:600;color:#0f172a;margin:0;">Perfis &amp; Papéis</h1>
        <p style="font-size:12px;color:#64748b;margin:0;">Controle de permissões do seu grupo</p>
      </div>
    </div>
    <div style="flex:1;overflow:auto;padding:24px;display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start;">

      <!-- Roles -->
      <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:20px;">
        <h2 style="font-size:13px;font-weight:700;color:#0f172a;margin:0 0 12px;">Papéis</h2>
        <div v-for="r in roles" :key="r.id" style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9;">
          <span style="font-size:13px;color:#0f172a;">{{ r.nome }} <span v-if="r.is_system" style="font-size:10px;color:#94a3b8;">(sistema)</span></span>
          <span v-if="authStore.can('role:manage')">
            <button @click="editarRole(r)" style="font-size:11px;color:#4f46e5;background:none;border:none;cursor:pointer;">editar</button>
            <button v-if="!r.is_system" @click="removerRole(r)" style="font-size:11px;color:#dc2626;background:none;border:none;cursor:pointer;">remover</button>
          </span>
        </div>
        <div v-if="authStore.can('role:manage')" style="margin-top:14px;border-top:1px solid #e2e8f0;padding-top:14px;">
          <input v-model="roleForm.nome" placeholder="Nome do papel" style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;box-sizing:border-box;margin-bottom:8px;" />
          <div style="max-height:200px;overflow:auto;display:flex;flex-direction:column;gap:4px;margin-bottom:8px;">
            <label v-for="p in permissions" :key="p.id" style="font-size:12px;color:#334155;display:flex;gap:6px;align-items:center;">
              <input type="checkbox" :checked="roleForm.permission_codes.includes(p.code)" @change="togglePerm(p.code)" />
              <code style="font-size:11px;">{{ p.code }}</code>
            </label>
          </div>
          <button @click="salvarRole" style="background:#4f46e5;color:white;font-size:13px;font-weight:600;padding:8px;border-radius:8px;border:none;cursor:pointer;width:100%;">
            {{ roleForm.id ? 'Salvar papel' : 'Criar papel' }}
          </button>
        </div>
      </div>

      <!-- Profiles -->
      <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:20px;">
        <h2 style="font-size:13px;font-weight:700;color:#0f172a;margin:0 0 12px;">Perfis</h2>
        <div v-for="p in profiles" :key="p.id" style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9;">
          <span style="font-size:13px;color:#0f172a;">{{ p.nome }} <span v-if="p.is_protected" style="font-size:10px;color:#d97706;">(protegido)</span></span>
          <span v-if="authStore.can('profile:manage') && !p.is_protected">
            <button @click="editarProfile(p)" style="font-size:11px;color:#4f46e5;background:none;border:none;cursor:pointer;">editar</button>
            <button v-if="!p.is_system" @click="removerProfile(p)" style="font-size:11px;color:#dc2626;background:none;border:none;cursor:pointer;">remover</button>
          </span>
        </div>
        <div v-if="authStore.can('profile:manage')" style="margin-top:14px;border-top:1px solid #e2e8f0;padding-top:14px;">
          <input v-model="profileForm.nome" placeholder="Nome do perfil" style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;box-sizing:border-box;margin-bottom:8px;" />
          <div style="display:flex;flex-direction:column;gap:4px;margin-bottom:8px;">
            <label v-for="r in roles" :key="r.id" style="font-size:12px;color:#334155;display:flex;gap:6px;align-items:center;">
              <input type="checkbox" :checked="profileForm.role_ids.includes(r.id)" @change="toggleRole(r.id)" />
              {{ r.nome }}
            </label>
          </div>
          <button @click="salvarProfile" style="background:#4f46e5;color:white;font-size:13px;font-weight:600;padding:8px;border-radius:8px;border:none;cursor:pointer;width:100%;">
            {{ profileForm.id ? 'Salvar perfil' : 'Criar perfil' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Wire the route**

In `frontend/src/router/index.ts`, add to the authenticated routes:
```typescript
    {
      path: '/perfis',
      name: 'perfis',
      component: () => import('../views/RolesView.vue'),
      meta: { requiresAuth: true, permission: 'role:read' },
    },
```

- [ ] **Step 3: Manual verification**

As Dono: open `/perfis`. Create a role "Caixa" with `custo:read`+`rateio:pay`; create a profile "Operador" with that role; go to Membros and assign it to a member; log in as that member and confirm gated UI matches. Confirm Dono profile shows "(protegido)" and has no edit/remove buttons.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/RolesView.vue frontend/src/router/index.ts
git commit -m "feat(authz-fe): Perfis & Papéis management view

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review (completed)

**Spec coverage:** Data model (Tasks 2, 8) · permission catalog (Task 1) · per-tenant defaults (Task 5) · anti-lockout (Tasks 5, 17) · enforcement `require()` (Task 4) · tenant isolation across all open routers (Tasks 9–14) · whatsapp/campanha gating (Task 15) · authz CRUD + `/me` (Tasks 9, 16, 17) · migration + call-sites (Tasks 7, 8) · frontend gating + management UI (Tasks 19–22) · tests + `authz` marker (every backend task). All spec sections map to a task.

**Placeholder scan:** The one ugly `__import__` line in Task 13 is immediately followed by the clean import replacement; implementer uses the clean version. No TBD/TODO left.

**Type consistency:** `resolve_permissions(user) -> set[str]`, `require(*codes)`, `seed_tenant_defaults -> RoleProfile`, `get_profile(profile_id, tenant_id)`, `get_profile_by_nome(tenant_id, nome)`, `assign_profile(user_id, profile_id, tenant_id)` used consistently across tasks. `UsuarioCreate` (no tenant_id/role) and `UsuarioService.create(data, tenant_id, role_profile_id)` consistent between Tasks 6, 7, 9.

**Note for executor:** xfail markers added in Tasks 3/4/5 are removed in Task 6 — do not skip that cleanup. The full-suite gate is Task 15 Step 6 (security fix complete) and Task 18 (end-to-end).
