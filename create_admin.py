from werkzeug.security import generate_password_hash
from app import create_app
from extensions import db
from models.admin_models import AdminUser, Role

app = create_app()

with app.app_context():
    # Create the Admin Role
    admin_role = Role(name="Admin")
    db.session.add(admin_role)
    db.session.commit()

    # Create the Admin User
    admin_user = AdminUser(
        username="admin",
        email="admin@example.com",
        password_hash=generate_password_hash("password123"),  # Replace with a secure password
        role=admin_role
    )
    db.session.add(admin_user)
    db.session.commit()

    print("Admin user created successfully!")
