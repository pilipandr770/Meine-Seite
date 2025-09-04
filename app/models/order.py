import os
from app.models.database import db

_SHOP_SCHEMA = os.environ.get('POSTGRES_SCHEMA_SHOP')
# More reliable check for PostgreSQL - check for postgres in DATABASE_URL or DATABASE_URI
_db_url = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_URI') or ''
_USE_SHOP_SCHEMA = bool(_SHOP_SCHEMA and ('postgres' in _db_url or 'postgresql' in _db_url))
from datetime import datetime
import enum
from sqlalchemy.ext.hybrid import hybrid_property

class OrderStatus(enum.Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'

class PaymentStatus(enum.Enum):
    PENDING = 'pending'
    PAID = 'paid'
    FAILED = 'failed'
    REFUNDED = 'refunded'
    AWAITING_PAYMENT = 'awaiting_payment'

class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = {'schema': _SHOP_SCHEMA} if _USE_SHOP_SCHEMA else {}
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50))
    address_line1 = db.Column(db.String(255))
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(2))
    
    payment_method = db.Column(db.String(50), nullable=False)
    payment_status = db.Column(
        db.Enum(PaymentStatus, values_callable=lambda obj: [e.value for e in obj]), 
        default=PaymentStatus.PENDING.value
    )
    payment_reference = db.Column(db.String(255))  # Reference ID from payment gateway
    
    order_status = db.Column(
        db.Enum(OrderStatus, values_callable=lambda obj: [e.value for e in obj]), 
        default=OrderStatus.PENDING.value
    )
    
    subtotal = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0.0)
    tax = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, nullable=False)
    
    notes = db.Column(db.Text)
    
    coupon_id = db.Column(db.Integer, db.ForeignKey(f'{_SHOP_SCHEMA}.coupons.id' if _USE_SHOP_SCHEMA else 'coupons.id'))
    coupon_code = db.Column(db.String(50))
    
    user_id = db.Column(db.Integer, db.ForeignKey('rozoom_schema.users.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='selectin', cascade='all, delete-orphan')
    # Back-populates for user relation (defined in User)
    user = db.relationship('User', back_populates='orders')
    
    @property
    def country_name(self):
        # Dictionary of country codes to country names
        countries = {
            'DE': 'Germany',
            'AT': 'Austria',
            'CH': 'Switzerland',
            'UA': 'Ukraine',
            'PL': 'Poland',
            'GB': 'United Kingdom',
            'US': 'United States',
            'CA': 'Canada',
            'FR': 'France',
            'IT': 'Italy',
            'ES': 'Spain',
            'NL': 'Netherlands',
            'BE': 'Belgium',
            'SE': 'Sweden',
            'NO': 'Norway',
            'DK': 'Denmark',
            'FI': 'Finland',
            'CZ': 'Czech Republic',
            'SK': 'Slovakia',
            'HU': 'Hungary',
            'RO': 'Romania',
            'BG': 'Bulgaria',
            'GR': 'Greece'
        }
        return countries.get(self.country, self.country)
    
    @property
    def invoice_url(self):
        # In a real application, this would return a URL to a generated invoice
        # For now, just return None
        return None
    
    @property
    def delivery_address(self):
        if not self.address_line1:
            return None
        return {
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'postal_code': self.postal_code,
            'city': self.city,
            'country_name': self.country_name
        }
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

    @hybrid_property
    def status(self):
        """Expose a simple 'status' attribute used by admin routes.

        For queries and assignments the app expects `Order.status` to exist
        (e.g. filter(Order.status == 'paid')). Map that to the
        payment_status column which contains values like 'paid'.
        """
        return self.payment_status

    @status.setter
    def status(self, value):
        # When admin sets a status like 'paid' treat it as a payment status.
        # Future: could route other values to order_status when needed.
        self.payment_status = value

    @status.expression
    def status(cls):
        return cls.payment_status

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    __table_args__ = {'schema': _SHOP_SCHEMA} if _USE_SHOP_SCHEMA else {}
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey(f'{_SHOP_SCHEMA}.orders.id' if _USE_SHOP_SCHEMA else 'orders.id'), nullable=False)
    
    product_id = db.Column(db.Integer, db.ForeignKey(f'{_SHOP_SCHEMA}.products.id' if _USE_SHOP_SCHEMA else 'products.id'))
    product_name = db.Column(db.String(255), nullable=False)
    product_slug = db.Column(db.String(255))
    product_duration = db.Column(db.Integer)  # Duration in minutes
    
    price_per_unit = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    total_price = db.Column(db.Float, nullable=False)
    # Для поэтапной оплаты проектов
    project_stage_id = db.Column(db.Integer, nullable=True, index=True)
    billed_hours = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<OrderItem {self.id} for Order {self.order_id}>'


class Payment(db.Model):
    __tablename__ = 'payments'
    __table_args__ = {'schema': _SHOP_SCHEMA} if _USE_SHOP_SCHEMA else {}

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey(f'{_SHOP_SCHEMA}.orders.id' if _USE_SHOP_SCHEMA else 'orders.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='EUR')
    status = db.Column(db.String(50), default='pending')
    provider = db.Column(db.String(50))
    provider_payment_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship('Order', backref=db.backref('payment', uselist=False))

    def __repr__(self):
        return f'<Payment {self.id} for Order {self.order_id}>'

# Runtime migrations for order_items new columns
try:
    from app.models.database import db as _db_for_order
    engine = _db_for_order.get_engine()
    with engine.connect() as conn:
        table_name = f"{_SHOP_SCHEMA + '.' if _USE_SHOP_SCHEMA else ''}order_items"
        conn.execute(_db_for_order.text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS project_stage_id INTEGER"))
        conn.execute(_db_for_order.text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS billed_hours INTEGER DEFAULT 0"))
except Exception:
    pass
