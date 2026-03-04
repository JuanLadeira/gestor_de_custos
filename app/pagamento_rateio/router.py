from fastapi import APIRouter, HTTPException, status

from app.pagamento_rateio.schemas import (
    PagamentoRateioCreate,
    PagamentoRateioPublic,
    PagamentoRateioUpdate,
)
from app.pagamento_rateio.services import PagamentoRateioServiceDep

router = APIRouter(
    prefix="/api/rateios",
    tags=["Pagamentos Rateio"],
    responses={404: {"description": "Nao encontrado"}},
)


@router.get("/", response_model=list[PagamentoRateioPublic])
async def list_pagamentos_rateio(
    service: PagamentoRateioServiceDep,
    custo_id: int | None = None,
    usuario_id: int | None = None,
):
    return await service.get_all(custo_id=custo_id, usuario_id=usuario_id)


@router.get("/{pagamento_id}", response_model=PagamentoRateioPublic)
async def get_pagamento_rateio(pagamento_id: int, service: PagamentoRateioServiceDep):
    pagamento = await service.get_by_id(pagamento_id)
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento rateio nao encontrado")
    return pagamento


@router.post(
    "/", response_model=PagamentoRateioPublic, status_code=status.HTTP_201_CREATED
)
async def create_pagamento_rateio(
    data: PagamentoRateioCreate, service: PagamentoRateioServiceDep
):
    """Create a new cost sharing entry.

    The sum of all percentages for a cost cannot exceed 100%.
    The calculated value is automatically computed based on the cost total and percentage.
    """
    return await service.create(data)


@router.put("/{pagamento_id}", response_model=PagamentoRateioPublic)
async def update_pagamento_rateio(
    pagamento_id: int, data: PagamentoRateioUpdate, service: PagamentoRateioServiceDep
):
    """Update a cost sharing entry.

    If percentage is updated, the sum validation is performed again and
    the calculated value is recalculated.
    """
    pagamento = await service.update(pagamento_id, data)
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento rateio nao encontrado")
    return pagamento


@router.delete("/{pagamento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pagamento_rateio(
    pagamento_id: int, service: PagamentoRateioServiceDep
):
    deleted = await service.delete(pagamento_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Pagamento rateio nao encontrado")
