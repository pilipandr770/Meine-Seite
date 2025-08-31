#!/usr/bin/env python3
"""Verify candidate passwords against local admin user.

Usage:
  python scripts/verify_admin_password.py "password1" "password2" ...
"""
import sys
from pathlib import Path

# ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.app import create_app
from app.models.user import User

def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/verify_admin_password.py "password1" "password2" ...')
        return 2

    candidates = sys.argv[1:]
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print('No admin user found.')
            return 1
        for p in candidates:
            ok = admin.check_password(p)
            print(f'Password: {p!r} -> match: {ok}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
