from fastapi import APIRouter, HTTPException, status

from app.custo_fixo.schemas import CustoFixoCreate, CustoFixoPublic, CustoFixoUpdate
from app.custo_fixo.services import CustoFixoServiceDep

router = APIRouter(
    prefix="/api/custos-fixos",
    tags=["Custos Fixos"],
    responses={404: {"description": "Nao encontrado"}},
)


@router.get("/", response_model=list[CustoFixoPublic])
async def list_custos_fixos(
    service: CustoFixoServiceDep,
    tenant_id: int | None = None,
):
    return await service.get_all(tenant_id=tenant_id)


@router.get("/{custo_fixo_id}", response_model=CustoFixoPublic)
async def get_custo_fixo(custo_fixo_id: int, service: CustoFixoServiceDep):
    custo_fixo = await service.get_by_id(custo_fixo_id)
    if not custo_fixo:
        raise HTTPException(status_code=404, detail="Custo fixo nao encontrado")
    return custo_fixo


@router.post("/", response_model=CustoFixoPublic, status_code=status.HTTP_201_CREATED)
async def create_custo_fixo(data: CustoFixoCreate, service: CustoFixoServiceDep):
    return await service.create(data)


@router.put("/{custo_fixo_id}", response_model=CustoFixoPublic)
async def update_custo_fixo(
    custo_fixo_id: int, data: CustoFixoUpdate, service: CustoFixoServiceDep
):
    custo_fixo = await service.update(custo_fixo_id, data)
    if not custo_fixo:
        raise HTTPException(status_code=404, detail="Custo fixo nao encontrado")
    return custo_fixo


@router.delete("/{custo_fixo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custo_fixo(custo_fixo_id: int, service: CustoFixoServiceDep):
    deleted = await service.delete(custo_fixo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Custo fixo nao encontrado")
