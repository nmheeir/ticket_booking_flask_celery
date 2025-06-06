from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.models.event import Event
from app.models.booking import Booking
from app.forms.booking import BookingForm
from app.forms.event import EventForm
from app.utils.database import db, commit_changes
from app.utils.decorators import permission_required
from app.utils.permissions import Permission
from datetime import datetime

events_bp = Blueprint("events", __name__)


@events_bp.route("/")
def list():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    search = request.args.get("search", "").strip()

    query = Event.query.filter(Event.event_date >= datetime.now())

    if search:
        # Lọc theo tên hoặc địa điểm (venue)
        query = query.filter(
            or_(
                Event.title.ilike(f"%{search}%"),
                Event.venue.ilike(f"%{search}%")
            )
        )

    query = query.order_by(Event.event_date)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    events = pagination.items

    return render_template(
        "events/list.html",
        events=events,
        pagination=pagination,
        search=search,
    )


@events_bp.route("/<int:event_id>")
def detail(event_id):
    event = Event.query.get_or_404(event_id)
    form = BookingForm()
    return render_template("events/detail.html", event=event, form=form)


@events_bp.route("/create", methods=["GET", "POST"])
@permission_required(Permission.MANAGE_EVENTS)
def create():
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            name=form.name.data,
            description=form.description.data,
            event_date=form.event_date.data,
            venue=form.venue.data,
            total_tickets=form.total_tickets.data,
            price=form.price.data,
        )
        db.session.add(event)
        commit_changes()
        flash("Event created successfully!", "success")
        return redirect(url_for("events.detail", event_id=event.id))
    return render_template("events/create.html", form=form)


@events_bp.route("/<int:event_id>/edit", methods=["GET", "POST"])
@permission_required(Permission.MANAGE_EVENTS)
def edit(event_id):
    event = Event.query.get_or_404(event_id)
    form = EventForm(obj=event)
    if form.validate_on_submit():
        event.name = form.name.data
        event.description = form.description.data
        event.event_date = form.event_date.data
        event.venue = form.venue.data
        event.total_tickets = form.total_tickets.data
        event.price = form.price.data
        commit_changes()
        flash("Event updated successfully!", "success")
        return redirect(url_for("events.detail", event_id=event.id))
    return render_template("events/edit.html", form=form, event=event)


@events_bp.route("/<int:event_id>/delete", methods=["POST"])
@permission_required(Permission.MANAGE_EVENTS)
def delete(event_id):
    event = Event.query.get_or_404(event_id)
    if Booking.query.filter_by(event_id=event.id).first():
        flash("Cannot delete event with existing bookings.", "danger")
    else:
        db.session.delete(event)
        commit_changes()
        flash("Event deleted successfully!", "success")
    return redirect(url_for("events.list"))
