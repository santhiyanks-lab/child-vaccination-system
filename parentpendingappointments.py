#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
print("Content-Type: text/html\r\n\r\n")

import cgi
import cgitb
import pymysql
import sys
from datetime import date
from collections import OrderedDict

sys.stdout.reconfigure(encoding='utf-8')
cgitb.enable()

form = cgi.FieldStorage()
hid  = form.getfirst("parent_id")

if not hid or not hid.strip().isdigit():
    print("<h3>Invalid Parent ID!</h3>")
    exit()

parent_id = int(hid.strip())

con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()

today = date.today()

def to_date(val):
    if val is None:
        return None
    from datetime import datetime as _dt
    if hasattr(val, "date"):
        return val.date()
    if isinstance(val, date):
        return val
    try:
        return _dt.strptime(str(val).strip()[:10], "%Y-%m-%d").date()
    except Exception:
        return None

# ---------------------------------------------------------
# CORRECT SORTING: Child -> Vaccine -> Dose ASC -> Date -> Time
# ---------------------------------------------------------
cur.execute("""
    SELECT
        cv.id,
        cv.child_id,
        c.child_name,
        cv.vaccine_id,
        v.vaccine_name,
        COALESCE(cv.dose_number, v.dose_number, 1) AS dose_number,
        cv.hospital_id,
        h.hospital_name,
        cv.appointment_date,
        cv.appointment_time,
        cv.reschedule_date,
        cv.reschedule_time,
        cv.status
    FROM child_vaccine cv
    JOIN children  c ON cv.child_id   = c.child_id
    JOIN vaccine   v ON cv.vaccine_id = v.vaccine_id
    LEFT JOIN hospital h ON cv.hospital_id = h.hospital_id
    WHERE c.parent_id = %s
      AND LOWER(TRIM(cv.status)) IN ('pending','confirmed','rescheduled','notified')
    ORDER BY
        c.child_name ASC,
        cv.vaccine_id ASC,
        COALESCE(cv.dose_number, v.dose_number, 1) ASC,
        cv.appointment_date ASC,
        cv.appointment_time ASC
""", (parent_id,))

rows = cur.fetchall()

# ---------------------------------------------------------
# Group by child — ORDER ALREADY CORRECT FROM SQL
# ---------------------------------------------------------
child_groups = OrderedDict()
child_names  = {}

for row in rows:
    cid   = row[1]
    cname = str(row[2]) if row[2] else "Unknown"
    if cid not in child_groups:
        child_groups[cid] = []
        child_names[cid]  = cname
    child_groups[cid].append(row)

total_records  = len(rows)
total_children = len(child_groups)

print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pending Appointments</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
  :root {{
    --sidebar-w:260px; --topbar-h:60px;
    --primary:#1565c0; --bg:#f0f4f8;
  }}
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',sans-serif;background:var(--bg);color:#1e293b}}

  .topbar{{position:fixed;top:0;left:0;right:0;height:var(--topbar-h);
    background:#0d1b2a;display:flex;align-items:center;
    justify-content:space-between;padding:0 16px;
    z-index:1100;box-shadow:0 2px 10px rgba(0,0,0,.3)}}
  .topbar-left{{display:flex;align-items:center;gap:12px}}
  .topbar img{{height:40px;width:40px;border-radius:50%;border:2px solid rgba(255,255,255,.4);object-fit:cover}}
  .topbar .brand{{color:#fff;font-size:1rem;font-weight:700}}
  .hamburger{{background:none;border:none;color:#fff;font-size:1.4rem;cursor:pointer;
    padding:4px 8px;border-radius:6px;display:none;transition:background .2s}}
  .hamburger:hover{{background:rgba(255,255,255,.1)}}
  .topbar-right a{{color:#cfd8dc;text-decoration:none;font-size:.85rem;
    padding:6px 14px;border:1px solid #37474f;border-radius:6px;transition:all .2s}}
  .topbar-right a:hover{{background:#e53935;border-color:#e53935;color:#fff}}

  .sidebar{{position:fixed;top:var(--topbar-h);left:0;
    width:var(--sidebar-w);height:calc(100vh - var(--topbar-h));
    background:#0d1b2a;overflow-y:auto;z-index:1000;
    transition:transform .3s ease;padding:16px 12px 24px;
    scrollbar-width:thin;scrollbar-color:#1e3a5f transparent}}
  .sidebar-label{{color:#546e7a;font-size:.68rem;font-weight:700;
    letter-spacing:1.5px;text-transform:uppercase;padding:12px 8px 4px}}
  .sidebar .nav-link{{color:#b0bec5;border-radius:8px;padding:9px 12px;
    font-size:.87rem;display:flex;align-items:center;gap:10px;
    text-decoration:none;transition:all .2s;margin-bottom:2px}}
  .sidebar .nav-link i{{width:18px;text-align:center;font-size:.9rem}}
  .sidebar .nav-link:hover,.sidebar .nav-link.active{{background:var(--primary);color:#fff}}
  .sidebar-group summary{{list-style:none;color:#b0bec5;padding:9px 12px;
    border-radius:8px;display:flex;align-items:center;gap:10px;
    cursor:pointer;font-size:.87rem;transition:background .2s;
    margin-bottom:2px;user-select:none}}
  .sidebar-group summary::-webkit-details-marker{{display:none}}
  .sidebar-group summary:hover{{background:#1c2d3e;color:#fff}}
  .sidebar-group summary .caret{{margin-left:auto;transition:transform .25s;font-size:.75rem}}
  .sidebar-group[open] summary .caret{{transform:rotate(90deg)}}
  .sidebar-group[open] summary{{color:#fff;background:#1c2d3e}}
  .sub-links{{padding:4px 0 4px 28px}}
  .sub-links a{{display:flex;align-items:center;gap:8px;color:#78909c;
    font-size:.83rem;padding:7px 10px;border-radius:6px;
    text-decoration:none;transition:all .2s;margin-bottom:1px}}
  .sub-links a:hover{{color:#fff;background:rgba(255,255,255,.07)}}
  .sidebar-divider{{border:none;border-top:1px solid #1c2d3e;margin:10px 0}}
  .sidebar-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:999}}

  .main{{margin-left:var(--sidebar-w);margin-top:var(--topbar-h);
    padding:28px 24px;min-height:calc(100vh - var(--topbar-h))}}

  .page-header{{display:flex;align-items:center;gap:14px;margin-bottom:22px}}
  .page-header-icon{{background:linear-gradient(135deg,#e65100,#fb8c00);
    color:#fff;width:48px;height:48px;border-radius:12px;
    display:flex;align-items:center;justify-content:center;font-size:1.2rem;flex-shrink:0}}
  .page-header h4{{font-size:1.2rem;font-weight:700;margin:0 0 2px}}
  .page-header p{{font-size:.85rem;color:#64748b;margin:0}}

  .summary-strip{{background:#fff;border-radius:12px;padding:14px 20px;
    margin-bottom:24px;box-shadow:0 2px 10px rgba(0,0,0,.06);
    display:flex;align-items:center;gap:12px;flex-wrap:wrap}}
  .sum-badge{{padding:4px 14px;border-radius:20px;font-size:.83rem;font-weight:700}}
  .sum-badge.orange{{background:#fff3e0;color:#e65100}}
  .sum-badge.blue{{background:#e3f2fd;color:#1565c0}}

  .child-section{{margin-bottom:36px}}
  .child-heading{{display:flex;align-items:center;gap:12px;
    background:linear-gradient(135deg,#1565c0 0%,#0d47a1 100%);
    color:#fff;border-radius:14px 14px 0 0;padding:14px 20px}}
  .child-avatar{{width:40px;height:40px;border-radius:50%;
    background:rgba(255,255,255,.2);border:2px solid rgba(255,255,255,.4);
    display:flex;align-items:center;justify-content:center;
    font-size:1.1rem;flex-shrink:0}}
  .child-heading-info h5{{font-size:1rem;font-weight:700;margin:0}}
  .child-heading-info small{{font-size:.78rem;color:rgba(255,255,255,.7)}}
  .child-appt-count{{margin-left:auto;background:rgba(255,255,255,.2);
    padding:3px 14px;border-radius:20px;font-size:.8rem;font-weight:700;white-space:nowrap}}

  .table-card{{background:#fff;border-radius:0 0 14px 14px;
    box-shadow:0 4px 16px rgba(0,0,0,.08);overflow:hidden}}
  .table-wrapper{{overflow-x:auto;-webkit-overflow-scrolling:touch}}
  .appt-table{{width:100%;border-collapse:collapse;min-width:780px}}
  .appt-table thead th{{background:#f0f7ff;color:#1565c0;
    padding:10px 14px;font-size:.79rem;font-weight:700;
    text-align:center;white-space:nowrap;border-bottom:2px solid #bbdefb}}
  .appt-table tbody td{{padding:10px 14px;text-align:center;font-size:.86rem;color:#444;
    border-bottom:1px solid #f0f4f8;vertical-align:middle}}
  .appt-table tbody tr:nth-child(even){{background:#fafcff}}
  .appt-table tbody tr:hover{{background:#f0f7ff}}
  .appt-table tbody tr:last-child td{{border-bottom:none}}
  .appt-table tbody tr.row-rescheduled{{background:#fff8e1!important}}
  .appt-table tbody tr.row-rescheduled:hover{{background:#fff3cd!important}}

  .dose-badge{{display:inline-block;background:#e3f2fd;color:#1565c0;
    border-radius:20px;padding:3px 12px;font-size:.75rem;font-weight:700}}
  .date-strike{{color:#aaa;text-decoration:line-through;font-size:.8rem;display:block}}
  .date-new-pill{{display:inline-block;background:#fff3e0;color:#e65100;
    border:1px solid #ffcc80;border-radius:8px;
    padding:2px 9px;font-size:.8rem;font-weight:700;margin-top:2px}}

  /* Mobile cards */
  .mobile-child-section{{display:none;margin-bottom:24px}}
  .mobile-child-heading{{background:linear-gradient(135deg,#1565c0,#0d47a1);
    color:#fff;border-radius:12px 12px 0 0;padding:12px 16px;
    display:flex;align-items:center;gap:10px}}
  .mobile-child-heading span{{font-size:.95rem;font-weight:700}}
  .mobile-child-heading small{{font-size:.78rem;color:rgba(255,255,255,.7);margin-left:auto}}
  .mobile-cards-body{{padding:12px;background:#fff;border-radius:0 0 12px 12px;
    box-shadow:0 3px 12px rgba(0,0,0,.07)}}
  .mobile-appt-card{{background:#f8fbff;border:1px solid #e0e8f0;
    border-radius:10px;padding:14px;margin-bottom:12px;
    box-shadow:0 1px 6px rgba(0,0,0,.04)}}
  .mobile-appt-card:last-child{{margin-bottom:0}}
  .mobile-appt-card.rescheduled-card{{border-left:4px solid #fd7e14;background:#fffaf5}}
  .mobile-appt-header{{display:flex;justify-content:space-between;
    align-items:flex-start;margin-bottom:10px;flex-wrap:wrap;gap:6px}}
  .mobile-appt-title{{font-size:.9rem;font-weight:700;color:#1565c0}}
  .mobile-row{{display:flex;justify-content:space-between;align-items:center;
    padding:5px 0;font-size:.84rem;border-bottom:1px dashed #eee}}
  .mobile-row:last-of-type{{border-bottom:none}}
  .mobile-label{{font-weight:600;color:#555}}
  .mobile-value{{color:#222;text-align:right}}
  .mobile-value.new-val{{color:#e65100;font-weight:700}}
  .mobile-actions{{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}}
  .reschedule-note{{background:#fff3e0;border-left:3px solid #fd7e14;
    border-radius:6px;padding:8px 12px;margin-top:8px;font-size:.81rem;color:#7c4d00}}

  .view-btn{{background:#1565c0;color:#fff;border:none;
    padding:5px 13px;border-radius:6px;cursor:pointer;font-size:.82rem;transition:background .2s}}
  .view-btn:hover{{background:#0d47a1}}
  .complete-btn{{background:#2e7d32;color:#fff;border:none;
    padding:5px 13px;border-radius:6px;cursor:pointer;font-size:.82rem;transition:background .2s}}
  .complete-btn:hover{{background:#1b5e20}}
  .complete-btn:disabled{{background:#6c757d;cursor:not-allowed;opacity:.65}}

  .badge-pending{{background:#ffc107;color:#333;padding:3px 10px;border-radius:12px;font-size:.77rem;font-weight:600}}
  .badge-confirmed{{background:#2e7d32;color:#fff;padding:3px 10px;border-radius:12px;font-size:.77rem;font-weight:600}}
  .badge-rescheduled{{background:#e65100;color:#fff;padding:3px 10px;border-radius:12px;font-size:.77rem;font-weight:600}}
  .badge-notified{{background:#7b1fa2;color:#fff;padding:3px 10px;border-radius:12px;font-size:.77rem;font-weight:600}}

  .info-label{{font-weight:bold;color:#555;min-width:130px;display:inline-block}}
  .box-original{{background:#f0f9ff;border-left:4px solid #1565c0;border-radius:8px;padding:14px 18px;margin-bottom:12px}}
  .box-reschedule{{background:#fff3e0;border-left:4px solid #fd7e14;border-radius:8px;padding:14px 18px;margin-bottom:12px}}
  .box-child-info{{background:#f0fff4;border-left:4px solid #2e7d32;border-radius:8px;padding:14px 18px;margin-bottom:12px}}

  .empty-state{{text-align:center;padding:60px 20px;background:#fff;
    border-radius:14px;box-shadow:0 2px 12px rgba(0,0,0,.07)}}
  .empty-state i{{font-size:3rem;color:#cbd5e1;margin-bottom:16px;display:block}}
  .empty-state h5{{color:#64748b;font-weight:600}}
  .empty-state p{{font-size:.88rem;color:#94a3b8}}

  @media(max-width:991px){{
    .sidebar{{transform:translateX(-100%)}}
    .sidebar.open{{transform:translateX(0)}}
    .sidebar-overlay.open{{display:block}}
    .main{{margin-left:0}}
    .hamburger{{display:block}}
  }}
  @media(max-width:700px){{
    .table-wrapper{{display:none}}
    .mobile-child-section{{display:block}}
  }}
  @media(max-width:576px){{.main{{padding:16px 10px}}}}
</style>
</head>
<body>

<!-- TOPBAR -->
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

<!-- SIDEBAR -->
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
      <a href="parentaddappointments.py?parent_id={parent_id}"><i class="fa fa-plus"></i> Add Appointment</a>
      <a href="parentpendingappointments.py?parent_id={parent_id}" style="color:#fff;background:rgba(255,255,255,.1);">
        <i class="fa fa-clock"></i> Pending
      </a>
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

<!-- MAIN -->
<main class="main">
  <div class="page-header">
    <div class="page-header-icon"><i class="fa fa-clock"></i></div>
    <div>
      <h4>Pending Appointments</h4>
      <p>Track and manage your children's upcoming vaccine appointments</p>
    </div>
  </div>

  <div class="summary-strip">
    <i class="fa-solid fa-hourglass-half" style="color:#e65100"></i>
    <span style="font-size:.9rem;color:#475569;font-weight:600;">Total Pending</span>
    <span class="sum-badge orange">{total_records} Record{"s" if total_records != 1 else ""}</span>
    <span class="sum-badge blue"><i class="fa fa-children me-1"></i>{total_children} Child{"ren" if total_children != 1 else ""}</span>
  </div>
""")

all_modals = ""

if child_groups:
    for cid, appt_list in child_groups.items():
        cname      = child_names[cid]
        appt_count = len(appt_list)

        # ===== DESKTOP TABLE =====
        print(f"""
  <div class="child-section">
    <div class="child-heading">
      <div class="child-avatar"><i class="fa-solid fa-child"></i></div>
      <div class="child-heading-info">
        <h5>{cname}</h5>
        <small>Vaccine appointments pending</small>
      </div>
      <span class="child-appt-count">{appt_count} Appointment{"s" if appt_count != 1 else ""}</span>
    </div>
    <div class="table-card">
      <div class="table-wrapper">
        <table class="appt-table">
          <thead>
            <tr>
              <th>#</th>
              <th><i class="fa-solid fa-syringe me-1"></i>Vaccine</th>
              <th>Dose</th>
              <th><i class="fa-solid fa-hospital me-1"></i>Hospital</th>
              <th><i class="fa-solid fa-calendar me-1"></i>Date</th>
              <th><i class="fa-solid fa-clock me-1"></i>Time</th>
              <th>Status</th>
              <th>View</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>""")

        for idx, appt in enumerate(appt_list, start=1):
            (appt_id, a_child_id, a_child_name,
             vaccine_id, vaccine_name,
             dose_number,
             hospital_id, hospital_name,
             appointment_date, appointment_time,
             reschedule_date, reschedule_time,
             status) = appt

            vaccine_name  = str(vaccine_name)  if vaccine_name  else "—"
            dose_number   = int(dose_number)   if dose_number is not None else 1
            hospital_name = str(hospital_name) if hospital_name else "Not Assigned"
            status        = str(status).strip().lower() if status else "pending"

            orig_date = str(appointment_date) if appointment_date else "Not Set"
            orig_time = str(appointment_time) if appointment_time else "Not Set"
            r_date    = str(reschedule_date)  if reschedule_date  else None
            r_time    = str(reschedule_time)  if reschedule_time  else None

            is_rescheduled = (
                status == "rescheduled" and r_date is not None and
                (r_date != orig_date or r_time is not None)
            )

            eff_raw        = reschedule_date if (status == "rescheduled" and reschedule_date) else appointment_date
            effective_date = to_date(eff_raw)
            is_disabled    = today < effective_date if effective_date is not None else True
            btn_disabled   = "disabled" if is_disabled else ""
            btn_title      = f'title="Appointment on {effective_date}"' if is_disabled else 'title="Mark as completed"'

            if status == "pending":
                badge     = "<span class='badge-pending'><i class='fa fa-clock me-1'></i>Pending</span>"
                row_class = ""
            elif status == "confirmed":
                badge     = "<span class='badge-confirmed'><i class='fa fa-check me-1'></i>Confirmed</span>"
                row_class = ""
            elif status == "rescheduled":
                badge     = "<span class='badge-rescheduled'><i class='fa fa-rotate me-1'></i>Rescheduled</span>"
                row_class = "row-rescheduled"
            else:
                badge     = "<span class='badge-notified'><i class='fa fa-bell me-1'></i>Notified</span>"
                row_class = ""

            if is_rescheduled:
                show_date = r_date
                show_time = r_time if r_time else orig_time
                date_cell = (f'<span class="date-strike">{orig_date}</span>'
                             f'<span class="date-new-pill"><i class="fa fa-rotate me-1"></i>{show_date}</span>')
                time_cell = (f'<span class="date-strike">{orig_time}</span>'
                             f'<span class="date-new-pill">{show_time}</span>')
            else:
                date_cell = orig_date
                time_cell = orig_time

            print(f"""
            <tr class="{row_class}">
              <td>{idx}</td>
              <td><b>{vaccine_name}</b></td>
              <td><span class="dose-badge">Dose {dose_number}</span></td>
              <td>{hospital_name}</td>
              <td>{date_cell}</td>
              <td>{time_cell}</td>
              <td>{badge}</td>
              <td>
                <button class="view-btn" data-bs-toggle="modal" data-bs-target="#modal{appt_id}">
                  <i class="fa fa-eye me-1"></i>View
                </button>
              </td>
              <td>
                <form method="post" action="parentcompletedappointments.py" style="display:inline"
                      onsubmit="return confirm('Mark this appointment as completed?');">
                  <input type="hidden" name="parent_id" value="{parent_id}">
                  <input type="hidden" name="cv_id"     value="{appt_id}">
                  <button type="submit" class="complete-btn" {btn_disabled} {btn_title}>
                    <i class="fa fa-check me-1"></i>Done
                  </button>
                </form>
              </td>
            </tr>""")

            # Build modal
            reschedule_box = ""
            if is_rescheduled:
                show_r_time = r_time if r_time else orig_time
                reschedule_box = f"""
        <div class="box-reschedule">
          <h6 class="fw-bold mb-3" style="color:#e65100">
            <i class="fa fa-rotate me-2"></i>Rescheduled Appointment
          </h6>
          <div class="row g-2">
            <div class="col-12 col-sm-6">
              <p class="mb-1"><span class="info-label">New Date</span>:
                <strong style="color:#e65100">{r_date}</strong></p>
            </div>
            <div class="col-12 col-sm-6">
              <p class="mb-0"><span class="info-label">New Time</span>:
                <strong style="color:#e65100">{show_r_time}</strong></p>
            </div>
          </div>
          <p class="mb-0 mt-2" style="font-size:.8rem;color:#7c4d00">
            <i class="fa fa-circle-info me-1"></i>Original was <s>{orig_date} at {orig_time}</s>
          </p>
        </div>"""

            all_modals += f"""
<div class="modal fade" id="modal{appt_id}" tabindex="-1">
  <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header" style="background:#1565c0;color:#fff">
        <h5 class="modal-title">
          <i class="fa fa-info-circle me-2"></i>Appointment Details — {cname}
        </h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <div class="box-child-info">
          <h6 class="fw-bold text-success mb-3">
            <i class="fa fa-child me-2"></i>Child &amp; Vaccine Info
          </h6>
          <div class="row g-2">
            <div class="col-12 col-sm-6">
              <p class="mb-2"><span class="info-label">Child Name</span>: <strong>{cname}</strong></p>
              <p class="mb-2"><span class="info-label">Vaccine</span>: {vaccine_name}</p>
            </div>
            <div class="col-12 col-sm-6">
              <p class="mb-2"><span class="info-label">Dose</span>: <span class="dose-badge">Dose {dose_number}</span></p>
              <p class="mb-2"><span class="info-label">Hospital</span>: {hospital_name}</p>
            </div>
          </div>
          <p class="mb-0"><span class="info-label">Status</span>: {badge}</p>
        </div>
        <div class="box-original">
          <h6 class="fw-bold text-primary mb-3">
            <i class="fa fa-calendar-check me-2"></i>Original Appointment
          </h6>
          <div class="row g-2">
            <div class="col-12 col-sm-6">
              <p class="mb-1"><span class="info-label">Date</span>: {orig_date}</p>
            </div>
            <div class="col-12 col-sm-6">
              <p class="mb-0"><span class="info-label">Time</span>: {orig_time}</p>
            </div>
          </div>
        </div>
        {reschedule_box}
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary btn-sm" data-bs-dismiss="modal">
          <i class="fa fa-xmark me-1"></i>Close
        </button>
      </div>
    </div>
  </div>
</div>"""

        print("""          </tbody>
        </table>
      </div>
    </div>""")

        # ===== MOBILE CARDS =====
        print(f"""
    <div class="mobile-child-section">
      <div class="mobile-child-heading">
        <i class="fa-solid fa-child"></i>
        <span>{cname}</span>
        <small>{appt_count} Appointment{"s" if appt_count != 1 else ""}</small>
      </div>
      <div class="mobile-cards-body">""")

        for idx, appt in enumerate(appt_list, start=1):
            (appt_id, a_child_id, a_child_name,
             vaccine_id, vaccine_name,
             dose_number,
             hospital_id, hospital_name,
             appointment_date, appointment_time,
             reschedule_date, reschedule_time,
             status) = appt

            vaccine_name  = str(vaccine_name)  if vaccine_name  else "—"
            dose_number   = int(dose_number)   if dose_number is not None else 1
            hospital_name = str(hospital_name) if hospital_name else "Not Assigned"
            status        = str(status).strip().lower() if status else "pending"

            orig_date = str(appointment_date) if appointment_date else "Not Set"
            orig_time = str(appointment_time) if appointment_time else "Not Set"
            r_date    = str(reschedule_date)  if reschedule_date  else None
            r_time    = str(reschedule_time)  if reschedule_time  else None

            is_rescheduled = (
                status == "rescheduled" and r_date is not None and
                (r_date != orig_date or r_time is not None)
            )

            eff_raw        = reschedule_date if (status == "rescheduled" and reschedule_date) else appointment_date
            effective_date = to_date(eff_raw)
            is_disabled    = today < effective_date if effective_date is not None else True
            btn_disabled   = "disabled" if is_disabled else ""
            btn_title      = f'title="Appointment on {effective_date}"' if is_disabled else 'title="Mark as completed"'

            if status == "pending":
                badge      = "<span class='badge-pending'><i class='fa fa-clock me-1'></i>Pending</span>"
                card_class = ""
            elif status == "confirmed":
                badge      = "<span class='badge-confirmed'><i class='fa fa-check me-1'></i>Confirmed</span>"
                card_class = ""
            elif status == "rescheduled":
                badge      = "<span class='badge-rescheduled'><i class='fa fa-rotate me-1'></i>Rescheduled</span>"
                card_class = "rescheduled-card"
            else:
                badge      = "<span class='badge-notified'><i class='fa fa-bell me-1'></i>Notified</span>"
                card_class = ""

            if is_rescheduled:
                show_date = r_date
                show_time = r_time if r_time else orig_time
                date_lbl  = "New Date"; time_lbl = "New Time"
                dvc       = "mobile-value new-val"; tvc = "mobile-value new-val"
                r_note    = f'<div class="reschedule-note"><i class="fa fa-rotate me-1"></i>Rescheduled to <strong>{r_date}</strong> at <strong>{show_time}</strong> &mdash; Original: <s>{orig_date}</s></div>'
            else:
                show_date = orig_date; show_time = orig_time
                date_lbl  = "Date"; time_lbl = "Time"
                dvc       = "mobile-value"; tvc = "mobile-value"
                r_note    = ""

            print(f"""
        <div class="mobile-appt-card {card_class}">
          <div class="mobile-appt-header">
            <span class="mobile-appt-title"><i class="fa-solid fa-syringe me-1"></i>{idx}. {vaccine_name}</span>
            {badge}
          </div>
          <div class="mobile-row"><span class="mobile-label">Dose</span>
            <span class="mobile-value"><span class="dose-badge">Dose {dose_number}</span></span></div>
          <div class="mobile-row"><span class="mobile-label">Hospital</span>
            <span class="mobile-value">{hospital_name}</span></div>
          <div class="mobile-row"><span class="mobile-label">{date_lbl}</span>
            <span class="{dvc}">{show_date}</span></div>
          <div class="mobile-row"><span class="mobile-label">{time_lbl}</span>
            <span class="{tvc}">{show_time}</span></div>
          {r_note}
          <div class="mobile-actions">
            <button class="view-btn" data-bs-toggle="modal" data-bs-target="#modal{appt_id}">
              <i class="fa fa-eye me-1"></i>View
            </button>
            <form method="post" action="parentcompletedappointments.py"
                  onsubmit="return confirm('Mark as completed?');">
              <input type="hidden" name="parent_id" value="{parent_id}">
              <input type="hidden" name="cv_id"     value="{appt_id}">
              <button type="submit" class="complete-btn" {btn_disabled} {btn_title}>
                <i class="fa fa-check me-1"></i>Done
              </button>
            </form>
          </div>
        </div>""")

        print("""      </div>
    </div>""")

        print("""  </div>""")

else:
    print("""
  <div class="empty-state">
    <i class="fa-solid fa-calendar-check"></i>
    <h5>No Pending Appointments</h5>
    <p>All appointments are up to date. New ones will appear here once notified.</p>
  </div>""")

# Modals
print(all_modals)

print(f"""
</main>
<script>
function toggleSidebar() {{
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('overlay').classList.toggle('open');
}}
window.addEventListener('resize', function() {{
  if (window.innerWidth > 991) {{
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('overlay').classList.remove('open');
  }}
}});
</script>
</body>
</html>
""")

con.close()