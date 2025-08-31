#!/usr/bin/env python
"""
Simple database initialization for production deployment.
This script only creates tables if they don't exist, without dropping them.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

app_dir = os.path.join(current_dir, 'app')
if app_dir not in sys.path:
    sys.path.append(app_dir)

def init_database():
    """Initialize database for production - create tables without dropping."""
    try:
        from app.app import create_app
        from app.models.database import db

        logger.info("Creating Flask app for database initialization...")
        app = create_app()

        with app.app_context():
            logger.info("Creating database tables...")

            # Create all tables (this won't drop existing ones)
            db.create_all()
            logger.info("✅ All tables created successfully")

            # Create admin user if it doesn't exist
            try:
                from app.models.user import User
                from werkzeug.security import generate_password_hash

                existing_admin = User.query.filter_by(email='pilipandr79@icloud.com').first()
                if not existing_admin:
                    admin_user = User(
                        email='pilipandr79@icloud.com',
                        username='admin',
                        password='Dnepr75ok10',
                        first_name='Admin',
                        last_name='User',
                        is_admin=True
                    )
                    admin_user.is_active = True
                    db.session.add(admin_user)
                    db.session.commit()
                    logger.info("✅ Admin user created")
                else:
                    logger.info("Admin user already exists")
            except Exception as e:
                logger.error(f"Failed to create admin user: {e}")

        logger.info("✅ Database initialization completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
