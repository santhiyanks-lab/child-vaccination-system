#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
print("Content-Type: text/html\r\n\r\n")

import cgi
import cgitb
import pymysql
import sys

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

# ---------------- FETCH CONFIRMED APPOINTMENTS ----------------
cur.execute("""
    SELECT cv.id,
           c.child_name,
           v.vaccine_name,
           v.dose_number,
           cv.appointment_date,
           cv.appointment_time,
           cv.status
    FROM child_vaccine cv
    JOIN children c ON cv.child_id = c.child_id
    JOIN vaccine v ON cv.vaccine_id = v.vaccine_id
    WHERE cv.hospital_id=%s
    AND cv.status='confirmed'
    ORDER BY cv.appointment_date ASC, cv.appointment_time ASC
""", (oid,))

rows = cur.fetchall()

# Fetch full details for modals
modal_details = {}
for row in rows:
    cv_id = row[0]
    cur.execute("""
        SELECT c.child_name, c.dob, c.gender, c.blood_group, c.weight,
               c.identification_mark, v.vaccine_name, v.dose_number,
               cv.appointment_date, cv.appointment_time,
               p.father_name, p.mobile_number
        FROM child_vaccine cv
        JOIN children c ON cv.child_id = c.child_id
        JOIN vaccine v ON cv.vaccine_id = v.vaccine_id
        JOIN parent p ON c.parent_id = p.parent_id
        WHERE cv.id=%s
    """, (cv_id,))
    modal_details[cv_id] = cur.fetchone()

# ---------------- HTML ----------------
print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Confirmed Vaccine Appointments</title>
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

  body {{
    font-family: 'Segoe UI', sans-serif;
    background: var(--bg);
    color: #1e293b;
  }}

  /* ===== TOPBAR ===== */
  .topbar {{
    position: fixed;
    top: 0; left: 0; right: 0;
    height: var(--topbar-h);
    background: #0d1b2a;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
    z-index: 1100;
    box-shadow: 0 2px 10px rgba(0,0,0,.3);
  }}
  .topbar-left {{ display: flex; align-items: center; gap: 12px; }}
  .topbar img {{
    height: 40px; width: 40px;
    border-radius: 50%;
    border: 2px solid rgba(255,255,255,.4);
    object-fit: cover;
  }}
  .topbar .brand {{ color: #fff; font-size: 1rem; font-weight: 700; }}
  .topbar .subbrand {{ color: #90a4ae; font-size: .75rem; display: block; }}
  .hamburger {{
    background: none; border: none;
    color: #fff; font-size: 1.4rem;
    cursor: pointer; padding: 4px 8px;
    border-radius: 6px; display: none;
    transition: background .2s;
  }}
  .hamburger:hover {{ background: rgba(255,255,255,.1); }}
  .topbar-right a {{
    color: #cfd8dc; text-decoration: none;
    font-size: .85rem; padding: 6px 14px;
    border: 1px solid #37474f; border-radius: 6px;
    transition: all .2s;
  }}
  .topbar-right a:hover {{ background: #e53935; border-color: #e53935; color: #fff; }}

  /* ===== SIDEBAR ===== */
  .sidebar {{
    position: fixed;
    top: var(--topbar-h); left: 0;
    width: var(--sidebar-w);
    height: calc(100vh - var(--topbar-h));
    background: #0d1b2a;
    overflow-y: auto;
    z-index: 1000;
    transition: transform .3s ease;
    padding: 16px 12px 24px;
    scrollbar-width: thin;
    scrollbar-color: #1e3a5f transparent;
  }}
  .sidebar-label {{
    color: #546e7a; font-size: .68rem;
    font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; padding: 12px 8px 4px;
  }}
  .sidebar .nav-link {{
    color: #b0bec5; border-radius: 8px;
    padding: 9px 12px; font-size: .87rem;
    display: flex; align-items: center; gap: 10px;
    text-decoration: none; transition: all .2s; margin-bottom: 2px;
  }}
  .sidebar .nav-link i {{ width: 18px; text-align: center; font-size: .9rem; }}
  .sidebar .nav-link:hover,
  .sidebar .nav-link.active {{ background: var(--primary); color: #fff; }}
  .sidebar-group summary {{
    list-style: none; color: #b0bec5;
    padding: 9px 12px; border-radius: 8px;
    display: flex; align-items: center; gap: 10px;
    cursor: pointer; font-size: .87rem;
    transition: background .2s; margin-bottom: 2px;
    user-select: none;
  }}
  .sidebar-group summary::-webkit-details-marker {{ display: none; }}
  .sidebar-group summary:hover {{ background: #1c2d3e; color: #fff; }}
  .sidebar-group summary .caret {{
    margin-left: auto; transition: transform .25s; font-size: .75rem;
  }}
  .sidebar-group[open] summary .caret {{ transform: rotate(90deg); }}
  .sidebar-group[open] summary {{ color: #fff; background: #1c2d3e; }}
  .sub-links {{ padding: 4px 0 4px 28px; }}
  .sub-links a {{
    display: flex; align-items: center; gap: 8px;
    color: #78909c; font-size: .83rem;
    padding: 7px 10px; border-radius: 6px;
    text-decoration: none; transition: all .2s; margin-bottom: 1px;
  }}
  .sub-links a:hover {{ color: #fff; background: rgba(255,255,255,.07); }}
  .sub-links a.active {{ color: #fff; background: rgba(255,255,255,.07); }}
  .sidebar-divider {{ border: none; border-top: 1px solid #1c2d3e; margin: 10px 0; }}

  /* ===== OVERLAY ===== */
  .sidebar-overlay {{
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,.55); z-index: 999;
    backdrop-filter: blur(2px);
  }}

  /* ===== MAIN ===== */
  .main {{
    margin-left: var(--sidebar-w);
    margin-top: var(--topbar-h);
    padding: 28px 24px;
    min-height: calc(100vh - var(--topbar-h));
    transition: margin-left .3s;
  }}

  /* ===== PAGE HEADER ===== */
  .page-header {{
    display: flex; align-items: center; gap: 14px; margin-bottom: 24px;
  }}
  .page-header-icon {{
    background: linear-gradient(135deg, #1565c0, #42a5f5);
    color: #fff; width: 48px; height: 48px;
    border-radius: 12px; display: flex;
    align-items: center; justify-content: center;
    font-size: 1.2rem; flex-shrink: 0;
    box-shadow: 0 4px 12px rgba(21,101,192,.3);
  }}
  .page-header h4 {{ font-size: 1.2rem; font-weight: 700; margin: 0 0 2px; }}
  .page-header p {{ font-size: .85rem; color: #64748b; margin: 0; }}

  /* ===== SUMMARY STRIP ===== */
  .summary-strip {{
    background: #fff;
    border-radius: 12px;
    padding: 14px 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,.06);
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }}
  .summary-strip .count-badge {{
    background: #e3f2fd; color: #1565c0;
    padding: 4px 14px; border-radius: 20px;
    font-size: .85rem; font-weight: 700;
  }}

  /* ===== TABLE CARD ===== */
  .table-card {{
    background: #fff;
    border-radius: 14px;
    box-shadow: 0 2px 14px rgba(0,0,0,.08);
    overflow: hidden;
  }}
  .vaccine-table {{ font-size: .87rem; margin: 0; }}
  .vaccine-table thead th {{
    background: #f8fafc;
    color: #475569;
    font-weight: 700;
    font-size: .78rem;
    letter-spacing: .5px;
    text-transform: uppercase;
    padding: 12px 14px;
    border-color: #f1f5f9;
    white-space: nowrap;
  }}
  .vaccine-table tbody td {{
    padding: 12px 14px;
    border-color: #f1f5f9;
    vertical-align: middle;
  }}
  .vaccine-table tbody tr:hover {{ background: #f8fafc; }}

  /* ===== BADGES ===== */
  .badge-confirmed {{
    background: #e3f2fd; color: #1565c0;
    padding: 4px 12px; border-radius: 20px;
    font-size: .78rem; font-weight: 700;
    display: inline-flex; align-items: center; gap: 4px;
  }}
  .badge-dose {{
    background: #e3f2fd; color: #1565c0;
    padding: 3px 10px; border-radius: 20px;
    font-size: .78rem; font-weight: 700;
  }}
  .btn-view {{
    background: #e3f2fd; color: #1565c0;
    border: none; border-radius: 7px;
    padding: 5px 14px; font-size: .8rem;
    font-weight: 600; cursor: pointer;
    transition: all .2s; display: inline-flex;
    align-items: center; gap: 5px;
  }}
  .btn-view:hover {{ background: #1565c0; color: #fff; }}

  /* ===== MOBILE CARDS ===== */
  .mobile-vaccine-card {{
    display: none;
    background: #f8fafc;
    border-radius: 10px;
    padding: 14px;
    margin: 10px 14px;
    border: 1px solid #e2e8f0;
  }}
  .mvc-header {{
    display: flex; justify-content: space-between;
    align-items: flex-start; margin-bottom: 10px; gap: 8px;
  }}
  .mvc-name {{ font-weight: 700; font-size: .9rem; color: #1e293b; }}
  .mvc-row {{
    display: flex; justify-content: space-between;
    font-size: .83rem; padding: 4px 0;
    border-bottom: 1px solid #f1f5f9; gap: 8px;
  }}
  .mvc-row:last-child {{ border: none; }}
  .mvc-label {{ color: #94a3b8; font-weight: 700; font-size: .75rem; white-space: nowrap; }}
  .mvc-val {{ color: #1e293b; font-weight: 500; text-align: right; }}

  /* ===== MODALS ===== */
  .modal-content {{
    border: none; border-radius: 14px;
    box-shadow: 0 8px 32px rgba(0,0,0,.15);
    overflow: hidden;
    animation: zoomIn .25s ease;
  }}
  @keyframes zoomIn {{
    from {{ transform: scale(.92); opacity: 0; }}
    to   {{ transform: scale(1);   opacity: 1; }}
  }}
  .modal-section {{
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 12px;
  }}
  .modal-section h6 {{
    font-size: .82rem; font-weight: 700;
    letter-spacing: .8px; text-transform: uppercase; margin-bottom: 12px;
  }}
  .info-row {{
    display: flex; gap: 6px; font-size: .88rem;
    padding: 4px 0; border-bottom: 1px solid rgba(0,0,0,.05);
    flex-wrap: wrap;
  }}
  .info-row:last-child {{ border: none; }}
  .info-label {{ color: #64748b; font-weight: 600; min-width: 140px; flex-shrink: 0; }}
  .info-val {{ color: #1e293b; word-break: break-word; }}

  /* ===== EMPTY STATE ===== */
  .empty-state {{
    text-align: center; padding: 60px 20px;
    background: #fff; border-radius: 14px;
    box-shadow: 0 2px 12px rgba(0,0,0,.07);
  }}
  .empty-state i {{ font-size: 3rem; color: #cbd5e1; margin-bottom: 16px; display: block; }}
  .empty-state h5 {{ color: #64748b; font-weight: 600; }}
  .empty-state p {{ font-size: .88rem; color: #94a3b8; }}

  /* ===== RESPONSIVE ===== */
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

<!-- ===== TOPBAR ===== -->
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

<!-- OVERLAY -->
<div class="sidebar-overlay" id="overlay" onclick="toggleSidebar()"></div>

<!-- ===== SIDEBAR ===== -->
<nav class="sidebar" id="sidebar">
  <div class="sidebar-label">Menu</div>
  <a href="hospital_dash.py?hospital_id={oid}" class="nav-link">
    <i class="fa fa-gauge"></i> Dashboard
  </a>
  <a href="hospital_profile.py?hospital_id={oid}" class="nav-link">
    <i class="fa fa-user"></i> My Profile
  </a>
  <hr class="sidebar-divider">
  <div class="sidebar-label">Vaccinations</div>
  <details class="sidebar-group" open>
    <summary>
      <i class="fa-solid fa-syringe"></i> Vaccine Details
      <i class="fa fa-chevron-right caret"></i>
    </summary>
    <div class="sub-links">
      <a href="hospitalpendingvaccine.py?hospital_id={oid}"><i class="fa-solid fa-clock"></i> Pending</a>
      <a href="hospitalconfirmedvaccine.py?hospital_id={oid}" class="active"><i class="fa-solid fa-check"></i> Confirmed</a>
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
  <a href="home.py" class="nav-link" style="color:#ef9a9a;">
    <i class="fa fa-right-from-bracket"></i> Logout
  </a>
</nav>

<!-- ===== MAIN ===== -->
<main class="main">

  <div class="page-header">
    <div class="page-header-icon">
      <i class="fa-solid fa-check"></i>
    </div>
    <div>
      <h4>Confirmed Vaccine Appointments</h4>
      <p>Appointments confirmed and scheduled for administration</p>
    </div>
  </div>

  <div class="summary-strip">
    <i class="fa-solid fa-list-check text-primary"></i>
    <span style="font-size:.9rem;color:#475569;font-weight:600;">Total Confirmed</span>
    <span class="count-badge">{len(rows)} Record{"s" if len(rows) != 1 else ""}</span>
  </div>
""")

all_modals = ""

if rows:
    print("""
  <div class="table-card">

    <!-- Desktop Table -->
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
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
""")

    for i, row in enumerate(rows, start=1):
        cv_id = row[0]
        print(f"""
          <tr>
            <td><span style="background:#f1f5f9;color:#475569;padding:3px 8px;border-radius:6px;font-weight:600;">{i}</span></td>
            <td><strong>{row[1]}</strong></td>
            <td>{row[2]}</td>
            <td><span class="badge-dose">Dose {row[3]}</span></td>
            <td>{row[4]}</td>
            <td>{row[5]}</td>
            <td><span class="badge-confirmed"><i class="fa fa-check"></i> Confirmed</span></td>
            <td>
              <button class="btn-view" data-bs-toggle="modal" data-bs-target="#viewModal{cv_id}">
                <i class="fa fa-eye"></i> View
              </button>
            </td>
          </tr>
""")

        # Build modal
        detail = modal_details.get(cv_id)
        if detail:
            all_modals += f"""
<div class="modal fade" id="viewModal{cv_id}" tabindex="-1">
  <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header" style="background:linear-gradient(135deg,#1565c0,#42a5f5);">
        <h5 class="modal-title text-white">
          <i class="fa fa-id-card me-2"></i>Full Appointment Details
        </h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">

        <div class="modal-section" style="background:#e3f2fd;">
          <h6 style="color:#1565c0;"><i class="fa fa-child me-2"></i>Child Information</h6>
          <div class="row g-0">
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Child Name</span><span class="info-val">{detail[0]}</span></div>
              <div class="info-row"><span class="info-label">Date of Birth</span><span class="info-val">{detail[1]}</span></div>
              <div class="info-row"><span class="info-label">Gender</span><span class="info-val">{detail[2]}</span></div>
            </div>
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Blood Group</span><span class="info-val">{detail[3]}</span></div>
              <div class="info-row"><span class="info-label">Weight</span><span class="info-val">{detail[4]} kg</span></div>
              <div class="info-row"><span class="info-label">Identification</span><span class="info-val">{detail[5]}</span></div>
            </div>
          </div>
        </div>

        <div class="modal-section" style="background:#e8f5e9;">
          <h6 style="color:#2e7d32;"><i class="fa fa-syringe me-2"></i>Vaccine Information</h6>
          <div class="row g-0">
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Vaccine Name</span><span class="info-val">{detail[6]}</span></div>
              <div class="info-row"><span class="info-label">Dose Number</span><span class="info-val"><span class="badge-dose">Dose {detail[7]}</span></span></div>
            </div>
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Date</span><span class="info-val">{detail[8]}</span></div>
              <div class="info-row"><span class="info-label">Time</span><span class="info-val">{detail[9]}</span></div>
            </div>
          </div>
        </div>

        <div class="modal-section" style="background:#fff8e1;">
          <h6 style="color:#f57f17;"><i class="fa fa-user me-2"></i>Parent Information</h6>
          <div class="row g-0">
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Parent Name</span><span class="info-val">{detail[10]}</span></div>
            </div>
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Phone</span><span class="info-val">{detail[11]}</span></div>
            </div>
          </div>
        </div>

      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
      </div>
    </div>
  </div>
</div>"""

    print("        </tbody>\n      </table>\n    </div>")

    # Mobile cards
    print("""    <div class="mobile-cards-section" style="padding-bottom:8px;">""")
    for i, row in enumerate(rows, start=1):
        cv_id = row[0]
        print(f"""
      <div class="mobile-vaccine-card">
        <div class="mvc-header">
          <div>
            <div class="mvc-name">{row[1]}</div>
            <div style="font-size:.8rem;color:#64748b;">{row[2]}</div>
          </div>
          <span class="badge-confirmed"><i class="fa fa-check"></i> Confirmed</span>
        </div>
        <div class="mvc-row"><span class="mvc-label">Serial</span><span class="mvc-val">#{i}</span></div>
        <div class="mvc-row"><span class="mvc-label">Dose</span><span class="mvc-val"><span class="badge-dose">Dose {row[3]}</span></span></div>
        <div class="mvc-row"><span class="mvc-label">Date</span><span class="mvc-val">{row[4]}</span></div>
        <div class="mvc-row"><span class="mvc-label">Time</span><span class="mvc-val">{row[5]}</span></div>
        <div style="margin-top:10px;">
          <button class="btn-view w-100" data-bs-toggle="modal" data-bs-target="#viewModal{cv_id}">
            <i class="fa fa-eye"></i> View Full Details
          </button>
        </div>
      </div>
""")
    print("    </div>")   # mobile-cards-section
    print("  </div>")     # table-card

else:
    print("""
  <div class="empty-state">
    <i class="fa-solid fa-check-circle"></i>
    <h5>No Confirmed Appointments</h5>
    <p>Confirmed vaccination appointments will appear here.</p>
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