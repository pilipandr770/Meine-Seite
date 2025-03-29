import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///clients.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SUPPORTED_LANGUAGES = ['uk', 'en', 'de']
