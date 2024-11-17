# models/ecommerce_models.py

from datetime import datetime
from extensions import db  # Make sure to import db from your extensions
from models.admin_models import AdminUser
from models.admin_models import Role

# Association table for many-to-many relationship between Promotion and Product
promotion_products = db.Table('promotion_products',
    db.Column('promotion_id', db.Integer, db.ForeignKey('promotions.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True)
)

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategory.id'), nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    specifications = db.Column(db.Text, nullable=True)
    discount = db.Column(db.Float, default=0.0)
    promotions = db.relationship('Promotion', secondary=promotion_products, back_populates='products')
    inventory_records = db.relationship('Inventory', backref='product', lazy=True)

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    subcategories = db.relationship('Subcategory', backref='category', lazy=True)

class Subcategory(db.Model):
    __tablename__ = 'subcategory'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    products = db.relationship('Product', backref='subcategory', lazy=True)

class Warehouse(db.Model):
    __tablename__ = 'warehouse'
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)
    inventories = db.relationship('Inventory', backref='warehouse', lazy=True)

class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    membership_tier = db.Column(db.String(20), nullable=False, default='Normal')  # 'Normal', 'Premium', 'Gold'
    orders = db.relationship('Order', backref='customer', lazy=True)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    tracking_number = db.Column(db.String(50), nullable=True)
    returns = db.relationship('Return', back_populates='order')

class Return(db.Model):
    __tablename__ = 'returns'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=True)
    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    issued_refunds = db.Column(db.Boolean, default=False)
    offered_replacement = db.Column(db.Boolean, default=False)
    return_date = db.Column(db.DateTime, default=datetime.utcnow)
    order = db.relationship('Order', back_populates='returns')
class Promotion(db.Model):
    __tablename__ = 'promotions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    discount_percent = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    user_tier = db.Column(db.String(20), nullable=True)  # 'Normal', 'Premium', 'Gold' or None for all tiers
    products = db.relationship('Product', secondary=promotion_products, back_populates='promotions')

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('admin_user.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    admin_user = db.relationship('AdminUser', backref='activity_logs')

roles_permissions = db.Table(
    'roles_permissions',
    db.metadata,
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True),
    extend_existing=True  # This ensures redefinition is allowed
)





