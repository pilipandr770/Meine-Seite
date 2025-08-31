#!/usr/bin/env python3
"""
Create admin user using SQLAlchemy
"""
import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

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

# Import database functions
from app.models.database import get_postgres_uri, create_db_engine
from sqlalchemy import text

# Create engine
uri = get_postgres_uri()
engine = create_db_engine(uri, schema='rozoom_clients,rozoom_shop,rozoom_schema')

with engine.connect() as conn:
    # Set search path
    conn.execute(text("SET search_path TO rozoom_clients,rozoom_shop,rozoom_schema"))
    conn.commit()

    # Check if user exists
    result = conn.execute(text("SELECT id FROM rozoom_schema.users WHERE email = :email"), {'email': 'pilipandr79@icloud.com'})
    if result.fetchone():
        print("Admin user already exists!")
    else:
        # Create admin user
        password_hash = generate_password_hash('Dnepr75ok10')
        conn.execute(text("""
            INSERT INTO rozoom_schema.users (email, username, password_hash, first_name, last_name, is_admin, is_active, created_at)
            VALUES (:email, :username, :password_hash, :first_name, :last_name, :is_admin, :is_active, :created_at)
        """), {
            'email': 'pilipandr79@icloud.com',
            'username': 'admin',
            'password_hash': password_hash,
            'first_name': 'Admin',
            'last_name': 'User',
            'is_admin': True,
            'is_active': True,
            'created_at': datetime.utcnow()
        })
        conn.commit()
        print("✅ Admin user created successfully!")
        print("Email: pilipandr79@icloud.com")
        print("Password: Dnepr75ok10")
