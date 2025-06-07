from app.extensions import db
from flask_migrate import Migrate

migrate = Migrate()

def init_db(app):
    """Initialize database"""
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
        return True
    except Exception as e:
        db.session.rollback()
        return False 