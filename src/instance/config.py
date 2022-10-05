"""Flask configuration"""
import os
from dotenv import load_dotenv, dotenv_values
from pathlib import Path

basepath = Path(__file__).parent.parent.parent.resolve()

load_dotenv(f"{Path(__file__).parent / '.env'}", verbose=True)

SECRET_KEY = os.environ.get('SECRET_KEY')
FLASK_ENV = "development"
DEBUG = True
TESTING = False
SESSION_SCRATCH_DIR = '/tmp'
UPLOAD_FOLDER = '/tmp/bayestourney_uploads'
Path(SESSION_SCRATCH_DIR).mkdir(parents=True, exist_ok=True)
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

# SQLAlchemy config
SQLALCHEMY_DATABASE_URI = (os.environ.get('DATABASE_URL')
                           or f"sqlite:///{basepath / 'data' / 'mydb.db'}")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Email configuration
MAIL_SERVER = os.environ.get('MAIL_SERVER')
MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
ADMIN_MAIL_SENDER = os.environ.get('ADMIN_MAIL_SENDER')
