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
    # Ленивая стратегия: не создаём схемы и таблицы автоматически здесь.
    # Предполагаем, что схемы есть или создаются через миграции / отдельный скрипт.
    # Это предотвращает ранние подключения и дублирование метаданных.
    
    # Import and register routes after app creation
    from routes import register_routes
    register_routes(app)
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
