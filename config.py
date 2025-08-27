import os
import logging
import sys
import ssl

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
    if database_uri and database_uri.startswith('postgres'):
        # Если указана POSTGRES_SCHEMA, добавляем настройку search_path
        if ON_RENDER:
            schema = os.environ.get("POSTGRES_SCHEMA", "render_schema")
            logger.info(f"Running on Render.com, base schema: {schema}")
        else:
            schema = os.environ.get("POSTGRES_SCHEMA", "rozoom_schema")
            logger.info(f"Running locally, base schema: {schema}")

        client_schema = os.environ.get('POSTGRES_SCHEMA_CLIENTS')
        if client_schema and client_schema != schema:
            combined_search_path = f"{client_schema},{schema}"
            logger.info(f"Additional client requests schema detected: {client_schema}")
        else:
            combined_search_path = schema
        
        # Нормализуем префикс
        if database_uri.startswith('postgres://'):
            database_uri = database_uri.replace('postgres://', 'postgresql://', 1)

        # Добавляем драйвер pg8000 если psycopg2 отсутствует
        try:
            import psycopg2  # noqa: F401
            driver_prefix = 'postgresql://'
        except Exception:
            driver_prefix = 'postgresql+pg8000://'
            if database_uri.startswith('postgresql://'):
                database_uri = database_uri.replace('postgresql://', driver_prefix, 1)

        # Добавляем search_path через параметр options если ещё не указан
        # Для psycopg2 можно использовать options=, для pg8000 — установим через событие connect
        if '+pg8000://' in database_uri:
            logger.info("Using pg8000: will set search_path via engine event, not URI options")
        else:
            if 'options=' not in database_uri:
                sep = '&' if '?' in database_uri else '?'
                database_uri = f"{database_uri}{sep}options=-c%20search_path%3D{combined_search_path}"

        SQLALCHEMY_DATABASE_URI = database_uri
        CLIENT_REQUESTS_SCHEMA = client_schema
        DB_SEARCH_PATH = combined_search_path
        logger.info(f"Configured PostgreSQL search_path: {combined_search_path}")
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_size': 5,
            'max_overflow': 10,
            'connect_args': {}
        }
        if '+pg8000://' in database_uri:
            try:
                SSL_CONTEXT = ssl.create_default_context()
                SQLALCHEMY_ENGINE_OPTIONS['connect_args']['ssl_context'] = SSL_CONTEXT
            except Exception as e:
                logger.warning(f"Failed to create SSL context: {e}")
    else:
        # Fallback на SQLite для локальной разработки
        SQLALCHEMY_DATABASE_URI = database_uri or "sqlite:///instance/clients.db"
        logger.info("Using SQLite database for development")
        SQLALCHEMY_ENGINE_OPTIONS = {}
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Другие настройки приложения
    SUPPORTED_LANGUAGES = ['uk', 'en', 'de']
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    USE_CHAT_COMPLETION = os.environ.get("USE_CHAT_COMPLETION", "true").lower() == "true"
