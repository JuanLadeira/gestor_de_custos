import asyncio
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.custo.models import Custo, StatusPagamento
from app.database.session import async_session_factory
from app.logger import logger
from app.notificacao.email_service import send_email_sync
from app.pagamento_rateio.models import PagamentoRateio, StatusRateio
from app.settings import Settings
from app.usuario.models import Usuario

settings = Settings()


def format_currency(value: Decimal) -> str:
    """Format decimal value as Brazilian Real currency."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@celery_app.task(name="app.notificacao.tasks.disparar_email_lembrete")
def disparar_email_lembrete(
    email: str,
    nome: str,
    valor: str,
    descricao: str,
    vencimento: str,
) -> bool:
    """Send a reminder email about a pending payment."""
    subject = f"Lembrete: Pagamento pendente - {descricao}"

    body_html = f"""
    <html>
    <body>
        <h2>Olá, {nome}!</h2>
        <p>Este é um lembrete sobre um pagamento pendente:</p>
        <table style="border-collapse: collapse; margin: 20px 0;">
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Descrição:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{descricao}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Valor:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{valor}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Vencimento:</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{vencimento}</td>
            </tr>
        </table>
        <p>Por favor, regularize seu pagamento.</p>
        <p>Atenciosamente,<br>Gestor de Custos</p>
    </body>
    </html>
    """

    body_text = f"""
    Olá, {nome}!

    Este é um lembrete sobre um pagamento pendente:

    Descrição: {descricao}
    Valor: {valor}
    Vencimento: {vencimento}

    Por favor, regularize seu pagamento.

    Atenciosamente,
    Gestor de Custos
    """

    return send_email_sync(email, subject, body_html, body_text)


async def _buscar_vencimentos_proximos(session: AsyncSession) -> list[dict]:
    """Find costs due soon with pending payments."""
    hoje = date.today()
    data_limite = hoje + timedelta(days=settings.DAYS_BEFORE_DUE_NOTIFICATION)

    # Query for pending payments where cost is due soon and not yet paid
    query = (
        select(PagamentoRateio, Custo, Usuario)
        .join(Custo, PagamentoRateio.custo_id == Custo.id)
        .join(Usuario, PagamentoRateio.usuario_id == Usuario.id)
        .where(PagamentoRateio.status == StatusRateio.PENDENTE)
        .where(Custo.status == StatusPagamento.PENDENTE)
        .where(Custo.data_vencimento <= data_limite)
        .where(Custo.data_vencimento >= hoje)
    )

    result = await session.execute(query)
    rows = result.all()

    notificacoes = []
    for pagamento, custo, usuario in rows:
        notificacoes.append(
            {
                "email": usuario.email,
                "nome": usuario.nome,
                "valor": format_currency(pagamento.valor_calculado),
                "descricao": custo.descricao,
                "vencimento": custo.data_vencimento.strftime("%d/%m/%Y"),
            }
        )

    return notificacoes


@celery_app.task(name="app.notificacao.tasks.checar_vencimentos_e_notificar")
def checar_vencimentos_e_notificar() -> dict:
    """Daily task: check for upcoming due dates and send reminder emails."""

    async def _run():
        async with async_session_factory() as session:
            notificacoes = await _buscar_vencimentos_proximos(session)

        enviados = 0
        erros = 0

        for notif in notificacoes:
            try:
                disparar_email_lembrete.delay(
                    email=notif["email"],
                    nome=notif["nome"],
                    valor=notif["valor"],
                    descricao=notif["descricao"],
                    vencimento=notif["vencimento"],
                )
                enviados += 1
            except Exception as e:
                logger.error(f"Erro ao enfileirar notificacao: {e}")
                erros += 1

        return {"notificacoes_encontradas": len(notificacoes), "enviados": enviados, "erros": erros}

    return asyncio.run(_run())
