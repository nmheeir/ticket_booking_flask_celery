from datetime import datetime, timedelta
from app.extensions import celery
from app.models.booking import Booking
from app.models.event import Event
from app.models.ticket import Ticket
from app.utils.database import db, commit_changes
from app.services.notification_service import NotificationService

@celery.task(name='tasks.process_booking')
def process_booking(booking_id):
    """Process a booking after payment confirmation"""
    try:
        booking = Booking.query.get(booking_id)
        if not booking:
            return {'status': 'error', 'message': 'Booking not found'}

        # Generate tickets
        for _ in range(booking.quantity):
            ticket = Ticket(event_id=booking.event_id, booking_id=booking.id)
            db.session.add(ticket)

        # Update booking status
        booking.confirm()
        
        # Update event available tickets
        event = Event.query.get(booking.event_id)
        event.update_available_tickets(booking.quantity)

        commit_changes()

        # Send confirmation notification
        NotificationService.send_booking_confirmation(booking)

        return {
            'status': 'success',
            'booking_number': booking.booking_number,
            'tickets': [ticket.ticket_number for ticket in booking.tickets]
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@celery.task(name='tasks.cancel_expired_bookings')
def cancel_expired_bookings():
    """Cancel unpaid bookings after expiration time"""
    expiration_time = datetime.utcnow() - timedelta(minutes=30)
    expired_bookings = Booking.query.filter(
        Booking.status == 'pending',
        Booking.payment_status == 'pending',
        Booking.created_at <= expiration_time
    ).all()

    cancelled_count = 0
    for booking in expired_bookings:
        try:
            # Return tickets to event
            event = Event.query.get(booking.event_id)
            event.update_available_tickets(booking.quantity, operation='increase')
            
            # Cancel booking
            booking.cancel()
            commit_changes()
            
            # Send cancellation notification
            NotificationService.send_booking_cancellation(booking)
            
            cancelled_count += 1
        except Exception as e:
            continue

    return {'status': 'success', 'cancelled_bookings': cancelled_count}

@celery.task(name='tasks.generate_booking_report')
def generate_booking_report(start_date, end_date):
    """Generate booking report for a date range"""
    try:
        bookings = Booking.query.filter(
            Booking.created_at.between(start_date, end_date),
            Booking.status == 'confirmed',
            Booking.payment_status == 'paid'
        ).all()

        report_data = {
            'total_bookings': len(bookings),
            'total_revenue': sum(booking.total_amount for booking in bookings),
            'bookings': [booking.to_dict() for booking in bookings]
        }

        return {'status': 'success', 'data': report_data}
    except Exception as e:
        return {'status': 'error', 'message': str(e)} 