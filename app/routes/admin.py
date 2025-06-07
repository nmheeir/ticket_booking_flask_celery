from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user
from app.models.user import User
from app.models.event import Event
from app.models.booking import Booking
from app.models.role import Role
from app.utils.database import db, commit_changes
from app.utils.decorators import permission_required
from app.utils.permissions import Permission
from datetime import datetime, timedelta

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


@admin_bp.route("/users")
@permission_required(Permission.MANAGE_USERS)
def users():
    users = User.query.all()
    roles = Role.query.all()
    return render_template("admin/users.html", users=users, roles=roles)


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@permission_required(Permission.MANAGE_USERS)
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    role_id = request.form.get("role_id", type=int)

    if user.id == current_user.id:
        flash("You cannot change your own role.", "danger")
    else:
        role = Role.query.get_or_404(role_id)
        user.role = role
        commit_changes()
        flash(f"Role updated for {user.email}", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@permission_required(Permission.MANAGE_USERS)
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "danger")
    else:
        user.is_active = not user.is_active
        commit_changes()
        flash(f"Active status updated for {user.email}", "success")
    return redirect(url_for("admin.users"))


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
