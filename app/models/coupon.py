import os
from app.models.database import db
from datetime import datetime

_SHOP_SCHEMA = os.environ.get('POSTGRES_SCHEMA_SHOP')
# More reliable check for PostgreSQL - check for postgres in DATABASE_URL or DATABASE_URI
_db_url = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_URI') or ''
_USE_SHOP_SCHEMA = bool(_SHOP_SCHEMA and ('postgres' in _db_url or 'postgresql' in _db_url))

class Coupon(db.Model):
    __tablename__ = 'coupons'
    __table_args__ = {'schema': _SHOP_SCHEMA} if _USE_SHOP_SCHEMA else {}
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    discount_type = db.Column(db.String(20), nullable=False)  # 'percentage' or 'fixed'
    discount_value = db.Column(db.Float, nullable=False)  # percentage or amount
    
    valid_from = db.Column(db.DateTime)
    valid_to = db.Column(db.DateTime)
    
    usage_limit = db.Column(db.Integer)  # Maximum number of times this coupon can be used
    times_used = db.Column(db.Integer, default=0)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='coupon', lazy=True)
    
    @property
    def is_expired(self):
        if not self.valid_to:
            return False
        return datetime.utcnow() > self.valid_to
    
    @property
    def is_valid(self):
        if not self.is_active:
            return False
        
        if self.is_expired:
            return False
        
        if self.valid_from and datetime.utcnow() < self.valid_from:
            return False
        
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False
        
        return True
    
    def __repr__(self):
        return f'<Coupon {self.code}>'
