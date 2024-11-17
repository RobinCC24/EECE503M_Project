# admin_forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SelectMultipleField, validators, SubmitField, DecimalField, IntegerField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange
from flask_wtf.file import FileAllowed
from wtforms.fields import DateField

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    subcategory_id = SelectField('Subcategory', coerce=int, validators=[DataRequired()])
    specifications = TextAreaField('Specifications', validators=[Optional()])
    discount = DecimalField('Discount', validators=[Optional(), NumberRange(min=0, max=100)])
    image = FileField('Product Image', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')])
    submit = SubmitField('Submit')

class InventoryForm(FlaskForm):
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Update Inventory')

class OrderForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled')
    ], validators=[DataRequired()])
    submit = SubmitField('Update Order')

class ReturnForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Processed', 'Processed')
    ], validators=[DataRequired()])
    submit = SubmitField('Update Return')

class BulkUploadForm(FlaskForm):
    file = FileField('CSV File', validators=[DataRequired(), FileAllowed(['csv'], 'CSV files only!')])
    submit = SubmitField('Upload')

class PromotionForm(FlaskForm):
    name = StringField('Promotion Name', validators=[DataRequired(), Length(max=100)])
    discount_percent = DecimalField('Discount Percent', validators=[DataRequired(), NumberRange(min=0, max=100)])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    user_tier = SelectField('User Tier', choices=[
        ('', 'All'),
        ('Normal', 'Normal'),
        ('Premium', 'Premium'),
        ('Gold', 'Gold')
    ], validators=[Optional()])
    product_ids = SelectMultipleField('Products', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class EditUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role_id = SelectField('Role', coerce=int)  # Role will be a dropdown
    password = PasswordField('Password', validators=[Optional()])  # Optional: only set if provided