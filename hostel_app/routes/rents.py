from datetime import date, datetime

from flask import Blueprint, redirect, render_template, request

from hostel_app.db import get_db_connection, get_fresh_cursor


rents_bp = Blueprint("rents", __name__)


def parse_month_year(value):
    value = (value or "").strip()
    if not value:
        return None

    for fmt in ("%Y-%m", "%B %Y"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m")
        except ValueError:
            continue
    return None


def normalize_rent_status(status, due_date, paid_date):
    status = (status or "Pending").strip().title()
    if status == "Paid":
        return "Paid", paid_date or due_date or date.today().isoformat()
    if status == "Cancelled":
        return "Cancelled", None
    if due_date:
        try:
            due = datetime.strptime(due_date, "%Y-%m-%d").date()
            if due < date.today():
                return "Overdue", None
        except ValueError:
            pass
    return "Pending", None


@rents_bp.route("/add_rent", methods=["GET", "POST"])
def add_rent():
    if request.method == "POST":
        try:
            student_id = request.form.get("student_id", 0)
            month_year = parse_month_year(request.form.get("month_year") or request.form.get("month"))
            amount = request.form.get("amount", 0)
            due_date = request.form.get("due_date", "")
            requested_status = request.form.get("status", "Pending")
            paid_date = request.form.get("paid_date", "") or None

            if not student_id or not month_year or not due_date or not amount:
                _, cursor = get_db_connection()
                cursor.execute("SELECT student_id, first_name, last_name FROM student WHERE status='Active'")
                students = cursor.fetchall()
                return render_template(
                    "add_rent.html",
                    students=students,
                    error="Student, billing month, due date, and amount are required",
                    active_page="add_rent",
                )

            status, paid_date = normalize_rent_status(requested_status, due_date, paid_date)

            db, cursor = get_db_connection()
            cursor.execute("SELECT room_id FROM allocation WHERE student_id=%s AND status='Active'", (int(student_id),))
            allocation = cursor.fetchone()
            if not allocation:
                cursor.execute("SELECT student_id, first_name, last_name FROM student WHERE status='Active'")
                students = cursor.fetchall()
                return render_template(
                    "add_rent.html",
                    students=students,
                    error="Student is not allocated to any active room",
                    active_page="add_rent",
                )

            room_id = allocation["room_id"]
            cursor.execute(
                """
                INSERT INTO rent (student_id, room_id, amount, due_date, paid_date, month_year, status, payment_method)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Cash')
                """,
                (int(student_id), room_id, float(amount), due_date, paid_date, month_year, status),
            )
            db.commit()
            return redirect("/rents")
        except Exception as err:
            print(f"Error adding rent: {err}")
            if "UNIQUE" in str(err) or "unique" in str(err):
                _, cursor = get_db_connection()
                cursor.execute("SELECT student_id, first_name, last_name FROM student WHERE status='Active'")
                students = cursor.fetchall()
                return render_template(
                    "add_rent.html",
                    students=students,
                    error="Rent already exists for this student and month",
                    active_page="add_rent",
                )
            _, cursor = get_db_connection()
            cursor.execute("SELECT student_id, first_name, last_name FROM student WHERE status='Active'")
            students = cursor.fetchall()
            return render_template("add_rent.html", students=students, error="Error adding rent", active_page="add_rent")

    try:
        _, cursor = get_db_connection()
        cursor.execute("SELECT student_id, first_name, last_name FROM student WHERE status='Active'")
        students = cursor.fetchall()
        return render_template("add_rent.html", students=students, active_page="add_rent")
    except Exception:
        return render_template("add_rent.html", students=[], error="Error loading students", active_page="add_rent")


@rents_bp.route("/rents")
def rents():
    try:
        db, cursor = get_db_connection()
        cursor.execute("SELECT rent_id, due_date FROM rent WHERE status='Pending'")
        pending_rents = cursor.fetchall()
        for rent in pending_rents:
            try:
                due = datetime.strptime(rent["due_date"], "%Y-%m-%d").date()
            except (TypeError, ValueError):
                continue
            if due < date.today():
                cursor.execute("UPDATE rent SET status='Overdue', paid_date=NULL WHERE rent_id=%s", (rent["rent_id"],))
        db.commit()

        cursor = get_fresh_cursor()
        if cursor is None:
            return render_template("rents.html", rents=[], error="Database connection error", active_page="rents")

        cursor.execute(
            """
            SELECT r.rent_id, s.student_id, s.first_name, s.last_name, r.room_id, rm.room_no,
                   r.month_year, r.amount, r.status, r.due_date, r.paid_date
            FROM rent r
            JOIN student s ON r.student_id = s.student_id
            JOIN room rm ON r.room_id = rm.room_id
            ORDER BY r.due_date DESC
            """
        )
        data = cursor.fetchall()
        return render_template("rents.html", rents=data, active_page="rents")
    except Exception as err:
        print(f"Error loading rents: {err}")
        return render_template("rents.html", rents=[], error="Error loading rents", active_page="rents")


@rents_bp.route("/edit_rent/<int:rent_id>", methods=["GET", "POST"])
def edit_rent(rent_id):
    try:
        db, _ = get_db_connection()

        if request.method == "POST":
            amount = request.form.get("amount", 0)
            status = request.form.get("status", "Pending")
            paid_date = request.form.get("paid_date", None)
            due_date = request.form.get("due_date", "")

            if not amount or not due_date:
                cursor = get_fresh_cursor()
                cursor.execute("SELECT * FROM rent WHERE rent_id=%s", (rent_id,))
                rent = cursor.fetchone()
                return render_template("edit_rent.html", rent=rent, error="Amount and due date are required", active_page="rents")

            status, paid_date = normalize_rent_status(status, due_date, paid_date)

            cursor = get_fresh_cursor()
            if cursor is None:
                return render_template("edit_rent.html", error="Database connection error", active_page="rents")

            cursor.execute(
                """
                UPDATE rent
                SET amount=%s, status=%s, due_date=%s, paid_date=%s
                WHERE rent_id=%s
                """,
                (float(amount), status, due_date, paid_date if paid_date else None, rent_id),
            )
            if cursor.rowcount == 0:
                return render_template("edit_rent.html", error="Rent record not found", active_page="rents")

            db.commit()
            return redirect("/rents")

        cursor = get_fresh_cursor()
        if cursor is None:
            return render_template("edit_rent.html", error="Database connection error", active_page="rents")

        cursor.execute("SELECT * FROM rent WHERE rent_id=%s", (rent_id,))
        rent = cursor.fetchone()
        if not rent:
            return redirect("/rents")
        return render_template("edit_rent.html", rent=rent, active_page="rents")
    except Exception as err:
        print(f"Error in edit_rent: {err}")
        return redirect("/rents")


@rents_bp.route("/delete_rent/<int:rent_id>", methods=["POST"])
def delete_rent(rent_id):
    db, cursor = get_db_connection()
    try:
        cursor.execute("DELETE FROM rent WHERE rent_id=%s", (rent_id,))
        db.commit()
    except Exception as err:
        print(f"Error: {err}")
    return redirect("/rents")
