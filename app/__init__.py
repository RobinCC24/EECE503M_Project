from flask import Flask, app, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect
#from flask_login import LoginManager
from config import Config
from flask_migrate import Migrate

db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
#login_manager = LoginManager()
#login_manager.login_view = 'login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    csrf = CSRFProtect(app)
    
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    #login_manager.init_app(app)
    
    from .routes.inventory import inventory_bp
    from .routes.orders import orders_bp
    from .routes.products import products_bp
    from .routes.customers import customers_bp

    app.register_blueprint(inventory_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(customers_bp)

    #app.register_blueprint(inventory_bp, url_prefix='/inventory')
    #app.register_blueprint(orders_bp, url_prefix='/orders')
    #app.register_blueprint(products_bp, url_prefix='/products')
    #app.register_blueprint(customers_bp, url_prefix='/customers')

    @app.route('/')
    def index():
        return 'Welcome!'

    return app
