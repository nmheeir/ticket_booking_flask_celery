from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize database with the Flask app"""
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import models here to ensure they are registered with SQLAlchemy
    from app.models.user import User
    from app.models.event import Event
    from app.models.ticket import Ticket
    from app.models.booking import Booking

def create_tables(app):
    """Create all database tables"""
    with app.app_context():
        db.create_all()

def drop_tables(app):
    """Drop all database tables"""
    with app.app_context():
        db.drop_all()

def commit_changes():
    """Commit changes to database"""
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e 