import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.app import create_app
from app.models.product import Product, ProductImage
from app.models.database import db

app = create_app()
with app.app_context():
    static = app.static_folder
    # scan products and categories
    count = 0
    for p in Product.query.all():
        img = p.image or ''
        if img.startswith('/static/'):
            rel = img.replace('/static/', '', 1)
            path = os.path.join(static, rel)
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    data = f.read()
                filename = os.path.basename(path)
                pi = ProductImage(product_id=p.id, url=None, alt=filename, data=data, filename=filename, content_type='application/octet-stream')
                db.session.add(pi)
                db.session.flush()
                p.image = f'/media/image/{pi.id}'
                count += 1
    db.session.commit()
    print('Migrated', count, 'images to DB')
