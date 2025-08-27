import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key")
    
    # Получаем DATABASE_URI из переменной окружения или используем значение по умолчанию
    database_uri = os.environ.get("DATABASE_URI")
    
    # Если переменная DATABASE_URI установлена, используем ее
    if database_uri and database_uri.startswith('postgresql'):
        # Добавляем параметры для схемы, если используется PostgreSQL
        if '?' in database_uri:
            SQLALCHEMY_DATABASE_URI = f"{database_uri}&options=-c%20search_path=rozoom_schema"
        else:
            SQLALCHEMY_DATABASE_URI = f"{database_uri}?options=-c%20search_path=rozoom_schema"
    else:
        # Fallback на SQLite для локальной разработки
        SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///clients.db")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SUPPORTED_LANGUAGES = ['uk', 'en', 'de']
