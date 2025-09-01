"""Admin forms for RoZoom website"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, BooleanField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from flask_wtf.file import FileField, FileAllowed

class CategoryForm(FlaskForm):
    """Form for creating and editing categories"""
    name = StringField('Name', validators=[
        DataRequired(), 
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    description = TextAreaField('Description', validators=[
        Optional(), 
        Length(max=500, message='Description cannot exceed 500 characters')
    ])
    image = FileField('Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')
    ])

class ProductForm(FlaskForm):
    """Form for creating and editing products"""
    name = StringField('Name', validators=[
        DataRequired(), 
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    short_description = TextAreaField('Short Description', validators=[
        DataRequired(), 
        Length(max=200, message='Short description cannot exceed 200 characters')
    ])
    description = TextAreaField('Full Description', validators=[
        DataRequired(), 
        Length(max=2000, message='Description cannot exceed 2000 characters')
    ])
    price = FloatField('Price', validators=[
        DataRequired(), 
        NumberRange(min=0, message='Price must be positive')
    ])
    sale_price = FloatField('Sale Price', validators=[
        Optional(), 
        NumberRange(min=0, message='Sale price must be positive')
    ])
    stock = IntegerField('Stock', validators=[
        DataRequired(), 
        NumberRange(min=0, message='Stock must be positive')
    ])
    is_active = BooleanField('Active', default=True)
    is_featured = BooleanField('Featured', default=False)
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    image = FileField('Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')
    ])
    duration = IntegerField('Duration (minutes)', validators=[
        Optional(), 
        NumberRange(min=0, message='Duration must be positive')
    ])
    is_virtual = BooleanField('Virtual Product', default=True, description='Check for digital/virtual products like consultation hours')

class OrderStatusForm(FlaskForm):
    """Form for updating order status"""
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded')
    ], validators=[DataRequired()])

class UserForm(FlaskForm):
    """Form for admin editing users"""
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=3, max=50, message='Username must be between 3 and 50 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Length(min=6, max=100, message='Email must be between 6 and 100 characters')
    ])
    is_admin = BooleanField('Admin', default=False)
    is_active = BooleanField('Active', default=True)

class ProjectForm(FlaskForm):
    """Form for creating and editing projects"""
    name = StringField('Project Name', validators=[
        DataRequired(),
        Length(min=2, max=200, message='Project name must be between 2 and 200 characters')
    ])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=1000, message='Description cannot exceed 1000 characters')
    ])
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    client_id = SelectField('Client', coerce=int, validators=[Optional()], default=None)
    deadline = DateField('Deadline', validators=[Optional()], format='%Y-%m-%d')

class EditProjectForm(FlaskForm):
    """Form for editing projects"""
    name = StringField('Project Name', validators=[
        DataRequired(),
        Length(min=2, max=200, message='Project name must be between 2 and 200 characters')
    ])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=1000, message='Description cannot exceed 1000 characters')
    ])
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold')
    ], validators=[DataRequired()])
    deadline = DateField('Deadline', validators=[Optional()], format='%Y-%m-%d')
