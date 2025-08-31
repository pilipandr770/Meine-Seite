import os, sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.app import create_app
from app.models.product import Product

app = create_app()
with app.app_context():
    print('Product count:', Product.query.count())
