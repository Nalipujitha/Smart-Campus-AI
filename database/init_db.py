import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# pyrefly: ignore [missing-import]
from flask import Flask
from backend.config import Config
from backend.extensions import db
import backend.models # Ensure all models are imported

def init_database(app=None):
    """
    Initializes the SQLite database tables.
    """
    if app is None:
        app = Flask(__name__)
        app.config.from_object(Config)
        db.init_app(app)

    with app.app_context():
        # Ensure database directory exists
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if db_path != ':memory:':
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

        db.create_all()
        print("Database schema successfully created/verified at:", app.config['SQLALCHEMY_DATABASE_URI'])

if __name__ == '__main__':
    init_database()
