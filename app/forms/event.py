from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, DateField, SubmitField, SelectField
from wtforms.validators import DataRequired, NumberRange, Optional

class EventForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    venue = StringField('Venue', validators=[DataRequired()])
    event_date = DateField('Event Date', validators=[DataRequired()])
    total_tickets = IntegerField('Total Tickets', validators=[DataRequired(), NumberRange(min=1)])
    price = IntegerField('Price', validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField('Category', choices=[('Music', 'Music'), ('Art', 'Art'), ('Sports', 'Sports'), ('Technology', 'Technology'), ('Other', 'Other')], validators=[DataRequired()])
    image_url = StringField('Image URL', validators=[Optional()])
    submit = SubmitField('Save')