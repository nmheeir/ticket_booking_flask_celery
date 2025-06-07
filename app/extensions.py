from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from celery import Celery

# Initialize extensions
mail = Mail()
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
celery = Celery('app')

def init_celery(app=None):
    """Initialize Celery with Flask app context"""
    if not app:
        return

    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        imports=[
            'app.celery.tasks.booking_tasks',
            'app.celery.tasks.notification_tasks'
        ]
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery 