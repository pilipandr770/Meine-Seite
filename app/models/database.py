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
                    # Include projects_schema in search_path if it's configured
                    projects_schema = app.config.get('PROJECTS_SCHEMA')
                    if projects_schema and projects_schema not in search_path.split(','):
                        full_search_path = f"{search_path},{projects_schema}"
                    else:
                        full_search_path = search_path
                    cursor.execute(f"SET search_path TO {full_search_path}")
                    cursor.close()
                    logger.info(f"Set search_path to {full_search_path} for connection {id(dbapi_conn)}")
                except Exception as e:
                    logger.warning(f"Failed to set search_path '{search_path}': {e}")
                    # Don't raise exception to avoid breaking connection
            
            # Функция для обработки отключений соединений
            @event.listens_for(engine, 'checkout')
            def ping_connection(dbapi_conn, conn_record, conn_proxy):
                try:
                    cursor = dbapi_conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                except Exception as e:
                    logger.warning(f"Connection ping failed: {e}")
                    # Invalidate the connection so SQLAlchemy creates a new one
                    conn_proxy.invalidate()
                    raise
            
            # Создание необходимых таблиц при инициализации
            try:
                logger.info("Инициализация таблиц базы данных...")
                from sqlalchemy import text

                # Создание дополнительных схем (clients + shop + projects) если они указаны в конфиге
                with engine.begin() as conn:
                    client_schema = app.config.get('CLIENT_REQUESTS_SCHEMA')
                    shop_schema = app.config.get('SHOP_SCHEMA')
                    projects_schema = app.config.get('PROJECTS_SCHEMA')
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
                    # Create projects schema if configured
                    projects_schema = app.config.get('PROJECTS_SCHEMA')
                    if projects_schema:
                        try:
                            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {projects_schema}"))
                            logger.info(f"Схема {projects_schema} создана или уже существует")
                        except Exception as e:
                            logger.error(f"Ошибка при создании схемы {projects_schema}: {e}")
                            # If projects_schema couldn't be created and differs from client_schema, fall back to client_schema
                            if client_schema and projects_schema != client_schema:
                                logger.warning(f"Использование {client_schema} в качестве запасного варианта для projects_schema")
                                app.config['PROJECTS_SCHEMA'] = client_schema
                                projects_schema = client_schema
                    # No explicit commit needed - engine.begin() handles transaction automatically

                # Use SQLAlchemy to create all tables (only create, don't drop in production)
                with app.app_context():
                    # Set search_path before creating tables - include all schemas
                    projects_schema = app.config.get('PROJECTS_SCHEMA')
                    if projects_schema and projects_schema not in search_path.split(','):
                        table_search_path = f"{search_path},{projects_schema}"
                    else:
                        table_search_path = search_path
                    
                    with engine.begin() as conn:
                        try:
                            conn.execute(text(f"SET search_path TO {table_search_path}"))
                            logger.info(f"Set search_path to {table_search_path} for table creation")
                        except Exception as e:
                            logger.warning(f"Failed to set search_path for table creation: {e}")
                    
                    # FIRST: Create client_requests table manually before other tables
                    if client_schema:
                        with engine.begin() as conn:
                            try:
                                conn.execute(text(f"SET search_path TO {table_search_path}"))
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
                    
                    # Check environment - NEVER drop tables in production
                    environment = app.config.get('ENVIRONMENT', 'development')
                    flask_env = os.environ.get('FLASK_ENV', 'development')
                    render_env = os.environ.get('RENDER', 'false')
                    render_service = os.environ.get('RENDER_SERVICE_ID', '')
                    
                    logger.info(f"Environment detection: ENVIRONMENT={environment}, FLASK_ENV={flask_env}, RENDER={render_env}, RENDER_SERVICE_ID={render_service}")
                    
                    # Multiple ways to detect production (Render.com specific)
                    is_production = (
                        environment == 'production' or 
                        flask_env == 'production' or 
                        render_env == 'true' or
                        bool(render_service) or
                        'RENDER' in os.environ or
                        'RENDER_SERVICE_ID' in os.environ
                    )
                    
                    logger.info(f"Production detection result: {is_production}")
                    
                    if not is_production:
                        logger.info("Development environment detected - skipping table drop to preserve existing data")
                        # Don't drop tables in development to preserve existing data
                        try:
                            db.create_all()
                            logger.info("✅ Все таблицы созданы или уже существуют")
                        except Exception as e:
                            logger.warning(f"Error creating tables with db.create_all(): {e}")
                            logger.info("Attempting to create tables individually...")
                            # Try to create tables individually to handle foreign key dependencies
                            from app.models.user import User
                            from app.models.product import Category, Product, ProductImage, ProductReview
                            from app.models.shop import Cart, CartItem
                            from app.models.order import Order, OrderItem, Payment
                            from app.models.coupon import Coupon
                            from app.models.client import Client, ClientRequest
                            from app.models.task import Task
                            from app.models.project import Project, ProjectStage
                            
                            # Create tables in dependency order
                            try:
                                User.__table__.create(db.engine, checkfirst=True)
                                logger.info("✅ User table created")
                            except Exception as e:
                                logger.warning(f"Error creating User table: {e}")
                            
                            try:
                                Client.__table__.create(db.engine, checkfirst=True)
                                logger.info("✅ Client table created")
                            except Exception as e:
                                logger.warning(f"Error creating Client table: {e}")
                            
                            try:
                                ClientRequest.__table__.create(db.engine, checkfirst=True)
                                logger.info("✅ ClientRequest table created")
                            except Exception as e:
                                logger.warning(f"Error creating ClientRequest table: {e}")
                            
                            try:
                                Category.__table__.create(db.engine, checkfirst=True)
                                logger.info("✅ Category table created")
                            except Exception as e:
                                logger.warning(f"Error creating Category table: {e}")
                            
                            try:
                                Product.__table__.create(db.engine, checkfirst=True)
                                logger.info("✅ Product table created")
                            except Exception as e:
                                logger.warning(f"Error creating Product table: {e}")
                            
                            try:
                                Cart.__table__.create(db.engine, checkfirst=True)
                                logger.info("✅ Cart table created")
                            except Exception as e:
                                logger.warning(f"Error creating Cart table: {e}")
                            
                            try:
                                CartItem.__table__.create(db.engine, checkfirst=True)
                                logger.info("✅ CartItem table created")
                            except Exception as e:
                                logger.warning(f"Error creating CartItem table: {e}")
                            
                            try:
                                Order.__table__.create(db.engine, checkfirst=True)
                                logger.info("✅ Order table created")
                            except Exception as e:
                                logger.warning(f"Error creating Order table: {e}")
                            
                            try:
                                OrderItem.__table__.create(db.engine, checkfirst=True)
                                logger.info("✅ OrderItem table created")
                            except Exception as e:
                                logger.warning(f"Error creating OrderItem table: {e}")
                            
                            try:
                                Project.__table__.create(db.engine, checkfirst=True)
                                logger.info("✅ Project table created")
                            except Exception as e:
                                logger.warning(f"Error creating Project table: {e}")
                            
                            try:
                                Task.__table__.create(db.engine, checkfirst=True)
                                logger.info("✅ Task table created")
                            except Exception as e:
                                logger.warning(f"Error creating Task table: {e}")
                            
                            # Create remaining tables
                            try:
                                Coupon.__table__.create(db.engine, checkfirst=True)
                                logger.info("✅ Coupon table created")
                            except Exception as e:
                                logger.warning(f"Error creating Coupon table: {e}")
                            
                            try:
                                Payment.__table__.create(db.engine, checkfirst=True)
                                logger.info("✅ Payment table created")
                            except Exception as e:
                                logger.warning(f"Error creating Payment table: {e}")
                            
                            try:
                                ProductImage.__table__.create(db.engine, checkfirst=True)
                                logger.info("✅ ProductImage table created")
                            except Exception as e:
                                logger.warning(f"Error creating ProductImage table: {e}")
                            
                            try:
                                ProductReview.__table__.create(db.engine, checkfirst=True)
                                logger.info("✅ ProductReview table created")
                            except Exception as e:
                                logger.warning(f"Error creating ProductReview table: {e}")
                            
                            try:
                                # Ensure search_path includes projects_schema for ProjectStage creation
                                projects_schema = app.config.get('PROJECTS_SCHEMA')
                                if projects_schema:
                                    with engine.begin() as conn:
                                        conn.execute(text(f"SET search_path TO {table_search_path}"))
                                
                                ProjectStage.__table__.create(db.engine, checkfirst=True)
                                logger.info("✅ ProjectStage table created")
                            except Exception as e:
                                logger.warning(f"Error creating ProjectStage table: {e}")
                    else:
                        logger.info("Production environment detected - creating tables in dependency order")
                        # In production, create tables individually to ensure correct dependency order
                        
                        # Ensure search_path includes projects_schema for table creation
                        projects_schema = app.config.get('PROJECTS_SCHEMA')
                        if projects_schema and projects_schema not in table_search_path.split(','):
                            production_search_path = f"{table_search_path},{projects_schema}"
                        else:
                            production_search_path = table_search_path
                        
                        # Set search_path for the engine
                        with engine.begin() as conn:
                            try:
                                conn.execute(text(f"SET search_path TO {production_search_path}"))
                                logger.info(f"Set search_path to {production_search_path} for production table creation")
                            except Exception as e:
                                logger.warning(f"Failed to set search_path for production table creation: {e}")
                        
                        from app.models.user import User
                        from app.models.product import Category, Product, ProductImage, ProductReview
                        from app.models.shop import Cart, CartItem
                        from app.models.order import Order, OrderItem, Payment
                        from app.models.coupon import Coupon
                        from app.models.client import Client, ClientRequest
                        from app.models.task import Task
                        from app.models.project import Project, ProjectStage
                        
                        # Create tables in strict dependency order
                        try:
                            User.__table__.create(db.engine, checkfirst=True)
                            logger.info("✅ User table created")
                        except Exception as e:
                            logger.warning(f"Error creating User table: {e}")
                        
                        try:
                            Client.__table__.create(db.engine, checkfirst=True)
                            logger.info("✅ Client table created")
                        except Exception as e:
                            logger.warning(f"Error creating Client table: {e}")
                        
                        try:
                            ClientRequest.__table__.create(db.engine, checkfirst=True)
                            logger.info("✅ ClientRequest table created")
                        except Exception as e:
                            logger.warning(f"Error creating ClientRequest table: {e}")
                        
                        try:
                            Category.__table__.create(db.engine, checkfirst=True)
                            logger.info("✅ Category table created")
                        except Exception as e:
                            logger.warning(f"Error creating Category table: {e}")
                        
                        try:
                            Product.__table__.create(db.engine, checkfirst=True)
                            logger.info("✅ Product table created")
                        except Exception as e:
                            logger.warning(f"Error creating Product table: {e}")
                        
                        try:
                            Cart.__table__.create(db.engine, checkfirst=True)
                            logger.info("✅ Cart table created")
                        except Exception as e:
                            logger.warning(f"Error creating Cart table: {e}")
                        
                        try:
                            CartItem.__table__.create(db.engine, checkfirst=True)
                            logger.info("✅ CartItem table created")
                        except Exception as e:
                            logger.warning(f"Error creating CartItem table: {e}")
                        
                        try:
                            Order.__table__.create(db.engine, checkfirst=True)
                            logger.info("✅ Order table created")
                        except Exception as e:
                            logger.warning(f"Error creating Order table: {e}")
                        
                        try:
                            OrderItem.__table__.create(db.engine, checkfirst=True)
                            logger.info("✅ OrderItem table created")
                        except Exception as e:
                            logger.warning(f"Error creating OrderItem table: {e}")
                        
                        # Create Project BEFORE ProjectStage (dependency order)
                        try:
                            Project.__table__.create(db.engine, checkfirst=True)
                            logger.info("✅ Project table created")
                        except Exception as e:
                            logger.warning(f"Error creating Project table: {e}")
                        
                        try:
                            Task.__table__.create(db.engine, checkfirst=True)
                            logger.info("✅ Task table created")
                        except Exception as e:
                            logger.warning(f"Error creating Task table: {e}")
                        
                        # Create ProjectStage AFTER Project (dependency order)
                        try:
                            # Ensure search_path includes projects_schema for ProjectStage creation
                            if projects_schema:
                                with engine.begin() as conn:
                                    conn.execute(text(f"SET search_path TO {production_search_path}"))
                            
                            ProjectStage.__table__.create(db.engine, checkfirst=True)
                            logger.info("✅ ProjectStage table created")
                        except Exception as e:
                            logger.warning(f"Error creating ProjectStage table: {e}")
                        
                        # Create remaining tables
                        try:
                            Coupon.__table__.create(db.engine, checkfirst=True)
                            logger.info("✅ Coupon table created")
                        except Exception as e:
                            logger.warning(f"Error creating Coupon table: {e}")
                        
                        try:
                            Payment.__table__.create(db.engine, checkfirst=True)
                            logger.info("✅ Payment table created")
                        except Exception as e:
                            logger.warning(f"Error creating Payment table: {e}")
                        
                        try:
                            ProductImage.__table__.create(db.engine, checkfirst=True)
                            logger.info("✅ ProductImage table created")
                        except Exception as e:
                            logger.warning(f"Error creating ProductImage table: {e}")
                        
                        try:
                            ProductReview.__table__.create(db.engine, checkfirst=True)
                            logger.info("✅ ProductReview table created")
                        except Exception as e:
                            logger.warning(f"Error creating ProductReview table: {e}")
                    logger.info("✅ Все таблицы созданы или уже существуют")
            except Exception as e:
                logger.error(f"Общая ошибка при инициализации таблиц: {e}")

    return db
