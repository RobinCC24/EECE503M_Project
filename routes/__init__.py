from .customers import customers_bp
from .admin_routes import admin_bp
from .order_routes import order_bp
from .product_routes import product_bp
from .inventory import inventory_bp

__all__ = [
    "customers_bp",
    "admin_bp",
    "order_bp",
    "product_bp",
    "inventory_bp",
]
