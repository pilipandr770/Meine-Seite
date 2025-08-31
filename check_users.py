#!/usr/bin/env python3
"""
Check database for users
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

app = create_app()

with app.app_context():
    try:
        print("Checking User table...")
        table_exists = User.__table__.exists(db.engine)
        print(f"User table exists: {table_exists}")
        
        if table_exists:
            users = User.query.all()
            print(f"Users found: {len(users)}")
            for user in users:
                print(f"  - {user.email} (admin: {user.is_admin})")
        else:
            print("User table does not exist")
            
    except Exception as e:
        print(f"Error: {e}")
