#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe

from datetime import datetime
import pymysql
import cgi
import cgitb
import sys

cgitb.enable()
sys.stdout.reconfigure(encoding='utf-8')
print("Content-Type:text/html\r\n\r\n")

form = cgi.FieldStorage()
appointment_id = form.getfirst("appointment_id")
reschedule_date = form.getfirst("reschedule_date")
reschedule_time = form.getfirst("reschedule_time")
hospital_id = form.getfirst("hospital_id")  # pass hospital_id from the form

# Validate input
if not appointment_id or not reschedule_date or not reschedule_time:
    print("<script>alert('Please select both date and time!');window.history.back();</script>")
    exit()

# Combine date and time into datetime string (MySQL datetime format)
try:
    reschedule_datetime = f"{reschedule_date} {reschedule_time}:00"  # 'YYYY-MM-DD HH:MM:SS'
except Exception as e:
    print(f"<script>alert('Invalid date/time format: {e}');window.history.back();</script>")
    exit()

# Connect to database
try:
    con = pymysql.connect(host="localhost", user="root", password="", database="child")
    cur = con.cursor()

    # Update the appointment
    cur.execute("""
        UPDATE child_vaccine
        SET appointment_date=%s, status='rescheduled'
        WHERE id=%s
    """, (reschedule_datetime, appointment_id))

    con.commit()
    con.close()

    # Redirect back to pending appointments for the hospital
    print(
        f"<script>alert('Appointment Rescheduled Successfully!');window.location='hospitalpendingvaccine.py?hospital_id={hospital_id}';</script>")

except Exception as e:
    if con:
        con.rollback()
        con.close()
    print(f"<h3>Database Error:</h3>{e}")