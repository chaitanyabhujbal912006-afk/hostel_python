import os

import mysql.connector


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "hostel_db"),
}

db = None
cursor = None


def get_db_connection():
    global db, cursor
    try:
        if db is None or not db.is_connected():
            db = mysql.connector.connect(**DB_CONFIG)
            cursor = db.cursor(dictionary=True)
        elif cursor is None:
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


def close_db(_error=None):
    global db, cursor
    try:
        if cursor is not None:
            cursor.close()
    except Exception:
        pass
    try:
        if db is not None and db.is_connected():
            db.close()
    except Exception:
        pass
    cursor = None
    db = None


def init_app(app):
    app.teardown_appcontext(close_db)
