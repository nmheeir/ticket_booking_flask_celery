from datetime import datetime
from flask import current_app, url_for
from app.models.user import User
from app.utils.database import db
from app.celery.tasks.email_tasks import send_email_notification
from itsdangerous import URLSafeTimedSerializer

class AuthService:
    @staticmethod
    def register_user(email, password, first_name, last_name, phone=None):
        """
        Register a new user and send confirmation email
        
        Args:
            email (str): User's email
            password (str): User's password
            first_name (str): User's first name
            last_name (str): User's last name
            phone (str, optional): User's phone number
            
        Returns:
            tuple: (User object, str message)
        """
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return None, "Email already registered"

            # Create new user
            user = User(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone
            )
            
            # Save user to database
            db.session.add(user)
            db.session.commit()

            # Generate confirmation token
            token = user.generate_confirmation_token()
            
            # Create confirmation URL
            confirmation_url = url_for(
                'auth.confirm_email',
                token=token,
                _external=True
            )

            # Prepare email context
            context = {
                'user': user.to_dict(),
                'confirmation_url': confirmation_url,
                'year': datetime.utcnow().year
            }

            # Send confirmation email asynchronously using Celery
            send_email_notification.delay(
                recipient_email=user.email,
                subject='Please Confirm Your Account',
                template_name='mail/registration_confirmation.html',
                context=context
            )


            return user, "Registration successful. Please check your email to confirm your account."
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"[register_user] Error registering user with email={email}: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            )
            return None, "An error occurred during registration. Please try again."

    @staticmethod
    def confirm_email(token):
        """
        Confirm user's email using token
        
        Args:
            token (str): Confirmation token
            
        Returns:
            tuple: (bool success, str message, User object or None)
        """
        try:
            # Get user ID from token
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            data = s.loads(token, salt='email-confirm-salt', max_age=3600)  # 1 hour expiration
            user_id = data.get('confirm')

            if not user_id:
                return False, "Invalid confirmation link", None

            # Get user
            user = User.query.get(user_id)
            if not user:
                return False, "User not found", None

            if user.is_confirmed:
                return True, "Account already confirmed", user

            # Confirm user
            user.is_confirmed = True
            user.confirmed_at = datetime.utcnow()
            db.session.commit()

            return True, "Your account has been confirmed successfully", user

        # Trong method confirm_email
        except Exception as e:
            current_app.logger.error(
                f"[confirm_email] Error confirming token={token}: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            )
            return False, "The confirmation link is invalid or has expired", None

        
    @staticmethod
    def resend_confirmation_email(user):
        """
        Resend confirmation email to user if not already confirmed.

        Args:
            user (User): The user to resend email to.

        Returns:
            tuple: (bool success, str message)
        """
        if user.is_confirmed:
            return False, "Your account is already confirmed."

        try:
            token = user.generate_confirmation_token()
            confirmation_url = url_for(
                'auth.confirm_email',
                token=token,
                _external=True
            )

            context = {
                'user': user.to_dict(),
                'confirmation_url': confirmation_url,
                'year': datetime.utcnow().year
            }

            send_email_notification.delay(
                recipient_email=user.email,
                subject='Please Confirm Your Account',
                template_name='mail/registration_confirmation.html',
                context=context
            )

            return True, "A new confirmation email has been sent to your email address."

        # Trong method resend_confirmation_email
        except Exception as e:
            current_app.logger.error(
                f"[resend_confirmation_email] Error resending to user_id={user.id}: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            )
            return False, "An error occurred while resending confirmation email."
