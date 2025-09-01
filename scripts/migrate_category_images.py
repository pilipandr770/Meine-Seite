"""
Script to modify the Category model to store images in the database instead of the filesystem.
"""
import os
import sys
import logging
import requests
from io import BytesIO

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def modify_category_model():
    """Add a binary data column to the Category model."""
    from app import app
    from app.models.product import Category, db
    from flask_migrate import Migrate
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import LargeBinary, String
    
    with app.app_context():
        try:
            # Create a migration context
            migrate = Migrate(app, db)
            conn = db.engine.connect()
            ctx = MigrationContext.configure(conn)
            op = Operations(ctx)
            
            # Add the necessary columns to the Category model
            schema = os.environ.get('POSTGRES_SCHEMA_SHOP')
            table_name = 'categories'
            table_name_with_schema = f"{schema}.{table_name}" if schema else table_name
            
            try:
                op.add_column(table_name_with_schema, db.Column('image_data', LargeBinary))
                op.add_column(table_name_with_schema, db.Column('image_filename', String(255)))
                op.add_column(table_name_with_schema, db.Column('image_content_type', String(100)))
                logger.info(f"Added image_data, image_filename, and image_content_type columns to {table_name_with_schema}")
            except Exception as e:
                logger.warning(f"Failed to add columns: {e}")
                logger.info("Columns might already exist or there was an issue adding them.")
            
            # Update the Category model to include these fields
            if not hasattr(Category, 'image_data'):
                Category.image_data = db.Column(db.LargeBinary)
            if not hasattr(Category, 'image_filename'):
                Category.image_filename = db.Column(db.String(255))
            if not hasattr(Category, 'image_content_type'):
                Category.image_content_type = db.Column(db.String(100))
            
            logger.info("Category model updated successfully")
            
        except Exception as e:
            logger.error(f"Error modifying category model: {e}")
            return False
    
    return True

def migrate_category_images():
    """Migrate existing category images from filesystem/URLs to the database."""
    from app import app
    from app.models.product import Category, db
    
    with app.app_context():
        try:
            categories = Category.query.all()
            base_url = app.config.get('BASE_URL', 'https://meine-seite.onrender.com')
            
            for category in categories:
                if category.image and not category.image_data:
                    try:
                        logger.info(f"Migrating image for category {category.name}: {category.image}")
                        
                        # Check if it's a relative URL or absolute URL
                        image_url = category.image
                        if image_url.startswith('/'):
                            image_url = f"{base_url}{image_url}"
                        
                        # Fetch the image
                        logger.info(f"Fetching image from: {image_url}")
                        response = requests.get(image_url)
                        
                        if response.status_code == 200:
                            # Store the image data in the database
                            category.image_data = response.content
                            category.image_filename = os.path.basename(category.image)
                            category.image_content_type = response.headers.get('Content-Type', 'image/jpeg')
                            logger.info(f"Successfully migrated image for category {category.name}")
                        else:
                            logger.warning(f"Failed to fetch image for category {category.name}: status code {response.status_code}")
                    
                    except Exception as e:
                        logger.error(f"Error migrating image for category {category.name}: {e}")
            
            db.session.commit()
            logger.info("All category images migrated successfully")
            
        except Exception as e:
            logger.error(f"Error during migration: {e}")
            db.session.rollback()
            return False
    
    return True

def update_media_route():
    """Print instructions for updating the media route."""
    print("""
To complete the migration, add a new route to the media blueprint:

@media.route('/media/category-image/<int:category_id>')
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
    """)

def update_admin_shop_route():
    """Print instructions for updating the admin_shop route."""
    print("""
Update the admin_shop.py file to store category images in the database.
Replace the image handling in add_category and edit_category:

# In add_category/edit_category routes:
if 'image' in request.files:
    file = request.files['image']
    if file.filename:
        current_app.logger.info(f"Processing image upload for category: {name}")
        file.stream.seek(0)
        
        # Read file content
        binary = file.read()
        # Store image data in the Category model
        category.image_data = binary
        category.image_filename = secure_filename(file.filename)
        category.image_content_type = file.mimetype
        
        # Set the image URL to the serve_category_image route
        category.image = url_for('media.serve_category_image', category_id=category.id, _external=True)
    """)

def main():
    print("Starting category image migration...")
    
    # Step 1: Modify the Category model
    if not modify_category_model():
        print("Failed to modify Category model. Please check the error logs.")
        return
    
    # Step 2: Migrate existing images
    if not migrate_category_images():
        print("Failed to migrate category images. Please check the error logs.")
        return
    
    # Step 3: Provide instructions for updating routes
    print("\nCategory model modification and image migration completed!")
    print("\nFurther steps required:")
    update_media_route()
    update_admin_shop_route()
    
    print("\nMigration script completed successfully!")

if __name__ == "__main__":
    main()
