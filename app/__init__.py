"""
Flask application initialization for RoZoom website.
"""
from flask import Flask
try:
    from flask_bootstrap import Bootstrap
    _HAS_BOOTSTRAP = True
except Exception:
    # Optional dependency in local dev; proceed without it if missing.
    Bootstrap = None
    _HAS_BOOTSTRAP = False
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf import CSRFProtect
from config import Config

# Use the shared db instance from app.models.database
from app.models.database import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    if _HAS_BOOTSTRAP and Bootstrap:
        Bootstrap(app)

    login = LoginManager()
    login.login_view = 'auth.login'
    login.init_app(app)

    migrate = Migrate()
    migrate.init_app(app, db)

    Mail(app)
    CSRFProtect(app)

    # Register blueprints
    from app.routes.main import bp as main_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.pages import bp as pages_bp
    from app.routes.crm import bp as crm_bp
    from app.routes.calendar_routes import bp as calendar_bp
    from app.routes.chatbot import bp as chatbot_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(pages_bp)
    app.register_blueprint(crm_bp)
    app.register_blueprint(calendar_bp, url_prefix='/calendar')
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot')

    # Initialize DB (shared instance)
    db.init_app(app)

    # Import canonical models so SQLAlchemy maps them exactly once
    # Keep imports here to ensure models are registered after app and db are configured
    from app.models import client, task, user
    # Canonical shop models
    from app.models import product, order, coupon, shop

    return app
    from app.routes.shop import shop_bp
    from app.routes.stripe_webhooks import stripe_webhooks
    
    app.register_blueprint(main_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(crm_bp, url_prefix='/crm')
    app.register_blueprint(chatbot_bp, url_prefix='/chat')
    app.register_blueprint(calendar_bp, url_prefix='/calendar')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(admin_shop, url_prefix='/admin/shop')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(shop_bp, url_prefix='/shop')
    app.register_blueprint(stripe_webhooks, url_prefix='/webhooks/stripe')
    
    # Language handling
    @app.before_request
    def set_default_language():
        if 'lang' not in session:
            session['lang'] = request.accept_languages.best_match(['en', 'de', 'uk']) or 'de'

    # Ensure `current_user` is always available in templates (some templates access it directly)
    @app.context_processor
    def inject_current_user():
        return {'current_user': current_user}
    
    return app