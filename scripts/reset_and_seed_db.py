"""Reset local SQLite DB (development) and seed sample categories and products.

WARNING: This script drops all tables in the configured database. Use only in local
development when DATABASE_URL points to a local SQLite file.
"""
import os
import sys
from pathlib import Path
from decimal import Decimal

# Ensure repo root is on sys.path so `import app` works when running the script
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# If running locally for seeding, ensure Postgres schema env vars don't force schema usage
for _k in ('POSTGRES_SCHEMA', 'POSTGRES_SCHEMA_CLIENTS', 'POSTGRES_SCHEMA_SHOP'):
    if _k in os.environ:
        os.environ.pop(_k)

from app.app import create_app
from app.models.database import db
# Use the canonical shop models that admin routes import
from app.models.product import Category, Product
from app.models.user import User


def main():
    app = create_app()
    with app.app_context():
        # Safety check: only allow when using sqlite/local file
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if not db_uri or 'sqlite' not in db_uri:
            print('Refusing to reset DB: not using SQLite. SQLALCHEMY_DATABASE_URI=', db_uri)
            sys.exit(1)

        # Drop and recreate all tables
        print('Dropping all tables...')
        # SQLite does not support schema-qualified table names; clear any schema on Table metadata
        if 'sqlite' in db_uri:
            for tbl in list(db.metadata.tables.values()):
                if getattr(tbl, 'schema', None):
                    tbl.schema = None
        db.drop_all()
        print('Creating tables...')
        db.create_all()

        # Create admin user if missing
        admin_email = 'admin@example.com'
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            # User.__init__(email, username, password, ...)
            admin = User(email=admin_email, username='admin', password='MyNewStrongP@ssw0rd!', is_admin=True)
            # ensure active flag
            admin.is_active = True
            db.session.add(admin)
            print('Created admin user with email', admin_email)
        else:
            # Update existing admin: set password, ensure admin and active flags
            admin.set_password('MyNewStrongP@ssw0rd!')
            admin.is_admin = True
            admin.is_active = True
            db.session.add(admin)
            print('Updated admin password and flags for', admin_email)

        # Seed categories and products (hour packages)
        print('Seeding categories and products...')
        cat = Category(name='Hours', slug='hours', description='Пакеты часов для консультаций')
        db.session.add(cat)
        db.session.commit()

        p1 = Product(
            name='1 hour',
            slug='1-hour',
            price=Decimal('50.00'),
            category_id=cat.id,
            description='One hour session',
        )
        p1.sku = 'HOUR-1'
        # Ensure seeded products have stock so add-to-cart checks pass
        p1.stock = 10
        p1.in_stock = True
        p2 = Product(
            name='5 hours',
            slug='5-hours',
            price=Decimal('225.00'),
            category_id=cat.id,
            description='Five hour bundle',
        )
        p2.sku = 'HOUR-5'
        p2.stock = 5
        p2.in_stock = True
        db.session.add_all([p1, p2])
        db.session.commit()

        print('Seed complete. Admin credentials: admin@example.com / MyNewStrongP@ssw0rd!')


if __name__ == '__main__':
    main()
