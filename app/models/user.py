"""User model for authentication and authorization."""
from app.models.database import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import uuid

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'rozoom_schema'}
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    
    # Relations
    # Eager load with selectin to minimize per-order lazy queries while keeping separate SELECT
    orders = db.relationship('Order', back_populates='user', lazy='selectin')
    cart = db.relationship('Cart', backref='user', lazy=True, uselist=False)
    projects = db.relationship('Project', backref='user', lazy=True, foreign_keys='Project.user_id')
    
    def __init__(self, email, username, password, first_name=None, last_name=None, is_admin=False):
        self.email = email.lower()
        self.username = username
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.is_admin = is_admin
        
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def generate_reset_token(self):
        self.reset_token = str(uuid.uuid4())
        self.reset_token_expiry = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        return self.reset_token
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
