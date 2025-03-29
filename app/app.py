from flask import Flask
from config import Config  # Нове: імпорт класу конфігурації
from app.routes import register_routes  # Changed back to absolute import
from app.models.client import db        # Changed back to absolute import

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # Завантаження конфігурації (секретний ключ та ін.)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///clients.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()  # Створюємо таблиці у базі

    register_routes(app)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
