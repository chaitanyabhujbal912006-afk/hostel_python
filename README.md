# Hostel Python

Simple Flask-based hostel management app for local development and demos.

## Quick start (Windows PowerShell)

1. Create and activate virtualenv (if not already):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Initialize the SQLite database (dev):

```powershell
python init_db.py
```

4. Run the app:

```powershell
.\.venv\Scripts\python.exe app.py
```

5. Open http://127.0.0.1:5000 in your browser.

## Notes
- Do NOT commit `.venv/` or `hostel.db` to source control. `.gitignore` is configured to ignore them.
- To use MySQL, set `DB_ENGINE=mysql` and configure `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` as environment variables. Install the connector with `pip install mysql-connector-python`.
- The schema files are `database_schema.sql` (MySQL) and `database_sqlite.sql` (SQLite). Use `init_db.py` to create the local SQLite DB.

## Contributing
- Open issues and PRs. Add migrations/schema updates rather than committing DB files.
