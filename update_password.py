import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="shreeswamisamarth",
    database="hostel_db"
)

cursor = db.cursor()
cursor.execute("UPDATE admin SET password='admin123' WHERE username='admin'")
db.commit()

print("✅ Password updated to: admin123")
cursor.execute("SELECT username, password FROM admin")
result = cursor.fetchone()
print(f"✅ Username: {result[0]}")
print(f"✅ Password: {result[1]}")

db.close()
