from datetime import datetime
from . import db

# Existing models from your project
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategory.id', name='fk1'), nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    specifications = db.Column(db.Text, nullable=True)
    discount = db.Column(db.Float, default=0.0)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    subcategories = db.relationship('Subcategory', backref='category', lazy=True)


class Subcategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id', name='fk2'), nullable=False)
    products = db.relationship('Product', backref='subcategory', lazy=True)


class Warehouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)
    inventories = db.relationship('Inventory', backref='warehouse', lazy=True)


class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', name='fk3', ondelete='CASCADE'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id', name='fk4'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    product = db.relationship('Product', backref=db.backref('inventory_records', lazy=True))


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    membership_tier = db.Column(db.String(20), nullable=False, default='Standard')
    orders = db.relationship('Order', backref='customer', lazy=True)


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', name='fk5'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    tracking_number = db.Column(db.String(50), nullable=True)


class Return(db.Model):
    __tablename__ = 'returns'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', name='fk6'), nullable=False)
    product_id = db.Column(db.Integer, nullable=True)
    reason = db.Column(db.String, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    issued_refunds = db.Column(db.Boolean, default=False)
    offered_replacement = db.Column(db.Boolean, default=False)
    return_date = db.Column(db.DateTime, default=datetime.utcnow)
