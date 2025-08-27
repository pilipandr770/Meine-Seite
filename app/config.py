import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
    
    # Получаем DATABASE_URL (приоритет) или DATABASE_URI (для обратной совместимости)
    database_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_URI", "sqlite:///instance/clients.db")
    
    # Для PostgreSQL добавляем параметры схемы
    if database_url.startswith("postgresql://"):
        schema = os.getenv("POSTGRES_SCHEMA", "rozoom_schema")
        SQLALCHEMY_DATABASE_URI = f"{database_url}?options=-c search_path={schema}"
    else:
        SQLALCHEMY_DATABASE_URI = database_url
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SUPPORTED_LANGUAGES = ["uk", "en", "de"]
    
    # Режим работы (development/production)
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # Telegram настройки
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # OpenAI настройки
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    USE_CHAT_COMPLETION = os.getenv("USE_CHAT_COMPLETION", "true").lower() == "true"
    
    # Google Calendar API
    CALENDAR_API_KEY = os.getenv("CALENDAR_API_KEY")
    
# Использование класса Config
config = Config()
