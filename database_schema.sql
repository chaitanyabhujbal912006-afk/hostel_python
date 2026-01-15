-- ============================================
-- HOSTEL MANAGEMENT SYSTEM - DATABASE SCHEMA
-- ============================================
-- Drop existing database if needed
DROP DATABASE IF EXISTS hostel_db;
CREATE DATABASE hostel_db;
USE hostel_db;

-- ============================================
-- 1. ADMIN TABLE (Authentication)
-- ============================================
CREATE TABLE admin (
    admin_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,  -- Will store hashed passwords
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    INDEX idx_username (username)
);

-- ============================================
-- 2. ROOM TABLE (Room Management)
-- ============================================
CREATE TABLE room (
    room_id INT PRIMARY KEY AUTO_INCREMENT,
    room_no VARCHAR(20) NOT NULL UNIQUE,
    room_type ENUM('AC', 'Non-AC') NOT NULL DEFAULT 'Non-AC',
    capacity INT NOT NULL CHECK (capacity > 0),
    occupied INT NOT NULL DEFAULT 0,
    price_per_month DECIMAL(10, 2) NOT NULL CHECK (price_per_month > 0),
    status ENUM('Available', 'Full', 'Maintenance') NOT NULL DEFAULT 'Available',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_status (status),
    INDEX idx_room_no (room_no)
);

-- ============================================
-- 3. STUDENT TABLE (Student Information)
-- ============================================
CREATE TABLE student (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL UNIQUE,
    date_of_birth DATE,
    enrollment_date DATE NOT NULL DEFAULT (CURDATE()),
    guardian_name VARCHAR(100),
    guardian_phone VARCHAR(20),
    address TEXT,
    city VARCHAR(50),
    state VARCHAR(50),
    status ENUM('Active', 'Inactive', 'Left') NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_phone (phone),
    INDEX idx_status (status),
    INDEX idx_enrollment_date (enrollment_date)
);

-- ============================================
-- 4. ALLOCATION TABLE (Room Assignment)
-- ============================================
CREATE TABLE allocation (
    allocation_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL UNIQUE,  -- One room per student
    room_id INT NOT NULL,
    allocation_date DATE NOT NULL DEFAULT (CURDATE()),
    expected_release_date DATE,
    actual_release_date DATE,
    status ENUM('Active', 'Released', 'Transferred') NOT NULL DEFAULT 'Active',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES room(room_id) ON DELETE RESTRICT,
    INDEX idx_status (status),
    INDEX idx_allocation_date (allocation_date),
    CONSTRAINT check_release_date CHECK (actual_release_date IS NULL OR actual_release_date >= allocation_date)
);

-- ============================================
-- 5. RENT TABLE (Rent Payments)
-- ============================================
CREATE TABLE rent (
    rent_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    room_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount > 0),
    due_date DATE NOT NULL,
    paid_date DATE,
    payment_method ENUM('Cash', 'Check', 'UPI', 'Bank Transfer', 'Other') DEFAULT 'Cash',
    month_year VARCHAR(7) NOT NULL,  -- Format: YYYY-MM
    status ENUM('Pending', 'Paid', 'Overdue', 'Cancelled') NOT NULL DEFAULT 'Pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES room(room_id) ON DELETE RESTRICT,
    INDEX idx_status (status),
    INDEX idx_month_year (month_year),
    INDEX idx_due_date (due_date),
    INDEX idx_paid_date (paid_date),
    INDEX idx_student_id (student_id),
    UNIQUE KEY unique_rent (student_id, month_year)  -- One rent entry per student per month
);

-- ============================================
-- 6. EXPENSES TABLE (Hostel Expenses)
-- ============================================
CREATE TABLE expenses (
    expense_id INT PRIMARY KEY AUTO_INCREMENT,
    expense_type ENUM(
        'Electricity', 'Water', 'Maintenance', 'Cleaning', 'Security',
        'Internet', 'Furniture', 'Kitchen', 'Medical', 'Repairs',
        'Staff Salary', 'Food', 'Supplies', 'Transport', 'Other'
    ) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount > 0),
    expense_date DATE NOT NULL DEFAULT (CURDATE()),
    description TEXT,
    payment_method ENUM('Cash', 'Check', 'UPI', 'Bank Transfer', 'Credit Card', 'Other') DEFAULT 'Cash',
    reference_number VARCHAR(100),
    approved_by INT,
    status ENUM('Pending', 'Approved', 'Rejected') NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (approved_by) REFERENCES admin(admin_id) ON DELETE SET NULL,
    INDEX idx_expense_type (expense_type),
    INDEX idx_expense_date (expense_date),
    INDEX idx_status (status)
);

-- ============================================
-- 7. MAINTENANCE LOG TABLE
-- ============================================
CREATE TABLE maintenance_log (
    maintenance_id INT PRIMARY KEY AUTO_INCREMENT,
    room_id INT NOT NULL,
    issue_description TEXT NOT NULL,
    reported_date DATE NOT NULL DEFAULT (CURDATE()),
    completed_date DATE,
    assigned_to VARCHAR(100),
    cost DECIMAL(10, 2),
    status ENUM('Open', 'In Progress', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Open',
    priority ENUM('Low', 'Medium', 'High', 'Critical') NOT NULL DEFAULT 'Medium',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (room_id) REFERENCES room(room_id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_priority (priority)
);

-- ============================================
-- 8. AUDIT LOG TABLE (Track changes)
-- ============================================
CREATE TABLE audit_log (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    admin_id INT,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    record_id INT,
    old_value TEXT,
    new_value TEXT,
    action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    
    FOREIGN KEY (admin_id) REFERENCES admin(admin_id) ON DELETE SET NULL,
    INDEX idx_action_date (action_date),
    INDEX idx_table_name (table_name)
);

-- ============================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================

-- Insert admin users
INSERT INTO admin (username, password, email) VALUES 
('admin', 'hashed_password_here', 'admin@hostel.com');

-- Insert rooms
INSERT INTO room (room_no, room_type, capacity, price_per_month, status) VALUES 
('101', 'AC', 4, 5000.00, 'Available'),
('102', 'AC', 4, 5000.00, 'Available'),
('103', 'Non-AC', 4, 3000.00, 'Available'),
('104', 'Non-AC', 2, 2500.00, 'Available'),
('201', 'AC', 4, 5000.00, 'Available'),
('202', 'Non-AC', 4, 3000.00, 'Available');

-- Insert students
INSERT INTO student (first_name, last_name, email, phone, enrollment_date, status) VALUES 
('Rajesh', 'Kumar', 'rajesh@email.com', '9876543210', '2026-01-01', 'Active'),
('Priya', 'Singh', 'priya@email.com', '9876543211', '2026-01-02', 'Active'),
('Arjun', 'Patel', 'arjun@email.com', '9876543212', '2026-01-03', 'Active');

-- ============================================
-- VIEWS (For commonly used queries)
-- ============================================

-- Active allocations with student and room details
CREATE VIEW active_allocations AS
SELECT 
    a.allocation_id,
    s.student_id,
    CONCAT(s.first_name, ' ', s.last_name) AS student_name,
    s.email,
    s.phone,
    r.room_no,
    r.room_type,
    r.price_per_month,
    a.allocation_date
FROM allocation a
JOIN student s ON a.student_id = s.student_id
JOIN room r ON a.room_id = r.room_id
WHERE a.status = 'Active';

-- Outstanding rent payments
CREATE VIEW outstanding_rent AS
SELECT 
    r.rent_id,
    s.student_id,
    CONCAT(s.first_name, ' ', s.last_name) AS student_name,
    s.phone,
    r.month_year,
    r.amount,
    r.due_date,
    DATEDIFF(CURDATE(), r.due_date) AS days_overdue
FROM rent r
JOIN student s ON r.student_id = s.student_id
WHERE r.status IN ('Pending', 'Overdue')
ORDER BY r.due_date ASC;

-- Room occupancy summary
CREATE VIEW room_occupancy_summary AS
SELECT 
    room_no,
    room_type,
    capacity,
    occupied,
    (capacity - occupied) AS available,
    ROUND((occupied / capacity) * 100, 2) AS occupancy_percentage,
    CASE 
        WHEN occupied >= capacity THEN 'Full'
        WHEN occupied > 0 THEN 'Partial'
        ELSE 'Empty'
    END AS occupancy_status
FROM room;

-- Monthly expense summary
CREATE VIEW monthly_expense_summary AS
SELECT 
    DATE_FORMAT(expense_date, '%Y-%m') AS month,
    expense_type,
    COUNT(*) AS count,
    SUM(amount) AS total
FROM expenses
WHERE status = 'Approved'
GROUP BY DATE_FORMAT(expense_date, '%Y-%m'), expense_type
ORDER BY month DESC;

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================
-- Already added in table definitions, but here's a summary:
-- - All foreign keys have indexes
-- - All status columns have indexes
-- - Date columns have indexes for range queries
-- - Email and phone are unique indexed for quick lookups

-- ============================================
-- TIPS FOR GOOD DATABASE DESIGN
-- ============================================
/*
1. ✅ PRIMARY KEYS: Every table has a unique identifier
2. ✅ FOREIGN KEYS: Relationships are enforced at database level
3. ✅ CONSTRAINTS: NOT NULL, UNIQUE, CHECK constraints prevent bad data
4. ✅ INDEXES: Strategic indexes on frequently queried columns
5. ✅ ENUMS: Used for fixed values (status, type) to save space
6. ✅ TIMESTAMPS: Track when records are created/modified
7. ✅ VIEWS: Pre-built queries for common reports
8. ✅ DATA TYPES: Appropriate types (DECIMAL for money, not FLOAT)
9. ✅ NORMALIZATION: No duplicate data, proper relationships
10. ✅ ON DELETE: CASCADE for dependent records, RESTRICT for referenced
*/
