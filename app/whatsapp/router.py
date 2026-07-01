from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.auth.current_user import CurrentUser
from app.authz.dependencies import require
from app.database.session import async_session_factory
from app.whatsapp.models import WhatsappInstancia
from app.whatsapp.schemas import (
    InstanciaCreate,
    InstanciaPublic,
    MensagemMidiaRequest,
    MensagemTextoRequest,
    WebhookEvento,
)
from app.whatsapp.services import WhatsappServiceDep

router = APIRouter(
    prefix="/api/whatsapp",
    tags=["WhatsApp"],
)


async def _get_instancia_or_404(instancia_id: int, current_user: CurrentUser, service: WhatsappServiceDep):
    instancia = await service.obter_instancia(instancia_id, current_user.tenant_id)
    if not instancia:
        raise HTTPException(status_code=404, detail="Instância não encontrada")
    return instancia


@router.get("/instancias", response_model=list[InstanciaPublic],
            dependencies=[Depends(require("whatsapp:read"))])
async def listar_instancias(current_user: CurrentUser, service: WhatsappServiceDep):
    return await service.listar_instancias(current_user.tenant_id)


@router.post("/instancias", response_model=InstanciaPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require("whatsapp:manage"))])
async def criar_instancia(
    data: InstanciaCreate,
    current_user: CurrentUser,
    service: WhatsappServiceDep,
):
    return await service.criar_instancia(current_user.tenant_id, data)


@router.get("/instancias/{instancia_id}/qrcode",
            dependencies=[Depends(require("whatsapp:manage"))])
async def obter_qrcode(
    instancia_id: int,
    current_user: CurrentUser,
    service: WhatsappServiceDep,
):
    instancia = await _get_instancia_or_404(instancia_id, current_user, service)
    return await service.obter_qrcode(instancia)


@router.get("/instancias/{instancia_id}/status", response_model=InstanciaPublic,
            dependencies=[Depends(require("whatsapp:read"))])
async def sincronizar_status(
    instancia_id: int,
    current_user: CurrentUser,
    service: WhatsappServiceDep,
):
    instancia = await _get_instancia_or_404(instancia_id, current_user, service)
    return await service.sincronizar_status(instancia)


@router.delete("/instancias/{instancia_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require("whatsapp:manage"))])
async def deletar_instancia(
    instancia_id: int,
    current_user: CurrentUser,
    service: WhatsappServiceDep,
):
    instancia = await _get_instancia_or_404(instancia_id, current_user, service)
    await service.deletar_instancia(instancia)


@router.post("/instancias/{instancia_id}/mensagens/texto",
             dependencies=[Depends(require("whatsapp:send"))])
async def enviar_texto(
    instancia_id: int,
    data: MensagemTextoRequest,
    current_user: CurrentUser,
    service: WhatsappServiceDep,
):
    instancia = await _get_instancia_or_404(instancia_id, current_user, service)
    return await service.enviar_texto(instancia, data)


@router.post("/instancias/{instancia_id}/mensagens/midia",
             dependencies=[Depends(require("whatsapp:send"))])
async def enviar_midia(
    instancia_id: int,
    data: MensagemMidiaRequest,
    current_user: CurrentUser,
    service: WhatsappServiceDep,
):
    instancia = await _get_instancia_or_404(instancia_id, current_user, service)
    return await service.enviar_midia(instancia, data)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def receber_webhook(evento: WebhookEvento):
    if evento.event == "MESSAGES_UPSERT":
        await _processar_mensagem_recebida(evento)
    return {"received": True, "event": evento.event, "instance": evento.instance}


async def _processar_mensagem_recebida(evento: WebhookEvento) -> None:
    """Process incoming WhatsApp messages and save to inbox."""
    try:
        data = evento.data
        # Skip messages sent by us
        key = data.get("key", {})
        if key.get("fromMe"):
            return

        conteudo = (
            data.get("message", {}).get("conversation")
            or data.get("message", {}).get("extendedTextMessage", {}).get("text")
            or ""
        )
        if not conteudo:
            return

        numero = key.get("remoteJid", "").replace("@s.whatsapp.net", "")
        evolution_id = key.get("id")

        async with async_session_factory() as session:
            # Find instance by name
            result = await session.execute(
                select(WhatsappInstancia).where(
                    WhatsappInstancia.instance_name == evento.instance
                )
            )
            instancia = result.scalar_one_or_none()
            if not instancia:
                return

            from app.campanha.services import InboxService
            import httpx
            async with httpx.AsyncClient() as client:
                inbox = InboxService(session, client)
                await inbox.upsert_from_webhook(
                    tenant_id=instancia.tenant_id,
                    instancia_id=instancia.id,
                    numero=numero,
                    conteudo=conteudo,
                    evolution_id=evolution_id,
                )
            await session.commit()
    except Exception:
        pass  # Webhook must always return 200
