import os
from flask import Flask
from app.config import Config
from app.extensions import celery, init_celery

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Celery
init_celery(app)

# Initialize Celery
celery.conf.broker_url = app.config['CELERY_BROKER_URL']
celery.conf.result_backend = app.config['CELERY_RESULT_BACKEND']
celery.conf.imports = [
    'app.celery.tasks.booking_tasks',
    'app.celery.tasks.notification_tasks'
]

TaskBase = celery.Task
class ContextTask(TaskBase):
    abstract = True
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return TaskBase.__call__(self, *args, **kwargs)

celery.Task = ContextTask
