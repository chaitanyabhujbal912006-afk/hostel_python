import os

import mysql.connector


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
}

with open('database_schema.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()
for statement in [part.strip() for part in sql.split(';') if part.strip()]:
    cursor.execute(statement)

conn.commit()
cursor.close()
conn.close()
print('MySQL database initialized successfully')
