from fastapi import APIRouter, HTTPException, status

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


@router.get("/", response_model=list[MesReferenciaPublic])
async def list_meses_referencia(
    service: MesReferenciaServiceDep,
    tenant_id: int | None = None,
):
    return await service.get_all(tenant_id=tenant_id)


@router.get("/tenant/{tenant_id}/atual", response_model=MesReferenciaPublic)
async def get_ou_criar_mes_atual(tenant_id: int, service: MesReferenciaServiceDep):
    """Get or create the current month reference for a tenant.

    If the month doesn't exist, it will be created and all active fixed costs
    will be automatically imported as costs for this month.
    """
    return await service.obter_ou_criar_mes_atual(tenant_id)


@router.get("/{mes_referencia_id}", response_model=MesReferenciaPublic)
async def get_mes_referencia(mes_referencia_id: int, service: MesReferenciaServiceDep):
    mes_ref = await service.get_by_id(mes_referencia_id)
    if not mes_ref:
        raise HTTPException(status_code=404, detail="Mes de referencia nao encontrado")
    return mes_ref


@router.post("/", response_model=MesReferenciaPublic, status_code=status.HTTP_201_CREATED)
async def create_mes_referencia(
    data: MesReferenciaCreate, service: MesReferenciaServiceDep
):
    # Check if already exists
    existing = await service.get_by_tenant_ano_mes(data.tenant_id, data.ano, data.mes)
    if existing:
        raise HTTPException(
            status_code=400, detail="Mes de referencia ja existe para este tenant"
        )
    return await service.create(data)


@router.put("/{mes_referencia_id}", response_model=MesReferenciaPublic)
async def update_mes_referencia(
    mes_referencia_id: int, data: MesReferenciaUpdate, service: MesReferenciaServiceDep
):
    mes_ref = await service.update(mes_referencia_id, data)
    if not mes_ref:
        raise HTTPException(status_code=404, detail="Mes de referencia nao encontrado")
    return mes_ref


@router.delete("/{mes_referencia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mes_referencia(
    mes_referencia_id: int, service: MesReferenciaServiceDep
):
    deleted = await service.delete(mes_referencia_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Mes de referencia nao encontrado")


@router.post(
    "/{mes_referencia_id}/importar-custos-fixos",
    status_code=status.HTTP_201_CREATED,
)
async def importar_custos_fixos(
    mes_referencia_id: int, service: MesReferenciaServiceDep
):
    """Manually trigger import of fixed costs for a specific month."""
    mes_ref = await service.get_by_id(mes_referencia_id)
    if not mes_ref:
        raise HTTPException(status_code=404, detail="Mes de referencia nao encontrado")

    custos = await service.importar_custos_fixos_para_mes(
        mes_referencia_id, mes_ref.tenant_id
    )
    return {"message": f"{len(custos)} custos fixos importados"}
