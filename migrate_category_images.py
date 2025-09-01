"""
Migration script to move category images from filesystem to database
"""
import os
import sys
from io import BytesIO
from flask import url_for
from datetime import datetime

# Add the parent directory to sys.path to allow importing app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.database import db
from app.models.product import Category

def migrate_category_images():
    """Migrate existing category images from filesystem to database"""
    print("Starting category image migration...")
    app = create_app()
    
    with app.app_context():
        # Modify Category model - Ensure needed columns exist
        # Note: In production, you'd use a proper migration tool like Alembic
        try:
            inspector = db.inspect(db.engine)
            category_columns = [col['name'] for col in inspector.get_columns('categories')]
            
            # Check if we need to add new columns
            needed_columns = {
                'image_data': db.LargeBinary,
                'image_content_type': db.String(100),
                'image_filename': db.String(255)
            }
            
            for col_name, col_type in needed_columns.items():
                if col_name not in category_columns:
                    print(f"Adding column {col_name} to categories table")
                    db.engine.execute(f"ALTER TABLE categories ADD COLUMN {col_name} {col_type.__visit_name__}")
            
            print("✅ Schema updated successfully")
        except Exception as e:
            print(f"❌ Error updating schema: {e}")
            return

        # Get all categories with images
        categories = Category.query.filter(Category.image.isnot(None)).all()
        print(f"Found {len(categories)} categories with images to migrate")

        migrated_count = 0
        for category in categories:
            try:
                if not category.image or not category.image.startswith('/static/'):
                    continue
                
                # Extract the image path from URL
                relative_path = category.image.replace('/static', '')
                full_path = os.path.join(app.static_folder, relative_path[1:])
                
                if not os.path.exists(full_path):
                    print(f"❌ Image file not found: {full_path}")
                    continue
                
                # Read the image file
                with open(full_path, 'rb') as f:
                    image_data = f.read()
                
                # Update the category with the binary data
                filename = os.path.basename(full_path)
                content_type = 'image/jpeg' if filename.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
                
                category.image_data = image_data
                category.image_content_type = content_type
                category.image_filename = filename
                
                # Update the category's image URL to point to the new route
                # Use the new blueprint name in the URL
                category.image = f'/category_media/category-image/{category.id}'
                
                print(f"✅ Migrated image for category: {category.name}, ID: {category.id}")
                migrated_count += 1
                
            except Exception as e:
                print(f"❌ Error migrating image for category {category.id}: {e}")
        
        # Commit the changes
        try:
            db.session.commit()
            print(f"✅ Successfully migrated {migrated_count} category images to the database")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error committing changes: {e}")

if __name__ == "__main__":
    migrate_category_images()
