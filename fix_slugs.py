import sys
import os
sys.path.append('.')
sys.path.append(os.path.dirname(__file__))

from app.models.database import db, init_db
from app.models.product import Product
from slugify import slugify
from app.app import create_app

app = create_app()
with app.app_context():
    products = Product.query.filter(Product.slug.is_(None)).all()
    print(f'Found {len(products)} products with null slugs')
    for product in products:
        if product.name:
            old_slug = product.slug
            product.slug = slugify(product.name)
            print(f'Fixed product {product.id}: "{product.name}" -> slug: "{product.slug}"')
        else:
            print(f'Product {product.id} has no name, cannot generate slug')
    if products:
        db.session.commit()
        print('✅ Committed slug fixes')
    else:
        print('✅ No products with null slugs found')
