"""
Register the category media blueprint and routes in your Flask application
"""
from flask import Blueprint
from app.routes.category_media import add_category_image_route

def register_media_blueprint(app):
    """
    Register the media blueprint with the Flask app
    
    Args:
        app: The Flask application instance
    """
    # Create the media blueprint with a unique name to avoid conflicts
    # Note: use url_prefix to match the expected URL pattern /category_media/...
    category_media_bp = Blueprint('category_media', __name__, url_prefix='/category_media')
    
    # Add the category image route
    category_media_bp = add_category_image_route(category_media_bp)
    
    # Register the blueprint with the app
    app.register_blueprint(category_media_bp)
    
    return app
