from datetime import datetime
from flask_login import AnonymousUserMixin, UserMixin
from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.database import db
from app.utils.permissions import Permission
from app.models.role import Role


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_confirmed = db.Column(db.Boolean, default=False)
    confirmed_at = db.Column(db.DateTime)

    # Relationships
    bookings = db.relationship("Booking", backref="user", lazy=True)

    def __init__(self, email, password, first_name, last_name, phone=None):
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        if self.role is None:
            if self.email == current_app.config["ADMIN_USERNAME"]:
                self.role = Role.query.filter_by(name="Administrator").first()
            if self.role is None:
                self.role = Role.query.filter_by(name="User").first()

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"

    def can(self, permission):
        """Check if user has the given permission"""
        return (
            self.role is not None
            and self.is_active
            and self.role.has_permission(permission)
        )

    def is_administrator(self):
        """Check if user is administrator"""
        return self.can(Permission.MANAGE_USERS)

    def generate_confirmation_token(self):
        """Generate confirmation token"""
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return s.dumps({"confirm": self.id}, salt='email-confirm-salt')

    def confirm_account(self, token, expiration=3600):
        """Confirm user account"""
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token, salt='email-confirm-salt', max_age=expiration)
        except:
            return False
        if data.get("confirm") != self.id:
            return False
        self.is_confirmed = True
        self.confirmed_at = datetime.utcnow()
        db.session.commit()
        return True

    @property
    def is_admin(self):
        """Compatibility property for existing code"""
        return self.is_administrator()

    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "is_active": self.is_active,
            "role": self.role.name if self.role else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_confirmed": self.is_confirmed,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
        }

    @staticmethod
    def generate_fake_data(count=10):
        """Generate fake data for testing"""
        from faker import Faker

        fake = Faker()
        users = []
        for _ in range(count):
            user = User(
                email=fake.email(),
                password=fake.password(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                phone=fake.phone_number(),
            )
            users.append(user)
        return users

    def __repr__(self):
        return f"<User {self.email}>"
    
class AnonymousUser(AnonymousUserMixin):
    @property
    def is_confirmed(self):
        return False
    
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

    def ping(self):
        pass
