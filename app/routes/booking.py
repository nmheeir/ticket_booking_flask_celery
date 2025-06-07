from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user
from app.models.booking import Booking
from app.services.booking_service import BookingService
from app.services.payment_service import PaymentService
from app.forms.booking import BookingForm, PaymentForm
from app.utils.decorators import permission_required
from app.utils.permissions import Permission
import logging
from datetime import datetime
from app.utils.database import db

logger = logging.getLogger(__name__)

booking_bp = Blueprint("booking", __name__)


@booking_bp.route("/my-bookings")
@permission_required(Permission.VIEW_OWN_BOOKINGS)
def my_bookings():
    bookings = (
        Booking.query.filter_by(user_id=current_user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    return render_template("booking/my_bookings.html", bookings=bookings)


@booking_bp.route("/create/<int:event_id>", methods=["POST"])
@permission_required(Permission.BOOK_TICKET)
def create_booking(event_id):
    form = BookingForm()
    if form.validate_on_submit():
        try:
            result = BookingService.create_booking(
                user_id=current_user.id, event_id=event_id, quantity=form.quantity.data
            )
            # Generate payment URL using booking number
            return redirect(url_for("booking.checkout", booking_number=result["booking"]["booking_number"]))
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("events.detail", event_id=event_id))
    return redirect(url_for("events.detail", event_id=event_id))


@booking_bp.route("/checkout/<booking_number>", methods=["GET", "POST"])
@permission_required(Permission.BOOK_TICKET)
def checkout(booking_number):
    booking = Booking.query.filter_by(booking_number=booking_number).first_or_404()
    
    # Verify booking belongs to current user
    if booking.user_id != current_user.id and not current_user.can(
        Permission.MANAGE_BOOKINGS
    ):
        flash("Unauthorized access", "danger")
        return redirect(url_for("booking.my_bookings"))
    
    # Calculate time elapsed since booking creation
    time_elapsed = datetime.utcnow() - booking.created_at
    if time_elapsed.total_seconds() > 600:  # 10 minutes = 600 seconds
        # Booking has expired
        if booking.status == "pending" and booking.payment_status == "pending":
            # Cancel the booking if it's still pending
            booking.cancel()
            db.session.commit()
            flash("Booking has expired. Please create a new booking.", "warning")
        return redirect(url_for("booking.my_bookings"))

    # Calculate remaining time for client-side timer
    remaining_seconds = max(600 - int(time_elapsed.total_seconds()), 0)
    
    # Verify booking is pending payment
    if booking.status != "pending" or booking.payment_status != "pending":
        flash("Invalid booking status", "danger")
        return redirect(url_for("booking.my_bookings"))

    form = PaymentForm()
    if form.validate_on_submit():
        try:
            # Process payment
            payment_result = PaymentService.process_payment(
                amount=booking.total_amount,
                card_number=form.card_number.data,
                expiry=form.expiry.data,
                cvv=form.cvv.data,
                booking_id=booking.id,
            )

            if payment_result["status"] == "success":
                # Complete booking with payment
                BookingService.complete_payment(booking.id, payment_result)
                flash(
                    "Payment successful! Your tickets have been issued and sent to your email.",
                    "success",
                )
                return redirect(url_for("booking.my_bookings"))
            else:
                flash("Payment processing failed. Please try again.", "danger")

        except Exception as e:
            logger.error(f"Payment failed for booking {booking_number}: {str(e)}")
            flash("Payment processing failed. Please try again.", "danger")

    return render_template(
        "booking/checkout.html", 
        booking=booking, 
        form=form,
        remaining_seconds=remaining_seconds
    )


@booking_bp.route("/cancel/<string:booking_number>", methods=["POST"])
@permission_required(Permission.CANCEL_TICKET)
def cancel_booking(booking_number):
    booking = Booking.query.filter_by(booking_number=booking_number).first_or_404()

    # Verify booking belongs to current user or user has manage bookings permission
    if booking.user_id != current_user.id and not current_user.can(
        Permission.MANAGE_BOOKINGS
    ):
        flash("Unauthorized access", "danger")
        return redirect(url_for("booking.my_bookings"))

    try:
        booking = BookingService.cancel_booking(booking_number, current_user.id)
        flash("Booking cancelled successfully", "success")
    except ValueError as e:
        error_message = (
            f"Failed to cancel booking ID {booking_number} for user ID {current_user.id} "
            f"({getattr(current_user, 'username', 'N/A')}): {str(e)}"
        )
        logger.error(error_message)
        flash(error_message, "danger")
    return redirect(url_for("booking.my_bookings", booking_number=booking_number))


@booking_bp.route("/all")
@permission_required(Permission.VIEW_ALL_BOOKINGS)
def all_bookings():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template("booking/all_bookings.html", bookings=bookings)
