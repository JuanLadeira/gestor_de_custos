from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.current_user import CurrentUser
from app.authz.dependencies import require
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
from app.authz.service import AuthzServiceDep
from app.usuario.schemas import UsuarioPublic

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
