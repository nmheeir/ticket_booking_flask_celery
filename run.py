import os
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf import CSRFProtect
from app.config import config
from app.utils.database import init_db
from app.utils.filters import register_filters
from app.models.user import User
from app.utils.init_roles import init_roles
from app.utils.database import db


def create_app(config_name=None):
    """Create Flask application"""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    init_db(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    mail = Mail()
    mail.init_app(app)

    csrf = CSRFProtect()
    csrf.init_app(app)

    # Register filters
    register_filters(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

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

    # Initialize roles
    with app.app_context():
        init_roles()

    return app


app = create_app()


@app.cli.command()
def forge():
    """Generate fake data for testing"""
    from app.models.user import User
    from app.models.event import Event
    from app.models.booking import Booking
    from app.models.ticket import Ticket

    # Generate fake users
    users = User.generate_fake_data(count=10)
    db.session.add_all(users)
    db.session.commit()

    # Generate fake events
    events = Event.generate_fake_data(count=10)
    db.session.add_all(events)
    db.session.commit()

    # Generate fake bookings
    bookings = Booking.generate_fake_data(count=10)
    db.session.add_all(bookings)
    db.session.commit()

    # Generate fake tickets
    tickets = Ticket.generate_fake_data(count=10)
    db.session.add_all(tickets)
    db.session.commit()

    print("Fake data generated successfully")
