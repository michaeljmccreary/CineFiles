import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Load the TMDB API key from environment variables
    TMDB_API_KEY = os.getenv('TMDB_API')

# Hardocoded secret key for session management - Bad security makes app vulnerable to session attacks
# Secret key Generated using https://secretkeygen.vercel.app/ - hard coding into the app on purpose
    secret_key = "46bcef3f322dec211634eb9d0f497056"

    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///cinefiles.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False