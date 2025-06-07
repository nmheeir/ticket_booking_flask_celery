from datetime import datetime
from app.models.booking import Booking
from app.models.event import Event
from app.utils.database import db, commit_changes
from app.services.payment_service import PaymentService
from app.celery.tasks.booking_tasks import process_booking, cancel_expired_bookings, generate_booking_report

class BookingService:
    @staticmethod
    def create_booking(user_id, event_id, quantity):
        """
        Create a new booking and initiate asynchronous processing
        
        Args:
            user_id (int): ID of the user making the booking
            event_id (int): ID of the event being booked
            quantity (int): Number of tickets to book
            
        Returns:
            dict: Contains booking details and payment information
            
        Raises:
            ValueError: If event not found, sold out, or insufficient tickets
        """
        # Validate event existence and availability
        event = Event.query.get(event_id)
        if not event:
            raise ValueError('Event not found')

        if event.is_sold_out():
            raise ValueError('Event is sold out')

        if quantity > event.available_tickets:
            raise ValueError('Not enough tickets available')

        # Calculate total amount
        total_amount = event.price * quantity

        # Create booking record
        booking = Booking(
            user_id=user_id,
            event_id=event_id,
            quantity=quantity,
            total_amount=total_amount
        )

        db.session.add(booking)
        commit_changes()

        # Create payment intent
        payment_data = PaymentService.create_payment_intent(booking.id, 123, 123, 123)
        
        # Trigger asynchronous booking processing
        process_booking.delay(booking.id)

        return {
            'booking': booking.to_dict(),
            'payment': payment_data
        }

    @staticmethod
    def get_user_bookings(user_id):
        """
        Get all bookings for a specific user
        
        Args:
            user_id (int): ID of the user
            
        Returns:
            list: List of Booking objects
        """
        return Booking.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_event_bookings(event_id):
        """
        Get all bookings for a specific event
        
        Args:
            event_id (int): ID of the event
            
        Returns:
            list: List of Booking objects
        """
        return Booking.query.filter_by(event_id=event_id).all()

    @staticmethod
    def cancel_booking(booking_id, user_id):
        """
        Cancel a booking and process refund
        
        Args:
            booking_id (int): ID of the booking to cancel
            user_id (int): ID of the user requesting cancellation
            
        Returns:
            dict: Cancelled booking details
            
        Raises:
            ValueError: If booking not found, unauthorized, or cannot be cancelled
        """
        # Validate booking and permissions
        booking = Booking.query.get(booking_id)
        if not booking:
            raise ValueError('Booking not found')

        if booking.user_id != user_id:
            raise ValueError('Unauthorized to cancel this booking')

        if not booking.is_cancellable():
            raise ValueError('Booking cannot be cancelled')

        # Process payment refund
        refund_result = PaymentService.process_refund(booking.id)
        if refund_result['status'] != 'success':
            raise ValueError('Refund failed')

        # Return tickets to event inventory
        event = Event.query.get(booking.event_id)
        event.update_available_tickets(booking.quantity, operation='increase')

        # Update booking status
        booking.cancel()
        commit_changes()

        return booking.to_dict()

    @staticmethod
    def get_booking_stats(start_date=None, end_date=None):
        """
        Generate booking statistics report asynchronously
        
        Args:
            start_date (datetime, optional): Start date for report period
            end_date (datetime, optional): End date for report period
            
        Returns:
            dict: Task ID for the report generation process
        """
        # Convert dates to string format if provided
        start_str = start_date.isoformat() if start_date else None
        end_str = end_date.isoformat() if end_date else None
        
        # Trigger asynchronous report generation
        task = generate_booking_report.delay(start_str, end_str)
        
        return {'task_id': task.id}

    @staticmethod
    def cleanup_expired_bookings():
        """
        Initiate cleanup of expired bookings
        
        Returns:
            dict: Task ID for the cleanup process
        """
        task = cancel_expired_bookings.delay()
        return {'task_id': task.id} 