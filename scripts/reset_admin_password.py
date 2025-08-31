#!/usr/bin/env python3
"""Reset or create the local 'admin' user password.

Usage:
  python scripts/reset_admin_password.py "NewP@ssw0rd"

This script runs the app factory, finds or creates a user with username 'admin'
and sets its password using the application's User model helper.
"""
import sys
import logging
from pathlib import Path

# Ensure project root is on sys.path so `import app` works when running the script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.app import create_app
from app.models.user import User
from app.models.database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) < 2:
        logger.error('Usage: python scripts/reset_admin_password.py "<new_password>"')
        return 1

    new_password = sys.argv[1]
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin:
            admin.set_password(new_password)
            db.session.add(admin)
            logger.info('Updated existing admin password.')
        else:
            # Minimal required fields: email, username, password
            admin = User(email='admin@example.com', username='admin', password=new_password, is_admin=True)
            db.session.add(admin)
            logger.info('Created new admin user and set password.')

        db.session.commit()
        logger.info('Done. Admin password set.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
