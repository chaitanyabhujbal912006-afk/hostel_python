# HOSTEL MANAGEMENT SYSTEM - PROJECT DOCUMENTATION

---

## 1. PROJECT OVERVIEW

**Project Name:** Hostel Management System  
**Type:** Web Application (Flask-based)  
**Purpose:** A comprehensive system for managing hostel operations including student records, room allocations, rent collection, and expense tracking.  
**Target Users:** Hostel administrators and managers  

---

## 2. TECHNOLOGY STACK

| Technology | Purpose |
|-----------|---------|
| **Backend Framework** | Flask (Python) |
| **Database** | MySQL (Primary) / SQLite (Fallback) |
| **Frontend** | HTML5, CSS3, Jinja2 Templates |
| **Connector** | mysql-connector-python |
| **Server Runtime** | Python 3.x |

---

## 3. DATABASE SCHEMA

### Database Entities:

#### 3.1 **admin** Table
Stores administrator authentication credentials.

```
Columns:
- admin_id (INT, Primary Key, Auto Increment)
- username (VARCHAR(50), UNIQUE, NOT NULL)
- password (VARCHAR(255), NOT NULL) - Hashed passwords
- email (VARCHAR(100), UNIQUE)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- is_active (BOOLEAN, Default: TRUE)

Indexes: idx_username
```

#### 3.2 **room** Table
Manages hostel room information and availability.

```
Columns:
- room_id (INT, Primary Key, Auto Increment)
- room_no (VARCHAR(20), UNIQUE, NOT NULL) - Room identifier
- room_type (ENUM: 'AC', 'Non-AC', Default: 'Non-AC')
- capacity (INT, NOT NULL, > 0) - Total capacity per room
- occupied (INT, Default: 0) - Current occupancy count
- price_per_month (DECIMAL(10,2), NOT NULL, > 0)
- status (ENUM: 'Available', 'Full', 'Maintenance', Default: 'Available')
- description (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Indexes: idx_status, idx_room_no
```

#### 3.3 **student** Table
Stores detailed student information.

```
Columns:
- student_id (INT, Primary Key, Auto Increment)
- first_name (VARCHAR(50), NOT NULL)
- last_name (VARCHAR(50), NOT NULL)
- email (VARCHAR(100), UNIQUE, NOT NULL)
- phone (VARCHAR(20), UNIQUE, NOT NULL)
- date_of_birth (DATE)
- enrollment_date (DATE, Default: CURDATE())
- guardian_name (VARCHAR(100))
- guardian_phone (VARCHAR(20))
- address (TEXT)
- city (VARCHAR(50))
- state (VARCHAR(50))
- status (ENUM: 'Active', 'Inactive', 'Left', Default: 'Active')
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Indexes: idx_email, idx_phone, idx_status, idx_enrollment_date
```

#### 3.4 **allocation** Table
Tracks room assignments to students (one-to-one relationship).

```
Columns:
- allocation_id (INT, Primary Key, Auto Increment)
- student_id (INT, UNIQUE, NOT NULL) - One room per student
- room_id (INT, NOT NULL)
- allocation_date (DATE, Default: CURDATE())
- expected_release_date (DATE)
- actual_release_date (DATE)
- status (ENUM: 'Active', 'Released', 'Transferred', Default: 'Active')
- notes (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Foreign Keys:
- FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE
- FOREIGN KEY (room_id) REFERENCES room(room_id) ON DELETE RESTRICT

Indexes: idx_status, idx_allocation_date
Constraints: actual_release_date >= allocation_date
```

#### 3.5 **rent** Table
Records rent payments and payment tracking.

```
Columns:
- rent_id (INT, Primary Key, Auto Increment)
- student_id (INT, NOT NULL)
- room_id (INT, NOT NULL)
- amount (DECIMAL(10,2), NOT NULL, > 0)
- due_date (DATE, NOT NULL)
- paid_date (DATE)
- payment_method (ENUM: 'Cash', 'Check', 'UPI', 'Bank Transfer', 'Other', Default: 'Cash')
- month_year (VARCHAR(7), NOT NULL) - Format: YYYY-MM
- status (ENUM: 'Pending', 'Paid', 'Overdue', 'Cancelled', Default: 'Pending')
- notes (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Foreign Keys:
- FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE
- FOREIGN KEY (room_id) REFERENCES room(room_id) ON DELETE RESTRICT

Indexes: idx_status, idx_month_year, idx_due_date, idx_paid_date, idx_student_id
Unique Constraint: unique_rent (student_id, month_year) - One entry per student per month
```

#### 3.6 **expenses** Table
Tracks hostel operational expenses.

```
Columns:
- expense_id (INT, Primary Key, Auto Increment)
- expense_type (ENUM: 'Electricity', 'Water', 'Maintenance', 'Cleaning', 'Security', 
               'Internet', 'Furniture', 'Kitchen', 'Medical', 'Repairs', 
               'Staff Salary', 'Food', 'Supplies', 'Transport', 'Other')
- amount (DECIMAL(10,2), NOT NULL, > 0)
- expense_date (DATE, NOT NULL, Default: CURDATE())
- description (TEXT)
- payment_method (ENUM: 'Cash', 'Check', 'UPI', 'Bank Transfer', 'Credit Card', 'Other', Default: 'Cash')
- reference_number (VARCHAR(100))
- approved_by (INT) - References admin table
- status (ENUM: 'Pending', 'Approved', 'Rejected', Default: 'Pending')
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Foreign Keys:
- FOREIGN KEY (approved_by) REFERENCES admin(admin_id) ON DELETE SET NULL

Indexes: idx_expense_type, idx_expense_date, idx_status
```

#### 3.7 **maintenance_log** Table
Tracks maintenance requests and repairs.

```
Columns:
- maintenance_id (INT, Primary Key, Auto Increment)
- room_id (INT, NOT NULL)
- issue_description (TEXT, NOT NULL)
- [Additional columns as needed]

Foreign Key:
- FOREIGN KEY (room_id) REFERENCES room(room_id) ON DELETE RESTRICT
```

---

## 4. CORE FEATURES & MODULES

### 4.1 Dashboard Module
**Route:** `/dashboard`  
**File:** `hostel_app/routes/dashboard.py`

**Functionality:**
- Displays system overview with key metrics
- Shows total student count
- Shows total rooms count
- Displays occupancy statistics:
  - Total occupied beds
  - Total available beds
- Shows financial metrics:
  - Total expenses
  - Rent collection status (Paid/Unpaid)
  - Rent collection percentage
  - Total rent collected amount
- Displays expense data trends by date

**Key Queries:**
- Count total students
- Count total rooms
- Calculate total expenses
- Get expense breakdown by date
- Calculate occupancy metrics
- Track rent payment statistics

---

### 4.2 Student Management Module
**Route Prefix:** `/students`  
**File:** `hostel_app/routes/students.py`

**Routes:**
1. **GET/POST `/add_student`** - Add new student
2. **GET `/students`** - View all students with allocation status
3. **GET/POST `/edit_student/<student_id>`** - Edit student details
4. **GET `/delete_student/<student_id>`** - Delete student record

**Features:**
- Add student with personal details
- View all active/inactive students
- Edit student information
- Delete student records
- Automatic student-room allocation tracking
- Student status management (Active, Inactive, Left)

**Fields Managed:**
- First name, Last name
- Email (UNIQUE), Phone (UNIQUE)
- Date of birth
- Guardian name & phone
- Address, City, State
- Enrollment date
- Current room assignment (if allocated)

**Validations:**
- Email uniqueness
- Phone uniqueness
- Required fields validation

---

### 4.3 Room Management Module
**Route Prefix:** `/rooms`  
**File:** `hostel_app/routes/rooms.py`

**Routes:**
1. **GET/POST `/add_room`** - Add new room
2. **GET `/rooms`** - View all rooms
3. **GET/POST `/edit_room/<room_id>`** - Edit room details
4. **GET `/delete_room/<room_id>`** - Delete room

**Features:**
- Create new rooms with details
- View all rooms and their status
- Edit room information
- Delete rooms (cascades to allocations)
- Room capacity tracking
- Occupancy management

**Room Details:**
- Room number (UNIQUE)
- Room type (AC/Non-AC)
- Capacity (max students)
- Current occupancy count
- Price per month
- Room status (Available, Full, Maintenance)
- Description

**Validations:**
- Room number uniqueness
- Capacity must be > 0
- Price must be > 0

---

### 4.4 Room Allocation Module
**Route Prefix:** `/allocations`  
**File:** `hostel_app/routes/allocations.py`

**Routes:**
1. **GET/POST `/allocate`** - Allocate student to room
2. **GET `/allocations`** - View all active allocations
3. **GET/POST `/edit_allocation/<allocation_id>`** - Modify allocation
4. **GET `/delete_allocation/<allocation_id>`** - Release student from room

**Features:**
- Allocate active students to available rooms
- Transfer students between rooms
- View all allocations grouped by room
- Edit allocation details
- Release students from rooms
- Automatic occupancy count updates

**Business Logic:**
- Prevents allocation if room is full (occupied >= capacity)
- One room per student (UNIQUE constraint)
- Automatic room occupancy updates
- Supports student transfers between rooms
- Allocations show sorted by room number and student name

**Allocation States:**
- Active: Current allocation
- Released: Student left
- Transferred: Student moved to different room

---

### 4.5 Rent Management Module
**Route Prefix:** `/rents`  
**File:** `hostel_app/routes/rents.py`

**Routes:**
1. **GET/POST `/add_rent`** - Create rent record
2. **GET `/rents`** - View all rent records with filtering
3. **GET/POST `/edit_rent/<rent_id>`** - Modify rent details
4. **GET `/delete_rent/<rent_id>`** - Delete rent record

**Features:**
- Create rent records for allocated students
- Track monthly rent per student
- Payment tracking and status management
- Support multiple payment methods
- Automatic overdue detection
- Rent collection reporting
- Month-wise billing

**Rent Fields:**
- Student ID
- Room ID
- Amount due
- Due date
- Paid date
- Payment method (Cash, Check, UPI, Bank Transfer, Other)
- Month/Year (Format: YYYY-MM)
- Status (Pending, Paid, Overdue, Cancelled)
- Notes

**Rent Status Logic:**
- **Paid:** When payment is received
- **Overdue:** When due date has passed and not paid
- **Pending:** Default status for unpaid rent
- **Cancelled:** Manually cancelled entries

**Validations:**
- Only allows rent for allocated students
- One rent entry per student per month (UNIQUE constraint)
- Cannot add rent for unallocated students

---

### 4.6 Expense Management Module
**Route Prefix:** `/expenses`  
**File:** `hostel_app/routes/expenses.py`

**Routes:**
1. **GET/POST `/add_expense`** - Record new expense
2. **GET `/expenses`** - View all expenses
3. **GET/POST `/edit_expense/<expense_id>`** - Edit expense details
4. **GET `/delete_expense/<expense_id>`** - Delete expense record

**Features:**
- Record hostel operational expenses
- Categorize expenses by type
- Track payment methods
- Approval workflow (Pending/Approved/Rejected)
- Expense reporting and analysis
- Date-wise expense tracking

**Expense Categories:**
- Electricity
- Water
- Maintenance
- Cleaning
- Security
- Internet
- Furniture
- Kitchen
- Medical
- Repairs
- Staff Salary
- Food
- Supplies
- Transport
- Other

**Expense Fields:**
- Type (dropdown)
- Amount
- Expense date
- Description
- Payment method
- Reference number
- Approved by (admin ID)
- Status (Pending, Approved, Rejected)

---

## 5. APPLICATION FLOW

### 5.1 User Journey - System Administrator

```
1. Access Application
   ↓
2. Dashboard (Overview)
   ├─ View key metrics
   ├─ Check occupancy
   ├─ Review expenses
   └─ Monitor rent collection
   ↓
3. Module Navigation
   ├─ Students Management
   │  ├─ Add new student
   │  ├─ View all students
   │  ├─ Edit student details
   │  └─ Delete student
   │
   ├─ Rooms Management
   │  ├─ Add new room
   │  ├─ View all rooms
   │  ├─ Edit room details
   │  └─ Delete room
   │
   ├─ Allocations Management
   │  ├─ Allocate student to room
   │  ├─ View all allocations
   │  ├─ Transfer student
   │  └─ Release student
   │
   ├─ Rent Management
   │  ├─ Add rent record
   │  ├─ View all rent details
   │  ├─ Mark as paid
   │  └─ Track overdue payments
   │
   └─ Expenses Management
      ├─ Add new expense
      ├─ View expenses
      ├─ Edit expense
      └─ Categorize expenses
```

### 5.2 Room Allocation Flow

```
Step 1: Student Registration
├─ Add student to system
├─ Set student status to "Active"
└─ Student details stored in database

Step 2: Check Room Availability
├─ View all rooms
├─ Check capacity vs occupancy
└─ Identify available rooms

Step 3: Allocate Student
├─ Select student
├─ Select available room
├─ System checks:
│  ├─ Is room capacity available?
│  └─ Does student already have allocation?
├─ If transfer: Release old allocation
├─ Create new allocation record
└─ Update room occupancy count

Step 4: Monitor Allocation
├─ View active allocations grouped by room
├─ Edit allocation details
├─ Release student when leaving
└─ Update room status automatically
```

### 5.3 Rent Collection Flow

```
Step 1: Create Rent Record
├─ Student must be allocated to a room
├─ Enter rent amount
├─ Set due date
├─ Assign to month/year
└─ Set initial status to "Pending"

Step 2: Track Payment
├─ Mark as "Paid" when payment received
├─ Record payment date
├─ Select payment method
├─ Update rent record

Step 3: Monitor Overdue
├─ System automatically marks unpaid rent as "Overdue"
├─ If due_date < today AND status != 'Paid'
└─ Status = "Overdue"

Step 4: Reporting
├─ Dashboard shows rent collection percentage
├─ Shows paid vs unpaid count
├─ Displays total collected amount
└─ Tracks trends over time
```

### 5.4 Expense Tracking Flow

```
Step 1: Record Expense
├─ Select expense category
├─ Enter amount
├─ Set expense date
├─ Add description
├─ Select payment method
└─ Set status (usually "Approved")

Step 2: Categorization
├─ Expense type helps in analysis
├─ Group expenses by category
└─ Track category-wise spending

Step 3: Reporting
├─ Dashboard shows total expenses
├─ Displays expense trend by date
├─ Can filter by category
└─ Supports financial analysis
```

---

## 6. API ENDPOINTS & ROUTES

| Module | Method | Endpoint | Functionality |
|--------|--------|----------|---------------|
| **Dashboard** | GET | `/` | Redirect to dashboard |
| | GET | `/dashboard` | View dashboard overview |
| **Students** | GET/POST | `/add_student` | Add new student |
| | GET | `/students` | View all students |
| | GET/POST | `/edit_student/<id>` | Edit student details |
| | GET | `/delete_student/<id>` | Delete student |
| **Rooms** | GET/POST | `/add_room` | Add new room |
| | GET | `/rooms` | View all rooms |
| | GET/POST | `/edit_room/<id>` | Edit room details |
| | GET | `/delete_room/<id>` | Delete room |
| **Allocations** | GET/POST | `/allocate` | Allocate student to room |
| | GET | `/allocations` | View all allocations |
| | GET/POST | `/edit_allocation/<id>` | Edit allocation |
| | GET | `/delete_allocation/<id>` | Release student |
| **Rents** | GET/POST | `/add_rent` | Add rent record |
| | GET | `/rents` | View all rent records |
| | GET/POST | `/edit_rent/<id>` | Edit rent details |
| | GET | `/delete_rent/<id>` | Delete rent |
| **Expenses** | GET/POST | `/add_expense` | Add expense |
| | GET | `/expenses` | View expenses |
| | GET/POST | `/edit_expense/<id>` | Edit expense |
| | GET | `/delete_expense/<id>` | Delete expense |

---

## 7. PROJECT STRUCTURE

```
hostel_python/
│
├── app.py                          # Flask app entry point
├── init_db.py                      # MySQL database initialization script
├── update_password.py              # Utility for password updates
├── database_schema.sql             # MySQL schema definition
├── database_sqlite.sql             # SQLite schema definition
├── hostel.db                       # SQLite database (fallback)
│
├── hostel_app/                     # Main Flask application package
│   ├── __init__.py                 # Flask app factory (create_app)
│   ├── db.py                       # Database connection management
│   │
│   └── routes/                     # Route blueprints
│       ├── __init__.py
│       ├── dashboard.py            # Dashboard metrics endpoint
│       ├── students.py             # Student CRUD operations
│       ├── rooms.py                # Room CRUD operations
│       ├── allocations.py          # Allocation management
│       ├── rents.py                # Rent tracking & management
│       └── expenses.py             # Expense recording & tracking
│
├── templates/                      # Jinja2 HTML templates
│   ├── base.html                   # Base template (layout)
│   ├── sidebar.html                # Navigation sidebar
│   ├── dashboard.html              # Dashboard page
│   ├── add_student.html            # Student registration form
│   ├── students.html               # Students list page
│   ├── edit_student.html           # Student edit form
│   ├── add_room.html               # Room creation form
│   ├── rooms.html                  # Rooms list page
│   ├── edit_room.html              # Room edit form
│   ├── allocate.html               # Room allocation form
│   ├── allocations.html            # Allocations list page
│   ├── edit_allocation.html        # Allocation edit form
│   ├── add_rent.html               # Rent entry form
│   ├── rents.html                  # Rent records page
│   ├── edit_rent.html              # Rent edit form
│   ├── add_expense.html            # Expense recording form
│   ├── expenses.html               # Expenses list page
│   └── edit_expense.html           # Expense edit form
│
└── static/                         # Static assets
    └── css/
        ├── style.css               # Main stylesheet
        └── premium.css             # Premium theme styles
```

---

## 8. CONFIGURATION & SETUP

### 8.1 Database Configuration

**Environment Variables:**
```
DB_ENGINE       : 'auto'|'mysql'|'sqlite' (Default: auto)
DB_HOST         : MySQL host (Default: localhost)
DB_USER         : MySQL user (Default: root)
DB_PASSWORD     : MySQL password (Default: root123)
DB_NAME         : Database name (Default: hostel_db)
SQLITE_DB_PATH  : SQLite DB file path (Default: hostel.db)
```

### 8.2 Database Initialization

**For MySQL:**
```bash
python init_db.py
```
- Reads `database_schema.sql`
- Creates MySQL database
- Initializes all tables

**For SQLite:**
- Automatically initialized on first connection
- Uses `database_sqlite.sql` schema
- Creates `hostel.db` file

### 8.3 Flask Configuration

**In `hostel_app/__init__.py`:**
- Template folder: `../templates`
- Static folder: `../static`
- Secret key: `your_secure_secret_key_here_change_this` (Change in production)

### 8.4 Database Connection Management

**File:** `hostel_app/db.py`

Features:
- Automatic MySQL/SQLite fallback
- Connection pooling
- Cursor adaptation for MySQL/SQLite compatibility
- SQLite row factory for dict-like access
- Auto-initialization of SQLite schema

---

## 9. KEY BUSINESS RULES & CONSTRAINTS

### 9.1 Student-Room Relationship
- **One student → One room (UNIQUE allocation)**
- Cannot allocate user twice without releasing first
- Supports room transfers
- Cascading deletion: Delete student → Delete allocation

### 9.2 Room Occupancy Management
- Cannot exceed room capacity
- Occupancy count updates automatically
- Room status (Available/Full/Maintenance) based on context
- Full deletion cascades related data

### 9.3 Rent Management
- **One rent entry per student per month (UNIQUE constraint)**
- Only for allocated students
- Automatic overdue detection (due_date < today)
- Payment tracking with multiple methods
- Status transitions: Pending → Paid/Overdue/Cancelled

### 9.4 Data Integrity
- Foreign key constraints enforced
- Date validations (release_date >= allocation_date)
- Amount validations (> 0)
- Email and phone uniqueness at student level
- Room number uniqueness

---

## 10. KEY FEATURES SUMMARY

| Feature | Module | Status |
|---------|--------|--------|
| Student Registration & Management | Students | ✓ Active |
| Room Management | Rooms | ✓ Active |
| Room Allocation & Transfer | Allocations | ✓ Active |
| Rent Tracking & Payment | Rents | ✓ Active |
| Expense Management | Expenses | ✓ Active |
| Dashboard with Metrics | Dashboard | ✓ Active |
| Database Dual Support (MySQL/SQLite) | DB | ✓ Active |
| Admin Authentication | Admin | ✓ Present |
| Rent Overdue Detection | Rents | ✓ Active |
| Expense Categorization | Expenses | ✓ Active |
| Occupancy Tracking | Rooms | ✓ Active |
| Payment Methods Support | Rents/Expenses | ✓ Active |

---

## 11. DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                    HOSTEL MANAGEMENT SYSTEM                     │
└─────────────────────────────────────────────────────────────────┘

                         Dashboard (Overview)
                                │
                    ┌───────────┼───────────┐
                    ↓           ↓           ↓
            ┌──────────────┐ ┌───────────┐ ┌──────────────┐
            │   Students   │ │   Rooms   │ │ Allocations  │
            └──────────────┘ └───────────┘ └──────────────┘
                    │              │              │
                    └──────────┬───┴──────────────┘
                               ↓
                    ┌──────────────────────┐
                    │   Active Rentals     │
                    └──────────────────────┘
                               ↓
                    ┌──────────────────────┐
                    │  Rent Management &   │
                    │  Payment Tracking    │
                    └──────────────────────┘
                               ↓
                    ┌──────────────────────┐
                    │   Expense Tracking   │
                    │   & Categorization   │
                    └──────────────────────┘
                               ↓
                    ┌──────────────────────┐
                    │  Financial Reports   │
                    │  & Dashboard Metrics │
                    └──────────────────────┘
```

---

## 12. TECHNICAL SPECIFICATIONS

| Aspect | Details |
|--------|---------|
| **Framework** | Flask 2.x |
| **Language** | Python 3.x |
| **Primary DB** | MySQL 5.7+ / 8.0+ |
| **Fallback DB** | SQLite 3 |
| **ORM/Query** | Direct SQL with mysql-connector-python |
| **Frontend** | HTML5 + CSS3 + Jinja2 Templates |
| **Session Management** | Flask Sessions |
| **Authentication** | Admin table (future implementation) |
| **Validation** | Client-side & Server-side |
| **Error Handling** | Try-catch with user feedback |

---

## 13. FUTURE ENHANCEMENTS (Potential)

1. **Authentication & Authorization**
   - Login system for admins
   - Role-based access control
   - Session management

2. **Reporting**
   - Monthly reports (PDF export)
   - Financial summaries
   - Student records reports
   - Occupancy analytics

3. **Analytics**
   - Advanced financial dashboards
   - Predictive analytics for occupancy
   - Expense trend analysis

4. **Communication**
   - Email notifications for pending rent
   - SMS alerts
   - Hostel announcements

5. **Mobile Application**
   - Mobile app for rent payment tracking
   - Student portal

6. **API**
   - RESTful API for integrations
   - Third-party payment gateway integration

---

## 14. SECURITY CONSIDERATIONS

**Current Implementation:**
- Database connection with credentials (environment variables recommended)
- Input validation on forms
- SQL parameterization to prevent SQL injection

**Recommended Enhancements:**
- Change default secret key
- Implement HTTPS
- Add auth layer with password hashing (bcrypt)
- Input sanitization
- CSRF protection
- Rate limiting
- Database backups

---

## 15. INSTALLATION & EXECUTION

### Installation Steps:
1. Install Python 3.x
2. Create virtual environment: `python -m venv .venv`
3. Activate environment: `.\.venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install flask mysql-connector-python`
5. Set environment variables for DB connection
6. Initialize database: `python init_db.py`

### Running Application:
```bash
python app.py
```
- Application runs on `http://localhost:5000`
- Debug mode enabled by default

---

**Document Version:** 1.0  
**Last Updated:** Current  
**Status:** Complete Overview of Hostel Management System

---
