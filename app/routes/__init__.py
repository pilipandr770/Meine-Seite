from flask import Blueprint
from .main import main_bp
from .pages import pages_bp
from .chatbot import chatbot_bp
from .calendar_routes import calendar_bp  # Імпортуємо calendar_bp з нового файлу

def register_routes(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(chatbot_bp, url_prefix="/chatbot")
    app.register_blueprint(calendar_bp)  # Реєструємо маршрути календаря
    # ...інші блакитні принти
