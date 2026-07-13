import os
import sqlite3

try:
    import mysql.connector
except ImportError:
    mysql = None
else:
    mysql = mysql.connector


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_ENGINE = os.getenv("DB_ENGINE", "auto").lower()
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "root123"),
    "database": os.getenv("DB_NAME", "hostel_db"),
}
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", os.path.join(BASE_DIR, "hostel.db"))
SQLITE_SCHEMA_PATH = os.path.join(BASE_DIR, "database_sqlite.sql")

db = None
cursor = None
backend = None


class SQLiteCursorAdapter:
    def __init__(self, raw_cursor):
        self._cursor = raw_cursor

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def execute(self, query, params=None):
        translated_query = query.replace("%s", "?")
        if params is None:
            self._cursor.execute(translated_query)
        else:
            self._cursor.execute(translated_query, params)
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        return dict(row) if row is not None else None

    def fetchall(self):
        return [dict(row) for row in self._cursor.fetchall()]

    def close(self):
        self._cursor.close()

    def __getattr__(self, name):
        return getattr(self._cursor, name)


def _should_try_mysql():
    return DB_ENGINE in {"auto", "mysql"} and mysql is not None


def _initialize_sqlite_database(connection):
    schema_cursor = connection.cursor()
    try:
        schema_cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name='admin'
            """
        )
        if schema_cursor.fetchone():
            return

        with open(SQLITE_SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
            connection.executescript(schema_file.read())
        connection.commit()
    finally:
        schema_cursor.close()


def _connect_sqlite():
    sqlite_connection = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_connection.row_factory = sqlite3.Row
    _initialize_sqlite_database(sqlite_connection)
    return sqlite_connection


def _connect_mysql():
    if not _should_try_mysql():
        return None
    return mysql.connect(**DB_CONFIG)


def _is_connection_alive():
    if db is None:
        return False
    if backend == "mysql":
        return db.is_connected()
    if backend == "sqlite":
        return True
    return False


def _build_cursor(connection):
    if backend == "mysql":
        return connection.cursor(dictionary=True)
    return SQLiteCursorAdapter(connection.cursor())


def get_db_connection():
    global db, cursor, backend
    try:
        if _is_connection_alive():
            if cursor is None:
                cursor = _build_cursor(db)
            return db, cursor

        db = None
        cursor = None
        backend = None

        if _should_try_mysql():
            try:
                db = _connect_mysql()
                backend = "mysql"
                cursor = _build_cursor(db)
                return db, cursor
            except Exception as err:
                print(f"MySQL unavailable, switching to SQLite: {err}")

        db = _connect_sqlite()
        backend = "sqlite"
        cursor = _build_cursor(db)
        return db, cursor
    except Exception as err:
        print(f"Database Error: {err}")
        return None, None


def get_fresh_cursor():
    global cursor
    connection, _ = get_db_connection()
    if connection is None:
        return None
    cursor = _build_cursor(connection)
    return cursor


def close_db(_error=None):
    global db, cursor, backend
    try:
        if cursor is not None:
            cursor.close()
    except Exception:
        pass
    try:
        if db is not None and _is_connection_alive():
            db.close()
    except Exception:
        pass
    cursor = None
    db = None
    backend = None


def init_app(app):
    app.teardown_appcontext(close_db)
