"""
Updated utility functions to handle saving category images to the database
"""
import os
import uuid
from datetime import datetime
from PIL import Image
from io import BytesIO
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def save_category_image(file, category=None):
    """
    Save a category image to the database instead of the filesystem
    
    Args:
        file: The file object from the request
        category: Existing category object (if updating an existing category)
    
    Returns:
        image_url: The URL to serve the image from the database
        
    Note: This function updates the category object's image_data, image_content_type,
          and image_filename attributes but does NOT commit to the database.
          The caller must call db.session.commit() to save changes.
    """
    try:
        if not file:
            return None
        
        # Process the image with PIL for possible resizing/optimization
        img = Image.open(file)
        
        # Resize if needed (optional)
        max_size = (800, 800)  # Example max size
        img.thumbnail(max_size, Image.LANCZOS)
        
        # Save to BytesIO instead of filesystem
        img_byte_arr = BytesIO()
        
        # Determine format from original filename
        filename = file.filename
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Default to PNG if unknown extension
        img_format = 'JPEG' if file_ext in ['.jpg', '.jpeg'] else 'PNG'
        content_type = f'image/{img_format.lower()}'
        
        # Save to BytesIO with the appropriate format
        img.save(img_byte_arr, format=img_format, optimize=True)
        img_byte_arr.seek(0)
        
        # Generate a unique filename
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # Update the category object if provided
        if category:
            category.image_data = img_byte_arr.getvalue()
            category.image_content_type = content_type
            category.image_filename = unique_filename
            
            # Set the URL for accessing the image through the route
            return f'/media/category-image/{category.id}'
        
        # Return the binary data if no category provided (for further processing)
        return {
            'data': img_byte_arr.getvalue(),
            'content_type': content_type,
            'filename': unique_filename
        }
        
    except Exception as e:
        logger.exception(f"Error saving category image: {str(e)}")
        return None
