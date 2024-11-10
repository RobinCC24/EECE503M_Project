from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes.orders import orders_bp
    from app.routes.users import customers_bp

    app.register_blueprint(orders_bp, url_prefix='/api')
    app.register_blueprint(customers_bp, url_prefix='/api')

    return app
