#!/usr/bin/env python3
"""Print basic info about the 'admin' user from the local database."""
from pathlib import Path
import sys

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.app import create_app
from app.models.user import User

def main():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print('No admin user found (username="admin").')
            return 1
        print('id:', admin.id)
        print('username:', admin.username)
        print('email:', admin.email)
        print('is_admin:', bool(admin.is_admin))
        print('is_active:', bool(admin.is_active))
        return 0

if __name__ == '__main__':
    raise SystemExit(main())
