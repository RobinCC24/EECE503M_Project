from flask import Flask, app, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
#from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
#login_manager = LoginManager()
#login_manager.login_view = 'login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    bcrypt.init_app(app)
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
        return render_template('index.html')

    @app.route('/products.html')
    def add_product_page():
        return render_template('products.html')

    return app
