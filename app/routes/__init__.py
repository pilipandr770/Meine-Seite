from flask import Blueprint
from .main import main_bp
from .chatbot import chatbot_bp
from .crm import crm_bp
from .calendar import calendar_bp
from .pages import pages_bp  # Додаємо новий файл pages.py

def register_routes(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(chatbot_bp, url_prefix="/chatbot")
    app.register_blueprint(crm_bp, url_prefix="/crm")
    app.register_blueprint(calendar_bp, url_prefix="/calendar")
    app.register_blueprint(pages_bp)  # Реєструємо нові маршрути
