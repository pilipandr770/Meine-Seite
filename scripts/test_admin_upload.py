"""Test script: programmatic admin login and multipart image upload to /admin/products/1/edit

This script uses Flask's test client to:
- Ensure local seed data exists (calls reset_and_seed_db)
- Log in as admin via the login form
- Submit the edit product form for product id 1 with an attached image
- Print DB findings about created ProductImage rows
"""
import re
import io
from pprint import pprint
import sys
from pathlib import Path

# Ensure repo root is on sys.path so `import app` works when running the script
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.app import create_app
from app.models.product import Product, ProductImage, Category

# Reuse the seed helper to ensure predictable data
from scripts.reset_and_seed_db import main as seed_main


def main():
    print('Starting test_admin_upload...')
    app = create_app()

    # Ensure seeded data exists (safe for local sqlite dev)
    with app.app_context():
        try:
            seed_main()
        except SystemExit:
            # seed_main may call sys.exit if DB not sqlite; ignore in that case
            pass

    with app.test_client() as client:
        print('Created test client')
        # Get login page to obtain CSRF token in session/form
        r = client.get('/auth/login')
        html = r.get_data(as_text=True)
        m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
        csrf = m.group(1) if m else ''
        print('Got csrf for login:', bool(csrf))

        # Post login
        login_resp = client.post('/auth/login', data={
            'email': 'admin@example.com',
            'password': 'MyNewStrongP@ssw0rd!',
            'csrf_token': csrf
        }, follow_redirects=True)
        print('Login response code:', login_resp.status_code)

        # Fetch edit page for product 1 to get form CSRF and current values
        edit_get = client.get('/admin/products/1/edit')
        if edit_get.status_code != 200:
            print('Failed to load edit page for product 1; status', edit_get.status_code)
            return
        edit_html = edit_get.get_data(as_text=True)
        m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', edit_html)
        edit_csrf = m.group(1) if m else ''
        print('Got csrf for edit form:', bool(edit_csrf))

        # Prepare form data using current product values to satisfy validators
        with app.app_context():
            p = Product.query.get(1)
            if not p:
                print('Product 1 not found; aborting')
                return
            cat = Category.query.first()
            if not cat:
                print('No category found; aborting')
                return

            form_data = {
                'name': p.name or 'Test Product',
                'short_description': p.short_description or 'Short desc',
                'description': p.description or 'Full desc',
                'price': str(p.price or '10.0'),
                'sale_price': str(p.sale_price or ''),
                'stock': str(p.stock or 1),
                'category_id': str(p.category_id or cat.id),
                'duration': str(p.duration or ''),
                'is_virtual': 'y' if getattr(p, 'is_virtual', False) else '',
                'is_active': 'y' if getattr(p, 'is_active', True) else '',
                'is_featured': 'y' if getattr(p, 'is_featured', False) else '',
                'csrf_token': edit_csrf
            }

        # Attach a small in-memory image file
        img = (io.BytesIO(b"test image bytes for admin upload"), 'admin_test.jpg')

        # The test client expects file tuples inside the data mapping for multipart
        multipart = dict(form_data)
        multipart['image'] = img

        post_resp = client.post('/admin/products/1/edit', data=multipart, content_type='multipart/form-data', follow_redirects=True)
        print('POST edit response code:', post_resp.status_code)

        # Inspect DB for new ProductImage records for product 1
        with app.app_context():
            imgs = ProductImage.query.filter_by(product_id=1).order_by(ProductImage.id.desc()).limit(5).all()
            print('Found', len(imgs), 'images for product 1')
            for im in imgs:
                print('Image id:', im.id, 'filename:', getattr(im, 'filename', None), 'has_data:', bool(getattr(im, 'data', None)), 'url:', getattr(im, 'url', None))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        print('Exception during test_admin_upload:')
        traceback.print_exc()
        raise
