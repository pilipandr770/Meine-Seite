from flask import Flask
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import config
sys.path.append(parent_dir)
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    # Используем DATABASE_URI из конфига, который берется из переменной окружения
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Определение схемы для PostgreSQL в зависимости от окружения
    if os.environ.get('RENDER'):
        app.config['POSTGRES_SCHEMA'] = os.environ.get('POSTGRES_SCHEMA', 'render_schema')
    else:
        app.config['POSTGRES_SCHEMA'] = os.environ.get('POSTGRES_SCHEMA', 'rozoom_schema')
    
    # Import here to avoid circular imports - используем новый модуль database.py
    try:
        # Пробуем использовать новый интерфейс с поддержкой pg8000
        try:
            from app.models.database import db, init_db
            logger.info("Successfully imported new database module")
            init_db(app)
            logger.info("Successfully initialized database with app using new interface")
        except ImportError:
            # Запасной вариант - старый интерфейс
            from app.models.client import db
            logger.info("Using legacy database interface")
            db.init_app(app)
            logger.info("Successfully initialized database with app using legacy interface")
    except ImportError as e:
        logger.error(f"Failed to import database models: {e}")
        raise
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

    # Проверяем, нужно ли создать схему в PostgreSQL
    schema = app.config.get('POSTGRES_SCHEMA')
    if app.config.get("SQLALCHEMY_DATABASE_URI", "").startswith("postgresql") and schema:
        with app.app_context():
            # Сначала создаем схему, если она не существует
            try:
                db.session.execute(db.text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                db.session.commit()
                # Установим схему по умолчанию для текущей сессии
                db.session.execute(db.text(f"SET search_path TO {schema}"))
                db.session.commit()
                logger.info(f"Schema {schema} created or already exists")
            except Exception as e:
                logger.error(f"Error creating schema: {e}")
                db.session.rollback()
    
    # Теперь создаем таблицы
    with app.app_context():
        try:
            db.create_all()
            logger.info("Tables successfully created")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            db.session.rollback()
    
    # Import and register routes after app creation
    from routes import register_routes
    register_routes(app)
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
