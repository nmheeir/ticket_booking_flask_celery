from datetime import datetime
from flask import render_template, current_app
from flask_mail import Message
from app.extensions import mail
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_email(recipient_email, subject, template_name, context):
        """
        Send an email using Flask-Mail
        
        Args:
            recipient_email (str): Email address of the recipient
            subject (str): Email subject
            template_name (str): Name of the template file (e.g. 'mail/registration_confirmation.html')
            context (dict): Context variables for the template
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Add current year to context for all templates
            if 'year' not in context:
                context['year'] = datetime.utcnow().year

            logger.info(f"Preparing to send email to {recipient_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Using template: {template_name}")
            
            # Get mail sender from config
            mail_sender = current_app.config.get('MAIL_DEFAULT_SENDER')
            if not mail_sender:
                logger.error("MAIL_DEFAULT_SENDER not configured")
                return False
            
            msg = Message(
                subject=subject,
                recipients=[recipient_email],
                sender=mail_sender
            )
            
            # Render template with context
            msg.html = render_template(template_name, **context)
            
            logger.info("Email content rendered successfully")
            mail.send(msg)
            logger.info(f"Email sent successfully to {recipient_email}")
            
            return True
        except Exception as e:
            logger.error(f"Error sending email to {recipient_email}: {str(e)}")
            logger.exception("Full traceback:")
            return False