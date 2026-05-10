#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
print("Content-Type:text/html\r\n\r\n")

import pymysql, cgi, cgitb
from datetime import datetime, date
cgitb.enable()

con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()

form = cgi.FieldStorage()
child_id    = form.getvalue("child_id")
complete_id = form.getvalue("complete_id")
dose_no     = form.getvalue("dose_no")
hid         = form.getvalue("parent_id")

def add_months(d, months):
    month = d.month - 1 + int(months)
    year  = d.year + month // 12
    month = month % 12 + 1
    day   = min(d.day, 28)
    return date(year, month, day)

# ================= MARK VACCINE COMPLETED =================
if child_id and complete_id and dose_no:
    cur.execute("""
        INSERT INTO child_vaccine (child_id, vaccine_id, dose_number, taken_date)
        VALUES (%s, %s, %s, %s)
    """, (child_id, complete_id, dose_no, datetime.now().date()))
    con.commit()

# ================= FETCH CHILDREN =================
cur.execute("SELECT child_id, child_name FROM children WHERE parent_id=%s", (hid,))
all_children = cur.fetchall()

# ================= FETCH VACCINES IF CHILD SELECTED =================
vaccine_rows = []
child_dob    = None
today        = datetime.now().date()

if child_id:
    cur.execute("SELECT dob FROM children WHERE child_id=%s", (child_id,))
    row = cur.fetchone()
    if row:
        child_dob = row[0]
        cur.execute("SELECT * FROM vaccine WHERE status='confirmed' ORDER BY minimum_age ASC")
        vaccines = cur.fetchall()

        for v in vaccines:
            due = add_months(child_dob, v[3]) if child_dob else None

            cur.execute("""
                SELECT * FROM child_vaccine
                WHERE child_id=%s AND vaccine_id=%s AND dose_number=%s
            """, (child_id, v[0], v[5]))
            taken = cur.fetchone()

            if taken:
                status_key = "completed"
            elif due and today > due:
                status_key = "overdue"
            else:
                status_key = "upcoming"

            vaccine_rows.append({
                "id"    : v[0],
                "name"  : v[1],
                "dose"  : v[5],
                "due"   : str(due) if due else "N/A",
                "status": status_key,
                "taken" : bool(taken),
            })

# ================= HTML =================
print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vaccine Schedule</title>
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

  /* ===== SELECT CARD ===== */
  .select-card {{
    background: #fff; border-radius: 14px;
    box-shadow: 0 3px 12px rgba(0,0,0,.08);
    padding: 22px; margin-bottom: 24px;
  }}
  .select-card label {{
    font-weight: 700; color: #334155; margin-bottom: 8px;
    display: block; font-size: .92rem;
  }}
  .child-select {{
    border-radius: 8px; border: 1.5px solid #e2e8f0;
    padding: 10px 14px; font-size: .92rem; width: 100%;
    transition: border-color .2s;
  }}
  .child-select:focus {{
    border-color: #1565c0; outline: none;
    box-shadow: 0 0 0 3px rgba(21,101,192,.12);
  }}
  .btn-view-schedule {{
    background: linear-gradient(135deg, #1565c0, #1976d2);
    color: #fff; border: none; border-radius: 8px;
    padding: 10px 24px; font-size: .92rem; font-weight: 600;
    cursor: pointer; margin-top: 12px;
    display: flex; align-items: center; gap: 8px; transition: opacity .2s;
  }}
  .btn-view-schedule:hover {{ opacity: .9; }}

  /* ===== STATS ROW ===== */
  .stats-row {{
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 14px; margin-bottom: 24px;
  }}
  .stat-card {{
    background: #fff; border-radius: 12px; padding: 16px 18px;
    box-shadow: 0 2px 10px rgba(0,0,0,.06);
    display: flex; align-items: center; gap: 14px;
  }}
  .stat-icon {{
    width: 44px; height: 44px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; flex-shrink: 0;
  }}
  .stat-icon.green  {{ background: #e8f5e9; color: #2e7d32; }}
  .stat-icon.red    {{ background: #fde8e8; color: #c62828; }}
  .stat-icon.orange {{ background: #fff3e0; color: #e65100; }}
  .stat-label {{ font-size: .78rem; color: #888; font-weight: 600; }}
  .stat-value {{ font-size: 1.3rem; font-weight: 800; color: #1e293b; line-height: 1; }}

  /* ===== TABLE CARD ===== */
  .table-card {{
    background: #fff; border-radius: 14px;
    box-shadow: 0 3px 12px rgba(0,0,0,.08); overflow: hidden;
  }}
  .table-card-header {{
    background: #0d1b2a; color: #fff; padding: 13px 20px;
    font-weight: 700; font-size: .92rem;
    display: flex; align-items: center; gap: 8px;
  }}
  .table-wrapper {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
  .vaccine-table {{ width: 100%; border-collapse: collapse; min-width: 520px; }}
  .vaccine-table thead th {{
    background: #e3f2fd; color: #1565c0; padding: 11px 14px;
    font-size: .84rem; font-weight: 700; text-align: center;
    white-space: nowrap; border-bottom: 2px solid #bbdefb;
  }}
  .vaccine-table tbody td {{
    padding: 10px 14px; text-align: center; font-size: .87rem;
    color: #444; border-bottom: 1px solid #f0f0f0; vertical-align: middle;
  }}
  .vaccine-table tbody tr:nth-child(even) {{ background: #fafafa; }}
  .vaccine-table tbody tr:hover {{ background: #f0f7ff; }}
  .vaccine-table tbody tr:last-child td {{ border-bottom: none; }}

  /* ===== MOBILE CARDS ===== */
  .mobile-vaccine-cards {{ display: none; padding: 14px; }}
  .mobile-vcard {{
    border-radius: 10px; padding: 14px; margin-bottom: 12px;
    border: 1px solid #e0e8f0;
  }}
  .mobile-vcard:last-child {{ margin-bottom: 0; }}
  .mobile-vcard.completed {{ background: #f0fff4; border-left: 4px solid #2e7d32; }}
  .mobile-vcard.overdue   {{ background: #fff5f5; border-left: 4px solid #c62828; }}
  .mobile-vcard.upcoming  {{ background: #fff8ec; border-left: 4px solid #e65100; }}
  .mobile-vcard-title {{
    font-weight: 700; font-size: .93rem; margin-bottom: 10px;
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 6px;
  }}
  .mobile-row {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 4px 0; font-size: .855rem; border-bottom: 1px dashed #ddd;
  }}
  .mobile-row:last-of-type {{ border-bottom: none; }}
  .mobile-label {{ font-weight: 600; color: #555; }}
  .mobile-value {{ color: #222; text-align: right; }}
  .mobile-action {{ margin-top: 10px; text-align: right; }}

  /* ===== BADGES ===== */
  .badge-completed {{ background: #2e7d32; color: #fff; padding: 3px 10px; border-radius: 12px; font-size: .78rem; font-weight: 600; }}
  .badge-overdue   {{ background: #c62828; color: #fff; padding: 3px 10px; border-radius: 12px; font-size: .78rem; font-weight: 600; }}
  .badge-upcoming  {{ background: #e65100; color: #fff; padding: 3px 10px; border-radius: 12px; font-size: .78rem; font-weight: 600; }}

  /* ===== MARK DONE BTN ===== */
  .btn-done {{
    background: #2e7d32; color: #fff; border: none;
    padding: 5px 14px; border-radius: 6px; cursor: pointer;
    font-size: .82rem; transition: background .2s;
    display: inline-flex; align-items: center; gap: 5px;
  }}
  .btn-done:hover {{ background: #1b5e20; }}

  /* ===== EMPTY STATE ===== */
  .empty-state {{ text-align: center; padding: 40px 20px; color: #888; }}
  .empty-state i {{ font-size: 2.5rem; margin-bottom: 12px; display: block; }}

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
    .stats-row {{ grid-template-columns: 1fr; }}
  }}
  @media (max-width: 576px) {{
    .main {{ padding: 16px 10px; }}
    .select-card {{ padding: 16px 14px; }}
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
  <details class="sidebar-group">
    <summary>
      <i class="fa-solid fa-calendar-check"></i> Appointments
      <i class="fa fa-chevron-right caret"></i>
    </summary>
    <div class="sub-links">
      <a href="parentaddappointments.py?parent_id={hid}"><i class="fa fa-plus"></i> Add Appointment</a>
      <a href="parentpendingappointments.py?parent_id={hid}"><i class="fa fa-clock"></i> Pending</a>
      <a href="parentcompletedappointments.py?parent_id={hid}"><i class="fa fa-circle-check"></i> Completed</a>
    </div>
  </details>

  <hr class="sidebar-divider">
  <a href="parentnotify.py?parent_id={hid}" class="nav-link">
    <i class="fa-solid fa-bell"></i> Notifications
  </a>

  <hr class="sidebar-divider">
  <a href="parentfeedback.py?parent_id={hid}" class="nav-link active">
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
    <div class="page-header-icon"><i class="fa fa-syringe"></i></div>
    <div>
      <h4>Vaccine Schedule</h4>
      <p>View and track your child's vaccination schedule</p>
    </div>
  </div>

  <!-- Child Selector -->
  <div class="select-card">
    <form method="post">
      <input type="hidden" name="parent_id" value="{hid}">
      <label for="child_select">
        <i class="fa-solid fa-child me-2" style="color:#1565c0;"></i>Select a Child to View Schedule
      </label>
      <select name="child_id" id="child_select" class="child-select" required>
        <option value="">-- Select Child --</option>
""")

for c in all_children:
    selected = "selected" if child_id and str(c[0]) == str(child_id) else ""
    print(f'        <option value="{c[0]}" {selected}>{c[1]}</option>')

print(f"""
      </select>
      <button type="submit" class="btn-view-schedule">
        <i class="fa fa-eye"></i> View Schedule
      </button>
    </form>
  </div>
""")

# ===== VACCINE SCHEDULE =====
if child_id and vaccine_rows:
    completed_count = sum(1 for v in vaccine_rows if v["status"] == "completed")
    overdue_count   = sum(1 for v in vaccine_rows if v["status"] == "overdue")
    upcoming_count  = sum(1 for v in vaccine_rows if v["status"] == "upcoming")

    print(f"""
  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-icon green"><i class="fa-solid fa-circle-check"></i></div>
      <div>
        <div class="stat-label">Completed</div>
        <div class="stat-value">{completed_count}</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-icon red"><i class="fa-solid fa-triangle-exclamation"></i></div>
      <div>
        <div class="stat-label">Overdue</div>
        <div class="stat-value">{overdue_count}</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-icon orange"><i class="fa-solid fa-clock"></i></div>
      <div>
        <div class="stat-label">Upcoming</div>
        <div class="stat-value">{upcoming_count}</div>
      </div>
    </div>
  </div>

  <div class="table-card">
    <div class="table-card-header">
      <i class="fa-solid fa-list"></i> Vaccine Schedule
    </div>
    <div class="table-wrapper">
      <table class="vaccine-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Vaccine Name</th>
            <th>Dose No.</th>
            <th>Due Date</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>""")

    for i, v in enumerate(vaccine_rows, 1):
        if v["status"] == "completed":
            badge  = "<span class='badge-completed'>&#10003; Completed</span>"
            action = "<span class='text-muted'>—</span>"
        elif v["status"] == "overdue":
            badge  = "<span class='badge-overdue'>&#9888; Overdue</span>"
            action = f"""
              <form method="post" onsubmit="return confirm('Mark this vaccine as done?');">
                <input type="hidden" name="child_id"    value="{child_id}">
                <input type="hidden" name="complete_id" value="{v['id']}">
                <input type="hidden" name="dose_no"     value="{v['dose']}">
                <input type="hidden" name="parent_id"   value="{hid}">
                <button type="submit" class="btn-done">
                  <i class="fa-solid fa-check"></i> Mark Done
                </button>
              </form>"""
        else:
            badge  = "<span class='badge-upcoming'>&#9679; Upcoming</span>"
            action = f"""
              <form method="post" onsubmit="return confirm('Mark this vaccine as done?');">
                <input type="hidden" name="child_id"    value="{child_id}">
                <input type="hidden" name="complete_id" value="{v['id']}">
                <input type="hidden" name="dose_no"     value="{v['dose']}">
                <input type="hidden" name="parent_id"   value="{hid}">
                <button type="submit" class="btn-done">
                  <i class="fa-solid fa-check"></i> Mark Done
                </button>
              </form>"""

        print(f"""
          <tr>
            <td>{i}</td>
            <td><b>{v['name']}</b></td>
            <td>Dose {v['dose']}</td>
            <td>{v['due']}</td>
            <td>{badge}</td>
            <td>{action}</td>
          </tr>""")

    print("""
        </tbody>
      </table>
    </div>

    <!-- Mobile Cards -->
    <div class="mobile-vaccine-cards">""")

    for i, v in enumerate(vaccine_rows, 1):
        css_class = v["status"]

        if v["status"] == "completed":
            badge       = "<span class='badge-completed'>&#10003; Completed</span>"
            action_html = ""
        else:
            badge = f"<span class='badge-{v['status']}'>{('&#9888; Overdue' if v['status'] == 'overdue' else '&#9679; Upcoming')}</span>"
            action_html = f"""
        <div class="mobile-action">
          <form method="post" onsubmit="return confirm('Mark as done?');">
            <input type="hidden" name="child_id"    value="{child_id}">
            <input type="hidden" name="complete_id" value="{v['id']}">
            <input type="hidden" name="dose_no"     value="{v['dose']}">
            <input type="hidden" name="parent_id"   value="{hid}">
            <button type="submit" class="btn-done">
              <i class="fa-solid fa-check"></i> Mark Done
            </button>
          </form>
        </div>"""

        print(f"""
      <div class="mobile-vcard {css_class}">
        <div class="mobile-vcard-title">
          <span><i class="fa-solid fa-syringe me-1"></i>{i}. {v['name']}</span>
          {badge}
        </div>
        <div class="mobile-row">
          <span class="mobile-label">Dose</span>
          <span class="mobile-value">Dose {v['dose']}</span>
        </div>
        <div class="mobile-row">
          <span class="mobile-label">Due Date</span>
          <span class="mobile-value">{v['due']}</span>
        </div>
        {action_html}
      </div>""")

    print("""
    </div>
  </div>""")

elif child_id and not vaccine_rows:
    print("""
  <div class="table-card">
    <div class="empty-state">
      <i class="fa-solid fa-syringe text-muted"></i>
      No vaccine schedule found for this child.
    </div>
  </div>""")

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