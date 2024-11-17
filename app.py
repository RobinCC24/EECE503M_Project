from flask import Flask, redirect, url_for
from config import DevelopmentConfig  # Update to ProductionConfig in production
from extensions import db, login_manager, csrf
from models.ecommerce_models import AdminUser
from routes import admin_bp, customers_bp, order_bp, product_bp, inventory_bp
from flask_migrate import Migrate

# Initialize Flask-Migrate
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)  # Flask-Migrate for database migrations
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register blueprints with URL prefixes for better organization
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(order_bp, url_prefix='/orders')
    app.register_blueprint(product_bp, url_prefix='/products')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')

    # Setup login manager
    login_manager.login_view = 'admin.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return AdminUser.query.get(int(user_id))

    # Define a root route
    @app.route('/')
    def home():
        return redirect(url_for('admin.login'))  # Redirect root to admin login

    return app

# Debugging URL Map and Running the Application
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("URL Map:")
        print(app.url_map)  # Prints all available routes
    app.run(debug=True)
