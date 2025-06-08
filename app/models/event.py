from datetime import datetime
from app.utils.database import db


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default="draft")
    venue = db.Column(db.String(200), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    total_tickets = db.Column(db.Integer, nullable=False)
    available_tickets = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    tickets = db.relationship("Ticket", backref="event", lazy=True)

    def __init__(
        self,
        title,
        description,
        venue,
        event_date,
        total_tickets,
        price,
        status,
        category=None,
        image_url=None,
    ):
        self.title = title
        self.description = description
        self.venue = venue
        self.event_date = event_date
        self.total_tickets = total_tickets
        self.available_tickets = total_tickets
        self.price = price
        self.status = status
        self.category = category
        self.image_url = image_url

    def update_available_tickets(self, quantity, operation="decrease"):
        """Update available tickets count"""
        if operation == "decrease":
            if self.available_tickets >= quantity:
                self.available_tickets -= quantity
                return True
            return False
        elif operation == "increase":
            if self.available_tickets + quantity <= self.total_tickets:
                self.available_tickets += quantity
                return True
            return False

    def is_sold_out(self):
        """Check if event is sold out"""
        return self.available_tickets <= 0

    def to_dict(self):
        """Convert event object to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "venue": self.venue,
            "event_date": self.event_date.isoformat(),
            "status": self.status,
            "total_tickets": self.total_tickets,
            "available_tickets": self.available_tickets,
            "price": self.price,
            "category": self.category,
            "image_url": self.image_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @staticmethod
    def generate_fake_data(count=10):
        """Generate fake data for testing"""
        from faker import Faker

        fake = Faker()
        events = []
        for _ in range(count):
            event = Event(
                title=fake.sentence(),
                description=fake.text(),
                status=fake.random_element(
                    elements=("draft", "published", "cancelled")
                ),
                venue=fake.city(),
                event_date=fake.date_time_between(start_date="+1d", end_date="+30d"),
                total_tickets=fake.random_int(min=100, max=500),
                price=fake.random_int(min=10, max=100),
                category=fake.random_element(
                    elements=("Music", "Art", "Sports", "Technology", "Other")
                ),
                image_url=fake.image_url(300, 400),
            )
            events.append(event)
        return events

    def __repr__(self):
        return f"<Event {self.title}>"
