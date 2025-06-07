from datetime import datetime, timedelta
from app.extensions import celery
from app.models.booking import Booking
from app.models.event import Event
from app.models.ticket import Ticket
from app.services.email_service import EmailService
from app.utils.database import db, commit_changes

@celery.task(
    name="tasks.process_booking", bind=True, max_retries=3, default_retry_delay=60
)  # Retry after 60 seconds
def process_booking(self, booking_id):
    """
    Asynchronously process a booking after payment confirmation

    This task performs the following operations:
    1. Validates booking existence
    2. Generates tickets for the booking
    3. Updates booking status to confirmed
    4. Updates event's available ticket count
    5. Sends confirmation notification

    Args:
        booking_id (int): ID of the booking to process

    Returns:
        dict: Processing result containing status and details

    Retries:
        Max retries: 3
        Retry delay: 60 seconds
    """
    try:
        # Retrieve and validate booking
        booking = Booking.query.get(booking_id)
        if not booking:
            return {"status": "error", "message": "Booking not found"}

        # Generate individual tickets for the booking
        for _ in range(booking.quantity):
            ticket = Ticket(
                event_id=booking.event_id,
                booking_id=booking.id,
                # Add additional ticket details as needed
            )
            db.session.add(ticket)

        # Update booking status to confirmed
        booking.confirm()

        # Update event's available ticket count
        event = Event.query.get(booking.event_id)
        event.update_available_tickets(booking.quantity)

        # Commit all database changes
        commit_changes()

        # Send confirmation notification to user
        EmailService.send_email(
            booking.user.email,
            "Booking Confirmation",
            "mail/booking_confirmation.html",
            {"booking": booking},
        )

        # Return success response with booking details
        return {
            "status": "success",
            "booking_number": booking.booking_number,
            "tickets": [ticket.ticket_number for ticket in booking.tickets],
        }
    except Exception as e:
        # Retry the task in case of failure
        self.retry(exc=e)


@celery.task(name="tasks.cancel_expired_bookings")
def cancel_expired_bookings():
    """
    Cancel all unpaid bookings that have exceeded the payment timeout

    This task:
    1. Identifies expired bookings (pending payment > 30 minutes)
    2. Returns tickets to event inventory
    3. Updates booking status to cancelled
    4. Sends cancellation notifications

    Returns:
        dict: Summary of cancelled bookings
    """
    # Calculate expiration threshold (30 minutes ago)
    expiration_time = datetime.utcnow() - timedelta(minutes=30)

    # Find all expired bookings
    expired_bookings = Booking.query.filter(
        Booking.status == "pending",
        Booking.payment_status == "pending",
        Booking.created_at <= expiration_time,
    ).all()

    cancelled_count = 0
    for booking in expired_bookings:
        try:
            # Return tickets to event inventory
            event = Event.query.get(booking.event_id)
            event.update_available_tickets(booking.quantity, operation="increase")

            # Update booking status to cancelled
            booking.cancel()
            commit_changes()

            # Notify user about booking cancellation
            EmailService.send_email(
                booking.user.email,
                "Booking Cancellation",
                "booking_cancellation.html",
                {"booking": booking},
            )

            cancelled_count += 1
        except Exception as e:
            # Log error and continue with next booking
            continue

    return {
        "status": "success",
        "cancelled_bookings": cancelled_count,
        "timestamp": datetime.utcnow().isoformat(),
    }


@celery.task(name="tasks.generate_booking_report")
def generate_booking_report(start_date, end_date):
    """
    Generate a comprehensive booking report for a specified date range

    This task analyzes confirmed and paid bookings within the date range
    and generates statistical data including total bookings, revenue,
    and detailed booking information.

    Args:
        start_date (str): ISO format start date for report period
        end_date (str): ISO format end date for report period

    Returns:
        dict: Report data including statistics and booking details
    """
    try:
        # Convert string dates to datetime objects
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        # Query confirmed and paid bookings
        query = Booking.query.filter(
            Booking.status == "confirmed", Booking.payment_status == "paid"
        )

        # Apply date filters if provided
        if start_dt:
            query = query.filter(Booking.created_at >= start_dt)
        if end_dt:
            query = query.filter(Booking.created_at <= end_dt)

        bookings = query.all()

        # Calculate report statistics
        total_bookings = len(bookings)
        total_revenue = sum(booking.total_amount for booking in bookings)
        avg_booking_value = total_revenue / total_bookings if total_bookings > 0 else 0

        # Prepare detailed report data
        report_data = {
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "average_booking_value": avg_booking_value,
            "period": {"start": start_date, "end": end_date},
            "bookings": [booking.to_dict() for booking in bookings],
        }

        return {"status": "success", "data": report_data}
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
