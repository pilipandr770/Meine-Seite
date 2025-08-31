import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
print('START SCRIPT')
from app.app import create_app
app = create_app()
print('APP CREATED')
with app.app_context():
    from app.models.database import db
    from app.models.product import Product, Category
    from app.models.shop import Cart, CartItem
    # Ensure product exists
    p = Product.query.first()
    if not p:
        cat = Category(name='Default', slug='default')
        db.session.add(cat)
        db.session.flush()
        p = Product(name='QuickTest', slug='quick-test', price=5.0, stock=5, category_id=cat.id, is_active=True)
        db.session.add(p)
        db.session.commit()
    # create cart
    cart = Cart(session_id='quick-session')
    db.session.add(cart)
    db.session.flush()
    item = CartItem(cart_id=cart.id, product_id=p.id, quantity=1, price=p.price)
    db.session.add(item)
    db.session.commit()
    from flask import url_for
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['cart_id'] = cart.id
    print('About to post to /shop/checkout')
    rv = client.post('/shop/checkout', data={'first_name':'A','last_name':'B','email':'x@x.com'})
    print('STATUS', rv.status_code)
    print('LEN', len(rv.get_data()))
print('END SCRIPT')
