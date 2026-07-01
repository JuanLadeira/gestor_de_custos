import secrets
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.assinatura.models import AssinaturaStatus
from app.assinatura.services import AssinaturaService
from app.logger import logger
from app.notificacao.email_service import send_email_async
from app.plano.services import PlanoService
from app.tenant.schemas import TenantCreate
from app.tenant.services import TenantService
from app.usuario.schemas import UsuarioCreate
from app.usuario.services import UsuarioService


async def handle_checkout_completed(event_data: dict, session: AsyncSession) -> None:
    """
    Creates Tenant + OWNER Usuario + Assinatura when Stripe checkout completes.
    """
    checkout_session = event_data["object"]
    metadata = checkout_session.get("metadata", {})

    plano_id = metadata.get("plano_id")
    tenant_nome = metadata.get("tenant_nome")
    email = metadata.get("email")
    username = metadata.get("username")
    nome = metadata.get("nome")
    metadata.get("periodo", "mensal")

    if not all([plano_id, tenant_nome, email, username, nome]):
        logger.error("checkout.session.completed: metadata incompleto %s", metadata)
        return

    plano_id = int(plano_id)
    stripe_subscription_id = checkout_session.get("subscription")
    stripe_customer_id = checkout_session.get("customer")

    tenant_service = TenantService(session)
    usuario_service = UsuarioService(session)
    plano_service = PlanoService(session)
    assinatura_service = AssinaturaService(session)

    # Check if plano exists
    plano = await plano_service.get_by_id(plano_id)
    if not plano:
        logger.error("Plano %s não encontrado", plano_id)
        return

    # Create Tenant (also seeds authz defaults)
    tenant = await tenant_service.create(TenantCreate(nome=tenant_nome))
    logger.info("Tenant criado: %s (id=%s)", tenant.nome, tenant.id)

    from app.authz.service import AuthzService

    authz_service = AuthzService(session)
    dono = await authz_service.get_profile_by_nome(tenant.id, "Dono")

    senha_temporaria = secrets.token_urlsafe(16)

    # Create user with Dono profile
    usuario = await usuario_service.create(
        UsuarioCreate(
            username=username,
            email=email,
            nome=nome,
            password=senha_temporaria,
        ),
        tenant_id=tenant.id,
        role_profile_id=dono.id,
    )
    logger.info("Usuario Dono criado: %s (id=%s)", usuario.username, usuario.id)

    # Create Assinatura
    await assinatura_service.create(
        tenant_id=tenant.id,
        plano_id=plano_id,
        stripe_subscription_id=stripe_subscription_id,
        stripe_customer_id=stripe_customer_id,
        data_inicio=datetime.now(tz=timezone.utc),
        status=AssinaturaStatus.ATIVA,
    )
    logger.info("Assinatura criada para tenant %s", tenant.id)

    # Send welcome email with credentials
    await send_email_async(
        to_email=email,
        subject="Bem-vindo ao Gestor de Custos — suas credenciais",
        body_html=f"""
        <h2>Bem-vindo, {nome}!</h2>
        <p>Sua conta foi criada com sucesso no plano <strong>{plano.nome}</strong>.</p>
        <p><strong>Usuário:</strong> {username}</p>
        <p><strong>Senha temporária:</strong> {senha_temporaria}</p>
        <p>Acesse o sistema e altere sua senha assim que possível.</p>
        """,
        body_text=(
            f"Bem-vindo, {nome}!\n\n"
            f"Usuário: {username}\n"
            f"Senha temporária: {senha_temporaria}\n\n"
            "Acesse o sistema e altere sua senha assim que possível."
        ),
    )


async def handle_subscription_updated(event_data: dict, session: AsyncSession) -> None:
    subscription = event_data["object"]
    stripe_subscription_id = subscription["id"]
    stripe_status = subscription.get("status")
    current_period_end = subscription.get("current_period_end")

    assinatura_service = AssinaturaService(session)
    assinatura = await assinatura_service.get_by_stripe_subscription_id(stripe_subscription_id)
    if not assinatura:
        logger.warning("Assinatura não encontrada: %s", stripe_subscription_id)
        return

    # Map stripe status to internal status
    status_map = {
        "active": AssinaturaStatus.ATIVA,
        "past_due": AssinaturaStatus.SUSPENSA,
        "canceled": AssinaturaStatus.CANCELADA,
        "unpaid": AssinaturaStatus.SUSPENSA,
    }
    new_status = status_map.get(stripe_status, AssinaturaStatus.SUSPENSA)

    update_data: dict = {"status": new_status}
    if current_period_end:
        update_data["data_proxima_cobranca"] = datetime.fromtimestamp(
            current_period_end, tz=timezone.utc
        )

    from app.assinatura.schemas import AssinaturaUpdate as AU

    await assinatura_service.update(assinatura.id, AU(**update_data))
    logger.info("Assinatura %s atualizada: status=%s", stripe_subscription_id, new_status)


async def handle_subscription_deleted(event_data: dict, session: AsyncSession) -> None:
    subscription = event_data["object"]
    stripe_subscription_id = subscription["id"]

    assinatura_service = AssinaturaService(session)
    assinatura = await assinatura_service.get_by_stripe_subscription_id(stripe_subscription_id)
    if not assinatura:
        logger.warning("Assinatura não encontrada para cancelamento: %s", stripe_subscription_id)
        return

    from app.assinatura.schemas import AssinaturaUpdate

    await assinatura_service.update(
        assinatura.id, AssinaturaUpdate(status=AssinaturaStatus.CANCELADA)
    )
    logger.info("Assinatura %s cancelada", stripe_subscription_id)


async def handle_payment_failed(event_data: dict, session: AsyncSession) -> None:
    invoice = event_data["object"]
    stripe_subscription_id = invoice.get("subscription")
    if not stripe_subscription_id:
        return

    assinatura_service = AssinaturaService(session)
    assinatura = await assinatura_service.get_by_stripe_subscription_id(stripe_subscription_id)
    if not assinatura:
        logger.warning("Assinatura não encontrada para falha de pagamento: %s", stripe_subscription_id)
        return

    from app.assinatura.schemas import AssinaturaUpdate

    await assinatura_service.update(
        assinatura.id, AssinaturaUpdate(status=AssinaturaStatus.SUSPENSA)
    )
    logger.info("Assinatura %s suspensa por falha de pagamento", stripe_subscription_id)
