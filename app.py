from flask import Flask, render_template, request, redirect, session
import mysql.connector
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secure_secret_key_here_change_this"

# Global connection variables
db = None
cursor = None

def get_db_connection():
    """Create a database connection"""
    global db, cursor
    try:
        if db is None or not db.is_connected():
            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="shreeswamisamarth",
                database="hostel_db"
            )
            cursor = db.cursor(dictionary=True)
        return db, cursor
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return None, None

# Initialize connection on startup
try:
    db, cursor = get_db_connection()
    print("✅ Database connected successfully")
except Exception as e:
    print(f"❌ Database connection failed: {e}")

# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template("login.html", error="Username and password required")

        try:
            cursor.execute("SELECT * FROM admin WHERE username=%s", (username,))
            admin = cursor.fetchone()

            if admin and admin["password"] == password:
                session["admin"] = username
                session["admin_id"] = admin["admin_id"]
                return redirect("/dashboard")
            else:
                return render_template("login.html", error="Invalid username or password")
        except Exception as e:
            print(f"Login error: {e}")
            return render_template("login.html", error="Login error. Try again.")

    return render_template("login.html")


# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/")

    # Counts
    cursor.execute("SELECT COUNT(*) AS total_students FROM student")
    students = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) AS total_rooms FROM room")
    rooms = cursor.fetchone()

    cursor.execute("SELECT IFNULL(SUM(amount),0) AS total_expense FROM expenses")
    expenses = cursor.fetchone()

    # Expense chart (group by date)
    cursor.execute("""
        SELECT expense_date, SUM(amount) AS total
        FROM expenses
        GROUP BY expense_date
    """)
    expense_data = cursor.fetchall()

    # Overall occupancy (occupied beds vs available beds)
    cursor.execute("""
        SELECT 
            SUM(occupied) AS total_occupied,
            SUM(capacity) AS total_capacity
        FROM room
    """)
    occupancy = cursor.fetchone()
    total_occupied = occupancy["total_occupied"] or 0
    total_available = (occupancy["total_capacity"] or 0) - total_occupied

    # Rent collection data
    cursor.execute("""
        SELECT COUNT(*) AS total_rent FROM rent WHERE status='paid'
    """)
    paid_rent = cursor.fetchone()

    cursor.execute("""
        SELECT COUNT(*) AS total_rent FROM rent WHERE status='unpaid'
    """)
    unpaid_rent = cursor.fetchone()

    cursor.execute("""
        SELECT IFNULL(SUM(amount),0) AS total_collected FROM rent WHERE status='paid'
    """)
    rent_collected = cursor.fetchone()

    total_paid_rent = paid_rent["total_rent"] or 0
    total_unpaid_rent = unpaid_rent["total_rent"] or 0
    total_rent = total_paid_rent + total_unpaid_rent
    rent_collection_percentage = int((total_paid_rent / total_rent * 100)) if total_rent > 0 else 0

    return render_template(
        "dashboard.html",
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
        current_date=datetime.now().strftime("%A, %B %d, %Y")
    )


# ADD STUDENT
@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    if "admin" not in session:
        return redirect("/")

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

            query = """
            INSERT INTO student (first_name, last_name, email, phone, guardian_name, guardian_phone, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Active')
            """
            cursor.execute(query, (first_name, last_name, email, phone, guardian_name, guardian_phone))
            db.commit()
            return redirect("/students")
        except mysql.connector.Error as err:
            if err.errno == 1062:  # Duplicate entry
                return render_template("add_student.html", error="Email or phone already exists")
            return render_template("add_student.html", error="Error adding student")

    return render_template("add_student.html")


# LIST STUDENTS
@app.route("/students")
def students():
    if "admin" not in session:
        return redirect("/")

    try:
        cursor.execute("""
            SELECT s.*, r.room_no 
            FROM student s
            LEFT JOIN allocation a ON s.student_id = a.student_id AND a.status = 'Active'
            LEFT JOIN room r ON a.room_id = r.room_id
            WHERE s.status IN ('Active', 'Inactive')
            ORDER BY s.enrollment_date DESC
        """)
        data = cursor.fetchall()
        return render_template("students.html", students=data)
    except Exception as e:
        return render_template("students.html", students=[], error="Error loading students")


# EDIT STUDENT
@app.route("/edit_student/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    if "admin" not in session:
        return redirect("/")

    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        phone = request.form["phone"]

        query = """
        UPDATE student 
        SET first_name=%s, last_name=%s, email=%s, phone=%s 
        WHERE student_id=%s
        """
        cursor.execute(query, (first_name, last_name, email, phone, student_id))
        db.commit()

        return redirect("/students")

    cursor.execute("SELECT * FROM student WHERE student_id=%s", (student_id,))
    student = cursor.fetchone()
    return render_template("edit_student.html", student=student)


# DELETE STUDENT
@app.route("/delete_student/<int:student_id>")
def delete_student(student_id):
    if "admin" not in session:
        return redirect("/")

    try:
        # Delete related records (CASCADE is set in DB, but doing it explicitly for clarity)
        cursor.execute("DELETE FROM rent WHERE student_id=%s", (student_id,))
        cursor.execute("DELETE FROM allocation WHERE student_id=%s", (student_id,))
        cursor.execute("DELETE FROM student WHERE student_id=%s", (student_id,))
        db.commit()
        return redirect("/students")
    except Exception as e:
        db.rollback()
        return redirect("/students")


# ADD EXPENSE
@app.route("/add_expense", methods=["GET", "POST"])
def add_expense():
    if "admin" not in session:
        return redirect("/")

    if request.method == "POST":
        try:
            expense_type = request.form.get("expense_type", "").strip()
            amount = request.form.get("amount", 0)
            expense_date = request.form.get("expense_date", datetime.now().date())
            description = request.form.get("description", "").strip()
            payment_method = request.form.get("payment_method", "Cash")

            if not expense_type or not amount:
                return render_template("add_expense.html", error="Expense type and amount required")

            query = """
            INSERT INTO expenses (expense_type, amount, expense_date, description, payment_method, approved_by, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Approved')
            """
            print(f"DEBUG: Adding expense - Type: {expense_type}, Amount: {amount}, Date: {expense_date}")
            cursor.execute(query, (expense_type, float(amount), expense_date, description, payment_method, session.get("admin_id")))
            db.commit()
            print(f"DEBUG: Expense added successfully")
            return redirect("/expenses")
        except Exception as e:
            print(f"Error adding expense: {e}")
            return render_template("add_expense.html", error=f"Error adding expense: {str(e)}")

    return render_template("add_expense.html")


# LIST EXPENSES
@app.route("/expenses")
def expenses():
    if "admin" not in session:
        return redirect("/")

    try:
        # Reconnect if needed
        global db, cursor
        db, cursor = get_db_connection()
        
        cursor.execute("""
            SELECT * FROM expenses
            ORDER BY expense_date DESC
        """)
        data = cursor.fetchall()
        print(f"DEBUG: Found {len(data)} expenses")
        print(f"DEBUG: Data = {data}")
        return render_template("expenses.html", expenses=data)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return render_template("expenses.html", expenses=[], error="Error loading expenses")


# EDIT EXPENSE
@app.route("/edit_expense/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    if "admin" not in session:
        return redirect("/")

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

            cursor.execute("""
                UPDATE expenses 
                SET expense_type=%s, amount=%s, expense_date=%s, description=%s, payment_method=%s
                WHERE expense_id=%s
            """, (expense_type, float(amount), expense_date, description, payment_method, expense_id))
            db.commit()
            return redirect("/expenses")

        cursor.execute("SELECT * FROM expenses WHERE expense_id=%s", (expense_id,))
        expense = cursor.fetchone()
        if not expense:
            return redirect("/expenses")
        return render_template("edit_expense.html", expense=expense)
    except Exception as e:
        print(f"Error: {e}")
        return redirect("/expenses")


# DELETE EXPENSE
@app.route("/delete_expense/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    if "admin" not in session:
        return redirect("/")

    try:
        cursor.execute("DELETE FROM expenses WHERE expense_id=%s", (expense_id,))
        db.commit()
        return redirect("/expenses")
    except Exception as e:
        print(f"Error: {e}")
        return redirect("/expenses")
# ADD ROOM
@app.route("/add_room", methods=["GET", "POST"])
def add_room():
    if "admin" not in session:
        return redirect("/")

    if request.method == "POST":
        try:
            room_no = request.form.get("room_no", "").strip()
            room_type = request.form.get("room_type", "Non-AC")
            capacity = request.form.get("capacity", 0)
            price_per_month = request.form.get("price_per_month", 0)

            if not room_no or not capacity or not price_per_month:
                return render_template("add_room.html", error="All fields required")

            query = """
            INSERT INTO room (room_no, room_type, capacity, price_per_month, status)
            VALUES (%s, %s, %s, %s, 'Available')
            """
            cursor.execute(query, (room_no, room_type, int(capacity), float(price_per_month)))
            db.commit()
            return redirect("/rooms")
        except mysql.connector.Error as err:
            if err.errno == 1062:  # Duplicate room_no
                return render_template("add_room.html", error="Room number already exists")
            return render_template("add_room.html", error="Error adding room")

    return render_template("add_room.html")


# LIST ROOMS
@app.route("/rooms")
def rooms():
    if "admin" not in session:
        return redirect("/")

    try:
        cursor.execute("""
            SELECT * FROM room
            ORDER BY room_no ASC
        """)
        data = cursor.fetchall()
        return render_template("rooms.html", rooms=data)
    except Exception as e:
        return render_template("rooms.html", rooms=[], error="Error loading rooms")


# EDIT ROOM
@app.route("/edit_room/<int:room_id>", methods=["GET", "POST"])
def edit_room(room_id):
    if "admin" not in session:
        return redirect("/")

    if request.method == "POST":
        try:
            room_no = request.form.get("room_no", "").strip()
            room_type = request.form.get("room_type", "Non-AC")
            capacity = request.form.get("capacity", 0)
            price_per_month = request.form.get("price_per_month", 0)

            query = """
            UPDATE room
            SET room_no=%s, room_type=%s, capacity=%s, price_per_month=%s
            WHERE room_id=%s
            """
            cursor.execute(query, (room_no, room_type, int(capacity), float(price_per_month), room_id))
            db.commit()
            return redirect("/rooms")
        except Exception as e:
            return render_template("edit_room.html", error="Error updating room")

    try:
        cursor.execute("SELECT * FROM room WHERE room_id=%s", (room_id,))
        room = cursor.fetchone()
        return render_template("edit_room.html", room=room)
    except Exception as e:
        return redirect("/rooms")


# DELETE ROOM
@app.route("/delete_room/<int:room_id>")
def delete_room(room_id):
    if "admin" not in session:
        return redirect("/")

    # Delete related allocations first
    cursor.execute("DELETE FROM allocation WHERE room_id=%s", (room_id,))
    db.commit()

    # Delete the room
    cursor.execute("DELETE FROM room WHERE room_id=%s", (room_id,))
    db.commit()

    return redirect("/rooms")

# ALLOCATE STUDENT TO ROOM
@app.route("/allocate", methods=["GET", "POST"])
def allocate():
    if "admin" not in session:
        return redirect("/")

    if request.method == "POST":
        try:
            student_id = request.form.get("student_id", 0)
            room_id = request.form.get("room_id", 0)

            # Check room capacity
            cursor.execute("SELECT capacity, occupied FROM room WHERE room_id=%s", (room_id,))
            room = cursor.fetchone()
            
            if not room:
                return render_template("allocate.html", error="Room not found")
            
            if room["occupied"] >= room["capacity"]:
                return render_template("allocate.html", error="Room is full. Cannot allocate.")

            # Check if student already allocated
            cursor.execute("SELECT room_id FROM allocation WHERE student_id=%s AND status='Active'", (student_id,))
            existing_allocation = cursor.fetchone()

            if existing_allocation:
                old_room_id = existing_allocation["room_id"]
                cursor.execute("UPDATE room SET occupied = occupied - 1 WHERE room_id=%s", (old_room_id,))
                cursor.execute("UPDATE allocation SET status='Transferred' WHERE student_id=%s", (student_id,))

            # Create new allocation
            query = "INSERT INTO allocation (student_id, room_id, status) VALUES (%s, %s, 'Active')"
            cursor.execute(query, (student_id, room_id))
            cursor.execute("UPDATE room SET occupied = occupied + 1 WHERE room_id=%s", (room_id,))
            db.commit()
            return redirect("/allocations")
        except Exception as e:
            return render_template("allocate.html", error="Error allocating room")

    try:
        cursor.execute("SELECT student_id, first_name, last_name FROM student WHERE status='Active'")
        students = cursor.fetchall()
        cursor.execute("SELECT room_id, room_no, capacity, occupied FROM room WHERE status='Available'")
        rooms = cursor.fetchall()
        return render_template("allocate.html", students=students, rooms=rooms)
    except Exception as e:
        return render_template("allocate.html", students=[], rooms=[], error="Error loading data")


# VIEW ALLOCATIONS
@app.route("/allocations")
def allocations():
    if "admin" not in session:
        return redirect("/")

    cursor.execute("""
        SELECT a.allocation_id, s.first_name, s.last_name, r.room_no, r.room_id
        FROM allocation a
        JOIN student s ON a.student_id = s.student_id
        JOIN room r ON a.room_id = r.room_id
        ORDER BY r.room_no, s.first_name
    """)
    data = cursor.fetchall()

    # Group allocations by room
    rooms_dict = {}
    for alloc in data:
        room_no = alloc["room_no"]
        room_id = alloc["room_id"]
        
        if room_no not in rooms_dict:
            rooms_dict[room_no] = {
                "room_id": room_id,
                "room_no": room_no,
                "students": []
            }
        
        rooms_dict[room_no]["students"].append({
            "allocation_id": alloc["allocation_id"],
            "first_name": alloc["first_name"],
            "last_name": alloc["last_name"]
        })
    
    # Convert to sorted list
    rooms_list = sorted(rooms_dict.values(), key=lambda x: x["room_no"])

    return render_template("allocations.html", rooms=rooms_list)


# EDIT ALLOCATION
@app.route("/edit_allocation/<int:allocation_id>", methods=["GET", "POST"])
def edit_allocation(allocation_id):
    if "admin" not in session:
        return redirect("/")

    if request.method == "POST":
        new_room_id = request.form["room_id"]

        # Get current allocation to find old room
        cursor.execute("SELECT room_id FROM allocation WHERE allocation_id=%s", (allocation_id,))
        current = cursor.fetchone()
        old_room_id = current["room_id"]

        # Only update counts if room is being changed
        if old_room_id != int(new_room_id):
            # Decrease count in old room
            cursor.execute("UPDATE room SET occupied = occupied - 1 WHERE room_id=%s", (old_room_id,))
            # Increase count in new room
            cursor.execute("UPDATE room SET occupied = occupied + 1 WHERE room_id=%s", (new_room_id,))

        # Update allocation
        query = "UPDATE allocation SET room_id=%s WHERE allocation_id=%s"
        cursor.execute(query, (new_room_id, allocation_id))
        db.commit()

        return redirect("/allocations")

    cursor.execute("""
        SELECT a.allocation_id, a.student_id, s.first_name, s.last_name, a.room_id
        FROM allocation a
        JOIN student s ON a.student_id = s.student_id
        WHERE a.allocation_id=%s
    """, (allocation_id,))
    allocation = cursor.fetchone()

    cursor.execute("SELECT room_id, room_no FROM room")
    rooms = cursor.fetchall()

    return render_template("edit_allocation.html", allocation=allocation, rooms=rooms)


# DELETE ALLOCATION
@app.route("/delete_allocation/<int:allocation_id>")
def delete_allocation(allocation_id):
    if "admin" not in session:
        return redirect("/")

    # Get room_id before deleting allocation
    cursor.execute("SELECT room_id FROM allocation WHERE allocation_id=%s", (allocation_id,))
    allocation = cursor.fetchone()
    
    if allocation:
        room_id = allocation["room_id"]
        # Decrease occupied count in room
        cursor.execute("UPDATE room SET occupied = occupied - 1 WHERE room_id=%s", (room_id,))
    
    # Delete allocation
    cursor.execute("DELETE FROM allocation WHERE allocation_id=%s", (allocation_id,))
    db.commit()

    return redirect("/allocations")

# ADD RENT
@app.route("/add_rent", methods=["GET", "POST"])
def add_rent():
    if "admin" not in session:
        return redirect("/")

    if request.method == "POST":
        try:
            student_id = request.form.get("student_id", 0)
            month_year = request.form.get("month_year", "")  # Format: YYYY-MM
            amount = request.form.get("amount", 0)
            due_date = request.form.get("due_date", "")

            # Get room_id from allocation
            cursor.execute("SELECT room_id FROM allocation WHERE student_id=%s AND status='Active'", (student_id,))
            allocation = cursor.fetchone()
            
            if not allocation:
                return render_template("add_rent.html", error="Student not allocated to any room")

            room_id = allocation["room_id"]

            query = """
            INSERT INTO rent (student_id, room_id, amount, due_date, month_year, status, payment_method)
            VALUES (%s, %s, %s, %s, %s, 'Pending', 'Cash')
            """
            cursor.execute(query, (student_id, room_id, float(amount), due_date, month_year))
            db.commit()
            return redirect("/rents")
        except mysql.connector.Error as err:
            if err.errno == 1062:  # Duplicate entry
                return render_template("add_rent.html", error="Rent already recorded for this student/month")
            return render_template("add_rent.html", error="Error adding rent")

    try:
        cursor.execute("SELECT student_id, first_name, last_name FROM student WHERE status='Active'")
        students = cursor.fetchall()
        return render_template("add_rent.html", students=students)
    except Exception as e:
        return render_template("add_rent.html", students=[], error="Error loading students")

# VIEW RENTS
@app.route("/rents")
def rents():
    if "admin" not in session:
        return redirect("/")

    try:
        cursor.execute("""
            SELECT r.rent_id, s.student_id, s.first_name, s.last_name, r.room_id, 
                   r.month_year, r.amount, r.status, r.due_date, r.paid_date
            FROM rent r
            JOIN student s ON r.student_id = s.student_id
            ORDER BY r.due_date DESC
        """)
        data = cursor.fetchall()
        return render_template("rents.html", rents=data)
    except Exception as e:
        return render_template("rents.html", rents=[], error="Error loading rents")


# EDIT RENT
@app.route("/edit_rent/<int:rent_id>", methods=["GET", "POST"])
def edit_rent(rent_id):
    if "admin" not in session:
        return redirect("/")

    try:
        if request.method == "POST":
            amount = request.form.get("amount", 0)
            status = request.form.get("status", "Pending")
            paid_date = request.form.get("paid_date", None)

            query = """
            UPDATE rent 
            SET amount=%s, status=%s, paid_date=%s
            WHERE rent_id=%s
            """
            cursor.execute(query, (float(amount), status, paid_date if paid_date else None, rent_id))
            db.commit()
            return redirect("/rents")

        cursor.execute("SELECT * FROM rent WHERE rent_id=%s", (rent_id,))
        rent = cursor.fetchone()
        if not rent:
            return redirect("/rents")
        return render_template("edit_rent.html", rent=rent)
    except Exception as e:
        print(f"Error: {e}")
        return redirect("/rents")


# DELETE RENT
@app.route("/delete_rent/<int:rent_id>", methods=["POST"])
def delete_rent(rent_id):
    if "admin" not in session:
        return redirect("/")

    try:
        cursor.execute("DELETE FROM rent WHERE rent_id=%s", (rent_id,))
        db.commit()
        return redirect("/rents")
    except Exception as e:
        print(f"Error: {e}")
        return redirect("/rents")

# LOGOUT
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
