import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Load the TMDB API key from environment variables
    TMDB_API_KEY = os.getenv('TMDB_API')

    # Load the secret key from environment variables
    SECRET_KEY = os.getenv('SECRET_KEY')

    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///cinelog.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False