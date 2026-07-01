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
