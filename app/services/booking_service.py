from datetime import datetime
from app.models.booking import Booking
from app.models.event import Event
from app.utils.database import db, commit_changes
from app.services.payment_service import PaymentService

class BookingService:
    @staticmethod
    def create_booking(user_id, event_id, quantity):
        """Create a new booking"""
        event = Event.query.get(event_id)
        if not event:
            raise ValueError('Event not found')

        if event.is_sold_out():
            raise ValueError('Event is sold out')

        if quantity > event.available_tickets:
            raise ValueError('Not enough tickets available')

        total_amount = event.price * quantity

        booking = Booking(
            user_id=user_id,
            event_id=event_id,
            quantity=quantity,
            total_amount=total_amount
        )

        db.session.add(booking)
        commit_changes()

        # Create payment intent
        payment_data = PaymentService.create_payment_intent(booking.id)
        
        return {
            'booking': booking.to_dict(),
            'payment': payment_data
        }

    @staticmethod
    def get_user_bookings(user_id):
        """Get all bookings for a user"""
        return Booking.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_event_bookings(event_id):
        """Get all bookings for an event"""
        return Booking.query.filter_by(event_id=event_id).all()

    @staticmethod
    def cancel_booking(booking_id, user_id):
        """Cancel a booking"""
        booking = Booking.query.get(booking_id)
        if not booking:
            raise ValueError('Booking not found')

        if booking.user_id != user_id:
            raise ValueError('Unauthorized to cancel this booking')

        if not booking.is_cancellable():
            raise ValueError('Booking cannot be cancelled')

        # Process refund
        refund_result = PaymentService.process_refund(booking.id)
        if refund_result['status'] != 'success':
            raise ValueError('Refund failed')

        # Return tickets to event
        event = Event.query.get(booking.event_id)
        event.update_available_tickets(booking.quantity, operation='increase')

        # Cancel booking
        booking.cancel()
        commit_changes()

        return booking.to_dict()

    @staticmethod
    def get_booking_stats(start_date=None, end_date=None):
        """Get booking statistics"""
        query = Booking.query.filter(
            Booking.status == 'confirmed',
            Booking.payment_status == 'paid'
        )

        if start_date:
            query = query.filter(Booking.created_at >= start_date)
        if end_date:
            query = query.filter(Booking.created_at <= end_date)

        bookings = query.all()

        return {
            'total_bookings': len(bookings),
            'total_revenue': sum(booking.total_amount for booking in bookings),
            'average_booking_value': sum(booking.total_amount for booking in bookings) / len(bookings) if bookings else 0
        } 