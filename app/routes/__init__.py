from flask import Blueprint
from .main import main_bp
from .pages import pages_bp
from .chatbot import chatbot_bp
from .calendar_routes import calendar_bp  # Імпортуємо calendar_bp з нового файлу
from .crm import crm_bp  # Импортируем blueprint для CRM
from .project import project_bp  # Импортируем blueprint для управления проектами
from .admin import admin_bp  # Импортируем blueprint админки
from .admin_shop import admin_shop  # Импортируем blueprint админки магазина
from .auth import auth_bp  # Импортируем blueprint для аутентификации
from .shop import shop_bp  # Импортируем blueprint магазина
from .stripe_webhooks import stripe_webhooks  # Импортируем blueprint для Stripe webhook'ов
from .media import media  # Serve images stored in DB
from .debug import debug_bp  # Debug routes

def register_routes(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(chatbot_bp, url_prefix="/chatbot")
    app.register_blueprint(calendar_bp)  # Реєструємо маршрути календаря
    app.register_blueprint(crm_bp, url_prefix="/crm")  # Регистрируем маршруты CRM
    app.register_blueprint(project_bp)  # Регистрируем маршруты управления проектами
    app.register_blueprint(admin_bp, url_prefix="/admin")  # Регистрируем маршруты админки
    app.register_blueprint(admin_shop, url_prefix="/admin/shop")  # Регистрируем маршруты админки магазина
    app.register_blueprint(auth_bp, url_prefix="/auth")  # Регистрируем маршруты аутентификации
    app.register_blueprint(shop_bp, url_prefix="/shop")  # Регистрируем маршруты магазина
    app.register_blueprint(stripe_webhooks, url_prefix="/webhooks/stripe")  # Регистрируем маршруты Stripe webhook'ов
    app.register_blueprint(media)  # /media/image/<id>
    app.register_blueprint(debug_bp, url_prefix="/debug")  # Debug routes
    # ...інші блакитні принти
