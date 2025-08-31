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
    # pick a product
    p = Product.query.first()
    if not p:
        print('No product found')
        exit(1)
    # create a tiny test image
    data = b'\x89PNG\r\n\x1a\n' + b'0' * 1024
    img = ProductImage(product_id=p.id, url=None, alt='test.png', data=data, filename='test.png', content_type='image/png')
    db.session.add(img)
    db.session.commit()
    p.image = f'/media/image/{img.id}'
    db.session.commit()
    print('Created image id', img.id, 'and assigned to product', p.id)
