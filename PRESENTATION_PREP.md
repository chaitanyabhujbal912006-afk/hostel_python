# Presentation Prep Pack

## 1. 10-12 Slide Deck Structure
1. Title Slide
2. Problem Statement and Objectives
3. System Features
4. Architecture Overview
5. Database Design
6. Core Modules and Workflows
7. Dashboard Analytics (Graphs + Tables)
8. Validation and Business Rules
9. Demo Walkthrough
10. Challenges and Learnings
11. Future Enhancements
12. Q&A

## 2. Suggested Slide Content

### Slide 1: Title
- Hostel Management System
- Team member names
- Guide/faculty name
- Date

### Slide 2: Problem Statement
- Manual hostel records are error-prone.
- Need centralized data for students, rooms, rent, and expenses.
- Need dynamic dashboard for quick decisions.

### Slide 3: Feature Summary
- Student onboarding and profile management
- Room inventory and capacity tracking
- Room allocation with capacity checks
- Rent lifecycle (pending, paid, overdue)
- Expense tracking by category
- Dashboard with filters, charts, and live summaries

### Slide 4: Architecture
- Flask + Jinja (server-rendered app)
- MySQL relational database
- Chart.js for dashboard visuals
- API endpoint for dynamic dashboard refresh

### Slide 5: Database Schema Highlights
- Main tables: `student`, `room`, `allocation`, `rent`, `expenses`
- FK relationships enforce data integrity
- Unique constraints:
  - `student.email`, `student.phone`
  - `rent(student_id, month_year)`

### Slide 6: Module Breakdown
- `students.py`: add/list/edit/delete students
- `rooms.py`: room CRUD and occupancy views
- `allocations.py`: room assignment and transfer logic
- `rents.py`: billing records and status normalization
- `expenses.py`: expense CRUD
- `dashboard.py`: KPI and analytics API

### Slide 7: Dashboard Intelligence
- Graphs:
  - expense trend
  - occupancy split
  - monthly finance trend
  - rent status distribution
- Tables:
  - pending dues
  - expense category summary
- Date range filter + auto-refresh

### Slide 8: Data Integrity Rules
- Capacity enforcement during allocation
- Prevent duplicate monthly rent records
- Convert pending to overdue by due date
- Student deletion cleans dependent records and room occupancy

### Slide 9: Live Demo Flow
1. Add room
2. Add student
3. Allocate student to room
4. Add rent and expense
5. Open dashboard and apply date filter
6. Show graph/table changes in real time

### Slide 10: Challenges and Solutions
- Keeping occupancy counts accurate
- Handling duplicate and invalid entries
- Keeping dashboard dynamic without full reload
- Syncing backend SQL aggregates with frontend charts

### Slide 11: Future Scope
- Login/auth roles (admin/staff)
- Notifications for dues and overdue rents
- PDF/CSV reporting
- Advanced analytics and forecasting
- Test automation and CI pipeline

### Slide 12: Closing
- Outcomes achieved
- What is production-ready vs what is next
- Thank you + Q&A

## 3. 5-Minute Demo Script (Speaker Notes)
- "We built a Flask-based Hostel Management System to digitize core hostel operations."
- "First, I will add a room and show inventory updates."
- "Next, we onboard a student and allocate a room. Capacity checks prevent over-allocation."
- "Then we create a rent record and an expense entry."
- "On dashboard, KPIs and charts update based on live data."
- "Applying date filter refreshes finance trend, rent status, pending dues, and expense category summary."
- "This helps management identify overdue dues and spending patterns quickly."

## 4. Likely Viva Questions and Ready Answers

Q1. Why Flask?
- Lightweight, modular with Blueprints, easy template integration, ideal for this scope.

Q2. How is data consistency maintained?
- DB constraints (FK + unique keys) and route-level validations for capacity, duplicate rent, and required fields.

Q3. How do you handle overdue rent?
- In `rents` route, pending records are checked against due date; past due becomes `Overdue`.

Q4. How is dashboard dynamic?
- `/api/dashboard-data` returns aggregated JSON; frontend updates chart/table widgets without page reload.

Q5. What are current limitations?
- Basic security hardening still needed (CSRF, role-based auth, stricter transaction handling in some routes).

## 5. Final Day Checklist
- Ensure MySQL is running and schema initialized.
- Verify DB credentials are aligned in env vars/scripts.
- Seed enough sample data for meaningful charts.
- Keep 2 fallback demos ready:
  - screenshot/video
  - pre-seeded database
- Rehearse with timer (7 to 10 minutes).

## 6. What To Show in Code (if asked)
- App wiring: `hostel_app/__init__.py`
- DB management: `hostel_app/db.py`
- Allocation logic: `hostel_app/routes/allocations.py`
- Rent status logic: `hostel_app/routes/rents.py`
- Dashboard API: `hostel_app/routes/dashboard.py`
