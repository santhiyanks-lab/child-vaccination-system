#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
print("content-type:text/html\r\n\r\n")

import cgi, cgitb, pymysql
from datetime import date

cgitb.enable()
con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()
form = cgi.FieldStorage()

def add_months(original_date, months):
    month = original_date.month - 1 + months
    year = original_date.year + month // 12
    month = month % 12 + 1
    day = min(original_date.day, 28)
    return date(year, month, day)

parent_id = form.getvalue("parent_id")
if not parent_id:
    print("<h3>Parent ID Missing</h3>")
    exit()

cur.execute("""
SELECT
c.child_id, c.child_name, c.dob, c.weight,
c.gender, c.blood_group, c.identification_mark,
p.father_name, p.father_age,
p.mother_name, p.mother_age, p.mother_weight,
p.email, p.mobile_number, p.occupation,
p.state, p.district, p.address, p.pincode,
p.father_aadhar_image, p.parent_profile
FROM children c
LEFT JOIN parent p ON c.parent_id = p.parent_id
WHERE c.parent_id = %s
ORDER BY c.child_id
""", (parent_id,))
children = cur.fetchall()

print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Notifications</title>
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
    background: linear-gradient(135deg, #1565c0, #42a5f5);
    color: #fff; width: 48px; height: 48px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; flex-shrink: 0;
    box-shadow: 0 4px 12px rgba(21,101,192,.3);
  }}
  .page-header h4 {{ font-size: 1.2rem; font-weight: 700; margin: 0 0 2px; }}
  .page-header p {{ font-size: .85rem; color: #64748b; margin: 0; }}

  /* ===== TABLE CARD ===== */
  .table-card {{
    background: #fff; border-radius: 14px;
    box-shadow: 0 3px 12px rgba(0,0,0,.08); overflow: hidden;
  }}
  .table-wrapper {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
  .notify-table {{ width: 100%; border-collapse: collapse; min-width: 480px; }}
  .notify-table thead th {{
    background: #e3f2fd; color: #1565c0;
    padding: 12px 16px; font-size: .88rem;
    font-weight: 700; text-align: center; white-space: nowrap;
    border-bottom: 2px solid #bbdefb;
  }}
  .notify-table tbody td {{
    padding: 11px 16px; text-align: center;
    font-size: .9rem; color: #444;
    border-bottom: 1px solid #f0f0f0; vertical-align: middle;
  }}
  .notify-table tbody tr:last-child td {{ border-bottom: none; }}
  .notify-table tbody tr:hover {{ background: #f8fbff; }}

  /* ===== MOBILE CARDS ===== */
  .mobile-cards {{ display: none; padding: 14px; }}
  .mobile-card {{
    background: #fff; border: 1px solid #e0e8f0;
    border-radius: 12px; padding: 16px; margin-bottom: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,.06);
  }}
  .mobile-card:last-child {{ margin-bottom: 0; }}
  .mobile-card-title {{
    font-size: 1rem; font-weight: 700; color: #1565c0;
    margin-bottom: 10px; display: flex; align-items: center; gap: 8px;
  }}
  .mobile-row {{
    display: flex; justify-content: space-between;
    align-items: center; padding: 5px 0; font-size: .875rem;
    border-bottom: 1px dashed #eee;
  }}
  .mobile-row:last-of-type {{ border-bottom: none; }}
  .mobile-label {{ font-weight: 600; color: #555; }}
  .mobile-value {{ color: #222; text-align: right; }}
  .mobile-action {{ margin-top: 12px; text-align: right; }}

  /* ===== BUTTONS ===== */
  .view-btn {{
    background: #1565c0; color: #fff; border: none;
    padding: 6px 16px; border-radius: 6px;
    cursor: pointer; font-size: .85rem; transition: background .2s;
  }}
  .view-btn:hover {{ background: #0d47a1; }}

  /* ===== MODAL ===== */
  .modal-section {{ border-radius: 8px; padding: 14px 18px; margin-bottom: 14px; }}
  .modal-section.blue {{ background: #f0f9ff; border-left: 4px solid #1565c0; }}
  .modal-section.green {{ background: #f0fff4; border-left: 4px solid #2e7d32; }}
  .modal-section.red {{ background: #fff5f5; border-left: 4px solid #c62828; }}
  .modal-section h6 {{ font-weight: 700; margin-bottom: 10px; font-size: .95rem; }}
  .modal-info-row {{
    display: flex; flex-wrap: wrap; gap: 2px 12px;
    margin-bottom: 5px; font-size: .88rem;
  }}
  .modal-info-row b {{ min-width: 130px; color: #555; }}
  .modal-img {{
    max-height: 120px; border-radius: 8px;
    border: 2px solid #dee2e6; margin-top: 6px;
  }}
  .vaccine-table {{ width: 100%; border-collapse: collapse; margin-top: 4px; }}
  .vaccine-table th {{
    background: #f1f3f5; padding: 8px 12px;
    font-size: .82rem; text-align: center; color: #333;
  }}
  .vaccine-table td {{
    padding: 7px 12px; text-align: center;
    font-size: .85rem; border-bottom: 1px solid #eee;
  }}

  /* ===== RESPONSIVE ===== */
  @media (max-width: 991px) {{
    .sidebar {{ transform: translateX(-100%); }}
    .sidebar.open {{ transform: translateX(0); }}
    .sidebar-overlay.open {{ display: block; }}
    .main {{ margin-left: 0; }}
    .hamburger {{ display: block; }}
  }}
  @media (max-width: 600px) {{
    .table-wrapper {{ display: none; }}
    .mobile-cards {{ display: block; }}
  }}
  @media (max-width: 576px) {{
    .main {{ padding: 16px 10px; }}
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
  <a href="parentnotify.py?parent_id={parent_id}" class="nav-link active">
    <i class="fa-solid fa-bell"></i> Notifications
  </a>

  <hr class="sidebar-divider">
  <a href="parentfeedback.py?parent_id={parent_id}" class="nav-link">
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
    <div class="page-header-icon"><i class="fa fa-bell"></i></div>
    <div>
      <h4>Notifications</h4>
      <p>Vaccine notifications for your children</p>
    </div>
  </div>
""")

modal_content = ""
index = 1

if children:
    # ---- Desktop Table ----
    print("""
  <div class="table-card">
    <div class="table-wrapper">
      <table class="notify-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Child Name</th>
            <th>Date of Birth</th>
            <th>Weight (kg)</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>""")

    for child in children:
        child_id   = child[0]
        child_name = child[1]
        child_dob  = child[2]
        weight     = child[3]

        print(f"""
          <tr>
            <td>{index}</td>
            <td><b>{child_name}</b></td>
            <td>{child_dob}</td>
            <td>{weight}</td>
            <td>
              <button class="view-btn" data-bs-toggle="modal" data-bs-target="#modal{child_id}">
                <i class="fa fa-eye me-1"></i>View More
              </button>
            </td>
          </tr>""")
        index += 1

    print("""
        </tbody>
      </table>
    </div>
  </div>""")

    # ---- Mobile Cards ----
    print("""  <div class="mobile-cards">""")
    index = 1
    for child in children:
        child_id   = child[0]
        child_name = child[1]
        child_dob  = child[2]
        weight     = child[3]

        print(f"""
    <div class="mobile-card">
      <div class="mobile-card-title">
        <i class="fa-solid fa-child-reaching"></i> {index}. {child_name}
      </div>
      <div class="mobile-row">
        <span class="mobile-label">Date of Birth</span>
        <span class="mobile-value">{child_dob}</span>
      </div>
      <div class="mobile-row">
        <span class="mobile-label">Weight</span>
        <span class="mobile-value">{weight} kg</span>
      </div>
      <div class="mobile-action">
        <button class="view-btn" data-bs-toggle="modal" data-bs-target="#modal{child_id}">
          <i class="fa fa-eye me-1"></i>View Full Details
        </button>
      </div>
    </div>""")
        index += 1

    print("""  </div>""")

    # ---- Build Modals ----
    index = 1
    for child in children:
        child_id   = child[0]
        child_name = child[1]
        child_dob  = child[2]
        weight     = child[3]

        cur.execute("""
            SELECT v.vaccine_name, v.dose_number, cv.status
            FROM child_vaccine cv
            JOIN vaccine v ON cv.vaccine_id = v.vaccine_id
            WHERE cv.child_id = %s
        """, (child_id,))
        vaccines = cur.fetchall()

        vaccine_rows = ""
        if vaccines:
            for vac in vaccines:
                status = vac[2].strip().lower() if vac[2] else ""
                if status == "completed":
                    badge = '<span class="badge bg-success">Taken</span>'
                elif status == "pending":
                    badge = '<span class="badge bg-warning text-dark">Not Taken</span>'
                elif status == "notified":
                    badge = '<span class="badge bg-info text-dark">Notified</span>'
                else:
                    badge = '<span class="badge bg-secondary">Not Scheduled</span>'
                vaccine_rows += f"<tr><td>{vac[0]}</td><td>{vac[1]}</td><td>{badge}</td></tr>"
        else:
            vaccine_rows = '<tr><td colspan="3" class="text-center text-muted">No Vaccines Found</td></tr>'

        modal_content += f"""
<div class="modal fade" id="modal{child_id}" tabindex="-1">
  <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header bg-primary text-white">
        <h5 class="modal-title">
          <i class="fa fa-bell me-2"></i>Notification Details — {child_name}
        </h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">

        <div class="modal-section blue">
          <h6 class="text-primary"><i class="fa fa-child me-1"></i> Child Details</h6>
          <div class="row g-1">
            <div class="col-12 col-sm-6">
              <div class="modal-info-row"><b>Name</b><span>: {child_name}</span></div>
              <div class="modal-info-row"><b>Date of Birth</b><span>: {child_dob}</span></div>
              <div class="modal-info-row"><b>Weight</b><span>: {weight} kg</span></div>
            </div>
            <div class="col-12 col-sm-6">
              <div class="modal-info-row"><b>Gender</b><span>: {child[4]}</span></div>
              <div class="modal-info-row"><b>Blood Group</b><span>: {child[5]}</span></div>
              <div class="modal-info-row"><b>ID Mark</b><span>: {child[6]}</span></div>
            </div>
          </div>
        </div>

        <div class="modal-section green">
          <h6 class="text-success"><i class="fa fa-user me-1"></i> Parent Details</h6>
          <div class="row g-1">
            <div class="col-12 col-sm-6">
              <div class="modal-info-row"><b>Father Name</b><span>: {child[7]}</span></div>
              <div class="modal-info-row"><b>Father Age</b><span>: {child[8]}</span></div>
              <div class="modal-info-row"><b>Mother Name</b><span>: {child[9]}</span></div>
              <div class="modal-info-row"><b>Mother Age</b><span>: {child[10]}</span></div>
              <div class="modal-info-row"><b>Mother Weight</b><span>: {child[11]}</span></div>
              <div class="modal-info-row"><b>Email</b><span>: {child[12]}</span></div>
            </div>
            <div class="col-12 col-sm-6">
              <div class="modal-info-row"><b>Mobile</b><span>: {child[13]}</span></div>
              <div class="modal-info-row"><b>Occupation</b><span>: {child[14]}</span></div>
              <div class="modal-info-row"><b>State</b><span>: {child[15]}</span></div>
              <div class="modal-info-row"><b>District</b><span>: {child[16]}</span></div>
              <div class="modal-info-row"><b>Address</b><span>: {child[17]}</span></div>
              <div class="modal-info-row"><b>Pincode</b><span>: {child[18]}</span></div>
            </div>
          </div>
          <div class="row g-2 mt-2">
            <div class="col-6 col-sm-4">
              <div style="font-size:.82rem;font-weight:600;color:#555;margin-bottom:4px;">Aadhar Image</div>
              <img src="./images/{child[19]}" class="modal-img" alt="Aadhar">
            </div>
            <div class="col-6 col-sm-4">
              <div style="font-size:.82rem;font-weight:600;color:#555;margin-bottom:4px;">Profile Photo</div>
              <img src="./images/{child[20]}" class="modal-img" alt="Profile">
            </div>
          </div>
        </div>

        <div class="modal-section red">
          <h6 class="text-danger"><i class="fa fa-syringe me-1"></i> Vaccine Details</h6>
          <div style="overflow-x:auto;">
            <table class="vaccine-table">
              <thead>
                <tr>
                  <th>Vaccine Name</th>
                  <th>Dose No</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>{vaccine_rows}</tbody>
            </table>
          </div>
        </div>

      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Close</button>
      </div>
    </div>
  </div>
</div>"""
        index += 1

else:
    print("""
  <div class="alert alert-info text-center" style="border-radius:10px;">
    <i class="fa fa-inbox me-2 fa-lg"></i>No notification data found.
  </div>""")

print(modal_content)

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