import os
from flask import Flask, current_app
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='image_debug.log'
)
logger = logging.getLogger(__name__)

def check_uploads_structure():
    """Check the uploads directory structure and permissions"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        static_path = os.path.join(base_dir, 'app', 'static')
        uploads_path = os.path.join(static_path, 'uploads')
        categories_path = os.path.join(uploads_path, 'categories')
        products_path = os.path.join(uploads_path, 'products')
        
        # Check if directories exist
        logger.info(f"Static path exists: {os.path.exists(static_path)}")
        logger.info(f"Uploads path exists: {os.path.exists(uploads_path)}")
        logger.info(f"Categories path exists: {os.path.exists(categories_path)}")
        logger.info(f"Products path exists: {os.path.exists(products_path)}")
        
        # Check if directories are writable
        logger.info(f"Static path writable: {os.access(static_path, os.W_OK)}")
        logger.info(f"Uploads path writable: {os.access(uploads_path, os.W_OK)}")
        if os.path.exists(categories_path):
            logger.info(f"Categories path writable: {os.access(categories_path, os.W_OK)}")
        if os.path.exists(products_path):
            logger.info(f"Products path writable: {os.access(products_path, os.W_OK)}")
            
        # Try creating test files
        try:
            categories_test_file = os.path.join(categories_path, 'test_write.txt')
            with open(categories_test_file, 'w') as f:
                f.write('Test write to categories')
            logger.info(f"Successfully wrote test file to categories: {categories_test_file}")
            os.remove(categories_test_file)
            logger.info("Successfully removed test file")
        except Exception as e:
            logger.error(f"Failed to write test file to categories: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error checking uploads structure: {str(e)}")

if __name__ == "__main__":
    check_uploads_structure()
