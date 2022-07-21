"""Flask configuration"""
from os import environ
from dotenv import load_dotenv, dotenv_values
from pathlib import Path

load_dotenv(f"{Path(__file__).parent / '.env'}", verbose=True)

SECRET_KEY = environ.get('SECRET_KEY')
FLASK_ENV = "development"
DEBUG = True
TESTING = False
SESSION_SCRATCH_DIR = '/tmp'
UPLOAD_FOLDER = '/tmp/bayestourney_uploads'
Path(SESSION_SCRATCH_DIR).mkdir(parents=True, exist_ok=True)
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

# Email configuration
MAIL_SERVER = environ.get('MAIL_SERVER')
MAIL_PORT = int(environ.get('MAIL_PORT') or 25)
MAIL_USE_TLS = environ.get('MAIL_USE_TLS') is not None
MAIL_USERNAME = environ.get('MAIL_USERNAME')
MAIL_PASSWORD = environ.get('MAIL_PASSWORD')
ADMINS = environ.get('ADMINS')
