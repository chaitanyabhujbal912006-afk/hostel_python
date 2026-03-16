from flask import Blueprint, redirect, render_template, request

from hostel_app.auth import login_required
from hostel_app.db import get_db_connection


allocations_bp = Blueprint("allocations", __name__)


@allocations_bp.route("/allocate", methods=["GET", "POST"])
@login_required
def allocate():
    db, cursor = get_db_connection()

    if request.method == "POST":
        try:
            student_id = request.form.get("student_id", 0)
            room_id = request.form.get("room_id", 0)

            cursor.execute("SELECT capacity, occupied FROM room WHERE room_id=%s", (room_id,))
            room = cursor.fetchone()
            if not room:
                return render_template("allocate.html", error="Room not found")
            if room["occupied"] >= room["capacity"]:
                return render_template("allocate.html", error="Room is full. Cannot allocate.")

            cursor.execute("SELECT room_id FROM allocation WHERE student_id=%s AND status='Active'", (student_id,))
            existing_allocation = cursor.fetchone()

            if existing_allocation:
                old_room_id = existing_allocation["room_id"]
                cursor.execute("UPDATE room SET occupied = occupied - 1 WHERE room_id=%s", (old_room_id,))
                cursor.execute("UPDATE allocation SET status='Transferred' WHERE student_id=%s", (student_id,))

            cursor.execute(
                "INSERT INTO allocation (student_id, room_id, status) VALUES (%s, %s, 'Active')",
                (student_id, room_id),
            )
            cursor.execute("UPDATE room SET occupied = occupied + 1 WHERE room_id=%s", (room_id,))
            db.commit()
            return redirect("/allocations")
        except Exception:
            return render_template("allocate.html", error="Error allocating room")

    try:
        cursor.execute("SELECT student_id, first_name, last_name FROM student WHERE status='Active'")
        students = cursor.fetchall()
        cursor.execute("SELECT room_id, room_no, capacity, occupied FROM room WHERE status='Available'")
        rooms = cursor.fetchall()
        return render_template("allocate.html", students=students, rooms=rooms)
    except Exception:
        return render_template("allocate.html", students=[], rooms=[], error="Error loading data")


@allocations_bp.route("/allocations")
@login_required
def allocations():
    _, cursor = get_db_connection()
    cursor.execute(
        """
        SELECT a.allocation_id, s.first_name, s.last_name, r.room_no, r.room_id
        FROM allocation a
        JOIN student s ON a.student_id = s.student_id
        JOIN room r ON a.room_id = r.room_id
        ORDER BY r.room_no, s.first_name
        """
    )
    data = cursor.fetchall()

    rooms_dict = {}
    for alloc in data:
        room_no = alloc["room_no"]
        room_id = alloc["room_id"]
        if room_no not in rooms_dict:
            rooms_dict[room_no] = {"room_id": room_id, "room_no": room_no, "students": []}
        rooms_dict[room_no]["students"].append(
            {
                "allocation_id": alloc["allocation_id"],
                "first_name": alloc["first_name"],
                "last_name": alloc["last_name"],
            }
        )

    rooms_list = sorted(rooms_dict.values(), key=lambda room: room["room_no"])
    return render_template("allocations.html", rooms=rooms_list)


@allocations_bp.route("/edit_allocation/<int:allocation_id>", methods=["GET", "POST"])
@login_required
def edit_allocation(allocation_id):
    db, cursor = get_db_connection()

    if request.method == "POST":
        new_room_id = request.form["room_id"]
        cursor.execute("SELECT room_id FROM allocation WHERE allocation_id=%s", (allocation_id,))
        current = cursor.fetchone()
        old_room_id = current["room_id"]

        if old_room_id != int(new_room_id):
            cursor.execute("UPDATE room SET occupied = occupied - 1 WHERE room_id=%s", (old_room_id,))
            cursor.execute("UPDATE room SET occupied = occupied + 1 WHERE room_id=%s", (new_room_id,))

        cursor.execute("UPDATE allocation SET room_id=%s WHERE allocation_id=%s", (new_room_id, allocation_id))
        db.commit()
        return redirect("/allocations")

    cursor.execute(
        """
        SELECT a.allocation_id, a.student_id, s.first_name, s.last_name, a.room_id
        FROM allocation a
        JOIN student s ON a.student_id = s.student_id
        WHERE a.allocation_id=%s
        """,
        (allocation_id,),
    )
    allocation = cursor.fetchone()

    cursor.execute("SELECT room_id, room_no FROM room")
    rooms = cursor.fetchall()
    return render_template("edit_allocation.html", allocation=allocation, rooms=rooms)


@allocations_bp.route("/delete_allocation/<int:allocation_id>")
@login_required
def delete_allocation(allocation_id):
    db, cursor = get_db_connection()
    cursor.execute("SELECT room_id FROM allocation WHERE allocation_id=%s", (allocation_id,))
    allocation = cursor.fetchone()

    if allocation:
        cursor.execute("UPDATE room SET occupied = occupied - 1 WHERE room_id=%s", (allocation["room_id"],))

    cursor.execute("DELETE FROM allocation WHERE allocation_id=%s", (allocation_id,))
    db.commit()
    return redirect("/allocations")
