from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask import current_app
from app.models.user import User
from app.forms.auth import LoginForm, RegistrationForm
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.index'))
        flash('Invalid email or password', 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user, message = AuthService.register_user(
            email=form.email.data,
            password=form.password.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data
        )
        
        if user:
            flash(message, 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(message, 'danger')

    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.before_app_request
def before_request():
    if current_user.is_authenticated and not current_user.is_confirmed \
        and request.blueprint != 'auth' \
        and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))

@auth_bp.route('/confirm/<token>')
def confirm_email(token):
    """Confirm user's email address"""
    if current_user.is_authenticated and current_user.is_confirmed:
        flash('Your account is already confirmed.', 'info')
        return redirect(url_for('main.index'))
        
    success, message, user = AuthService.confirm_email(token)
    flash(message, 'success' if success else 'danger')
    
    if success and user and not current_user.is_authenticated:
        login_user(user)
        
    if success:
        return redirect(url_for('main.index'))
    return redirect(url_for('auth.unconfirmed'))

@auth_bp.route('/unconfirmed')
def unconfirmed():
    """Show unconfirmed page"""
    if current_user.is_anonymous:
        return redirect(url_for('auth.login'))
    if current_user.is_confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

@auth_bp.route('/resend-confirmation')
@login_required
def resend_confirmation():
    """Resend confirmation email"""
    success, message = AuthService.resend_confirmation_email(current_user)
    flash(message, 'info' if success else 'danger')
    
    if success:
        return redirect(url_for('auth.unconfirmed'))
    else:
        return redirect(url_for('main.index'))
