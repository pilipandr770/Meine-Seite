#!/usr/bin/env python3
"""
Test login functionality
"""
import os
import sys

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

app_dir = os.path.join(current_dir, 'app')
if app_dir not in sys.path:
    sys.path.append(app_dir)

from app.app import create_app
from app.models.database import db
from app.models.user import User
from werkzeug.security import check_password_hash

app = create_app()

with app.app_context():
    try:
        print("Testing user lookup...")
        user = User.query.filter_by(email='admin@example.com').first()
        if user:
            print(f"User found: {user.email}")
            print(f"Username: {user.username}")
            print(f"Is admin: {user.is_admin}")
            print(f"Is active: {user.is_active}")
            print(f"Password hash check: {check_password_hash(user.password_hash, 'admin123')}")
        else:
            print("User not found")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
