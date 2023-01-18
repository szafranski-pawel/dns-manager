import os
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import InputRequired, Email, EqualTo, Length, ValidationError


class SignupForm(FlaskForm):
    """User Sign-up Form."""
    name = StringField(
        'Name',
        validators=[InputRequired()]
    )
    email = StringField(
        'Email',
        validators=[
            InputRequired(),
            Email(message='Enter a valid email.'),
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(),
            Length(min=8, max=64, message='Select a stronger password.')
        ]
    )
    confirm = PasswordField(
        'Confirm Your Password',
        validators=[
            InputRequired(),
            EqualTo('password', message='Passwords must match.')
        ]
    )
    domain = StringField(
        'Subdomain',
        validators=[
            InputRequired(),
            Length(min=1, max=64)
        ]
    )
    invite_code = StringField(
        'Invite Code',
        validators=[
            InputRequired()
        ]
    )
    def validate_invite_code(form, field):
        if field.data != os.environ['INVITE_CODE']:
            raise ValidationError('Provide correct invite code')

    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    """User Log-in Form."""
    email = StringField(
        'Email',
        validators=[
            InputRequired(),
            Email(message='Enter a valid email.')
        ]
    )
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Log In')