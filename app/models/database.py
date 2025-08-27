"""
Модуль для обеспечения совместимости с различными драйверами PostgreSQL.
Предоставляет интерфейс для работы как с psycopg2, так и с pg8000.
"""
import os
import logging
from sqlalchemy import create_engine
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)

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
    # Добавляем sslmode=require если не указано (Render требует SSL)
    if 'sslmode=' not in database_url:
        sep = '&' if '?' in database_url else '?'
        database_url = f"{database_url}{sep}sslmode=require"
    return database_url

def create_db_engine(uri=None, schema=None):
    """Создает SQLAlchemy Engine с поддержкой как psycopg2, так и pg8000."""
    if uri is None:
        uri = get_postgres_uri()
    
    # Добавляем к URI параметры для использования схемы, если указана
    connect_args = {}
    if schema:
        # Для pg8000
        connect_args['options'] = f'-c search_path={schema}'

    try:
        # Сначала пробуем pg8000 (чистый Python драйвер, совместимый с Python 3.13)
        engine = create_engine(
            uri, 
            connect_args=connect_args,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=10,
            max_overflow=20,
            echo=False,
            execution_options={"schema_translate_map": {None: schema}} if schema else {}
        )
        # Проверяем подключение
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Successfully connected to PostgreSQL using pg8000")
        return engine
    except Exception as e:
        logger.warning(f"Failed to connect using pg8000: {e}")
        
        # Удаляем параметр из URI, который может быть специфичным для pg8000
        if "?driver=pg8000" in uri:
            uri = uri.replace("?driver=pg8000", "")
        
        try:
            # Резервный вариант - пробуем psycopg2
            engine = create_engine(
                uri,
                connect_args={"options": f"-c search_path={schema}"} if schema else {},
                pool_pre_ping=True,
                pool_recycle=300,
                pool_size=10,
                max_overflow=20,
                echo=False,
                execution_options={"schema_translate_map": {None: schema}} if schema else {}
            )
            # Проверяем подключение
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            logger.info("Successfully connected to PostgreSQL using psycopg2")
            return engine
        except Exception as e2:
            logger.error(f"Failed to connect to database with both drivers: {e2}")
            raise

# Глобальный экземпляр SQLAlchemy для совместимости со стандартным кодом Flask-SQLAlchemy
db = SQLAlchemy()

def init_db(app):
    """Инициализирует базу данных с учетом настроек схемы."""
    # Устанавливаем URI из функции для обеспечения совместимости с разными драйверами
    app.config['SQLALCHEMY_DATABASE_URI'] = get_postgres_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Инициализируем объект SQLAlchemy с приложением
    db.init_app(app)
    
    # Если указана схема в конфигурации, настраиваем ее
    schema = app.config.get('POSTGRES_SCHEMA')
    if schema:
        # Добавляем обработчик событий до запроса для установки схемы
        @app.before_request
        def set_schema():
            if hasattr(db, 'session'):
                db.session.execute(f'SET search_path TO {schema}')
    
    return db
