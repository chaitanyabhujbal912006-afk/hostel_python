from flask import Blueprint, redirect, render_template, request

from hostel_app.db import get_db_connection


allocations_bp = Blueprint("allocations", __name__)


@allocations_bp.route("/allocate", methods=["GET", "POST"])
def allocate():
    db, cursor = get_db_connection()

    if request.method == "POST":
        try:
            student_id = int(request.form.get("student_id", 0))
            room_id = int(request.form.get("room_id", 0))

            if not student_id or not room_id:
                return render_template("allocate.html", students=[], rooms=[], error="Student and room are required", active_page="allocate")

            cursor.execute("SELECT capacity FROM room WHERE room_id=%s", (room_id,))
            room = cursor.fetchone()
            if not room:
                return render_allocate_form("Room not found")

            # Check current occupancy by counting active allocations
            cursor.execute("SELECT COUNT(*) as current_occupied FROM allocation WHERE room_id=%s AND status='Active'", (room_id,))
            occupancy = cursor.fetchone()
            current_occupied = occupancy["current_occupied"] if occupancy else 0

            cursor.execute("SELECT allocation_id, room_id FROM allocation WHERE student_id=%s", (student_id,))
            existing_allocation = cursor.fetchone()

            if existing_allocation:
                if existing_allocation["room_id"] == room_id:
                    return redirect("/allocations")

                if current_occupied >= room["capacity"]:
                    return render_allocate_form("Room is full. Cannot allocate.")

                old_room_id = existing_allocation["room_id"]
                cursor.execute("UPDATE room SET occupied = occupied - 1 WHERE room_id=%s", (old_room_id,))
                cursor.execute(
                    """
                    UPDATE allocation
                    SET room_id=%s, status='Active', actual_release_date=NULL
                    WHERE allocation_id=%s
                    """,
                    (room_id, existing_allocation["allocation_id"]),
                )
            else:
                if current_occupied >= room["capacity"]:
                    return render_allocate_form("Room is full. Cannot allocate.")

                cursor.execute(
                    "INSERT INTO allocation (student_id, room_id, status) VALUES (%s, %s, 'Active')",
                    (student_id, room_id),
                )

            cursor.execute("UPDATE room SET occupied = occupied + 1 WHERE room_id=%s", (room_id,))
            db.commit()
            return redirect("/allocations")
        except Exception as err:
            db.rollback()
            print(f"Error allocating room: {err}")
            return render_allocate_form("Error allocating room")

    return render_allocate_form()


@allocations_bp.route("/allocations")
def allocations():
    _, cursor = get_db_connection()
    cursor.execute(
        """
        SELECT a.allocation_id, s.first_name, s.last_name, r.room_no, r.room_id
        FROM allocation a
        JOIN student s ON a.student_id = s.student_id
        JOIN room r ON a.room_id = r.room_id
        WHERE a.status = 'Active'
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
    return render_template("allocations.html", rooms=rooms_list, active_page="allocations")


@allocations_bp.route("/edit_allocation/<int:allocation_id>", methods=["GET", "POST"])
def edit_allocation(allocation_id):
    db, cursor = get_db_connection()

    if request.method == "POST":
        new_room_id = int(request.form["room_id"])
        cursor.execute("SELECT room_id FROM allocation WHERE allocation_id=%s", (allocation_id,))
        current = cursor.fetchone()
        if not current:
            return redirect("/allocations")
        old_room_id = current["room_id"]

        if old_room_id != int(new_room_id):
            # Check if new room has capacity by counting active allocations
            cursor.execute("SELECT COUNT(*) as current_occupied FROM allocation WHERE room_id=%s AND status='Active'", (new_room_id,))
            occupancy = cursor.fetchone()
            current_occupied = occupancy["current_occupied"] if occupancy else 0
            
            cursor.execute("SELECT capacity FROM room WHERE room_id=%s", (new_room_id,))
            new_room = cursor.fetchone()
            if not new_room:
                return redirect("/allocations")
            if current_occupied >= new_room["capacity"]:
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
                return render_template("edit_allocation.html", allocation=allocation, rooms=rooms, error="Selected room is full", active_page="allocations")

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
    return render_template("edit_allocation.html", allocation=allocation, rooms=rooms, active_page="allocations")


@allocations_bp.route("/delete_allocation/<int:allocation_id>")
def delete_allocation(allocation_id):
    db, cursor = get_db_connection()
    cursor.execute("SELECT room_id FROM allocation WHERE allocation_id=%s", (allocation_id,))
    allocation = cursor.fetchone()

    if allocation:
        cursor.execute("UPDATE room SET occupied = occupied - 1 WHERE room_id=%s", (allocation["room_id"],))

        cursor.execute("DELETE FROM allocation WHERE allocation_id=%s", (allocation_id,))
        db.commit()
    return redirect("/allocations")


def render_allocate_form(error=None):
    _, cursor = get_db_connection()
    try:
        cursor.execute(
            """
            SELECT s.student_id, s.first_name, s.last_name
            FROM student s
            LEFT JOIN allocation a ON s.student_id = a.student_id AND a.status = 'Active'
            WHERE s.status='Active'
            ORDER BY s.first_name, s.last_name
            """
        )
        students = cursor.fetchall()
        cursor.execute(
            """
            SELECT r.room_id, r.room_no, r.capacity, COUNT(a.allocation_id) as occupied
            FROM room r
            LEFT JOIN allocation a ON r.room_id = a.room_id AND a.status = 'Active'
            WHERE r.status != 'Maintenance'
            GROUP BY r.room_id
            HAVING COUNT(a.allocation_id) < r.capacity
            ORDER BY r.room_no
            """
        )
        rooms = cursor.fetchall()
        return render_template("allocate.html", students=students, rooms=rooms, error=error, active_page="allocate")
    except Exception:
        return render_template("allocate.html", students=[], rooms=[], error=error or "Error loading data", active_page="allocate")
