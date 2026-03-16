import mysql.connector
from flask import Blueprint, redirect, render_template, request

from hostel_app.auth import login_required
from hostel_app.db import get_db_connection, get_fresh_cursor


rents_bp = Blueprint("rents", __name__)


@rents_bp.route("/add_rent", methods=["GET", "POST"])
@login_required
def add_rent():
    if request.method == "POST":
        try:
            student_id = request.form.get("student_id", 0)
            month_year = request.form.get("month_year", "")
            amount = request.form.get("amount", 0)
            due_date = request.form.get("due_date", "")

            db, cursor = get_db_connection()
            cursor.execute("SELECT room_id FROM allocation WHERE student_id=%s AND status='Active'", (student_id,))
            allocation = cursor.fetchone()
            if not allocation:
                return render_template("add_rent.html", error="Student not allocated to any room")

            room_id = allocation["room_id"]
            cursor.execute(
                """
                INSERT INTO rent (student_id, room_id, amount, due_date, month_year, status, payment_method)
                VALUES (%s, %s, %s, %s, %s, 'Pending', 'Cash')
                """,
                (student_id, room_id, float(amount), due_date, month_year),
            )
            db.commit()
            return redirect("/rents")
        except mysql.connector.Error as err:
            if err.errno == 1062:
                return render_template("add_rent.html", error="Rent already recorded for this student/month")
            return render_template("add_rent.html", error="Error adding rent")

    try:
        _, cursor = get_db_connection()
        cursor.execute("SELECT student_id, first_name, last_name FROM student WHERE status='Active'")
        students = cursor.fetchall()
        return render_template("add_rent.html", students=students)
    except Exception:
        return render_template("add_rent.html", students=[], error="Error loading students")


@rents_bp.route("/rents")
@login_required
def rents():
    try:
        cursor = get_fresh_cursor()
        if cursor is None:
            return render_template("rents.html", rents=[], error="Database connection error")

        cursor.execute(
            """
            SELECT r.rent_id, s.student_id, s.first_name, s.last_name, r.room_id,
                   r.month_year, r.amount, r.status, r.due_date, r.paid_date
            FROM rent r
            JOIN student s ON r.student_id = s.student_id
            ORDER BY r.due_date DESC
            """
        )
        data = cursor.fetchall()
        return render_template("rents.html", rents=data)
    except Exception as err:
        print(f"Error loading rents: {err}")
        return render_template("rents.html", rents=[], error="Error loading rents")


@rents_bp.route("/edit_rent/<int:rent_id>", methods=["GET", "POST"])
@login_required
def edit_rent(rent_id):
    try:
        db, _ = get_db_connection()

        if request.method == "POST":
            amount = request.form.get("amount", 0)
            status = request.form.get("status", "Pending")
            paid_date = request.form.get("paid_date", None)

            cursor = get_fresh_cursor()
            if cursor is None:
                return render_template("edit_rent.html", error="Database connection error")

            cursor.execute(
                """
                UPDATE rent
                SET amount=%s, status=%s, paid_date=%s
                WHERE rent_id=%s
                """,
                (float(amount), status, paid_date if paid_date else None, rent_id),
            )
            if cursor.rowcount == 0:
                return render_template("edit_rent.html", error="Rent record not found")

            db.commit()
            return redirect("/rents")

        cursor = get_fresh_cursor()
        if cursor is None:
            return render_template("edit_rent.html", error="Database connection error")

        cursor.execute("SELECT * FROM rent WHERE rent_id=%s", (rent_id,))
        rent = cursor.fetchone()
        if not rent:
            return redirect("/rents")
        return render_template("edit_rent.html", rent=rent)
    except Exception as err:
        print(f"Error in edit_rent: {err}")
        return redirect("/rents")


@rents_bp.route("/delete_rent/<int:rent_id>", methods=["POST"])
@login_required
def delete_rent(rent_id):
    db, cursor = get_db_connection()
    try:
        cursor.execute("DELETE FROM rent WHERE rent_id=%s", (rent_id,))
        db.commit()
    except Exception as err:
        print(f"Error: {err}")
    return redirect("/rents")
