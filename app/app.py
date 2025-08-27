from flask import Flask
import os
import sys

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
    
    # Import here to avoid circular imports
    from models.client import db
    db.init_app(app)

    # Проверяем, нужно ли создать схему в PostgreSQL
    if app.config.get("SQLALCHEMY_DATABASE_URI", "").startswith("postgresql"):
        with app.app_context():
            # Сначала создаем схему, если она не существует
            try:
                db.session.execute(db.text("CREATE SCHEMA IF NOT EXISTS rozoom_schema"))
                db.session.commit()
                # Установим схему по умолчанию для текущей сессии
                db.session.execute(db.text("SET search_path TO rozoom_schema"))
                db.session.commit()
                print("Схема rozoom_schema создана или уже существует.")
            except Exception as e:
                print(f"Ошибка при создании схемы: {e}")
                db.session.rollback()
    
    # Теперь создаем таблицы
    with app.app_context():
        try:
            db.create_all()
            print("Таблицы успешно созданы.")
        except Exception as e:
            print(f"Ошибка при создании таблиц: {e}")
            db.session.rollback()
    
    # Import and register routes after app creation
    from routes import register_routes
    register_routes(app)
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
