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

        dono = await self.get_profile_by_nome(tenant_id, "Dono")
        if not dono:
            return 0
        result = await self.session.execute(
            select(func.count())
            .select_from(Usuario)
            .where(Usuario.role_profile_id == dono.id, Usuario.ativo == True)  # noqa: E712
        )
        return int(result.scalar_one())

    async def assign_profile(self, user_id: int, profile_id: int, tenant_id: int) -> Usuario:
        from fastapi import HTTPException

        user = await self.session.get(Usuario, user_id)
        if not user or user.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        target = await self.get_profile(profile_id, tenant_id)
        if not target:
            raise HTTPException(status_code=404, detail="Perfil não encontrado")

        dono = await self.get_profile_by_nome(tenant_id, "Dono")
        removing_last_dono = (
            dono is not None
            and user.role_profile_id == dono.id
            and target.id != dono.id
            and await self.count_active_dono(tenant_id) <= 1
        )
        if removing_last_dono:
            raise HTTPException(status_code=409, detail="Não é possível remover o último Dono")

        user.role_profile_id = profile_id
        await self.session.flush()
        await self.session.refresh(user)
        return user


def get_authz_service(session: AsyncDBSession) -> AuthzService:
    return AuthzService(session)


AuthzServiceDep = Annotated[AuthzService, Depends(get_authz_service)]
