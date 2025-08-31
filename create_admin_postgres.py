#!/usr/bin/env python3
"""
Script to create an admin user for the Flask application
"""
import os
import sys
from werkzeug.security import generate_password_hash

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Add app directory to path
app_dir = os.path.join(current_dir, 'app')
if app_dir not in sys.path:
    sys.path.append(app_dir)

def create_admin():
    """Create an admin user using Flask application context"""
    print("Loading environment variables...")
    from dotenv import load_dotenv
    load_dotenv()
    print("Env loaded")
    
    print("Starting admin creation...")
    from app.app import create_app
    from app.models.user import User, db

    print("Creating app...")
    app = create_app()

    print("Entering app context...")
    with app.app_context():
        try:
            print("Checking for existing admin...")
            # Check if admin user already exists
            existing_admin = User.query.filter_by(email='pilipandr79@icloud.com').first()
            if existing_admin:
                print("Admin user already exists!")
                return

            print("Creating admin user...")
            # Create admin user
            admin_user = User(
                email='pilipandr79@icloud.com',
                username='admin',
                password_hash=generate_password_hash('Dnepr75ok10'),
                first_name='Admin',
                last_name='User',
                is_admin=True,
                is_active=True
            )

            print("Adding to session...")
            db.session.add(admin_user)
            print("Committing...")
            db.session.commit()

            print("✅ Admin user created successfully!")
            print("Email: pilipandr79@icloud.com")
            print("Password: Dnepr75ok10")
            print("Username: admin")

        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    create_admin()
