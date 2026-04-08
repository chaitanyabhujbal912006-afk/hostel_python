from flask import Blueprint, redirect, render_template, request

from hostel_app.db import get_db_connection


students_bp = Blueprint("students", __name__)


@students_bp.route("/add_student", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        try:
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            date_of_birth = request.form.get("date_of_birth", "").strip()
            enrollment_date = request.form.get("enrollment_date", "").strip()
            guardian_name = request.form.get("guardian_name", "").strip()
            guardian_phone = request.form.get("guardian_phone", "").strip()
            address = request.form.get("address", "").strip()
            city = request.form.get("city", "").strip()
            state = request.form.get("state", "").strip()
            status = request.form.get("status", "Active").strip()

            # Validate required fields
            if not all([first_name, last_name, email, phone, enrollment_date]):
                return render_template("add_student.html", error="First Name, Last Name, Email, Phone, and Enrollment Date are required", active_page="add_student")

            db, cursor = get_db_connection()
            cursor.execute(
                """
                INSERT INTO student (first_name, last_name, email, phone, date_of_birth, 
                                    enrollment_date, guardian_name, guardian_phone, 
                                    address, city, state, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (first_name, last_name, email, phone, date_of_birth if date_of_birth else None, 
                 enrollment_date, guardian_name, guardian_phone, address, city, state, status),
            )
            db.commit()
            return redirect("/students")
        except Exception as err:
            print(f"Error adding student: {err}")
            if "UNIQUE" in str(err) or "unique" in str(err):
                return render_template("add_student.html", error="Email or phone already exists", active_page="add_student")
            return render_template("add_student.html", error=f"Error adding student: {str(err)}", active_page="add_student")

    return render_template("add_student.html", active_page="add_student")


@students_bp.route("/students")
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
        return render_template("students.html", students=data, active_page="students")
    except Exception as err:
        print(f"Error loading students: {err}")
        return render_template("students.html", students=[], error=f"Error loading students: {err}", active_page="students")


@students_bp.route("/edit_student/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    db, cursor = get_db_connection()

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        date_of_birth = request.form.get("date_of_birth", "").strip()
        enrollment_date = request.form.get("enrollment_date", "").strip()
        guardian_name = request.form.get("guardian_name", "").strip()
        guardian_phone = request.form.get("guardian_phone", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()
        status = request.form.get("status", "Active").strip()

        if not all([first_name, last_name, email, phone, enrollment_date]):
            cursor.execute("SELECT * FROM student WHERE student_id=%s", (student_id,))
            student = cursor.fetchone()
            return render_template("edit_student.html", student=student, error="First Name, Last Name, Email, Phone, and Enrollment Date are required")

        try:
            cursor.execute(
                """
                UPDATE student
                SET first_name=%s, last_name=%s, email=%s, phone=%s, date_of_birth=%s,
                    enrollment_date=%s, guardian_name=%s, guardian_phone=%s, 
                    address=%s, city=%s, state=%s, status=%s
                WHERE student_id=%s
                """,
                (first_name, last_name, email, phone, date_of_birth if date_of_birth else None,
                 enrollment_date, guardian_name, guardian_phone, address, city, state, status, student_id),
            )
            db.commit()
            return redirect("/students")
        except Exception as err:
            cursor.execute("SELECT * FROM student WHERE student_id=%s", (student_id,))
            student = cursor.fetchone()
            db.rollback()
            if "UNIQUE" in str(err).upper():
                return render_template("edit_student.html", student=student, error="Email or phone already exists")
            return render_template("edit_student.html", student=student, error=f"Error updating student: {err}")

    cursor.execute("SELECT * FROM student WHERE student_id=%s", (student_id,))
    student = cursor.fetchone()
    if not student:
        return redirect("/students")
    return render_template("edit_student.html", student=student)


@students_bp.route("/delete_student/<int:student_id>")
def delete_student(student_id):
    db, cursor = get_db_connection()
    try:
        # First, find the room_id that the student is allocated to
        cursor.execute(
            "SELECT room_id FROM allocation WHERE student_id=%s AND status='Active'",
            (student_id,)
        )
        allocation = cursor.fetchone()
        
        # If student has an active allocation, decrement room occupancy
        if allocation:
            room_id = allocation["room_id"]
            cursor.execute(
                "UPDATE room SET occupied = occupied - 1 WHERE room_id=%s AND occupied > 0",
                (room_id,)
            )
            # Update status to Available if it was Full
            cursor.execute(
                "UPDATE room SET status = 'Available' WHERE room_id=%s AND occupied < capacity AND status = 'Full'",
                (room_id,)
            )
        
        # Delete related records
        cursor.execute("DELETE FROM rent WHERE student_id=%s", (student_id,))
        cursor.execute("DELETE FROM allocation WHERE student_id=%s", (student_id,))
        cursor.execute("DELETE FROM student WHERE student_id=%s", (student_id,))
        
        db.commit()
    except Exception as err:
        print(f"Error deleting student: {err}")
        db.rollback()
    return redirect("/students")
