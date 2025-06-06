from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user
from app.utils.permissions import Permission

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'danger')
                return redirect(url_for('auth.login', next=request.path))
            
            if not current_user.is_active:
                flash('Your account is not active.', 'danger')
                return redirect(url_for('main.index'))
                
            if not current_user.can(permission):
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.index'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return permission_required(Permission.MANAGE_USERS)(f)

def staff_required(f):
    return permission_required(Permission.MANAGE_EVENTS)(f) 