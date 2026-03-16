import mysql.connector
from flask import Blueprint, redirect, render_template, request

from hostel_app.auth import login_required
from hostel_app.db import get_db_connection


students_bp = Blueprint("students", __name__)


@students_bp.route("/add_student", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        try:
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            guardian_name = request.form.get("guardian_name", "").strip()
            guardian_phone = request.form.get("guardian_phone", "").strip()

            if not all([first_name, last_name, email, phone]):
                return render_template("add_student.html", error="All fields required")

            db, cursor = get_db_connection()
            cursor.execute(
                """
                INSERT INTO student (first_name, last_name, email, phone, guardian_name, guardian_phone, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'Active')
                """,
                (first_name, last_name, email, phone, guardian_name, guardian_phone),
            )
            db.commit()
            return redirect("/students")
        except mysql.connector.Error as err:
            if err.errno == 1062:
                return render_template("add_student.html", error="Email or phone already exists")
            return render_template("add_student.html", error="Error adding student")

    return render_template("add_student.html")


@students_bp.route("/students")
@login_required
def students():
    try:
        _, cursor = get_db_connection()
        cursor.execute(
            """
            SELECT s.*, r.room_no
            FROM student s
            LEFT JOIN allocation a ON s.student_id = a.student_id AND a.status = 'Active'
            LEFT JOIN room r ON a.room_id = r.room_id
            WHERE s.status IN ('Active', 'Inactive')
            ORDER BY s.student_id ASC
            """
        )
        data = cursor.fetchall()
        return render_template("students.html", students=data)
    except Exception:
        return render_template("students.html", students=[], error="Error loading students")


@students_bp.route("/edit_student/<int:student_id>", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    db, cursor = get_db_connection()

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        if not all([first_name, last_name, email, phone]):
            student = {
                "student_id": student_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
            }
            return render_template("edit_student.html", student=student, error="All fields required")

        try:
            cursor.execute(
                """
                UPDATE student
                SET first_name=%s, last_name=%s, email=%s, phone=%s
                WHERE student_id=%s
                """,
                (first_name, last_name, email, phone, student_id),
            )
            db.commit()
            return redirect("/students")
        except mysql.connector.Error as err:
            db.rollback()
            student = {
                "student_id": student_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
            }
            if err.errno == 1062:
                return render_template("edit_student.html", student=student, error="Email or phone already exists")
            return render_template("edit_student.html", student=student, error=f"Error updating student: {err.msg}")

    cursor.execute("SELECT * FROM student WHERE student_id=%s", (student_id,))
    student = cursor.fetchone()
    if not student:
        return redirect("/students")
    return render_template("edit_student.html", student=student)


@students_bp.route("/delete_student/<int:student_id>")
@login_required
def delete_student(student_id):
    db, cursor = get_db_connection()
    try:
        cursor.execute("DELETE FROM rent WHERE student_id=%s", (student_id,))
        cursor.execute("DELETE FROM allocation WHERE student_id=%s", (student_id,))
        cursor.execute("DELETE FROM student WHERE student_id=%s", (student_id,))
        db.commit()
    except Exception:
        db.rollback()
    return redirect("/students")
