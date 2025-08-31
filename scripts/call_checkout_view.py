import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
print('START')
from app.app import create_app
from app.routes.shop import checkout
from flask import Request
app = create_app()
with app.app_context():
    try:
        print('Calling checkout view directly (GET)')
        rv = checkout()
        print('OK, returned', type(rv))
    except Exception as e:
        print('EX', repr(e))
print('END')
