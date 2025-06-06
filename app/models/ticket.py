from datetime import datetime
import uuid
from app.utils.database import db
from app.models.booking import Booking
from random import randint

class Ticket(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(50), unique=True, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, used, cancelled
    qr_code = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, event_id, booking_id):
        self.ticket_number = self.generate_ticket_number()
        self.event_id = event_id
        self.booking_id = booking_id
        self.generate_qr_code()

    @staticmethod
    def generate_ticket_number():
        """Generate unique ticket number"""
        return f"TKT-{uuid.uuid4().hex[:8].upper()}"

    def generate_qr_code(self):
        """Generate QR code for ticket"""
        # In a real application, you would use a QR code generation library
        # and possibly store the QR code image in a cloud storage
        self.qr_code = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={self.ticket_number}"

    def mark_as_used(self):
        """Mark ticket as used"""
        self.status = 'used'

    def cancel(self):
        """Cancel ticket"""
        self.status = 'cancelled'

    def is_valid(self):
        """Check if ticket is valid"""
        return self.status == 'active'

    def to_dict(self):
        """Convert ticket object to dictionary"""
        return {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'event_id': self.event_id,
            'booking_id': self.booking_id,
            'status': self.status,
            'qr_code': self.qr_code,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
    def generate_fake_data(count=20):
        """Generate fake Ticket objects for testing"""
        from faker import Faker
        fake = Faker()
        tickets = []

        booking_count = Booking.query.count()
        if booking_count == 0:
            raise ValueError("No bookings found in the database. Cannot generate tickets without bookings.")

        for _ in range(count):
            booking = Booking.query.offset(randint(0, booking_count - 1)).first()
            if not booking:
                continue  # Tránh lỗi nếu không lấy được booking

            ticket = Ticket(
                event_id=booking.event_id,
                booking_id=booking.id,
            )

            tickets.append(ticket)

        return tickets

    def __repr__(self):
        return f'<Ticket {self.ticket_number}>' 