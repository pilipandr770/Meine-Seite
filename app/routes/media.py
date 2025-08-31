from flask import Blueprint, current_app, send_file, redirect, abort, url_for
from io import BytesIO
import os
import logging
from app.models.product import ProductImage

media = Blueprint('media', __name__)
logger = logging.getLogger(__name__)

@media.route('/media/image/<int:image_id>')
def serve_image(image_id):
    try:
        logger.debug(f"Serving image ID: {image_id}")
        img = ProductImage.query.get(image_id)
        if not img:
            logger.warning(f"Image not found in database: {image_id}")
            abort(404)
        
        # If external URL present, redirect
        if img.url:
            logger.debug(f"Redirecting to external URL: {img.url}")
            return redirect(img.url)
        
        if img.data:
            logger.debug(f"Serving image from database: {img.filename}, {len(img.data)} bytes")
            return send_file(
                BytesIO(img.data), 
                mimetype=img.content_type or 'application/octet-stream', 
                download_name=img.filename
            )
        
        logger.warning(f"Image exists in database but has no data: {image_id}")
        abort(404)
    except Exception as e:
        logger.exception(f"Error serving image {image_id}: {str(e)}")
        abort(500)

@media.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    """Serve files from the uploads directory"""
    try:
        static_folder = current_app.static_folder
        file_path = os.path.join(static_folder, 'uploads', filename)
        
        if not os.path.exists(file_path):
            logger.warning(f"File not found on disk: {file_path}")
            abort(404)
            
        # Log file details for debugging
        file_size = os.path.getsize(file_path)
        logger.debug(f"Serving file: {file_path}, size: {file_size} bytes")
        
        # Get directory from filename
        base_filename = os.path.basename(filename)
        
        return send_file(file_path, download_name=base_filename)
    except Exception as e:
        logger.exception(f"Error serving uploaded file {filename}: {str(e)}")
        abort(500)
