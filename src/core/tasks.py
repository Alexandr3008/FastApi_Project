from __future__ import annotations

import smtplib
from email.mime.text import MIMEText

from celery import Celery

from src.config import Settings
from src.core.logging_config import logger

settings = Settings()
celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL
)

@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def send_registration_email(self, to_email: str):
    """
    Send a welcome email to a newly registered user.

    Args:
        to_email: Recipient email address

    Raises:
        smtplib.SMTPException: If email sending fails
    """
    try:
        html = """
        Добро пожаловать!
        Вы успешно зарегистрировались на нашем маркетплейс-блоге.
        """
        message = MIMEText(html, "html")
        message["From"] = settings.SMTP_USER
        message["To"] = to_email
        message["Subject"] = "Регистрация прошла успешно"

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
    except smtplib.SMTPException as e:
        logger.error(f"Failed to send email to {to_email}: {e!s}")
        raise self.retry(exc=e)
