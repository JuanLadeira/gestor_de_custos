from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.current_user import CurrentUser
from app.authz.dependencies import require
from app.custo_fixo.schemas import CustoFixoCreate, CustoFixoPublic, CustoFixoUpdate
from app.custo_fixo.services import CustoFixoServiceDep

router = APIRouter(
    prefix="/api/custos-fixos",
    tags=["Custos Fixos"],
    responses={404: {"description": "Nao encontrado"}},
)


@router.get("/", response_model=list[CustoFixoPublic], dependencies=[Depends(require("custo_fixo:read"))])
async def list_custos_fixos(current_user: CurrentUser, service: CustoFixoServiceDep):
    return await service.get_all(tenant_id=current_user.tenant_id)


@router.get("/{custo_fixo_id}", response_model=CustoFixoPublic, dependencies=[Depends(require("custo_fixo:read"))])
async def get_custo_fixo(custo_fixo_id: int, current_user: CurrentUser, service: CustoFixoServiceDep):
    cf = await service.get_scoped(custo_fixo_id, current_user.tenant_id)
    if not cf:
        raise HTTPException(status_code=404, detail="Custo fixo nao encontrado")
    return cf


@router.post("/", response_model=CustoFixoPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require("custo_fixo:create"))])
async def create_custo_fixo(data: CustoFixoCreate, current_user: CurrentUser, service: CustoFixoServiceDep):
    return await service.create(data, tenant_id=current_user.tenant_id)


@router.put("/{custo_fixo_id}", response_model=CustoFixoPublic, dependencies=[Depends(require("custo_fixo:update"))])
async def update_custo_fixo(custo_fixo_id: int, data: CustoFixoUpdate, current_user: CurrentUser, service: CustoFixoServiceDep):
    cf = await service.get_scoped(custo_fixo_id, current_user.tenant_id)
    if not cf:
        raise HTTPException(status_code=404, detail="Custo fixo nao encontrado")
    return await service.update(cf, data)


@router.delete("/{custo_fixo_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require("custo_fixo:delete"))])
async def delete_custo_fixo(custo_fixo_id: int, current_user: CurrentUser, service: CustoFixoServiceDep):
    cf = await service.get_scoped(custo_fixo_id, current_user.tenant_id)
    if not cf:
        raise HTTPException(status_code=404, detail="Custo fixo nao encontrado")
    await service.delete(cf)
