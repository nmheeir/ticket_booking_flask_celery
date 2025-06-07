from app.extensions import celery
from app.services.email_service import EmailService
import logging
from datetime import datetime, timedelta
from app.models.event import Event
from app.models.booking import Booking

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

@celery.task(name='tasks.send_event_reminders')
def send_event_reminders():
    """Send reminders for events happening soon"""
    logger.info("Starting event reminder check")
    
    # Get events happening in the next 24 hours
    reminder_threshold = datetime.utcnow() + timedelta(hours=24)
    upcoming_events = Event.query.filter(
        Event.start_time <= reminder_threshold,
        Event.start_time > datetime.utcnow(),
        Event.status == 'active'
    ).all()
    
    reminder_count = 0
    failed_count = 0
    
    for event in upcoming_events:
        # Get all confirmed bookings for this event
        bookings = Booking.query.filter(
            Booking.event_id == event.id,
            Booking.status == 'confirmed'
        ).all()
        
        for booking in bookings:
            try:
                # Prepare reminder context
                context = {
                    'user': booking.user.to_dict(),
                    'event': event.to_dict(),
                    'booking': booking.to_dict(),
                    'tickets': [ticket.to_dict() for ticket in booking.tickets]
                }
                
                # Send reminder email
                success = EmailService.send_email(
                    recipient_email=booking.user.email,
                    subject=f"Reminder: {event.name} starts in 24 hours!",
                    template_name='mail/event_reminder.html',
                    context=context
                )
                
                if success:
                    reminder_count += 1
                    logger.info(f"Sent reminder for event {event.name} to {booking.user.email}")
                else:
                    failed_count += 1
                    logger.error(f"Failed to send reminder for event {event.name} to {booking.user.email}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Error sending reminder: {str(e)}")
                continue
    
    logger.info(f"Event reminder task completed. Sent: {reminder_count}, Failed: {failed_count}")
    return {
        'status': 'success',
        'reminders_sent': reminder_count,
        'reminders_failed': failed_count
    }

@celery.task(name='tasks.send_low_ticket_alerts')
def send_low_ticket_alerts():
    """Send alerts for events with low ticket availability"""
    logger.info("Starting low ticket availability check")
    
    # Get active events with less than 10% tickets remaining
    active_events = Event.query.filter(
        Event.status == 'active',
        Event.start_time > datetime.utcnow()
    ).all()
    
    alert_count = 0
    for event in active_events:
        try:
            # Calculate ticket availability percentage
            remaining_percentage = (event.available_tickets / event.total_tickets) * 100
            
            if remaining_percentage <= 10:  # Less than 10% tickets remaining
                # Get event organizer/admin email
                admin_email = event.organizer_email  # Assuming you have this field
                
                # Send low ticket alert
                context = {
                    'event': event.to_dict(),
                    'remaining_tickets': event.available_tickets,
                    'remaining_percentage': round(remaining_percentage, 2)
                }
                
                success = EmailService.send_email(
                    recipient_email=admin_email,
                    subject=f"Low Ticket Alert: {event.name}",
                    template_name='mail/low_ticket_alert.html',
                    context=context
                )
                
                if success:
                    alert_count += 1
                    logger.info(f"Sent low ticket alert for event {event.name}")
                    
        except Exception as e:
            logger.error(f"Error sending low ticket alert for event {event.name}: {str(e)}")
            continue
    
    logger.info(f"Low ticket alert task completed. Alerts sent: {alert_count}")
    return {
        'status': 'success',
        'alerts_sent': alert_count
    }

@celery.task(name='tasks.cleanup_abandoned_bookings')
def cleanup_abandoned_bookings():
    """Clean up abandoned bookings (created but not paid)"""
    logger.info("Starting abandoned booking cleanup")
    
    # Find bookings that were created more than 15 minutes ago and still pending
    cutoff_time = datetime.utcnow() - timedelta(minutes=15)
    abandoned_bookings = Booking.query.filter(
        Booking.status == 'pending',
        Booking.created_at <= cutoff_time
    ).all()
    
    cleaned_count = 0
    for booking in abandoned_bookings:
        try:
            # Return tickets to event
            event = Event.query.get(booking.event_id)
            if event:
                event.available_tickets += booking.quantity
            
            # Delete the booking
            Booking.query.filter_by(id=booking.id).delete()
            
            cleaned_count += 1
            logger.info(f"Cleaned up abandoned booking {booking.id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up booking {booking.id}: {str(e)}")
            continue
    
    logger.info(f"Abandoned booking cleanup completed. Cleaned: {cleaned_count}")
    return {
        'status': 'success',
        'bookings_cleaned': cleaned_count
    } 