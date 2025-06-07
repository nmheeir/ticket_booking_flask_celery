from datetime import datetime
import uuid
from app.models.payment import Payment
from app.utils.database import db


class PaymentService:
    @staticmethod
    def process_payment(amount, card_number, expiry, cvv, booking_id):
        """Process payment (mock implementation)"""
        # In production: Gọi Stripe API ở đây
        payment_id = str(uuid.uuid4())

        payment = Payment(
            id=payment_id,
            booking_id=booking_id,
            amount=amount,
            status='paid',
            method='card',
            created_at=datetime.utcnow()
        )
        db.session.add(payment)
        db.session.commit()

        return {'status': 'success', 'payment_id': payment_id}

    @staticmethod
    def create_payment_intent(amount, card_number, expiry, cvv):
        """Create a payment intent (mocked)"""
        intent_id = str(uuid.uuid4())
        return {
            'status': 'created',
            'intent_id': intent_id,
            'amount': amount,
            'currency': 'USD'
        }

    @staticmethod
    def process_refund(booking_id):
        """Process refund for a booking (mocked)"""
        payment = Payment.query.filter_by(booking_id=booking_id).first()

        if not payment:
            return {'status': 'error', 'message': 'Payment not found'}

        if payment.status != 'paid':
            return {'status': 'error', 'message': 'Invalid payment status'}

        # Update status
        payment.status = 'refunded'
        payment.refunded_at = datetime.utcnow()
        db.session.commit()

        return {'status': 'success', 'message': 'Refund processed'}

    @staticmethod
    def get_payment_status(booking_id):
        """Get payment status"""
        payment = Payment.query.filter_by(booking_id=booking_id).first()
        if not payment:
            return 'not_found'
        return payment.status

    @staticmethod
    def get_payment_details(booking_id):
        """Return detailed payment info"""
        payment = Payment.query.filter_by(booking_id=booking_id).first()
        if not payment:
            return None

        return {
            'payment_id': payment.id,
            'amount': payment.amount,
            'status': payment.status,
            'method': payment.method,
            'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'refunded_at': payment.refunded_at.strftime('%Y-%m-%d %H:%M:%S') if payment.refunded_at else None
        }
