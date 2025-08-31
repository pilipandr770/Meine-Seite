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
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)

    def __init__(self, *args, **kwargs):
        if 'slug' not in kwargs and 'name' in kwargs:
            kwargs['slug'] = slugify(kwargs.get('name', ''))
        super(Category, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'
    __table_args__ = {'schema': _SHOP_SCHEMA} if _USE_SHOP_SCHEMA else {}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    sku = db.Column(db.String(50), unique=True)
    short_description = db.Column(db.Text)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    sale_price = db.Column(db.Float)
    image = db.Column(db.String(255))
    # Numeric stock count used across admin/shop logic
    stock = db.Column(db.Integer, default=0)
    duration = db.Column(db.Integer)  # Duration in minutes
    format = db.Column(db.String(100))  # e.g., "Video call", "In person"
    language = db.Column(db.String(50))  # e.g., "English", "German", "Ukrainian"
    prerequisites = db.Column(db.Text)
    includes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    stripe_url = db.Column(db.String(255))  # Stripe payment URL
    is_featured = db.Column(db.Boolean, default=False)
    in_stock = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    category_id = db.Column(db.Integer, db.ForeignKey(f'{_SHOP_SCHEMA}.categories.id' if _USE_SHOP_SCHEMA else 'categories.id'))

    # Relationships
    gallery_images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('ProductReview', backref='product', lazy=True, cascade='all, delete-orphan')

    def __init__(self, *args, **kwargs):
        if 'slug' not in kwargs and 'name' in kwargs:
            kwargs['slug'] = slugify(kwargs.get('name', ''))
        if 'sku' not in kwargs:
            kwargs['sku'] = str(uuid.uuid4()).split('-')[0].upper()
        if 'stock' not in kwargs:
            # Set default stock to None to indicate unlimited stock
            kwargs['stock'] = None
        if 'is_active' not in kwargs:
            kwargs['is_active'] = True
        if 'in_stock' not in kwargs:
            kwargs['in_stock'] = True
        super(Product, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'<Product {self.name}>'

    @hybrid_property
    def average_rating(self):
        approved = [r for r in self.reviews if getattr(r, 'is_approved', True)]
        if not approved:
            return 0
        return sum(r.rating for r in approved) / len(approved)


class ProductImage(db.Model):
    __tablename__ = 'product_images'
    __table_args__ = {'schema': _SHOP_SCHEMA} if _USE_SHOP_SCHEMA else {}

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey(f'{_SHOP_SCHEMA}.products.id' if _USE_SHOP_SCHEMA else 'products.id'), nullable=False)
    # URL is optional - we will support serving images from DB via /media/image/<id>
    url = db.Column(db.String(255))
    alt = db.Column(db.String(255))
    # Binary data stored in DB for portability across deployments
    data = db.Column(db.LargeBinary)
    filename = db.Column(db.String(255))
    content_type = db.Column(db.String(100))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ProductImage {self.id} for Product {self.product_id}>'


class ProductReview(db.Model):
    __tablename__ = 'product_reviews'
    __table_args__ = {'schema': _SHOP_SCHEMA} if _USE_SHOP_SCHEMA else {}

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey(f'{_SHOP_SCHEMA}.products.id' if _USE_SHOP_SCHEMA else 'products.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    author_name = db.Column(db.String(100), nullable=True)
    author_email = db.Column(db.String(100), nullable=True)
    content = db.Column(db.Text, nullable=True)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ProductReview {self.id} for Product {self.product_id}>'
