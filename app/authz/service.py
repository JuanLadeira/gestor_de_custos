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
