from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length

class BookingForm(FlaskForm):
    quantity = IntegerField('Number of Tickets', validators=[
        DataRequired(),
        NumberRange(min=1, message='Please select at least 1 ticket')
    ])
    submit = SubmitField('Book Now')

class PaymentForm(FlaskForm):
    card_holder = StringField('Card Holder Name', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    card_number = StringField('Card Number', validators=[
        DataRequired(),
        Length(min=16, max=16, message='Please enter a valid card number')
    ])
    expiry = StringField('Expiry Date', validators=[
        DataRequired(),
        Length(min=5, max=5, message='Please enter a valid expiry date (MM/YY)')
    ])
    cvv = StringField('CVV', validators=[
        DataRequired(),
        Length(min=3, max=4, message='Please enter a valid CVV')
    ])
    submit = SubmitField('Pay Now') 