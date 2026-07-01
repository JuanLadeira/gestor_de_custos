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
