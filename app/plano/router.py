from fastapi import APIRouter

from app.plano.schemas import PlanoPublic
from app.plano.services import PlanoServiceDep

router = APIRouter(
    prefix="/api/planos",
    tags=["Planos"],
)


@router.get("/", response_model=list[PlanoPublic])
async def list_planos(service: PlanoServiceDep):
    """Lista planos ativos (público, para landing page)."""
    return await service.get_all(apenas_ativos=True)
