from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length


class BookingForm(FlaskForm):
    quantity = IntegerField("Number of Tickets", default=1)
    submit = SubmitField("Book Now")

    def __init__(self, max_tickets=10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quantity.validators = [
            DataRequired(),
            NumberRange(min=1, max=max_tickets, message=f"You can book between 1 and {max_tickets} tickets"),
        ]

class PaymentForm(FlaskForm):
    card_holder = StringField(
        "Card Holder Name", validators=[DataRequired(), Length(min=2, max=100)]
    )
    card_number = StringField(
        "Card Number",
        validators=[
            DataRequired(),
            Length(min=16, max=16, message="Please enter a valid card number"),
        ],
    )
    expiry = StringField(
        "Expiry Date",
        validators=[
            DataRequired(),
            Length(min=5, max=5, message="Please enter a valid expiry date (MM/YY)"),
        ],
    )
    cvv = StringField(
        "CVV",
        validators=[
            DataRequired(),
            Length(min=3, max=4, message="Please enter a valid CVV"),
        ],
    )
    submit = SubmitField("Pay Now")
