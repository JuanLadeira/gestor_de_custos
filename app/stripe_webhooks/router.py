import stripe
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from app.database import AsyncDBSession
from app.logger import logger
from app.plano.services import PlanoServiceDep
from app.settings import Settings
from app.stripe_webhooks import handlers

settings = Settings()
stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter(tags=["Stripe"])


class CheckoutSessionRequest(BaseModel):
    plano_id: int
    periodo: str  # "mensal" | "anual"
    tenant_nome: str
    email: str
    username: str
    nome: str


@router.post("/checkout/session")
async def create_checkout_session(
    data: CheckoutSessionRequest,
    plano_service: PlanoServiceDep,
):
    """Cria uma Stripe Checkout Session para o plano escolhido."""
    plano = await plano_service.get_by_id(data.plano_id)
    if not plano or not plano.ativo:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    price_id = (
        plano.stripe_price_id_mensal
        if data.periodo == "mensal"
        else plano.stripe_price_id_anual
    )
    if not price_id:
        raise HTTPException(
            status_code=400, detail=f"Stripe price ID não configurado para período '{data.periodo}'"
        )

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{settings.FRONTEND_URL}/assinatura/sucesso",
            cancel_url=f"{settings.FRONTEND_URL}/",
            metadata={
                "plano_id": str(data.plano_id),
                "tenant_nome": data.tenant_nome,
                "email": data.email,
                "username": data.username,
                "nome": data.nome,
                "periodo": data.periodo,
            },
        )
    except stripe.StripeError as e:
        logger.error("Stripe error: %s", e)
        raise HTTPException(status_code=502, detail="Erro ao criar sessão de pagamento")

    return {"checkout_url": session.url}


@router.post("/stripe/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(request: Request, session: AsyncDBSession):
    """Recebe eventos do Stripe e processa webhooks."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    except Exception as e:
        logger.error("Stripe webhook error: %s", e)
        raise HTTPException(status_code=400, detail="Webhook error")

    event_type = event["type"]
    event_data = event["data"]

    async with session.begin():
        if event_type == "checkout.session.completed":
            await handlers.handle_checkout_completed(event_data, session)
        elif event_type == "customer.subscription.updated":
            await handlers.handle_subscription_updated(event_data, session)
        elif event_type == "customer.subscription.deleted":
            await handlers.handle_subscription_deleted(event_data, session)
        elif event_type == "invoice.payment_failed":
            await handlers.handle_payment_failed(event_data, session)
        else:
            logger.debug("Unhandled Stripe event: %s", event_type)

    return {"received": True}
