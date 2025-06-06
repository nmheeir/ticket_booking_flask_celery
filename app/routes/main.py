from flask import Blueprint, render_template
from app.models.event import Event
from datetime import datetime

main_bp = Blueprint('main', __name__, static_folder='../static', template_folder='../templates')

@main_bp.route('/')
def index():
    # Get upcoming events
    upcoming_events = Event.query.filter(
        Event.event_date >= datetime.utcnow(),
        Event.is_active == True
    ).order_by(Event.event_date.asc()).limit(6).all()

    # Get featured events (you might want to add a 'featured' field to the Event model)
    featured_events = Event.query.filter(
        Event.is_active == True
    ).order_by(Event.created_at.desc()).limit(3).all()

    return render_template(
        'main/index.html',
        upcoming_events=upcoming_events,
        featured_events=featured_events
    ) 