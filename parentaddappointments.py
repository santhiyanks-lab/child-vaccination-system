#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
print("Content-Type: text/html\r\n\r\n")

import cgi
import cgitb
import pymysql
import sys
import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

cgitb.enable()
sys.stdout.reconfigure(encoding='utf-8')

try:
    con = pymysql.connect(host="localhost", user="root", password="", database="child", autocommit=False)
    cur = con.cursor()
except Exception as e:
    print(f"<h3>Database Connection Error: {e}</h3>"); exit()

form      = cgi.FieldStorage()
hid       = form.getfirst("parent_id")
if not hid or not hid.strip().isdigit():
    print("<script>alert('Invalid Access');location.href='home.py';</script>"); exit()
parent_id = int(hid)

cur.execute("SELECT * FROM parent WHERE parent_id=%s", (parent_id,))
if not cur.fetchone():
    print("<h3>Parent Not Found!</h3>"); exit()

# ── Hospitals ──
cur.execute("SELECT hospital_id, hospital_name, state, district FROM hospital ORDER BY state, district, hospital_name")
hospital_data = {}
for hid_val, hname, hstate, hdistrict in cur.fetchall():
    hospital_data.setdefault(hstate, {}).setdefault(hdistrict, []).append({"id": hid_val, "name": hname})
hospital_json_str = json.dumps(hospital_data)
all_states = sorted(hospital_data.keys())

cur.execute("SELECT child_id, child_name, dob FROM children WHERE parent_id=%s", (parent_id,))
children = cur.fetchall()

def safe_int(val):
    try: return int(val)
    except: return 0

def to_date(val):
    if val is None: return None
    if isinstance(val, str):
        try: return datetime.strptime(val, "%Y-%m-%d").date()
        except: return None
    if hasattr(val, 'year'): return val
    return None

IAP_SLOT_DAYS = {1:0,2:42,3:70,4:98,5:180,6:180,7:270,8:365,9:455,10:487}
AGE_LABELS    = {1:"Birth",2:"6 Weeks",3:"10 Weeks",4:"14 Weeks",5:"6 Months",
                 6:"6 Months",7:"9 Months",8:"12 Months",9:"15 Months",10:"16-18 Months"}

# ── Build grouped visits per child ──
visits_by_child = {}
for child in children:
    child_id, child_name, dob = child[0], child[1], child[2]
    dob_date = to_date(dob)

    cur.execute("""
        SELECT cv.vaccine_id, v.vaccine_name, v.dose_number,
               v.due_days, v.interval_days,
               cv.status, cv.appointment_date, cv.appointment_time
        FROM child_vaccine cv
        JOIN vaccine v ON cv.vaccine_id = v.vaccine_id
        WHERE cv.child_id = %s
        ORDER BY CAST(v.dose_number AS UNSIGNED)
    """, (child_id,))
    rows = cur.fetchall()

    enriched = []
    prev_ref_date = None
    for row in rows:
        vid, vname, dose_num, due_days, interval_days, status, appt_date_val, appt_time_val = row
        visit_num = safe_int(dose_num)
        due_date  = None
        if dob_date:
            iap = IAP_SLOT_DAYS.get(visit_num)
            if iap is not None:
                due_date = dob_date + timedelta(days=iap)
            elif visit_num == 1:
                due_date = dob_date + timedelta(days=(int(due_days) if due_days else 0))
            elif prev_ref_date and interval_days:
                due_date = prev_ref_date + timedelta(days=int(interval_days))
        appt_date_obj = to_date(appt_date_val)
        prev_ref_date = appt_date_obj or due_date or prev_ref_date
        enriched.append({"vid":vid,"vname":vname,"visit_num":visit_num,
                         "due_date":due_date,"status":status or "pending",
                         "appt_date":appt_date_obj,
                         "appt_time":str(appt_time_val) if appt_time_val else "",
                         "child_id":child_id})

    slot_groups = {}; slot_order = []
    for e in enriched:
        sk = e["due_date"].strftime("%Y-%m-%d") if e["due_date"] else f"unk_{e['visit_num']}"
        if sk not in slot_groups:
            slot_groups[sk] = []; slot_order.append(sk)
        slot_groups[sk].append(e)

    visit_cards = []
    first_bookable_found = False
    today_d = datetime.today().date()

    for sk in slot_order:
        group         = slot_groups[sk]
        visit_nums    = [g["visit_num"] for g in group]
        vaccine_names = ", ".join(g["vname"] for g in group)
        age_label     = AGE_LABELS.get(min(visit_nums), f"Visit {min(visit_nums)}")
        due_date      = group[0]["due_date"]
        due_date_str  = due_date.strftime("%Y-%m-%d") if due_date else ""
        all_completed = all(g["status"] == "completed" for g in group)
        any_booked    = any(g["appt_date"] is not None for g in group)
        all_pending   = all(g["status"] not in ("completed",) and g["appt_date"] is None for g in group)
        combined_val  = ",".join(f"{child_id}-{g['vid']}" for g in group)
        is_past_due   = (due_date is not None and due_date < today_d)

        if all_completed:
            locked = True;  lock_reason = "completed"
        elif any_booked:
            locked = True;  lock_reason = "booked"
            first_bookable_found = True
        elif not first_bookable_found and all_pending:
            locked = False; lock_reason = ""
            first_bookable_found = True
        else:
            locked = True;  lock_reason = "prev_pending"

        visit_cards.append({
            "value":         combined_val,
            "visit_nums":    visit_nums,
            "age_label":     age_label,
            "vaccine_names": vaccine_names,
            "due_date":      due_date_str,
            "status":        "completed" if all_completed else ("booked" if any_booked else "pending"),
            "locked":        locked,
            "lock_reason":   lock_reason,
            "is_combined":   len(group) > 1,
            "count":         len(group),
            "is_past_due":   is_past_due,
        })

    visits_by_child[child_id] = visit_cards

visits_json_str = json.dumps(visits_by_child)

# ── POST: Mark Already Done ──
if os.environ.get("REQUEST_METHOD") == "POST" and form.getfirst("mark_already_done"):
    selection        = form.getfirst("child_vaccine_done")
    hospital_id      = form.getfirst("already_done_hospital_id")
    already_done_date = form.getfirst("already_done_date")
    already_done_time = form.getfirst("already_done_time")

    if not selection:
        print("<script>alert('No vaccine selected.');window.history.back();</script>"); exit()
    if not hospital_id or not str(hospital_id).strip().isdigit():
        print("<script>alert('Please select a hospital before marking as already given.');window.history.back();</script>"); exit()
    if not already_done_date:
        print("<script>alert('Please enter the date the vaccine was given.');window.history.back();</script>"); exit()
    if not already_done_time:
        print("<script>alert('Please enter the time the vaccine was given.');window.history.back();</script>"); exit()

    hospital_id_val  = int(hospital_id)
    done_date        = to_date(already_done_date) or datetime.today().date()
    done_time        = already_done_time  # stored as string e.g. "10:30"

    try:
        for pair in [p.strip() for p in selection.split(",")]:
            cid_val, vaccine_id = map(int, pair.split("-"))

            # 1. Update child_vaccine status to completed
            cur.execute("""
                UPDATE child_vaccine
                SET status='completed',
                    taken_date=%s,
                    hospital_id=%s,
                    appointment_date=%s,
                    appointment_time=%s
                WHERE child_id=%s AND vaccine_id=%s
            """, (done_date, hospital_id_val, done_date, done_time, cid_val, vaccine_id))

            # 2. Check if appointment record already exists
            cur.execute("""
                SELECT appo_id FROM appointment
                WHERE child_id=%s AND vaccine_id=%s AND parent_id=%s
            """, (cid_val, vaccine_id, parent_id))
            existing = cur.fetchone()

            if existing:
                # Update existing appointment to completed
                cur.execute("""
                    UPDATE appointment
                    SET status='completed',
                        hospital_id=%s,
                        appointment_date=%s,
                        appointment_time=%s
                    WHERE child_id=%s AND vaccine_id=%s AND parent_id=%s
                """, (hospital_id_val, done_date, done_time, cid_val, vaccine_id, parent_id))
            else:
                # Insert new appointment record so hospital can see it
                cur.execute("""
                    INSERT INTO appointment
                    (child_id, vaccine_id, parent_id, hospital_id,
                     appointment_date, appointment_time, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'completed')
                """, (cid_val, vaccine_id, parent_id, hospital_id_val, done_date, done_time))

        con.commit()
        print(f"<script>alert('Marked as already given!\\nThe next dose is now unlocked for booking.');window.location.href='parentaddappointments.py?parent_id={parent_id}';</script>")
        exit()
    except Exception as e:
        con.rollback()
        print(f"<h3>Error marking as done: {e}</h3>"); exit()

# ── POST: Book Appointment ──
if os.environ.get("REQUEST_METHOD") == "POST" and form.getfirst("book_appointment"):
    selection        = form.getfirst("child_vaccine")
    hospital_id      = form.getfirst("hospital_id")
    appointment_date = form.getfirst("appointment_date")
    appointment_time = form.getfirst("appointment_time")

    if not selection or not hospital_id or not appointment_date or not appointment_time:
        print("<script>alert('All fields are required!');window.history.back();</script>")
    else:
        try:
            hospital_id_val    = int(hospital_id)
            pairs              = [p.strip() for p in selection.split(",")]
            child_id_for_email = None
            vaccine_ids_booked = []
            for pair in pairs:
                cid_val, vaccine_id = map(int, pair.split("-"))
                if child_id_for_email is None: child_id_for_email = cid_val
                vaccine_ids_booked.append(vaccine_id)
                cur.execute("""
                    UPDATE child_vaccine
                    SET hospital_id=%s, appointment_date=%s, appointment_time=%s, status='pending'
                    WHERE child_id=%s AND vaccine_id=%s
                """, (hospital_id_val, appointment_date, appointment_time, cid_val, vaccine_id))

                # Also insert into appointment table so hospital can see it
                cur.execute("""
                    SELECT appo_id FROM appointment
                    WHERE child_id=%s AND vaccine_id=%s AND parent_id=%s
                """, (cid_val, vaccine_id, parent_id))
                existing = cur.fetchone()
                if existing:
                    cur.execute("""
                        UPDATE appointment
                        SET hospital_id=%s, appointment_date=%s,
                            appointment_time=%s, status='Booked'
                        WHERE child_id=%s AND vaccine_id=%s AND parent_id=%s
                    """, (hospital_id_val, appointment_date, appointment_time, cid_val, vaccine_id, parent_id))
                else:
                    cur.execute("""
                        INSERT INTO appointment
                        (child_id, vaccine_id, parent_id, hospital_id,
                         appointment_date, appointment_time, status)
                        VALUES (%s, %s, %s, %s, %s, %s, 'Booked')
                    """, (cid_val, vaccine_id, parent_id, hospital_id_val, appointment_date, appointment_time))

            con.commit()

            cur.execute("""
                SELECT p.father_name, p.mobile_number, c.child_name
                FROM parent p JOIN children c ON c.parent_id=p.parent_id
                WHERE p.parent_id=%s AND c.child_id=%s
            """, (parent_id, child_id_for_email))
            email_info = cur.fetchone()

            if vaccine_ids_booked:
                fmt2 = ",".join(["%s"]*len(vaccine_ids_booked))
                cur.execute(f"SELECT vaccine_name FROM vaccine WHERE vaccine_id IN ({fmt2})", tuple(vaccine_ids_booked))
                vax_names_str = ", ".join(r[0] for r in cur.fetchall())
            else:
                vax_names_str = "-"

            cur.execute("SELECT hospital_name, owner_email FROM hospital WHERE hospital_id=%s",(hospital_id_val,))
            hospital_info = cur.fetchone()

            if email_info and hospital_info:
                try:
                    SENDER_EMAIL = "santhiyanks@gmail.com"; SENDER_PASSWORD = "snnr avxt cqgb ocwy"
                    body = f"""<html><body style="font-family:Arial,sans-serif;padding:20px;background:#f4f6f9">
<div style="max-width:580px;margin:auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,.1)">
  <div style="background:#0d6efd;padding:20px 28px"><h2 style="color:#fff;margin:0">New Vaccination Appointment</h2></div>
  <div style="padding:24px 28px">
    <p>Dear <b>{hospital_info[0]}</b>,</p>
    <table style="width:100%;font-size:14px;border-collapse:collapse">
      <tr><td style="padding:5px 0;font-weight:700;width:150px">Parent</td><td>: {email_info[0]}</td></tr>
      <tr><td style="padding:5px 0;font-weight:700">Phone</td><td>: {email_info[1]}</td></tr>
      <tr><td style="padding:5px 0;font-weight:700">Child</td><td>: {email_info[2]}</td></tr>
      <tr><td style="padding:5px 0;font-weight:700">Vaccines</td><td>: {vax_names_str}</td></tr>
      <tr><td style="padding:5px 0;font-weight:700">Date</td><td>: {appointment_date}</td></tr>
      <tr><td style="padding:5px 0;font-weight:700">Time</td><td>: {appointment_time}</td></tr>
    </table>
  </div>
  <div style="background:#f8f9fa;padding:12px 28px;text-align:center"><p style="color:#aaa;font-size:12px;margin:0">Child Vaccination System</p></div>
</div></body></html>"""
                    msg = MIMEMultipart("alternative"); msg["Subject"] = f"Appointment - {email_info[2]}"
                    msg["From"] = SENDER_EMAIL; msg["To"] = hospital_info[1]
                    msg.attach(MIMEText(body,"html"))
                    with smtplib.SMTP_SSL("smtp.gmail.com",465) as s:
                        s.login(SENDER_EMAIL,SENDER_PASSWORD); s.sendmail(SENDER_EMAIL,hospital_info[1],msg.as_string())
                except: pass

            print(f"<script>alert('Appointment Booked Successfully!');window.location.href='parentaddappointments.py?parent_id={parent_id}';</script>")
            exit()
        except Exception as e:
            con.rollback(); print(f"<h3>Error: {e}</h3>"); exit()

# ─────────────────────────────────────────────────────────────
#  HTML
# ─────────────────────────────────────────────────────────────
print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Book Appointment</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
/* ── Reset & base ── */
:root{{--sw:260px;--th:60px;--pr:#1565c0;--bg:#f0f4f8}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',sans-serif;background:var(--bg);color:#1e293b}}

/* ── Topbar ── */
.topbar{{position:fixed;top:0;left:0;right:0;height:var(--th);background:#0d1b2a;
  display:flex;align-items:center;justify-content:space-between;padding:0 16px;
  z-index:1100;box-shadow:0 2px 10px rgba(0,0,0,.3)}}
.topbar-left{{display:flex;align-items:center;gap:12px}}
.topbar img{{height:40px;width:40px;border-radius:50%;border:2px solid rgba(255,255,255,.4);object-fit:cover}}
.brand{{color:#fff;font-size:1rem;font-weight:700}}
.hamburger{{background:none;border:none;color:#fff;font-size:1.4rem;cursor:pointer;
  padding:4px 8px;border-radius:6px;display:none}}
.topbar-right a{{color:#cfd8dc;text-decoration:none;font-size:.85rem;padding:6px 14px;
  border:1px solid #37474f;border-radius:6px;transition:all .2s}}
.topbar-right a:hover{{background:#e53935;border-color:#e53935;color:#fff}}

/* ── Sidebar ── */
.sidebar{{position:fixed;top:var(--th);left:0;width:var(--sw);
  height:calc(100vh - var(--th));background:#0d1b2a;overflow-y:auto;
  z-index:1000;transition:transform .3s;padding:16px 12px 24px;
  scrollbar-width:thin;scrollbar-color:#1e3a5f transparent}}
.sidebar-label{{color:#546e7a;font-size:.68rem;font-weight:700;
  letter-spacing:1.5px;text-transform:uppercase;padding:12px 8px 4px}}
.sidebar .nav-link{{color:#b0bec5;border-radius:8px;padding:9px 12px;font-size:.87rem;
  display:flex;align-items:center;gap:10px;text-decoration:none;transition:all .2s;margin-bottom:2px}}
.sidebar .nav-link:hover,.sidebar .nav-link.active{{background:var(--pr);color:#fff}}
.sidebar-group summary{{list-style:none;color:#b0bec5;padding:9px 12px;border-radius:8px;
  display:flex;align-items:center;gap:10px;cursor:pointer;font-size:.87rem;
  transition:background .2s;margin-bottom:2px;user-select:none}}
.sidebar-group summary::-webkit-details-marker{{display:none}}
.sidebar-group summary:hover{{background:#1c2d3e;color:#fff}}
.sidebar-group summary .caret{{margin-left:auto;transition:transform .25s;font-size:.75rem}}
.sidebar-group[open] summary .caret{{transform:rotate(90deg)}}
.sidebar-group[open] summary{{color:#fff;background:#1c2d3e}}
.sub-links{{padding:4px 0 4px 28px}}
.sub-links a{{display:flex;align-items:center;gap:8px;color:#78909c;font-size:.83rem;
  padding:7px 10px;border-radius:6px;text-decoration:none;transition:all .2s;margin-bottom:1px}}
.sub-links a:hover{{color:#fff;background:rgba(255,255,255,.07)}}
.sidebar-divider{{border:none;border-top:1px solid #1c2d3e;margin:10px 0}}
.sidebar-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:999}}

/* ── Main layout ── */
.main{{margin-left:var(--sw);margin-top:var(--th);padding:28px 24px;
  min-height:calc(100vh - var(--th))}}

/* ── Page header ── */
.page-hdr{{display:flex;align-items:center;gap:14px;margin-bottom:28px}}
.phdr-icon{{background:linear-gradient(135deg,#1565c0,#42a5f5);color:#fff;
  width:48px;height:48px;border-radius:12px;display:flex;align-items:center;
  justify-content:center;font-size:1.2rem;flex-shrink:0}}

/* ── Step card ── */
.step-card{{background:#fff;border-radius:14px;box-shadow:0 2px 12px rgba(0,0,0,.07);
  padding:24px 28px;margin-bottom:20px;border:1.5px solid #e2e8f0}}
.step-card.active-card{{border-color:#1565c0;box-shadow:0 4px 20px rgba(21,101,192,.12)}}
.step-card.done-card{{border-color:#a5d6a7;background:#f9fffe}}
.step-card.pastdue-card{{border-color:#f97316;background:#fffbf5}}
.step-card.disabled-card{{opacity:.5;pointer-events:none}}

/* Step header */
.step-hdr{{display:flex;align-items:center;gap:12px;margin-bottom:16px}}
.step-num{{width:32px;height:32px;border-radius:50%;background:#1565c0;color:#fff;
  display:flex;align-items:center;justify-content:center;font-size:.85rem;
  font-weight:800;flex-shrink:0}}
.step-num.done{{background:#16a34a}}
.step-num.orange{{background:#f97316}}
.step-title{{font-size:1rem;font-weight:700;color:#1e293b}}
.step-subtitle{{font-size:.8rem;color:#64748b;margin-top:1px}}

/* ── Visit list ── */
.vaccine-list{{display:flex;flex-direction:column;gap:8px}}
.visit-row{{display:flex;align-items:stretch;border:1.5px solid #e2e8f0;
  border-radius:10px;overflow:hidden;transition:all .2s;background:#fff;min-height:68px}}
.visit-row.clickable{{cursor:pointer}}
.visit-row.clickable:hover{{border-color:#1565c0;box-shadow:0 2px 8px rgba(21,101,192,.15)}}
.visit-row.v-selected{{border-color:#1565c0;background:#f0f7ff;
  box-shadow:0 0 0 3px rgba(21,101,192,.15)}}
.visit-row.v-locked{{opacity:.5;cursor:not-allowed;pointer-events:none;background:#f8fafc}}
.visit-row.v-pastdue{{border-color:#f97316;background:#fffbf5;cursor:default;
  flex-direction:column}}
.visit-row.v-completed{{border-color:#a5d6a7;background:#f9fffe;cursor:default}}
.visit-row input[type=radio]{{display:none}}

/* Visit strip */
.v-strip{{width:70px;flex-shrink:0;display:flex;flex-direction:column;
  align-items:center;justify-content:center;
  background:linear-gradient(160deg,#1565c0,#1976d2);
  color:#fff;padding:8px 4px;gap:3px}}
.v-strip.s-done  {{background:linear-gradient(160deg,#16a34a,#15803d)}}
.v-strip.s-booked{{background:linear-gradient(160deg,#2563eb,#1d4ed8)}}
.v-strip.s-lock  {{background:linear-gradient(160deg,#94a3b8,#64748b)}}
.v-strip.s-past  {{background:linear-gradient(160deg,#f97316,#ea580c)}}
.v-strip .vs-icon{{font-size:.95rem;opacity:.9}}
.v-strip .vs-age {{font-size:.65rem;font-weight:800;text-align:center;
  line-height:1.2;word-break:break-word;max-width:62px}}

/* Visit body */
.v-body{{flex:1;padding:10px 14px;display:flex;flex-direction:column;
  gap:4px;min-width:0}}
.v-name{{font-weight:600;font-size:.88rem;color:#1e293b;
  white-space:normal;word-break:break-word;line-height:1.4}}
.v-tag{{display:inline-flex;align-items:center;gap:4px;border-radius:6px;
  padding:2px 8px;font-size:.69rem;font-weight:700;width:fit-content;margin-bottom:2px}}
.tag-combined{{background:#fef3c7;color:#92400e;border:1px solid #fde68a}}
.tag-pastdue {{background:#fff7ed;color:#c2410c;border:1px solid #fed7aa}}
.v-date-row{{display:flex;align-items:center;flex-wrap:wrap;gap:6px;margin-top:2px}}
.v-due-lbl{{font-size:.74rem;font-weight:600;color:#64748b;white-space:nowrap}}
.v-due-pill{{display:inline-flex;align-items:center;gap:4px;border-radius:7px;
  padding:3px 11px;font-size:.8rem;font-weight:700;white-space:nowrap}}
.pill-green {{background:#e8f5e9;color:#2e7d32;border:1px solid #a5d6a7}}
.pill-orange{{background:#fff3e0;color:#e65100;border:1px solid #ffcc80}}
.pill-grey  {{background:#f1f5f9;color:#64748b;border:1px solid #e2e8f0}}

/* Visit right badge */
.v-right{{display:flex;align-items:center;padding:0 14px 0 8px;flex-shrink:0}}
.v-badge{{font-size:.71rem;font-weight:700;padding:4px 11px;border-radius:20px;white-space:nowrap}}
.bg-book{{background:#dcfce7;color:#15803d;border:1px solid #86efac}}
.bg-past{{background:#fff7ed;color:#c2410c;border:1px solid #fed7aa}}
.bg-done{{background:#d1fae5;color:#065f46}}
.bg-bkd {{background:#dbeafe;color:#1d4ed8}}
.bg-lck {{background:#f1f5f9;color:#94a3b8}}

/* Past-due action row */
.v-pastdue-actions{{padding:10px 14px 12px;border-top:1px dashed #fed7aa;
  display:flex;align-items:center;gap:10px;flex-wrap:wrap}}
.pd-q{{font-size:.79rem;font-weight:700;color:#92400e;white-space:nowrap}}
.btn-given{{display:inline-flex;align-items:center;gap:6px;background:#16a34a;
  color:#fff;border:none;border-radius:8px;padding:8px 16px;
  font-size:.84rem;font-weight:700;cursor:pointer;transition:background .2s}}
.btn-given:hover{{background:#15803d}}
.btn-late{{display:inline-flex;align-items:center;gap:6px;background:#fff;
  color:#ea580c;border:2px solid #ea580c;border-radius:8px;padding:7px 14px;
  font-size:.84rem;font-weight:700;cursor:pointer;transition:all .2s}}
.btn-late:hover,.btn-late.active{{background:#ea580c;color:#fff}}

/* ── Modal overlay ── */
.modal-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);
  z-index:2000;align-items:center;justify-content:center}}
.modal-overlay.show{{display:flex}}
.modal-box{{background:#fff;border-radius:14px;padding:28px 28px 24px;
  max-width:460px;width:90%;box-shadow:0 8px 32px rgba(0,0,0,.18)}}
.modal-title{{font-size:1rem;font-weight:700;color:#1e293b;margin-bottom:4px}}
.modal-sub{{font-size:.82rem;color:#64748b;margin-bottom:18px}}
.modal-actions{{display:flex;gap:10px;justify-content:flex-end;margin-top:20px;flex-wrap:wrap}}
.btn-cancel{{background:#f1f5f9;color:#64748b;border:none;border-radius:8px;
  padding:9px 18px;font-size:.88rem;font-weight:600;cursor:pointer}}
.btn-confirm-green{{background:#16a34a;color:#fff;border:none;border-radius:8px;
  padding:9px 18px;font-size:.88rem;font-weight:700;cursor:pointer}}
.btn-confirm-green:hover{{background:#15803d}}

/* ── Form controls ── */
.form-label{{font-weight:600;color:#334155;margin-bottom:6px;display:block;font-size:.9rem}}
.form-select,.form-control{{border-radius:8px;border:1.5px solid #cbd5e1;
  padding:10px 14px;font-size:.92rem;width:100%;
  transition:border-color .2s,box-shadow .2s;background:#fff}}
.form-select:focus,.form-control:focus{{border-color:#1565c0;
  box-shadow:0 0 0 3px rgba(21,101,192,.12);outline:none}}
.form-control.filled-green{{border-color:#22c55e!important;background:#f0fdf4!important}}
.form-control.filled-orange{{border-color:#f97316!important;background:#fff7ed!important}}

/* ── Summary box ── */
.selected-summary{{background:#f0f7ff;border:1.5px solid #bfdbfe;border-radius:10px;
  padding:12px 16px;margin-bottom:18px;display:none}}
.selected-summary.show{{display:block}}
.ss-title{{font-size:.78rem;font-weight:700;color:#1e40af;text-transform:uppercase;
  letter-spacing:.5px;margin-bottom:8px}}
.ss-tags{{display:flex;flex-wrap:wrap;gap:6px}}
.ss-tag{{background:#dbeafe;color:#1d4ed8;border-radius:6px;
  padding:3px 10px;font-size:.78rem;font-weight:600}}

/* ── Book button ── */
.btn-book{{background:linear-gradient(135deg,#1565c0,#1976d2);color:#fff;border:none;
  border-radius:10px;padding:13px 20px;font-size:1rem;font-weight:700;width:100%;
  cursor:pointer;transition:opacity .2s;margin-top:4px;
  display:flex;align-items:center;justify-content:center;gap:8px}}
.btn-book:hover{{opacity:.9}}

/* ── Responsive ── */
@media(max-width:991px){{
  .sidebar{{transform:translateX(-100%)}}
  .sidebar.open{{transform:translateX(0)}}
  .sidebar-overlay.open{{display:block}}
  .main{{margin-left:0}}
  .hamburger{{display:block}}
}}
@media(max-width:600px){{
  .main{{padding:14px 10px}}
  .step-card{{padding:18px 16px}}
  .v-strip{{width:58px}}
  .v-name{{font-size:.83rem}}
  .v-pastdue-actions{{flex-direction:column;align-items:flex-start}}
}}
</style>
</head>
<body>

<!-- Topbar -->
<div class="topbar">
  <div class="topbar-left">
    <button class="hamburger" onclick="toggleSidebar()"><i class="fa fa-bars"></i></button>
    <img src="./images/logo.jpg" alt="logo" onerror="this.style.display='none'">
    <span class="brand">Child Vaccination</span>
  </div>
  <div class="topbar-right">
    <a href="home.py"><i class="fa fa-right-from-bracket me-1"></i>Logout</a>
  </div>
</div>
<div class="sidebar-overlay" id="overlay" onclick="toggleSidebar()"></div>

<!-- Sidebar -->
<nav class="sidebar" id="sidebar">
  <div class="sidebar-label">Menu</div>
  <a href="parent_dash.py?parent_id={parent_id}" class="nav-link"><i class="fa fa-gauge"></i> Dashboard</a>
  <a href="parent_profile.py?parent_id={parent_id}" class="nav-link"><i class="fa fa-user"></i> My Profile</a>
  <hr class="sidebar-divider">
  <details class="sidebar-group">
    <summary><i class="fa-solid fa-child"></i> Child <i class="fa fa-chevron-right caret"></i></summary>
    <div class="sub-links">
      <a href="parentaddchild.py?parent_id={parent_id}"><i class="fa fa-plus"></i> Add Child</a>
      <a href="parentviewchild.py?parent_id={parent_id}"><i class="fa fa-eye"></i> View Child</a>
    </div>
  </details>
  <hr class="sidebar-divider">
  <details class="sidebar-group" open>
    <summary><i class="fa-solid fa-calendar-check"></i> Appointments <i class="fa fa-chevron-right caret"></i></summary>
    <div class="sub-links">
      <a href="parentaddappointments.py?parent_id={parent_id}" style="color:#fff;background:rgba(255,255,255,.1);"><i class="fa fa-plus"></i> Add Appointment</a>
      <a href="parentpendingappointments.py?parent_id={parent_id}"><i class="fa fa-clock"></i> Pending</a>
      <a href="parentcompletedappointments.py?parent_id={parent_id}"><i class="fa fa-circle-check"></i> Completed</a>
    </div>
  </details>
  <hr class="sidebar-divider">
  <a href="parentnotify.py?parent_id={parent_id}" class="nav-link"><i class="fa-solid fa-bell"></i> Notifications</a>
  <hr class="sidebar-divider">
  <a href="parentfeedback.py?parent_id={parent_id}" class="nav-link"><i class="fa-solid fa-comment"></i> FeedBack</a>
  <hr class="sidebar-divider">
  <a href="home.py" class="nav-link" style="color:#ef9a9a;"><i class="fa fa-right-from-bracket"></i> Logout</a>
</nav>

<!-- ══════════════════════════════════════
     ALREADY GIVEN MODAL
══════════════════════════════════════ -->
<div class="modal-overlay" id="modal_already_given">
  <div class="modal-box">
    <div class="modal-title"><i class="fa fa-check-circle me-2 text-success"></i>Mark as Already Given</div>
    <div class="modal-sub" id="modal_vaccine_label">Select hospital where vaccine was administered</div>

    <form method="post" action="parentaddappointments.py?parent_id={parent_id}" id="form_already_given">
      <input type="hidden" name="parent_id"           value="{parent_id}">
      <input type="hidden" name="child_vaccine_done"  id="fld_done_val">
      <input type="hidden" name="mark_already_done"   value="1">

      <!-- State -->
      <div class="mb-2">
        <label class="form-label" style="font-size:.85rem"><i class="fa fa-map me-1 text-primary"></i>State</label>
        <select id="modal_state" class="form-select" style="font-size:.88rem"
                onchange="loadDistricts(this.value,'modal_district','modal_hospital')">
          <option value="">-- Select State --</option>
""")
for s in all_states:
    print(f'          <option value="{s}">{s}</option>')
print(f"""
        </select>
      </div>

      <!-- District -->
      <div class="mb-2">
        <label class="form-label" style="font-size:.85rem"><i class="fa fa-location-dot me-1 text-primary"></i>District</label>
        <select id="modal_district" class="form-select" style="font-size:.88rem"
                onchange="loadHospitals(this.value,'modal_state','modal_hospital')">
          <option value="">-- Select State First --</option>
        </select>
      </div>

      <!-- Hospital -->
      <div class="mb-2">
        <label class="form-label" style="font-size:.85rem"><i class="fa fa-hospital me-1 text-primary"></i>Hospital where it was given</label>
        <select name="already_done_hospital_id" id="modal_hospital" class="form-select" style="font-size:.88rem" required>
          <option value="">-- Select District First --</option>
        </select>
      </div>

      <!-- Date & Time -->
      <div class="row g-2 mt-1 mb-1">
        <div class="col-12 col-sm-6">
          <label class="form-label" style="font-size:.85rem"><i class="fa fa-calendar me-1 text-primary"></i>Date Given</label>
          <input type="date" name="already_done_date" id="modal_done_date"
                 class="form-control" style="font-size:.88rem" required>
          <small class="text-muted" style="font-size:.75rem">Cannot be a future date</small>
        </div>
        <div class="col-12 col-sm-6">
          <label class="form-label" style="font-size:.85rem"><i class="fa fa-clock me-1 text-primary"></i>Time Given</label>
          <input type="time" name="already_done_time" id="modal_done_time"
                 class="form-control" style="font-size:.88rem"
                 value="09:00" required min="09:00" max="17:00">
          <small class="text-muted" style="font-size:.75rem">Clinic hours: 9:00 AM - 5:00 PM</small>
        </div>
      </div>

      <div class="modal-actions">
        <button type="button" class="btn-cancel" onclick="closeModal()">Cancel</button>
        <button type="submit" class="btn-confirm-green" onclick="return confirmAlreadyGiven()">
          <i class="fa fa-check me-1"></i>Confirm - Mark as Done
        </button>
      </div>
    </form>
  </div>
</div>

<!-- Main -->
<main class="main">
  <div class="page-hdr">
    <div class="phdr-icon"><i class="fa fa-calendar-plus"></i></div>
    <div>
      <h4 style="font-size:1.15rem;font-weight:700;margin:0 0 3px">Book Vaccination Appointment</h4>
      <p style="font-size:.83rem;color:#64748b;margin:0">Follow the steps below - fill each section completely</p>
    </div>
  </div>

  <!-- STEP 1 — Select Child -->
  <div class="step-card active-card" id="card_step1">
    <div class="step-hdr">
      <div class="step-num" id="snum1">1</div>
      <div>
        <div class="step-title">Select Child</div>
        <div class="step-subtitle">Choose the child to vaccinate</div>
      </div>
    </div>
    <select id="child_select" class="form-select" onchange="onChildChange(this.value)" required>
      <option value="">-- Select Child --</option>
""")
for child in children:
    print(f'      <option value="{child[0]}">{child[1]}</option>')
print(f"""
    </select>
  </div>

  <!-- STEP 2 — Select Visit -->
  <div class="step-card disabled-card" id="card_step2">
    <div class="step-hdr">
      <div class="step-num" id="snum2">2</div>
      <div>
        <div class="step-title">Select Vaccination Visit</div>
        <div class="step-subtitle">Choose which visit to book or record</div>
      </div>
    </div>
    <div id="visit_list_wrapper">
      <p style="color:#94a3b8;font-size:.87rem"><i class="fa fa-arrow-up me-1"></i>Select a child above first</p>
    </div>
  </div>

  <!-- STEP 3 — Hospital + Date/Time -->
  <div class="step-card disabled-card" id="card_step3">
    <div class="step-hdr">
      <div class="step-num" id="snum3">3</div>
      <div>
        <div class="step-title">Select Hospital</div>
        <div class="step-subtitle">Choose the hospital by state and district</div>
      </div>
    </div>

    <div class="selected-summary" id="sel_summary">
      <div class="ss-title"><i class="fa fa-syringe me-1"></i>Selected Visit</div>
      <div class="ss-tags" id="sel_summary_tags"></div>
    </div>

    <form method="post" action="parentaddappointments.py?parent_id={parent_id}"
          id="form_book" onsubmit="return validateBook()">
      <input type="hidden" name="parent_id"        value="{parent_id}">
      <input type="hidden" name="child_vaccine"    id="fld_vaccine_val">
      <input type="hidden" name="book_appointment" value="1">

      <!-- State -->
      <div class="mb-3">
        <label class="form-label"><i class="fa fa-map me-1 text-primary"></i>State</label>
        <select id="sel_state" class="form-select" onchange="loadDistricts(this.value,'sel_district','sel_hospital')">
          <option value="">-- Select State --</option>
""")
for s in all_states:
    print(f'          <option value="{s}">{s}</option>')
print(f"""
        </select>
      </div>

      <!-- District -->
      <div class="mb-3">
        <label class="form-label"><i class="fa fa-location-dot me-1 text-primary"></i>District</label>
        <select id="sel_district" class="form-select" onchange="loadHospitals(this.value,'sel_state','sel_hospital')">
          <option value="">-- Select State First --</option>
        </select>
      </div>

      <!-- Hospital -->
      <div class="mb-4">
        <label class="form-label"><i class="fa fa-hospital me-1 text-primary"></i>Hospital</label>
        <select name="hospital_id" id="sel_hospital" class="form-select" required>
          <option value="">-- Select District First --</option>
        </select>
      </div>

      <!-- STEP 4 — Date & Time -->
      <div style="border-top:1.5px dashed #e2e8f0;margin:20px 0 20px"></div>
      <div class="step-hdr" style="margin-bottom:16px">
        <div class="step-num" id="snum4">4</div>
        <div>
          <div class="step-title">Appointment Date &amp; Time</div>
          <div class="step-subtitle">Auto-filled from vaccine due date - adjust if needed</div>
        </div>
      </div>

      <div class="row g-3 mb-4">
        <div class="col-12 col-sm-6">
          <label class="form-label"><i class="fa fa-calendar me-1 text-primary"></i>Appointment Date</label>
          <input type="date" name="appointment_date" id="sel_date" class="form-control" required>
          <small class="text-muted mt-1 d-block" id="date_hint"></small>
        </div>
        <div class="col-12 col-sm-6">
          <label class="form-label"><i class="fa fa-clock me-1 text-primary"></i>Appointment Time</label>
          <input type="time" name="appointment_time" id="sel_time"
                 class="form-control" value="09:00" required min="09:00" max="17:00">
          <small class="text-muted mt-1 d-block">Clinic hours: 9:00 AM - 5:00 PM</small>
        </div>
      </div>

      <button type="submit" class="btn-book" id="btn_book_submit">
        <i class="fa fa-calendar-check"></i> Confirm Booking
      </button>
    </form>
  </div>

</main>

<script>
const visitsData   = {visits_json_str};
const hospitalData = {hospital_json_str};
const todayISO     = new Date().toISOString().split('T')[0];

/* ── sidebar ── */
function toggleSidebar(){{
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('overlay').classList.toggle('open');
}}
window.addEventListener('resize',function(){{
  if(window.innerWidth>991){{
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('overlay').classList.remove('open');
  }}
}});

/* ── format date ── */
function fmtDate(iso){{
  if(!iso)return'';
  const d=new Date(iso+'T00:00:00');
  return d.toLocaleDateString('en-GB',{{day:'2-digit',month:'short',year:'numeric'}});
}}

/* ── Step 1: child changed ── */
function onChildChange(childId){{
  const wrapper=document.getElementById('visit_list_wrapper');
  const card2  =document.getElementById('card_step2');
  const card3  =document.getElementById('card_step3');

  card3.classList.add('disabled-card');
  card3.classList.remove('active-card');
  document.getElementById('sel_summary').classList.remove('show');
  document.getElementById('fld_vaccine_val').value='';

  if(!childId){{
    wrapper.innerHTML='<p style="color:#94a3b8;font-size:.87rem"><i class="fa fa-arrow-up me-1"></i>Select a child above first</p>';
    card2.classList.add('disabled-card'); card2.classList.remove('active-card');
    return;
  }}

  card2.classList.remove('disabled-card'); card2.classList.add('active-card');

  const visits=visitsData[String(childId)]||[];
  if(!visits.length){{
    wrapper.innerHTML='<p style="color:#e53935;font-size:.87rem"><i class="fa fa-circle-exclamation me-1"></i>No vaccination visits found.</p>';
    return;
  }}

  let html='<div class="vaccine-list">';
  visits.forEach(function(v,idx){{
    const pastDue=v.is_past_due&&!v.locked;

    /* ── PAST-DUE ROW ── */
    if(pastDue){{
      const cTag=v.is_combined?`<span class="v-tag tag-combined"><i class="fa fa-layer-group me-1"></i>${{v.count}} vaccines - same visit</span>`:'';
      html+=`
      <div class="visit-row v-pastdue">
        <div style="display:flex;align-items:stretch;min-height:68px">
          <div class="v-strip s-past">
            <div class="vs-icon"><i class="fa-solid fa-syringe"></i></div>
            <div class="vs-age">${{v.age_label}}</div>
          </div>
          <div class="v-body">
            ${{cTag}}
            <span class="v-tag tag-pastdue"><i class="fa fa-triangle-exclamation me-1"></i>Past due</span>
            <div class="v-name">${{v.vaccine_names}}</div>
            <div class="v-date-row">
              <span class="v-due-lbl">Was due:</span>
              <span class="v-due-pill pill-orange"><i class="fa fa-calendar" style="font-size:.72rem"></i> ${{fmtDate(v.due_date)}}</span>
            </div>
          </div>
          <div class="v-right"><span class="v-badge bg-past">Past Due</span></div>
        </div>
        <div class="v-pastdue-actions">
          <span class="pd-q"><i class="fa fa-question-circle me-1"></i>What happened?</span>
          <button type="button" class="btn-given"
                  onclick="openAlreadyGivenModal('${{v.value}}','${{v.vaccine_names}}','${{v.due_date}}')">
            <i class="fa fa-check-circle"></i>&nbsp;Already Given at Hospital
          </button>
          <button type="button" class="btn-late" id="btn_late_${{idx}}"
                  onclick="selectLateBooking('${{v.value}}','${{v.age_label}}','${{v.vaccine_names}}','${{v.due_date}}',this)">
            <i class="fa fa-calendar-plus"></i>&nbsp;Book Late Appointment
          </button>
        </div>
      </div>`;
      return;
    }}

    /* ── NORMAL ROW ── */
    let sTxt,sBadge,sStrip;
    if(v.status==='completed')         {{sTxt='Completed';sBadge='bg-done';sStrip='s-done';}}
    else if(v.lock_reason==='booked')  {{sTxt='Booked';   sBadge='bg-bkd'; sStrip='s-booked';}}
    else if(v.locked)                  {{sTxt='Locked';   sBadge='bg-lck'; sStrip='s-lock';}}
    else                               {{sTxt='Book Now'; sBadge='bg-book';sStrip='';}}

    const cTag=v.is_combined?`<span class="v-tag tag-combined"><i class="fa fa-layer-group me-1"></i>${{v.count}} vaccines - same visit</span>`:'';
    let dateLine='';
    if(v.due_date){{
      dateLine=`<span class="v-due-lbl">Due:</span><span class="v-due-pill pill-green"><i class="fa fa-calendar-check" style="font-size:.72rem"></i> ${{fmtDate(v.due_date)}}</span>`;
    }}else if(v.locked&&v.lock_reason==='prev_pending'){{
      dateLine=`<span style="color:#f59e0b;font-size:.76rem;font-weight:600"><i class="fa fa-lock me-1"></i>Complete previous visit first</span>`;
    }}else{{
      dateLine=`<span class="v-due-pill pill-grey">Date not calculated</span>`;
    }}

    const inner=`
      <div class="v-strip ${{sStrip}}">
        <div class="vs-icon"><i class="fa-solid fa-syringe"></i></div>
        <div class="vs-age">${{v.age_label}}</div>
      </div>
      <div class="v-body">
        ${{cTag}}
        <div class="v-name">${{v.vaccine_names}}</div>
        <div class="v-date-row">${{dateLine}}</div>
      </div>
      <div class="v-right"><span class="v-badge ${{sBadge}}">${{sTxt}}</span></div>`;

    if(v.locked){{
      html+=`<div class="visit-row v-locked">${{inner}}</div>`;
    }}else{{
      html+=`<label class="visit-row clickable" id="vrow_${{idx}}">
        <input type="radio" name="_vr" value="${{v.value}}"
               data-due="${{v.due_date}}" data-age="${{v.age_label}}"
               data-vaccines="${{encodeURIComponent(v.vaccine_names)}}"
               onchange="selectNormalVisit(this)">
        ${{inner}}
      </label>`;
    }}
  }});
  html+='</div>';
  wrapper.innerHTML=html;
  card2.scrollIntoView({{behavior:'smooth',block:'start'}});
}}

/* ── Open Already Given Modal ── */
function openAlreadyGivenModal(value, names, dueDate){{
  document.getElementById('fld_done_val').value = value;
  document.getElementById('modal_vaccine_label').textContent =
    'Select the hospital where [ ' + names + ' ] was given';
  // reset dropdowns
  document.getElementById('modal_state').value    = '';
  document.getElementById('modal_district').innerHTML = '<option value="">-- Select State First --</option>';
  document.getElementById('modal_hospital').innerHTML  = '<option value="">-- Select District First --</option>';
  // set date: pre-fill with due date, max = today (cannot be future)
  const df = document.getElementById('modal_done_date');
  df.value = (dueDate && dueDate <= todayISO) ? dueDate : todayISO;
  df.max   = todayISO;
  df.min   = '';
  // reset time to 09:00
  document.getElementById('modal_done_time').value = '09:00';
  document.getElementById('modal_already_given').classList.add('show');
}}

function closeModal(){{
  document.getElementById('modal_already_given').classList.remove('show');
}}

function confirmAlreadyGiven(){{
  const hosp = document.getElementById('modal_hospital').value;
  if(!hosp){{
    alert('Please select the hospital where the vaccine was given.');
    return false;
  }}
  const dv = document.getElementById('modal_done_date').value;
  if(!dv){{
    alert('Please enter the date the vaccine was given.');
    return false;
  }}
  if(dv > todayISO){{
    alert('Date given cannot be a future date.');
    return false;
  }}
  const tv = document.getElementById('modal_done_time').value;
  if(!tv){{
    alert('Please enter the time the vaccine was given.');
    return false;
  }}
  const hh = parseInt(tv.split(':')[0]);
  if(hh < 9 || hh >= 17){{
    alert('Time must be between 9:00 AM and 5:00 PM.');
    return false;
  }}
  return true;
}}

/* ── Book Late (past-due) ── */
function selectLateBooking(value,ageLabel,names,dueDate,btn){{
  document.querySelectorAll('.btn-late').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  fillBookingForm(value,ageLabel,names,todayISO,true,dueDate);
}}

/* ── Normal visit selected ── */
function selectNormalVisit(radio){{
  document.querySelectorAll('.visit-row.clickable').forEach(r=>r.classList.remove('v-selected'));
  radio.closest('.visit-row').classList.add('v-selected');
  fillBookingForm(
    radio.value,
    radio.dataset.age,
    decodeURIComponent(radio.dataset.vaccines||''),
    radio.dataset.due,
    false,
    ''
  );
}}

/* ── Fill Step 3+4 ── */
function fillBookingForm(value,ageLabel,names,dueDate,isLate,origDue){{
  document.getElementById('fld_vaccine_val').value=value;

  const card3=document.getElementById('card_step3');
  card3.classList.remove('disabled-card'); card3.classList.add('active-card');

  const summary=document.getElementById('sel_summary');
  const tags   =document.getElementById('sel_summary_tags');
  summary.classList.add('show');
  let tagsHtml=`<span class="ss-tag"><i class="fa fa-child me-1"></i>${{ageLabel}}</span>`;
  names.split(',').forEach(n=>{{tagsHtml+=`<span class="ss-tag">${{n.trim()}}</span>`;}});
  if(isLate) tagsHtml+=`<span class="ss-tag" style="background:#fff7ed;color:#c2410c">Late booking</span>`;
  tags.innerHTML=tagsHtml;

  const df  =document.getElementById('sel_date');
  const tf  =document.getElementById('sel_time');
  const hint=document.getElementById('date_hint');
  df.min=todayISO;

  if(isLate){{
    df.value=todayISO;
    df.className='form-control filled-orange';
    tf.className='form-control filled-orange';
    hint.innerHTML='<span style="color:#ea580c;font-weight:600"><i class="fa fa-triangle-exclamation me-1"></i>Vaccine was due '+fmtDate(origDue)+' - booking today as late appointment</span>';
    document.getElementById('btn_book_submit').style.background='linear-gradient(135deg,#ea580c,#f97316)';
  }}else{{
    const filled=(dueDate&&dueDate>=todayISO)?dueDate:todayISO;
    df.value=filled;
    df.className='form-control filled-green';
    tf.className='form-control filled-green';
    hint.innerHTML=dueDate?'<span style="color:#16a34a;font-weight:600"><i class="fa fa-calendar-check me-1"></i>Auto-filled from due date - adjust if needed</span>':'';
    document.getElementById('btn_book_submit').style.background='';
  }}
  tf.value='09:00';
  card3.scrollIntoView({{behavior:'smooth',block:'start'}});
}}

/* ── Hospital loaders ── */
function loadDistricts(state,distId,hospId){{
  const ds=document.getElementById(distId),hs=document.getElementById(hospId);
  hs.innerHTML='<option value="">-- Select District First --</option>';
  if(!state||!hospitalData[state]){{ds.innerHTML='<option value="">-- Select State First --</option>';return;}}
  ds.innerHTML='<option value="">-- Select District --</option>';
  Object.keys(hospitalData[state]).sort().forEach(d=>
    ds.innerHTML+='<option value="'+d+'">'+d+'</option>');
}}

function loadHospitals(district,stateId,hospId){{
  const state=document.getElementById(stateId).value;
  const hs   =document.getElementById(hospId);
  if(!district||!state||!hospitalData[state]||!hospitalData[state][district]){{
    hs.innerHTML='<option value="">-- Select District First --</option>';return;
  }}
  const arr=hospitalData[state][district];
  if(!arr||!arr.length){{hs.innerHTML='<option value="">No hospitals found</option>';return;}}
  hs.innerHTML='<option value="">-- Select Hospital --</option>';
  arr.forEach(h=>hs.innerHTML+='<option value="'+h.id+'">'+h.name+'</option>');
}}

/* ── Validation ── */
function validateBook(){{
  if(!document.getElementById('fld_vaccine_val').value){{alert('Please select a visit.');return false;}}
  if(!document.getElementById('sel_hospital').value){{alert('Please select a hospital.');return false;}}
  const dv=document.getElementById('sel_date').value;
  if(!dv){{alert('Please enter appointment date.');return false;}}
  if(dv<todayISO){{alert('Appointment date cannot be in the past.');return false;}}
  const tv=document.getElementById('sel_time').value;
  if(!tv){{alert('Please enter appointment time.');return false;}}
  const hh=parseInt(tv.split(':')[0]);
  if(hh<9||hh>=17){{alert('Time must be between 9:00 AM and 5:00 PM.');return false;}}
  return true;
}}

document.getElementById('sel_date').min=todayISO;
</script>
</body>
</html>
""")
con.close()