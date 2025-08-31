# db_adapter.py
from sqlalchemy import create_engine, text
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_db_schema():
    """
    Инициализирует схему БД при запуске приложения
    """
    try:
        # Получаем URL базы данных из конфигурации
        db_url = current_app.config['SQLALCHEMY_DATABASE_URI']
        schema_name = os.environ.get('POSTGRES_SCHEMA', 'rozoom_schema')

        # Skip schema creation on SQLite
        if db_url.startswith('sqlite'):
            logger.info('SQLite detected — skipping Postgres schema initialization in db_adapter.')
            return True

        # Создаем движок SQLAlchemy
        engine = create_engine(db_url)

        # Создаем схему, если она не существует
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            conn.commit()

        logger.info(f"Схема {schema_name} успешно создана или уже существует")
        return True
    except Exception as e:
        logger.error(f"Ошибка при инициализации схемы БД: {e}")
        return False

def get_db_url():
    """
    Формирует URL подключения к БД из переменных окружения или использует SQLite по умолчанию
    """
    database_url = os.environ.get('DATABASE_URL')
    
    # Если URL начинается с postgresql:// и не указана схема
    if database_url and database_url.startswith('postgresql://'):
        schema = os.environ.get('POSTGRES_SCHEMA', 'rozoom_schema')
        return database_url, {'options': f'-c search_path={schema}'}
    
    # По умолчанию используем SQLite
    return 'sqlite:///instance/clients.db', {}
