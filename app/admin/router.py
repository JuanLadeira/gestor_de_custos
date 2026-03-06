from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.admin.current_admin import CurrentAdmin
from app.admin.schemas import AdminCreate, AdminPublic, Token
from app.admin.services import AdminServiceDep
from app.assinatura.schemas import AssinaturaPublic, AssinaturaUpdate
from app.assinatura.services import AssinaturaServiceDep
from app.auth.security import create_access_token, verify_password
from app.plano.schemas import PlanoCreate, PlanoPublic, PlanoUpdate
from app.plano.services import PlanoServiceDep
from app.tenant.schemas import TenantCreate, TenantPublic, TenantUpdate
from app.tenant.services import TenantServiceDep

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


# ─── Assinaturas ──────────────────────────────────────────────────────────────

@router.get("/assinaturas", response_model=list[AssinaturaPublic])
async def list_assinaturas(_: CurrentAdmin, service: AssinaturaServiceDep):
    return await service.get_all()


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


# ─── Admin management (bootstrap) ────────────────────────────────────────────

@router.post("/admins", response_model=AdminPublic, status_code=status.HTTP_201_CREATED)
async def create_admin(
    data: AdminCreate, _: CurrentAdmin, service: AdminServiceDep
):
    existing = await service.get_by_username(data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username já existe")
    return await service.create(data)
