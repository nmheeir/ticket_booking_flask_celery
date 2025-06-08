from datetime import datetime
from flask import render_template, current_app
from flask_mail import Message
from app.extensions import mail
from app.celery.tasks.email_tasks import send_email_notification
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_email(recipient_email, subject, template_name, context):
        """
        Send an email using Flask-Mail through Celery task
        
        Args:
            recipient_email (str): Email address of the recipient
            subject (str): Email subject
            template_name (str): Name of the template file (e.g. 'mail/registration_confirmation.html')
            context (dict): Context variables for the template
            
        Returns:
            bool: True if email was queued successfully, False otherwise
        """
        try:
            # Add current year to context for all templates
            if 'year' not in context:
                context['year'] = datetime.utcnow().year

            logger.info(f"Preparing to queue email to {recipient_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Using template: {template_name}")
            
            # Get mail sender from config
            mail_sender = current_app.config.get('MAIL_DEFAULT_SENDER')
            if not mail_sender:
                logger.error("MAIL_DEFAULT_SENDER not configured")
                return False
            
            # Queue email sending task
            send_email_notification.delay(
                recipient_email=recipient_email,
                subject=subject,
                template_name=template_name,
                context=context
            )
            
            logger.info(f"Email queued successfully for {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error queuing email for {recipient_email}: {str(e)}")
            logger.exception("Full traceback:")
            return False