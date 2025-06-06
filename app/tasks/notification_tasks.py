from app.tasks.celery_app import celery
from app.services.notification_service import NotificationService

@celery.task(name='tasks.send_email_notification')
def send_email_notification(recipient_email, subject, template_name, context):
    """Send email notification"""
    try:
        NotificationService.send_email(
            recipient_email=recipient_email,
            subject=subject,
            template_name=template_name,
            context=context
        )
        return {'status': 'success', 'message': f'Email sent to {recipient_email}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@celery.task(name='tasks.send_booking_reminder')
def send_booking_reminder(booking_id):
    """Send booking reminder before event"""
    try:
        from app.models.booking import Booking
        booking = Booking.query.get(booking_id)
        if not booking:
            return {'status': 'error', 'message': 'Booking not found'}

        NotificationService.send_booking_reminder(booking)
        return {'status': 'success', 'booking_number': booking.booking_number}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@celery.task(name='tasks.send_event_updates')
def send_event_updates(event_id, update_message):
    """Send updates about an event to all ticket holders"""
    try:
        from app.models.event import Event
        from app.models.booking import Booking
        
        event = Event.query.get(event_id)
        if not event:
            return {'status': 'error', 'message': 'Event not found'}

        # Get all confirmed bookings for the event
        bookings = Booking.query.filter(
            Booking.event_id == event_id,
            Booking.status == 'confirmed'
        ).all()

        notification_count = 0
        for booking in bookings:
            try:
                NotificationService.send_event_update(booking, update_message)
                notification_count += 1
            except Exception:
                continue

        return {
            'status': 'success',
            'notifications_sent': notification_count,
            'total_bookings': len(bookings)
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)} 