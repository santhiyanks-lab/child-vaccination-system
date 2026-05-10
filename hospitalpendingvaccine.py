#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
print("Content-Type: text/html\r\n\r\n")

import cgi
import cgitb
import pymysql
import sys
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.stdout.reconfigure(encoding='utf-8')
cgitb.enable()

SENDER_EMAIL    = "santhiyanks@gmail.com"
SENDER_PASSWORD = "snnr avxt cqgb ocwy"

# ================= EMAIL HELPERS =================
def send_email(to_email, subject, html_body):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = SENDER_EMAIL
        msg["To"]      = to_email
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        return True, ""
    except Exception as e:
        return False, str(e)


def build_email_html(action, parent_name, child_name, child_dob,
                     child_gender, child_blood_group,
                     vaccine_name, dose_number, hospital_name,
                     appointment_date, appointment_time,
                     reschedule_date=None, reschedule_time=None):
    if action == "confirmed":
        header_color = "#198754"
        header_icon  = "Appointment Confirmed"
        intro = ("Dear <b>" + str(parent_name) + "</b>,<br><br>"
                 "Your child's vaccination appointment has been "
                 "<b style='color:#198754;'>confirmed</b> by <b>" + str(hospital_name) + "</b>.")
        date_label = "Appointment Date"
        date_value = str(appointment_date)
        time_value = str(appointment_time)
    else:
        header_color = "#0d6efd"
        header_icon  = "Appointment Rescheduled"
        intro = ("Dear <b>" + str(parent_name) + "</b>,<br><br>"
                 "Your child's vaccination appointment has been "
                 "<b style='color:#0d6efd;'>rescheduled</b> by <b>" + str(hospital_name) + "</b>.")
        date_label = "New Appointment Date"
        date_value = str(reschedule_date)
        time_value = str(reschedule_time) if reschedule_time else str(appointment_time)

    html  = "<div style='font-family:Arial,sans-serif;max-width:620px;margin:auto;border:1px solid #ddd;border-radius:10px;overflow:hidden;'>"
    html += "<div style='background:" + header_color + ";padding:25px 30px;text-align:center;'>"
    html += "<h2 style='color:white;margin:0;'>" + header_icon + "</h2>"
    html += "<p style='color:rgba(255,255,255,0.85);margin:6px 0 0;'>Child Vaccination Management System</p>"
    html += "</div><div style='padding:25px 30px;background:#fff;'>"
    html += "<p style='font-size:15px;color:#333;'>" + intro + "</p>"
    html += "<div style='background:#f0f9ff;border-left:4px solid " + header_color + ";border-radius:8px;padding:15px 20px;margin:20px 0;'>"
    html += "<h4 style='margin:0 0 12px;color:" + header_color + ";'>Child Details</h4>"
    html += "<table style='width:100%;font-size:14px;color:#333;border-collapse:collapse;'>"
    html += "<tr><td style='padding:5px 0;width:160px;'><b>Child Name</b></td><td>: " + str(child_name) + "</td></tr>"
    html += "<tr><td style='padding:5px 0;'><b>Date of Birth</b></td><td>: " + str(child_dob) + "</td></tr>"
    html += "<tr><td style='padding:5px 0;'><b>Gender</b></td><td>: " + str(child_gender) + "</td></tr>"
    html += "<tr><td style='padding:5px 0;'><b>Blood Group</b></td><td>: <span style='background:#dc3545;color:white;padding:2px 10px;border-radius:20px;font-size:13px;'>" + str(child_blood_group) + "</span></td></tr>"
    html += "</table></div>"
    html += "<div style='background:#f8f9fa;border-left:4px solid " + header_color + ";border-radius:8px;padding:15px 20px;margin:20px 0;'>"
    html += "<h4 style='margin:0 0 12px;color:" + header_color + ";'>Appointment Details</h4>"
    html += "<table style='width:100%;font-size:14px;color:#333;border-collapse:collapse;'>"
    html += "<tr><td style='padding:5px 0;width:160px;'><b>Vaccine</b></td><td>: " + str(vaccine_name) + "</td></tr>"
    html += "<tr><td style='padding:5px 0;'><b>Dose Number</b></td><td>: " + str(dose_number) + "</td></tr>"
    html += "<tr><td style='padding:5px 0;'><b>Hospital</b></td><td>: " + str(hospital_name) + "</td></tr>"
    html += "<tr><td style='padding:5px 0;'><b>" + date_label + "</b></td><td>: <b style='color:" + header_color + ";'>" + date_value + "</b></td></tr>"
    html += "<tr><td style='padding:5px 0;'><b>Time</b></td><td>: " + time_value + "</td></tr>"
    html += "</table></div>"
    html += "<p style='font-size:13px;color:#777;margin-top:25px;'>Please arrive 10 minutes before your scheduled time.</p>"
    html += "</div><div style='background:#f1f1f1;padding:15px 30px;text-align:center;font-size:12px;color:#999;'>Automated email - Child Vaccination System</div></div>"
    return html


# ================= FORM DATA =================
form         = cgi.FieldStorage()
hid          = form.getfirst("hospital_id")
action       = form.getfirst("action")
appt_id      = form.getfirst("appt_id")
resched_date = form.getfirst("reschedule_date")
resched_time = form.getfirst("reschedule_time")

if not hid or not hid.strip().isdigit():
    print("<h3 style='color:red;'>Invalid Hospital ID!</h3>")
    exit()

hospital_id = int(hid.strip())
oid = str(hospital_id)

# ================= DATABASE =================
try:
    con = pymysql.connect(host="localhost", user="root", password="", database="child")
    cur = con.cursor()
except Exception as e:
    print(f"<h3 style='color:red;'>Database connection error: {e}</h3>")
    exit()

# ================= HANDLE CONFIRM =================
if action == "confirm" and appt_id and appt_id.strip().isdigit():
    appt_id_clean = int(appt_id.strip())
    cur.execute("""
        SELECT cv.id, c.child_name, c.dob, c.gender, c.blood_group,
               v.vaccine_name, v.dose_number, h.hospital_name,
               cv.appointment_date, cv.appointment_time,
               p.father_name, p.email
        FROM child_vaccine cv
        JOIN children c ON cv.child_id   = c.child_id
        JOIN vaccine  v ON cv.vaccine_id  = v.vaccine_id
        JOIN hospital h ON cv.hospital_id = h.hospital_id
        JOIN parent   p ON c.parent_id    = p.parent_id
        WHERE cv.id = %s
    """, (appt_id_clean,))
    row = cur.fetchone()
    if row:
        _, child_name, child_dob, child_gender, child_blood_group, \
        vaccine_name, dose_number, hospital_name, appointment_date, appointment_time, \
        father_name, parent_email = row
        cur.execute(
            "UPDATE child_vaccine SET status='confirmed', confirmed_date=CURDATE() WHERE id=%s",
            (appt_id_clean,)
        )
        con.commit()
        subject   = "Vaccination Appointment Confirmed - " + str(child_name)
        html_body = build_email_html(
            "confirmed", father_name, child_name, child_dob,
            child_gender, child_blood_group or "N/A",
            vaccine_name, dose_number, hospital_name,
            appointment_date, appointment_time
        )
        ok, err   = send_email(parent_email, subject, html_body)
        email_msg = "Appointment confirmed and email sent!" if ok else "Confirmed but email failed: " + err
    else:
        email_msg = "Appointment not found."
    safe_msg = email_msg.replace("'", "\\'")
    print(f"<script>alert('{safe_msg}');window.location.href='hospitalpendingvaccine.py?hospital_id={hospital_id}';</script>")
    con.close()
    exit()

# ================= HANDLE RESCHEDULE =================
if action == "reschedule" and appt_id and appt_id.strip().isdigit() and resched_date:
    appt_id_clean = int(appt_id.strip())
    cur.execute("""
        SELECT cv.id, c.child_name, c.dob, c.gender, c.blood_group,
               v.vaccine_name, v.dose_number, h.hospital_name,
               cv.appointment_date, cv.appointment_time,
               p.father_name, p.email
        FROM child_vaccine cv
        JOIN children c ON cv.child_id   = c.child_id
        JOIN vaccine  v ON cv.vaccine_id  = v.vaccine_id
        JOIN hospital h ON cv.hospital_id = h.hospital_id
        JOIN parent   p ON c.parent_id    = p.parent_id
        WHERE cv.id = %s
    """, (appt_id_clean,))
    row = cur.fetchone()
    if row:
        _, child_name, child_dob, child_gender, child_blood_group, \
        vaccine_name, dose_number, hospital_name, appointment_date, appointment_time, \
        father_name, parent_email = row
        new_time = resched_time if resched_time else appointment_time
        cur.execute("""
            UPDATE child_vaccine
            SET status='rescheduled',
                reschedule_date=%s,
                appointment_date=%s,
                appointment_time=%s
            WHERE id=%s
        """, (resched_date, resched_date, new_time, appt_id_clean))
        con.commit()
        subject   = "Vaccination Appointment Rescheduled - " + str(child_name)
        html_body = build_email_html(
            "rescheduled", father_name, child_name, child_dob,
            child_gender, child_blood_group or "N/A",
            vaccine_name, dose_number, hospital_name,
            appointment_date, appointment_time,
            resched_date, new_time
        )
        ok, err   = send_email(parent_email, subject, html_body)
        email_msg = "Rescheduled and email sent!" if ok else "Rescheduled but email failed: " + err
    else:
        email_msg = "Appointment not found."
    safe_msg = email_msg.replace("'", "\\'")
    print(f"<script>alert('{safe_msg}');window.location.href='hospitalpendingvaccine.py?hospital_id={hospital_id}';</script>")
    con.close()
    exit()

# ================= FETCH DATA =================
cur.execute("SELECT hospital_name FROM hospital WHERE hospital_id=%s", (hospital_id,))
hosp_row = cur.fetchone()
hospital_name_display = hosp_row[0] if hosp_row else "Hospital"

# Fetch both 'pending' and 'notified' rows so admin-notified children also appear
cur.execute("""
    SELECT cv.id, cv.child_id, c.child_name,
           c.dob, c.gender, c.blood_group,
           cv.vaccine_id, v.vaccine_name, v.dose_number,
           cv.appointment_date, cv.appointment_time,
           cv.reschedule_date, cv.status,
           p.father_name, p.email, p.mobile_number
    FROM child_vaccine cv
    LEFT JOIN children c ON cv.child_id   = c.child_id
    LEFT JOIN vaccine  v ON cv.vaccine_id  = v.vaccine_id
    LEFT JOIN parent   p ON c.parent_id    = p.parent_id
    WHERE cv.hospital_id = %s
      AND LOWER(TRIM(cv.status)) IN ('pending', 'notified')
    ORDER BY cv.appointment_date ASC
""", (hospital_id,))
appointments = cur.fetchall()

# ================= FETCH CROSS-HOSPITAL HISTORY =================
# For each child in the pending list, fetch all COMPLETED doses from OTHER hospitals
# Returns: child_id -> list of {dose_number, vaccine_name, hospital_name, address, taken_date, status}
child_ids = list(set(appt[1] for appt in appointments)) if appointments else []

cross_hospital_history = {}  # child_id -> [rows]

if child_ids:
    format_ids = ','.join(['%s'] * len(child_ids))
    cur.execute(f"""
        SELECT
            cv.child_id,
            v.dose_number,
            v.vaccine_name,
            h.hospital_name,
            h.address,
            cv.taken_date,
            cv.status,
            h.hospital_id
        FROM child_vaccine cv
        LEFT JOIN vaccine  v ON cv.vaccine_id  = v.vaccine_id
        LEFT JOIN hospital h ON cv.hospital_id = h.hospital_id
        WHERE cv.child_id IN ({format_ids})
          AND cv.hospital_id != %s
          AND LOWER(TRIM(cv.status)) IN ('completed', 'confirmed', 'taken')
        ORDER BY cv.child_id, v.dose_number ASC
    """, (*child_ids, hospital_id))

    for row in cur.fetchall():
        cid = row[0]
        if cid not in cross_hospital_history:
            cross_hospital_history[cid] = []
        cross_hospital_history[cid].append({
            "dose_number":   row[1] if row[1] else "-",
            "vaccine_name":  row[2] if row[2] else "Unknown",
            "hospital_name": row[3] if row[3] else "Unknown Hospital",
            "address":       row[4] if row[4] else "Address not available",
            "taken_date":    str(row[5]) if row[5] else "-",
            "status":        row[6] if row[6] else "-",
        })

today_str = str(datetime.date.today())

# ================= HTML =================
print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pending Vaccine Appointments</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
  :root {{
    --sidebar-w: 260px;
    --topbar-h: 60px;
    --primary: #1565c0;
    --bg: #f0f4f8;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: var(--bg); color: #1e293b; }}

  .topbar {{
    position: fixed; top: 0; left: 0; right: 0; height: var(--topbar-h);
    background: #0d1b2a; display: flex; align-items: center;
    justify-content: space-between; padding: 0 16px; z-index: 1100;
    box-shadow: 0 2px 10px rgba(0,0,0,.3);
  }}
  .topbar-left {{ display: flex; align-items: center; gap: 12px; }}
  .topbar img {{ height: 40px; width: 40px; border-radius: 50%; border: 2px solid rgba(255,255,255,.4); object-fit: cover; }}
  .topbar .brand {{ color: #fff; font-size: 1rem; font-weight: 700; }}
  .topbar .subbrand {{ color: #90a4ae; font-size: .75rem; display: block; }}
  .hamburger {{ background: none; border: none; color: #fff; font-size: 1.4rem; cursor: pointer; padding: 4px 8px; border-radius: 6px; display: none; }}
  .hamburger:hover {{ background: rgba(255,255,255,.1); }}
  .topbar-right a {{ color: #cfd8dc; text-decoration: none; font-size: .85rem; padding: 6px 14px; border: 1px solid #37474f; border-radius: 6px; transition: all .2s; }}
  .topbar-right a:hover {{ background: #e53935; border-color: #e53935; color: #fff; }}

  .sidebar {{
    position: fixed; top: var(--topbar-h); left: 0;
    width: var(--sidebar-w); height: calc(100vh - var(--topbar-h));
    background: #0d1b2a; overflow-y: auto; z-index: 1000;
    transition: transform .3s ease; padding: 16px 12px 24px;
    scrollbar-width: thin; scrollbar-color: #1e3a5f transparent;
  }}
  .sidebar-label {{ color: #546e7a; font-size: .68rem; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; padding: 12px 8px 4px; }}
  .sidebar .nav-link {{ color: #b0bec5; border-radius: 8px; padding: 9px 12px; font-size: .87rem; display: flex; align-items: center; gap: 10px; text-decoration: none; transition: all .2s; margin-bottom: 2px; }}
  .sidebar .nav-link i {{ width: 18px; text-align: center; font-size: .9rem; }}
  .sidebar .nav-link:hover, .sidebar .nav-link.active {{ background: var(--primary); color: #fff; }}
  .sidebar-group summary {{ list-style: none; color: #b0bec5; padding: 9px 12px; border-radius: 8px; display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: .87rem; transition: background .2s; margin-bottom: 2px; user-select: none; }}
  .sidebar-group summary::-webkit-details-marker {{ display: none; }}
  .sidebar-group summary:hover {{ background: #1c2d3e; color: #fff; }}
  .sidebar-group summary .caret {{ margin-left: auto; transition: transform .25s; font-size: .75rem; }}
  .sidebar-group[open] summary .caret {{ transform: rotate(90deg); }}
  .sidebar-group[open] summary {{ color: #fff; background: #1c2d3e; }}
  .sub-links {{ padding: 4px 0 4px 28px; }}
  .sub-links a {{ display: flex; align-items: center; gap: 8px; color: #78909c; font-size: .83rem; padding: 7px 10px; border-radius: 6px; text-decoration: none; transition: all .2s; margin-bottom: 1px; }}
  .sub-links a:hover {{ color: #fff; background: rgba(255,255,255,.07); }}
  .sub-links a.active {{ color: #fff; background: rgba(255,255,255,.07); }}
  .sidebar-divider {{ border: none; border-top: 1px solid #1c2d3e; margin: 10px 0; }}
  .sidebar-overlay {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,.55); z-index: 999; backdrop-filter: blur(2px); }}

  .main {{ margin-left: var(--sidebar-w); margin-top: var(--topbar-h); padding: 28px 24px; min-height: calc(100vh - var(--topbar-h)); transition: margin-left .3s; }}

  .page-header {{ display: flex; align-items: center; gap: 14px; margin-bottom: 20px; }}
  .page-header-icon {{ background: linear-gradient(135deg,#e65100,#ff8f00); color:#fff; width:48px; height:48px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:1.2rem; flex-shrink:0; box-shadow:0 4px 12px rgba(230,81,0,.3); }}
  .page-header h4 {{ font-size: 1.2rem; font-weight: 700; margin: 0 0 2px; }}
  .page-header p {{ font-size: .85rem; color: #64748b; margin: 0; }}

  .summary-strip {{ background: #fff; border-radius: 12px; padding: 14px 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,.06); display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
  .count-badge {{ background: #fff3e0; color: #e65100; padding: 4px 14px; border-radius: 20px; font-size: .85rem; font-weight: 700; }}

  .table-card {{ background: #fff; border-radius: 14px; box-shadow: 0 2px 14px rgba(0,0,0,.08); overflow: hidden; }}
  .vaccine-table {{ font-size: .86rem; margin: 0; }}
  .vaccine-table thead th {{ background: #f8fafc; color: #475569; font-weight: 700; font-size: .75rem; letter-spacing: .5px; text-transform: uppercase; padding: 11px 12px; border-color: #f1f5f9; white-space: nowrap; }}
  .vaccine-table tbody td {{ padding: 11px 12px; border-color: #f1f5f9; vertical-align: middle; }}
  .vaccine-table tbody tr:hover {{ background: #f8fafc; }}

  .badge-pending {{ background: #fff3e0; color: #e65100; padding: 3px 10px; border-radius: 20px; font-size: .75rem; font-weight: 700; }}
  .badge-dose {{ background: #e3f2fd; color: #1565c0; padding: 3px 10px; border-radius: 20px; font-size: .75rem; font-weight: 700; }}
  .blood-badge {{ background: #ffebee; color: #c62828; padding: 2px 10px; border-radius: 20px; font-size: .75rem; font-weight: 700; }}
  .badge-other-hosp {{ background: #fff3e0; color: #e65100; padding: 2px 9px; border-radius: 20px; font-size: .72rem; font-weight: 700; }}

  .btn-view {{ background:#e3f2fd; color:#1565c0; border:none; border-radius:6px; padding:5px 10px; font-size:.78rem; font-weight:600; cursor:pointer; transition:all .2s; display:inline-flex; align-items:center; gap:4px; }}
  .btn-view:hover {{ background:#1565c0; color:#fff; }}
  .btn-confirm {{ background:#e8f5e9; color:#2e7d32; border:none; border-radius:6px; padding:5px 10px; font-size:.78rem; font-weight:600; cursor:pointer; transition:all .2s; display:inline-flex; align-items:center; gap:4px; }}
  .btn-confirm:hover {{ background:#2e7d32; color:#fff; }}
  .btn-reschedule {{ background:#fff8e1; color:#f57f17; border:none; border-radius:6px; padding:5px 10px; font-size:.78rem; font-weight:600; cursor:pointer; transition:all .2s; display:inline-flex; align-items:center; gap:4px; }}
  .btn-reschedule:hover {{ background:#f57f17; color:#fff; }}

  /* ---- Cross-hospital history styles ---- */
  .cross-hosp-section {{
    background: #fff8e1;
    border: 1.5px solid #ffe082;
    border-radius: 10px;
    padding: 14px 16px;
    margin-top: 2px;
  }}
  .cross-hosp-section .ch-title {{
    font-size: .78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .7px;
    color: #e65100;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 7px;
  }}
  .cross-hosp-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: .83rem;
  }}
  .cross-hosp-table thead th {{
    background: #ffe0b2;
    color: #bf360c;
    padding: 7px 10px;
    font-size: .72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .4px;
    border-bottom: 2px solid #ffcc80;
    white-space: nowrap;
  }}
  .cross-hosp-table tbody td {{
    padding: 8px 10px;
    border-bottom: 1px solid #ffe082;
    color: #1e293b;
    vertical-align: top;
  }}
  .cross-hosp-table tbody tr:last-child td {{
    border-bottom: none;
  }}
  .cross-hosp-table tbody tr:hover {{
    background: #fff3e0;
  }}
  .ch-hosp-name {{
    font-weight: 600;
    color: #bf360c;
  }}
  .ch-address {{
    font-size: .78rem;
    color: #64748b;
    margin-top: 2px;
  }}
  .no-cross-hosp {{
    font-size: .83rem;
    color: #94a3b8;
    text-align: center;
    padding: 10px 0 4px;
  }}
  .alert-cross-hosp {{
    background: #fff3e0;
    border-left: 4px solid #e65100;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: .82rem;
    color: #7c4700;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
  }}
  /* ---- end cross-hospital ---- */

  .mobile-vaccine-card {{ display:none; background:#f8fafc; border-radius:10px; padding:14px; margin:10px 14px; border:1px solid #e2e8f0; }}
  .mvc-header {{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px; gap:8px; }}
  .mvc-name {{ font-weight:700; font-size:.9rem; color:#1e293b; }}
  .mvc-vaccine {{ font-size:.8rem; color:#64748b; }}
  .mvc-row {{ display:flex; justify-content:space-between; font-size:.83rem; padding:4px 0; border-bottom:1px solid #f1f5f9; gap:8px; }}
  .mvc-row:last-of-type {{ border:none; }}
  .mvc-label {{ color:#94a3b8; font-weight:700; font-size:.75rem; white-space:nowrap; }}
  .mvc-val {{ color:#1e293b; font-weight:500; text-align:right; }}
  .mvc-actions {{ display:flex; gap:6px; margin-top:12px; flex-wrap:wrap; }}
  .mvc-actions button {{ flex:1; min-width:80px; justify-content:center; }}

  .modal-content {{ border:none; border-radius:14px; box-shadow:0 8px 32px rgba(0,0,0,.15); overflow:hidden; animation:zoomIn .25s ease; }}
  @keyframes zoomIn {{ from {{ transform:scale(.92); opacity:0; }} to {{ transform:scale(1); opacity:1; }} }}
  .modal-section {{ border-radius:10px; padding:16px 18px; margin-bottom:12px; }}
  .modal-section h6 {{ font-size:.82rem; font-weight:700; letter-spacing:.8px; text-transform:uppercase; margin-bottom:12px; }}
  .info-row {{ display:flex; gap:6px; font-size:.88rem; padding:4px 0; border-bottom:1px solid rgba(0,0,0,.05); flex-wrap:wrap; }}
  .info-row:last-child {{ border:none; }}
  .info-label {{ color:#64748b; font-weight:600; min-width:140px; flex-shrink:0; }}
  .info-val {{ color:#1e293b; word-break:break-word; }}
  .modal .form-control {{ border-radius:8px; border:1.5px solid #e2e8f0; font-size:.9rem; }}
  .modal .form-control:focus {{ border-color:var(--primary); box-shadow:0 0 0 3px rgba(21,101,192,.12); }}
  .modal .form-label {{ font-size:.85rem; font-weight:600; color:#475569; }}

  .empty-state {{ text-align:center; padding:60px 20px; background:#fff; border-radius:14px; box-shadow:0 2px 12px rgba(0,0,0,.07); }}
  .empty-state i {{ font-size:3rem; color:#cbd5e1; margin-bottom:16px; display:block; }}
  .empty-state h5 {{ color:#64748b; font-weight:600; }}
  .empty-state p {{ font-size:.88rem; color:#94a3b8; }}

  @media (max-width: 991px) {{
    .sidebar {{ transform: translateX(-100%); }}
    .sidebar.open {{ transform: translateX(0); }}
    .sidebar-overlay.open {{ display: block; }}
    .main {{ margin-left: 0; }}
    .hamburger {{ display: block; }}
  }}
  @media (max-width: 640px) {{
    .main {{ padding: 16px 12px; }}
    .desktop-table {{ display: none; }}
    .mobile-vaccine-card {{ display: block; }}
  }}
  @media (min-width: 641px) {{
    .mobile-cards-section {{ display: none; }}
  }}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-left">
    <button class="hamburger" onclick="toggleSidebar()"><i class="fa fa-bars"></i></button>
    <img src="./images/logo.jpg" alt="logo" onerror="this.style.display='none'">
    <div>
      <span class="brand">Child Vaccination</span>
      <span class="subbrand">Hospital Portal</span>
    </div>
  </div>
  <div class="topbar-right">
    <a href="home.py"><i class="fa fa-right-from-bracket me-1"></i> Logout</a>
  </div>
</div>

<div class="sidebar-overlay" id="overlay" onclick="toggleSidebar()"></div>

<nav class="sidebar" id="sidebar">
  <div class="sidebar-label">Menu</div>
  <a href="hospital_dash.py?hospital_id={oid}" class="nav-link"><i class="fa fa-gauge"></i> Dashboard</a>
  <a href="hospital_profile.py?hospital_id={oid}" class="nav-link"><i class="fa fa-user"></i> My Profile</a>
  <hr class="sidebar-divider">
  <div class="sidebar-label">Vaccinations</div>
  <details class="sidebar-group" open>
    <summary>
      <i class="fa-solid fa-syringe"></i> Vaccine Details
      <i class="fa fa-chevron-right caret"></i>
    </summary>
    <div class="sub-links">
      <a href="hospitalpendingvaccine.py?hospital_id={oid}" class="active"><i class="fa-solid fa-clock"></i> Pending</a>
      <a href="hospitalconfirmedvaccine.py?hospital_id={oid}"><i class="fa-solid fa-check"></i> Confirmed</a>
      <a href="hospitalrescheduledvaccine.py?hospital_id={oid}"><i class="fa-solid fa-calendar-days"></i> Rescheduled</a>
      <a href="hospitalcompletedvaccine.py?hospital_id={oid}"><i class="fa-solid fa-circle-check"></i> Completed</a>
    </div>
  </details>
  <hr class="sidebar-divider">
  <div class="sidebar-label">Feedback</div>
    <div class="sub-links">
      <a href="hospitalparentfeedback.py?hospital_id={oid}">
        <i class="fa-solid fa-comments"></i> Parent Feedback
      </a>
    </div>
  </details>
  <hr class="sidebar-divider">
  <a href="home.py" class="nav-link" style="color:#ef9a9a;"><i class="fa fa-right-from-bracket"></i> Logout</a>
</nav>

<main class="main">
  <div class="page-header">
    <div class="page-header-icon"><i class="fa fa-clock"></i></div>
    <div>
      <h4>Pending Vaccine Appointments</h4>
      <p>Review, confirm or reschedule appointments &mdash; previous doses from other hospitals are shown in each record</p>
    </div>
  </div>

  <div class="summary-strip">
    <i class="fa-solid fa-hourglass-half text-warning"></i>
    <span style="font-size:.9rem;color:#475569;font-weight:600;">Total Pending</span>
    <span class="count-badge">{len(appointments)} Record{"s" if len(appointments) != 1 else ""}</span>
  </div>
""")

all_modals = ""

if appointments:
    print("""
  <div class="table-card">
    <div class="table-responsive desktop-table">
      <table class="table vaccine-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Child Name</th>
            <th>Vaccine</th>
            <th>Dose</th>
            <th>Date</th>
            <th>Time</th>
            <th>Prior Doses</th>
            <th>Status</th>
            <th>View</th>
            <th>Confirm</th>
            <th>Reschedule</th>
          </tr>
        </thead>
        <tbody>
""")

    for index, appt in enumerate(appointments, start=1):
        (appt_id_val, child_id, child_name, child_dob, child_gender,
         child_blood_group, vaccine_id, vaccine_name, dose_number,
         appointment_date, appointment_time, reschedule_date, status,
         father_name, parent_email, parent_mobile) = appt

        appointment_date_str  = str(appointment_date)  if appointment_date  else "Not Set"
        appointment_time_str  = str(appointment_time)  if appointment_time  else "Not Set"
        reschedule_date_str   = str(reschedule_date)   if reschedule_date   else "-"
        child_dob_str         = str(child_dob)         if child_dob         else "-"
        child_blood_group_str = str(child_blood_group) if child_blood_group else "N/A"
        child_gender_str      = str(child_gender)      if child_gender      else "-"
        child_name_str        = str(child_name)        if child_name        else "Unknown"
        vaccine_name_str      = str(vaccine_name)      if vaccine_name      else "Unknown"
        father_name_str       = str(father_name)       if father_name       else "-"
        parent_email_str      = str(parent_email)      if parent_email      else "-"
        parent_mobile_str     = str(parent_mobile)     if parent_mobile     else "-"
        dose_number_str       = str(dose_number)       if dose_number       else "-"

        # Cross-hospital history for this child
        prior_doses     = cross_hospital_history.get(child_id, [])
        prior_count     = len(prior_doses)
        prior_badge_str = (
            f'<span class="badge-other-hosp"><i class="fa fa-hospital" style="font-size:.7rem;"></i> '
            f'{prior_count} from other hosp.</span>'
            if prior_count > 0 else
            '<span style="font-size:.78rem;color:#94a3b8;">None</span>'
        )

        # Build the cross-hospital rows for the modal
        if prior_doses:
            ch_alert = (
                f'<div class="alert-cross-hosp">'
                f'<i class="fa fa-triangle-exclamation"></i>'
                f'<span>This child has <strong>{prior_count} previous dose(s)</strong> administered '
                f'at other hospitals. Please review before confirming.</span>'
                f'</div>'
            )
            ch_rows = ""
            for pd in prior_doses:
                ch_rows += (
                    f"<tr>"
                    f"<td><span class='badge-dose'>Dose {pd['dose_number']}</span></td>"
                    f"<td><strong>{pd['vaccine_name']}</strong></td>"
                    f"<td>"
                    f"  <div class='ch-hosp-name'><i class='fa fa-hospital' style='font-size:.8rem;margin-right:5px;'></i>{pd['hospital_name']}</div>"
                    f"  <div class='ch-address'><i class='fa fa-location-dot' style='font-size:.75rem;margin-right:4px;'></i>{pd['address']}</div>"
                    f"</td>"
                    f"<td>{pd['taken_date']}</td>"
                    f"</tr>"
                )
            cross_hosp_html = f"""
        <div class="modal-section cross-hosp-section">
          <div class="ch-title">
            <i class="fa fa-hospital"></i>
            Previous Doses from Other Hospitals
          </div>
          {ch_alert}
          <div style="overflow-x:auto;">
            <table class="cross-hosp-table">
              <thead>
                <tr>
                  <th>Dose No.</th>
                  <th>Vaccine Name</th>
                  <th>Hospital Name &amp; Address</th>
                  <th>Date Given</th>
                </tr>
              </thead>
              <tbody>
                {ch_rows}
              </tbody>
            </table>
          </div>
        </div>"""
        else:
            cross_hosp_html = f"""
        <div class="modal-section cross-hosp-section">
          <div class="ch-title">
            <i class="fa fa-hospital"></i>
            Previous Doses from Other Hospitals
          </div>
          <div class="no-cross-hosp">
            <i class="fa fa-circle-check" style="color:#1d9e75;margin-right:6px;"></i>
            No prior doses from other hospitals found for this child.
          </div>
        </div>"""

        print(f"""
          <tr>
            <td><span style="background:#f1f5f9;color:#475569;padding:3px 8px;border-radius:6px;font-weight:600;">{index}</span></td>
            <td><strong>{child_name_str}</strong></td>
            <td>{vaccine_name_str}</td>
            <td><span class="badge-dose">Dose {dose_number_str}</span></td>
            <td>{appointment_date_str}</td>
            <td>{appointment_time_str}</td>
            <td>{prior_badge_str}</td>
            <td><span class="badge-pending"><i class="fa fa-clock"></i> Pending</span></td>
            <td><button class="btn-view" data-bs-toggle="modal" data-bs-target="#detailModal{appt_id_val}"><i class="fa fa-eye"></i> View</button></td>
            <td><button class="btn-confirm" data-bs-toggle="modal" data-bs-target="#confirmModal{appt_id_val}"><i class="fa fa-check"></i> Confirm</button></td>
            <td><button class="btn-reschedule" data-bs-toggle="modal" data-bs-target="#rescheduleModal{appt_id_val}"><i class="fa fa-calendar-alt"></i> Reschedule</button></td>
          </tr>
""")

        # ---- Build modals ----
        all_modals += f"""
<div class="modal fade" id="detailModal{appt_id_val}" tabindex="-1">
  <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header" style="background:linear-gradient(135deg,#0d1b2a,#1c2d3e);">
        <h5 class="modal-title text-white"><i class="fa fa-info-circle me-2"></i>Appointment Details</h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">

        <div class="modal-section" style="background:#e3f2fd;">
          <h6 style="color:#1565c0;"><i class="fa fa-child me-2"></i>Child Information</h6>
          <div class="row g-0">
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Child Name</span><span class="info-val">{child_name_str}</span></div>
              <div class="info-row"><span class="info-label">Date of Birth</span><span class="info-val">{child_dob_str}</span></div>
              <div class="info-row"><span class="info-label">Gender</span><span class="info-val">{child_gender_str}</span></div>
              <div class="info-row"><span class="info-label">Blood Group</span><span class="info-val"><span class="blood-badge">{child_blood_group_str}</span></span></div>
            </div>
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Parent Name</span><span class="info-val">{father_name_str}</span></div>
              <div class="info-row"><span class="info-label">Email</span><span class="info-val">{parent_email_str}</span></div>
              <div class="info-row"><span class="info-label">Mobile</span><span class="info-val">{parent_mobile_str}</span></div>
            </div>
          </div>
        </div>

        <div class="modal-section" style="background:#e8f5e9;">
          <h6 style="color:#2e7d32;"><i class="fa fa-syringe me-2"></i>Current Appointment</h6>
          <div class="row g-0">
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Vaccine</span><span class="info-val">{vaccine_name_str}</span></div>
              <div class="info-row"><span class="info-label">Dose Number</span><span class="info-val"><span class="badge-dose">Dose {dose_number_str}</span></span></div>
              <div class="info-row"><span class="info-label">Reschedule Date</span><span class="info-val">{reschedule_date_str}</span></div>
            </div>
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Appointment Date</span><span class="info-val">{appointment_date_str}</span></div>
              <div class="info-row"><span class="info-label">Time</span><span class="info-val">{appointment_time_str}</span></div>
              <div class="info-row"><span class="info-label">Status</span><span class="info-val"><span class="badge-pending">Pending</span></span></div>
            </div>
          </div>
        </div>

        {cross_hosp_html}

      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
      </div>
    </div>
  </div>
</div>

<div class="modal fade" id="confirmModal{appt_id_val}" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header" style="background:linear-gradient(135deg,#2e7d32,#66bb6a);">
        <h5 class="modal-title text-white"><i class="fa fa-check-circle me-2"></i>Confirm Appointment</h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <div class="modal-section" style="background:#e8f5e9;">
          <div class="info-row"><span class="info-label">Child</span><span class="info-val"><strong>{child_name_str}</strong></span></div>
          <div class="info-row"><span class="info-label">Vaccine</span><span class="info-val">{vaccine_name_str} &mdash; <span class="badge-dose">Dose {dose_number_str}</span></span></div>
          <div class="info-row"><span class="info-label">Date &amp; Time</span><span class="info-val">{appointment_date_str} at {appointment_time_str}</span></div>
          <div class="info-row"><span class="info-label">Parent Email</span><span class="info-val">{parent_email_str}</span></div>
        </div>
        {'<div class="alert-cross-hosp mb-2"><i class="fa fa-triangle-exclamation"></i><span><strong>' + str(prior_count) + ' prior dose(s)</strong> from other hospitals on record. See View for details.</span></div>' if prior_count > 0 else ''}
        <div class="alert alert-info mb-0" style="font-size:.85rem;">
          <i class="fa fa-envelope me-1"></i> A confirmation email will be sent to the parent automatically.
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
        <a href="hospitalpendingvaccine.py?hospital_id={hospital_id}&action=confirm&appt_id={appt_id_val}" class="btn btn-success">
          <i class="fa fa-check me-1"></i> Yes, Confirm &amp; Send Email
        </a>
      </div>
    </div>
  </div>
</div>

<div class="modal fade" id="rescheduleModal{appt_id_val}" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header" style="background:linear-gradient(135deg,#f57f17,#ffca28);">
        <h5 class="modal-title"><i class="fa fa-calendar-alt me-2"></i>Reschedule Appointment</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <div class="modal-section" style="background:#fff8e1;margin-bottom:14px;">
          <div class="info-row"><span class="info-label">Child</span><span class="info-val"><strong>{child_name_str}</strong></span></div>
          <div class="info-row"><span class="info-label">Vaccine</span><span class="info-val">{vaccine_name_str} &mdash; Dose {dose_number_str}</span></div>
          <div class="info-row"><span class="info-label">Current Date</span><span class="info-val">{appointment_date_str} at {appointment_time_str}</span></div>
        </div>
        <form method="get" action="hospitalpendingvaccine.py">
          <input type="hidden" name="hospital_id" value="{hospital_id}">
          <input type="hidden" name="action" value="reschedule">
          <input type="hidden" name="appt_id" value="{appt_id_val}">
          <div class="mb-3">
            <label class="form-label">New Date <span class="text-danger">*</span></label>
            <input type="date" name="reschedule_date" class="form-control" required min="{today_str}">
          </div>
          <div class="mb-3">
            <label class="form-label">New Time</label>
            <input type="time" name="reschedule_time" class="form-control">
          </div>
          <div class="alert alert-info mb-3" style="font-size:.85rem;">
            <i class="fa fa-envelope me-1"></i> A reschedule email will be sent to the parent automatically.
          </div>
          <div class="d-flex justify-content-end gap-2">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="submit" class="btn btn-warning">
              <i class="fa fa-calendar-check me-1"></i> Reschedule &amp; Send Email
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</div>"""

    print("        </tbody>\n      </table>\n    </div>")

    # ---- Mobile cards ----
    print("""    <div class="mobile-cards-section" style="padding-bottom:8px;">""")
    for index, appt in enumerate(appointments, start=1):
        (appt_id_val, child_id, child_name, child_dob, child_gender,
         child_blood_group, vaccine_id, vaccine_name, dose_number,
         appointment_date, appointment_time, reschedule_date, status,
         father_name, parent_email, parent_mobile) = appt

        appointment_date_str = str(appointment_date) if appointment_date else "Not Set"
        appointment_time_str = str(appointment_time) if appointment_time else "Not Set"
        child_name_str       = str(child_name)       if child_name       else "Unknown"
        vaccine_name_str     = str(vaccine_name)     if vaccine_name     else "Unknown"
        dose_number_str      = str(dose_number)      if dose_number      else "-"
        prior_count_m        = len(cross_hospital_history.get(child_id, []))

        print(f"""
      <div class="mobile-vaccine-card">
        <div class="mvc-header">
          <div>
            <div class="mvc-name">{child_name_str}</div>
            <div class="mvc-vaccine">{vaccine_name_str}</div>
          </div>
          <span class="badge-pending"><i class="fa fa-clock"></i> Pending</span>
        </div>
        <div class="mvc-row"><span class="mvc-label">Serial</span><span class="mvc-val">#{index}</span></div>
        <div class="mvc-row"><span class="mvc-label">Dose</span><span class="mvc-val"><span class="badge-dose">Dose {dose_number_str}</span></span></div>
        <div class="mvc-row"><span class="mvc-label">Date</span><span class="mvc-val">{appointment_date_str}</span></div>
        <div class="mvc-row"><span class="mvc-label">Time</span><span class="mvc-val">{appointment_time_str}</span></div>
        {'<div class="mvc-row"><span class="mvc-label">Other Hosp Doses</span><span class="mvc-val badge-other-hosp">' + str(prior_count_m) + ' record(s)</span></div>' if prior_count_m > 0 else ''}
        <div class="mvc-actions">
          <button class="btn-view" data-bs-toggle="modal" data-bs-target="#detailModal{appt_id_val}"><i class="fa fa-eye"></i> View</button>
          <button class="btn-confirm" data-bs-toggle="modal" data-bs-target="#confirmModal{appt_id_val}"><i class="fa fa-check"></i> Confirm</button>
          <button class="btn-reschedule" data-bs-toggle="modal" data-bs-target="#rescheduleModal{appt_id_val}"><i class="fa fa-calendar-alt"></i> Reschedule</button>
        </div>
      </div>
""")
    print("    </div>")
    print("  </div>")

else:
    print("""
  <div class="empty-state">
    <i class="fa-solid fa-hourglass-end"></i>
    <h5>No Pending Appointments</h5>
    <p>All caught up! New pending appointments will appear here.</p>
  </div>
""")

print(all_modals)

print("""
</main>
<script>
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('overlay').classList.toggle('open');
}
</script>
</body>
</html>
""")

con.close()