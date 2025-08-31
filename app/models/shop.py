"""Cart models for the shop domain.

Only Cart and CartItem live here. Other shop models (Category, Product, Order, Coupon)
live in their own modules (`product.py`, `order.py`, `coupon.py`) to avoid duplicate
SQLAlchemy Table definitions.
"""

from app.models.database import db
import os
from datetime import datetime

# Shop schema guard: only set schema when using Postgres and POSTGRES_SCHEMA_SHOP is set
_SHOP_SCHEMA = os.environ.get('POSTGRES_SCHEMA_SHOP')
# More reliable check for PostgreSQL - check for postgres in DATABASE_URL or DATABASE_URI
_db_url = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_URI') or ''
_USE_SHOP_SCHEMA = bool(_SHOP_SCHEMA and ('postgres' in _db_url or 'postgresql' in _db_url))


class Cart(db.Model):
    __tablename__ = 'carts'
    __table_args__ = {'schema': _SHOP_SCHEMA} if _USE_SHOP_SCHEMA else {}

    id = db.Column(db.Integer, primary_key=True)
    # session_id is only required for guest carts; allow null for user-owned carts
    session_id = db.Column(db.String(128), unique=True, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('rozoom_schema.users.id'), nullable=True)
    # Cart status: 'open' or 'closed'
    status = db.Column(db.String(20), default='open', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('CartItem', backref='cart', lazy=True, cascade='all, delete-orphan')

    def total(self):
        return sum(item.line_total() for item in self.items)

    @property
    def subtotal(self):
        """Compatibility property: subtotal of the cart used by templates and checkout.

        Returns a float sum of each item's subtotal/line_total.
        """
        try:
            return sum(getattr(item, 'subtotal', item.line_total()) for item in self.items)
        except Exception:
            return 0.0


class CartItem(db.Model):
    __tablename__ = 'cart_items'
    __table_args__ = {'schema': _SHOP_SCHEMA} if _USE_SHOP_SCHEMA else {}

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey(f'{_SHOP_SCHEMA}.carts.id' if _USE_SHOP_SCHEMA else 'carts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey(f'{_SHOP_SCHEMA}.products.id' if _USE_SHOP_SCHEMA else 'products.id'), nullable=False)
    # Relationship to Product so templates and routes can use `item.product`
    product = db.relationship('Product', lazy=True)
    quantity = db.Column(db.Integer, default=1)
    # Store price at time of adding to cart so totals don't change if product price updates
    price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def line_total(self):
        # product.price may be Decimal or Numeric; convert for calculation
        # Prefer the cart item's stored price; fall back to product price
        price = getattr(self, 'price', None) or getattr(self.product, 'price', 0) or 0
        try:
            return float(price) * int(self.quantity)
        except Exception:
            return 0

    @property
    def subtotal(self):
        """Compatibility property used by checkout and templates."""
        return self.line_total()
