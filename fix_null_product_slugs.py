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
    # Find all products with null slugs
    products_with_null_slugs = Product.query.filter(Product.slug.is_(None)).all()
    print(f'Found {len(products_with_null_slugs)} products with null slugs')

    fixed_count = 0
    for product in products_with_null_slugs:
        if product.name:
            # Generate a slug from the product name
            new_slug = slugify(product.name)
            product.slug = new_slug
            print(f'Fixed product {product.id}: "{product.name}" -> slug: "{new_slug}"')
            fixed_count += 1
        else:
            print(f'Product {product.id} has no name, cannot generate slug')

    if fixed_count > 0:
        try:
            db.session.commit()
            print(f'✅ Successfully fixed {fixed_count} products with null slugs')
        except Exception as e:
            db.session.rollback()
            print(f'❌ Error committing changes: {e}')
    else:
        print('✅ No products with null slugs found')
