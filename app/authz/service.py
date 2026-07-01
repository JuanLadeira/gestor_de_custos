from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz import catalog
from app.authz.catalog import DEFAULT_PROFILES, DEFAULT_ROLES
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

    async def get_profile(self, profile_id: int, tenant_id: int) -> RoleProfile | None:
        result = await self.session.execute(
            select(RoleProfile).where(
                RoleProfile.id == profile_id, RoleProfile.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()

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
