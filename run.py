#!/usr/bin/env python
"""
Run script for the application.
Use this script to run from the project root directory.
This is the entry point for Gunicorn in production.
"""

import os
import sys
import logging

# Load environment variables from .env file FIRST, before any other imports
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger = logging.getLogger(__name__)
    logger.info("Loaded environment variables from .env file")
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("python-dotenv not installed, .env file not loaded")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Add app directory to path
app_dir = os.path.join(current_dir, 'app')
if app_dir not in sys.path:
    sys.path.append(app_dir)

logger.info("Initializing Flask application...")

# Create the app instance for Gunicorn to import
from app.app import create_app
app = create_app()
logger.info(f"Flask application initialized with config: {app.config['ENVIRONMENT'] if 'ENVIRONMENT' in app.config else 'default'}")

# Create admin user if it doesn't exist
with app.app_context():
    try:
        from app.models.user import User
        from app.models.database import db
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
            admin_user.is_active = True  # Set is_active after creation
            db.session.add(admin_user)
            db.session.commit()
            logger.info("✅ Admin user created: pilipandr79@icloud.com")
        else:
            logger.info("Admin user already exists")
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")

# Run the app if executed directly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    logger.info(f"Running Flask app on port {port} with debug={debug}")
    app.run(host="0.0.0.0", port=port, debug=debug)
