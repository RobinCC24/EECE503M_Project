from app import create_app
from extensions import db
from models.admin_models import AdminUser, Role, Permission

app = create_app()

with app.app_context():
    # Get or create the Admin Role
    admin_role = Role.query.filter_by(name="Admin").first()
    if not admin_role:
        admin_role = Role(name="Admin")
        db.session.add(admin_role)
        db.session.commit()

    # Add all permissions to the Admin Role
    permissions = [
        "manage_products",
        "manage_inventory",
        "manage_orders",
        "manage_customers",
        "manage_promotions",
        "view_roles",
        "delete_users",
        "view_activity_logs",
    ]
    for perm_name in permissions:
        permission = Permission.query.filter_by(name=perm_name).first()
        if not permission:
            permission = Permission(name=perm_name)
            db.session.add(permission)
            db.session.commit()
        if permission not in admin_role.permissions:
            admin_role.permissions.append(permission)
    db.session.commit()

    print("Permissions successfully granted to Admin role.")
