import os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Load the TMDB API key from environment variables
    TMDB_API_KEY = os.getenv('TMDB_API')
    SECRET_KEY = os.getenv('SECRET_KEY')

    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///cinefiles.db'
    # Disable track modifications to save resources
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # This ensures that cookies are only sent over HTTPS in production
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    # This prevents Javascript access which prevents XSS attacks
    SESSION_COOKIE_HTTPONLY = True
    # Thius prevents against Cross site request forgery(CSRF) attacks 
    SESSION_COOKIE_SAMESITE = 'Strict'
    # 15 minute session lifetime for better security
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=15)
