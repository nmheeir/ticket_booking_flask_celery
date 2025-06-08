from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.models.user import User
from app.models.event import Event
from app.models.booking import Booking
from app.models.role import Role
from app.utils.database import db, commit_changes
from app.utils.decorators import permission_required, admin_required
from app.utils.permissions import Permission
from app.services.email_service import EmailService
from app.extensions import csrf
from datetime import datetime, timedelta
from app.celery.tasks.email_tasks import send_email_notification

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard")
@permission_required(Permission.VIEW_DASHBOARD)
def dashboard():
    # Get basic statistics
    total_users = User.query.count()
    total_events = Event.query.count()
    total_bookings = Booking.query.count()

    # Get recent bookings
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()

    # Get upcoming events
    upcoming_events = (
        Event.query.filter(Event.event_date >= datetime.now())
        .order_by(Event.event_date)
        .limit(5)
        .all()
    )

    # Calculate revenue
    total_revenue = (
        db.session.query(db.func.sum(Booking.total_amount))
        .filter(Booking.status == "confirmed")
        .scalar()
        or 0
    )

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_events=total_events,
        total_bookings=total_bookings,
        total_revenue=total_revenue,
        recent_bookings=recent_bookings,
        upcoming_events=upcoming_events,
    )





@admin_bp.route("/events")
@permission_required(Permission.MANAGE_EVENTS)
def events():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    search = request.args.get("search", "").strip()

    query = Event.query

    if search:
        query = query.filter(Event.title.ilike(f"%{search}%"))

    pagination = query.order_by(Event.event_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    events = pagination.items

    return render_template(
        "admin/events.html",
        events=events,
        pagination=pagination,
        search=search,  # để giữ lại giá trị trong ô tìm kiếm
    )


@admin_bp.route("/bookings")
@permission_required(Permission.VIEW_ALL_BOOKINGS)
def bookings():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template("admin/bookings.html", bookings=bookings)


@admin_bp.route("/reports")
@permission_required(Permission.VIEW_REPORTS)
def reports():
    # Get date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # Daily bookings
    daily_bookings = (
        db.session.query(
            db.func.date(Booking.created_at).label("date"),
            db.func.count(Booking.id).label("count"),
        )
        .filter(Booking.created_at.between(start_date, end_date))
        .group_by(db.func.date(Booking.created_at))
        .all()
    )

    # Revenue by event
    revenue_by_event = (
        db.session.query(Event.name, db.func.sum(Booking.total_amount).label("revenue"))
        .join(Booking, Event.id == Booking.event_id)
        .filter(Booking.status == "confirmed")
        .group_by(Event.id)
        .all()
    )

    return render_template(
        "admin/reports.html",
        daily_bookings=daily_bookings,
        revenue_by_event=revenue_by_event,
    )
    
@admin_bp.route("user_detail/int:user_id")
@permission_required(Permission.VIEW_ALL_BOOKINGS)
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("admin/user_detail.html", user=user)

@admin_bp.route('/users')
@login_required
@admin_required
def list_users():
    users = User.query.all()
    return render_template('admin/users/list.html', users=users)

@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('admin/users/view.html', user=user)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.role = request.form.get('role')
        
        if request.form.get('password'):
            user.set_password(request.form.get('password'))
            
        db.session.commit()
        flash('User updated successfully', 'success')
        return redirect(url_for('admin.list_users'))
        
    return render_template('admin/users/edit.html', user=user)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Cannot delete admin user', 'error')
        return redirect(url_for('admin.list_users'))
        
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully', 'success')
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/send-bulk-email', methods=['GET'])
@login_required
@admin_required
def bulk_email_form():
    users = User.query.all()
    events = Event.query.filter(Event.event_date >= datetime.now()).all()
    return render_template('admin/users/bulk_email.html', users=users, events=events)

@admin_bp.route('/send-bulk-email', methods=['POST'])
@login_required
@admin_required
def send_bulk_email():
    selected_users = request.form.getlist('selected_users[]')
    event_id = request.form.get('event_id')
    custom_message = request.form.get('custom_message', '')
    
    if not selected_users:
        flash('Please select at least one user', 'error')
        return redirect(url_for('admin.bulk_email_form'))
        
    if not event_id:
        flash('Please select an event', 'error')
        return redirect(url_for('admin.bulk_email_form'))
    
    event = Event.query.get_or_404(event_id)
    
    # Tạo event URL trước khi gửi email
    event_url = url_for('events.detail', event_id=event.id, _external=True)
    
    success_count = 0
    fail_count = 0
    
    for user_id in selected_users:
        user = User.query.get(user_id)
        if user:
            context = {
                'user': user.to_dict(),
                'event': event.to_dict(),
                'custom_message': custom_message,
                'event_url': event_url  # Thêm URL vào context
            }
            
            # Gửi email thông qua Celery task
            result = send_email_notification.delay(
                recipient_email=user.email,
                subject=f"New Event Announcement: {event.title}",
                template_name='mail/event_announcement.html',
                context=context
            )
            
            if result.get():
                success_count += 1
            else:
                fail_count += 1
    
    if success_count > 0:
        flash(f'Successfully sent {success_count} emails', 'success')
    if fail_count > 0:
        flash(f'Failed to send {fail_count} emails', 'error')
        
    return redirect(url_for('admin.bulk_email_form'))
