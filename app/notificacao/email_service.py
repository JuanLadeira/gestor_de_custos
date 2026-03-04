import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.logger import logger
from app.settings import Settings

settings = Settings()


async def send_email_async(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
) -> bool:
    """Send an email asynchronously using aiosmtplib."""
    try:
        message = MIMEMultipart("alternative")
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = to_email
        message["Subject"] = subject

        # Add text part
        if body_text:
            part_text = MIMEText(body_text, "plain", "utf-8")
            message.attach(part_text)

        # Add HTML part
        part_html = MIMEText(body_html, "html", "utf-8")
        message.attach(part_html)

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            start_tls=False,
            use_tls=False,
        )

        logger.info(f"Email enviado com sucesso para {to_email}")
        return True

    except Exception as e:
        logger.error(f"Erro ao enviar email para {to_email}: {e}")
        return False


def send_email_sync(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
) -> bool:
    """Synchronous wrapper for send_email_async, for use in Celery tasks."""
    return asyncio.run(send_email_async(to_email, subject, body_html, body_text))
