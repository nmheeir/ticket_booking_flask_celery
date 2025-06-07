from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.forms.auth import RegistrationForm, LoginForm
from app.services.auth_service import AuthService
from datetime import datetime
from app.tasks import send_email_notification
