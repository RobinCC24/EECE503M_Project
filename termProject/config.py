import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mysecretkey'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'  # SQLite for local testing
    SQLALCHEMY_TRACK_MODIFICATIONS = False
