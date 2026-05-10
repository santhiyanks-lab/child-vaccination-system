#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
import sys, pymysql, cgi, cgitb, smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.stdout.reconfigure(encoding="utf-8")
print("Content-Type:text/html\r\n\r\n")
cgitb.enable()

con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id  INT AUTO_INCREMENT PRIMARY KEY,
    parent_id    INT NOT NULL,
    child_id     INT NOT NULL,
    vaccine_id   INT NOT NULL,
    hospital_id  INT NOT NULL,
    rating       INT NOT NULL,
    comment      TEXT,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NULL,
    notified     TINYINT DEFAULT 0
)
""")
con.commit()

# ─── EMAIL ────────────────────────────────────────────────────────────────────
SMTP_HOST          = "smtp.gmail.com"
SMTP_PORT          = 587
SMTP_USER          = "santhiyanks@gmail.com"
SMTP_PASS          = "snnr avxt cqgb ocwy"
ADMIN_EMAIL        = "santhiyanks@gmail.com"
HOSPITAL_MGR_EMAIL = "santhiyanks@gmail.com"

def send_low_rating_email(rating, parent, child, vaccine_name, hosp_name, comment):
    try:
        stars = "⭐" * rating + "☆" * (5 - rating)
        html = f"""<html><body style="font-family:Arial;padding:20px;background:#f4f6fa">
        <div style="max-width:620px;margin:auto;background:#fff;border-radius:14px;padding:28px;box-shadow:0 4px 16px rgba(0,0,0,.1)">
          <h2 style="color:#dc2626">🚨 Low Rating Alert – Immediate Action Required</h2><hr>
          <p><b>Rating:</b> {stars} ({rating}/5)</p>
          <p><b>Comment:</b> {comment or 'No comment'}</p><hr>
          <h3 style="color:#1e3a8a">👨‍👩‍👦 Parent Details</h3>
          <p><b>Name:</b> {parent[1]}<br><b>Email:</b> {parent[6]}<br><b>Phone:</b> {parent[7]}</p><hr>
          <h3 style="color:#1e3a8a">👶 Child Details</h3>
          <p><b>Name:</b> {child[2]}<br><b>DOB:</b> {child[3]}<br><b>Gender:</b> {child[5]}</p><hr>
          <h3 style="color:#1e3a8a">💉 Vaccine</h3>
          <p><b>Vaccine:</b> {vaccine_name}<br><b>Hospital:</b> {hosp_name}</p>
        </div></body></html>"""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"⚠️ Low Feedback Rating ({rating}★) – Action Needed"
        msg["From"]    = SMTP_USER
        msg["To"]      = f"{HOSPITAL_MGR_EMAIL}, {ADMIN_EMAIL}"
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, [HOSPITAL_MGR_EMAIL, ADMIN_EMAIL], msg.as_string())
    except Exception:
        pass

# ─── FORM ─────────────────────────────────────────────────────────────────────
form      = cgi.FieldStorage()
_pid      = form.getvalue("parent_id")
parent_id = _pid[0] if isinstance(_pid, list) else _pid
action    = form.getvalue("action", "")

if parent_id is None:
    print("<h3 style='color:red;text-align:center;margin-top:50px;'>Parent ID Missing! Please login again.</h3>")
    exit()

parent_id = int(parent_id)
cur.execute("SELECT * FROM parent WHERE parent_id=%s", (parent_id,))
parent = cur.fetchone()
parent_name = parent[1] if parent else "Parent"

# ─── HANDLE SUBMIT ────────────────────────────────────────────────────────────
msg_html = ""
if action == "submit":
    child_id    = int(form.getvalue("child_id",    0))
    vaccine_id  = int(form.getvalue("vaccine_id",  0))
    hospital_id = int(form.getvalue("hospital_id", 0))
    rating      = int(form.getvalue("rating",      0))
    comment     = form.getvalue("comment", "").strip()

    if child_id and vaccine_id and hospital_id and 1 <= rating <= 5:
        cur.execute("""INSERT INTO feedback(parent_id,child_id,vaccine_id,hospital_id,rating,comment,submitted_at)
                       VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                    (parent_id, child_id, vaccine_id, hospital_id, rating, comment,
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        con.commit()
        fid = cur.lastrowid
        if rating < 2:
            cur.execute("SELECT * FROM children WHERE child_id=%s", (child_id,))
            child = cur.fetchone()
            cur.execute("SELECT vaccine_name FROM vaccine WHERE vaccine_id=%s", (vaccine_id,))
            vrow = cur.fetchone()
            cur.execute("SELECT hospital_name FROM hospital WHERE hospital_id=%s", (hospital_id,))
            hrow = cur.fetchone()
            send_low_rating_email(rating, parent, child,
                                  vrow[0] if vrow else "N/A",
                                  hrow[0] if hrow else "N/A", comment)
            cur.execute("UPDATE feedback SET notified=1 WHERE feedback_id=%s", (fid,))
            con.commit()
            msg_html = "<div class='alert alert-danger border-0 rounded-3'><i class='fa fa-triangle-exclamation me-2'></i>Feedback submitted. Hospital manager has been <strong>notified</strong> about your low rating.</div>"
        else:
            msg_html = "<div class='alert alert-success border-0 rounded-3'><i class='fa fa-circle-check me-2'></i>Feedback submitted successfully! Thank you.</div>"
    else:
        msg_html = "<div class='alert alert-warning border-0 rounded-3'>Please complete all fields and select a star rating.</div>"

elif action == "edit":
    feedback_id = int(form.getvalue("feedback_id", 0))
    rating      = int(form.getvalue("rating",      0))
    comment     = form.getvalue("comment", "").strip()

    if feedback_id and 1 <= rating <= 5:
        cur.execute("SELECT * FROM feedback WHERE feedback_id=%s AND parent_id=%s",
                    (feedback_id, parent_id))
        existing = cur.fetchone()
        if existing:
            cur.execute("""UPDATE feedback SET rating=%s, comment=%s, updated_at=%s,
                           notified = CASE WHEN %s < 2 THEN 0 ELSE notified END
                           WHERE feedback_id=%s""",
                        (rating, comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), rating, feedback_id))
            con.commit()
            if rating < 2:
                cur.execute("SELECT * FROM children WHERE child_id=%s", (existing[2],))
                child = cur.fetchone()
                cur.execute("SELECT vaccine_name FROM vaccine WHERE vaccine_id=%s", (existing[3],))
                vrow = cur.fetchone()
                cur.execute("SELECT hospital_name FROM hospital WHERE hospital_id=%s", (existing[4],))
                hrow = cur.fetchone()
                send_low_rating_email(rating, parent, child,
                                      vrow[0] if vrow else "N/A",
                                      hrow[0] if hrow else "N/A", comment)
                cur.execute("UPDATE feedback SET notified=1 WHERE feedback_id=%s", (feedback_id,))
                con.commit()
                msg_html = "<div class='alert alert-danger border-0 rounded-3'><i class='fa fa-triangle-exclamation me-2'></i>Feedback updated. Hospital manager has been <strong>notified</strong> about your low rating.</div>"
            else:
                msg_html = "<div class='alert alert-success border-0 rounded-3'><i class='fa fa-circle-check me-2'></i>Feedback updated successfully!</div>"
        else:
            msg_html = "<div class='alert alert-danger border-0 rounded-3'>Unauthorized or feedback not found.</div>"
    else:
        msg_html = "<div class='alert alert-warning border-0 rounded-3'>Please complete all fields and select a star rating.</div>"

# ─── DATA FOR PAGE ────────────────────────────────────────────────────────────
cur.execute("SELECT * FROM children WHERE parent_id=%s", (parent_id,))
children = cur.fetchall()

# ─── FIX: GROUP BY vaccine so each vaccine shows only ONCE per child ──────────
child_vaccines = {}
for ch in children:
    cur.execute("""
        SELECT v.vaccine_id, v.vaccine_name,
               GROUP_CONCAT(cv.dose_number ORDER BY cv.dose_number SEPARATOR ', ') AS doses,
               cv.hospital_id
        FROM child_vaccine cv
        JOIN vaccine v ON cv.vaccine_id = v.vaccine_id
        WHERE cv.child_id=%s AND cv.status='completed'
        GROUP BY v.vaccine_id, v.vaccine_name, cv.hospital_id
    """, (ch[0],))
    child_vaccines[ch[0]] = cur.fetchall()

# ─── FETCH FEEDBACKS WITH FULL DETAILS ───────────────────────────────────────
cur.execute("""
    SELECT f.feedback_id, f.child_id, f.vaccine_id, f.hospital_id, f.rating, f.comment,
           f.submitted_at, f.updated_at, f.notified,
           c.child_name, c.dob, c.gender, c.blood_group,
           v.vaccine_name,
           h.hospital_name,
           cv.dose_number, cv.appointment_date
    FROM feedback f
    JOIN children c   ON f.child_id    = c.child_id
    JOIN vaccine v    ON f.vaccine_id  = v.vaccine_id
    JOIN hospital h   ON f.hospital_id = h.hospital_id
    LEFT JOIN child_vaccine cv ON cv.id = (
        SELECT id FROM child_vaccine
        WHERE child_id    = f.child_id
          AND vaccine_id  = f.vaccine_id
          AND hospital_id = f.hospital_id
        ORDER BY appointment_date DESC
        LIMIT 1
    )
    WHERE f.parent_id=%s
    ORDER BY f.submitted_at DESC
""", (parent_id,))
my_feedbacks = cur.fetchall()

cur.execute("SELECT hospital_id, hospital_name FROM hospital")
all_hospitals = cur.fetchall()

print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Feedback – Child Vaccination</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
  :root {{
    --sidebar-w: 260px;
    --topbar-h: 60px;
    --primary: #1565c0;
    --green: #2e7d32;
    --bg: #f0f4f8;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: var(--bg); color: #1e293b; }}

  /* ===== TOPBAR ===== */
  .topbar {{
    position: fixed; top: 0; left: 0; right: 0;
    height: var(--topbar-h); background: #0d1b2a;
    display: flex; align-items: center;
    justify-content: space-between;
    padding: 0 16px; z-index: 1100;
    box-shadow: 0 2px 10px rgba(0,0,0,.3);
  }}
  .topbar-left {{ display: flex; align-items: center; gap: 12px; }}
  .topbar img {{
    height: 40px; width: 40px; border-radius: 50%;
    border: 2px solid rgba(255,255,255,.4); object-fit: cover;
  }}
  .topbar .brand {{ color: #fff; font-size: 1rem; font-weight: 700; }}
  .topbar .subbrand {{ color: #90a4ae; font-size: .75rem; display: block; }}
  .hamburger {{
    background: none; border: none; color: #fff; font-size: 1.4rem;
    cursor: pointer; padding: 4px 8px; border-radius: 6px;
    display: none; transition: background .2s;
  }}
  .hamburger:hover {{ background: rgba(255,255,255,.1); }}
  .topbar-right h4 {{
    color: white; text-decoration: none; font-size: .85rem;
    padding: 6px 14px; border: 1px solid #37474f;
    border-radius: 6px; transition: all .2s;
  }}

  /* ===== SIDEBAR ===== */
  .sidebar {{
    position: fixed; top: var(--topbar-h); left: 0;
    width: var(--sidebar-w); height: calc(100vh - var(--topbar-h));
    background: #0d1b2a; overflow-y: auto; z-index: 1000;
    transition: transform .3s ease; padding: 16px 12px 24px;
    scrollbar-width: thin; scrollbar-color: #1e3a5f transparent;
  }}
  .sidebar-label {{
    color: #546e7a; font-size: .68rem; font-weight: 700;
    letter-spacing: 1.5px; text-transform: uppercase; padding: 12px 8px 4px;
  }}
  .sidebar .nav-link {{
    color: #b0bec5; border-radius: 8px; padding: 9px 12px;
    font-size: .87rem; display: flex; align-items: center;
    gap: 10px; text-decoration: none; transition: all .2s; margin-bottom: 2px;
  }}
  .sidebar .nav-link i {{ width: 18px; text-align: center; font-size: .9rem; }}
  .sidebar .nav-link:hover,
  .sidebar .nav-link.active {{ background: var(--primary); color: #fff; }}
  .sidebar-group summary {{
    list-style: none; color: #b0bec5; padding: 9px 12px;
    border-radius: 8px; display: flex; align-items: center; gap: 10px;
    cursor: pointer; font-size: .87rem; transition: background .2s;
    margin-bottom: 2px; user-select: none;
  }}
  .sidebar-group summary::-webkit-details-marker {{ display: none; }}
  .sidebar-group summary:hover {{ background: #1c2d3e; color: #fff; }}
  .sidebar-group summary .caret {{ margin-left: auto; transition: transform .25s; font-size: .75rem; }}
  .sidebar-group[open] summary .caret {{ transform: rotate(90deg); }}
  .sidebar-group[open] summary {{ color: #fff; background: #1c2d3e; }}
  .sub-links {{ padding: 4px 0 4px 28px; }}
  .sub-links a {{
    display: flex; align-items: center; gap: 8px;
    color: #78909c; font-size: .83rem; padding: 7px 10px;
    border-radius: 6px; text-decoration: none; transition: all .2s; margin-bottom: 1px;
  }}
  .sub-links a:hover {{ color: #fff; background: rgba(255,255,255,.07); }}
  .sidebar-divider {{ border: none; border-top: 1px solid #1c2d3e; margin: 10px 0; }}

  /* ===== OVERLAY ===== */
  .sidebar-overlay {{
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,.55); z-index: 999; backdrop-filter: blur(2px);
  }}

  /* ===== MAIN ===== */
  .main {{
    margin-left: var(--sidebar-w); margin-top: var(--topbar-h);
    padding: 28px 24px; min-height: calc(100vh - var(--topbar-h));
    transition: margin-left .3s;
  }}

  /* ===== PAGE HEADER ===== */
  .page-header {{ display:flex; align-items:flex-start; gap:14px; margin-bottom:24px; flex-wrap:wrap; }}
  .page-header-icon {{
    background: linear-gradient(135deg,#e53935,#ff7043); color:#fff;
    width:52px; height:52px; border-radius:14px;
    display:flex; align-items:center; justify-content:center; font-size:1.4rem; flex-shrink:0;
  }}
  .page-header-text h4 {{ font-size:1.3rem; font-weight:700; margin:0 0 4px; }}
  .page-header-text p {{ font-size:.88rem; color:#64748b; margin:0; }}

  /* ===== FORM CARD ===== */
  .form-card {{
    background:#fff; border-radius:16px; padding:28px;
    box-shadow:0 2px 12px rgba(0,0,0,.08); margin-bottom:24px;
  }}
  .form-card .card-title {{
    font-size:1rem; font-weight:700; border-bottom:2px solid #f1f5f9;
    padding-bottom:12px; margin-bottom:20px;
  }}

  /* ===== STARS ===== */
  .star-rating {{ display:flex; flex-direction:row-reverse; gap:6px; justify-content:flex-end; }}
  .star-rating input {{ display:none; }}
  .star-rating label {{
    font-size:2.4rem; color:#d1d5db; cursor:pointer;
    transition:color .15s,transform .1s; line-height:1;
  }}
  .star-rating input:checked ~ label,
  .star-rating label:hover,
  .star-rating label:hover ~ label {{ color:#f59e0b; transform:scale(1.1); }}
  .rating-hint {{ font-size:.85rem; font-weight:600; min-height:20px; margin-top:6px; }}
  .hint-1,.hint-2 {{ color:#dc2626; }}
  .hint-3 {{ color:#f97316; }}
  .hint-4,.hint-5 {{ color:#16a34a; }}
  .low-warn {{
    background:#fef2f2; border:1.5px solid #fca5a5; border-radius:10px;
    padding:10px 14px; color:#b91c1c; font-size:.84rem; display:none; margin-top:8px;
  }}
  .low-warn.show {{ display:flex; align-items:center; gap:8px; }}

  /* ===== FEEDBACK CARDS ===== */
  .fb-card {{
    background:#fff; border-radius:12px; border:1.5px solid #e5e7eb;
    padding:16px 18px; margin-bottom:14px; transition:box-shadow .2s;
  }}
  .fb-card:hover {{ box-shadow:0 4px 16px rgba(0,0,0,.12); border-color:#a5b4fc; }}
  .fb-card.low {{ border-color:#fca5a5; background:#fff8f8; }}
  .fb-stars {{ font-size:1.3rem; line-height:1; }}
  .badge-low {{ background:#fee2e2; color:#b91c1c; font-size:.72rem; padding:3px 10px; border-radius:20px; font-weight:700; }}
  .badge-edited {{ background:#eff6ff; color:#1d4ed8; font-size:.72rem; padding:3px 10px; border-radius:20px; font-weight:700; }}
  .edit-btn {{
    background:#ede9fe; color:#4f46e5; border:none; border-radius:8px;
    padding:6px 16px; font-size:.82rem; font-weight:700; cursor:pointer; white-space:nowrap;
  }}
  .edit-btn:hover {{ background:#c7d2fe; }}
  .view-btn {{
    background:#e0f2fe; color:#0369a1; border:none; border-radius:8px;
    padding:6px 16px; font-size:.82rem; font-weight:700; cursor:pointer; white-space:nowrap;
  }}
  .view-btn:hover {{ background:#bae6fd; }}

  select.form-select, textarea.form-control {{
    border-radius:10px; border:1.5px solid #e5e7eb; font-size:.9rem;
  }}
  select.form-select:focus, textarea.form-control:focus {{
    border-color:#1565c0; box-shadow:0 0 0 3px rgba(21,101,192,.1);
  }}

  /* ===== DETAIL MODAL ===== */
  .detail-section {{ background:#f8fafc; border-radius:10px; padding:14px 16px; margin-bottom:12px; }}
  .detail-section-title {{
    font-size:.78rem; font-weight:700; text-transform:uppercase;
    letter-spacing:1px; color:#64748b; margin-bottom:10px;
  }}
  .detail-row {{
    display:flex; justify-content:space-between; align-items:center;
    padding:5px 0; border-bottom:1px solid #f1f5f9; font-size:.88rem;
  }}
  .detail-row:last-child {{ border-bottom:none; }}
  .detail-label {{ color:#64748b; font-weight:500; }}
  .detail-value {{ color:#1e293b; font-weight:600; text-align:right; }}
  .stars-display {{ color:#f59e0b; font-size:1.3rem; }}

  /* ===== RESPONSIVE ===== */
  @media (max-width: 991px) {{
    .sidebar {{ transform: translateX(-100%); }}
    .sidebar.open {{ transform: translateX(0); }}
    .sidebar-overlay.open {{ display: block; }}
    .main {{ margin-left: 0; }}
    .hamburger {{ display: block; }}
  }}
  @media (max-width: 576px) {{
    .main {{ padding: 16px 12px; }}
    .form-card {{ padding: 18px; }}
  }}
</style>
</head>
<body>

<!-- ===== TOPBAR ===== -->
<div class="topbar">
  <div class="topbar-left">
    <button class="hamburger" onclick="toggleSidebar()" aria-label="Open menu">
      <i class="fa fa-bars"></i>
    </button>
    <img src="./images/logo.jpg" alt="logo" onerror="this.style.display='none'">
    <div>
      <span class="brand">Child Vaccination</span>
    </div>
  </div>
  <div class="topbar-right">
    <h4>Parent Portal</h4>
  </div>
</div>

<!-- OVERLAY -->
<div class="sidebar-overlay" id="overlay" onclick="toggleSidebar()"></div>

<!-- ===== SIDEBAR ===== -->
<nav class="sidebar" id="sidebar">
  <div class="sidebar-label">Menu</div>
  <a href="parent_dash.py?parent_id={parent_id}" class="nav-link">
    <i class="fa fa-gauge"></i> Dashboard
  </a>
  <a href="parent_profile.py?parent_id={parent_id}" class="nav-link">
    <i class="fa fa-user"></i> My Profile
  </a>

  <hr class="sidebar-divider">
  <details class="sidebar-group">
    <summary>
      <i class="fa-solid fa-child"></i> Child
      <i class="fa fa-chevron-right caret"></i>
    </summary>
    <div class="sub-links">
      <a href="parentaddchild.py?parent_id={parent_id}"><i class="fa fa-plus"></i> Add Child</a>
      <a href="parentviewchild.py?parent_id={parent_id}"><i class="fa fa-eye"></i> View Child</a>
    </div>
  </details>

  <hr class="sidebar-divider">
  <details class="sidebar-group">
    <summary>
      <i class="fa-solid fa-calendar-check"></i> Appointments
      <i class="fa fa-chevron-right caret"></i>
    </summary>
    <div class="sub-links">
      <a href="parentaddappointments.py?parent_id={parent_id}"><i class="fa fa-plus"></i> Add Appointment</a>
      <a href="parentpendingappointments.py?parent_id={parent_id}"><i class="fa fa-clock"></i> Pending</a>
      <a href="parentcompletedappointments.py?parent_id={parent_id}"><i class="fa fa-circle-check"></i> Completed</a>
    </div>
  </details>

  <hr class="sidebar-divider">
  <a href="parentnotify.py?parent_id={parent_id}" class="nav-link">
    <i class="fa-solid fa-bell"></i> Notifications
  </a>

  <hr class="sidebar-divider">
  <a href="parentfeedback.py?parent_id={parent_id}" class="nav-link active">
    <i class="fa-solid fa-star"></i> FeedBack
  </a>

  <hr class="sidebar-divider">
  <a href="home.py" class="nav-link" style="color:#ef9a9a;">
    <i class="fa fa-right-from-bracket"></i> Logout
  </a>
</nav>

<!-- ===== MAIN ===== -->
<main class="main">

  <div class="page-header">
    <div class="page-header-icon"><i class="fa fa-star"></i></div>
    <div class="page-header-text">
      <h4>Vaccine Feedback</h4>
      <p>Rate your vaccination experience and help us improve services</p>
    </div>
  </div>

  {msg_html}

  <div class="row g-4">
    <div class="col-lg-5">
      <div class="form-card">
        <div class="card-title"><i class="fa fa-pen-to-square me-2 text-primary"></i>Submit New Feedback</div>
        <form method="post" action="parentfeedback.py?parent_id={parent_id}">
          <input type="hidden" name="parent_id" value="{parent_id}">
          <input type="hidden" name="action"    value="submit">

          <div class="mb-3">
            <label class="form-label fw-semibold" style="font-size:.88rem;">👶 Select Child</label>
            <select name="child_id" id="childSelect" class="form-select"
                    onchange="loadVaccines(this.value)" required>
              <option value="">-- Select Child --</option>
""")

for ch in children:
    print(f'              <option value="{ch[0]}">{ch[2]}</option>')

print(f"""
            </select>
          </div>

          <div class="mb-3">
            <label class="form-label fw-semibold" style="font-size:.88rem;">💉 Select Vaccine</label>
            <select name="vaccine_id" id="vaccineSelect" class="form-select" required>
              <option value="">-- Select Child First --</option>
            </select>
          </div>

          <div class="mb-3">
            <label class="form-label fw-semibold" style="font-size:.88rem;">🏥 Hospital</label>
            <select name="hospital_id" id="hospitalSelect" class="form-select" required>
              <option value="">-- Auto-filled from vaccine --</option>
            </select>
          </div>

          <div class="mb-3">
            <label class="form-label fw-semibold" style="font-size:.88rem;">⭐ Your Rating</label>
            <div class="star-rating">
              <input type="radio" name="rating" id="s5" value="5">
              <label for="s5" title="Excellent">★</label>
              <input type="radio" name="rating" id="s4" value="4">
              <label for="s4" title="Good">★</label>
              <input type="radio" name="rating" id="s3" value="3">
              <label for="s3" title="Average">★</label>
              <input type="radio" name="rating" id="s2" value="2">
              <label for="s2" title="Poor">★</label>
              <input type="radio" name="rating" id="s1" value="1">
              <label for="s1" title="Very Poor">★</label>
            </div>
            <div class="rating-hint" id="ratingHint" style="color:#94a3b8;">Click a star to rate</div>
            <div class="low-warn" id="lowWarn">
              <i class="fa fa-triangle-exclamation"></i>
              <span>Rating below 2 will <strong>notify the hospital manager</strong> immediately.</span>
            </div>
          </div>

          <div class="mb-4">
            <label class="form-label fw-semibold" style="font-size:.88rem;">
              💬 Comment <span class="text-muted fw-normal">(optional)</span>
            </label>
            <textarea name="comment" class="form-control" rows="3"
                      placeholder="Share your experience..."></textarea>
          </div>

          <button type="submit" class="btn btn-primary w-100 fw-bold" style="border-radius:10px;padding:11px;">
            <i class="fa fa-paper-plane me-2"></i>Submit Feedback
          </button>
        </form>
      </div>
    </div>

    <div class="col-lg-7">
      <div class="form-card">
        <div class="card-title">
          <i class="fa fa-clock-rotate-left me-2 text-primary"></i>
          My Feedback History
          <span class="badge bg-primary ms-2" style="font-size:.75rem;">{len(my_feedbacks)}</span>
        </div>
        <p style="font-size:.82rem;color:#94a3b8;margin-bottom:14px;">
          <i class="fa fa-circle-info me-1"></i> Click <b>View Details</b> on any card to see full child, vaccine &amp; hospital info.
        </p>
""")

if not my_feedbacks:
    print("""
        <div class="text-center py-5">
          <i class="fa fa-star-half-stroke fa-3x mb-3" style="color:#d1d5db;"></i>
          <p class="text-muted mb-0">No feedback submitted yet.</p>
          <p class="text-muted" style="font-size:.85rem;">Submit your first feedback after vaccination!</p>
        </div>
    """)
else:
    for fb in my_feedbacks:
        fb_id        = fb[0]
        fb_rating    = fb[4]
        fb_comment   = fb[5] or ""
        fb_date      = str(fb[6])[:16]
        fb_updated   = str(fb[7])[:16] if fb[7] else None
        fb_notified  = fb[8]
        child_name   = fb[9]
        child_dob    = str(fb[10]) if fb[10] else "N/A"
        child_gender = fb[11] or "N/A"
        child_blood  = fb[12] or "N/A"
        vaccine_name = fb[13]
        hosp_name    = fb[14]
        dose_number  = fb[15] or "N/A"
        appt_date    = str(fb[16])[:10] if fb[16] else "N/A"

        filled   = "⭐" * fb_rating
        empty    = '<span style="color:#d1d5db">' + "★" * (5 - fb_rating) + '</span>'
        is_low   = fb_rating < 2

        safe_comment      = fb_comment.replace("`", "&#96;").replace("\\", "\\\\")
        safe_child_name   = child_name.replace('"', '&quot;')
        safe_vaccine_name = vaccine_name.replace('"', '&quot;')
        safe_hosp_name    = hosp_name.replace('"', '&quot;')
        safe_comment_js   = fb_comment.replace("\\", "\\\\").replace("`", "\\`").replace("'", "\\'")

        print(f"""
        <div class="fb-card {'low' if is_low else ''}">
          <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
            <div style="flex:1;min-width:0;">
              <div class="fb-stars mb-1">{filled}{empty}
                <span class="ms-1 fw-bold" style="font-size:.9rem;vertical-align:middle;">{fb_rating}/5</span>
              </div>
              <div style="font-size:.82rem;color:#64748b;">
                💉 <b>{vaccine_name}</b> &nbsp;|&nbsp; 👶 {child_name} &nbsp;|&nbsp; 🏥 {hosp_name}
              </div>
              <div style="font-size:.78rem;color:#94a3b8;margin-top:3px;">
                🗓️ {fb_date}
                {'&nbsp;<span class="badge-edited">✏️ Edited ' + fb_updated + '</span>' if fb_updated else ''}
                {'&nbsp;<span class="badge-low">⚠️ Manager Notified</span>' if fb_notified else ''}
              </div>
              <div style="font-size:.88rem;color:#374151;margin-top:8px;">
                {'<em style="color:#9ca3af">No comment provided</em>' if not fb_comment else fb_comment}
              </div>
            </div>
            <div class="d-flex flex-column gap-2">
              <button class="view-btn" onclick="openDetails(
                '{safe_child_name}', '{child_dob}', '{child_gender}', '{child_blood}',
                '{safe_vaccine_name}', '{dose_number}', '{appt_date}',
                '{safe_hosp_name}',
                {fb_rating}, `{safe_comment_js}`, '{fb_date}'
              )">
                <i class="fa fa-eye me-1"></i>View Details
              </button>
              <button class="edit-btn" onclick="openEdit({fb_id}, {fb_rating}, `{safe_comment}`)">
                <i class="fa fa-pen me-1"></i>Edit
              </button>
            </div>
          </div>
        </div>
        """)

print(f"""
      </div>
    </div>
  </div>
</main>

<!-- ─── DETAILS MODAL ──────────────────────────────────────────────────────── -->
<div class="modal fade" id="detailsModal" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered modal-lg">
    <div class="modal-content" style="border-radius:16px;border:none;overflow:hidden;">
      <div class="modal-header" style="background:linear-gradient(135deg,#1565c0,#0d47a1);">
        <h5 class="modal-title text-white"><i class="fa fa-circle-info me-2"></i>Feedback Details</h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body p-4">
        <div class="text-center mb-4">
          <div class="stars-display" id="detailStars"></div>
          <div id="detailRatingText" style="font-size:.9rem;font-weight:700;margin-top:4px;"></div>
          <div id="dDate" style="font-size:.78rem;color:#94a3b8;margin-top:2px;"></div>
        </div>
        <div class="row g-3">
          <div class="col-md-4">
            <div class="detail-section">
              <div class="detail-section-title"><i class="fa fa-child me-1"></i>Child Details</div>
              <div class="detail-row"><span class="detail-label">Name</span><span class="detail-value" id="dChildName">—</span></div>
              <div class="detail-row"><span class="detail-label">Date of Birth</span><span class="detail-value" id="dChildDob">—</span></div>
              <div class="detail-row"><span class="detail-label">Gender</span><span class="detail-value" id="dChildGender">—</span></div>
              <div class="detail-row"><span class="detail-label">Blood Group</span><span class="detail-value" id="dChildBlood">—</span></div>
            </div>
          </div>
          <div class="col-md-4">
            <div class="detail-section">
              <div class="detail-section-title"><i class="fa fa-syringe me-1"></i>Vaccine Details</div>
              <div class="detail-row"><span class="detail-label">Vaccine</span><span class="detail-value" id="dVaccineName">—</span></div>
              <div class="detail-row"><span class="detail-label">Dose</span><span class="detail-value" id="dDose">—</span></div>
              <div class="detail-row"><span class="detail-label">Appointment</span><span class="detail-value" id="dApptDate">—</span></div>
            </div>
          </div>
          <div class="col-md-4">
            <div class="detail-section">
              <div class="detail-section-title"><i class="fa fa-hospital me-1"></i>Hospital Details</div>
              <div class="detail-row"><span class="detail-label">Hospital</span><span class="detail-value" id="dHospName">—</span></div>
            </div>
          </div>
        </div>
        <div class="detail-section mt-1">
          <div class="detail-section-title"><i class="fa fa-comment me-1"></i>Your Comment</div>
          <p id="dComment" style="font-size:.9rem;color:#374151;margin:0;"></p>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ─── EDIT MODAL ────────────────────────────────────────────────────────── -->
<div class="modal fade" id="editModal" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content" style="border-radius:16px;border:none;overflow:hidden;">
      <div class="modal-header" style="background:#0d1b2a;">
        <h5 class="modal-title text-white"><i class="fa fa-pen me-2"></i>Edit Feedback</h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body p-4">
        <form method="post" action="parentfeedback.py?parent_id={parent_id}">
          <input type="hidden" name="parent_id"  value="{parent_id}">
          <input type="hidden" name="action"      value="edit">
          <input type="hidden" name="feedback_id" id="editFeedbackId">

          <div class="mb-3">
            <label class="form-label fw-semibold" style="font-size:.88rem;">⭐ Your Rating</label>
            <div class="star-rating" id="editStarRating">
              <input type="radio" name="rating" id="es5" value="5"><label for="es5">★</label>
              <input type="radio" name="rating" id="es4" value="4"><label for="es4">★</label>
              <input type="radio" name="rating" id="es3" value="3"><label for="es3">★</label>
              <input type="radio" name="rating" id="es2" value="2"><label for="es2">★</label>
              <input type="radio" name="rating" id="es1" value="1"><label for="es1">★</label>
            </div>
            <div class="rating-hint" id="editRatingHint" style="color:#94a3b8;"> </div>
            <div class="low-warn" id="editLowWarn">
              <i class="fa fa-triangle-exclamation"></i>
              <span>Rating below 2 will <strong>notify the hospital manager</strong>.</span>
            </div>
          </div>

          <div class="mb-4">
            <label class="form-label fw-semibold" style="font-size:.88rem;">💬 Comment</label>
            <textarea name="comment" id="editComment" class="form-control" rows="3"
                      placeholder="Update your comment..."></textarea>
          </div>

          <button type="submit" class="btn btn-primary w-100 fw-bold" style="border-radius:10px;padding:11px;">
            <i class="fa fa-floppy-disk me-2"></i>Save Changes
          </button>
        </form>
      </div>
    </div>
  </div>
</div>

<script>
// ─── FIX: childVaccines now has unique vaccines with grouped doses ───────────
const childVaccines = {{
""")

# Build JS object — each vaccine appears ONCE, doses shown as "Dose 1, 2, 3"
parts = []
for ch in children:
    vlist = child_vaccines.get(ch[0], [])
    entries = ",".join(
        f'{{vaccine_id:{v[0]},vaccine_name:"{v[1]}",doses:"{v[2] or "1"}",hospital_id:{v[3]}}}'
        for v in vlist
    )
    parts.append(f'  {ch[0]}: [{entries}]')
print(",\n".join(parts))

hosp_map_js = "{" + ",".join(f'{h[0]}:"{h[1]}"' for h in all_hospitals) + "}"

print(f"""
}};
const hospitalMap = {hosp_map_js};

// ─── FIX: loadVaccines now shows each vaccine ONCE with all its doses ────────
function loadVaccines(childId) {{
  const vSel = document.getElementById('vaccineSelect');
  const hSel = document.getElementById('hospitalSelect');
  vSel.innerHTML = '<option value="">-- Select Vaccine --</option>';
  hSel.innerHTML = '<option value="">-- Select Vaccine First --</option>';
  if (!childId || !childVaccines[+childId]) return;
  childVaccines[+childId].forEach(v => {{
    const opt = document.createElement('option');
    opt.value = v.vaccine_id;
    opt.dataset.hospital = v.hospital_id;
    // Shows: "Polio (Dose: 1, 2, 3)" — unique per vaccine
    opt.textContent = v.vaccine_name + ' (Dose: ' + v.doses + ')';
    vSel.appendChild(opt);
  }});
}}

document.getElementById('vaccineSelect').addEventListener('change', function() {{
  const opt  = this.options[this.selectedIndex];
  const hid  = opt ? opt.dataset.hospital : null;
  const hSel = document.getElementById('hospitalSelect');
  hSel.innerHTML = '<option value="">-- Select --</option>';
  if (hid && hospitalMap[hid]) {{
    const o = document.createElement('option');
    o.value = hid; o.textContent = hospitalMap[hid]; o.selected = true;
    hSel.appendChild(o);
  }}
}});

const hints    = ['','😞 Very Poor','😕 Poor','😐 Average','😊 Good','🤩 Excellent'];
const hintClrs = ['','#dc2626','#dc2626','#f97316','#16a34a','#16a34a'];

function bindStars(selector, hintId, warnId) {{
  document.querySelectorAll(selector).forEach(r => {{
    r.addEventListener('change', () => updateHint(+r.value, hintId, warnId));
  }});
}}
function updateHint(v, hintId, warnId) {{
  const hint = document.getElementById(hintId);
  const warn = document.getElementById(warnId);
  hint.textContent = hints[v];
  hint.className   = 'rating-hint hint-' + v;
  v < 2 ? warn.classList.add('show') : warn.classList.remove('show');
}}

bindStars('#s1,#s2,#s3,#s4,#s5',      'ratingHint',     'lowWarn');
bindStars('#es1,#es2,#es3,#es4,#es5', 'editRatingHint', 'editLowWarn');

function openDetails(childName, childDob, childGender, childBlood,
                     vaccineName, dose, apptDate,
                     hospName, rating, comment, fbDate) {{
  document.getElementById('dChildName').textContent   = childName;
  document.getElementById('dChildDob').textContent    = childDob;
  document.getElementById('dChildGender').textContent = childGender;
  document.getElementById('dChildBlood').textContent  = childBlood;
  document.getElementById('dVaccineName').textContent = vaccineName;
  document.getElementById('dDose').textContent        = dose;
  document.getElementById('dApptDate').textContent    = apptDate;
  document.getElementById('dHospName').textContent    = hospName;
  document.getElementById('dComment').textContent     = comment || 'No comment provided';
  document.getElementById('dDate').textContent        = '🗓️ Submitted: ' + fbDate;
  document.getElementById('detailStars').textContent  = '⭐'.repeat(rating) + '☆'.repeat(5 - rating);
  const rEl = document.getElementById('detailRatingText');
  rEl.textContent = hints[rating] + ' (' + rating + '/5)';
  rEl.style.color = hintClrs[rating];
  new bootstrap.Modal(document.getElementById('detailsModal')).show();
}}

function openEdit(feedbackId, rating, comment) {{
  document.getElementById('editFeedbackId').value = feedbackId;
  document.getElementById('editComment').value    = comment;
  const r = document.getElementById('es' + rating);
  if (r) {{ r.checked = true; updateHint(rating, 'editRatingHint', 'editLowWarn'); }}
  new bootstrap.Modal(document.getElementById('editModal')).show();
}}

function toggleSidebar() {{
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('overlay').classList.toggle('open');
}}
</script>
</body>
</html>
""")

con.close()