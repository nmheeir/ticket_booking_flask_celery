import os
from flask import Flask
from app.config import config
from app.utils.database import init_db
from app.utils.filters import register_filters
from app.models.user import User
from app.utils.init_roles import init_roles
from app.extensions import mail, csrf, login_manager, init_celery

def create_app(config_name=None):
    """Create Flask application"""
    app = Flask(__name__)

    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
    app.config.from_object(config[config_name])

    # Initialize extensions
    init_db(app)
    mail.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    init_celery(app)
    
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register filters
    register_filters(app)

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.events import events_bp
    from app.routes.booking import booking_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(events_bp, url_prefix="/events")
    app.register_blueprint(booking_bp, url_prefix="/booking")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    return app

app = create_app()

@app.cli.command()
def initroles():
    """Khởi tạo dữ liệu cơ bản như các vai trò (roles)"""
    init_roles()
    print("Roles initialized.")

@app.cli.command()
def forge():
    """Generate fake data for testing"""
    from app.models.user import User
    from app.models.event import Event
    from app.models.booking import Booking
    from app.models.ticket import Ticket
    from app.extensions import db

    users = User.generate_fake_data(count=10)
    db.session.add_all(users)
    db.session.commit()

    events = Event.generate_fake_data(count=10)
    db.session.add_all(events)
    db.session.commit()

    bookings = Booking.generate_fake_data(count=10)
    db.session.add_all(bookings)
    db.session.commit()

    tickets = Ticket.generate_fake_data(count=10)
    db.session.add_all(tickets)
    db.session.commit()

    print("Fake data generated successfully")
