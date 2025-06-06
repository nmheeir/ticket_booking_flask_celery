from datetime import datetime
import uuid
from random import randint
from app.utils.database import db
from app.models.user import User
from app.models.event import Event

class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    booking_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, refunded
    payment_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tickets = db.relationship('Ticket', backref='booking', lazy=True)
    event = db.relationship('Event', backref='bookings', lazy=True)

    def __init__(self, user_id, event_id, quantity, total_amount):
        self.booking_number = self.generate_booking_number()
        self.user_id = user_id
        self.event_id = event_id
        self.quantity = quantity
        self.total_amount = total_amount

    @staticmethod
    def generate_booking_number():
        """Generate unique booking number"""
        return f"BKG-{uuid.uuid4().hex[:8].upper()}"

    def confirm(self):
        """Confirm booking"""
        self.status = 'confirmed'

    def cancel(self):
        """Cancel booking"""
        self.status = 'cancelled'

    def mark_as_paid(self, payment_id):
        """Mark booking as paid"""
        self.payment_status = 'paid'
        self.payment_id = payment_id

    def refund(self):
        """Mark booking as refunded"""
        self.payment_status = 'refunded'

    def is_cancellable(self):
        """Check if booking can be cancelled"""
        return self.status == 'confirmed' and self.payment_status == 'paid'

    def to_dict(self):
        """Convert booking object to dictionary"""
        return {
            'id': self.id,
            'booking_number': self.booking_number,
            'user_id': self.user_id,
            'event_id': self.event_id,
            'quantity': self.quantity,
            'total_amount': self.total_amount,
            'status': self.status,
            'payment_status': self.payment_status,
            'payment_id': self.payment_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tickets': [ticket.to_dict() for ticket in self.tickets]
        }
        
    def generate_fake_data(count=20):
        """Generate fake data for testing"""
        from faker import Faker
        fake = Faker()
        bookings = []
        eventCount = Event.query.count()
        userCount = User.query.count()
        for _ in range(count):
            u = User.query.offset(randint(0, userCount - 1)).first()
            p = Event.query.offset(randint(0, eventCount - 1)).first()
            booking = Booking(
                user_id=u.id,
                event_id=p.id,
                quantity=fake.random_int(min=1, max=5),
                total_amount=fake.random_int(min=10, max=100)
            )
            bookings.append(booking)
        return bookings

    def __repr__(self):
        return f'<Booking {self.booking_number}>' 