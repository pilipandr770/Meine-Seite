import os
import logging
import sys

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    # Основные настройки
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key")
    ENVIRONMENT = os.environ.get("FLASK_ENV", "development")
    
    # Определяем, запущены ли мы на Render.com
    ON_RENDER = "RENDER" in os.environ
    
    # Настройки базы данных
    # Проверяем сначала DATABASE_URI, затем DATABASE_URL (на случай если Render.com использует это имя)
    database_uri = os.environ.get("DATABASE_URI") or os.environ.get("DATABASE_URL")
    
    # Если есть переменная DATABASE_URI или DATABASE_URL и она PostgreSQL, используем её
    if database_uri and database_uri.startswith('postgresql'):
        # Если указана POSTGRES_SCHEMA, добавляем настройку search_path
        if ON_RENDER:
            # На Render.com используем специальную схему
            schema = os.environ.get("POSTGRES_SCHEMA", "render_schema")
            logger.info(f"Running on Render.com, using schema: {schema}")
        else:
            schema = os.environ.get("POSTGRES_SCHEMA", "rozoom_schema")
            logger.info(f"Running locally, using schema: {schema}")
        
        # Для PostgreSQL добавляем параметры для схемы, если они не указаны в URI
        if "options=" not in database_uri:
            SQLALCHEMY_DATABASE_URI = f"{database_uri}?options=-c%20search_path%3D{schema}"
        else:
            SQLALCHEMY_DATABASE_URI = database_uri
        logger.info(f"Using PostgreSQL database with schema: {schema}")
    else:
        # Fallback на SQLite для локальной разработки
        SQLALCHEMY_DATABASE_URI = database_uri or "sqlite:///instance/clients.db"
        logger.info("Using SQLite database for development")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Другие настройки приложения
    SUPPORTED_LANGUAGES = ['uk', 'en', 'de']
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    USE_CHAT_COMPLETION = os.environ.get("USE_CHAT_COMPLETION", "true").lower() == "true"
