import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
    
    # Получаем DATABASE_URL (приоритет) или DATABASE_URI (для обратной совместимости)
    database_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_URI", "sqlite:///instance/clients.db")
    
    # Для PostgreSQL можно указать схему через engine options; не модифицируем URI напрямую
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_ENGINE_OPTIONS = {}
    if database_url.startswith("postgresql://"):
        schema = os.getenv("POSTGRES_SCHEMA", "rozoom_schema")
        # Используем опцию connect_args для задания search_path
        SQLALCHEMY_ENGINE_OPTIONS = {'connect_args': {'options': f'-c search_path={schema}'}}
        
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
    
    # Stripe платежи
    STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    # Optional test Price ID to use when product-specific price_id is not set
    STRIPE_TEST_PRICE_ID = os.getenv("STRIPE_TEST_PRICE_ID")
    
# Использование класса Config
config = Config()
