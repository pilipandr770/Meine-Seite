import os
import sys
from flask import Flask, current_app
import logging

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Test function to fix stock issues
def fix_stock_issues():
    try:
        # Import app context
        from app.app import create_app
        from app.models.database import db
        from app.models.product import Product

        app = create_app()
        
        with app.app_context():
            # Update all products to have a large stock value
            products = Product.query.all()
            print(f"Found {len(products)} products to update")
            
            for product in products:
                product.stock = 999  # Set a large stock value
                product.in_stock = True  # Ensure in_stock flag is True
            
            db.session.commit()
            print("All products updated with stock=999 and in_stock=True")
            print("Please restart the Flask application for changes to take effect.")
    except Exception as e:
        print(f"Error fixing stock issues: {str(e)}")

# Original test function
def test_file_saving():
    # Create a test file
    test_content = b'Test content for file'
    file = MockFile(test_content, 'test_image.jpg', 'image/jpeg')
    
    # This simulates what happens in your code
    print("Reading file content...")
    content = file.read()
    print(f"Content length: {len(content)}")
    
    # Without reset, this would save an empty file
    print("Trying to save without reset...")
    save_path = os.path.join(os.getcwd(), 'test_output_without_reset.jpg')
    file.save(save_path)
    
    # Now reset the file position and try again
    print("Resetting file position...")
    file = MockFile(test_content, 'test_image.jpg', 'image/jpeg')  # Recreate file object
    
    # Try to save again after reset
    
if __name__ == "__main__":
    fix_stock_issues()
    print("Saving with fresh file object...")
    save_path = os.path.join(os.getcwd(), 'test_output_with_reset.jpg')
    file.save(save_path)
    
    # Check results
    try:
        print("\nResults:")
        print(f"Without reset file size: {os.path.getsize(os.path.join(os.getcwd(), 'test_output_without_reset.jpg'))}")
        print(f"With reset file size: {os.path.getsize(os.path.join(os.getcwd(), 'test_output_with_reset.jpg'))}")
    except Exception as e:
        print(f"Error checking file sizes: {e}")

if __name__ == "__main__":
    test_file_saving()
