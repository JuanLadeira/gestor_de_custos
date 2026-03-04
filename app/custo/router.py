from fastapi import APIRouter, HTTPException, status

from app.custo.schemas import CustoCreate, CustoPublic, CustoUpdate
from app.custo.services import CustoServiceDep

router = APIRouter(
    prefix="/api/custos",
    tags=["Custos"],
    responses={404: {"description": "Nao encontrado"}},
)


@router.get("/", response_model=list[CustoPublic])
async def list_custos(
    service: CustoServiceDep,
    mes_referencia_id: int | None = None,
):
    return await service.get_all(mes_referencia_id=mes_referencia_id)


@router.get("/{custo_id}", response_model=CustoPublic)
async def get_custo(custo_id: int, service: CustoServiceDep):
    custo = await service.get_by_id(custo_id)
    if not custo:
        raise HTTPException(status_code=404, detail="Custo nao encontrado")
    return custo


@router.post("/", response_model=CustoPublic, status_code=status.HTTP_201_CREATED)
async def create_custo(data: CustoCreate, service: CustoServiceDep):
    return await service.create(data)


@router.put("/{custo_id}", response_model=CustoPublic)
async def update_custo(custo_id: int, data: CustoUpdate, service: CustoServiceDep):
    custo = await service.update(custo_id, data)
    if not custo:
        raise HTTPException(status_code=404, detail="Custo nao encontrado")
    return custo


@router.delete("/{custo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custo(custo_id: int, service: CustoServiceDep):
    deleted = await service.delete(custo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Custo nao encontrado")
