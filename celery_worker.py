from app.tasks.celery_app import create_celery_app
from run import create_app

app = create_app()
app.app_context().push()

celery = create_celery_app() 