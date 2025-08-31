import sys
import os
sys.path.append('.')
sys.path.append(os.path.dirname(__file__))

from app.models.database import db
from app.models.product import Product
from slugify import slugify
from app.app import create_app

app = create_app()
with app.app_context():
    products = Product.query.filter(Product.slug.is_(None)).all()
    print(f'Found {len(products)} products with null slugs')

    fixed_count = 0
    for product in products:
        if product.name:
            old_slug = product.slug
            new_slug = slugify(product.name)
            product.slug = new_slug
            print(f'Fixed product {product.id}: "{product.name}" -> slug: "{new_slug}"')
            fixed_count += 1

    if fixed_count > 0:
        db.session.commit()
        print(f'✅ Successfully fixed {fixed_count} products with null slugs')
    else:
        print('✅ No products with null slugs found')
