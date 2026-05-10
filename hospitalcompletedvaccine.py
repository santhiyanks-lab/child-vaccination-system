#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
print("Content-Type: text/html\r\n\r\n")

import cgi
import cgitb
import pymysql
import sys
from collections import OrderedDict

sys.stdout.reconfigure(encoding='utf-8')
cgitb.enable()

# ---------------- DATABASE ----------------
con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()

form = cgi.FieldStorage()
oid = form.getfirst("hospital_id")

if not oid:
    print("<h3>Invalid Hospital ID</h3>")
    exit()

hospital_id = int(oid)

# ---------------- FETCH COMPLETED APPOINTMENTS ----------------
cur.execute("""
    SELECT cv.id,
           c.child_id,
           c.child_name,
           c.dob,
           c.gender,
           c.blood_group,
           c.weight,
           c.identification_mark,
           v.vaccine_name,
           v.dose_number,
           cv.appointment_date,
           cv.appointment_time,
           p.father_name,
           p.mobile_number
    FROM child_vaccine cv
    JOIN children c ON cv.child_id = c.child_id
    JOIN vaccine v ON cv.vaccine_id = v.vaccine_id
    JOIN parent p ON c.parent_id = p.parent_id
    WHERE cv.hospital_id=%s
    AND cv.status='completed'
    ORDER BY c.child_id ASC, v.dose_number ASC
""", (hospital_id,))

rows = cur.fetchall()

# ---------------- GROUP BY CHILD ----------------
children = OrderedDict()
for row in rows:
    cv_id          = row[0]
    child_id       = row[1]
    child_name     = row[2]
    dob            = row[3]
    gender         = row[4]
    blood_group    = row[5]
    weight         = row[6]
    identification = row[7]
    vaccine_name   = row[8]
    dose_number    = row[9]
    appt_date      = row[10]
    appt_time      = row[11]
    father_name    = row[12]
    mobile         = row[13]

    if child_id not in children:
        children[child_id] = {
            "child_name"     : child_name,
            "dob"            : dob,
            "gender"         : gender,
            "blood_group"    : blood_group,
            "weight"         : weight,
            "identification" : identification,
            "father_name"    : father_name,
            "mobile"         : mobile,
            "vaccines"       : []
        }
    children[child_id]["vaccines"].append({
        "cv_id"        : cv_id,
        "vaccine_name" : vaccine_name,
        "dose_number"  : dose_number,
        "appt_date"    : appt_date,
        "appt_time"    : appt_time,
    })

# ---------------- FETCH CROSS-HOSPITAL HISTORY ----------------
# For every child in the completed list, fetch all doses given at OTHER hospitals
# regardless of status (completed/confirmed/taken) so the full picture is visible.
child_ids = list(children.keys())
cross_hospital_history = {}   # child_id -> [dose dicts]

if child_ids:
    fmt = ','.join(['%s'] * len(child_ids))
    cur.execute(f"""
        SELECT
            cv.child_id,
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
        WHERE cv.child_id IN ({fmt})
          AND cv.hospital_id != %s
          AND LOWER(TRIM(cv.status)) IN ('completed','confirmed','taken')
        ORDER BY cv.child_id ASC, v.dose_number ASC
    """, (*child_ids, hospital_id))

    for r in cur.fetchall():
        cid = r[0]
        if cid not in cross_hospital_history:
            cross_hospital_history[cid] = []
        # prefer taken_date; fall back to appointment_date
        date_given = str(r[5]) if r[5] else (str(r[6]) if r[6] else "-")
        cross_hospital_history[cid].append({
            "dose_number"  : r[1] if r[1] else "-",
            "vaccine_name" : r[2] if r[2] else "Unknown",
            "hospital_name": r[3] if r[3] else "Unknown Hospital",
            "address"      : r[4] if r[4] else "Address not available",
            "date_given"   : date_given,
            "status"       : r[7] if r[7] else "-",
        })

# ---------------- HTML ----------------
print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Completed Vaccine Appointments</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
  :root {{
    --sidebar-w: 260px;
    --topbar-h: 60px;
    --primary: #1565c0;
    --success: #2e7d32;
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
  .hamburger {{ background: none; border: none; color: #fff; font-size: 1.4rem; cursor: pointer; padding: 4px 8px; border-radius: 6px; display: none; transition: background .2s; }}
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

  .page-header {{ display: flex; align-items: center; gap: 14px; margin-bottom: 24px; }}
  .page-header-icon {{ background: linear-gradient(135deg,#2e7d32,#66bb6a); color:#fff; width:48px; height:48px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:1.2rem; flex-shrink:0; box-shadow:0 4px 12px rgba(46,125,50,.3); }}
  .page-header h4 {{ font-size: 1.2rem; font-weight: 700; margin: 0 0 2px; }}
  .page-header p {{ font-size: .85rem; color: #64748b; margin: 0; }}

  .child-card {{ background: #fff; border-radius: 14px; box-shadow: 0 2px 14px rgba(0,0,0,.08); margin-bottom: 24px; overflow: hidden; }}
  .child-card-header {{ background: linear-gradient(135deg,#1565c0,#0d47a1); color:#fff; padding:14px 20px; display:flex; align-items:center; gap:12px; flex-wrap:wrap; }}
  .child-avatar {{ width:42px; height:42px; border-radius:50%; background:rgba(255,255,255,.2); display:flex; align-items:center; justify-content:center; font-size:1.1rem; flex-shrink:0; }}
  .child-card-header h5 {{ margin:0; font-size:.95rem; font-weight:700; }}
  .child-count {{ margin-left:auto; background:rgba(255,255,255,.2); padding:3px 12px; border-radius:20px; font-size:.8rem; }}

  /* cross-hospital indicator badge in table */
  .badge-cross {{ background:#fff3e0; color:#e65100; padding:2px 9px; border-radius:20px; font-size:.72rem; font-weight:700; }}

  .vaccine-table {{ font-size: .87rem; margin: 0; }}
  .vaccine-table thead th {{ background:#f8fafc; color:#475569; font-weight:700; font-size:.78rem; letter-spacing:.5px; text-transform:uppercase; padding:12px 14px; border-color:#f1f5f9; white-space:nowrap; }}
  .vaccine-table tbody td {{ padding:11px 14px; border-color:#f1f5f9; vertical-align:middle; }}
  .vaccine-table tbody tr:hover {{ background:#f8fafc; }}

  .badge-success {{ background:#e8f5e9; color:#2e7d32; padding:4px 12px; border-radius:20px; font-size:.78rem; font-weight:700; display:inline-flex; align-items:center; gap:4px; }}
  .badge-dose {{ background:#e3f2fd; color:#1565c0; padding:3px 10px; border-radius:20px; font-size:.78rem; font-weight:700; }}
  .btn-view {{ background:#e3f2fd; color:#1565c0; border:none; border-radius:7px; padding:5px 14px; font-size:.8rem; font-weight:600; cursor:pointer; transition:all .2s; display:inline-flex; align-items:center; gap:5px; }}
  .btn-view:hover {{ background:#1565c0; color:#fff; }}

  .mobile-vaccine-card {{ display:none; background:#f8fafc; border-radius:10px; padding:14px; margin:10px 14px; border:1px solid #e2e8f0; }}
  .mvc-row {{ display:flex; justify-content:space-between; font-size:.83rem; padding:4px 0; border-bottom:1px solid #f1f5f9; gap:8px; }}
  .mvc-row:last-child {{ border:none; }}
  .mvc-label {{ color:#94a3b8; font-weight:700; font-size:.75rem; white-space:nowrap; }}
  .mvc-val {{ color:#1e293b; font-weight:500; text-align:right; }}

  .modal-content {{ border:none; border-radius:14px; box-shadow:0 8px 32px rgba(0,0,0,.15); overflow:hidden; animation:zoomIn .25s ease; }}
  @keyframes zoomIn {{ from {{ transform:scale(.92);opacity:0; }} to {{ transform:scale(1);opacity:1; }} }}
  .modal-section {{ border-radius:10px; padding:16px 18px; margin-bottom:12px; }}
  .modal-section h6 {{ font-size:.82rem; font-weight:700; letter-spacing:.8px; text-transform:uppercase; margin-bottom:12px; }}
  .info-row {{ display:flex; gap:6px; font-size:.88rem; padding:4px 0; border-bottom:1px solid rgba(0,0,0,.05); flex-wrap:wrap; }}
  .info-row:last-child {{ border:none; }}
  .info-label {{ color:#64748b; font-weight:600; min-width:140px; flex-shrink:0; }}
  .info-val {{ color:#1e293b; word-break:break-word; }}

  /* ---- Cross-hospital section inside modal ---- */
  .cross-hosp-section {{
    background: #fff8e1;
    border: 1.5px solid #ffe082;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 12px;
  }}
  .ch-title {{
    font-size: .78rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .7px;
    color: #e65100; margin-bottom: 10px;
    display: flex; align-items: center; gap: 7px;
  }}
  .alert-cross-hosp {{
    background: #fff3e0; border-left: 4px solid #e65100;
    border-radius: 6px; padding: 8px 12px;
    font-size: .82rem; color: #7c4700;
    display: flex; align-items: center; gap: 8px;
    margin-bottom: 10px;
  }}
  .cross-hosp-table {{ width:100%; border-collapse:collapse; font-size:.83rem; }}
  .cross-hosp-table thead th {{
    background: #ffe0b2; color: #bf360c;
    padding: 7px 10px; font-size: .72rem;
    font-weight: 700; text-transform: uppercase;
    letter-spacing: .4px; border-bottom: 2px solid #ffcc80;
    white-space: nowrap;
  }}
  .cross-hosp-table tbody td {{
    padding: 8px 10px; border-bottom: 1px solid #ffe082;
    color: #1e293b; vertical-align: top;
  }}
  .cross-hosp-table tbody tr:last-child td {{ border-bottom: none; }}
  .cross-hosp-table tbody tr:hover {{ background: #fff3e0; }}
  .ch-hosp-name {{ font-weight: 600; color: #bf360c; }}
  .ch-address {{ font-size: .78rem; color: #64748b; margin-top: 2px; }}
  .no-cross-hosp {{
    font-size: .83rem; color: #94a3b8;
    text-align: center; padding: 10px 0 4px;
  }}
  /* ---- end cross-hospital ---- */

  .empty-state {{ text-align:center; padding:60px 20px; background:#fff; border-radius:14px; box-shadow:0 2px 12px rgba(0,0,0,.07); }}
  .empty-state i {{ font-size:3rem; color:#cbd5e1; margin-bottom:16px; }}
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
    .page-header {{ gap: 10px; }}
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
    <button class="hamburger" onclick="toggleSidebar()" aria-label="Menu">
      <i class="fa fa-bars"></i>
    </button>
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
      <a href="hospitalpendingvaccine.py?hospital_id={oid}"><i class="fa-solid fa-clock"></i> Pending</a>
      <a href="hospitalconfirmedvaccine.py?hospital_id={oid}"><i class="fa-solid fa-check"></i> Confirmed</a>
      <a href="hospitalrescheduledvaccine.py?hospital_id={oid}"><i class="fa-solid fa-calendar-days"></i> Rescheduled</a>
      <a href="hospitalcompletedvaccine.py?hospital_id={oid}" class="active"><i class="fa-solid fa-circle-check"></i> Completed</a>
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
    <div class="page-header-icon"><i class="fa-solid fa-circle-check"></i></div>
    <div>
      <h4>Completed Vaccine Appointments</h4>
      <p>All successfully administered vaccinations &mdash; previous doses from other hospitals shown in each record</p>
    </div>
  </div>
""")

all_modals = ""

if children:
    child_num = 1
    for child_id, cdata in children.items():
        vaccine_count = len(cdata["vaccines"])
        prior_doses   = cross_hospital_history.get(child_id, [])
        prior_count   = len(prior_doses)

        # ---- Build the cross-hospital HTML block (reused in every modal for this child) ----
        if prior_doses:
            ch_alert = (
                f'<div class="alert-cross-hosp">'
                f'<i class="fa fa-triangle-exclamation"></i>'
                f'<span>This child has <strong>{prior_count} dose(s)</strong> administered '
                f'at other hospitals before coming here.</span>'
                f'</div>'
            )
            ch_rows = ""
            for pd in prior_doses:
                ch_rows += (
                    f"<tr>"
                    f"<td><span class='badge-dose'>Dose {pd['dose_number']}</span></td>"
                    f"<td><strong>{pd['vaccine_name']}</strong></td>"
                    f"<td>"
                    f"  <div class='ch-hosp-name'>"
                    f"    <i class='fa fa-hospital' style='font-size:.8rem;margin-right:5px;'></i>"
                    f"    {pd['hospital_name']}"
                    f"  </div>"
                    f"  <div class='ch-address'>"
                    f"    <i class='fa fa-location-dot' style='font-size:.75rem;margin-right:4px;'></i>"
                    f"    {pd['address']}"
                    f"  </div>"
                    f"</td>"
                    f"<td>{pd['date_given']}</td>"
                    f"</tr>"
                )
            cross_hosp_html = f"""
        <div class="cross-hosp-section">
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
              <tbody>{ch_rows}</tbody>
            </table>
          </div>
        </div>"""
        else:
            cross_hosp_html = """
        <div class="cross-hosp-section">
          <div class="ch-title">
            <i class="fa fa-hospital"></i>
            Previous Doses from Other Hospitals
          </div>
          <div class="no-cross-hosp">
            <i class="fa fa-circle-check" style="color:#1d9e75;margin-right:6px;"></i>
            No prior doses from other hospitals recorded for this child.
          </div>
        </div>"""

        # ---- Child card header ----
        prior_badge = (
            f'&nbsp;<span class="badge-cross"><i class="fa fa-hospital" style="font-size:.7rem;"></i>'
            f' {prior_count} other hosp.</span>'
            if prior_count > 0 else ""
        )

        print(f"""
  <div class="child-card">
    <div class="child-card-header">
      <div class="child-avatar"><i class="fa-solid fa-child"></i></div>
      <div>
        <h5>{child_num}. {cdata["child_name"]} {prior_badge}</h5>
        <small style="opacity:.8;">DOB: {cdata["dob"]} &nbsp;|&nbsp; {cdata["gender"]}</small>
      </div>
      <div class="child-count">{vaccine_count} Vaccine{"s" if vaccine_count != 1 else ""}</div>
    </div>

    <div class="table-responsive desktop-table">
      <table class="table vaccine-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Vaccine Name</th>
            <th>Dose</th>
            <th>Date</th>
            <th>Time</th>
            <th>Other Hosp. Doses</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
""")

        for dose_num, vaccine in enumerate(cdata["vaccines"], start=1):
            cv_id = vaccine["cv_id"]

            prior_cell = (
                f'<span class="badge-cross"><i class="fa fa-hospital" style="font-size:.7rem;"></i>'
                f' {prior_count} record(s)</span>'
                if prior_count > 0
                else '<span style="font-size:.78rem;color:#94a3b8;">None</span>'
            )

            print(f"""
          <tr>
            <td><span style="background:#f1f5f9;color:#475569;padding:3px 8px;border-radius:6px;font-weight:600;">{dose_num}</span></td>
            <td><strong>{vaccine["vaccine_name"]}</strong></td>
            <td><span class="badge-dose">Dose {vaccine["dose_number"]}</span></td>
            <td>{vaccine["appt_date"]}</td>
            <td>{vaccine["appt_time"]}</td>
            <td>{prior_cell}</td>
            <td><span class="badge-success"><i class="fa fa-check"></i> Completed</span></td>
            <td>
              <button class="btn-view" data-bs-toggle="modal" data-bs-target="#viewModal{cv_id}">
                <i class="fa fa-eye"></i> View
              </button>
            </td>
          </tr>
""")

            # ---- Build modal (cross-hospital block is the same for every dose of the same child) ----
            all_modals += f"""
<div class="modal fade" id="viewModal{cv_id}" tabindex="-1">
  <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header" style="background:linear-gradient(135deg,#2e7d32,#66bb6a);">
        <h5 class="modal-title text-white">
          <i class="fa fa-id-card me-2"></i>Appointment Details
        </h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">

        <div class="modal-section" style="background:#e3f2fd;">
          <h6 style="color:#1565c0;"><i class="fa fa-child me-2"></i>Child Information</h6>
          <div class="row g-0">
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Child Name</span><span class="info-val">{cdata["child_name"]}</span></div>
              <div class="info-row"><span class="info-label">Date of Birth</span><span class="info-val">{cdata["dob"]}</span></div>
              <div class="info-row"><span class="info-label">Gender</span><span class="info-val">{cdata["gender"]}</span></div>
            </div>
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Blood Group</span><span class="info-val">{cdata["blood_group"]}</span></div>
              <div class="info-row"><span class="info-label">Weight</span><span class="info-val">{cdata["weight"]} kg</span></div>
              <div class="info-row"><span class="info-label">Identification</span><span class="info-val">{cdata["identification"]}</span></div>
            </div>
          </div>
        </div>

        <div class="modal-section" style="background:#e8f5e9;">
          <h6 style="color:#2e7d32;"><i class="fa fa-syringe me-2"></i>Vaccine Information</h6>
          <div class="row g-0">
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Vaccine Name</span><span class="info-val">{vaccine["vaccine_name"]}</span></div>
              <div class="info-row"><span class="info-label">Dose Number</span><span class="info-val"><span class="badge-dose">Dose {vaccine["dose_number"]}</span></span></div>
            </div>
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Date</span><span class="info-val">{vaccine["appt_date"]}</span></div>
              <div class="info-row"><span class="info-label">Time</span><span class="info-val">{vaccine["appt_time"]}</span></div>
            </div>
          </div>
        </div>

        <div class="modal-section" style="background:#fff8e1;">
          <h6 style="color:#f57f17;"><i class="fa fa-user me-2"></i>Parent Information</h6>
          <div class="row g-0">
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Parent Name</span><span class="info-val">{cdata["father_name"]}</span></div>
            </div>
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Phone</span><span class="info-val">{cdata["mobile"]}</span></div>
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
</div>"""

        print("        </tbody>\n      </table>\n    </div>")

        # ---- Mobile cards ----
        print("""    <div class="mobile-cards-section" style="padding-bottom:8px;">""")
        for dose_num, vaccine in enumerate(cdata["vaccines"], start=1):
            cv_id = vaccine["cv_id"]
            print(f"""
      <div class="mobile-vaccine-card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
          <strong style="font-size:.9rem;">{vaccine["vaccine_name"]}</strong>
          <span class="badge-dose">Dose {vaccine["dose_number"]}</span>
        </div>
        <div class="mvc-row"><span class="mvc-label">Serial</span><span class="mvc-val">#{dose_num}</span></div>
        <div class="mvc-row"><span class="mvc-label">Date</span><span class="mvc-val">{vaccine["appt_date"]}</span></div>
        <div class="mvc-row"><span class="mvc-label">Time</span><span class="mvc-val">{vaccine["appt_time"]}</span></div>
        {'<div class="mvc-row"><span class="mvc-label">Other Hosp.</span><span class="mvc-val badge-cross">' + str(prior_count) + ' dose(s)</span></div>' if prior_count > 0 else ''}
        <div class="mvc-row"><span class="mvc-label">Status</span><span class="mvc-val"><span class="badge-success"><i class="fa fa-check"></i> Completed</span></span></div>
        <div style="margin-top:10px;">
          <button class="btn-view w-100" data-bs-toggle="modal" data-bs-target="#viewModal{cv_id}">
            <i class="fa fa-eye"></i> View Full Details
          </button>
        </div>
      </div>
""")
        print("    </div>")   # mobile-cards-section
        print("  </div>")     # child-card
        child_num += 1

else:
    print("""
  <div class="empty-state">
    <i class="fa-solid fa-circle-check"></i>
    <h5>No Completed Appointments</h5>
    <p>Completed vaccinations will appear here once administered.</p>
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