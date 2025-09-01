"""
Setup script for testing the database changes related to category images
"""
from app import create_app, db
from app.models.product import Category
import sys

def test_category_db_fields():
    """Test that the new Category model fields are available"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if we can access the new fields on a Category object
            category = Category.query.first()
            
            if not category:
                print("No categories found in database. Creating a test category.")
                category = Category(
                    name="Test Category",
                    slug="test-category",
                    description="Test category for DB field validation"
                )
                db.session.add(category)
                db.session.commit()
                print(f"Created test category with ID: {category.id}")
            
            # Check if new fields exist
            print(f"Testing new fields on Category ID: {category.id}")
            
            # Try to access the fields (will raise AttributeError if they don't exist)
            print(f"image_data field: {'Available' if hasattr(category, 'image_data') else 'Not available'}")
            print(f"image_content_type field: {'Available' if hasattr(category, 'image_content_type') else 'Not available'}")
            print(f"image_filename field: {'Available' if hasattr(category, 'image_filename') else 'Not available'}")
            
            # If we get here, the fields are accessible
            print("✅ All new Category fields are accessible")
            return True
            
        except AttributeError as e:
            print(f"❌ Missing field: {e}")
            print("You need to add the new fields to the Category model in app/models/product.py")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

if __name__ == "__main__":
    if test_category_db_fields():
        print("Database fields test passed. The migrate_category_images.py script should work correctly.")
        sys.exit(0)
    else:
        print("Database fields test failed. Please update the Category model before running migrate_category_images.py")
        sys.exit(1)
