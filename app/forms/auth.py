"""Authentication forms for RoZoom website"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
import re

class LoginForm(FlaskForm):
    """Login form"""
    email = EmailField('Email', validators=[
        DataRequired(), 
        Email(message='Invalid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired()
    ])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    """Registration form"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=50, message='Username must be between 3 and 50 characters')
    ])
    email = EmailField('Email', validators=[
        DataRequired(),
        Email(message='Invalid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')
    
    def validate_password(self, password):
        """Custom validator for password complexity"""
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password.data):
            raise ValidationError('Password must contain at least one uppercase letter')
            
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password.data):
            raise ValidationError('Password must contain at least one lowercase letter')
            
        # Check for at least one number
        if not re.search(r'\d', password.data):
            raise ValidationError('Password must contain at least one number')
            
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password.data):
            raise ValidationError('Password must contain at least one special character')

class PasswordResetForm(FlaskForm):
    """Password reset request form"""
    email = EmailField('Email', validators=[
        DataRequired(),
        Email(message='Invalid email address')
    ])
    submit = SubmitField('Request Password Reset')

class PasswordChangeForm(FlaskForm):
    """Form for changing password after reset"""
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')
    
    def validate_password(self, password):
        """Custom validator for password complexity"""
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password.data):
            raise ValidationError('Password must contain at least one uppercase letter')
            
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password.data):
            raise ValidationError('Password must contain at least one lowercase letter')
            
        # Check for at least one number
        if not re.search(r'\d', password.data):
            raise ValidationError('Password must contain at least one number')
            
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password.data):
            raise ValidationError('Password must contain at least one special character')
