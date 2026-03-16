from datetime import datetime

from flask import Blueprint, redirect, render_template, request, session

from hostel_app.auth import login_required
from hostel_app.db import get_db_connection


expenses_bp = Blueprint("expenses", __name__)


@expenses_bp.route("/add_expense", methods=["GET", "POST"])
@login_required
def add_expense():
    if request.method == "POST":
        try:
            expense_type = request.form.get("expense_type", "").strip()
            amount = request.form.get("amount", 0)
            expense_date = request.form.get("expense_date", datetime.now().date())
            description = request.form.get("description", "").strip()
            payment_method = request.form.get("payment_method", "Cash")

            if not expense_type or not amount:
                return render_template("add_expense.html", error="Expense type and amount required")

            db, cursor = get_db_connection()
            cursor.execute(
                """
                INSERT INTO expenses (expense_type, amount, expense_date, description, payment_method, approved_by, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'Approved')
                """,
                (expense_type, float(amount), expense_date, description, payment_method, session.get("admin_id")),
            )
            db.commit()
            return redirect("/expenses")
        except Exception as err:
            print(f"Error adding expense: {err}")
            return render_template("add_expense.html", error=f"Error adding expense: {err}")

    return render_template("add_expense.html")


@expenses_bp.route("/expenses")
@login_required
def expenses():
    try:
        _, cursor = get_db_connection()
        cursor.execute(
            """
            SELECT * FROM expenses
            ORDER BY expense_date DESC
            """
        )
        data = cursor.fetchall()
        return render_template("expenses.html", expenses=data)
    except Exception as err:
        print(f"Error: {err}")
        return render_template("expenses.html", expenses=[], error="Error loading expenses")


@expenses_bp.route("/edit_expense/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    db, cursor = get_db_connection()
    try:
        if request.method == "POST":
            expense_type = request.form.get("expense_type", "").strip()
            amount = request.form.get("amount", 0)
            expense_date = request.form.get("expense_date")
            description = request.form.get("description", "").strip()
            payment_method = request.form.get("payment_method", "Cash")

            if not expense_type or not amount:
                cursor.execute("SELECT * FROM expenses WHERE expense_id=%s", (expense_id,))
                expense = cursor.fetchone()
                return render_template("edit_expense.html", expense=expense, error="Expense type and amount required")

            cursor.execute(
                """
                UPDATE expenses
                SET expense_type=%s, amount=%s, expense_date=%s, description=%s, payment_method=%s
                WHERE expense_id=%s
                """,
                (expense_type, float(amount), expense_date, description, payment_method, expense_id),
            )
            db.commit()
            return redirect("/expenses")

        cursor.execute("SELECT * FROM expenses WHERE expense_id=%s", (expense_id,))
        expense = cursor.fetchone()
        if not expense:
            return redirect("/expenses")
        return render_template("edit_expense.html", expense=expense)
    except Exception as err:
        print(f"Error: {err}")
        return redirect("/expenses")


@expenses_bp.route("/delete_expense/<int:expense_id>", methods=["POST"])
@login_required
def delete_expense(expense_id):
    db, cursor = get_db_connection()
    try:
        cursor.execute("DELETE FROM expenses WHERE expense_id=%s", (expense_id,))
        db.commit()
    except Exception as err:
        print(f"Error: {err}")
    return redirect("/expenses")
