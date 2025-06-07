from datetime import datetime
from app.models.booking import Booking
from app.models.event import Event
from app.utils.database import db, commit_changes
from app.services.payment_service import PaymentService
from app.services.email_service import EmailService
from app.celery.tasks.booking_tasks import process_booking, cancel_expired_bookings, generate_booking_report

class BookingService:
    @staticmethod
    def create_booking(user_id, event_id, quantity):
        """
        Create a new booking in pending state
        
        Args:
            user_id (int): ID of the user making the booking
            event_id (int): ID of the event being booked
            quantity (int): Number of tickets to book
            
        Returns:
            dict: Contains booking details
            
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

        # Create booking record in pending state
        booking = Booking(
            user_id=user_id,
            event_id=event_id,
            quantity=quantity,
            total_amount=total_amount
        )

        db.session.add(booking)
        commit_changes()

        # Schedule booking expiration check after 10 minutes
        cancel_expired_bookings.apply_async(countdown=600)  # 600 seconds = 10 minutes

        return {
            'booking': booking.to_dict()
        }

    @staticmethod
    def complete_payment(booking_id, payment_data):
        """
        Complete payment and process booking
        
        Args:
            booking_id (int): ID of the booking
            payment_data (dict): Payment processing result
            
        Returns:
            dict: Updated booking details
        """
        booking = Booking.query.get(booking_id)
        if not booking:
            raise ValueError('Booking not found')

        if booking.payment_status != 'pending':
            raise ValueError('Invalid booking status')

        # Mark booking as paid
        booking.mark_as_paid(payment_data['payment_id'])
        booking.confirm()
        commit_changes()

        # Process booking (generate tickets, etc)
        process_booking.delay(booking.id)

        # Send confirmation email only after successful payment
        EmailService.send_email(
            recipient_email=booking.user.email,
            subject='Booking Confirmation - Payment Successful',
            template_name='mail/booking_confirmation.html',
            context={
                'booking': booking.to_dict(),
                'event': booking.event.to_dict()
            }
        )

        return booking.to_dict()

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
    def cancel_booking(booking_number, user_id):
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
        booking = Booking.query.filter_by(booking_number=booking_number).first_or_404()
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