#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
import os.path
print("Content-Type: text/html\r\n\r\n")

import cgi, cgitb, pymysql, sys
sys.stdout.reconfigure(encoding='utf-8')
cgitb.enable()

con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()

form = cgi.FieldStorage()
hid  = form.getvalue("parent_id")

if not hid:
    print("<script>alert('Invalid Access');location.href='home.py';</script>")
    exit()

# ---- Fetch parent info ----
cur.execute("SELECT * FROM parent WHERE parent_id=%s", (hid,))
parent      = cur.fetchone()
parent_name = parent[1] if parent else "Parent"

# ---- Fetch stats ----
cur.execute("SELECT COUNT(*) FROM children WHERE parent_id=%s", (hid,))
child_count = cur.fetchone()[0]

cur.execute("""SELECT COUNT(*) FROM child_vaccine cv
               JOIN children c ON cv.child_id=c.child_id
               WHERE c.parent_id=%s AND cv.status='pending'""", (hid,))
pending_appts = cur.fetchone()[0]

cur.execute("""SELECT COUNT(*) FROM child_vaccine cv
               JOIN children c ON cv.child_id=c.child_id
               WHERE c.parent_id=%s AND cv.status='completed'""", (hid,))
completed_appts = cur.fetchone()[0]

cur.execute("""SELECT COUNT(*) FROM child_vaccine cv
               JOIN children c ON cv.child_id=c.child_id
               WHERE c.parent_id=%s AND cv.status='confirmed'""", (hid,))
confirmed_appts = cur.fetchone()[0]

# ---- Cross-hospital history summary for dashboard ----
# Fetch children of this parent, then all completed doses at ANY hospital,
# grouped by child so we can show a per-child summary card.
cur.execute("SELECT child_id, child_name FROM children WHERE parent_id=%s", (hid,))
children_rows = cur.fetchall()   # [(child_id, child_name), ...]

cross_summary = []   # list of dicts, one per child that has cross-hosp doses

for child_id, child_name in children_rows:
    # Get the hospitals this child has appointments at (primary hospitals)
    cur.execute("""
        SELECT DISTINCT cv.hospital_id
        FROM child_vaccine cv
        WHERE cv.child_id = %s
          AND LOWER(TRIM(cv.status)) IN ('pending','notified','confirmed')
        LIMIT 1
    """, (child_id,))
    primary_row = cur.fetchone()
    primary_hospital_id = primary_row[0] if primary_row else None

    # Fetch all completed doses at OTHER hospitals
    if primary_hospital_id:
        cur.execute("""
            SELECT
                v.dose_number,
                v.vaccine_name,
                h.hospital_name,
                h.address,
                cv.taken_date,
                cv.appointment_date,
                cv.status
            FROM child_vaccine cv
            LEFT JOIN vaccine  v ON cv.vaccine_id  = v.vaccine_id
            LEFT JOIN hospital h ON cv.hospital_id = h.hospital_id
            WHERE cv.child_id    = %s
              AND cv.hospital_id != %s
              AND h.hospital_id IS NOT NULL
              AND LOWER(TRIM(cv.status)) IN ('completed','confirmed','taken')
            ORDER BY v.dose_number ASC
        """, (child_id, primary_hospital_id))
    else:
        # No primary — show all completed doses across any hospital
        cur.execute("""
            SELECT
                v.dose_number,
                v.vaccine_name,
                h.hospital_name,
                h.address,
                cv.taken_date,
                cv.appointment_date,
                cv.status
            FROM child_vaccine cv
            LEFT JOIN vaccine  v ON cv.vaccine_id  = v.vaccine_id
            LEFT JOIN hospital h ON cv.hospital_id = h.hospital_id
            WHERE cv.child_id = %s
              AND h.hospital_id IS NOT NULL
              AND LOWER(TRIM(cv.status)) IN ('completed','confirmed','taken')
            ORDER BY v.dose_number ASC
        """, (child_id,))

    doses = cur.fetchall()
    if doses:
        dose_list = []
        for d in doses:
            date_given = str(d[4]) if d[4] else (str(d[5]) if d[5] else "-")
            dose_list.append({
                "dose_number"  : d[0] if d[0] else "-",
                "vaccine_name" : d[1] if d[1] else "Unknown",
                "hospital_name": d[2] if d[2] else "Unknown Hospital",
                "address"      : d[3] if d[3] else "Address not available",
                "date_given"   : date_given,
                "status"       : d[6] if d[6] else "-",
            })
        cross_summary.append({
            "child_id"  : child_id,
            "child_name": child_name,
            "doses"     : dose_list,
        })

total_cross_doses = sum(len(c["doses"]) for c in cross_summary)

print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Parent Dashboard</title>
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

  .topbar {{
    position: fixed; top: 0; left: 0; right: 0;
    height: var(--topbar-h); background: #0d1b2a;
    display: flex; align-items: center;
    justify-content: space-between;
    padding: 0 16px; z-index: 1100;
    box-shadow: 0 2px 10px rgba(0,0,0,.3);
  }}
  .topbar-left {{ display: flex; align-items: center; gap: 12px; }}
  .topbar img {{ height: 40px; width: 40px; border-radius: 50%; border: 2px solid rgba(255,255,255,.4); object-fit: cover; }}
  .topbar .brand {{ color: #fff; font-size: 1rem; font-weight: 700; }}
  .topbar .subbrand {{ color: #90a4ae; font-size: .75rem; display: block; }}
  .hamburger {{ background: none; border: none; color: #fff; font-size: 1.4rem; cursor: pointer; padding: 4px 8px; border-radius: 6px; display: none; transition: background .2s; }}
  .hamburger:hover {{ background: rgba(255,255,255,.1); }}
  .topbar-right h4 {{ color: white; font-size: .85rem; padding: 6px 14px; border: 1px solid #37474f; border-radius: 6px; }}

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

  .welcome-card {{
    background: linear-gradient(135deg,#1b5e20,#2e7d32);
    border-radius: 16px; padding: 28px 32px; color: #fff;
    box-shadow: 0 4px 20px rgba(27,94,32,.3);
    position: relative; overflow: hidden; margin-bottom: 28px;
  }}
  .welcome-card::before {{ content:''; position:absolute; top:-40px; right:-40px; width:180px; height:180px; background:rgba(255,255,255,.06); border-radius:50%; }}
  .welcome-card::after  {{ content:''; position:absolute; bottom:-60px; right:60px; width:240px; height:240px; background:rgba(255,255,255,.04); border-radius:50%; }}
  .welcome-card h3 {{ font-size:clamp(1.05rem,3vw,1.4rem); font-weight:700; margin:0 0 6px; position:relative; z-index:1; }}
  .welcome-card p  {{ font-size:.9rem; opacity:.85; margin:0; position:relative; z-index:1; }}

  .section-label {{ font-size:.72rem; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:#94a3b8; margin:0 0 14px; }}

  .stat-card {{ background:#fff; border-radius:14px; padding:18px 16px; display:flex; align-items:center; gap:14px; box-shadow:0 2px 12px rgba(0,0,0,.08); transition:transform .2s,box-shadow .2s; text-decoration:none; color:inherit; height:100%; border-bottom:3px solid transparent; }}
  .stat-card:hover {{ transform:translateY(-3px); box-shadow:0 8px 24px rgba(0,0,0,.12); color:inherit; }}
  .stat-icon {{ width:50px; height:50px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:1.25rem; flex-shrink:0; }}
  .stat-num {{ font-size:1.7rem; font-weight:800; line-height:1; margin:0; }}
  .stat-label {{ font-size:.78rem; color:#64748b; font-weight:600; margin:4px 0 0; }}

  .quick-link {{ background:#fff; border:none; border-radius:12px; padding:16px 12px; text-align:center; text-decoration:none; color:#1e293b; box-shadow:0 2px 10px rgba(0,0,0,.07); transition:all .2s; display:flex; flex-direction:column; align-items:center; gap:8px; height:100%; }}
  .quick-link:hover {{ transform:translateY(-3px); box-shadow:0 8px 20px rgba(0,0,0,.12); color:#1e293b; }}
  .ql-icon {{ width:44px; height:44px; border-radius:11px; display:flex; align-items:center; justify-content:center; font-size:1.1rem; }}
  .quick-link span {{ font-size:.82rem; font-weight:600; line-height:1.3; }}

  /* ===== CROSS-HOSPITAL SECTION ===== */
  .ch-banner {{
    background: linear-gradient(135deg,#e65100,#ff8f00);
    border-radius: 14px; padding: 18px 22px; color:#fff;
    margin-bottom: 28px; display:flex; align-items:center;
    justify-content:space-between; gap:14px; flex-wrap:wrap;
    box-shadow: 0 4px 16px rgba(230,81,0,.25);
  }}
  .ch-banner-left {{ display:flex; align-items:center; gap:14px; }}
  .ch-banner-icon {{ width:46px; height:46px; border-radius:12px; background:rgba(255,255,255,.2); display:flex; align-items:center; justify-content:center; font-size:1.2rem; flex-shrink:0; }}
  .ch-banner h5 {{ margin:0; font-size:.95rem; font-weight:700; }}
  .ch-banner p  {{ margin:0; font-size:.82rem; opacity:.88; }}
  .ch-banner-btn {{ background:rgba(255,255,255,.2); border:1.5px solid rgba(255,255,255,.5); color:#fff; border-radius:8px; padding:8px 18px; font-size:.84rem; font-weight:700; text-decoration:none; transition:background .2s; white-space:nowrap; }}
  .ch-banner-btn:hover {{ background:rgba(255,255,255,.35); color:#fff; }}

  .ch-child-card {{ background:#fff; border-radius:14px; box-shadow:0 2px 12px rgba(0,0,0,.08); margin-bottom:18px; overflow:hidden; border-left:4px solid #e65100; }}
  .ch-child-header {{ background:#fff8f0; padding:12px 18px; display:flex; align-items:center; gap:12px; border-bottom:1px solid #ffe0b2; flex-wrap:wrap; }}
  .ch-child-avatar {{ width:38px; height:38px; border-radius:50%; background:linear-gradient(135deg,#e65100,#ff8f00); display:flex; align-items:center; justify-content:center; font-size:1rem; font-weight:800; color:#fff; flex-shrink:0; }}
  .ch-child-name {{ font-size:.92rem; font-weight:700; color:#bf360c; }}
  .ch-dose-count {{ margin-left:auto; background:#fff3e0; color:#e65100; padding:3px 12px; border-radius:20px; font-size:.76rem; font-weight:700; border:1px solid #ffcc80; }}

  .ch-table {{ width:100%; border-collapse:collapse; font-size:.84rem; }}
  .ch-table thead th {{ background:#fff3e0; color:#bf360c; padding:9px 14px; font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.4px; border-bottom:2px solid #ffcc80; white-space:nowrap; }}
  .ch-table tbody td {{ padding:10px 14px; border-bottom:1px solid #fff3e0; vertical-align:top; }}
  .ch-table tbody tr:last-child td {{ border-bottom:none; }}
  .ch-table tbody tr:hover {{ background:#fff8f0; }}
  .ch-hosp-name {{ font-weight:600; color:#bf360c; font-size:.84rem; }}
  .ch-hosp-addr {{ font-size:.76rem; color:#64748b; margin-top:3px; display:flex; align-items:flex-start; gap:4px; }}
  .badge-dose-num {{ background:#e3f2fd; color:#1565c0; padding:3px 10px; border-radius:20px; font-size:.75rem; font-weight:700; }}
  .badge-done {{ background:#e8f5e9; color:#2e7d32; padding:3px 10px; border-radius:20px; font-size:.75rem; font-weight:700; }}

  .ch-empty {{ text-align:center; padding:32px 20px; background:#fff; border-radius:14px; box-shadow:0 2px 10px rgba(0,0,0,.06); }}
  .ch-empty i  {{ font-size:2.2rem; color:#a5d6a7; margin-bottom:10px; display:block; }}
  .ch-empty p  {{ font-size:.88rem; color:#64748b; margin:0; }}

  @media (max-width: 991px) {{
    .sidebar {{ transform: translateX(-100%); }}
    .sidebar.open {{ transform: translateX(0); }}
    .sidebar-overlay.open {{ display: block; }}
    .main {{ margin-left: 0; }}
    .hamburger {{ display: block; }}
  }}
  @media (max-width: 640px) {{
    .main {{ padding: 16px 12px; }}
    .welcome-card {{ padding: 20px 18px; }}
    .stat-card {{ padding: 14px 12px; gap: 12px; }}
    .stat-num {{ font-size: 1.4rem; }}
    .ch-table {{ font-size: .78rem; }}
    .ch-table thead th, .ch-table tbody td {{ padding: 8px 10px; }}
  }}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-left">
    <button class="hamburger" onclick="toggleSidebar()" aria-label="Open menu">
      <i class="fa fa-bars"></i>
    </button>
    <img src="./images/logo.jpg" alt="logo" onerror="this.style.display='none'">
    <div><span class="brand">Child Vaccination</span></div>
  </div>
  <div class="topbar-right">
    <h4>Parent Portal</h4>
  </div>
</div>

<div class="sidebar-overlay" id="overlay" onclick="toggleSidebar()"></div>

<nav class="sidebar" id="sidebar">
  <div class="sidebar-label">Menu</div>
  <a href="parent_dash.py?parent_id={hid}" class="nav-link active"><i class="fa fa-gauge"></i> Dashboard</a>
  <a href="parent_profile.py?parent_id={hid}" class="nav-link"><i class="fa fa-user"></i> My Profile</a>
  <hr class="sidebar-divider">
  <details class="sidebar-group">
    <summary><i class="fa-solid fa-child"></i> Child<i class="fa fa-chevron-right caret"></i></summary>
    <div class="sub-links">
      <a href="parentaddchild.py?parent_id={hid}"><i class="fa fa-plus"></i> Add Child</a>
      <a href="parentviewchild.py?parent_id={hid}"><i class="fa fa-eye"></i> View Child</a>
    </div>
  </details>
  <hr class="sidebar-divider">
  <details class="sidebar-group">
    <summary><i class="fa-solid fa-calendar-check"></i> Appointments<i class="fa fa-chevron-right caret"></i></summary>
    <div class="sub-links">
      <a href="parentaddappointments.py?parent_id={hid}"><i class="fa fa-plus"></i> Add Appointment</a>
      <a href="parentpendingappointments.py?parent_id={hid}"><i class="fa fa-clock"></i> Pending</a>
      <a href="parentcompletedappointments.py?parent_id={hid}"><i class="fa fa-circle-check"></i> Completed</a>
    </div>
  </details>
  <hr class="sidebar-divider">
  <a href="parentvaccinehistory.py?parent_id={hid}" class="nav-link">
    <i class="fa-solid fa-hospital"></i> Vaccine History
  </a>
  <hr class="sidebar-divider">
  <a href="parentnotify.py?parent_id={hid}" class="nav-link"><i class="fa-solid fa-bell"></i> Notifications</a>
  <hr class="sidebar-divider">
  <a href="parentfeedback.py?parent_id={hid}" class="nav-link"><i class="fa-solid fa-star"></i> Feedback</a>
  <hr class="sidebar-divider">
  <a href="home.py" class="nav-link" style="color:#ef9a9a;"><i class="fa fa-right-from-bracket"></i> Logout</a>
</nav>

<main class="main">

  <div class="welcome-card">
    <h3>Welcome back, {parent_name}! &#128075;</h3>
    <p>Manage your children's vaccination records and appointments from here.</p>
  </div>

  <p class="section-label">Overview</p>
  <div class="row g-3 mb-4">
    <div class="col-6 col-lg-3">
      <a href="parentviewchild.py?parent_id={hid}" class="stat-card" style="border-bottom-color:#2e7d32;">
        <div class="stat-icon" style="background:#e8f5e9;"><i class="fa-solid fa-child" style="color:#2e7d32;"></i></div>
        <div><p class="stat-num" style="color:#2e7d32;">{child_count}</p><p class="stat-label">My Children</p></div>
      </a>
    </div>
    <div class="col-6 col-lg-3">
      <a href="parentpendingappointments.py?parent_id={hid}" class="stat-card" style="border-bottom-color:#e65100;">
        <div class="stat-icon" style="background:#fff3e0;"><i class="fa-solid fa-clock" style="color:#e65100;"></i></div>
        <div><p class="stat-num" style="color:#e65100;">{pending_appts}</p><p class="stat-label">Pending</p></div>
      </a>
    </div>
    <div class="col-6 col-lg-3">
      <a href="parentpendingappointments.py?parent_id={hid}" class="stat-card" style="border-bottom-color:#1565c0;">
        <div class="stat-icon" style="background:#e3f2fd;"><i class="fa-solid fa-check" style="color:#1565c0;"></i></div>
        <div><p class="stat-num" style="color:#1565c0;">{confirmed_appts}</p><p class="stat-label">Confirmed</p></div>
      </a>
    </div>
    <div class="col-6 col-lg-3">
      <a href="parentcompletedappointments.py?parent_id={hid}" class="stat-card" style="border-bottom-color:#6a1b9a;">
        <div class="stat-icon" style="background:#f3e5f5;"><i class="fa-solid fa-circle-check" style="color:#6a1b9a;"></i></div>
        <div><p class="stat-num" style="color:#6a1b9a;">{completed_appts}</p><p class="stat-label">Completed</p></div>
      </a>
    </div>
  </div>

  <!-- ===== CROSS-HOSPITAL HISTORY SECTION ===== -->
  <p class="section-label">Previous Doses from Other Hospitals</p>
""")

if cross_summary:
    print(f"""
  <div class="ch-banner">
    <div class="ch-banner-left">
      <div class="ch-banner-icon"><i class="fa-solid fa-hospital"></i></div>
      <div>
        <h5>Your child{'ren have' if len(cross_summary) > 1 else ' has'} {total_cross_doses} dose{'s' if total_cross_doses != 1 else ''} recorded at other hospitals</h5>
        <p>These are doses given before the current hospital appointment. The hospital and admin can also see this.</p>
      </div>
    </div>
    <a href="parentvaccinehistory.py?parent_id={hid}" class="ch-banner-btn">
      <i class="fa-solid fa-arrow-right me-1"></i> View Full History
    </a>
  </div>
""")

    for child in cross_summary:
        initial = child["child_name"][0].upper() if child["child_name"] else "?"
        count   = len(child["doses"])
        print(f"""
  <div class="ch-child-card">
    <div class="ch-child-header">
      <div class="ch-child-avatar">{initial}</div>
      <div>
        <div class="ch-child-name"><i class="fa-solid fa-child" style="font-size:.8rem;margin-right:5px;"></i>{child["child_name"]}</div>
        <div style="font-size:.75rem;color:#78909c;margin-top:2px;">Doses administered at other hospitals</div>
      </div>
      <div class="ch-dose-count"><i class="fa-solid fa-syringe" style="font-size:.7rem;margin-right:4px;"></i>{count} Dose{'s' if count != 1 else ''}</div>
    </div>
    <div style="overflow-x:auto;">
      <table class="ch-table">
        <thead>
          <tr>
            <th>Dose No.</th>
            <th>Vaccine Name</th>
            <th>Hospital Name &amp; Address</th>
            <th>Date Given</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
""")
        for d in child["doses"]:
            print(f"""
          <tr>
            <td><span class="badge-dose-num">Dose {d["dose_number"]}</span></td>
            <td><strong>{d["vaccine_name"]}</strong></td>
            <td>
              <div class="ch-hosp-name">
                <i class="fa-solid fa-hospital" style="font-size:.78rem;margin-right:5px;"></i>{d["hospital_name"]}
              </div>
              <div class="ch-hosp-addr">
                <i class="fa-solid fa-location-dot" style="font-size:.74rem;margin-top:2px;"></i>
                <span>{d["address"]}</span>
              </div>
            </td>
            <td style="white-space:nowrap;">{d["date_given"]}</td>
            <td><span class="badge-done">{d["status"].capitalize()}</span></td>
          </tr>
""")
        print("        </tbody>\n      </table>\n    </div>\n  </div>")

else:
    print("""
  <div class="ch-empty">
    <i class="fa-solid fa-circle-check"></i>
    <p>All your children's doses have been administered at their registered hospital. No cross-hospital records found.</p>
  </div>
""")

print(f"""
  <!-- Quick Access -->
  <p class="section-label" style="margin-top:32px;">Quick Access</p>
  <div class="row g-3">
    <div class="col-6 col-sm-4 col-md-3">
      <a href="parent_profile.py?parent_id={hid}" class="quick-link">
        <div class="ql-icon" style="background:#e3f2fd;"><i class="fa fa-user" style="color:#1565c0;"></i></div>
        <span>My Profile</span>
      </a>
    </div>
    <div class="col-6 col-sm-4 col-md-3">
      <a href="parentaddchild.py?parent_id={hid}" class="quick-link">
        <div class="ql-icon" style="background:#e8f5e9;"><i class="fa-solid fa-child-reaching" style="color:#2e7d32;"></i></div>
        <span>Add Child</span>
      </a>
    </div>
    <div class="col-6 col-sm-4 col-md-3">
      <a href="parentviewchild.py?parent_id={hid}" class="quick-link">
        <div class="ql-icon" style="background:#fff3e0;"><i class="fa fa-eye" style="color:#e65100;"></i></div>
        <span>View Children</span>
      </a>
    </div>
    <div class="col-6 col-sm-4 col-md-3">
      <a href="parentaddappointments.py?parent_id={hid}" class="quick-link">
        <div class="ql-icon" style="background:#fce4ec;"><i class="fa fa-calendar-plus" style="color:#c62828;"></i></div>
        <span>Add Appointment</span>
      </a>
    </div>
    <div class="col-6 col-sm-4 col-md-3">
      <a href="parentpendingappointments.py?parent_id={hid}" class="quick-link">
        <div class="ql-icon" style="background:#fff8e1;"><i class="fa fa-hourglass-half" style="color:#f57f17;"></i></div>
        <span>Pending Appts</span>
      </a>
    </div>
    <div class="col-6 col-sm-4 col-md-3">
      <a href="parentcompletedappointments.py?parent_id={hid}" class="quick-link">
        <div class="ql-icon" style="background:#f3e5f5;"><i class="fa fa-circle-check" style="color:#6a1b9a;"></i></div>
        <span>Completed Appts</span>
      </a>
    </div>
    <div class="col-6 col-sm-4 col-md-3">
      <a href="parentvaccinehistory.py?parent_id={hid}" class="quick-link">
        <div class="ql-icon" style="background:#fff3e0;"><i class="fa-solid fa-hospital" style="color:#e65100;"></i></div>
        <span>Vaccine History</span>
      </a>
    </div>
    <div class="col-6 col-sm-4 col-md-3">
      <a href="parentnotify.py?parent_id={hid}" class="quick-link">
        <div class="ql-icon" style="background:#e8eaf6;"><i class="fa fa-bell" style="color:#283593;"></i></div>
        <span>Notifications</span>
      </a>
    </div>
  </div>

</main>

<script>
function toggleSidebar() {{
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('overlay').classList.toggle('open');
}}
</script>
</body>
</html>
""")

con.close()