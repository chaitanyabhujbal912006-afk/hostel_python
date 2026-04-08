from datetime import datetime, timedelta
from flask import Blueprint, redirect, render_template, request, jsonify
from hostel_app.db import get_db_connection


dashboard_bp = Blueprint("dashboard", __name__)

def get_fresh_db_connection():
    """Create a fresh database connection for each request"""
    db, _ = get_db_connection()
    if db:
        cursor = db.cursor(dictionary=True)
        return db, cursor
    return None, None


def get_dashboard_metrics(start_date=None, end_date=None):
    """Fetch dashboard metrics with optional date filtering"""
    db, cursor = get_fresh_db_connection()
    if cursor is None:
        return None

    try:
        # Build date filter for all queries
        date_filter = ""
        date_params = []
        if start_date and end_date:
            date_filter = " BETWEEN %s AND %s"
            date_params = [start_date, end_date]
        
        # Students - filtered by enrollment_date
        if start_date and end_date:
            cursor.execute(
                "SELECT COUNT(*) AS total_students FROM student WHERE enrollment_date" + date_filter,
                date_params
            )
        else:
            cursor.execute("SELECT COUNT(*) AS total_students FROM student")
        students = cursor.fetchone()

        # Rooms - filtered by room creation date or allocation within date range
        if start_date and end_date:
            cursor.execute(
                """
                SELECT COUNT(DISTINCT r.room_id) AS total_rooms FROM room r
                LEFT JOIN allocation a ON r.room_id = a.room_id
                WHERE a.allocation_date BETWEEN %s AND %s OR r.created_at BETWEEN %s AND %s
                """,
                [start_date, end_date, start_date, end_date]
            )
        else:
            cursor.execute("SELECT COUNT(*) AS total_rooms FROM room")
        rooms = cursor.fetchone()

        # Expense queries with date filtering
        if start_date and end_date:
            cursor.execute(
                """
                SELECT IFNULL(SUM(amount),0) AS total_expense FROM expenses
                WHERE expense_date BETWEEN %s AND %s
                """,
                (start_date, end_date)
            )
        else:
            cursor.execute("SELECT IFNULL(SUM(amount),0) AS total_expense FROM expenses")
        expenses = cursor.fetchone()

        # Expense data with date filtering
        if start_date and end_date:
            cursor.execute(
                """
                SELECT expense_date, SUM(amount) AS total
                FROM expenses
                WHERE expense_date BETWEEN %s AND %s
                GROUP BY expense_date
                ORDER BY expense_date DESC
                LIMIT 30
                """,
                (start_date, end_date)
            )
        else:
            cursor.execute(
                """
                SELECT expense_date, SUM(amount) AS total
                FROM expenses
                GROUP BY expense_date
                ORDER BY expense_date DESC
                LIMIT 30
                """
            )
        expense_data = cursor.fetchall()

        # Occupancy metrics - always based on active allocations
        if start_date and end_date:
            cursor.execute(
                """
                SELECT
                    COUNT(DISTINCT a.room_id) AS total_occupied,
                    (SELECT COUNT(*) FROM room WHERE capacity > 0) AS total_capacity
                FROM allocation a
                WHERE a.status = 'Active' AND a.allocation_date BETWEEN %s AND %s
                """,
                (start_date, end_date)
            )
        else:
            cursor.execute(
                """
                SELECT
                    COUNT(DISTINCT a.room_id) AS total_occupied,
                    (SELECT COUNT(*) FROM room WHERE capacity > 0) AS total_capacity
                FROM allocation a
                WHERE a.status = 'Active'
                """
            )
        occupancy = cursor.fetchone()
        total_occupied = occupancy["total_occupied"] or 0
        total_capacity = occupancy["total_capacity"] or 0
        total_available = total_capacity - total_occupied
        occupancy_percentage = int((total_occupied / total_capacity) * 100) if total_capacity > 0 else 0

        # Rent metrics - filtered by due_date
        if start_date and end_date:
            cursor.execute(
                "SELECT COUNT(*) AS total_rent FROM rent WHERE status='Paid' AND due_date BETWEEN %s AND %s",
                (start_date, end_date)
            )
        else:
            cursor.execute("SELECT COUNT(*) AS total_rent FROM rent WHERE status='Paid'")
        paid_rent = cursor.fetchone()

        if start_date and end_date:
            cursor.execute(
                "SELECT COUNT(*) AS total_rent FROM rent WHERE status IN ('Pending', 'Overdue') AND due_date BETWEEN %s AND %s",
                (start_date, end_date)
            )
        else:
            cursor.execute("SELECT COUNT(*) AS total_rent FROM rent WHERE status IN ('Pending', 'Overdue')")
        unpaid_rent = cursor.fetchone()

        if start_date and end_date:
            cursor.execute(
                "SELECT IFNULL(SUM(amount),0) AS total_collected FROM rent WHERE status='Paid' AND due_date BETWEEN %s AND %s",
                (start_date, end_date)
            )
        else:
            cursor.execute("SELECT IFNULL(SUM(amount),0) AS total_collected FROM rent WHERE status='Paid'")
        rent_collected = cursor.fetchone()

        if start_date and end_date:
            cursor.execute(
                "SELECT IFNULL(SUM(amount),0) AS total_pending FROM rent WHERE status IN ('Pending', 'Overdue') AND due_date BETWEEN %s AND %s",
                (start_date, end_date)
            )
        else:
            cursor.execute("SELECT IFNULL(SUM(amount),0) AS total_pending FROM rent WHERE status IN ('Pending', 'Overdue')")
        rent_pending = cursor.fetchone()

        total_paid_rent = paid_rent["total_rent"] or 0
        total_unpaid_rent = unpaid_rent["total_rent"] or 0
        total_rent = total_paid_rent + total_unpaid_rent
        rent_collection_percentage = int((total_paid_rent / total_rent) * 100) if total_rent > 0 else 0

        # Rent status distribution for chart
        if start_date and end_date:
            cursor.execute(
                """
                SELECT status, COUNT(*) AS total
                FROM rent
                WHERE due_date BETWEEN %s AND %s
                GROUP BY status
                """,
                (start_date, end_date),
            )
        else:
            cursor.execute(
                """
                SELECT status, COUNT(*) AS total
                FROM rent
                GROUP BY status
                """
            )
        rent_status_rows = cursor.fetchall()
        rent_status_counts = {"Paid": 0, "Pending": 0, "Overdue": 0, "Cancelled": 0}
        for row in rent_status_rows:
            status = row.get("status")
            if status in rent_status_counts:
                rent_status_counts[status] = int(row.get("total") or 0)

        # Monthly finance trend for chart (rent collected vs expenses)
        finance_params = []
        finance_where_rent = ""
        finance_where_expense = ""
        if start_date and end_date:
            finance_where_rent = " WHERE due_date BETWEEN %s AND %s"
            finance_where_expense = " WHERE expense_date BETWEEN %s AND %s"
            finance_params = [start_date, end_date]

        rent_monthly_query = f"""
            SELECT month_year AS month, IFNULL(SUM(amount), 0) AS rent_collected
            FROM rent
            {finance_where_rent}
            GROUP BY month_year
            ORDER BY month_year DESC
            LIMIT 6
            """
        if finance_params:
            cursor.execute(rent_monthly_query, finance_params)
        else:
            cursor.execute(rent_monthly_query)
        rent_monthly_rows = cursor.fetchall()

        expense_monthly_query = f"""
            SELECT DATE_FORMAT(expense_date, '%%Y-%%m') AS month, IFNULL(SUM(amount), 0) AS expense_total
            FROM expenses
            {finance_where_expense}
            GROUP BY DATE_FORMAT(expense_date, '%%Y-%%m')
            ORDER BY month DESC
            LIMIT 6
            """
        if finance_params:
            cursor.execute(expense_monthly_query, finance_params)
        else:
            cursor.execute(expense_monthly_query)
        expense_monthly_rows = cursor.fetchall()

        monthly_map = {}
        for row in rent_monthly_rows:
            month = row.get("month")
            if not month:
                continue
            monthly_map[month] = {
                "month": month,
                "rent_collected": float(row.get("rent_collected") or 0),
                "expense_total": 0.0,
            }
        for row in expense_monthly_rows:
            month = row.get("month")
            if not month:
                continue
            if month not in monthly_map:
                monthly_map[month] = {"month": month, "rent_collected": 0.0, "expense_total": 0.0}
            monthly_map[month]["expense_total"] = float(row.get("expense_total") or 0)

        monthly_finance = sorted(monthly_map.values(), key=lambda x: x["month"])

        # Table: upcoming/pending dues
        if start_date and end_date:
            cursor.execute(
                """
                SELECT
                    r.rent_id,
                    CONCAT(s.first_name, ' ', s.last_name) AS student_name,
                    rm.room_no,
                    r.due_date,
                    r.amount,
                    r.status,
                    GREATEST(DATEDIFF(CURDATE(), r.due_date), 0) AS days_overdue
                FROM rent r
                JOIN student s ON r.student_id = s.student_id
                JOIN room rm ON r.room_id = rm.room_id
                WHERE r.status IN ('Pending', 'Overdue') AND r.due_date BETWEEN %s AND %s
                ORDER BY r.due_date ASC
                LIMIT 8
                """,
                (start_date, end_date),
            )
        else:
            cursor.execute(
                """
                SELECT
                    r.rent_id,
                    CONCAT(s.first_name, ' ', s.last_name) AS student_name,
                    rm.room_no,
                    r.due_date,
                    r.amount,
                    r.status,
                    GREATEST(DATEDIFF(CURDATE(), r.due_date), 0) AS days_overdue
                FROM rent r
                JOIN student s ON r.student_id = s.student_id
                JOIN room rm ON r.room_id = rm.room_id
                WHERE r.status IN ('Pending', 'Overdue')
                ORDER BY r.due_date ASC
                LIMIT 8
                """
            )
        pending_dues_rows = cursor.fetchall()
        pending_dues = []
        for row in pending_dues_rows:
            due_date = row.get("due_date")
            pending_dues.append(
                {
                    "rent_id": row.get("rent_id"),
                    "student_name": row.get("student_name"),
                    "room_no": row.get("room_no"),
                    "due_date": due_date.strftime("%Y-%m-%d") if hasattr(due_date, "strftime") else str(due_date or ""),
                    "amount": float(row.get("amount") or 0),
                    "status": row.get("status"),
                    "days_overdue": int(row.get("days_overdue") or 0),
                }
            )

        # Table: expense category summary
        if start_date and end_date:
            cursor.execute(
                """
                SELECT expense_type, COUNT(*) AS entry_count, IFNULL(SUM(amount), 0) AS total_amount
                FROM expenses
                WHERE expense_date BETWEEN %s AND %s
                GROUP BY expense_type
                ORDER BY total_amount DESC
                LIMIT 8
                """,
                (start_date, end_date),
            )
        else:
            cursor.execute(
                """
                SELECT expense_type, COUNT(*) AS entry_count, IFNULL(SUM(amount), 0) AS total_amount
                FROM expenses
                GROUP BY expense_type
                ORDER BY total_amount DESC
                LIMIT 8
                """
            )
        expense_category_rows = cursor.fetchall()
        expense_category_summary = [
            {
                "expense_type": row.get("expense_type"),
                "entry_count": int(row.get("entry_count") or 0),
                "total_amount": float(row.get("total_amount") or 0),
            }
            for row in expense_category_rows
        ]

        return {
            "students": students["total_students"],
            "rooms": rooms["total_rooms"],
            "expense": expenses["total_expense"],
            "expense_data": expense_data,
            "total_occupied": total_occupied,
            "total_available": total_available,
            "total_capacity": total_capacity,
            "occupancy_percentage": occupancy_percentage,
            "total_paid_rent": total_paid_rent,
            "total_unpaid_rent": total_unpaid_rent,
            "rent_collection_percentage": rent_collection_percentage,
            "rent_collected": rent_collected["total_collected"],
            "rent_pending": rent_pending["total_pending"],
            "rent_status_counts": rent_status_counts,
            "monthly_finance": monthly_finance,
            "pending_dues": pending_dues,
            "expense_category_summary": expense_category_summary,
            "current_date": datetime.now().strftime("%A, %B %d, %Y"),
        }
    except mysql.connector.Error as err:
        print(f"Database Query Error: {err}")
        return None
    finally:
        try:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()
        except Exception:
            pass


@dashboard_bp.route("/")
def index():
    return redirect("/dashboard")


@dashboard_bp.route("/dashboard")
def dashboard():
    metrics = get_dashboard_metrics()
    if metrics is None:
        return redirect("/")

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        **metrics
    )


@dashboard_bp.route("/api/dashboard-data")
def dashboard_data():
    """API endpoint for dynamic dashboard data"""
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        print(f"API Request: start_date={start_date}, end_date={end_date}")
        
        metrics = get_dashboard_metrics(start_date, end_date)
        if metrics is None:
            print("ERROR: get_dashboard_metrics returned None")
            return jsonify({"error": "Database connection failed. Check server logs."}), 500

        # Convert expense_data to list of dicts for JSON serialization
        expense_data_list = []
        for item in metrics["expense_data"]:
            expense_data_list.append({
                "expense_date": item["expense_date"],
                "total": item["total"]
            })

        response = {
            "students": metrics["students"],
            "rooms": metrics["rooms"],
            "expense": metrics["expense"],
            "expense_data": expense_data_list,
            "total_occupied": metrics["total_occupied"],
            "total_available": metrics["total_available"],
            "total_capacity": metrics["total_capacity"],
            "occupancy_percentage": metrics["occupancy_percentage"],
            "total_paid_rent": metrics["total_paid_rent"],
            "total_unpaid_rent": metrics["total_unpaid_rent"],
            "rent_collection_percentage": metrics["rent_collection_percentage"],
            "rent_collected": metrics["rent_collected"],
            "rent_pending": metrics["rent_pending"],
            "rent_status_counts": metrics["rent_status_counts"],
            "monthly_finance": metrics["monthly_finance"],
            "pending_dues": metrics["pending_dues"],
            "expense_category_summary": metrics["expense_category_summary"],
            "current_date": metrics["current_date"],
        }
        
        print("API Response successful")
        return jsonify(response)
        
    except Exception as e:
        print(f"EXCEPTION in dashboard_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500
