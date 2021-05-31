"""Flask configuration"""
from os import environ
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / '.env')

FLASK_ENV = "development"
SECRET_KEY = environ.get('SECRET_KEY')

