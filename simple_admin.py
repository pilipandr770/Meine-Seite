#!/usr/bin/env python3
"""
Simple admin user creation
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

# Load environment
from dotenv import load_dotenv
load_dotenv()

from app.app import create_app
from app.models.user import User, db
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    try:
        # Check if admin user already exists
        existing_admin = User.query.filter_by(email='pilipandr79@icloud.com').first()
        if existing_admin:
            print("Admin user already exists!")
        else:
            # Create admin user
            admin_user = User(
                email='pilipandr79@icloud.com',
                username='admin',
                password='Dnepr75ok10',
                first_name='Admin',
                last_name='User',
                is_admin=True,
                is_active=True
            )

            db.session.add(admin_user)
            db.session.commit()

            print("✅ Admin user created successfully!")
            print("Email: pilipandr79@icloud.com")
            print("Password: Dnepr75ok10")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.session.rollback()
