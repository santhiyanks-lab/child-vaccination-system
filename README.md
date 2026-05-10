# child-vaccination-system
Integrated Digital Platform for
Child Vaccination
Scheduling · Monitoring · Reporting
A full-stack web application that automates child immunization scheduling, appointment booking, dose
tracking, and coverage reporting — replacing paper records with a secure, centralised digital system.
Python 3.11 Django 4.2 MySQL 8.0 Bootstrap 5 Celery+Redis MIT License
142 12 7 3 100%
Children
Registered
Hospitals
Approved
Vaccine
Modules
User
Roles
Auto
Scheduling
Table of Contents
01 Key Features p.2
02 Tech Stack p.2
03 Database Schema p.3
04 System Flow p.4
05 Application Modules p.4
06 Installation & Setup p.5
07 Old System vs New p.5
08 Future Scope p.6
MCA Mini Project · 2024–2026
Department of Computer Applications · Active Development
Developer · MCA Student
Guide: Asst. Professor, Dept. of Computer Applications
01 Key Features
Six core capabilities of the platform
Auto Schedule Generation
Calculates every vaccine due date from
the child's date of birth instantly on
registration.
Smart Notifications
Automated email & SMS reminders
dispatched to parents 7 days before
each dose is due.
Parent Portal
Parents register children, view full
vaccination schedules, and book at any
approved hospital.
Coverage Reports
Admin dashboard showing real-time
immunization coverage by region,
hospital, and age group.
02 Tech Stack
Technologies and frameworks used
Hospital Management
Admin-approved hospital workflow with
appointment calendars and completion
tracking.
Role-Based Access
Three distinct roles — Admin, Hospital,
Parent — each with fully isolated data
access.
 Python 3.11 + Django 4.2
 MySQL 8.0
 HTML5 + CSS3 + Bootstrap
5
 JavaScript (Vanilla)
 Celery + Redis
Backend framework — MVT architecture, ORM, session-based authentication,
URL routing
Relational database — 5 normalised tables with FK constraints and referential
integrity
Development environment — local Apache, MySQL, phpMyAdmin for database
management
Responsive frontend — adapts across desktop, tablet, and mobile viewports
Client-side form validation, dynamic schedule rendering, real-time field updates
Background task queue — runs daily to check due dates and dispatch
email/SMS reminders
 VS Code + WAMP Server
03 Database Schema
Five normalised MySQL tables — FK relationships and referential integrity
The  symbol denotes scheduling-critical fields. PK = Primary Key, FK = Foreign Key.
parent 18 fields
parent_id INT PK Primary key — auto-increment
father_name VARCHAR(50) Father's full name
mother_name VARCHAR(50) Mother's full name
mobile_number VARCHAR(15) 10-digit mobile
email VARCHAR(50) Login & notification email
state / district VARCHAR(50) Location for coverage reports
username VARCHAR(50) Unique login handle
password VARCHAR(50) Hashed credential
status ENUM active / inactive
hospital 18 fields
hospital_id INT PK Primary key
hospital_name VARCHAR(255) Official hospital name
state / district VARCHAR(50) Location
license_proof VARCHAR(255) Uploaded file path
owner_name VARCHAR(100) Responsible owner
owner_email VARCHAR(100) Contact email
username VARCHAR(50) Login handle
status ENUM pending / approved
child 13 fields
child_id INT PK Primary key
parent_id INT FK Links to parent table
vaccine_id INT FK Links to vaccine table
child_name VARCHAR(100) Full name
dob DATE Key field — drives all scheduling
gender ENUM Male / Female / Other
blood_group VARCHAR(20) e.g. B+, O
status ENUM pending/notified/completed
vaccine 11 fields
vaccine_id INT PK Primary key
vaccine_name VARCHAR(100) e.g. BCG, OPV, DPT
age_group VARCHAR(50) Target age group
dose_number VARCHAR(50) Dose 1 / Dose 2 …
due_days VARCHAR(20) Days from DOB for first dose
interval_days VARCHAR(20) Gap between subsequent doses
min / max age INT/VARCHAR Age eligibility constraints
status ENUM confirmed / deleted
appointment 9 fields
appo_id INT PK Primary key
child_id INT FK Links to child
vaccine_id INT FK Links to vaccine
parent_id INT FK Links to parent
hospital_id INT FK Links to hospital
appointment_date DATE Scheduled date
appointment_time TIME Scheduled time slot
rescheduled_on DATETIME Null if not rescheduled
status VARCHAR Booked / Completed
 Core Scheduling Formula
due_date = child.dob + vaccine.due_days
Subsequent doses: next_due = last_date + vaccine.interval_days
04 System Flow
End-to-end process — 8 stages
1
2
3
4
Hospital Registration
Hospital submits name, address, license proof,
and owner details. Status set to pending
Admin Approval
Admin reviews and approves the hospital. Status
changes to approved; hospital can now log in.
Parent & Child Registration
Parent creates an account and registers child
details — the Date of Birth field is critical.
Auto Schedule Generation
On save, system reads the vaccine table and
computes due_date = dob + due_days for every
05 Application Modules
Seven functional modules
Automated Reminders
5
6
7
8
Celery task runs daily. When a dose is 7 days
away, email and SMS are sent to the parent.
Appointment Booking
Parent selects hospital, picks date and time.
Record links child + vaccine + hospital + parent.
Dose Administration
Hospital staff mark the appointment as completed.
Child schedule and coverage report update
Coverage Reporting
Admin views real-time rates by vaccine, region,
hospital, and age group — fully automated.
01 Admin Module
02 User Authentication
Hospital approval, vaccine master CRUD, user oversight, and
coverage report generation.
Secure login/logout for all three roles with session management and
password hashing.
03 Parent Management
04 Child Registration
Registration, profile management, and dashboard showing all
children and their statuses.
Celery scheduler checks daily for upcoming doses and dispatches
email + SMS automatically.
Captures child health data and triggers automatic vaccination
schedule on save.
05 Vaccine Management
06 Appointment Module
Vaccine master with the core algorithm: due_date = dob + due_days;
interval_days for follow-ups.
Full lifecycle — booking, rescheduling, cancellation, and completion
marking by hospitals.
07 Notification Module
06 Installation & Setup
Four steps to get running locally
Step 1 Clone & Enter Project
git clone https://github.com/your-username/child-vaccination-system.git cd
child-vaccination-system
Step 2 Virtual Environment & Dependencies
python -m venv venv source venv/bin/activate # Windows: venv\Scripts\activate pip install -r
requirements.txt
Step 3 Database Configuration (settings.py)
DATABASES = { 'default': { 'ENGINE': 'django.db.backends.mysql', 'NAME': 'vaccination_db',
'USER': 'root', 'PASSWORD': 'your_password', 'HOST': 'localhost', 'PORT': '3306', } }
Step 4 Migrate, Create Superuser & Run
python manage.py makemigrations python manage.py migrate python manage.py createsuperuser python
manage.py runserver # Open: http://127.0.0.1:8000
07 Old System vs This System
Why this platform replaces the traditional paper-based approach
Feature Old Manual System This System
Vaccination records Paper cards — easily lost or damaged Permanent MySQL DB — never lost
Due date calculation Manual — often wrong intervals Automatic from DOB — always accurate
Reminders to parents None — parents must remember Auto email + SMS 7 days before due
Record access Single hospital register only Centralised — any approved hospital
Appointment booking Walk-in only Online booking at any approved hospital
Coverage reporting Manual counting of registers Real-time admin dashboard reports
Overdue tracking Not possible Automatic overdue alerts flagged
Data security No backup, can be forged Encrypted, backed up, role-secured
08 Future Scope
Planned enhancements for the next development phase
Mobile App (Android & iOS)
Push notifications to parent lock screens. Offline schedule
viewing for areas with poor connectivity.
ABDM / Health ID Integration
Link with India's Ayushman Bharat Digital Mission for
cross-country record access via Aadhaar Health ID.
AI Drop-out Risk Prediction
ML model to identify children likely to miss doses from
historical patterns — enables proactive outreach.
Digital QR Vaccine Card
Printable QR-code card per child — scan at any hospital for
instant record access, replacing paper cards.
  Sample Auto-Generated Schedule
Example output for child Ananya R. — DOB 15 Jan 2025
Vaccine Due Age Due Date Status
BCG At birth 15 Jan 2025 Done
OPV Dose 1 6 weeks 26 Feb 2025 Done
DPT Dose 1 6 weeks 26 Feb 2025 Done
DPT Dose 2 10 weeks 26 Mar 2025 Booked
Hepatitis B D3 14 weeks 23 Apr 2025 Pending
Measles 9 months 15 Oct 2025 Pending
MMR 15 months 15 Apr 2026 Pending
 VacciTrack
Integrated Digital Platform for Child Vaccination
Python 3.11 · Django 4.2 · MySQL 8.0 · Bootstrap 5 ·
