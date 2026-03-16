from flask import Blueprint, redirect, render_template, request, session

from hostel_app.db import get_db_connection


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template("login.html", error="Username and password required")

        try:
            _, cursor = get_db_connection()
            cursor.execute("SELECT * FROM admin WHERE username=%s", (username,))
            admin = cursor.fetchone()

            if admin and admin["password"] == password:
                session["admin"] = username
                session["admin_id"] = admin["admin_id"]
                return redirect("/dashboard")

            return render_template("login.html", error="Invalid username or password")
        except Exception as err:
            print(f"Login error: {err}")
            return render_template("login.html", error="Login error. Try again.")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")
