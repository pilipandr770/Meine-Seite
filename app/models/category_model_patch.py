"""
This is a patch file to update the Category model with new fields for storing images in the database.
Apply these changes to app/models/product.py
"""
from app.models.database import db
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from slugify import slugify
import uuid
import os

# Schema guard: only set schema when using Postgres and POSTGRES_SCHEMA_SHOP is set
_SHOP_SCHEMA = os.environ.get('POSTGRES_SCHEMA_SHOP')
# More reliable check for PostgreSQL - check for postgres in DATABASE_URL or DATABASE_URI
_db_url = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_URI') or ''
_USE_SHOP_SCHEMA = bool(_SHOP_SCHEMA and ('postgres' in _db_url or 'postgresql' in _db_url))

class Category(db.Model):
    __tablename__ = 'categories'
    __table_args__ = {'schema': _SHOP_SCHEMA} if _USE_SHOP_SCHEMA else {}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    # New fields for storing image data directly in the database
    image_data = db.Column(db.LargeBinary)
    image_content_type = db.Column(db.String(100))
    image_filename = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)

    def __init__(self, *args, **kwargs):
        # Existing initialization code goes here
        pass
