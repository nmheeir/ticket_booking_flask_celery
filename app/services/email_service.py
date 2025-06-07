from flask import render_template, current_app
from flask_mail import Message
from app.extensions import mail
import os, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_email(recipient_email, subject, template_name, context):
        """Send email using Flask-Mail"""
        try:
            logger.info(f"Preparing to send email to {recipient_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Using template: {template_name}")
            
            msg = Message(
                subject=subject,
                recipients=[recipient_email],
                sender=os.getenv('MAIL_DEFAULT_SENDER')
            )
            msg.html = render_template(template_name, **context)
            
            logger.info("Email content rendered successfully")
            mail.send(msg)
            logger.info(f"Email sent successfully to {recipient_email}")
            
            return True
        except Exception as e:
            logger.error(f"Error sending email to {recipient_email}: {str(e)}")
            logger.exception("Full traceback:")
            return False