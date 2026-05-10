#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
import os.path

print("Content-Type: text/html\r\n\r\n")

import cgi, cgitb, pymysql
import sys
from collections import OrderedDict

sys.stdout.reconfigure(encoding='utf-8')
cgitb.enable()

con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()

form = cgi.FieldStorage()
hid = form.getvalue("parent_id")

if not hid:
    print("<h3>Invalid Parent ID</h3>")
    exit()

# ---------------- MARK AS COMPLETED ----------------
cv_id_to_complete = form.getvalue("cv_id")
if cv_id_to_complete and str(cv_id_to_complete).isdigit():
    cur.execute("UPDATE child_vaccine SET status = 'completed' WHERE id = %s", (int(cv_id_to_complete),))
    con.commit()

# ---------------- FETCH COMPLETED APPOINTMENTS ----------------
cur.execute("""
    SELECT cv.id, c.child_id, c.child_name, c.dob, c.gender, c.blood_group,
           c.weight, c.identification_mark, v.vaccine_name, v.dose_number,
           cv.appointment_date, cv.appointment_time, p.father_name, p.mobile_number
    FROM child_vaccine cv
    JOIN children c ON cv.child_id = c.child_id
    JOIN vaccine v ON cv.vaccine_id = v.vaccine_id
    JOIN parent p ON c.parent_id = p.parent_id
    WHERE c.parent_id = %s AND cv.status = 'completed'
    ORDER BY c.child_id ASC, v.dose_number ASC
""", (hid,))

rows = cur.fetchall()

# ---------------- GROUP BY CHILD ----------------
children = OrderedDict()
for row in rows:
    cv_id, child_id, child_name, dob, gender, blood_group, weight, identification, \
    vaccine_name, dose_number, appt_date, appt_time, father_name, mobile = row

    if child_id not in children:
        children[child_id] = {
            "child_name": child_name, "dob": dob, "gender": gender,
            "blood_group": blood_group, "weight": weight,
            "identification": identification, "father_name": father_name,
            "mobile": mobile, "vaccines": []
        }
    children[child_id]["vaccines"].append({
        "cv_id": cv_id, "vaccine_name": vaccine_name,
        "dose_number": dose_number, "appt_date": appt_date, "appt_time": appt_time,
    })

print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Completed Appointments</title>
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
  .hamburger {{
    background: none; border: none; color: #fff; font-size: 1.4rem;
    cursor: pointer; padding: 4px 8px; border-radius: 6px;
    display: none; transition: background .2s;
  }}
  .hamburger:hover {{ background: rgba(255,255,255,.1); }}
  .topbar-right a {{
    color: #cfd8dc; text-decoration: none; font-size: .85rem;
    padding: 6px 14px; border: 1px solid #37474f;
    border-radius: 6px; transition: all .2s;
  }}
  .topbar-right a:hover {{ background: #e53935; border-color: #e53935; color: #fff; }}

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
  .page-header {{ display: flex; align-items: center; gap: 14px; margin-bottom: 24px; }}
  .page-header-icon {{
    background: linear-gradient(135deg, #2e7d32, #43a047);
    color: #fff; width: 48px; height: 48px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; flex-shrink: 0;
    box-shadow: 0 4px 12px rgba(46,125,50,.3);
  }}
  .page-header h4 {{ font-size: 1.2rem; font-weight: 700; margin: 0 0 2px; }}
  .page-header p {{ font-size: .85rem; color: #64748b; margin: 0; }}

  /* ===== CHILD CARD ===== */
  .child-card {{
    background: #fff; border-radius: 14px;
    margin-bottom: 28px;
    box-shadow: 0 3px 12px rgba(0,0,0,.08); overflow: hidden;
  }}
  .child-card-header {{
    background: linear-gradient(135deg, #1565c0, #1976d2);
    color: #fff; padding: 14px 20px;
    display: flex; align-items: center; gap: 12px;
  }}
  .child-avatar {{
    background: rgba(255,255,255,.2); border-radius: 50%;
    width: 42px; height: 42px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; flex-shrink: 0;
  }}
  .child-card-header h5 {{ margin: 0; font-size: 1rem; }}

  /* ===== TABLE ===== */
  .table-wrapper {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
  .vaccine-table {{ width: 100%; border-collapse: collapse; min-width: 560px; }}
  .vaccine-table thead th {{
    background: #e8f5e9; padding: 11px 14px;
    font-size: .85rem; font-weight: 700; color: #333;
    text-align: center; white-space: nowrap;
    border-bottom: 2px solid #c8e6c9;
  }}
  .vaccine-table tbody td {{
    padding: 10px 14px; text-align: center;
    font-size: .88rem; color: #444;
    border-bottom: 1px solid #f0f0f0; vertical-align: middle;
  }}
  .vaccine-table tbody tr:last-child td {{ border-bottom: none; }}
  .vaccine-table tbody tr:hover {{ background: #f8fbff; }}

  /* ===== MOBILE CARD VIEW ===== */
  .mobile-vaccine-cards {{ display: none; padding: 12px; }}
  .mobile-vaccine-card {{
    background: #f8f9fa; border: 1px solid #e0e0e0;
    border-radius: 10px; padding: 14px; margin-bottom: 12px;
  }}
  .mobile-vaccine-card:last-child {{ margin-bottom: 0; }}
  .mobile-row {{
    display: flex; justify-content: space-between;
    align-items: center; padding: 4px 0; font-size: .875rem;
  }}
  .mobile-label {{ font-weight: 600; color: #555; min-width: 110px; }}
  .mobile-value {{ color: #222; text-align: right; }}

  /* ===== BADGES ===== */
  .dose-badge {{
    background: #1565c0; color: #fff;
    padding: 2px 10px; border-radius: 12px;
    font-size: .78rem; font-weight: 600; white-space: nowrap;
  }}
  .status-badge {{
    background: #2e7d32; color: #fff;
    padding: 2px 10px; border-radius: 12px;
    font-size: .78rem; font-weight: 600;
  }}
  .view-btn {{
    background: #1565c0; color: #fff; border: none;
    padding: 5px 14px; border-radius: 6px;
    cursor: pointer; font-size: .82rem; transition: background .2s;
  }}
  .view-btn:hover {{ background: #0d47a1; }}

  /* ===== MODAL ===== */
  .info-label {{ font-weight: bold; color: #555; display: inline-block; }}
  .info-section {{ border-radius: 8px; padding: 15px 20px; margin-bottom: 14px; }}
  .info-section.blue {{ background: #f0f9ff; border-left: 4px solid #1565c0; }}
  .info-section.green {{ background: #f0fff4; border-left: 4px solid #2e7d32; }}
  .info-section.yellow {{ background: #fff8e1; border-left: 4px solid #f57f17; }}
  .info-section h6 {{ margin-bottom: 12px; font-weight: 700; }}
  .info-row {{
    display: flex; flex-wrap: wrap; gap: 4px 16px;
    margin-bottom: 6px; font-size: .9rem;
  }}

  /* ===== RESPONSIVE ===== */
  @media (max-width: 991px) {{
    .sidebar {{ transform: translateX(-100%); }}
    .sidebar.open {{ transform: translateX(0); }}
    .sidebar-overlay.open {{ display: block; }}
    .main {{ margin-left: 0; }}
    .hamburger {{ display: block; }}
  }}
  @media (max-width: 650px) {{
    .table-wrapper {{ display: none; }}
    .mobile-vaccine-cards {{ display: block; }}
  }}
  @media (max-width: 576px) {{
    .main {{ padding: 16px 10px; }}
    .child-card-header {{ padding: 12px 14px; }}
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
    <a href="home.py"><i class="fa fa-right-from-bracket me-1"></i> Logout</a>
  </div>
</div>

<!-- OVERLAY -->
<div class="sidebar-overlay" id="overlay" onclick="toggleSidebar()"></div>

<!-- ===== SIDEBAR ===== -->
<nav class="sidebar" id="sidebar">
  <div class="sidebar-label">Menu</div>
  <a href="parent_dash.py?parent_id={hid}" class="nav-link">
    <i class="fa fa-gauge"></i> Dashboard
  </a>
  <a href="parent_profile.py?parent_id={hid}" class="nav-link">
    <i class="fa fa-user"></i> My Profile
  </a>

  <hr class="sidebar-divider">
  <details class="sidebar-group">
    <summary>
      <i class="fa-solid fa-child"></i> Child
      <i class="fa fa-chevron-right caret"></i>
    </summary>
    <div class="sub-links">
      <a href="parentaddchild.py?parent_id={hid}"><i class="fa fa-plus"></i> Add Child</a>
      <a href="parentviewchild.py?parent_id={hid}"><i class="fa fa-eye"></i> View Child</a>
    </div>
  </details>

  <hr class="sidebar-divider">
  <details class="sidebar-group" open>
    <summary>
      <i class="fa-solid fa-calendar-check"></i> Appointments
      <i class="fa fa-chevron-right caret"></i>
    </summary>
    <div class="sub-links">
      <a href="parentaddappointments.py?parent_id={hid}"><i class="fa fa-plus"></i> Add Appointment</a>
      <a href="parentpendingappointments.py?parent_id={hid}"><i class="fa fa-clock"></i> Pending</a>
      <a href="parentcompletedappointments.py?parent_id={hid}" style="color:#fff;background:rgba(255,255,255,.07);">
        <i class="fa fa-circle-check"></i> Completed
      </a>
    </div>
  </details>

  <hr class="sidebar-divider">
  <a href="parentnotify.py?parent_id={hid}" class="nav-link">
    <i class="fa-solid fa-bell"></i> Notifications
  </a>

  <hr class="sidebar-divider">
  <a href="parentfeedback.py?parent_id={hid}" class="nav-link">
    <i class="fa-solid fa-comment"></i> FeedBack
  </a>

  <hr class="sidebar-divider">
  <a href="home.py" class="nav-link" style="color:#ef9a9a;">
    <i class="fa fa-right-from-bracket"></i> Logout
  </a>
</nav>

<!-- ===== MAIN ===== -->
<main class="main">

  <div class="page-header">
    <div class="page-header-icon"><i class="fa fa-circle-check"></i></div>
    <div>
      <h4>Completed Appointments</h4>
      <p>All completed vaccine appointments for your children</p>
    </div>
  </div>
""")

all_modals = ""

if children:
    child_num = 1
    for child_id, cdata in children.items():

        print(f"""
  <div class="child-card">
    <div class="child-card-header">
      <div class="child-avatar"><i class="fa fa-child"></i></div>
      <div>
        <h5>{child_num}. {cdata["child_name"]}</h5>
        <small style="opacity:.8;">{len(cdata["vaccines"])} completed vaccine(s)</small>
      </div>
    </div>

    <!-- Desktop Table -->
    <div class="table-wrapper">
      <table class="vaccine-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Vaccine Name</th>
            <th>Dose</th>
            <th>Date</th>
            <th>Time</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>""")

        for dose_num, vaccine in enumerate(cdata["vaccines"], start=1):
            cv_id = vaccine["cv_id"]
            print(f"""
          <tr>
            <td>{dose_num}</td>
            <td><b>{vaccine["vaccine_name"]}</b></td>
            <td><span class="dose-badge">Dose {vaccine["dose_number"]}</span></td>
            <td>{vaccine["appt_date"]}</td>
            <td>{vaccine["appt_time"]}</td>
            <td><span class="status-badge">&#10003; Completed</span></td>
            <td>
              <button class="view-btn" data-bs-toggle="modal" data-bs-target="#viewModal{cv_id}">
                <i class="fa fa-eye me-1"></i>View
              </button>
            </td>
          </tr>""")

        print("""
        </tbody>
      </table>
    </div>

    <!-- Mobile Card View -->
    <div class="mobile-vaccine-cards">""")

        for dose_num, vaccine in enumerate(cdata["vaccines"], start=1):
            cv_id = vaccine["cv_id"]
            print(f"""
      <div class="mobile-vaccine-card">
        <div class="mobile-row">
          <span class="mobile-label">#</span>
          <span class="mobile-value">{dose_num}</span>
        </div>
        <div class="mobile-row">
          <span class="mobile-label">Vaccine</span>
          <span class="mobile-value"><b>{vaccine["vaccine_name"]}</b></span>
        </div>
        <div class="mobile-row">
          <span class="mobile-label">Dose</span>
          <span class="mobile-value"><span class="dose-badge">Dose {vaccine["dose_number"]}</span></span>
        </div>
        <div class="mobile-row">
          <span class="mobile-label">Date</span>
          <span class="mobile-value">{vaccine["appt_date"]}</span>
        </div>
        <div class="mobile-row">
          <span class="mobile-label">Time</span>
          <span class="mobile-value">{vaccine["appt_time"]}</span>
        </div>
        <div class="mobile-row">
          <span class="mobile-label">Status</span>
          <span class="mobile-value"><span class="status-badge">&#10003; Completed</span></span>
        </div>
        <div class="mobile-row" style="margin-top:8px;">
          <span></span>
          <button class="view-btn" data-bs-toggle="modal" data-bs-target="#viewModal{cv_id}">
            <i class="fa fa-eye me-1"></i>View Details
          </button>
        </div>
      </div>""")

            all_modals += f"""
<div class="modal fade" id="viewModal{cv_id}" tabindex="-1">
  <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header bg-success text-white">
        <h5 class="modal-title">
          <i class="fa fa-id-card me-2"></i>Completed Appointment Details
        </h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">

        <div class="info-section blue">
          <h6 class="text-primary"><i class="fa fa-child me-1"></i> Child Information</h6>
          <div class="row g-2">
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Child Name</span><span>: {cdata["child_name"]}</span></div>
              <div class="info-row"><span class="info-label">Date of Birth</span><span>: {cdata["dob"]}</span></div>
              <div class="info-row"><span class="info-label">Gender</span><span>: {cdata["gender"]}</span></div>
            </div>
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Blood Group</span><span>: {cdata["blood_group"]}</span></div>
              <div class="info-row"><span class="info-label">Weight</span><span>: {cdata["weight"]} kg</span></div>
              <div class="info-row"><span class="info-label">ID Mark</span><span>: {cdata["identification"]}</span></div>
            </div>
          </div>
        </div>

        <div class="info-section green">
          <h6 class="text-success"><i class="fa fa-syringe me-1"></i> Vaccine Information</h6>
          <div class="row g-2">
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Vaccine Name</span><span>: {vaccine["vaccine_name"]}</span></div>
              <div class="info-row"><span class="info-label">Dose Number</span><span>: <span class="dose-badge">Dose {vaccine["dose_number"]}</span></span></div>
            </div>
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Appt. Date</span><span>: {vaccine["appt_date"]}</span></div>
              <div class="info-row"><span class="info-label">Appt. Time</span><span>: {vaccine["appt_time"]}</span></div>
            </div>
          </div>
        </div>

        <div class="info-section yellow">
          <h6 style="color:#f57f17;"><i class="fa fa-user me-1"></i> Parent Information</h6>
          <div class="row g-2">
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Parent Name</span><span>: {cdata["father_name"]}</span></div>
            </div>
            <div class="col-12 col-sm-6">
              <div class="info-row"><span class="info-label">Phone</span><span>: {cdata["mobile"]}</span></div>
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

        print("""
    </div>
  </div>""")

        child_num += 1

else:
    print("""
  <div class="alert alert-info text-center mt-3" style="border-radius:10px;">
    <i class="fa fa-inbox me-2 fa-lg"></i>No Completed Appointments Found
  </div>""")

print(all_modals)

print("""
</main>

<script>
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('overlay').classList.toggle('open');
}

window.addEventListener('resize', function() {
  if (window.innerWidth > 991) {
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('overlay').classList.remove('open');
  }
});
</script>
</body>
</html>
""")

con.close()