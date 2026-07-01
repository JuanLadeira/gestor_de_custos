from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.auth.current_user import CurrentUser
from app.authz.dependencies import CurrentPermissions, require
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


@router.get("/", response_model=list[PagamentoRateioPublic], dependencies=[Depends(require("rateio:read"))])
async def list_pagamentos_rateio(
    current_user: CurrentUser,
    service: PagamentoRateioServiceDep,
    custo_id: int,
):
    if not await service.custo_in_tenant(custo_id, current_user.tenant_id):
        raise HTTPException(status_code=404, detail="Custo nao encontrado")
    return await service.get_all(custo_id=custo_id)


@router.get("/{pagamento_id}", response_model=PagamentoRateioPublic, dependencies=[Depends(require("rateio:read"))])
async def get_pagamento_rateio(pagamento_id: int, current_user: CurrentUser, service: PagamentoRateioServiceDep):
    pagamento = await service.get_scoped(pagamento_id, current_user.tenant_id)
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento rateio nao encontrado")
    return pagamento


@router.post("/", response_model=PagamentoRateioPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require("rateio:create"))])
async def create_pagamento_rateio(
    data: PagamentoRateioCreate, current_user: CurrentUser, service: PagamentoRateioServiceDep
):
    if not await service.custo_in_tenant(data.custo_id, current_user.tenant_id):
        raise HTTPException(status_code=404, detail="Custo nao encontrado")
    if not await service.usuario_in_tenant(data.usuario_id, current_user.tenant_id):
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    return await service.create(data)


@router.put("/{pagamento_id}", response_model=PagamentoRateioPublic)
async def update_pagamento_rateio(
    pagamento_id: int,
    data: PagamentoRateioUpdate,
    current_user: CurrentUser,
    service: PagamentoRateioServiceDep,
    permissions: CurrentPermissions,
):
    pagamento = await service.get_scoped(pagamento_id, current_user.tenant_id)
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento rateio nao encontrado")
    needed = "rateio:pay" if data.status is not None else "rateio:update"
    if needed not in permissions:
        raise HTTPException(status_code=403, detail=f"Permissão necessária: {needed}")
    pagamento = await service.update(pagamento_id, data)
    if data.status is not None:
        await service.recalcular_status_custo(pagamento.custo_id)
    return pagamento


@router.post("/{pagamento_id}/comprovante", response_model=PagamentoRateioPublic,
             dependencies=[Depends(require("comprovante:upload"))])
async def upload_comprovante(
    pagamento_id: int, file: UploadFile, current_user: CurrentUser, service: PagamentoRateioServiceDep
):
    pagamento = await service.get_scoped(pagamento_id, current_user.tenant_id)
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento rateio nao encontrado")
    return await service.salvar_comprovante(pagamento_id, file)


@router.delete("/{pagamento_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require("rateio:delete"))])
async def delete_pagamento_rateio(pagamento_id: int, current_user: CurrentUser, service: PagamentoRateioServiceDep):
    pagamento = await service.get_scoped(pagamento_id, current_user.tenant_id)
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento rateio nao encontrado")
    await service.delete(pagamento_id)
