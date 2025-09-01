"""
Update the Category model to include database fields for storing image data
"""
from sqlalchemy import Column, LargeBinary, String
from app.models.database import db

# Add the following fields to the Category model class:
#   - image_data: LargeBinary to store the image binary data
#   - image_content_type: String to store the MIME type
#   - image_filename: String to store the filename

# This is a patch that should be applied to the existing Category model
# in app/models/product.py

"""
Example of how the Category model should look after these changes:

class Category(db.Model):
    # ... existing fields ...
    
    # Existing image URL field
    image = db.Column(db.String(255))
    
    # New fields for storing images in the database
    image_data = db.Column(db.LargeBinary)
    image_content_type = db.Column(db.String(100))
    image_filename = db.Column(db.String(255))
    
    # ... rest of the model ...
"""
