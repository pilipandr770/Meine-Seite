import requests, re, sys

BASE = 'http://127.0.0.1:5000'
session = requests.Session()

try:
    r = session.get(f'{BASE}/shop/product/1-hour', timeout=10)
except Exception as e:
    print('GET error:', e)
    sys.exit(2)

if r.status_code != 200:
    print('GET returned', r.status_code)
    sys.exit(3)

m = re.search(r'<meta name="csrf-token" content="([^"]+)"', r.text)
if not m:
    print('No CSRF token found in page')
    sys.exit(4)

csrf = m.group(1)
print('Found CSRF:', csrf[:8] + '...')

try:
    resp = session.post(f'{BASE}/shop/cart/add', json={'product_id': 1, 'quantity': 1}, headers={'X-CSRF-Token': csrf}, timeout=10)
except Exception as e:
    print('POST error:', e)
    sys.exit(5)

print('POST status:', resp.status_code)
print('POST headers:', dict(resp.headers))
print('POST body:', resp.text)
