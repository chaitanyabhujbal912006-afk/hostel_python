import os
import sys
import sqlite3
sys.path.insert(0, os.getcwd())
from hostel_app import db as hdb

print('SQLITE_DB_PATH=', hdb.SQLITE_DB_PATH)
print('DB exists:', os.path.exists(hdb.SQLITE_DB_PATH))
if os.path.exists(hdb.SQLITE_DB_PATH):
    conn = sqlite3.connect(hdb.SQLITE_DB_PATH)
    cur = conn.cursor()
    for t in ['student','room','expenses','rent']:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            print(t, cur.fetchone()[0])
        except Exception as e:
            print(t, 'err', e)
    conn.close()
else:
    print('DB file missing')
