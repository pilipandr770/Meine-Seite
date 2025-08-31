import os
import sys
# Ensure project root is on sys.path when running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.models.database import db
from app.models.product import Product, Category
from app.models.shop import Cart, CartItem
from app.models.user import User

app = create_app()

with app.app_context():
    # Ensure some product exists
    p = Product.query.first()
    if not p:
        cat = Category.query.first() or Category(name='Default', slug='default')
        db.session.add(cat)
        db.session.flush()
        p = Product(name='Test Product', slug='test-product', price=9.99, stock=10, category_id=cat.id, is_active=True)
        db.session.add(p)
        db.session.commit()
    # Create a cart and add item
    cart = Cart(session_id='test-session')
    db.session.add(cart)
    db.session.flush()
    item = CartItem(cart_id=cart.id, product_id=p.id, quantity=1, price=p.price)
    db.session.add(item)
    db.session.commit()

    client = app.test_client()
    # Attach session cookie by setting session directly
    with client.session_transaction() as sess:
        sess['cart_id'] = cart.id

    print('Posting to /shop/checkout ...')
    try:
        rv = client.post('/shop/checkout', data={'first_name':'T','last_name':'U','email':'test@example.com'})
        print('Status code:', rv.status_code)
        data = rv.get_data(as_text=True)
        print('Response snippet:', data[:800])
    except Exception as e:
        print('Exception during request:', repr(e))
