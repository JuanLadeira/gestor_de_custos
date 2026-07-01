from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.current_user import CurrentUser
from app.authz.dependencies import require
from app.mes_referencia.schemas import (
    MesReferenciaCreate,
    MesReferenciaPublic,
    MesReferenciaUpdate,
)
from app.mes_referencia.services import MesReferenciaServiceDep

router = APIRouter(
    prefix="/api/meses",
    tags=["Meses de Referencia"],
    responses={404: {"description": "Nao encontrado"}},
)


@router.get("/", response_model=list[MesReferenciaPublic], dependencies=[Depends(require("mes:read"))])
async def list_meses_referencia(current_user: CurrentUser, service: MesReferenciaServiceDep):
    return await service.get_all(tenant_id=current_user.tenant_id)


@router.get("/atual", response_model=MesReferenciaPublic, dependencies=[Depends(require("mes:read"))])
async def get_ou_criar_mes_atual(current_user: CurrentUser, service: MesReferenciaServiceDep):
    return await service.obter_ou_criar_mes_atual(current_user.tenant_id)


@router.get("/{mes_referencia_id}", response_model=MesReferenciaPublic, dependencies=[Depends(require("mes:read"))])
async def get_mes_referencia(mes_referencia_id: int, current_user: CurrentUser, service: MesReferenciaServiceDep):
    mes_ref = await service.get_by_id_scoped(mes_referencia_id, current_user.tenant_id)
    if not mes_ref:
        raise HTTPException(status_code=404, detail="Mes de referencia nao encontrado")
    return mes_ref


@router.post("/", response_model=MesReferenciaPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require("mes:create"))])
async def create_mes_referencia(
    data: MesReferenciaCreate, current_user: CurrentUser, service: MesReferenciaServiceDep
):
    existing = await service.get_by_tenant_ano_mes(current_user.tenant_id, data.ano, data.mes)
    if existing:
        raise HTTPException(status_code=400, detail="Mes de referencia ja existe para este tenant")
    return await service.create(data, tenant_id=current_user.tenant_id)


@router.put("/{mes_referencia_id}", response_model=MesReferenciaPublic,
            dependencies=[Depends(require("mes:update"))])
async def update_mes_referencia(
    mes_referencia_id: int, data: MesReferenciaUpdate, current_user: CurrentUser, service: MesReferenciaServiceDep
):
    mes_ref = await service.get_by_id_scoped(mes_referencia_id, current_user.tenant_id)
    if not mes_ref:
        raise HTTPException(status_code=404, detail="Mes de referencia nao encontrado")
    return await service.update(mes_referencia_id, data)


@router.post("/{mes_referencia_id}/importar-custos-fixos", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require("mes:import_fixos"))])
async def importar_custos_fixos(
    mes_referencia_id: int, current_user: CurrentUser, service: MesReferenciaServiceDep
):
    mes_ref = await service.get_by_id_scoped(mes_referencia_id, current_user.tenant_id)
    if not mes_ref:
        raise HTTPException(status_code=404, detail="Mes de referencia nao encontrado")
    custos = await service.importar_custos_fixos_para_mes(mes_referencia_id, current_user.tenant_id)
    return {"message": f"{len(custos)} custos fixos importados"}
