# create_tables_sqlite.py - create all SQLAlchemy tables using the app factory (SQLite/dev)
from app.app import create_app
from app.models.database import db

# Import likely models so metadata is registered
# Only import models that do not declare a specific PostgreSQL schema to avoid
# sqlite PRAGMA errors. We'll import commonly used tables; skip ClientRequest
# which uses 'rozoom_clients' schema.
safe_model_modules = [
    'app.models.client',
    'app.models.task',
    # Shop models (import if they exist and do not declare schema)
    'app.models.category',
    'app.models.product',
    'app.models.order',
    'app.models.coupon',
]

for m in safe_model_modules:
    try:
        mod = __import__(m, fromlist=['*'])
        # Skip modules that define tables with explicit 'schema' in __table_args__
        tbls = [getattr(mod, name) for name in dir(mod) if hasattr(getattr(mod, name), '__table__')]
        has_schema = False
        for t in tbls:
            table = getattr(t, '__table__', None)
            if table is not None and getattr(table, 'schema', None):
                has_schema = True
                break
        if has_schema:
            # don't import or register this module for sqlite create_all
            continue
    except Exception:
        # ignore missing modules
        pass

app = create_app()
with app.app_context():
    db.create_all()
    print('db.create_all() executed')
