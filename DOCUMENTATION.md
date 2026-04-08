# Hostel Management System - Technical Documentation

## 1. Project Overview
This project is a Flask-based Hostel Management System for managing:
- Students
- Rooms
- Room allocations
- Rent records
- Expenses
- Dashboard analytics

The application uses server-rendered templates (Jinja2) and MySQL as the primary database.

## 2. Tech Stack
- Backend: Python, Flask
- Database: MySQL (`mysql.connector`)
- Frontend: HTML, Jinja2 templates, CSS, Chart.js
- Runtime: Flask dev server (`debug=True` in local run)

## 3. High-Level Architecture
Request flow:
1. Browser sends HTTP request to Flask route.
2. Route handler reads/writes MySQL via `get_db_connection()`.
3. Handler returns rendered Jinja template or JSON API response.
4. Dashboard page uses AJAX (`/api/dashboard-data`) for dynamic updates.

Key app wiring:
- Entry point: `app.py`
- App factory and blueprint registration: `hostel_app/__init__.py`
- DB lifecycle: `hostel_app/db.py`

## 4. Folder Structure
- `app.py` - Flask startup
- `database_schema.sql` - full MySQL schema
- `database_sqlite.sql` - SQLite fallback schema
- `init_db.py` - DB bootstrap script
- `update_password.py` - admin password update script
- `hostel_app/db.py` - DB connection helpers
- `hostel_app/routes/` - feature modules
- `templates/` - Jinja templates
- `static/css/` - CSS files

## 5. Application Initialization
`hostel_app/__init__.py`:
- Creates Flask app with template/static folders
- Sets `secret_key`
- Registers DB teardown (`db.init_app(app)`)
- Registers Blueprints:
  - dashboard
  - students
  - expenses
  - rooms
  - allocations
  - rents

## 6. Database Layer
`hostel_app/db.py` provides:
- `get_db_connection()`:
  - Creates or reuses global MySQL connection and dictionary cursor
- `get_fresh_cursor()`:
  - Returns new dictionary cursor for fresh reads
- `close_db()`:
  - Closes cursor + connection on app context teardown

Configuration uses env vars with defaults:
- `DB_HOST` (default `localhost`)
- `DB_USER` (default `root`)
- `DB_PASSWORD` (no hardcoded secret; provide via environment)
- `DB_NAME` (default `hostel_db`)

## 7. Core Database Entities
Defined in `database_schema.sql`:
- `admin`
- `room`
- `student`
- `allocation`
- `rent`
- `expenses`
- `maintenance_log`
- `audit_log`

Important relationships:
- `allocation.student_id -> student.student_id`
- `allocation.room_id -> room.room_id`
- `rent.student_id -> student.student_id`
- `rent.room_id -> room.room_id`

## 8. Route Modules and Responsibilities

### 8.1 Students (`routes/students.py`)
- `GET/POST /add_student`
- `GET /students`
- `GET/POST /edit_student/<student_id>`
- `GET /delete_student/<student_id>`

Highlights:
- Validates required student fields
- Handles unique violations for email/phone
- On delete, cleans `rent`, `allocation`, and updates room occupancy/status

### 8.2 Rooms (`routes/rooms.py`)
- `GET/POST /add_room`
- `GET /rooms`
- `GET/POST /edit_room/<room_id>`
- `GET /delete_room/<room_id>`

Highlights:
- Room listing uses active allocation count for occupancy
- Prevents duplicate room number via DB unique constraint handling

### 8.3 Allocations (`routes/allocations.py`)
- `GET/POST /allocate`
- `GET /allocations`
- `GET/POST /edit_allocation/<allocation_id>`
- `GET /delete_allocation/<allocation_id>`

Highlights:
- Enforces capacity before assignment
- Moves student between rooms safely (decrement old, increment new)
- Supports grouped room-wise allocation view

### 8.4 Rents (`routes/rents.py`)
- `GET/POST /add_rent`
- `GET /rents`
- `GET/POST /edit_rent/<rent_id>`
- `POST /delete_rent/<rent_id>`

Highlights:
- Parses month formats (`YYYY-MM` and `Month YYYY`)
- Auto-normalizes status (`Paid`, `Pending`, `Overdue`, `Cancelled`)
- Marks pending records overdue when due date has passed
- Requires active room allocation before rent insert

### 8.5 Expenses (`routes/expenses.py`)
- `GET/POST /add_expense`
- `GET /expenses`
- `GET/POST /edit_expense/<expense_id>`
- `POST /delete_expense/<expense_id>`

Highlights:
- Stores operational expenses with category/date/payment method
- Expense list ordered by latest date

### 8.6 Dashboard (`routes/dashboard.py`)
- `GET /` -> redirects to `/dashboard`
- `GET /dashboard`
- `GET /api/dashboard-data`

Highlights:
- Computes KPIs: students, occupancy, collections, pending, etc.
- Supports date-range filtering
- Returns JSON for dynamic front-end updates
- Provides chart/table datasets:
  - expense trend
  - occupancy split
  - monthly finance trend
  - rent status distribution
  - pending dues table
  - expense category summary table

## 9. Frontend Design System
Common template shell:
- `templates/base.html`

Primary styling:
- `static/css/premium.css`

Dashboard interactivity:
- `templates/dashboard.html` includes Chart.js rendering and filter-driven API calls.

## 10. Key Business Rules
- A room cannot exceed capacity during allocation.
- Student rent entry requires active allocation.
- Duplicate rent for same student/month is blocked by DB unique key.
- Pending rent can become overdue based on due date.
- Student deletion cascades data cleanup and occupancy correction.

## 11. Error Handling Strategy
- Most routes wrap DB writes in `try/except`.
- User-visible errors are shown in form pages.
- Some routes use rollback on failure (`db.rollback()`).
- API endpoint returns JSON error with HTTP 500 for failures.

## 12. Known Technical Notes
- There are two similar project folders in workspace (`hostel_python` and `hostel_python-master`). Keep one as source of truth during deployment.
- DB password defaults differ between scripts (`db.py` vs `init_db.py`/`update_password.py`). Align them before production use.
- Many delete actions use `GET`; for production security, prefer `POST` with CSRF protection.

## 13. Local Setup and Run
1. Ensure MySQL server is running.
2. Configure env vars (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`) as needed.
3. Initialize schema:
   - `python init_db.py`
4. Start app:
   - `python app.py`
5. Open:
   - `http://127.0.0.1:5000/dashboard`

## 14. Suggested Next Improvements
- Add authentication/authorization middleware and session protection.
- Add CSRF for all form submissions.
- Replace global DB connection with per-request scoped connection pool.
- Add automated tests for routes and business rules.
- Add structured logging and centralized error tracking.
