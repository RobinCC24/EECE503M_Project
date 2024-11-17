# init_db.py

from app import create_app
from extensions import db
from models.ecommerce_models import (
    AdminUser, Role, Permission, Product, Category, Subcategory, Warehouse,
    Customer, Order, Inventory, Return, Promotion
)
from werkzeug.security import generate_password_hash

def init_db():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Database tables created.")

        # Create default roles and permissions
        create_permissions()
        create_roles()
        create_admin_user()

        # Optionally, seed initial data
        # seed_data()

def create_permissions():
    permissions = [
        'manage_products', 'manage_inventory', 'manage_orders',
        'manage_returns', 'manage_promotions', 'manage_customers',
        'view_activity_logs', 'manage_roles', 'manage_users'
    ]
    for perm_name in permissions:
        perm = Permission(name=perm_name)
        db.session.add(perm)
    db.session.commit()
    print("Permissions created.")

def create_roles():
    # Create roles and assign permissions
    permissions = Permission.query.all()

    # SuperAdmin role
    superadmin_role = Role(name='SuperAdmin')
    superadmin_role.permissions = permissions
    db.session.add(superadmin_role)

    # Admin role
    admin_permissions = [perm for perm in permissions if perm.name != 'manage_roles']
    admin_role = Role(name='Admin')
    admin_role.permissions = admin_permissions
    db.session.add(admin_role)

    db.session.commit()
    print("Roles created.")

def create_admin_user():
    # Create a default admin user
    if not AdminUser.query.filter_by(username='admin').first():
        password_hash = generate_password_hash('admin123')  # Replace with a secure password
        admin_user = AdminUser(
            username='admin',
            email='admin@example.com',
            password_hash=password_hash,
            role=Role.query.filter_by(name='SuperAdmin').first()
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created with username 'admin' and password 'admin123'.")
    else:
        print("Admin user already exists.")

def seed_data():
    # Optionally, add categories, subcategories, products, etc.
    # Example:
    category_names = ['Guitars', 'Keyboards', 'Drums', 'Violins', 'Audio Equipment']
    for name in category_names:
        category = Category(name=name)
        db.session.add(category)
    db.session.commit()
    print("Categories seeded.")

if __name__ == '__main__':
    init_db()
