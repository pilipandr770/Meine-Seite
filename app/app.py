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
    from app.models.database import db, init_db
    init_db(app)
    logger.info("Database initialized (pg8000 fallback enabled)")

    # Проверяем, нужно ли создать схему в PostgreSQL
    schema = app.config.get('POSTGRES_SCHEMA')
    extra_schema = os.environ.get('POSTGRES_SCHEMA_CLIENTS')
    if app.config.get("SQLALCHEMY_DATABASE_URI", "").startswith("postgresql") and schema:
        with app.app_context():
            # Сначала создаем схему, если она не существует
            try:
                from sqlalchemy import text
                db.session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                db.session.commit()
                # Установим схему по умолчанию для текущей сессии
                db.session.execute(text(f"SET search_path TO {schema}"))
                db.session.commit()
                logger.info(f"Schema {schema} created or already exists")
                # Создаем дополнительную схему для client requests если указана
                if extra_schema and extra_schema != schema:
                    db.session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {extra_schema}"))
                    db.session.commit()
                    logger.info(f"Extra schema {extra_schema} created or already exists")
            except Exception as e:
                logger.error(f"Error creating schema: {e}")
                db.session.rollback()
    
    # Теперь создаем таблицы
    with app.app_context():
        try:
            from sqlalchemy import text
            # Создаем таблицы в основной схеме
            db.create_all()
            logger.info("Tables successfully created in base schema")
            # Если есть дополнительная схема для client_requests, переносим/создаем там
            if extra_schema and extra_schema != schema:
                try:
                    db.session.execute(text(f"SET search_path TO {extra_schema}"))
                    db.session.commit()
                    # Создадим таблицу client_requests отдельно если её нет
                    db.session.execute(text(f"CREATE TABLE IF NOT EXISTS {extra_schema}.client_requests (LIKE {schema}.client_requests INCLUDING ALL)"))
                    db.session.commit()
                    logger.info(f"client_requests structure ensured in {extra_schema}")
                    # Вернём search_path
                    db.session.execute(text(f"SET search_path TO {schema}"))
                    db.session.commit()
                except Exception as e:
                    logger.error(f"Error ensuring client_requests in extra schema: {e}")
                    db.session.rollback()
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
