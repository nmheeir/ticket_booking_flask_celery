from flask import current_app, render_template
from flask_mail import Message, Mail

class NotificationService:
    @staticmethod
    def send_email(recipient_email, subject, template_name, context):
        """Send email using Flask-Mail"""
        mail = Mail(current_app)
        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        msg.html = render_template(template_name, **context)
        mail.send(msg)

    @classmethod
    def send_booking_confirmation(cls, booking):
        """Send booking confirmation email"""
        from app.models.user import User
        user = User.query.get(booking.user_id)
        
        context = {
            'user': user,
            'booking': booking,
            'event': booking.event,
            'tickets': booking.tickets
        }
        
        cls.send_email(
            recipient_email=user.email,
            subject='Booking Confirmation',
            template_name='email/booking_confirmation.html',
            context=context
        )

    @classmethod
    def send_booking_cancellation(cls, booking):
        """Send booking cancellation email"""
        from app.models.user import User
        user = User.query.get(booking.user_id)
        
        context = {
            'user': user,
            'booking': booking,
            'event': booking.event
        }
        
        cls.send_email(
            recipient_email=user.email,
            subject='Booking Cancelled',
            template_name='email/booking_cancellation.html',
            context=context
        )

    @classmethod
    def send_booking_reminder(cls, booking):
        """Send booking reminder email"""
        from app.models.user import User
        user = User.query.get(booking.user_id)
        
        context = {
            'user': user,
            'booking': booking,
            'event': booking.event,
            'tickets': booking.tickets
        }
        
        cls.send_email(
            recipient_email=user.email,
            subject='Event Reminder',
            template_name='email/booking_reminder.html',
            context=context
        )

    @classmethod
    def send_event_update(cls, booking, update_message):
        """Send event update email"""
        from app.models.user import User
        user = User.query.get(booking.user_id)
        
        context = {
            'user': user,
            'booking': booking,
            'event': booking.event,
            'update_message': update_message
        }
        
        cls.send_email(
            recipient_email=user.email,
            subject='Event Update',
            template_name='email/event_update.html',
            context=context
        ) 