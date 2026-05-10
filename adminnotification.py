#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
import cgi
import cgitb
import pymysql
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
from datetime import date
from collections import defaultdict

def add_months(original_date, months):
    months = int(months) if months else 0
    month  = original_date.month - 1 + months
    year   = original_date.year + month // 12
    month  = month % 12 + 1
    day    = min(original_date.day, [31,
        29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
        31,30,31,30,31,31,30,31,30,31][month-1])
    return date(year, month, day)

print("Content-type:text/html\r\n\r\n")
cgitb.enable()
sys.stdout.reconfigure(encoding='utf-8')
form = cgi.FieldStorage()

con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()
def qc(sql):
    cur.execute(sql)
    return cur.fetchone()[0]
# Feedback counts
total_fb = qc("SELECT COUNT(*) FROM feedback")
low_fb   = qc("SELECT COUNT(*) FROM feedback WHERE rating < 2")

def qc(sql):
    cur.execute(sql)
    return cur.fetchone()[0]

pending_parents    = qc("SELECT COUNT(*) FROM parent WHERE status='pending'")
approved_parents   = qc("SELECT COUNT(*) FROM parent WHERE status='approved'")
rejected_parents   = qc("SELECT COUNT(*) FROM parent WHERE status='rejected'")
total_parents      = qc("SELECT COUNT(*) FROM parent")
pending_hospitals  = qc("SELECT COUNT(*) FROM hospital WHERE status='pending'")
approved_hospitals = qc("SELECT COUNT(*) FROM hospital WHERE status='approved'")
rejected_hospitals = qc("SELECT COUNT(*) FROM hospital WHERE status='rejected'")
total_hospitals    = qc("SELECT COUNT(*) FROM hospital")
total_notified     = qc("SELECT COUNT(*) FROM child_vaccine WHERE LOWER(TRIM(status))='notified'")
total_children     = qc("SELECT COUNT(*) FROM children")
total_completed    = qc("SELECT COUNT(*) FROM child_vaccine WHERE status='completed'")

def nb(n, cls=""):
    return f'<span class="nbadge {cls}">{n}</span>' if n else ""

def sb(n):
    return f'<span class="nbadge" style="margin-left:auto">{n}</span>' if n else ""

# ================= EMAIL =================
def send_email(to_email, child_name, vaccine_name, scheduled_date, dose_number, father_name):
    sender_email    = "santhiyanks@gmail.com"
    sender_password = "snnr avxt cqgb ocwy"

    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4f8;padding:30px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.10);max-width:600px;width:100%;">
        <tr>
          <td style="background:linear-gradient(135deg,#0d47a1 0%,#1565c0 60%,#1976d2 100%);padding:36px 40px 28px;text-align:center;">
            <div style="background:rgba(255,255,255,0.15);display:inline-block;border-radius:50%;width:72px;height:72px;line-height:72px;margin-bottom:14px;font-size:34px;">&#128137;</div>
            <h1 style="margin:0;color:#ffffff;font-size:24px;font-weight:700;letter-spacing:0.5px;">Vaccination Reminder</h1>
            <p style="margin:8px 0 0;color:rgba(255,255,255,0.80);font-size:14px;">Child Vaccination Management System</p>
          </td>
        </tr>
        <tr>
          <td style="padding:32px 40px 0;">
            <p style="margin:0;font-size:16px;color:#1c1c1c;">Dear <strong>{father_name}</strong>,</p>
            <p style="margin:12px 0 0;font-size:15px;color:#444;line-height:1.7;">
              We would like to remind you that your child <strong style="color:#1565c0;">{child_name}</strong>
              is due for an important vaccination. Please review the details below.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 40px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background:linear-gradient(135deg,#e3f2fd,#f8fbff);border-radius:12px;border:1.5px solid #bbdefb;overflow:hidden;">
              <tr>
                <td style="background:#1565c0;padding:12px 24px;">
                  <span style="color:#fff;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1px;">&#128203; Vaccination Details</span>
                </td>
              </tr>
              <tr>
                <td style="padding:24px;">
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr><td style="padding:10px 0;border-bottom:1px solid #e0ecf8;">
                      <span style="color:#6b7280;font-size:12px;font-weight:600;text-transform:uppercase;">Child Name</span><br>
                      <span style="color:#1c1c1c;font-size:15px;font-weight:600;margin-top:4px;display:block;">&#128376; {child_name}</span>
                    </td></tr>
                    <tr><td style="padding:10px 0;border-bottom:1px solid #e0ecf8;">
                      <span style="color:#6b7280;font-size:12px;font-weight:600;text-transform:uppercase;">Vaccine Name</span><br>
                      <span style="color:#1c1c1c;font-size:15px;font-weight:600;margin-top:4px;display:block;">&#128137; {vaccine_name}</span>
                    </td></tr>
                    <tr><td style="padding:10px 0;border-bottom:1px solid #e0ecf8;">
                      <span style="color:#6b7280;font-size:12px;font-weight:600;text-transform:uppercase;">Dose Number</span><br>
                      <span style="display:inline-block;margin-top:6px;background:#1565c0;color:#fff;padding:5px 18px;border-radius:20px;font-size:13px;font-weight:700;">Dose {dose_number}</span>
                    </td></tr>
                    <tr><td style="padding:10px 0;">
                      <span style="color:#6b7280;font-size:12px;font-weight:600;text-transform:uppercase;">Scheduled Date</span><br>
                      <span style="display:inline-block;margin-top:6px;background:#e8f5e9;color:#2e7d32;padding:6px 18px;border-radius:20px;font-size:14px;font-weight:700;border:1px solid #c8e6c9;">&#128197; {scheduled_date}</span>
                    </td></tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:0 40px 24px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff8e1;border-radius:10px;border-left:4px solid #f57f17;">
              <tr><td style="padding:16px 20px;">
                <p style="margin:0;font-size:13px;color:#7c4d00;font-weight:700;">&#9888;&#65039; Important Reminders</p>
                <ul style="margin:8px 0 0;padding-left:18px;color:#5c4000;font-size:13px;line-height:2.0;">
                  <li>Please bring your child's vaccination card / health booklet.</li>
                  <li>Carry a valid ID proof of the parent.</li>
                  <li>Arrive at the hospital on or before the scheduled date.</li>
                  <li>Inform the doctor of any recent illness or allergies.</li>
                </ul>
              </td></tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:0 40px 32px;text-align:center;">
            <div style="background:#e8f5e9;border-radius:10px;padding:14px 20px;">
              <p style="margin:0;font-size:13px;color:#2e7d32;font-weight:600;">&#9989; Vaccination protects your child from serious diseases. Stay on schedule!</p>
            </div>
          </td>
        </tr>
        <tr>
          <td style="background:#1c1c2e;padding:20px 40px;text-align:center;">
            <p style="margin:0;color:rgba(255,255,255,0.5);font-size:12px;">&copy; 2026 Child Vaccination System &mdash; Admin Panel</p>
            <p style="margin:6px 0 0;color:rgba(255,255,255,0.3);font-size:11px;">This is an automated notification. Please do not reply to this email.</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Vaccination Reminder - {child_name} | {vaccine_name} (Dose {dose_number})"
        msg["From"]    = f"Child Vaccination System <{sender_email}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html_body, "html"))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True
    except Exception:
        return False


# ================= NOTIFY LOGIC =================
if "notify_id" in form:
    child_id = form.getvalue("notify_id")

    cur.execute("""
        SELECT c.child_id, c.child_name, c.dob, p.email, c.parent_id, p.father_name,
               p.state, p.district
        FROM children c JOIN parent p ON c.parent_id = p.parent_id
        WHERE c.child_id = %s
    """, (child_id,))
    child = cur.fetchone()

    if child:
        cid, child_name, dob, parent_email, parent_id, father_name, p_state, p_district = child

        cur.execute("""
            SELECT vaccine_id, vaccine_name, minimum_age, dose_number
            FROM vaccine
            WHERE LOWER(TRIM(status)) = 'confirmed'
            ORDER BY COALESCE(minimum_age, 0) ASC, COALESCE(dose_number, 1) ASC
        """)
        all_vaccines = cur.fetchall()

        cur.execute("""
            SELECT DISTINCT vaccine_id FROM child_vaccine WHERE child_id = %s
        """, (cid,))
        already_has_record = set(row[0] for row in cur.fetchall())

        pending_vaccines = [v for v in all_vaccines if v[0] not in already_has_record]

        if not pending_vaccines:
            print("<script>alert('All vaccines already notified for this child!');window.location.href='adminnotification.py'</script>")
        else:
            vaccine_id, vaccine_name, minimum_age, dose_number = pending_vaccines[0]
            dose_number = dose_number if dose_number else "1"

            try:
                min_age_val    = int(minimum_age) if minimum_age is not None else 0
                scheduled_date = add_months(dob, min_age_val)
            except Exception:
                scheduled_date = dob

            hosp_id = None
            cur.execute("""
                SELECT hospital_id FROM hospital
                WHERE LOWER(TRIM(state))    = LOWER(TRIM(%s))
                  AND LOWER(TRIM(district)) = LOWER(TRIM(%s))
                  AND LOWER(TRIM(status))   = 'approved'
                LIMIT 1
            """, (p_state, p_district))
            hosp_row = cur.fetchone()

            if not hosp_row:
                cur.execute("""
                    SELECT hospital_id FROM hospital
                    WHERE LOWER(TRIM(state))  = LOWER(TRIM(%s))
                      AND LOWER(TRIM(status)) = 'approved'
                    LIMIT 1
                """, (p_state,))
                hosp_row = cur.fetchone()

            if not hosp_row:
                cur.execute("""
                    SELECT hospital_id FROM hospital
                    WHERE LOWER(TRIM(status)) = 'approved'
                    LIMIT 1
                """)
                hosp_row = cur.fetchone()

            hosp_id = hosp_row[0] if hosp_row else None

            if send_email(parent_email, child_name, vaccine_name, scheduled_date, dose_number, father_name):
                try:
                    cur.execute("""
                        INSERT INTO child_vaccine
                            (child_id, vaccine_id, hospital_id,
                             appointment_date, appointment_time, dose_number, status)
                        VALUES (%s, %s, %s, %s, '09:00:00', %s, 'notified')
                    """, (cid, vaccine_id, hosp_id, scheduled_date, dose_number))
                    con.commit()

                    remaining = len(pending_vaccines) - 1
                    msg_text  = f"Notification Sent for {vaccine_name} - Dose {dose_number}! ({remaining} vaccine(s) remaining)"
                    print(f"<script>alert('{msg_text}');window.location.href='adminnotification.py'</script>")
                except Exception as db_err:
                    con.rollback()
                    err_msg = str(db_err).replace("'", "")
                    print(f"<script>alert('Database Error: {err_msg}');window.location.href='adminnotification.py'</script>")
            else:
                print("<script>alert('Email Sending Failed! Check SMTP App Password.');window.location.href='adminnotification.py'</script>")
    else:
        print("<script>alert('Child not found!');window.location.href='adminnotification.py'</script>")

    con.close()
    exit()


# ================= FETCH CHILDREN FOR PAGE =================
cur.execute("""
    SELECT c.child_id, c.child_name, c.dob, c.weight,
           c.gender, c.blood_group, c.identification_mark,
           p.father_name, p.father_age, p.mother_name, p.mother_age, p.mother_weight,
           p.email, p.mobile_number, p.occupation,
           p.state, p.district, p.address, p.pincode, p.father_aadhar_image, p.parent_profile,
           p.status AS parent_status
    FROM children c LEFT JOIN parent p ON c.parent_id = p.parent_id
    ORDER BY c.child_id
""")
children = cur.fetchall()

cur.execute("SELECT COUNT(*) FROM vaccine WHERE LOWER(TRIM(status)) = 'confirmed'")
total_confirmed_vaccines = cur.fetchone()[0]

# Vaccines per child (for the child-details section)
cur.execute("""
    SELECT cv.child_id, v.vaccine_name, v.minimum_age, cv.status, cv.taken_date
    FROM child_vaccine cv
    LEFT JOIN vaccine v ON cv.vaccine_id = v.vaccine_id
    ORDER BY v.minimum_age ASC
""")
vax_by_child = defaultdict(list)
for r in cur.fetchall():
    vax_by_child[r[0]].append({"name": r[1], "age": r[2], "status": r[3], "date": r[4]})

# Hospital per child
hosp_by_child = {}
try:
    cur.execute("""
        SELECT a.child_id, h.hospital_name, h.hospital_number, h.state, h.district
        FROM appointments a
        LEFT JOIN hospital h ON a.hospital_id = h.hospital_id
        WHERE h.hospital_id IS NOT NULL
    """)
    for r in cur.fetchall():
        hosp_by_child[r[0]] = {"name": r[1], "number": r[2], "state": r[3], "district": r[4]}
except Exception:
    pass

pending_children  = []
notified_children = []

for child in children:
    child_id = child[0]

    cur.execute("""
        SELECT COUNT(DISTINCT vaccine_id)
        FROM child_vaccine WHERE child_id = %s
    """, (child_id,))
    record_count = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM child_vaccine
        WHERE child_id = %s AND LOWER(TRIM(status)) IN ('notified', 'completed')
    """, (child_id,))
    notified_count = cur.fetchone()[0]

    if notified_count > 0:
        notified_children.append(child)
    if record_count < total_confirmed_vaccines:
        pending_children.append(child)

tp_alert = (f'<a href="adminpendingparent.py" class="talert pa">'
            f'<i class="fa-solid fa-user-clock"></i>'
            f'<span> {pending_parents} Parent Pending</span></a>') if pending_parents else ""

th_alert = (f'<a href="adminpendingmanager.py" class="talert ho">'
            f'<i class="fa-solid fa-hospital"></i>'
            f'<span> {pending_hospitals} Hospital Pending</span></a>') if pending_hospitals else ""

# ================= HTML PAGE =================
print(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Notification Center - Admin Panel</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    *,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
    :root{{
      --p:#1565c0;--pd:#0d47a1;--pl:#e3f2fd;--ac:#ff6f00;
      --sw:260px;--hh:60px;--tx:#1c1c1c;--mu:#6b7280;
      --bg:#f0f4f8;--ca:#fff;--bo:#dde3ea;
      --da:#e53935;--su:#2e7d32;--sl:#e8f5e9;
      --wa:#f57f17;--wl:#fff8e1;
      --ra:10px;--sh:0 2px 16px rgba(0,0,0,.09);
      --tr:.25s ease;--fn:'Segoe UI',Arial,sans-serif
    }}
    html{{scroll-behavior:smooth}}
    body{{font-family:var(--fn);background:var(--bg);color:var(--tx);min-height:100vh;line-height:1.6}}
    a{{text-decoration:none;color:inherit}}
    img{{max-width:100%;height:auto;display:block;object-fit:cover}}

    /* ===== OVERLAY ===== */
    .overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1100}}
    .overlay.active{{display:block}}

    /* ===== SIDEBAR ===== */
    .sidebar{{width:var(--sw);height:100vh;position:fixed;top:0;left:0;
      background:linear-gradient(180deg,#0d2a6e 0%,#1565c0 60%,#0d47a1 100%);
      display:flex;flex-direction:column;z-index:1200;overflow-y:auto;overflow-x:hidden;
      transition:transform var(--tr);scrollbar-width:thin;scrollbar-color:rgba(255,255,255,.2) transparent}}
    .sidebar::-webkit-scrollbar{{width:4px}}
    .sidebar::-webkit-scrollbar-thumb{{background:rgba(255,255,255,.2);border-radius:2px}}
    .sbrand{{display:flex;align-items:center;gap:12px;padding:18px 16px 14px;border-bottom:1px solid rgba(255,255,255,.15)}}
    .sbrand img{{width:42px;height:42px;border-radius:50%;border:2px solid rgba(255,255,255,.4);flex-shrink:0}}
    .sbrand span{{font-size:.95rem;font-weight:700;color:#fff;line-height:1.3}}
    .sbrand small{{display:block;font-size:.72rem;color:rgba(255,255,255,.6);font-weight:400}}
    .snav{{flex:1;padding:10px 0}}
    .ng{{border-bottom:1px solid rgba(255,255,255,.07)}}
    .ngt{{width:100%;background:transparent;border:none;cursor:pointer;display:flex;align-items:center;gap:10px;
      padding:13px 16px;color:rgba(255,255,255,.88);font-size:.88rem;font-weight:500;font-family:var(--fn);
      transition:background var(--tr),color var(--tr);text-align:left}}
    .ngt:hover,.ng.open .ngt{{background:rgba(255,255,255,.1);color:#fff}}
    .ngt .ic{{font-size:.95rem;width:20px;text-align:center;flex-shrink:0}}
    .ngt .ar{{margin-left:auto;font-size:.68rem;transition:transform var(--tr);flex-shrink:0}}
    .ng.open .ngt .ar{{transform:rotate(180deg)}}
    .nsub{{max-height:0;overflow:hidden;transition:max-height .35s ease;background:rgba(0,0,0,.15)}}
    .ng.open .nsub{{max-height:400px}}
    .nsub a{{display:flex;align-items:center;gap:8px;padding:9px 16px 9px 48px;color:rgba(255,255,255,.72);
      font-size:.83rem;transition:background var(--tr),color var(--tr);border-left:3px solid transparent;cursor:pointer}}
    .nsub a:hover,.nsub a.active{{background:rgba(255,255,255,.1);color:#fff;border-left-color:var(--ac)}}
    .nbadge{{background:#e53935;color:#fff;font-size:.67rem;font-weight:700;min-width:18px;height:18px;
      border-radius:9px;display:inline-flex;align-items:center;justify-content:center;padding:0 5px}}
    .nbadge.or{{background:var(--ac)}}.nbadge.gr{{background:#2e7d32}}.nbadge.gy{{background:#777}}
    .sfooter{{padding:14px 12px;border-top:1px solid rgba(255,255,255,.12)}}
    .btn-logout{{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:10px;
      background:var(--da);color:#fff;border:none;border-radius:var(--ra);font-size:.88rem;font-weight:600;
      font-family:var(--fn);cursor:pointer;text-decoration:none;transition:background var(--tr)}}
    .btn-logout:hover{{background:#b71c1c}}

    /* ===== MAIN WRAP ===== */
    .mwrap{{margin-left:var(--sw);display:flex;flex-direction:column;min-height:100vh}}
    .topbar{{height:var(--hh);background:var(--ca);border-bottom:1px solid var(--bo);position:sticky;top:0;
      z-index:900;display:flex;align-items:center;justify-content:space-between;padding:0 20px;
      box-shadow:0 1px 8px rgba(0,0,0,.06)}}
    .tbl{{display:flex;align-items:center;gap:12px}}
    .ttitle{{font-size:1rem;font-weight:700;color:var(--p)}}
    .tbcrumb{{font-size:.8rem;color:var(--mu)}}
    .tbcrumb a{{color:var(--p)}}
    .tbcrumb span{{margin:0 5px}}
    .hamburger{{display:none;flex-direction:column;gap:5px;background:transparent;border:none;cursor:pointer;
      padding:6px;border-radius:6px}}
    .hamburger span{{display:block;width:22px;height:2px;background:var(--tx);border-radius:2px;
      transition:transform var(--tr),opacity var(--tr)}}
    .hamburger.open span:nth-child(1){{transform:translateY(7px) rotate(45deg)}}
    .hamburger.open span:nth-child(2){{opacity:0}}
    .hamburger.open span:nth-child(3){{transform:translateY(-7px) rotate(-45deg)}}
    .tbr{{display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
    .abadge{{background:var(--pl);color:var(--p);padding:5px 14px;border-radius:20px;font-size:.82rem;font-weight:600}}
    .talert{{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:20px;font-size:.78rem;font-weight:700}}
    .talert.pa{{background:#fff3e0;color:#e65100}}
    .talert.ho{{background:#e8f5e9;color:#2e7d32}}
    .pc{{padding:24px 20px;flex:1}}

    /* ===== SECTIONS ===== */
    .section{{display:none}}.section.active{{display:block}}

    /* ===== NOTIFICATION SECTION ===== */
    .stats-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin-bottom:24px}}
    .stat-mini{{background:var(--ca);border-radius:var(--ra);padding:16px 18px;display:flex;align-items:center;
      gap:14px;box-shadow:var(--sh);border:1px solid var(--bo)}}
    .stat-mini-icon{{width:40px;height:40px;border-radius:10px;display:flex;align-items:center;
      justify-content:center;font-size:1rem;flex-shrink:0}}
    .stat-mini-icon.blue{{background:var(--pl);color:var(--p)}}
    .stat-mini-icon.orange{{background:var(--wl);color:var(--wa)}}
    .stat-mini-info h4{{font-size:1.3rem;font-weight:700;line-height:1}}
    .stat-mini-info p{{font-size:.75rem;color:var(--mu);margin-top:3px}}
    .section-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap;gap:10px}}
    .section-label{{display:flex;align-items:center;gap:10px}}
    .section-label-icon{{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:.9rem;flex-shrink:0}}
    .section-label-icon.pending{{background:var(--pl);color:var(--p)}}
    .section-label-icon.notified{{background:var(--wl);color:var(--wa)}}
    .section-label h3{{font-size:1rem;font-weight:700}}
    .section-label p{{font-size:.8rem;color:var(--mu);margin-top:1px}}
    .table-card{{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);overflow:hidden;margin-bottom:28px}}
    .table-card-header{{padding:13px 18px;display:flex;align-items:center;gap:8px;font-size:.9rem;font-weight:700;color:#fff}}
    .table-card-header.pending{{background:linear-gradient(90deg,var(--p),var(--pd))}}
    .table-card-header.notified{{background:linear-gradient(90deg,#e65100,var(--wa))}}
    .tw{{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}}
    table{{width:100%;border-collapse:collapse;min-width:580px}}
    thead{{background:#263238;color:#fff}}
    th{{padding:11px 14px;text-align:left;font-size:.8rem;font-weight:600;text-transform:uppercase;letter-spacing:.4px;white-space:nowrap}}
    td{{padding:11px 14px;font-size:.87rem;border-bottom:1px solid var(--bo);white-space:nowrap;vertical-align:middle}}
    tbody tr:hover{{background:var(--pl)}}
    tbody tr:last-child td{{border-bottom:none}}
    .snum{{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;background:var(--pl);color:var(--p);border-radius:50%;font-size:.78rem;font-weight:700}}
    .badge-pending{{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;background:var(--pl);color:var(--p);border-radius:20px;font-size:.75rem;font-weight:700}}
    .badge-notified{{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;background:var(--wl);color:var(--wa);border-radius:20px;font-size:.75rem;font-weight:700}}
    .btn-notify{{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;background:var(--su);color:#fff;border:none;border-radius:7px;font-family:var(--fn);font-size:.82rem;font-weight:600;cursor:pointer;transition:background var(--tr),transform var(--tr);text-decoration:none;white-space:nowrap}}
    .btn-notify:hover{{background:#1b5e20;transform:translateY(-1px)}}
    .btn-view{{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;background:var(--pl);color:var(--p);border:1px solid var(--p);border-radius:7px;font-family:var(--fn);font-size:.82rem;font-weight:600;cursor:pointer;transition:background var(--tr);white-space:nowrap}}
    .btn-view:hover{{background:var(--p);color:#fff}}
    .already-notified{{font-size:.82rem;color:var(--mu);font-style:italic}}
    .empty-row td{{text-align:center;padding:32px;color:var(--mu);font-size:.9rem}}

    /* ===== MODAL (for notification view) ===== */
    .modal-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:2000;align-items:center;justify-content:center;padding:16px}}
    .modal-overlay.active{{display:flex}}
    .modal-box{{background:var(--ca);border-radius:var(--ra);width:100%;max-width:720px;max-height:90vh;display:flex;flex-direction:column;box-shadow:0 8px 40px rgba(0,0,0,.2);animation:slideUp .25s ease}}
    @keyframes slideUp{{from{{transform:translateY(40px);opacity:0}}to{{transform:translateY(0);opacity:1}}}}
    .modal-head{{background:linear-gradient(90deg,var(--p),var(--pd));color:#fff;padding:16px 20px;display:flex;align-items:center;justify-content:space-between;border-radius:var(--ra) var(--ra) 0 0;flex-shrink:0}}
    .modal-head h4{{font-size:1rem;font-weight:700}}
    .modal-close{{background:rgba(255,255,255,.2);border:none;color:#fff;width:28px;height:28px;border-radius:50%;cursor:pointer;font-size:.9rem;display:flex;align-items:center;justify-content:center;transition:background var(--tr)}}
    .modal-close:hover{{background:rgba(255,255,255,.35)}}
    .modal-body{{padding:20px;overflow-y:auto;flex:1}}
    .modal-section-title{{font-size:.8rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--p);margin:16px 0 10px;padding-bottom:6px;border-bottom:2px solid var(--pl)}}
    .modal-section-title:first-child{{margin-top:0}}
    .detail-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px 20px}}
    .detail-item label{{display:block;font-size:.72rem;color:var(--mu);font-weight:600;text-transform:uppercase;letter-spacing:.4px;margin-bottom:2px}}
    .detail-item span{{font-size:.9rem;font-weight:500;color:var(--tx)}}
    .modal-img{{width:80px;height:80px;border-radius:8px;object-fit:cover;border:2px solid var(--bo)}}
    .img-row{{display:flex;gap:16px;flex-wrap:wrap;margin-top:10px}}
    .img-item{{text-align:center}}
    .img-item p{{font-size:.75rem;color:var(--mu);margin-top:5px}}
    .vac-table{{width:100%;border-collapse:collapse;margin-top:8px;font-size:.85rem}}
    .vac-table th{{background:var(--p);color:#fff;padding:8px 12px;text-align:left;font-size:.78rem}}
    .vac-table td{{padding:8px 12px;border-bottom:1px solid var(--bo)}}
    .vac-table tbody tr:hover{{background:var(--pl)}}
    .vac-badge-done{{background:var(--sl);color:var(--su);padding:2px 8px;border-radius:10px;font-size:.74rem;font-weight:700}}
    .vac-badge-pending{{background:var(--pl);color:var(--p);padding:2px 8px;border-radius:10px;font-size:.74rem;font-weight:700}}
    .vac-badge-notified{{background:var(--wl);color:var(--wa);padding:2px 8px;border-radius:10px;font-size:.74rem;font-weight:700}}
    .vac-badge-rescheduled{{background:#fff3e0;color:#e65100;padding:2px 8px;border-radius:10px;font-size:.74rem;font-weight:700}}
    .vac-badge-confirmed{{background:var(--sl);color:var(--su);padding:2px 8px;border-radius:10px;font-size:.74rem;font-weight:700}}

    /* ===== CHILDREN SECTION ===== */
    .page-hdr{{background:linear-gradient(120deg,var(--p),var(--pd));color:#fff;border-radius:var(--ra);padding:22px 28px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}}
    .page-hdr h2{{font-size:1.1rem;font-weight:700;margin-bottom:3px}}
    .page-hdr p{{font-size:.83rem;opacity:.8}}
    .page-hdr-badge{{background:rgba(255,255,255,.18);padding:7px 16px;border-radius:20px;font-size:.83rem;font-weight:700}}
    .toolbar{{display:flex;align-items:center;gap:12px;margin-bottom:18px;flex-wrap:wrap}}
    .sbox{{position:relative;flex:1;min-width:200px}}
    .sbox i{{position:absolute;left:11px;top:50%;transform:translateY(-50%);color:var(--mu);font-size:.82rem}}
    .sbox input{{width:100%;padding:9px 12px 9px 34px;border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.85rem;background:var(--ca)}}
    .sbox input:focus{{outline:none;border-color:var(--p)}}
    .fsel{{padding:9px 14px;border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.85rem;background:var(--ca);color:var(--tx);cursor:pointer}}
    .fsel:focus{{outline:none;border-color:var(--p)}}
    .cnt-lbl{{font-size:.84rem;color:var(--mu);font-weight:600;white-space:nowrap}}
    .child-card{{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);margin-bottom:16px;overflow:hidden}}
    .ccard-top{{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;flex-wrap:wrap;gap:10px}}
    .ccard-left{{display:flex;align-items:center;gap:14px}}
    .avatar{{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--p),var(--pd));border:2px solid var(--pl);display:flex;align-items:center;justify-content:center;font-size:1.15rem;font-weight:800;color:#fff;flex-shrink:0}}
    .ccard-name{{font-size:.96rem;font-weight:700;color:var(--tx)}}
    .ccard-sub{{font-size:.76rem;color:var(--mu);margin-top:2px}}
    .ccard-right{{display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
    .btn-viewmore{{display:inline-flex;align-items:center;gap:6px;padding:7px 16px;background:var(--p);color:#fff;border:none;border-radius:8px;font-size:.82rem;font-weight:600;font-family:var(--fn);cursor:pointer;transition:background var(--tr)}}
    .btn-viewmore:hover{{background:var(--pd)}}
    .btn-viewmore .vm-icon{{transition:transform var(--tr)}}
    .btn-viewmore.open .vm-icon{{transform:rotate(180deg)}}
    .ccard-details{{display:none;border-top:1px solid var(--bo)}}
    .ccard-details.open{{display:block}}
    .detail-tabs{{display:flex;border-bottom:2px solid var(--bo);background:#fafbfc}}
    .dtab{{flex:1;background:transparent;border:none;border-bottom:3px solid transparent;margin-bottom:-2px;padding:11px 10px;font-family:var(--fn);font-size:.83rem;font-weight:600;color:var(--mu);cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;transition:color var(--tr),border-color var(--tr),background var(--tr);white-space:nowrap}}
    .dtab:hover{{color:var(--p);background:var(--pl)}}
    .dtab.active{{color:var(--p);border-bottom-color:var(--ac);background:#f0f7ff}}
    .dpanel{{display:none;padding:18px 20px}}
    .dpanel.active{{display:block}}
    .dg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px 20px;margin-bottom:4px}}
    .di{{background:var(--bg);border:1px solid var(--bo);border-radius:8px;padding:9px 13px}}
    .di label{{display:block;font-size:.67rem;color:var(--mu);font-weight:700;text-transform:uppercase;letter-spacing:.4px;margin-bottom:3px}}
    .di span{{font-size:.86rem;font-weight:600;color:var(--tx);word-break:break-word}}
    .di.full{{grid-column:1/-1}}
    .vsumbadges{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}}
    .vsb{{display:flex;align-items:center;gap:5px;padding:5px 14px;border-radius:20px;font-size:.76rem;font-weight:700}}
    .vsb.tk{{background:#e8f5e9;color:#2e7d32}}
    .vsb.nt{{background:#fff3e0;color:#e65100}}
    .vsb.pd{{background:#fff8e1;color:#f57f17}}
    .vtable{{width:100%;border-collapse:collapse;font-size:.83rem}}
    .vtable th{{background:#f0f4f8;color:var(--p);padding:8px 12px;text-align:left;font-size:.74rem;font-weight:700;text-transform:uppercase;border-bottom:2px solid var(--bo)}}
    .vtable td{{padding:8px 12px;border-bottom:1px solid var(--bo)}}
    .vtable tbody tr:hover{{background:var(--pl)}}
    .vtable tbody tr:last-child td{{border-bottom:none}}
    .bx{{display:inline-flex;align-items:center;padding:3px 10px;border-radius:20px;font-size:.74rem;font-weight:700}}
    .bp{{background:#fff8e1;color:#f57f17}}.ba{{background:#e8f5e9;color:#2e7d32}}
    .br{{background:#ffebee;color:#c62828}}.bn{{background:#fff3e0;color:#e65100}}
    .bt{{background:#e8f5e9;color:#2e7d32}}.bgy{{background:#f3f4f6;color:#555}}
    .empty{{text-align:center;padding:60px 20px;color:var(--mu)}}
    .empty i{{font-size:3rem;opacity:.3;display:block;margin-bottom:14px}}

    footer{{background:#1c1c2e;color:rgba(255,255,255,.6);text-align:center;padding:14px 20px;font-size:.8rem}}

    @media(max-width:1024px){{:root{{--sw:230px}}}}
    @media(max-width:768px){{
      .sidebar{{transform:translateX(-100%)}}.sidebar.open{{transform:translateX(0)}}
      .mwrap{{margin-left:0}}.hamburger{{display:flex}}
      .pc{{padding:16px 12px}}.abadge{{display:none}}
      .detail-tabs{{overflow-x:auto}}
      .talert span{{display:none}}
    }}
    @media(max-width:480px){{
      th,td{{padding:9px 10px;font-size:.82rem}}
      .stats-row{{grid-template-columns:1fr 1fr}}
      .detail-grid{{grid-template-columns:1fr}}
      .modal-box{{max-height:95vh}}
      .dg{{grid-template-columns:1fr 1fr}}
    }}
  </style>
</head>
<body>
<div class="overlay" id="overlay"></div>

<!-- ===== SIDEBAR ===== -->
<aside class="sidebar" id="sidebar">
  <div class="sbrand">
    <img src="./images/logo.jpg" alt="logo" onerror="this.style.display='none'">
    <span>Child Vaccination<small>Admin Panel</small></span>
  </div>
  <nav class="snav">
    <div class="ng" id="g1">
      <button class="ngt" onclick="tg('g1')">
        <i class="fa-solid fa-user-group ic"></i> Parents {nb(pending_parents)}
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a href="adminpendingparent.py"><i class="fa-solid fa-clock"></i> Pending {sb(pending_parents)}</a>
        <a href="adminapprovedparent.py"><i class="fa-solid fa-check"></i> Approved {nb(approved_parents,"gr")}</a>
        <a href="adminrejectedparent.py"><i class="fa-solid fa-xmark"></i> Rejected {nb(rejected_parents,"gy")}</a>
      </div>
    </div>
    <div class="ng" id="g2">
      <button class="ngt" onclick="tg('g2')">
        <i class="fa-solid fa-hospital ic"></i> Hospital {nb(pending_hospitals,"or")}
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a href="adminpendingmanager.py"><i class="fa-solid fa-clock"></i> Pending Manager {sb(pending_hospitals)}</a>
        <a href="adminapprovedmanager.py"><i class="fa-solid fa-check"></i> Approved Manager {nb(approved_hospitals,"gr")}</a>
        <a href="adminrejectedmanager.py"><i class="fa-solid fa-xmark"></i> Rejected Manager {nb(rejected_hospitals,"gy")}</a>
      </div>
    </div>
    <div class="ng" id="g3">
      <button class="ngt" onclick="tg('g3')">
        <i class="fa-solid fa-syringe ic"></i> Vaccinations
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a href="adminaddvaccine.py"><i class="fa-solid fa-plus"></i> Add Vaccine</a>
        <a href="adminviewvaccine.py"><i class="fa-solid fa-eye"></i> View Vaccine</a>
        <a href="admindeletedvaccine.py"><i class="fa-solid fa-trash"></i> Deleted Vaccine</a>
      </div>
    </div>
    <div class="ng open" id="g4">
      <button class="ngt" onclick="tg('g4')">
        <i class="fa-solid fa-bell ic"></i> Notification {nb(total_notified,"or")}
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a href="adminnotification.py" class="active"><i class="fa-solid fa-paper-plane"></i> Notify {sb(total_notified)}</a>
        <a href="adminnotifiedchild.py"><i class="fa-solid fa-child"></i> Notified Child</a>
        <a href="admincompletedvaccine.py"><i class="fa-solid fa-circle-check"></i> Completed {nb(total_completed,"gr")}</a>
      </div>
    </div>
    <div class="ng" id="g5">
      <button class="ngt" onclick="tg('g5')">
        <i class="fa-solid fa-children ic"></i> Children {nb(total_children,"gr")}
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a onclick="showSection('sec-children')" id="link-children">
          <i class="fa-solid fa-child"></i> Child Details {sb(total_children)}
        </a>
      </div>
    </div>
     <div class="ng" id="g6">
      <button class="ngt" onclick="tg('g6')">
        <i class="fa-solid fa-star ic"></i> Feedback
        {nb(low_fb) if low_fb else ""}
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a href="adminparentfeedback.py"><i class="fa-solid fa-list"></i> All Feedback {sb(total_fb)}</a>
        <a href="adminlowratings.py"><i class="fa-solid fa-triangle-exclamation"></i> Low Ratings {nb(low_fb) if low_fb else ""}</a>
      </div>
    </div>
  </nav>
  <div class="sfooter">
    <a href="home.py" class="btn-logout"><i class="fa-solid fa-right-from-bracket"></i> Logout</a>
  </div>
</aside>

<!-- ===== MAIN WRAP ===== -->
<div class="mwrap">
  <header class="topbar">
    <div class="tbl">
      <button class="hamburger" id="hamburger"><span></span><span></span><span></span></button>
      <div>
        <div class="ttitle" id="page-title">Notification Center</div>
        <div class="tbcrumb">
          <a href="admindashboard.py">Dashboard</a>
          <span>&rsaquo;</span>
          <span id="breadcrumb-sub">Notification &rsaquo; Notify</span>
        </div>
      </div>
    </div>
    <div class="tbr">
      {tp_alert}{th_alert}
      <span class="abadge"><i class="fa-solid fa-shield-halved"></i> Admin</span>
    </div>
  </header>

  <main class="pc">

    <!-- ===== SECTION: NOTIFICATION ===== -->
    <div class="section active" id="sec-notify">
      <div class="stats-row">
        <div class="stat-mini">
          <div class="stat-mini-icon blue"><i class="fa-solid fa-child"></i></div>
          <div class="stat-mini-info"><h4>{len(pending_children)}</h4><p>Pending Notify</p></div>
        </div>
        <div class="stat-mini">
          <div class="stat-mini-icon orange"><i class="fa-solid fa-bell"></i></div>
          <div class="stat-mini-info"><h4>{len(notified_children)}</h4><p>Already Notified</p></div>
        </div>
      </div>
""")

# ---- PENDING TABLE ----
print(f"""
      <div class="section-header">
        <div class="section-label">
          <div class="section-label-icon pending"><i class="fa-solid fa-clock"></i></div>
          <div><h3>Pending Children</h3><p>Children awaiting vaccination notification</p></div>
        </div>
      </div>
      <div class="table-card">
        <div class="table-card-header pending">
          <i class="fa-solid fa-clock"></i> Pending &mdash; {len(pending_children)} Children
        </div>
        <div class="tw"><table>
          <thead><tr>
            <th>#</th>
            <th><i class="fa-solid fa-child"></i> Child Name</th>
            <th><i class="fa-solid fa-calendar"></i> DOB</th>
            <th><i class="fa-solid fa-weight-scale"></i> Weight</th>
            <th>Status</th><th>Details</th><th>Action</th>
          </tr></thead>
          <tbody>
""")
if pending_children:
    for idx, child in enumerate(pending_children, start=1):
        cid   = child[0]
        cname = child[1]
        cdob  = child[2]
        print(f"""<tr>
          <td><span class="snum">{idx}</span></td>
          <td><strong>{cname}</strong></td>
          <td>{cdob}</td>
          <td>{child[3]} kg</td>
          <td><span class="badge-pending"><i class="fa-solid fa-clock"></i> Pending</span></td>
          <td><button class="btn-view" onclick="openModal('modal{cid}')"><i class="fa-solid fa-eye"></i> View</button></td>
          <td>
            <a href="adminnotification.py?notify_id={cid}" class="btn-notify"
               onclick="return confirm('Send vaccination notification for {cname}?')">
              <i class="fa-solid fa-paper-plane"></i> Notify
            </a>
          </td>
        </tr>""")
else:
    print('<tr class="empty-row"><td colspan="7"><i class="fa-solid fa-check-circle"></i> All children have been notified.</td></tr>')
print("</tbody></table></div></div>")

# ---- NOTIFIED TABLE ----
print(f"""
      <div class="section-header">
        <div class="section-label">
          <div class="section-label-icon notified"><i class="fa-solid fa-bell"></i></div>
          <div><h3>Notified Children</h3><p>Vaccination notifications already sent</p></div>
        </div>
      </div>
      <div class="table-card">
        <div class="table-card-header notified">
          <i class="fa-solid fa-bell"></i> Notified &mdash; {len(notified_children)} Children
        </div>
        <div class="tw"><table>
          <thead><tr>
            <th>#</th>
            <th><i class="fa-solid fa-child"></i> Child Name</th>
            <th><i class="fa-solid fa-calendar"></i> DOB</th>
            <th><i class="fa-solid fa-weight-scale"></i> Weight</th>
            <th>Status</th><th>Details</th><th>Note</th>
          </tr></thead>
          <tbody>
""")
if notified_children:
    for idx, child in enumerate(notified_children, start=1):
        cid   = child[0]
        cname = child[1]
        cdob  = child[2]
        print(f"""<tr>
          <td><span class="snum">{idx}</span></td>
          <td><strong>{cname}</strong></td>
          <td>{cdob}</td>
          <td>{child[3]} kg</td>
          <td><span class="badge-notified"><i class="fa-solid fa-bell"></i> Notified</span></td>
          <td><button class="btn-view" onclick="openModal('modal{cid}')"><i class="fa-solid fa-eye"></i> View</button></td>
          <td><span class="already-notified"><i class="fa-solid fa-circle-check"></i> Already Notified</span></td>
        </tr>""")
else:
    print('<tr class="empty-row"><td colspan="7"><i class="fa-solid fa-info-circle"></i> No notified children yet.</td></tr>')
print("</tbody></table></div></div>")
print("</div><!-- /sec-notify -->")


# ===== SECTION: CHILDREN DETAILS =====
print(f"""
    <div class="section" id="sec-children">
      <div class="page-hdr">
        <div>
          <h2><i class="fa-solid fa-children"></i>&nbsp; Registered Children</h2>
          <p>Click <strong>View More</strong> on any child to see parent, vaccine &amp; hospital details</p>
        </div>
        <span class="page-hdr-badge"><i class="fa-solid fa-child"></i> {total_children} Total</span>
      </div>
      <div class="toolbar">
        <div class="sbox">
          <i class="fa-solid fa-magnifying-glass"></i>
          <input type="text" id="childSearch" placeholder="Search child name, father, mobile, blood group..." oninput="filterCards()">
        </div>
        <select class="fsel" id="genderFilter" onchange="filterCards()">
          <option value="">All Genders</option>
          <option value="male">Male</option>
          <option value="female">Female</option>
        </select>
        <select class="fsel" id="vacFilter" onchange="filterCards()">
          <option value="">All Vaccine Status</option>
          <option value="taken">Has Taken</option>
          <option value="notified">Notified</option>
          <option value="pending">Pending</option>
        </select>
        <span class="cnt-lbl" id="cntLbl">{len(children)} records</span>
      </div>
""")

if not children:
    print('<div class="empty"><i class="fa-solid fa-child-reaching"></i><p>No registered children found.</p></div>')
else:
    for r in children:
        cid      = r[0]
        cname    = r[1]  or "&mdash;"
        dob      = r[2]  or "&mdash;"
        weight   = r[3]  or "&mdash;"
        gender   = r[4]  or "&mdash;"
        blood    = r[5]  or "&mdash;"
        idmark   = r[6]  or "&mdash;"
        father   = r[7]  or "&mdash;"
        # r[8]=father_age, r[9]=mother_name, r[10]=mother_age, r[11]=mother_weight
        mother   = r[9]  or "&mdash;"
        email    = r[12] or "&mdash;"
        mobile   = r[13] or "&mdash;"
        occ      = r[14] or "&mdash;"
        state    = r[15] or "&mdash;"
        district = r[16] or "&mdash;"
        address  = r[17] or "&mdash;"
        pstatus  = r[21] or "pending"

        pbc      = {"approved":"ba","rejected":"br","pending":"bp"}.get(pstatus,"bp")
        gicon    = "fa-mars" if str(r[4]).lower()=="male" else ("fa-venus" if str(r[4]).lower()=="female" else "fa-genderless")
        initial  = str(r[1])[0].upper() if r[1] else "?"

        vaccines   = vax_by_child.get(cid, [])
        v_total    = len(vaccines)
        v_taken    = sum(1 for v in vaccines if v["status"]=="taken")
        v_notified = sum(1 for v in vaccines if v["status"]=="notified")
        v_pending  = v_total - v_taken - v_notified
        vac_statuses = " ".join(set(v["status"] or "pending" for v in vaccines)) if vaccines else "pending"

        h    = hosp_by_child.get(cid, {})
        hn   = h.get("name",     "Not assigned yet")
        hnum = h.get("number",   "&mdash;")
        hst  = h.get("state",    "&mdash;")
        hdi  = h.get("district", "&mdash;")

        vrows = ""
        for idx, v in enumerate(vaccines, 1):
            vs = v["status"] or "pending"
            vd = v["date"]   or "&mdash;"
            bc = "bt" if vs=="taken" else ("bn" if vs=="notified" else "bp")
            vrows += (f"<tr><td>{idx}</td><td><strong>{v['name']}</strong></td>"
                      f"<td>{v['age']} mo.</td><td>{vd}</td>"
                      f"<td><span class='bx {bc}'>{vs.capitalize()}</span></td></tr>")
        if not vrows:
            vrows = "<tr><td colspan='5' style='text-align:center;color:#bbb;padding:14px'>No vaccines assigned yet</td></tr>"

        print(f"""
      <div class="child-card"
           data-name="{str(r[1]).lower()}"
           data-father="{str(r[7] or '').lower()}"
           data-mobile="{mobile}"
           data-blood="{str(r[5] or '').lower()}"
           data-gender="{str(r[4] or '').lower()}"
           data-vacstatus="{vac_statuses}">
        <div class="ccard-top">
          <div class="ccard-left">
            <div class="avatar">{initial}</div>
            <div>
              <div class="ccard-name">
                <i class="fa-solid {gicon}" style="font-size:.85rem;opacity:.7"></i>&nbsp;{cname}
              </div>
              <div class="ccard-sub">
                DOB: {dob} &bull; Blood: {blood} &bull; {weight} kg &bull; {gender}
              </div>
            </div>
          </div>
          <div class="ccard-right">
            <span class="bx bgy"><i class="fa-solid fa-syringe"></i>&nbsp; {v_total} Vaccines</span>
            <span class="bx {pbc}">Parent: {pstatus.capitalize()}</span>
            <button class="btn-viewmore" onclick="toggleDetails(this, 'cdet{cid}')">
              <i class="fa-solid fa-chevron-down vm-icon"></i> View More
            </button>
          </div>
        </div>
        <div class="ccard-details" id="cdet{cid}">
          <div class="detail-tabs" id="ctabs{cid}">
            <button class="dtab active" onclick="switchDTab({cid},'parent')">
              <i class="fa-solid fa-users"></i> Parent
            </button>
            <button class="dtab" onclick="switchDTab({cid},'vaccine')">
              <i class="fa-solid fa-syringe"></i> Vaccine
            </button>
            <button class="dtab" onclick="switchDTab({cid},'hospital')">
              <i class="fa-solid fa-hospital"></i> Hospital
            </button>
          </div>
          <div class="dpanel active" id="cdp{cid}-parent">
            <div class="dg">
              <div class="di"><label>Father Name</label><span>{father}</span></div>
              <div class="di"><label>Mother Name</label><span>{mother}</span></div>
              <div class="di"><label>Mobile</label><span>{mobile}</span></div>
              <div class="di"><label>Email</label><span>{email}</span></div>
              <div class="di"><label>Occupation</label><span>{occ}</span></div>
              <div class="di"><label>State</label><span>{state}</span></div>
              <div class="di"><label>District</label><span>{district}</span></div>
              <div class="di"><label>Parent Status</label><span><span class="bx {pbc}">{pstatus.capitalize()}</span></span></div>
              <div class="di full"><label>Address</label><span>{address}</span></div>
            </div>
          </div>
          <div class="dpanel" id="cdp{cid}-vaccine">
            <div class="vsumbadges">
              <span class="vsb tk"><i class="fa-solid fa-check-circle"></i> {v_taken} Taken</span>
              <span class="vsb nt"><i class="fa-solid fa-bell"></i> {v_notified} Notified</span>
              <span class="vsb pd"><i class="fa-solid fa-clock"></i> {v_pending} Pending</span>
            </div>
            <div style="overflow-x:auto;border:1px solid var(--bo);border-radius:8px">
              <table class="vtable">
                <thead><tr><th>#</th><th>Vaccine Name</th><th>Due Age</th><th>Date Taken</th><th>Status</th></tr></thead>
                <tbody>{vrows}</tbody>
              </table>
            </div>
          </div>
          <div class="dpanel" id="cdp{cid}-hospital">
            <div class="dg">
              <div class="di"><label>Hospital Name</label><span>{hn}</span></div>
              <div class="di"><label>Contact Number</label><span>{hnum}</span></div>
              <div class="di"><label>State</label><span>{hst}</span></div>
              <div class="di"><label>District</label><span>{hdi}</span></div>
            </div>
          </div>
        </div>
      </div>
""")

print("""
    </div><!-- /sec-children -->

  </main>
  <footer>&copy; 2026 Child Vaccination System &mdash; Admin Panel</footer>
</div><!-- /mwrap -->
""")


# ---- MODALS (for notification view) ----
for child in children:
    child_id  = child[0]
    child_dob = child[2]

    cur.execute("""
        SELECT vaccine_id, vaccine_name, minimum_age, dose_number
        FROM vaccine
        WHERE LOWER(TRIM(status)) = 'confirmed'
        ORDER BY COALESCE(minimum_age, 0) ASC, COALESCE(dose_number, 1) ASC
        LIMIT 10
    """)
    vaccines = cur.fetchall()

    vac_rows = ""
    for vac in vaccines:
        vaccine_id, vaccine_name, minimum_age, dose_number = vac
        dose_number = dose_number if dose_number else "1"

        try:
            min_age_val    = int(minimum_age) if minimum_age is not None else 0
            scheduled_date = add_months(child_dob, min_age_val)
        except Exception:
            scheduled_date = child_dob

        cur.execute("""
            SELECT cv.appointment_date, cv.taken_date, cv.status, cv.dose_number,
                   h.hospital_name
            FROM child_vaccine cv
            LEFT JOIN hospital h ON cv.hospital_id = h.hospital_id
            WHERE cv.child_id  = %s AND cv.vaccine_id = %s
            LIMIT 1
        """, (child_id, vaccine_id))
        record = cur.fetchone()

        if record:
            appt_date    = record[0]
            taken_date   = record[1]
            v_status     = str(record[2]).strip().lower() if record[2] else "pending"
            rec_dose     = record[3] if record[3] else dose_number
            hosp_display = record[4] if record[4] else "Not Assigned"
            display_date = taken_date if taken_date else (appt_date if appt_date else scheduled_date)

            if v_status == 'completed':
                badge_cls = "vac-badge-done";        label = "Completed"
            elif v_status == 'confirmed':
                badge_cls = "vac-badge-confirmed";   label = "Confirmed"
            elif v_status == 'notified':
                badge_cls = "vac-badge-notified";    label = "Notified"
            elif v_status == 'rescheduled':
                badge_cls = "vac-badge-rescheduled"; label = "Rescheduled"
            else:
                badge_cls = "vac-badge-pending";     label = v_status.capitalize()
        else:
            display_date = scheduled_date
            rec_dose     = dose_number
            hosp_display = "Not yet assigned"
            label        = "Not Notified"
            badge_cls    = "vac-badge-pending"

        vac_rows += (
            f"<tr>"
            f"<td>{vaccine_name}</td>"
            f"<td><b>Dose {rec_dose}</b></td>"
            f"<td>{display_date}</td>"
            f"<td>{hosp_display}</td>"
            f"<td><span class='{badge_cls}'>{label}</span></td>"
            f"</tr>"
        )

    print(f"""
<div class="modal-overlay" id="modal{child_id}">
  <div class="modal-box">
    <div class="modal-head">
      <h4><i class="fa-solid fa-child"></i> {child[1]} &mdash; Full Details</h4>
      <button class="modal-close" onclick="closeModal('modal{child_id}')">&#x2715;</button>
    </div>
    <div class="modal-body">
      <div class="modal-section-title"><i class="fa-solid fa-child"></i> Child Information</div>
      <div class="detail-grid">
        <div class="detail-item"><label>Full Name</label><span>{child[1]}</span></div>
        <div class="detail-item"><label>Date of Birth</label><span>{child[2]}</span></div>
        <div class="detail-item"><label>Weight</label><span>{child[3]} kg</span></div>
        <div class="detail-item"><label>Gender</label><span>{child[4]}</span></div>
        <div class="detail-item"><label>Blood Group</label><span>{child[5]}</span></div>
        <div class="detail-item"><label>Identification Mark</label><span>{child[6]}</span></div>
      </div>
      <div class="modal-section-title"><i class="fa-solid fa-users"></i> Parent Information</div>
      <div class="detail-grid">
        <div class="detail-item"><label>Father Name</label><span>{child[7]}</span></div>
        <div class="detail-item"><label>Father Age</label><span>{child[8]}</span></div>
        <div class="detail-item"><label>Mother Name</label><span>{child[9]}</span></div>
        <div class="detail-item"><label>Mother Age</label><span>{child[10]}</span></div>
        <div class="detail-item"><label>Mother Weight</label><span>{child[11]} kg</span></div>
        <div class="detail-item"><label>Email</label><span>{child[12]}</span></div>
        <div class="detail-item"><label>Mobile</label><span>{child[13]}</span></div>
        <div class="detail-item"><label>Occupation</label><span>{child[14]}</span></div>
        <div class="detail-item"><label>State</label><span>{child[15]}</span></div>
        <div class="detail-item"><label>District</label><span>{child[16]}</span></div>
        <div class="detail-item"><label>Address</label><span>{child[17]}</span></div>
        <div class="detail-item"><label>Pincode</label><span>{child[18]}</span></div>
      </div>
      <div class="modal-section-title"><i class="fa-solid fa-image"></i> Documents</div>
      <div class="img-row">
        <div class="img-item">
          <img src="./images/{child[19]}" class="modal-img" alt="Aadhar" onerror="this.src='images/noimage.png'">
          <p>Father Aadhar</p>
        </div>
        <div class="img-item">
          <img src="./images/{child[20]}" class="modal-img" alt="Profile" onerror="this.src='images/noimage.png'">
          <p>Parent Profile</p>
        </div>
      </div>
      <div class="modal-section-title"><i class="fa-solid fa-syringe"></i> Vaccine Schedule</div>
      <div style="overflow-x:auto;">
        <table class="vac-table">
          <thead>
            <tr>
              <th>Vaccine</th><th>Dose</th><th>Appointment Date</th>
              <th>Hospital</th><th>Status</th>
            </tr>
          </thead>
          <tbody>{vac_rows}</tbody>
        </table>
      </div>
    </div>
  </div>
</div>""")

print("""
<script>
// ===== SIDEBAR =====
const hamburger = document.getElementById('hamburger');
const sidebar   = document.getElementById('sidebar');
const overlay   = document.getElementById('overlay');

function closeSB() {
  sidebar.classList.remove('open');
  hamburger.classList.remove('open');
  overlay.classList.remove('active');
  document.body.style.overflow = '';
}
hamburger.addEventListener('click', () => {
  const o = sidebar.classList.toggle('open');
  hamburger.classList.toggle('open', o);
  overlay.classList.toggle('active', o);
  document.body.style.overflow = o ? 'hidden' : '';
});
overlay.addEventListener('click', closeSB);
window.addEventListener('resize', () => { if (window.innerWidth > 768) closeSB(); });

function tg(id) {
  const g = document.getElementById(id);
  const o = g.classList.contains('open');
  document.querySelectorAll('.ng').forEach(x => x.classList.remove('open'));
  if (!o) g.classList.add('open');
}

// ===== SECTION SWITCHING =====
function showSection(id) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');

  const titles = {
    'sec-notify':   'Notification Center',
    'sec-children': 'Child Details'
  };
  const breadcrumbs = {
    'sec-notify':   'Notification &rsaquo; Notify',
    'sec-children': 'Children &rsaquo; Child Details'
  };
  document.getElementById('page-title').textContent = titles[id] || 'Notification Center';
  document.getElementById('breadcrumb-sub').innerHTML = breadcrumbs[id] || '';

  document.querySelectorAll('.nsub a').forEach(a => a.classList.remove('active'));
  if (id === 'sec-children') {
    document.getElementById('link-children').classList.add('active');
    document.querySelectorAll('.ng').forEach(x => x.classList.remove('open'));
    document.getElementById('g5').classList.add('open');
  }
  window.scrollTo(0, 0);
  closeSB();
}

// ===== NOTIFICATION MODALS =====
function openModal(id)  { document.getElementById(id).classList.add('active');    document.body.style.overflow = 'hidden'; }
function closeModal(id) { document.getElementById(id).classList.remove('active'); document.body.style.overflow = ''; }

document.querySelectorAll('.modal-overlay').forEach(m => {
  m.addEventListener('click', function(e) { if (e.target === this) closeModal(this.id); });
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape')
    document.querySelectorAll('.modal-overlay.active').forEach(m => closeModal(m.id));
});

// ===== CHILD CARD EXPAND / TABS =====
function toggleDetails(btn, detId) {
  const det    = document.getElementById(detId);
  const isOpen = det.classList.contains('open');
  det.classList.toggle('open', !isOpen);
  btn.classList.toggle('open', !isOpen);
  btn.innerHTML = isOpen
    ? '<i class="fa-solid fa-chevron-down vm-icon"></i> View More'
    : '<i class="fa-solid fa-chevron-up vm-icon open"></i> View Less';
}

function switchDTab(cid, tabName) {
  const panels = ['parent', 'vaccine', 'hospital'];
  const btns   = document.getElementById('ctabs' + cid).querySelectorAll('.dtab');
  panels.forEach((p, i) => {
    const el = document.getElementById('cdp' + cid + '-' + p);
    if (el) el.classList.toggle('active', p === tabName);
    if (btns[i]) btns[i].classList.toggle('active', p === tabName);
  });
}

// ===== SEARCH / FILTER CHILDREN =====
function filterCards() {
  const q  = document.getElementById('childSearch').value.toLowerCase();
  const gf = document.getElementById('genderFilter').value.toLowerCase();
  const vf = document.getElementById('vacFilter').value.toLowerCase();
  const cards = document.querySelectorAll('.child-card');
  let visible = 0;
  cards.forEach(c => {
    const matchQ = !q  || c.dataset.name.includes(q) || c.dataset.father.includes(q)
                       || c.dataset.mobile.includes(q) || c.dataset.blood.includes(q);
    const matchG = !gf || c.dataset.gender === gf;
    const matchV = !vf || (c.dataset.vacstatus || '').includes(vf);
    const show   = matchQ && matchG && matchV;
    c.style.display = show ? '' : 'none';
    if (show) visible++;
  });
  document.getElementById('cntLbl').textContent = visible + ' record' + (visible !== 1 ? 's' : '');
}
</script>
</body></html>
""")

con.close()