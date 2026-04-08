import os
import sys

import mysql.connector
from werkzeug.security import generate_password_hash


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "hostel_db"),
}
USERNAME = os.getenv("ADMIN_USERNAME", "admin")
NEW_PASSWORD = os.getenv("ADMIN_NEW_PASSWORD")

if not NEW_PASSWORD:
    print("Set ADMIN_NEW_PASSWORD env var before running this script.")
    sys.exit(1)

hashed_password = generate_password_hash(NEW_PASSWORD)

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("UPDATE admin SET password = %s WHERE username = %s", (hashed_password, USERNAME))

    if cursor.rowcount == 0:
        print(f"User '{USERNAME}' not found. No password was updated.")
    else:
        conn.commit()
        print(f"Password for '{USERNAME}' was hashed and updated to '{NEW_PASSWORD}'.")

    cursor.execute("SELECT username, password FROM admin WHERE username = %s", (USERNAME,))
    result = cursor.fetchone()
    if result:
        print(f"Username: {result[0]}")
        print(f"Stored Hash (first 30 chars): {result[1][:30]}...")

    cursor.close()
    conn.close()
except mysql.connector.Error as e:
    print(f"Database error: {e}")
