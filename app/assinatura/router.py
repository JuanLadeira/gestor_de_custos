from fastapi import APIRouter, HTTPException

from app.assinatura.schemas import AssinaturaPublic
from app.assinatura.services import AssinaturaServiceDep
from app.auth.current_user import CurrentUser

router = APIRouter(
    prefix="/api/assinaturas",
    tags=["Assinaturas"],
)


@router.get("/minha", response_model=AssinaturaPublic)
async def get_minha_assinatura(
    current_user: CurrentUser,
    service: AssinaturaServiceDep,
):
    """Retorna a assinatura do tenant do usuário logado."""
    assinatura = await service.get_by_tenant(current_user.tenant_id)
    if not assinatura:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")
    return assinatura
