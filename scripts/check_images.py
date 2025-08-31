import json
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.app import create_app
from app.models.product import Product
from app.models.product import ProductImage
from urllib.parse import urlparse

app = create_app()
with app.app_context():
    products = Product.query.limit(50).all()
    out = []
    for p in products:
        img = p.image or ''
        fs_path = None
        exists = False
        if img.startswith('/static/'):
            static_rel = img.replace('/static/', '', 1)
            fs_path = os.path.join(app.static_folder, static_rel)
            exists = os.path.exists(fs_path)
        elif img.startswith('/media/image/'):
            # extract id and check DB
            try:
                parts = img.rstrip('/').split('/')
                image_id = int(parts[-1])
                pi = ProductImage.query.get(image_id)
                exists = bool(pi and (pi.data or pi.url))
            except Exception:
                exists = False
        out.append({
            'id': p.id,
            'name': p.name,
            'image': img,
            'file_path': fs_path,
            'exists': exists
        })
    print(json.dumps(out, ensure_ascii=False, indent=2))
