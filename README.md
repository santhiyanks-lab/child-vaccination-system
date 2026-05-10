# child-vaccination-system
💉
Integrated Digital Platform for Child Vaccination
Scheduling, Monitoring & Reporting
A full-stack web application that automates child immunization scheduling, appointment booking, dose tracking, and coverage reporting — replacing paper records with a secure, centralized system.

🐍 Python 3.11
🌿 Django 4.2
🐬 MySQL 8.0
⚡ Bootstrap 5
📄 License: MIT
✅ Status: Active
🎓 MCA Mini Project
📋 Table of Contents
Project Overview
Key Features
Tech Stack
Screenshots
Database Schema
System Flow
Modules
Installation
Old vs New
Future Scope
Project Overview
🗓️
Auto Schedule Generation
Calculates every vaccine due date from a child's date of birth instantly on registration.
🔔
Smart Notifications
Automated email & SMS reminders sent to parents before each dose is due.
🏥
Hospital Management
Admin-approved hospital workflow with appointment calendars and dose completion tracking.
👨‍👩‍👧
Parent Portal
Parents can register children, view schedules, and book appointments at any hospital.
📊
Coverage Reports
Admin dashboard with real-time immunization coverage data by region and vaccine type.
🔒
Role-Based Access
Three distinct user roles — Admin, Hospital, Parent — each with isolated data access.
Tech Stack
PY
Python 3.11 + Django 4.2
Backend framework — MVT architecture, ORM, session auth, URL routing
SQL
MySQL 8.0
Relational database — 5 tables with FK relationships and referential integrity
UI
HTML5 + CSS3 + Bootstrap 5
Responsive frontend — works on desktop, tablet, and mobile
JS
JavaScript (Vanilla)
Form validation, dynamic schedule display, real-time field updates
⚙
Celery + Redis
Background task queue for scheduled dose reminder emails and SMS dispatch
IDE
VS Code + WAMP Server
Development environment — local Apache, MySQL, and phpMyAdmin
Screenshots
localhost:8000/admin/dashboard
Admin Dashboard
💉 VacciTrack
Hospitals
Vaccines
Reports
142
Children
12
Hospitals
3
Pending
Hospital	Status
City Health Centre	Approved
PHC Erode North	Pending
District Hospital	Approved
localhost:8000/parent/add-child
Child Registration Form
Child Name
Ananya R.
Date of Birth
2025-01-15
Gender
Female
Blood Group
B+
Weight (kg)
3.2
Identification Mark
Mole on left cheek
✓ Register & Generate Schedule
localhost:8000/parent/schedule/child/4
Auto-Generated Vaccination Schedule
BCG
At birth → 2025-01-15
✓ Done
OPV Dose 1
6 weeks → 2025-02-26
✓ Done
DPT Dose 2
10 weeks → 2025-03-26
Booked
Hepatitis B D3
14 weeks → 2025-04-23
Pending
Measles
9 months → 2025-10-15
Pending
localhost:8000/parent/book-appointment
Book Appointment
Child
Ananya R. (ID: C-004)
Vaccine Due
DPT Dose 2
Select Hospital
City Health Centre, Erode
Date
2025-03-26
Time
10:30 AM
📅 Confirm Appointment
Database Schema
parent
18 fields
parent_id
INT PK
father_name
VARCHAR(50)
mother_name
VARCHAR(50)
mobile_number
VARCHAR(15)
email
VARCHAR(50)
state / district
VARCHAR(50)
username / password
VARCHAR(50)
status
ENUM
hospital
18 fields
hospital_id
INT PK
hospital_name
VARCHAR(255)
state / district
VARCHAR(50)
license_proof
VARCHAR(255)
owner_name
VARCHAR(100)
owner_email
VARCHAR(100)
username / password
VARCHAR(50)
status
ENUM(pending/approved)
child
13 fields
child_id
INT PK
parent_id
INT FK
vaccine_id
INT FK
child_name
VARCHAR(100)
dob
DATE ⭐ key field
gender
ENUM
blood_group
VARCHAR(20)
status
ENUM(pending/notified/completed)
vaccine
11 fields
vaccine_id
INT PK
vaccine_name
VARCHAR(100)
age_group
VARCHAR(50)
dose_number
VARCHAR(50)
due_days
VARCHAR(20) ⭐
interval_days
VARCHAR(20) ⭐
min / max age
INT / VARCHAR
status
ENUM(confirmed/deleted)
appointment
9 fields — joins all 4 tables above
appo_id
INT PK
child_id
INT FK
vaccine_id
INT FK
parent_id
INT FK
hospital_id
INT FK
appointment_date
DATE
appointment_time
TIME
rescheduled_on
DATETIME
status
VARCHAR (Booked/Completed)
System Flow
1
Hospital Registration
A hospital submits a registration form with name, address, license proof, and owner details. Status is set to pending.
2
Admin Approval
Admin reviews and approves the hospital. Status changes to approved. Hospital can now log in.
3
Parent & Child Registration
Parent registers an account, then adds their child's details including the critical Date of Birth field.
4
⚡ Auto Schedule Generation
On child save, the system reads every vaccine in the vaccine table and computes: due_date = dob + due_days. Full schedule generated instantly.
5
🔔 Automated Reminders
Celery task runs daily. When a dose is 7 days away → email + SMS sent to parent. Overdue doses trigger follow-up alerts.
6
Appointment Booking
Parent selects a hospital, picks a date & time. Appointment record created in DB linking child + vaccine + hospital + parent.
7
Dose Administration & Completion
Hospital marks the appointment as completed. Child's schedule updates. Coverage report auto-refreshes.
8
📊 Coverage Reporting
Admin views real-time coverage rates by vaccine, region, hospital, and age group — no manual counting required.
Modules
01
Admin Module
Hospital approval workflow, vaccine master management, user oversight, and coverage report generation.
02
User Authentication Module
Secure login/logout for all three roles with session management and encrypted password storage.
03
Parent Management Module
Parent registration, profile management, and a dashboard showing all registered children and their statuses.
04
Child Registration Module
Captures child health data and triggers automatic vaccination schedule generation upon saving.
05
Vaccine Management Module
Vaccine master CRUD with the core scheduling algorithm: due_date = dob + due_days, subsequent doses use interval_days.
06
Appointment Module
End-to-end appointment lifecycle — booking, rescheduling, cancellation, and completion marking by hospitals.
07
Notification Module
Celery-powered background scheduler that checks daily for upcoming due dates and dispatches email + SMS reminders automatically.
Installation & Setup
bash
Step 1 — Clone & enter project
# Clone the repository
git clone https://github.com/your-username/child-vaccination-system.git
cd child-vaccination-system
bash
Step 2 — Virtual environment & dependencies
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
python
Step 3 — Database configuration (settings.py)
DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'vaccination_db',
    'USER': 'root',
    'PASSWORD': 'your_password',
    'HOST': 'localhost',
    'PORT': '3306',
  }
}
bash
Step 4 — Migrate & run
# Create database tables
python manage.py makemigrations
python manage.py migrate

# Create admin superuser
python manage.py createsuperuser

# Start the development server
python manage.py runserver

✓ Open: http://127.0.0.1:8000
Old System vs This System
Feature	❌ Old Manual System	✅ This System
Vaccination records	Paper cards — easily lost or damaged	Permanent MySQL database — never lost
Due date calculation	Manual — often wrong intervals	Automatic from DOB — always accurate
Reminders to parents	None — parents must remember	Auto email + SMS 7 days before due
Record access	Single hospital register only	Centralised — any approved hospital
Appointment booking	Walk-in only	Online booking at any hospital
Coverage reporting	Manual counting of registers	Real-time admin dashboard reports
Overdue dose tracking	Not possible	Automatic overdue alerts flagged
Data security	No backup, can be forged	Encrypted, backed up, role-secured
Future Scope
📱 Mobile
Android & iOS App
Push notifications directly to parent lock screens. Offline schedule viewing for areas with poor connectivity.
🔗 Integration
ABDM / Health ID Link
Integrate with India's Ayushman Bharat Digital Mission for cross-country record access using Aadhaar Health ID.
🤖 AI
Drop-out Risk Prediction
ML model to identify children likely to miss future doses based on historical drop-out patterns — enabling proactive outreach.
📲 QR Code
Digital Vaccine Card
Printable QR-code vaccine card per child — scan at any hospital for instant record access, replacing paper cards entirely.
