from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user
from app.models.booking import Booking
from app.models.event import Event
from app.models.ticket import Ticket
from app.services.booking_service import BookingService
from app.forms.booking import BookingForm, PaymentForm
from app.utils.database import db, commit_changes
from app.utils.decorators import permission_required
from app.utils.permissions import Permission

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/my-bookings')
@permission_required(Permission.VIEW_OWN_BOOKINGS)
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('booking/my_bookings.html', bookings=bookings)

@booking_bp.route('/create/<int:event_id>', methods=['POST'])
@permission_required(Permission.BOOK_TICKET)
def create_booking(event_id):
    form = BookingForm()
    if form.validate_on_submit():
        try:
            result = BookingService.create_booking(
                user_id=current_user.id,
                event_id=event_id,
                quantity=form.quantity.data
            )
            return redirect(url_for('booking.checkout', booking_id=result['booking']['id']))
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('events.detail', event_id=event_id))
    return redirect(url_for('events.detail', event_id=event_id))

@booking_bp.route('/checkout/<int:booking_id>', methods=['GET', 'POST'])
@permission_required(Permission.BOOK_TICKET)
def checkout(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Verify booking belongs to current user
    if booking.user_id != current_user.id and not current_user.can(Permission.MANAGE_BOOKINGS):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('booking.my_bookings'))
    
    # Verify booking is pending payment
    if booking.status != 'pending' or booking.payment_status != 'pending':
        flash('Invalid booking status', 'danger')
        return redirect(url_for('booking.my_bookings'))

    form = PaymentForm()
    if form.validate_on_submit():
        try:
            # Process payment and update booking
            booking.mark_as_paid('DUMMY_PAYMENT_ID')  # In a real app, use actual payment processing
            booking.confirm()
            
            # Create tickets
            for _ in range(booking.quantity):
                ticket = Ticket(event_id=booking.event_id, booking_id=booking.id)
                db.session.add(ticket)
            
            # Update event available tickets
            event = Event.query.get(booking.event_id)
            event.update_available_tickets(booking.quantity)
            
            commit_changes()
            
            flash('Payment successful! Your tickets have been issued.', 'success')
            return redirect(url_for('booking.my_bookings'))
        except Exception as e:
            flash('Payment processing failed. Please try again.', 'danger')
    
    return render_template('booking/checkout.html', booking=booking, form=form)

@booking_bp.route('/cancel/<int:booking_id>', methods=['POST'])
@permission_required(Permission.CANCEL_TICKET)
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Verify booking belongs to current user or user has manage bookings permission
    if booking.user_id != current_user.id and not current_user.can(Permission.MANAGE_BOOKINGS):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('booking.my_bookings'))
        
    try:
        booking = BookingService.cancel_booking(booking_id, current_user.id)
        flash('Booking cancelled successfully', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('booking.my_bookings'))

@booking_bp.route('/all')
@permission_required(Permission.VIEW_ALL_BOOKINGS)
def all_bookings():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('booking/all_bookings.html', bookings=bookings) 