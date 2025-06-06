from celery import Celery
from app.config import Config

def create_celery_app():
    """Create and configure Celery application"""
    celery = Celery(
        'ticket_booking',
        broker=Config.CELERY_BROKER_URL,
        backend=Config.CELERY_RESULT_BACKEND,
        include=[
            'app.tasks.booking_tasks',
            'app.tasks.notification_tasks'
        ]
    )

    # Optional configurations
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        task_soft_time_limit=25 * 60,  # 25 minutes
        worker_max_tasks_per_child=200,
        worker_prefetch_multiplier=4
    )

    return celery

celery = create_celery_app() 