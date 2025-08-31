import sqlite3
import os

db_path = os.path.join('instance','clients.db')
print('DB path:', db_path, 'exists=', os.path.exists(db_path))
if not os.path.exists(db_path):
    raise SystemExit('DB not found')
conn = sqlite3.connect(db_path)
c = conn.cursor()
for table in ('products','orders'):
    print('\nTable:', table)
    try:
        for row in c.execute(f"PRAGMA table_info('{table}')"):
            print(row)
    except Exception as e:
        print('Error reading table', table, e)
conn.close()
