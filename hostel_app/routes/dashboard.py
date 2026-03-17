from datetime import datetime

from flask import Blueprint, redirect, render_template

from hostel_app.db import get_db_connection


dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
def index():
    return redirect("/dashboard")

@dashboard_bp.route("/dashboard")
def dashboard():
    _, cursor = get_db_connection()
    if cursor is None:
        return redirect("/")

    cursor.execute("SELECT COUNT(*) AS total_students FROM student")
    students = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) AS total_rooms FROM room")
    rooms = cursor.fetchone()

    cursor.execute("SELECT IFNULL(SUM(amount),0) AS total_expense FROM expenses")
    expenses = cursor.fetchone()

    cursor.execute(
        """
        SELECT expense_date, SUM(amount) AS total
        FROM expenses
        GROUP BY expense_date
        """
    )
    expense_data = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            SUM(occupied) AS total_occupied,
            SUM(capacity) AS total_capacity
        FROM room
        """
    )
    occupancy = cursor.fetchone()
    total_occupied = occupancy["total_occupied"] or 0
    total_available = (occupancy["total_capacity"] or 0) - total_occupied

    cursor.execute("SELECT COUNT(*) AS total_rent FROM rent WHERE status='Paid'")
    paid_rent = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) AS total_rent FROM rent WHERE status IN ('Pending', 'Overdue')")
    unpaid_rent = cursor.fetchone()

    cursor.execute("SELECT IFNULL(SUM(amount),0) AS total_collected FROM rent WHERE status='Paid'")
    rent_collected = cursor.fetchone()

    total_paid_rent = paid_rent["total_rent"] or 0
    total_unpaid_rent = unpaid_rent["total_rent"] or 0
    total_rent = total_paid_rent + total_unpaid_rent
    rent_collection_percentage = int((total_paid_rent / total_rent) * 100) if total_rent > 0 else 0

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        students=students["total_students"],
        rooms=rooms["total_rooms"],
        expense=expenses["total_expense"],
        expense_data=expense_data,
        total_occupied=total_occupied,
        total_available=total_available,
        total_paid_rent=total_paid_rent,
        total_unpaid_rent=total_unpaid_rent,
        rent_collection_percentage=rent_collection_percentage,
        rent_collected=rent_collected["total_collected"],
        current_date=datetime.now().strftime("%A, %B %d, %Y"),
    )
