import mysql.connector


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "shreeswamisamarth",
    "database": "hostel_db",
}

db = None
cursor = None


def get_db_connection():
    global db, cursor
    try:
        if db is None or not db.is_connected():
            db = mysql.connector.connect(**DB_CONFIG)
            cursor = db.cursor(dictionary=True)
        return db, cursor
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return None, None


def get_fresh_cursor():
    global db, cursor
    try:
        if db is None or not db.is_connected():
            db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor(dictionary=True)
        return cursor
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return None


def init_db():
    global db, cursor
    try:
        db, cursor = get_db_connection()
        print("Database connected successfully")
    except Exception as err:
        print(f"Database connection failed: {err}")
