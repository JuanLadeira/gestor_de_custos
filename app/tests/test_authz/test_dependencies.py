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
@pytest.mark.xfail(reason="needs role_profile_id (Task 6)", strict=False)
async def test_require_allows_with_permission(mini_app, session):
    user = await _seed_user_with_codes(session, ["custo:create"])
    token = create_access_token({"sub": user.username})
    async with AsyncClient(transport=ASGITransport(app=mini_app), base_url="http://t") as c:
        r = await c.get("/needs-custo-create", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


@pytest.mark.authz
@pytest.mark.xfail(reason="needs role_profile_id (Task 6)", strict=False)
async def test_require_forbids_without_permission(mini_app, session):
    user = await _seed_user_with_codes(session, ["custo:read"])
    token = create_access_token({"sub": user.username})
    async with AsyncClient(transport=ASGITransport(app=mini_app), base_url="http://t") as c:
        r = await c.get("/needs-custo-create", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
