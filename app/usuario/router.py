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
            raise HTTPException(status_code=404, detail="Perfil não encontrado")
    return await service.create(data, tenant_id=current_user.tenant_id, role_profile_id=profile_id)


@router.put("/{usuario_id}", response_model=UsuarioPublic,
            dependencies=[Depends(require("usuario:update"))])
async def update_usuario(
    usuario_id: int,
    data: UsuarioUpdate,
    current_user: CurrentUser,
    service: UsuarioServiceDep,
    authz: AuthzServiceDep,
):
    usuario = await service.get_by_id(usuario_id)
    if not usuario or usuario.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    # Anti-lockout: block deactivating the last active Dono.
    # (Profile reassignment goes through PUT /usuarios/{id}/profile, guarded separately.)
    if data.ativo is False and usuario.ativo:
        dono = await authz.get_profile_by_nome(current_user.tenant_id, "Dono")
        if dono and usuario.role_profile_id == dono.id and await authz.count_active_dono(current_user.tenant_id) <= 1:
            raise HTTPException(status_code=409, detail="Não é possível remover o último Dono")

    return await service.update(usuario_id, data)


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require("usuario:delete"))])
async def delete_usuario(usuario_id: int, current_user: CurrentUser, service: UsuarioServiceDep):
    usuario = await service.get_by_id(usuario_id)
    if not usuario or usuario.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    await service.delete(usuario_id)
