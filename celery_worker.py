import os
from flask import Flask
from app.config import Config
from app.extensions import celery, init_celery, mail, db, csrf, login_manager
from celery.schedules import crontab
from datetime import datetime, timedelta

# Create Flask app
app = Flask(__name__,
           template_folder="templates",
           static_folder="static",
           root_path=os.path.join(os.path.dirname(__file__), "app"))
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
mail.init_app(app)
csrf.init_app(app)
login_manager.init_app(app)

# Initialize Celery
init_celery(app)

# Initialize Celery
celery.conf.broker_url = app.config['CELERY_BROKER_URL']
celery.conf.result_backend = app.config['CELERY_RESULT_BACKEND']
celery.conf.imports = [
    'app.celery.tasks.booking_tasks',
    'app.celery.tasks.email_tasks'
]

# Configure Celery Beat schedule
celery.conf.beat_schedule = {
    'send-event-reminders': {
        'task': 'tasks.send_event_reminders',
        'schedule': crontab(hour='*/12')  # Run every 12 hours
    },
    'cleanup-abandoned-bookings': {
        'task': 'tasks.cleanup_abandoned_bookings',
        'schedule': crontab(minute='*/15')  # Run every 15 minutes
    },
    'send-low-ticket-alerts': {
        'task': 'tasks.send_low_ticket_alerts',
        'schedule': crontab(hour='*/6')  # Run every 6 hours
    },
    'cancel-expired-bookings': {
        'task': 'tasks.cancel_expired_bookings',
        'schedule': crontab(minute='*/30')  # Run every 30 minutes
    },
    'generate-daily-report': {
        'task': 'tasks.generate_booking_report',
        'schedule': crontab(hour=0, minute=0),  # Run at midnight
        'args': (
            # Pass yesterday's date range
            (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d'),
            datetime.utcnow().strftime('%Y-%m-%d')
        )
    }
}

TaskBase = celery.Task
class ContextTask(TaskBase):
    abstract = True
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return TaskBase.__call__(self, *args, **kwargs)

celery.Task = ContextTask
