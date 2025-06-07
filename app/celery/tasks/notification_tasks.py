from app.extensions import celery
from app.services.email_service import EmailService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



@celery.task(name='tasks.send_email_notification', bind=True, max_retries=3)
def send_email_notification(self, recipient_email, subject, template_name, context):
    """Send email notification"""
    try:
        logger.info(f"Starting email notification task for {recipient_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Using template: {template_name}")
        logger.info(f"Context: {context}")
        
        success = EmailService.send_email(
            recipient_email=recipient_email,
            subject=subject,
            template_name=template_name,
            context=context
        )
        if success:
            logger.info(f"Email sent successfully to {recipient_email}")
            return {'status': 'success', 'message': f'Email sent to {recipient_email}'}
        else:
            logger.error(f"Failed to send email to {recipient_email}")
            raise Exception('Failed to send email')
    except Exception as e:
        # Retry task if failed
        if self.request.retries < self.max_retries:
            self.retry(countdown=60 * (self.request.retries + 1), exc=e)
        logger.error(f"Email notification task failed for {recipient_email}: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@celery.task(name='tasks.send_booking_reminder')
def send_booking_reminder(booking_id):
    """Send booking reminder before event"""
    try:
        from app.models.booking import Booking
        booking = Booking.query.get(booking_id)
        if not booking:
            return {'status': 'error', 'message': 'Booking not found'}

        # Get user information
        user = booking.user
        
        # Prepare email context
        context = {
            'user': user,
            'booking': booking,
            'event': booking.event,
            'tickets': booking.tickets
        }
        
        # Send reminder email
        success = EmailService.send_email(
            recipient_email=user.email,
            subject=f'Reminder: {booking.event.name} is coming up!',
            template_name='mail/booking_reminder.html',
            context=context
        )
        
        if success:
            return {'status': 'success', 'booking_number': booking.booking_number}
        else:
            raise Exception('Failed to send reminder email')
            
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
        failed_count = 0
        
        for booking in bookings:
            try:
                # Prepare email context
                context = {
                    'user': booking.user,
                    'booking': booking,
                    'event': event,
                    'update_message': update_message
                }
                
                # Send update email
                success = EmailService.send_email(
                    recipient_email=booking.user.email,
                    subject=f'Update for {event.name}',
                    template_name='mail/event_update.html',
                    context=context
                )
                
                if success:
                    notification_count += 1
                else:
                    failed_count += 1
                    
            except Exception:
                failed_count += 1
                continue

        return {
            'status': 'success',
            'notifications_sent': notification_count,
            'notifications_failed': failed_count,
            'total_bookings': len(bookings)
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)} 