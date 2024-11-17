from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Import models here
from .admin_models import AdminUser, Role, Permission
from .ecommerce_models import Product, Category, Subcategory, Warehouse, Inventory, Customer, Order

__all__ = [
    "db",
    "AdminUser", "Role", "Permission",
    "Product", "Category", "Subcategory", "Warehouse", "Inventory", "Customer", "Order"
]
