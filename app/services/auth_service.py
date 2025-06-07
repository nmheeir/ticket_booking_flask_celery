from datetime import datetime
from flask import current_app, url_for
from app.models.user import User
from app.utils.database import db
from app.celery.tasks.notification_tasks import send_email_notification
from itsdangerous import Serializer

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
            current_app.logger.error(f"Error in user registration: {str(e)}")
            return None, "An error occurred during registration. Please try again."

    @staticmethod
    def confirm_email(token):
        """
        Confirm user's email using token
        
        Args:
            token (str): Confirmation token
            
        Returns:
            tuple: (bool success, str message)
        """
        try:
            # Get user ID from token
            s = Serializer(current_app.config['SECRET_KEY'])
            data = s.loads(token)
            user_id = data.get('confirm')

            if not user_id:
                return False, "Invalid confirmation link"

            # Get user
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"

            if user.is_confirmed:
                return True, "Account already confirmed"

            # Confirm user
            user.is_confirmed = True
            user.confirmed_at = datetime.utcnow()
            db.session.commit()

            return True, "Your account has been confirmed successfully"

        except Exception as e:
            current_app.logger.error(f"Error in email confirmation: {str(e)}")
            return False, "The confirmation link is invalid or has expired" 