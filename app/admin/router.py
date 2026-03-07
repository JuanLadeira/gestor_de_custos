from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.admin.current_admin import CurrentAdmin
from app.admin.schemas import AdminCreate, AdminPublic, Token
from app.admin.services import AdminServiceDep
from app.whatsapp.schemas import InstanciaCreate, InstanciaPublic, InstanciaResumoStatus
from app.whatsapp.services import WhatsappServiceDep
from app.assinatura.schemas import (
    AssinaturaAdminPublic,
    AssinaturaCreate,
    AssinaturaPublic,
    AssinaturaUpdate,
)
from app.assinatura.services import AssinaturaServiceDep
from app.auth.security import create_access_token, verify_password
from app.plano.schemas import PlanoCreate, PlanoPublic, PlanoUpdate
from app.plano.services import PlanoServiceDep
from app.tenant.schemas import TenantCreate, TenantPublic, TenantUpdate
from app.tenant.services import TenantServiceDep
from app.usuario.schemas import UsuarioCreate, UsuarioCreateAdmin, UsuarioPublic, UsuarioUpdate
from app.usuario.services import UsuarioServiceDep

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.post("/login", response_model=Token)
async def admin_login(
    service: AdminServiceDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    admin = await service.get_by_username(form_data.username)
    if not admin or not verify_password(form_data.password, admin.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not admin.ativo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin inativo")

    access_token = create_access_token(data={"sub": f"admin:{admin.username}"})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=AdminPublic)
async def admin_me(current_admin: CurrentAdmin):
    return current_admin


# ─── Tenants ──────────────────────────────────────────────────────────────────

@router.get("/tenants", response_model=list[TenantPublic])
async def list_tenants(_: CurrentAdmin, service: TenantServiceDep):
    return await service.get_all()


@router.post("/tenants", response_model=TenantPublic, status_code=status.HTTP_201_CREATED)
async def create_tenant(_: CurrentAdmin, data: TenantCreate, service: TenantServiceDep):
    return await service.create(data)


@router.put("/tenants/{tenant_id}", response_model=TenantPublic)
async def update_tenant(
    tenant_id: int, data: TenantUpdate, _: CurrentAdmin, service: TenantServiceDep
):
    tenant = await service.update(tenant_id, data)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    return tenant


@router.delete("/tenants/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(tenant_id: int, _: CurrentAdmin, service: TenantServiceDep):
    deleted = await service.delete(tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")


# ─── Planos ───────────────────────────────────────────────────────────────────

@router.get("/planos", response_model=list[PlanoPublic])
async def list_planos(_: CurrentAdmin, service: PlanoServiceDep):
    return await service.get_all()


@router.post("/planos", response_model=PlanoPublic, status_code=status.HTTP_201_CREATED)
async def create_plano(_: CurrentAdmin, data: PlanoCreate, service: PlanoServiceDep):
    return await service.create(data)


@router.put("/planos/{plano_id}", response_model=PlanoPublic)
async def update_plano(
    plano_id: int, data: PlanoUpdate, _: CurrentAdmin, service: PlanoServiceDep
):
    plano = await service.update(plano_id, data)
    if not plano:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    return plano


@router.delete("/planos/{plano_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plano(plano_id: int, _: CurrentAdmin, service: PlanoServiceDep):
    deleted = await service.delete(plano_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Plano não encontrado")


# ─── Tenant → Usuários ────────────────────────────────────────────────────────

@router.get("/tenants/{tenant_id}/usuarios", response_model=list[UsuarioPublic])
async def list_tenant_usuarios(
    tenant_id: int, _: CurrentAdmin, service: UsuarioServiceDep
):
    return await service.get_all(tenant_id=tenant_id)


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
):
    existing = await service.get_by_username(data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username já existe")
    create_data = UsuarioCreate(tenant_id=tenant_id, **data.model_dump())
    return await service.create(create_data)


@router.put("/usuarios/{usuario_id}", response_model=UsuarioPublic)
async def update_usuario(
    usuario_id: int, data: UsuarioUpdate, _: CurrentAdmin, service: UsuarioServiceDep
):
    usuario = await service.update(usuario_id, data)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario


@router.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_usuario(usuario_id: int, _: CurrentAdmin, service: UsuarioServiceDep):
    deleted = await service.delete(usuario_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")


# ─── Tenant → Assinatura ──────────────────────────────────────────────────────

@router.get("/tenants/{tenant_id}/assinatura", response_model=AssinaturaPublic | None)
async def get_tenant_assinatura(
    tenant_id: int, _: CurrentAdmin, service: AssinaturaServiceDep
):
    return await service.get_by_tenant(tenant_id)


@router.post(
    "/tenants/{tenant_id}/assinatura",
    response_model=AssinaturaPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_tenant_assinatura(
    tenant_id: int,
    data: AssinaturaCreate,
    _: CurrentAdmin,
    service: AssinaturaServiceDep,
):
    existing = await service.get_by_tenant(tenant_id)
    if existing:
        raise HTTPException(status_code=400, detail="Tenant já possui assinatura")
    return await service.create(
        tenant_id=tenant_id, plano_id=data.plano_id, status=data.status
    )


# ─── Assinaturas ──────────────────────────────────────────────────────────────

@router.get("/assinaturas", response_model=list[AssinaturaAdminPublic])
async def list_assinaturas(_: CurrentAdmin, service: AssinaturaServiceDep):
    assinaturas = await service.get_all_admin()
    return [
        AssinaturaAdminPublic(
            **AssinaturaPublic.model_validate(a).model_dump(),
            tenant_nome=a.tenant.nome,
            plano_nome=a.plano.nome,
        )
        for a in assinaturas
    ]


@router.put("/assinaturas/{assinatura_id}", response_model=AssinaturaPublic)
async def update_assinatura(
    assinatura_id: int,
    data: AssinaturaUpdate,
    _: CurrentAdmin,
    service: AssinaturaServiceDep,
):
    assinatura = await service.update(assinatura_id, data)
    if not assinatura:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")
    return assinatura


# ─── WhatsApp ─────────────────────────────────────────────────────────────────

@router.get("/whatsapp/instancias", response_model=list[InstanciaPublic])
async def list_all_instancias(_: CurrentAdmin, service: WhatsappServiceDep):
    return await service.listar_todas_instancias()


@router.get("/whatsapp/instancias/resumo", response_model=InstanciaResumoStatus)
async def resumo_instancias(_: CurrentAdmin, service: WhatsappServiceDep):
    return await service.resumo_status()


@router.get(
    "/whatsapp/instancias/{instancia_id}/status", response_model=InstanciaPublic
)
async def sincronizar_instancia_status(
    instancia_id: int, _: CurrentAdmin, service: WhatsappServiceDep
):
    instancia = await service.obter_instancia_por_id(instancia_id)
    if not instancia:
        raise HTTPException(status_code=404, detail="Instância não encontrada")
    return await service.sincronizar_status(instancia)


@router.get("/tenants/{tenant_id}/whatsapp", response_model=list[InstanciaPublic])
async def list_tenant_instancias(
    tenant_id: int, _: CurrentAdmin, service: WhatsappServiceDep
):
    return await service.listar_instancias(tenant_id)


@router.post(
    "/tenants/{tenant_id}/whatsapp",
    response_model=InstanciaPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_tenant_instancia(
    tenant_id: int,
    data: InstanciaCreate,
    _: CurrentAdmin,
    service: WhatsappServiceDep,
):
    return await service.criar_instancia(tenant_id, data)


@router.delete("/whatsapp/instancias/{instancia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_instancia(
    instancia_id: int, _: CurrentAdmin, service: WhatsappServiceDep
):
    instancia = await service.obter_instancia_por_id(instancia_id)
    if not instancia:
        raise HTTPException(status_code=404, detail="Instância não encontrada")
    await service.deletar_instancia(instancia)


# ─── Admin management (bootstrap) ────────────────────────────────────────────

@router.post("/admins", response_model=AdminPublic, status_code=status.HTTP_201_CREATED)
async def create_admin(
    data: AdminCreate, _: CurrentAdmin, service: AdminServiceDep
):
    existing = await service.get_by_username(data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username já existe")
    return await service.create(data)
