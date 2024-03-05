"""Forms for Plant App."""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, PasswordField
from wtforms.validators import InputRequired, URL, Optional, Email, Length


class PlantSearchForm(FlaskForm):
    """Form for searching for a plant."""

    term = StringField(
        "Search Plants",
        validators=[InputRequired(), Length(max=30)],
    )


class SignupForm(FlaskForm):
    """Form for registering/adding new user."""

    username = StringField(
        "Username",
        validators=[InputRequired(), Length(max=30)]
    )

    first_name = StringField(
        "First Name",
        validators=[InputRequired(), Length(max=30)]
    )

    last_name = StringField(
        "Last Name",
        validators=[InputRequired(), Length(max=30)]
    )

    bio = TextAreaField(
        "Bio",
        validators=[Optional()]
    )

    email = StringField(
        "Email",
        validators=[InputRequired(), Email(), Length(max=50)]
    )

    password = PasswordField(
        "Password",
        validators=[InputRequired(), Length(min=6, max=50)]
    )

    image_url = StringField(
        "Image URL",
        validators=[Optional(), URL(), Length(max=255)]
    )


class ProfileEditForm(FlaskForm):
    """Form for editing user profile."""

    first_name = StringField(
        "First Name",
        validators=[InputRequired(), Length(max=30)]
    )

    last_name = StringField(
        "Last Name",
        validators=[InputRequired(), Length(max=30)]
    )

    description = TextAreaField(
        "Description",
        validators=[Optional()]
    )

    email = StringField(
        "Email",
        validators=[InputRequired(), Email(), Length(max=50)]
    )

    image_url = StringField(
        "Image URL",
        validators=[Optional(), URL(), Length(max=255)]
    )


class LoginForm(FlaskForm):
    """Login form; takes in username and password."""

    username = StringField(
        "Username",
        validators=[InputRequired(), Length(max=30)]
    )

    password = PasswordField(
        "Password",
        validators=[InputRequired(), Length(max=50)]
    )

class CSRFProtection(FlaskForm):
    """CSRFProtection form, intentionally has no fields."""
