from flask import Flask
import os
import sys
import logging

# Configure logging
log_level = logging.DEBUG if os.environ.get('FLASK_ENV') == 'development' else logging.INFO
logging.basicConfig(level=log_level, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.debug("Debug logging enabled")

# Create a custom handler to intercept warnings about insufficient stock
class StockWarningFilter(logging.Filter):
    def filter(self, record):
        # Block any "Insufficient stock" messages
        if record.levelname == "WARNING" and hasattr(record, "msg") and isinstance(record.msg, str):
            if "Insufficient stock" in record.msg:
                # Convert to debug message for troubleshooting but don't block execution
                logger.debug(f"INTERCEPTED: {record.msg}")
                return False
        return True

# Apply the filter to the app logger
logger.addFilter(StockWarningFilter())

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
from sqlalchemy import text

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    # Используем DATABASE_URI из конфига, который берется из переменной окружения
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Register custom template filters
    from app.utils.template_filters import register_template_filters
    register_template_filters(app)
    
    # Определение схемы для PostgreSQL в зависимости от окружения
    if os.environ.get('RENDER'):
        app.config['POSTGRES_SCHEMA'] = os.environ.get('POSTGRES_SCHEMA', 'render_schema')
    else:
        app.config['POSTGRES_SCHEMA'] = os.environ.get('POSTGRES_SCHEMA', 'rozoom_schema')
    
    # Import all models to ensure they're registered with SQLAlchemy before relationships are resolved
    from app.models import user, product, shop, order, coupon, client, task
    from app.models.user import User
    from app.models.product import Category, Product, ProductImage, ProductReview
    from app.models.shop import Cart, CartItem
    from app.models.order import Order, OrderItem, Payment
    from app.models.coupon import Coupon
    from app.models.client import Client, ClientRequest
    from app.models.task import Task
    from app.models.project import Project, ProjectStage
    
    # Import here to avoid circular imports - используем новый модуль database.py
    from app.models.database import db, init_db
    init_db(app)
    logger.info("Database initialized (pg8000 fallback enabled)")

    from flask_login import LoginManager, current_user
    from flask_wtf import CSRFProtect, csrf
    from flask_session import Session

    # Initialize Flask-Login so `current_user` is available in templates
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    # Initialize Flask-Session
    Session(app)

    @login_manager.user_loader
    def load_user(user_id):
        # Import here to avoid circular imports at module import time
        from app.models.user import User
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    # Ensure `current_user` is available in Jinja templates
    @app.context_processor
    def inject_current_user():
        return {'current_user': current_user}
    # Also add to jinja globals to be extra-safe for templates evaluated early
    app.jinja_env.globals['current_user'] = current_user
    # Initialize CSRF protection so templates can call csrf_token()
    csrf_protect = CSRFProtect()
    csrf_protect.init_app(app)
    # Expose helper to templates
    app.jinja_env.globals['csrf_token'] = lambda: csrf.generate_csrf()

    # Inject cart count into templates
    @app.context_processor
    def inject_cart_count():
        try:
            from app.routes.shop import get_cart
            cart = get_cart()
            count = sum(item.quantity for item in cart.items) if cart and cart.items else 0
        except Exception:
            count = 0
        return {'cart_count': count}

    # Проверяем, нужно ли создать схему в PostgreSQL
    schema = app.config.get('POSTGRES_SCHEMA')
    extra_schema = os.environ.get('POSTGRES_SCHEMA_CLIENTS')
    # Ленивая стратегия: не создаём схемы и таблицы автоматически здесь.
    # Предполагаем, что схемы есть или создаются через миграции / отдельный скрипт.
    # Это предотвращает ранние подключения и дублирование метаданных.
    
    # Import and register routes after app creation
    from app.routes import register_routes
    register_routes(app)
    
    from .i18n import register_i18n
    register_i18n(app)

    # Safety hook: rollback aborted transactions & remove session each request
    from app.models.database import db as _db_session

    @app.before_request
    def ensure_db_session_clean():
        """Proactively clear aborted (25P02) transaction state or broken connection before handlers.
        If a simple SELECT fails twice, dispose engine to force new connections."""
        try:
            _db_session.session.execute(text('SELECT 1'))
        except Exception as e:
            logger.warning(f"Pre-request DB check failed (will rollback): {e}")
            try:
                _db_session.session.rollback()
            except Exception as e_inner:
                logger.warning(f"Failed to rollback: {e_inner}")
                pass
        
            # Try a new session entirely
            try:
                _db_session.session.remove()
            except Exception:
                pass
            
            try:
                # Second attempt with fresh session
                _db_session.session.execute(text('SELECT 1'))
            except Exception as e2:
                logger.error(f"DB still unhealthy; disposing engine: {e2}")
                try:
                    # Force all connections to be recycled
                    engine = _db_session.get_engine()
                    engine.dispose()
                    # Create a fresh session
                    _db_session.session = _db_session.create_scoped_session()
                except Exception as e3:
                    logger.error(f"Failed to dispose engine: {e3}")
                    pass
    @app.teardown_request
    def cleanup_session(exc):  # exc is None if no exception
        try:
            if exc is not None:
                _db_session.session.rollback()
            # If connection in invalid (e.g., 25P02) state, ensure rollback anyway
            else:
                # Test session transaction state lightly
                if _db_session.session.get_bind() is not None:
                    # No direct public flag for aborted; a safe rollback is idempotent
                    _db_session.session.rollback()
            _db_session.session.remove()
        except Exception:
            pass
            
    # Add health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint that verifies database connectivity"""
        from flask import jsonify
        
        health_data = {
            "status": "ok",
            "database": "ok",
            "details": {}
        }
        
        # Check database connection
        try:
            # Simple query to check db connection
            result = _db_session.session.execute(text('SELECT 1 as test_value'))
            value = result.scalar()
            if value != 1:
                health_data["database"] = "error"
                health_data["status"] = "error" 
                health_data["details"]["database"] = "Unexpected query result"
        except Exception as e:
            health_data["database"] = "error"
            health_data["status"] = "error"
            health_data["details"]["database"] = str(e)
        
        # Check for column existence in order_items
        try:
            # Check if the column exists in a non-intrusive way
            result = _db_session.session.execute(
                text("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'order_items' AND column_name = 'project_stage_id'")
            )
            if result.scalar() == 0:
                health_data["details"]["order_items_column"] = "missing project_stage_id column"
                health_data["status"] = "warning"
        except Exception as e:
            health_data["details"]["schema_check"] = str(e)
        
        status_code = 200 if health_data["status"] == "ok" else 500
        return jsonify(health_data), status_code
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
