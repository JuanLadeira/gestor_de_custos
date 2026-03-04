from celery import Celery
from celery.schedules import crontab

from app.settings import Settings

settings = Settings()

celery_app = Celery(
    "gestor_custos",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.notificacao.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "checar-vencimentos-diariamente": {
        "task": "app.notificacao.tasks.checar_vencimentos_e_notificar",
        "schedule": crontab(hour=9, minute=0),  # Every day at 9 AM
    },
}
