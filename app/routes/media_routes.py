"""
Register the media blueprint and routes in your Flask application
"""
from flask import Blueprint
from app.routes.category_media import add_category_image_route

def register_media_blueprint(app):
    """
    Register the media blueprint with the Flask app
    
    Args:
        app: The Flask application instance
    """
    # Create the media blueprint if it doesn't exist
    media_bp = Blueprint('media', __name__)
    
    # Add the category image route
    media_bp = add_category_image_route(media_bp)
    
    # Register the blueprint with the app
    app.register_blueprint(media_bp)
    
    return app
