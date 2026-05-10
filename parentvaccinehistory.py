#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
print("Content-Type: text/html\r\n\r\n")

import cgi, cgitb, pymysql, sys
from collections import OrderedDict
sys.stdout.reconfigure(encoding='utf-8')
cgitb.enable()

con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()

form = cgi.FieldStorage()
hid  = form.getvalue("parent_id")

if not hid:
    print("<script>alert('Invalid Access');location.href='home.py';</script>")
    exit()

# ---- Parent info ----
cur.execute("SELECT * FROM parent WHERE parent_id=%s", (hid,))
parent      = cur.fetchone()
parent_name = parent[1] if parent else "Parent"

# ---- All children of this parent ----
cur.execute("SELECT child_id, child_name, dob, gender, blood_group FROM children WHERE parent_id=%s", (hid,))
children_rows = cur.fetchall()

# ---- For each child fetch ALL completed doses across ALL hospitals ----
# We show every completed dose with the hospital that administered it so the
# parent can see the complete picture across all hospitals in one timeline.
history = OrderedDict()   # child_id -> dict

for child_id, child_name, dob, gender, blood_group in children_rows:
    cur.execute("""
        SELECT
            v.dose_number,
            v.vaccine_name,
            h.hospital_name,
            h.address,
            cv.taken_date,
            cv.appointment_date,
            cv.status,
            cv.hospital_id
        FROM child_vaccine cv
        LEFT JOIN vaccine  v ON cv.vaccine_id  = v.vaccine_id
        LEFT JOIN hospital h ON cv.hospital_id = h.hospital_id
        WHERE cv.child_id = %s
          AND h.hospital_id IS NOT NULL
          AND LOWER(TRIM(cv.status)) IN ('completed','confirmed','taken')
        ORDER BY v.dose_number ASC
    """, (child_id,))

    all_doses = cur.fetchall()

    # Identify the current/primary hospital (from pending/notified/confirmed appointment)
    cur.execute("""
        SELECT cv.hospital_id, h.hospital_name
        FROM child_vaccine cv
        LEFT JOIN hospital h ON cv.hospital_id = h.hospital_id
        WHERE cv.child_id = %s
          AND LOWER(TRIM(cv.status)) IN ('pending','notified','confirmed')
        LIMIT 1
    """, (child_id,))
    primary_row         = cur.fetchone()
    primary_hosp_id     = primary_row[0] if primary_row else None
    primary_hosp_name   = primary_row[1] if primary_row else None

    doses_current = []   # doses at the current/primary hospital
    doses_other   = []   # doses at other hospitals

    for d in all_doses:
        date_given = str(d[4]) if d[4] else (str(d[5]) if d[5] else "-")
        entry = {
            "dose_number"  : d[0] if d[0] else "-",
            "vaccine_name" : d[1] if d[1] else "Unknown",
            "hospital_name": d[2] if d[2] else "Unknown Hospital",
            "address"      : d[3] if d[3] else "Address not available",
            "date_given"   : date_given,
            "status"       : d[6] if d[6] else "-",
            "hospital_id"  : d[7],
            "is_other"     : (primary_hosp_id is not None and d[7] != primary_hosp_id),
        }
        if entry["is_other"]:
            doses_other.append(entry)
        else:
            doses_current.append(entry)

    if all_doses:   # only include children that have at least one completed dose
        history[child_id] = {
            "child_name"        : child_name,
            "dob"               : str(dob) if dob else "-",
            "gender"            : gender   or "-",
            "blood_group"       : blood_group or "-",
            "primary_hosp_name" : primary_hosp_name or "Not assigned",
            "doses_current"     : doses_current,
            "doses_other"       : doses_other,
            "all_doses"         : doses_current + doses_other,
        }

total_other = sum(len(v["doses_other"]) for v in history.values())

print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vaccine History</title>
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
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Segoe UI',sans-serif; background:var(--bg); color:#1e293b; }}

  .topbar {{ position:fixed; top:0; left:0; right:0; height:var(--topbar-h); background:#0d1b2a; display:flex; align-items:center; justify-content:space-between; padding:0 16px; z-index:1100; box-shadow:0 2px 10px rgba(0,0,0,.3); }}
  .topbar-left {{ display:flex; align-items:center; gap:12px; }}
  .topbar img {{ height:40px; width:40px; border-radius:50%; border:2px solid rgba(255,255,255,.4); object-fit:cover; }}
  .topbar .brand {{ color:#fff; font-size:1rem; font-weight:700; }}
  .topbar-right h4 {{ color:white; font-size:.85rem; padding:6px 14px; border:1px solid #37474f; border-radius:6px; }}
  .hamburger {{ background:none; border:none; color:#fff; font-size:1.4rem; cursor:pointer; padding:4px 8px; border-radius:6px; display:none; }}
  .hamburger:hover {{ background:rgba(255,255,255,.1); }}

  .sidebar {{ position:fixed; top:var(--topbar-h); left:0; width:var(--sidebar-w); height:calc(100vh - var(--topbar-h)); background:#0d1b2a; overflow-y:auto; z-index:1000; transition:transform .3s ease; padding:16px 12px 24px; scrollbar-width:thin; scrollbar-color:#1e3a5f transparent; }}
  .sidebar-label {{ color:#546e7a; font-size:.68rem; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; padding:12px 8px 4px; }}
  .sidebar .nav-link {{ color:#b0bec5; border-radius:8px; padding:9px 12px; font-size:.87rem; display:flex; align-items:center; gap:10px; text-decoration:none; transition:all .2s; margin-bottom:2px; }}
  .sidebar .nav-link i {{ width:18px; text-align:center; font-size:.9rem; }}
  .sidebar .nav-link:hover, .sidebar .nav-link.active {{ background:var(--primary); color:#fff; }}
  .sidebar-group summary {{ list-style:none; color:#b0bec5; padding:9px 12px; border-radius:8px; display:flex; align-items:center; gap:10px; cursor:pointer; font-size:.87rem; transition:background .2s; margin-bottom:2px; user-select:none; }}
  .sidebar-group summary::-webkit-details-marker {{ display:none; }}
  .sidebar-group summary:hover {{ background:#1c2d3e; color:#fff; }}
  .sidebar-group summary .caret {{ margin-left:auto; transition:transform .25s; font-size:.75rem; }}
  .sidebar-group[open] summary .caret {{ transform:rotate(90deg); }}
  .sidebar-group[open] summary {{ color:#fff; background:#1c2d3e; }}
  .sub-links {{ padding:4px 0 4px 28px; }}
  .sub-links a {{ display:flex; align-items:center; gap:8px; color:#78909c; font-size:.83rem; padding:7px 10px; border-radius:6px; text-decoration:none; transition:all .2s; margin-bottom:1px; }}
  .sub-links a:hover {{ color:#fff; background:rgba(255,255,255,.07); }}
  .sidebar-divider {{ border:none; border-top:1px solid #1c2d3e; margin:10px 0; }}
  .sidebar-overlay {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,.55); z-index:999; backdrop-filter:blur(2px); }}

  .main {{ margin-left:var(--sidebar-w); margin-top:var(--topbar-h); padding:28px 24px; min-height:calc(100vh - var(--topbar-h)); transition:margin-left .3s; }}

  .page-header {{ display:flex; align-items:center; gap:14px; margin-bottom:20px; }}
  .page-header-icon {{ background:linear-gradient(135deg,#e65100,#ff8f00); color:#fff; width:48px; height:48px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:1.2rem; flex-shrink:0; box-shadow:0 4px 12px rgba(230,81,0,.3); }}
  .page-header h4 {{ font-size:1.2rem; font-weight:700; margin:0 0 2px; }}
  .page-header p  {{ font-size:.85rem; color:#64748b; margin:0; }}

  /* summary strip */
  .summary-strip {{ background:#fff; border-radius:12px; padding:14px 20px; margin-bottom:22px; box-shadow:0 2px 10px rgba(0,0,0,.06); display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
  .strip-badge {{ padding:4px 14px; border-radius:20px; font-size:.84rem; font-weight:700; }}
  .strip-orange {{ background:#fff3e0; color:#e65100; }}
  .strip-blue   {{ background:#e3f2fd; color:#1565c0; }}

  /* filter bar */
  .filter-bar {{ display:flex; gap:10px; margin-bottom:18px; flex-wrap:wrap; }}
  .filter-btn {{ padding:7px 18px; border-radius:20px; font-size:.82rem; font-weight:600; border:1.5px solid #dde3ea; background:#fff; color:#64748b; cursor:pointer; transition:all .2s; }}
  .filter-btn.active, .filter-btn:hover {{ background:#e65100; border-color:#e65100; color:#fff; }}

  /* child cards */
  .child-history-card {{ background:#fff; border-radius:14px; box-shadow:0 2px 14px rgba(0,0,0,.08); margin-bottom:28px; overflow:hidden; }}

  .child-history-header {{ padding:14px 20px; display:flex; align-items:center; gap:14px; flex-wrap:wrap; border-bottom:1px solid #f1f5f9; }}
  .child-avatar {{ width:44px; height:44px; border-radius:50%; background:linear-gradient(135deg,#e65100,#ff8f00); display:flex; align-items:center; justify-content:center; font-size:1.1rem; font-weight:800; color:#fff; flex-shrink:0; }}
  .child-info-name {{ font-size:.96rem; font-weight:700; color:#1e293b; }}
  .child-info-sub  {{ font-size:.76rem; color:#64748b; margin-top:2px; }}
  .child-hosp-tag  {{ margin-left:auto; background:#e3f2fd; color:#1565c0; padding:4px 12px; border-radius:20px; font-size:.76rem; font-weight:700; border:1px solid #b3d1f7; white-space:nowrap; }}

  /* tabs */
  .htabs {{ display:flex; border-bottom:2px solid #f1f5f9; background:#fafbfc; }}
  .htab  {{ flex:1; background:transparent; border:none; border-bottom:3px solid transparent; margin-bottom:-2px; padding:11px 10px; font-family:'Segoe UI',sans-serif; font-size:.83rem; font-weight:600; color:#64748b; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:6px; transition:all .2s; white-space:nowrap; }}
  .htab:hover {{ color:#e65100; background:#fff3e0; }}
  .htab.active {{ color:#e65100; border-bottom-color:#e65100; background:#fff8f0; }}
  .hpanel {{ display:none; padding:20px; }}
  .hpanel.active {{ display:block; }}

  /* dose table */
  .dose-table {{ width:100%; border-collapse:collapse; font-size:.85rem; }}
  .dose-table thead th {{ background:#f8fafc; color:#475569; font-weight:700; font-size:.74rem; letter-spacing:.4px; text-transform:uppercase; padding:10px 14px; border-bottom:2px solid #f1f5f9; white-space:nowrap; }}
  .dose-table tbody td {{ padding:11px 14px; border-bottom:1px solid #f1f5f9; vertical-align:top; }}
  .dose-table tbody tr:last-child td {{ border-bottom:none; }}
  .dose-table tbody tr:hover {{ background:#f8fafc; }}

  /* other-hospital rows get a warm tint */
  .dose-table tbody tr.other-row {{ background:#fffbf0; }}
  .dose-table tbody tr.other-row:hover {{ background:#fff3e0; }}

  .badge-dose {{ background:#e3f2fd; color:#1565c0; padding:3px 10px; border-radius:20px; font-size:.75rem; font-weight:700; }}
  .badge-other-hosp {{ background:#fff3e0; color:#e65100; padding:3px 10px; border-radius:20px; font-size:.72rem; font-weight:700; }}
  .badge-current-hosp {{ background:#e8f5e9; color:#2e7d32; padding:3px 10px; border-radius:20px; font-size:.72rem; font-weight:700; }}
  .badge-done {{ background:#e8f5e9; color:#2e7d32; padding:3px 10px; border-radius:20px; font-size:.75rem; font-weight:700; }}

  .hosp-name {{ font-weight:600; color:#bf360c; }}
  .hosp-addr {{ font-size:.77rem; color:#64748b; margin-top:3px; display:flex; align-items:flex-start; gap:4px; }}

  /* timeline (other-hospital only panel) */
  .timeline {{ position:relative; padding-left:28px; }}
  .timeline::before {{ content:''; position:absolute; left:10px; top:0; bottom:0; width:2px; background:#ffe082; border-radius:2px; }}
  .tl-item {{ position:relative; margin-bottom:20px; }}
  .tl-dot  {{ position:absolute; left:-23px; top:4px; width:14px; height:14px; border-radius:50%; background:#e65100; border:2px solid #fff; box-shadow:0 0 0 2px #e65100; }}
  .tl-card {{ background:#fff8f0; border:1px solid #ffe0b2; border-radius:10px; padding:13px 16px; }}
  .tl-vaccine {{ font-size:.9rem; font-weight:700; color:#bf360c; }}
  .tl-meta    {{ font-size:.78rem; color:#64748b; margin-top:5px; display:flex; flex-wrap:wrap; gap:8px; }}
  .tl-meta span {{ display:flex; align-items:center; gap:4px; }}
  .tl-hosp    {{ font-size:.82rem; color:#e65100; font-weight:600; margin-top:6px; }}
  .tl-addr    {{ font-size:.76rem; color:#94a3b8; margin-top:2px; }}

  .no-doses {{ text-align:center; padding:32px 20px; color:#94a3b8; font-size:.88rem; }}
  .no-doses i {{ font-size:2rem; color:#a5d6a7; display:block; margin-bottom:10px; }}

  .empty-state {{ text-align:center; padding:60px 20px; background:#fff; border-radius:14px; box-shadow:0 2px 12px rgba(0,0,0,.07); }}
  .empty-state i {{ font-size:3rem; color:#a5d6a7; margin-bottom:16px; display:block; }}
  .empty-state h5 {{ color:#64748b; font-weight:600; }}
  .empty-state p  {{ font-size:.88rem; color:#94a3b8; }}

  @media (max-width:991px) {{
    .sidebar {{ transform:translateX(-100%); }}
    .sidebar.open {{ transform:translateX(0); }}
    .sidebar-overlay.open {{ display:block; }}
    .main {{ margin-left:0; }}
    .hamburger {{ display:block; }}
  }}
  @media (max-width:640px) {{
    .main {{ padding:16px 12px; }}
    .dose-table {{ font-size:.78rem; }}
    .dose-table thead th, .dose-table tbody td {{ padding:8px 10px; }}
    .htabs {{ overflow-x:auto; }}
    .htab  {{ font-size:.76rem; padding:9px 8px; }}
  }}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-left">
    <button class="hamburger" onclick="toggleSidebar()"><i class="fa fa-bars"></i></button>
    <img src="./images/logo.jpg" alt="logo" onerror="this.style.display='none'">
    <div><span class="brand">Child Vaccination</span></div>
  </div>
  <div class="topbar-right"><h4>Parent Portal</h4></div>
</div>

<div class="sidebar-overlay" id="overlay" onclick="toggleSidebar()"></div>

<nav class="sidebar" id="sidebar">
  <div class="sidebar-label">Menu</div>
  <a href="parent_dash.py?parent_id={hid}" class="nav-link"><i class="fa fa-gauge"></i> Dashboard</a>
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
  <a href="parentvaccinehistory.py?parent_id={hid}" class="nav-link active"><i class="fa-solid fa-hospital"></i> Vaccine History</a>
  <hr class="sidebar-divider">
  <a href="parentnotify.py?parent_id={hid}" class="nav-link"><i class="fa-solid fa-bell"></i> Notifications</a>
  <hr class="sidebar-divider">
  <a href="parentfeedback.py?parent_id={hid}" class="nav-link"><i class="fa-solid fa-star"></i> Feedback</a>
  <hr class="sidebar-divider">
  <a href="home.py" class="nav-link" style="color:#ef9a9a;"><i class="fa fa-right-from-bracket"></i> Logout</a>
</nav>

<main class="main">

  <div class="page-header">
    <div class="page-header-icon"><i class="fa-solid fa-hospital"></i></div>
    <div>
      <h4>Vaccine History — All Hospitals</h4>
      <p>Complete dose records for all your children, across every hospital</p>
    </div>
  </div>

  <div class="summary-strip">
    <i class="fa-solid fa-children" style="color:#64748b;"></i>
    <span style="font-size:.9rem;color:#475569;font-weight:600;">{len(history)} Child{'ren' if len(history) != 1 else ''} with completed doses</span>
    <span class="strip-badge strip-orange"><i class="fa-solid fa-hospital" style="font-size:.75rem;margin-right:4px;"></i>{total_other} dose{'s' if total_other != 1 else ''} from other hospitals</span>
    <span class="strip-badge strip-blue">All records shown below</span>
  </div>

""")

if history:
    for idx, (child_id, cdata) in enumerate(history.items()):
        initial    = cdata["child_name"][0].upper() if cdata["child_name"] else "?"
        other_cnt  = len(cdata["doses_other"])
        cur_cnt    = len(cdata["doses_current"])
        all_cnt    = len(cdata["all_doses"])

        print(f"""
  <div class="child-history-card">
    <div class="child-history-header">
      <div class="child-avatar">{initial}</div>
      <div>
        <div class="child-info-name">
          <i class="fa-solid fa-child" style="font-size:.82rem;margin-right:5px;opacity:.7;"></i>
          {cdata["child_name"]}
          {'&nbsp;<span style="background:#fff3e0;color:#e65100;padding:2px 9px;border-radius:20px;font-size:.72rem;font-weight:700;"><i class="fa-solid fa-hospital" style="font-size:.68rem;margin-right:3px;"></i>' + str(other_cnt) + ' other hosp.</span>' if other_cnt > 0 else ''}
        </div>
        <div class="child-info-sub">
          DOB: {cdata["dob"]} &bull; {cdata["gender"]} &bull; Blood: {cdata["blood_group"]}
        </div>
      </div>
      <div class="child-hosp-tag">
        <i class="fa-solid fa-hospital" style="margin-right:5px;"></i>{cdata["primary_hosp_name"]}
      </div>
    </div>

    <div class="htabs" id="htabs{child_id}">
      <button class="htab active" onclick="switchHTab({child_id},'all')">
        <i class="fa-solid fa-list"></i> All Doses
        <span style="background:#e3f2fd;color:#1565c0;padding:1px 8px;border-radius:12px;font-size:.72rem;margin-left:4px;">{all_cnt}</span>
      </button>
      <button class="htab" onclick="switchHTab({child_id},'other')" style="{'color:#e65100;' if other_cnt > 0 else ''}">
        <i class="fa-solid fa-hospital"></i> Other Hospital Doses
        {'<span style="background:#fff3e0;color:#e65100;padding:1px 8px;border-radius:12px;font-size:.72rem;margin-left:4px;">' + str(other_cnt) + '</span>' if other_cnt > 0 else ''}
      </button>
      <button class="htab" onclick="switchHTab({child_id},'current')">
        <i class="fa-solid fa-circle-check"></i> Current Hospital
        <span style="background:#e8f5e9;color:#2e7d32;padding:1px 8px;border-radius:12px;font-size:.72rem;margin-left:4px;">{cur_cnt}</span>
      </button>
    </div>

    <!-- ALL DOSES PANEL -->
    <div class="hpanel active" id="hp{child_id}-all">
      <div style="overflow-x:auto;">
        <table class="dose-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Vaccine Name</th>
              <th>Dose No.</th>
              <th>Hospital Name &amp; Address</th>
              <th>Date Given</th>
              <th>Type</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
""")
        # Sort all doses by dose number
        sorted_all = sorted(cdata["all_doses"], key=lambda x: (x["dose_number"] if isinstance(x["dose_number"], int) else 999))
        for i, d in enumerate(sorted_all, 1):
            row_class = "other-row" if d["is_other"] else ""
            tag       = '<span class="badge-other-hosp"><i class="fa-solid fa-hospital" style="font-size:.68rem;margin-right:3px;"></i>Other</span>' if d["is_other"] else '<span class="badge-current-hosp"><i class="fa-solid fa-check" style="font-size:.68rem;margin-right:3px;"></i>Current</span>'
            print(f"""
            <tr class="{row_class}">
              <td style="color:#94a3b8;font-weight:600;">{i}</td>
              <td><strong>{d["vaccine_name"]}</strong></td>
              <td><span class="badge-dose">Dose {d["dose_number"]}</span></td>
              <td>
                <div class="hosp-name"><i class="fa-solid fa-hospital" style="font-size:.78rem;margin-right:5px;"></i>{d["hospital_name"]}</div>
                <div class="hosp-addr"><i class="fa-solid fa-location-dot" style="font-size:.74rem;margin-top:2px;"></i><span>{d["address"]}</span></div>
              </td>
              <td style="white-space:nowrap;">{d["date_given"]}</td>
              <td>{tag}</td>
              <td><span class="badge-done">{d["status"].capitalize()}</span></td>
            </tr>
""")
        print("          </tbody>\n        </table>\n      </div>\n    </div>")

        # OTHER HOSPITAL DOSES PANEL — timeline view
        print(f'    <div class="hpanel" id="hp{child_id}-other">')
        if cdata["doses_other"]:
            print('      <div class="timeline">')
            for d in cdata["doses_other"]:
                print(f"""
        <div class="tl-item">
          <div class="tl-dot"></div>
          <div class="tl-card">
            <div class="tl-vaccine">
              <i class="fa-solid fa-syringe" style="font-size:.82rem;margin-right:6px;"></i>
              {d["vaccine_name"]} &mdash; <span class="badge-dose">Dose {d["dose_number"]}</span>
            </div>
            <div class="tl-meta">
              <span><i class="fa-solid fa-calendar"></i> {d["date_given"]}</span>
              <span><i class="fa-solid fa-circle-check" style="color:#2e7d32;"></i> {d["status"].capitalize()}</span>
            </div>
            <div class="tl-hosp">
              <i class="fa-solid fa-hospital" style="font-size:.78rem;margin-right:5px;"></i>{d["hospital_name"]}
            </div>
            <div class="tl-addr">
              <i class="fa-solid fa-location-dot" style="font-size:.74rem;margin-right:4px;"></i>{d["address"]}
            </div>
          </div>
        </div>
""")
            print('      </div>')
        else:
            print('      <div class="no-doses"><i class="fa-solid fa-circle-check"></i>No doses from other hospitals for this child.</div>')
        print('    </div>')

        # CURRENT HOSPITAL PANEL
        print(f'    <div class="hpanel" id="hp{child_id}-current">')
        if cdata["doses_current"]:
            print('      <div style="overflow-x:auto;">')
            print('        <table class="dose-table"><thead><tr><th>#</th><th>Vaccine Name</th><th>Dose No.</th><th>Hospital</th><th>Date Given</th><th>Status</th></tr></thead><tbody>')
            for i, d in enumerate(cdata["doses_current"], 1):
                print(f"""
            <tr>
              <td style="color:#94a3b8;font-weight:600;">{i}</td>
              <td><strong>{d["vaccine_name"]}</strong></td>
              <td><span class="badge-dose">Dose {d["dose_number"]}</span></td>
              <td>
                <div class="hosp-name" style="color:#2e7d32;"><i class="fa-solid fa-hospital" style="font-size:.78rem;margin-right:5px;"></i>{d["hospital_name"]}</div>
                <div class="hosp-addr"><i class="fa-solid fa-location-dot" style="font-size:.74rem;margin-top:2px;"></i><span>{d["address"]}</span></div>
              </td>
              <td style="white-space:nowrap;">{d["date_given"]}</td>
              <td><span class="badge-done">{d["status"].capitalize()}</span></td>
            </tr>
""")
            print('          </tbody></table>\n      </div>')
        else:
            print('      <div class="no-doses"><i class="fa-solid fa-circle-check"></i>No completed doses at the current hospital yet.</div>')
        print('    </div>')

        print("  </div>")   # child-history-card

else:
    print("""
  <div class="empty-state">
    <i class="fa-solid fa-syringe"></i>
    <h5>No Completed Doses Found</h5>
    <p>Your children's completed vaccine records will appear here once doses are administered.</p>
  </div>
""")

print(f"""
</main>

<script>
function toggleSidebar() {{
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('overlay').classList.toggle('open');
}}
function switchHTab(cid, tab) {{
  const panels = ['all','other','current'];
  const btns   = document.getElementById('htabs'+cid).querySelectorAll('.htab');
  panels.forEach((p,i) => {{
    const el = document.getElementById('hp'+cid+'-'+p);
    if (el) el.classList.toggle('active', p===tab);
    if (btns[i]) btns[i].classList.toggle('active', p===tab);
  }});
}}
</script>
</body>
</html>
""")

con.close()