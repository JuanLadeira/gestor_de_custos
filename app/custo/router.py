from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.current_user import CurrentUser
from app.authz.dependencies import require
from app.custo.schemas import CustoCreate, CustoPublic, CustoUpdate
from app.custo.services import CustoServiceDep
from app.mes_referencia.services import MesReferenciaServiceDep

router = APIRouter(
    prefix="/api/custos",
    tags=["Custos"],
    responses={404: {"description": "Nao encontrado"}},
)


@router.get("/", response_model=list[CustoPublic], dependencies=[Depends(require("custo:read"))])
async def list_custos(
    current_user: CurrentUser,
    service: CustoServiceDep,
    mes_service: MesReferenciaServiceDep,
    mes_referencia_id: int,
):
    mes = await mes_service.get_by_id_scoped(mes_referencia_id, current_user.tenant_id)
    if not mes:
        raise HTTPException(status_code=404, detail="Mes de referencia nao encontrado")
    return await service.get_all(mes_referencia_id=mes_referencia_id)


@router.get("/{custo_id}", response_model=CustoPublic, dependencies=[Depends(require("custo:read"))])
async def get_custo(custo_id: int, current_user: CurrentUser, service: CustoServiceDep):
    custo = await service.get_scoped(custo_id, current_user.tenant_id)
    if not custo:
        raise HTTPException(status_code=404, detail="Custo nao encontrado")
    return custo


@router.post("/", response_model=CustoPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require("custo:create"))])
async def create_custo(
    data: CustoCreate,
    current_user: CurrentUser,
    service: CustoServiceDep,
    mes_service: MesReferenciaServiceDep,
):
    mes = await mes_service.get_by_id_scoped(data.mes_referencia_id, current_user.tenant_id)
    if not mes:
        raise HTTPException(status_code=404, detail="Mes de referencia nao encontrado")
    return await service.create(data)


@router.put("/{custo_id}", response_model=CustoPublic, dependencies=[Depends(require("custo:update"))])
async def update_custo(custo_id: int, data: CustoUpdate, current_user: CurrentUser, service: CustoServiceDep):
    custo = await service.get_scoped(custo_id, current_user.tenant_id)
    if not custo:
        raise HTTPException(status_code=404, detail="Custo nao encontrado")
    return await service.update(custo, data)


@router.delete("/{custo_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require("custo:delete"))])
async def delete_custo(custo_id: int, current_user: CurrentUser, service: CustoServiceDep):
    custo = await service.get_scoped(custo_id, current_user.tenant_id)
    if not custo:
        raise HTTPException(status_code=404, detail="Custo nao encontrado")
    await service.delete(custo)
