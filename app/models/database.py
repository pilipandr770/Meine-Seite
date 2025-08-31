"""
Модуль для обеспечения совместимости с различными драйверами PostgreSQL.
Предоставляет интерфейс для работы как с psycopg2, так и с pg8000.
"""
import os
import logging
import ssl
from datetime import datetime
from sqlalchemy import create_engine, event
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)

# Инициализация SQLAlchemy
db = SQLAlchemy()

class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def get_postgres_uri():
    """Возвращает URI подключения PostgreSQL. Если psycopg2 недоступен, форсируем драйвер pg8000."""
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_URI')
    if not database_url:
        host = os.environ.get('DATABASE_HOST', 'localhost')
        port = os.environ.get('DATABASE_PORT', '5432')
        database = os.environ.get('DATABASE_NAME', 'rozoom')
        username = os.environ.get('DATABASE_USERNAME', 'postgres')
        password = os.environ.get('DATABASE_PASSWORD', 'postgres')
        database_url = f'postgresql://{username}:{password}@{host}:{port}/{database}'

    # Нормализуем префикс
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    # Если уже указан конкретный драйвер, оставляем
    if database_url.startswith('postgresql+'):  # уже содержит драйвер
        return database_url

    # Проверяем доступность psycopg2, иначе используем pg8000
    use_pg8000 = False
    try:
        import psycopg2  # noqa: F401
    except Exception:
        use_pg8000 = True
    if use_pg8000:
        database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
    return database_url

def create_db_engine(uri=None, schema=None, engine_options=None):
    """Создает SQLAlchemy Engine, добавляя SSL для pg8000 при необходимости."""
    if uri is None:
        uri = get_postgres_uri()

    opts = engine_options.copy() if engine_options else {}

    connect_args = opts.pop('connect_args', {}) or {}
    # Если явно не передан ssl_context и драйвер pg8000 — добавим
    if 'pg8000' in uri and 'ssl_context' not in connect_args:
        try:
            connect_args['ssl_context'] = ssl.create_default_context()
        except Exception as e:
            logger.warning(f"Cannot create SSL context: {e}")

    # Если схема указана и не установлена через options в URI
    if schema and 'pg8000' not in uri:
        # Для psycopg2 допустим options через connect_args
        connect_args.setdefault('options', f'-c search_path={schema}')

    engine = create_engine(
        uri,
        connect_args=connect_args,
        **opts
    )
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        logger.info("Database connection OK")
    except Exception as e:
        logger.error(f"Initial DB connection failed: {e}")
        raise
    return engine

# Глобальный экземпляр SQLAlchemy для совместимости со стандартным кодом Flask-SQLAlchemy

def init_db(app):
    """Инициализирует базу данных: использует готовый URI из Config и engine options."""
    if 'SQLALCHEMY_DATABASE_URI' not in app.config:
        app.config['SQLALCHEMY_DATABASE_URI'] = get_postgres_uri()
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)

    # Применяем engine options (включая ssl_context) если заданы в конфиге
    engine_options = app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {})
    # Flask-SQLAlchemy примет их через параметр engine_options при init_app
    db.init_app(app)
    
    # В новых версиях Flask before_first_request устарел (removed)
    # Сразу прикрепляем событие при инициализации базы данных 
    uri = app.config['SQLALCHEMY_DATABASE_URI']
    search_path = app.config.get('DB_SEARCH_PATH') or os.getenv('POSTGRES_SCHEMA_CLIENTS')

    # Если используется SQLite (локальная разработка), пропускаем Postgres-специфичную логику
    if uri.startswith('sqlite'):
        logger.info("SQLite detected — skipping Postgres-specific schema setup.")
        return db

    # Продолжаем только для PostgreSQL (pg8000/psycopg2)
    if 'postgresql' in uri and search_path:
        # Получаем движок сразу
        with app.app_context():
            engine = db.get_engine()
            
            # Функция для установки search_path при подключении
            @event.listens_for(engine, 'connect')
            def set_search_path(dbapi_conn, conn_record):
                try:
                    cursor = dbapi_conn.cursor()
                    cursor.execute(f"SET search_path TO {search_path}")
                    cursor.close()
                    logger.info(f"Set search_path to {search_path} for connection {id(dbapi_conn)}")
                except Exception as e:
                    logger.warning(f"Failed to set search_path '{search_path}': {e}")
            
            # Создание необходимых таблиц при инициализации
            try:
                logger.info("Инициализация таблиц базы данных...")
                from sqlalchemy import text
                
                # Создание дополнительных схем (clients + shop) если они указаны в конфиге
                with engine.begin() as conn:
                    client_schema = app.config.get('CLIENT_REQUESTS_SCHEMA')
                    shop_schema = app.config.get('SHOP_SCHEMA')
                    # Create client requests schema if configured
                    if client_schema:
                        try:
                            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {client_schema}"))
                            logger.info(f"Схема {client_schema} создана или уже существует")
                        except Exception as e:
                            logger.error(f"Ошибка при создании схемы {client_schema}: {e}")
                    # Create shop schema if configured
                    if shop_schema:
                        try:
                            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {shop_schema}"))
                            logger.info(f"Схема {shop_schema} создана или уже существует")
                        except Exception as e:
                            logger.error(f"Ошибка при создании схемы {shop_schema}: {e}")
                
                # Use SQLAlchemy to create all tables
                with app.app_context():
                    # Drop all tables first to ensure foreign keys are updated
                    db.drop_all()
                    db.create_all()
                    logger.info("✅ Все таблицы созданы или уже существуют")
                
                # Additional manual table creation for client_requests if needed
                if client_schema:
                    with engine.begin() as conn:
                        try:
                            conn.execute(text(f"""
                            CREATE TABLE IF NOT EXISTS {client_schema}.client_requests (
                                id SERIAL PRIMARY KEY,
                                project_type VARCHAR(100) NOT NULL,
                                project_name VARCHAR(200),
                                task_description TEXT NOT NULL,
                                key_features TEXT,
                                design_preferences TEXT,
                                platform VARCHAR(100),
                                budget VARCHAR(100),
                                timeline VARCHAR(100),
                                integrations TEXT,
                                contact_method VARCHAR(100) NOT NULL,
                                contact_info VARCHAR(200),
                                status VARCHAR(30) DEFAULT 'new',
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                deadline TIMESTAMP,
                                priority INTEGER DEFAULT 1,
                                tech_stack TEXT,
                                acceptance_criteria TEXT,
                                notes TEXT
                            )
                            """))
                            logger.info(f"✅ Таблица {client_schema}.client_requests создана или уже существует")
                        except Exception as e:
                            logger.error(f"Ошибка при создании таблицы client_requests: {e}")
            except Exception as e:
                logger.error(f"Общая ошибка при инициализации таблиц: {e}")
    
    return db
