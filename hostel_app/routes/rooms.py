import mysql.connector
from flask import Blueprint, redirect, render_template, request

from hostel_app.auth import login_required
from hostel_app.db import get_db_connection


rooms_bp = Blueprint("rooms", __name__)


@rooms_bp.route("/add_room", methods=["GET", "POST"])
@login_required
def add_room():
    if request.method == "POST":
        try:
            room_no = request.form.get("room_no", "").strip()
            room_type = request.form.get("room_type", "Non-AC")
            capacity = request.form.get("capacity", 0)
            price_per_month = request.form.get("price_per_month", 0)

            if not room_no or not capacity or not price_per_month:
                return render_template("add_room.html", error="All fields required")

            db, cursor = get_db_connection()
            cursor.execute(
                """
                INSERT INTO room (room_no, room_type, capacity, price_per_month, status)
                VALUES (%s, %s, %s, %s, 'Available')
                """,
                (room_no, room_type, int(capacity), float(price_per_month)),
            )
            db.commit()
            return redirect("/rooms")
        except mysql.connector.Error as err:
            if err.errno == 1062:
                return render_template("add_room.html", error="Room number already exists")
            return render_template("add_room.html", error="Error adding room")

    return render_template("add_room.html")


@rooms_bp.route("/rooms")
@login_required
def rooms():
    try:
        _, cursor = get_db_connection()
        cursor.execute(
            """
            SELECT * FROM room
            ORDER BY room_no ASC
            """
        )
        data = cursor.fetchall()
        return render_template("rooms.html", rooms=data)
    except Exception:
        return render_template("rooms.html", rooms=[], error="Error loading rooms")


@rooms_bp.route("/edit_room/<int:room_id>", methods=["GET", "POST"])
@login_required
def edit_room(room_id):
    db, cursor = get_db_connection()

    if request.method == "POST":
        try:
            room_no = request.form.get("room_no", "").strip()
            room_type = request.form.get("room_type", "Non-AC")
            capacity = request.form.get("capacity", 0)
            price_per_month = request.form.get("price_per_month", 0)

            cursor.execute(
                """
                UPDATE room
                SET room_no=%s, room_type=%s, capacity=%s, price_per_month=%s
                WHERE room_id=%s
                """,
                (room_no, room_type, int(capacity), float(price_per_month), room_id),
            )
            db.commit()
            return redirect("/rooms")
        except Exception:
            return render_template("edit_room.html", error="Error updating room")

    try:
        cursor.execute("SELECT * FROM room WHERE room_id=%s", (room_id,))
        room = cursor.fetchone()
        return render_template("edit_room.html", room=room)
    except Exception:
        return redirect("/rooms")


@rooms_bp.route("/delete_room/<int:room_id>")
@login_required
def delete_room(room_id):
    db, cursor = get_db_connection()
    cursor.execute("DELETE FROM allocation WHERE room_id=%s", (room_id,))
    db.commit()
    cursor.execute("DELETE FROM room WHERE room_id=%s", (room_id,))
    db.commit()
    return redirect("/rooms")
