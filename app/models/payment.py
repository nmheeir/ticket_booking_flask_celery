from sqlalchemy import Nullable
from app.utils.database import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.String(64), primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, paid, refunded, failed
    method = db.Column(db.String(20), default='card')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    refunded_at = db.Column(db.DateTime, nullable=True)