"""
Updated route for serving category images directly from database
"""
from flask import Blueprint, send_file, abort, current_app
from io import BytesIO
import logging

# Import the required models
from app.models.product import Category

# Create a logger
logger = logging.getLogger(__name__)

def add_category_image_route(media_blueprint):
    """
    Add route for serving category images to an existing media blueprint
    
    Args:
        media_blueprint: The existing media Blueprint instance
    """
    @media_blueprint.route('/media/category-image/<int:category_id>')
    def serve_category_image(category_id):
        try:
            logger.debug(f"Serving category image ID: {category_id}")
            category = Category.query.get(category_id)
            if not category or not category.image_data:
                logger.warning(f"Category image not found: {category_id}")
                abort(404)
            
            logger.debug(f"Serving category image from database: {category.image_filename}, {len(category.image_data)} bytes")
            return send_file(
                BytesIO(category.image_data), 
                mimetype=category.image_content_type or 'application/octet-stream', 
                download_name=category.image_filename
            )
        except Exception as e:
            logger.exception(f"Error serving category image {category_id}: {str(e)}")
            abort(500)
    
    return media_blueprint
