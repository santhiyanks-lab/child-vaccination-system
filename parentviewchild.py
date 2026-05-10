#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
import datetime
import pymysql
import cgi
import cgitb
import sys

cgitb.enable()
sys.stdout.reconfigure(encoding='utf-8')
print("Content-Type:text/html\r\n\r\n")


def add_months(d, months):
    months = int(months)
    month  = d.month - 1 + months
    year   = d.year + month // 12
    month  = month % 12 + 1
    day    = min(d.day, 28)
    return datetime.date(year, month, day)


# ========================= FORM DATA =========================
form = cgi.FieldStorage()
parent_id_raw = form.getfirst("parent_id")

if not parent_id_raw:
    print("<h3 style='color:red;'>Parent ID missing in URL</h3>")
    exit()

parent_id_clean = parent_id_raw.replace("[","").replace("]","").replace("'","").strip()
if not parent_id_clean.isdigit():
    print("<h3 style='color:red;'>Invalid Parent ID</h3>")
    exit()

parent_id  = int(parent_id_clean)
delete_id  = form.getfirst("delete_id")
restore_id = form.getfirst("restore_id")
edit_id    = form.getfirst("edit_id")
save       = form.getfirst("save")

# ========================= DATABASE =========================
con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()


# ========================= HELPERS =========================
def get_all_vaccines():
    cur.execute("""
        SELECT vaccine_id, minimum_age, dose_number
        FROM vaccine
        WHERE status = 'confirmed'
        ORDER BY minimum_age ASC
    """)
    return cur.fetchall()


def create_vaccine_appointments(child_id, dob_value, parent_id_val):
    """
    Insert child_vaccine rows for every confirmed vaccine.
    appointment_date = DOB + minimum_age months, status = pending.
    parent_id is included because child_vaccine table has that column.
    Skips vaccines already assigned to this child.
    """
    if not dob_value:
        return

    if isinstance(dob_value, str):
        try:
            dob_obj = datetime.date.fromisoformat(dob_value)
        except Exception:
            return
    else:
        dob_obj = dob_value

    vaccines = get_all_vaccines()

    # Get vaccine_ids already in child_vaccine for this child
    cur.execute("SELECT vaccine_id FROM child_vaccine WHERE child_id = %s", (child_id,))
    existing = {row[0] for row in cur.fetchall()}

    inserted = 0
    for vac in vaccines:
        vaccine_id  = vac[0]
        min_age     = int(vac[1]) if vac[1] is not None else 0
        dose_number = int(vac[2]) if vac[2] is not None else 1

        if vaccine_id in existing:
            continue   # already has this vaccine — skip

        appt_date = add_months(dob_obj, min_age)

        # *** KEY FIX: include parent_id in INSERT ***
        cur.execute("""
            INSERT INTO child_vaccine
              (child_id, vaccine_id, parent_id, dose_number,
               appointment_date, appointment_time, status)
            VALUES (%s, %s, %s, %s, %s, '09:00:00', 'pending')
        """, (child_id, vaccine_id, parent_id_val, dose_number, appt_date))
        inserted += 1

    if inserted > 0:
        con.commit()


def refresh_vaccine_appointments(child_id, new_dob_value):
    """
    When DOB changes on edit, recalculate appointment_date for all pending vaccines.
    Completed / notified / confirmed vaccines are left untouched.
    """
    if not new_dob_value:
        return

    if isinstance(new_dob_value, str):
        try:
            dob_obj = datetime.date.fromisoformat(new_dob_value)
        except Exception:
            return
    else:
        dob_obj = new_dob_value

    cur.execute("""
        SELECT cv.id, v.minimum_age
        FROM child_vaccine cv
        JOIN vaccine v ON cv.vaccine_id = v.vaccine_id
        WHERE cv.child_id = %s
          AND LOWER(TRIM(cv.status)) = 'pending'
    """, (child_id,))
    rows = cur.fetchall()

    for row in rows:
        cv_id    = row[0]
        min_age  = int(row[1]) if row[1] is not None else 0
        new_date = add_months(dob_obj, min_age)
        cur.execute(
            "UPDATE child_vaccine SET appointment_date = %s WHERE id = %s",
            (new_date, cv_id)
        )

    if rows:
        con.commit()


# ========================= SOFT DELETE =========================
if delete_id and delete_id.isdigit():
    cur.execute("UPDATE children SET is_deleted=1 WHERE child_id=%s", (delete_id,))
    con.commit()
    print(f"<script>alert('Child Deleted Successfully');window.location.href='parentviewchild.py?parent_id={parent_id}';</script>")
    exit()

# ========================= RESTORE =========================
if restore_id and restore_id.isdigit():
    cur.execute("UPDATE children SET is_deleted=0 WHERE child_id=%s", (restore_id,))
    con.commit()
    print(f"<script>alert('Child Restored Successfully');window.location.href='parentviewchild.py?parent_id={parent_id}';</script>")
    exit()

# ========================= UPDATE (SAVE EDIT) =========================
if save:
    child_id = form.getfirst("child_id")
    if child_id and child_id.isdigit():
        child_name          = form.getfirst("child_name")
        dob                 = form.getfirst("dob")
        gender              = form.getfirst("gender")
        blood_group         = form.getfirst("blood_group")
        identification_mark = form.getfirst("identification_mark")
        weight_raw          = form.getfirst("weight") or "0"
        try:
            weight = float(weight_raw)
        except Exception:
            weight = 0

        cur.execute("SELECT dob FROM children WHERE child_id=%s", (child_id,))
        old_row = cur.fetchone()
        old_dob = str(old_row[0]) if old_row else None

        cur.execute("""
            UPDATE children
            SET child_name=%s, dob=%s, gender=%s, weight=%s,
                blood_group=%s, identification_mark=%s
            WHERE child_id=%s
        """, (child_name, dob, gender, weight, blood_group, identification_mark, child_id))
        con.commit()

        # Refresh dates if DOB changed
        if dob and dob != old_dob:
            refresh_vaccine_appointments(int(child_id), dob)

        # Ensure all vaccines assigned (fills missing ones with correct dates)
        create_vaccine_appointments(int(child_id), dob, parent_id)

        print(f"<script>alert('Child Updated Successfully');window.location.href='parentviewchild.py?parent_id={parent_id}';</script>")
        exit()

# ========================= FETCH DATA =========================
cur.execute("""
    SELECT child_id, child_name, dob, gender, weight, blood_group, identification_mark
    FROM children
    WHERE parent_id=%s AND is_deleted=0
    ORDER BY created_at DESC
""", (parent_id,))
children = cur.fetchall()

cur.execute("""
    SELECT child_id, child_name, dob, gender
    FROM children
    WHERE parent_id=%s AND is_deleted=1
""", (parent_id,))
deleted = cur.fetchall()

cur.execute("""
    SELECT age_group, minimum_age, maximum_age, dose_number, description, vaccine_image
    FROM vaccine
    WHERE status = 'confirmed'
    ORDER BY minimum_age ASC
""")
all_doses = cur.fetchall()

today = datetime.date.today()

edit_child = None
if edit_id and edit_id.isdigit():
    cur.execute("""
        SELECT child_id, child_name, dob, gender, weight, blood_group, identification_mark
        FROM children WHERE child_id=%s
    """, (edit_id,))
    edit_child = cur.fetchone()

# ========================= HTML =========================
print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>My Children</title>
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

  .topbar {{
    position: fixed; top: 0; left: 0; right: 0; height: var(--topbar-h);
    background: #0d1b2a; display: flex; align-items: center;
    justify-content: space-between; padding: 0 16px; z-index: 1100;
    box-shadow: 0 2px 10px rgba(0,0,0,.3);
  }}
  .topbar-left {{ display: flex; align-items: center; gap: 12px; }}
  .topbar img {{ height: 40px; width: 40px; border-radius: 50%; border: 2px solid rgba(255,255,255,.4); object-fit: cover; }}
  .topbar .brand {{ color: #fff; font-size: 1rem; font-weight: 700; }}
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
  .sidebar-divider {{ border: none; border-top: 1px solid #1c2d3e; margin: 10px 0; }}
  .sidebar-overlay {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,.55); z-index: 999; backdrop-filter: blur(2px); }}

  .main {{ margin-left: var(--sidebar-w); margin-top: var(--topbar-h); padding: 28px 24px; min-height: calc(100vh - var(--topbar-h)); transition: margin-left .3s; }}

  .page-header {{ display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 22px; }}
  .page-header-left {{ display: flex; align-items: center; gap: 14px; }}
  .page-header-icon {{ background: linear-gradient(135deg, #1565c0, #42a5f5); color: #fff; width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0; box-shadow: 0 4px 12px rgba(21,101,192,.3); }}
  .page-header h4 {{ font-size: 1.2rem; font-weight: 700; margin: 0 0 2px; }}
  .page-header p  {{ font-size: .85rem; color: #64748b; margin: 0; }}
  .btn-add-child {{ background: #2e7d32; color: #fff; border: none; border-radius: 8px; padding: 8px 16px; font-size: .85rem; font-weight: 600; text-decoration: none; display: flex; align-items: center; gap: 6px; transition: background .2s; }}
  .btn-add-child:hover {{ background: #1b5e20; color: #fff; }}

  .edit-card {{ background: #fff; border-radius: 14px; box-shadow: 0 3px 12px rgba(0,0,0,.08); padding: 22px; margin-bottom: 22px; border-left: 5px solid #ffc107; }}
  .edit-card h5 {{ font-size: 1rem; font-weight: 700; color: #1e293b; margin-bottom: 12px; }}
  .dob-note {{ background: #e3f2fd; border-left: 4px solid #1565c0; border-radius: 8px; padding: 10px 14px; font-size: .82rem; color: #1565c0; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }}
  .form-label {{ font-weight: 600; color: #334155; margin-bottom: 5px; display: block; font-size: .88rem; }}
  .form-control, .form-select {{ border-radius: 8px; border: 1.5px solid #e2e8f0; padding: 9px 13px; font-size: .9rem; width: 100%; transition: border-color .2s; }}
  .form-control:focus, .form-select:focus {{ border-color: #1565c0; outline: none; box-shadow: 0 0 0 3px rgba(21,101,192,.12); }}
  .btn-save {{ background: linear-gradient(135deg, #2e7d32, #43a047); color: #fff; border: none; border-radius: 8px; padding: 11px; font-size: .92rem; font-weight: 600; width: 100%; cursor: pointer; transition: opacity .2s; margin-top: 4px; display: flex; align-items: center; justify-content: center; gap: 8px; }}
  .btn-save:hover {{ opacity: .9; }}

  .table-card {{ background: #fff; border-radius: 14px; box-shadow: 0 3px 12px rgba(0,0,0,.08); overflow: hidden; margin-bottom: 24px; }}
  .table-card-header {{ padding: 13px 20px; font-weight: 700; font-size: .92rem; display: flex; align-items: center; gap: 8px; color: #fff; }}
  .table-card-header.dark {{ background: #0d1b2a; }}
  .table-card-header.danger {{ background: #c62828; }}
  .table-wrapper {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
  .children-table {{ width: 100%; border-collapse: collapse; min-width: 780px; }}
  .children-table thead th {{ background: #e3f2fd; color: #1565c0; padding: 11px 12px; font-size: .83rem; font-weight: 700; text-align: center; white-space: nowrap; border-bottom: 2px solid #bbdefb; }}
  .children-table tbody td {{ padding: 10px 12px; text-align: center; font-size: .86rem; color: #444; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }}
  .children-table tbody tr:nth-child(even) {{ background: #fafafa; }}
  .children-table tbody tr:hover {{ background: #f0f7ff; }}
  .children-table tbody tr:last-child td {{ border-bottom: none; }}

  .mobile-child-cards {{ display: none; padding: 14px; }}
  .mobile-child-card {{ background: #f8f9fa; border: 1px solid #e0e8f0; border-radius: 10px; padding: 14px; margin-bottom: 12px; }}
  .mobile-child-card:last-child {{ margin-bottom: 0; }}
  .mobile-child-title {{ font-weight: 700; color: #1565c0; font-size: .95rem; margin-bottom: 10px; display: flex; align-items: center; gap: 6px; }}
  .mobile-row {{ display: flex; justify-content: space-between; align-items: center; padding: 5px 0; font-size: .855rem; border-bottom: 1px dashed #ddd; }}
  .mobile-row:last-of-type {{ border-bottom: none; }}
  .mobile-label {{ font-weight: 600; color: #555; }}
  .mobile-value {{ color: #222; text-align: right; }}
  .mobile-actions {{ display: flex; gap: 6px; flex-wrap: wrap; margin-top: 12px; }}

  .btn-edit {{ background: #ffc107; color: #333; border: none; padding: 5px 12px; border-radius: 6px; cursor: pointer; font-size: .82rem; text-decoration: none; display: inline-flex; align-items: center; gap: 4px; transition: background .2s; white-space: nowrap; }}
  .btn-edit:hover {{ background: #e0a800; color: #333; }}
  .btn-del {{ background: #c62828; color: #fff; border: none; padding: 5px 12px; border-radius: 6px; cursor: pointer; font-size: .82rem; text-decoration: none; display: inline-flex; align-items: center; gap: 4px; transition: background .2s; white-space: nowrap; }}
  .btn-del:hover {{ background: #b71c1c; color: #fff; }}
  .btn-view {{ background: #0dcaf0; color: #333; border: none; padding: 5px 12px; border-radius: 6px; cursor: pointer; font-size: .82rem; display: inline-flex; align-items: center; gap: 4px; transition: background .2s; white-space: nowrap; }}
  .btn-view:hover {{ background: #0aa8c7; }}
  .btn-restore {{ background: #0dcaf0; color: #333; border: none; padding: 5px 12px; border-radius: 6px; font-size: .82rem; text-decoration: none; display: inline-flex; align-items: center; gap: 4px; transition: background .2s; white-space: nowrap; }}
  .btn-restore:hover {{ background: #0aa8c7; color: #333; }}

  .blood-badge {{ background: #c62828; color: #fff; padding: 2px 10px; border-radius: 20px; font-weight: bold; font-size: .78rem; }}
  .appt-date-badge {{ background: #e8f5e9; color: #2e7d32; padding: 2px 10px; border-radius: 20px; font-size: .76rem; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; }}

  .child-info-card {{ background: linear-gradient(135deg, #e8f4fd, #f0f9ff); border-left: 5px solid #1565c0; border-radius: 10px; padding: 16px; margin-bottom: 14px; }}
  .info-row {{ margin-bottom: 7px; display: flex; align-items: flex-start; font-size: .87rem; flex-wrap: wrap; gap: 4px; }}
  .info-row .label {{ font-weight: bold; color: #555; min-width: 130px; display: inline-block; }}
  .info-row .value {{ color: #222; }}
  .vaccine-img {{ height: 40px; width: 50px; object-fit: cover; border-radius: 5px; }}
  .section-divider {{ border: 0; border-top: 2px solid #dee2e6; margin: 16px 0; }}

  @media (max-width: 991px) {{
    .sidebar {{ transform: translateX(-100%); }}
    .sidebar.open {{ transform: translateX(0); }}
    .sidebar-overlay.open {{ display: block; }}
    .main {{ margin-left: 0; }}
    .hamburger {{ display: block; }}
  }}
  @media (max-width: 680px) {{ .table-wrapper {{ display: none; }} .mobile-child-cards {{ display: block; }} }}
  @media (max-width: 576px) {{ .main {{ padding: 16px 10px; }} .edit-card {{ padding: 16px 14px; }} }}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-left">
    <button class="hamburger" onclick="toggleSidebar()"><i class="fa fa-bars"></i></button>
    <img src="./images/logo.jpg" alt="logo" onerror="this.style.display='none'">
    <span class="brand">Child Vaccination</span>
  </div>
  <div class="topbar-right">
    <a href="home.py"><i class="fa fa-right-from-bracket me-1"></i> Logout</a>
  </div>
</div>

<div class="sidebar-overlay" id="overlay" onclick="toggleSidebar()"></div>

<nav class="sidebar" id="sidebar">
  <div class="sidebar-label">Menu</div>
  <a href="parent_dash.py?parent_id={parent_id}" class="nav-link"><i class="fa fa-gauge"></i> Dashboard</a>
  <a href="parent_profile.py?parent_id={parent_id}" class="nav-link"><i class="fa fa-user"></i> My Profile</a>
  <hr class="sidebar-divider">
  <details class="sidebar-group" open>
    <summary><i class="fa-solid fa-child"></i> Child <i class="fa fa-chevron-right caret"></i></summary>
    <div class="sub-links">
      <a href="parentaddchild.py?parent_id={parent_id}"><i class="fa fa-plus"></i> Add Child</a>
      <a href="parentviewchild.py?parent_id={parent_id}" style="color:#fff;background:rgba(255,255,255,.07);">
        <i class="fa fa-eye"></i> View Child
      </a>
    </div>
  </details>
  <hr class="sidebar-divider">
  <details class="sidebar-group">
    <summary><i class="fa-solid fa-calendar-check"></i> Appointments <i class="fa fa-chevron-right caret"></i></summary>
    <div class="sub-links">
      <a href="parentaddappointments.py?parent_id={parent_id}"><i class="fa fa-plus"></i> Add Appointment</a>
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

<main class="main">
<form method="post">
<input type="hidden" name="parent_id" value="{parent_id}">

<div class="page-header">
  <div class="page-header-left">
    <div class="page-header-icon"><i class="fa fa-children"></i></div>
    <div>
      <h4>My Children <span style="font-size:.8rem;color:#888;font-weight:400;">({len(children)} active)</span></h4>
      <p>View and manage your registered children</p>
    </div>
  </div>
  <a href="parentaddchild.py?parent_id={parent_id}" class="btn-add-child">
    <i class="fa fa-plus"></i> Add Child
  </a>
</div>
""")

# ========================= EDIT FORM =========================
if edit_child:
    c = edit_child
    sel_m = "selected" if c[3] == "Male"   else ""
    sel_f = "selected" if c[3] == "Female" else ""
    sel_o = "selected" if c[3] == "Other"  else ""
    print(f"""
<div class="edit-card">
  <h5><i class="fa-solid fa-pen me-2 text-warning"></i>Edit Child Details</h5>
  <div class="dob-note">
    <i class="fa-solid fa-circle-info"></i>
    <span>Changing the Date of Birth will automatically recalculate all pending
    vaccine appointment dates as <strong>DOB + vaccine minimum age</strong>.</span>
  </div>
  <input type="hidden" name="child_id" value="{c[0]}">
  <div class="row g-3">
    <div class="col-12 col-sm-6">
      <label class="form-label">Child Name</label>
      <input type="text" name="child_name" value="{c[1]}" class="form-control" required>
    </div>
    <div class="col-12 col-sm-6">
      <label class="form-label">Date of Birth</label>
      <input type="date" name="dob" value="{c[2]}" class="form-control" required>
    </div>
    <div class="col-12 col-sm-6">
      <label class="form-label">Gender</label>
      <select name="gender" class="form-select" required>
        <option value="Male"   {sel_m}>Male</option>
        <option value="Female" {sel_f}>Female</option>
        <option value="Other"  {sel_o}>Other</option>
      </select>
    </div>
    <div class="col-12 col-sm-6">
      <label class="form-label">Weight (kg)</label>
      <input type="number" step="0.1" name="weight" value="{c[4] if c[4] else ''}" class="form-control">
    </div>
    <div class="col-12 col-sm-6">
      <label class="form-label">Blood Group</label>
      <input type="text" name="blood_group" value="{c[5] if c[5] else ''}" class="form-control">
    </div>
    <div class="col-12 col-sm-6">
      <label class="form-label">Identification Mark</label>
      <input type="text" name="identification_mark" value="{c[6] if c[6] else ''}" class="form-control">
    </div>
    <div class="col-12">
      <button type="submit" name="save" value="1" class="btn-save">
        <i class="fa-solid fa-floppy-disk"></i> Save Changes
      </button>
    </div>
  </div>
</div>""")

# ========================= ACTIVE CHILDREN TABLE =========================
all_modals = ""

if children:
    print("""
<div class="table-card">
  <div class="table-card-header dark">
    <i class="fa-solid fa-list"></i> Active Children
  </div>
  <div class="table-wrapper">
    <table class="children-table">
      <thead><tr>
        <th>#</th><th>Name</th><th>DOB</th><th>Gender</th>
        <th>Blood Group</th><th>Weight</th>
        <th>Next Vaccine Date</th>
        <th>Actions</th><th>Details</th>
      </tr></thead>
      <tbody>""")

    index = 1
    for row in children:
        child_id_val        = row[0]
        child_name          = row[1]
        dob                 = row[2]
        gender              = row[3]
        weight              = row[4]
        blood_group         = row[5] if row[5] else "Not recorded"
        identification_mark = row[6] if row[6] else "Not recorded"

        dob_obj = dob
        if isinstance(dob_obj, str):
            try: dob_obj = datetime.date.fromisoformat(dob_obj)
            except: dob_obj = None

        if dob_obj:
            age_months  = (today.year - dob_obj.year) * 12 + (today.month - dob_obj.month)
            age_display = f"{age_months // 12} yr {age_months % 12} mo" if age_months >= 12 else f"{age_months} month(s)"
            dob_fmt     = dob_obj.strftime("%d %b %Y")
        else:
            age_months  = -1
            age_display = "Unknown"
            dob_fmt     = str(dob)

        weight_display = f"{weight} kg" if weight else "Not recorded"
        gender_icon    = "fa-mars" if gender == "Male" else ("fa-venus" if gender == "Female" else "fa-genderless")

        # Next pending appointment
        cur.execute("""
            SELECT cv.appointment_date, v.vaccine_name
            FROM child_vaccine cv
            JOIN vaccine v ON cv.vaccine_id = v.vaccine_id
            WHERE cv.child_id = %s
              AND LOWER(TRIM(cv.status)) = 'pending'
              AND cv.appointment_date IS NOT NULL
            ORDER BY cv.appointment_date ASC
            LIMIT 1
        """, (child_id_val,))
        next_appt = cur.fetchone()

        if next_appt and next_appt[0]:
            nd  = next_appt[0] if hasattr(next_appt[0], 'strftime') else datetime.date.fromisoformat(str(next_appt[0]))
            nds = nd.strftime("%d %b %Y")
            nv  = next_appt[1] if next_appt[1] else ""
            next_appt_cell = (f'<span class="appt-date-badge">'
                              f'<i class="fa-solid fa-calendar-check"></i>{nds}</span>'
                              f'<br><small style="color:#64748b;font-size:.74rem;">{nv}</small>')
        else:
            next_appt_cell = '<span style="color:#bbb;font-size:.8rem;">—</span>'

        print(f"""
        <tr>
          <td>{index}</td>
          <td><b>{child_name}</b></td>
          <td>{dob_fmt}</td>
          <td>{gender}</td>
          <td><span class="blood-badge">{blood_group}</span></td>
          <td>{weight_display}</td>
          <td>{next_appt_cell}</td>
          <td>
            <div style="display:flex;gap:5px;justify-content:center;flex-wrap:wrap;">
              <a href="parentviewchild.py?parent_id={parent_id}&edit_id={child_id_val}" class="btn-edit">
                <i class="fa-solid fa-pen"></i> Edit
              </a>
              <a href="parentviewchild.py?parent_id={parent_id}&delete_id={child_id_val}"
                 onclick="return confirm('Delete this child?')" class="btn-del">
                <i class="fa-solid fa-trash"></i> Delete
              </a>
            </div>
          </td>
          <td>
            <button type="button" class="btn-view"
                    data-bs-toggle="modal" data-bs-target="#vaccineModal{child_id_val}">
              <i class="fa-solid fa-eye"></i> Details
            </button>
          </td>
        </tr>""")

        # ===== BUILD MODAL =====
        child_details_html  = "<div class='child-info-card'>"
        child_details_html += "<h6 class='fw-bold mb-3 text-primary'><i class='fa-solid fa-id-card me-2'></i>Child Information</h6>"
        child_details_html += "<div class='row'><div class='col-12 col-sm-6'>"
        child_details_html += f"<div class='info-row'><span class='label'><i class='fa-solid fa-user me-1 text-primary'></i> Name</span><span class='value'>{child_name}</span></div>"
        child_details_html += f"<div class='info-row'><span class='label'><i class='fa-solid fa-calendar me-1 text-primary'></i> DOB</span><span class='value'>{dob_fmt}</span></div>"
        child_details_html += f"<div class='info-row'><span class='label'><i class='fa-solid {gender_icon} me-1 text-primary'></i> Gender</span><span class='value'>{gender}</span></div>"
        child_details_html += f"<div class='info-row'><span class='label'><i class='fa-solid fa-cake-candles me-1 text-primary'></i> Age</span><span class='value'>{age_display}</span></div>"
        child_details_html += "</div><div class='col-12 col-sm-6'>"
        child_details_html += f"<div class='info-row'><span class='label'><i class='fa-solid fa-weight-scale me-1 text-primary'></i> Weight</span><span class='value'>{weight_display}</span></div>"
        child_details_html += f"<div class='info-row'><span class='label'><i class='fa-solid fa-droplet me-1 text-danger'></i> Blood Group</span><span class='value'><span class='blood-badge'>{blood_group}</span></span></div>"
        child_details_html += f"<div class='info-row'><span class='label'><i class='fa-solid fa-fingerprint me-1 text-primary'></i> ID Mark</span><span class='value'>{identification_mark}</span></div>"
        child_details_html += "</div></div></div>"

        # Vaccine schedule per child with appointment_date
        cur.execute("""
            SELECT v.age_group, v.minimum_age, v.maximum_age, v.dose_number,
                   v.description, v.vaccine_image, v.vaccine_name,
                   cv.appointment_date, cv.status
            FROM child_vaccine cv
            JOIN vaccine v ON cv.vaccine_id = v.vaccine_id
            WHERE cv.child_id = %s
            ORDER BY v.minimum_age ASC
        """, (child_id_val,))
        child_vaccines = cur.fetchall()

        if child_vaccines:
            vaccine_html  = "<h6 class='fw-bold mb-3'><i class='fa-solid fa-syringe me-2 text-primary'></i>Vaccine Schedule</h6>"
            vaccine_html += "<div style='overflow-x:auto;'><table style='width:100%;border-collapse:collapse;min-width:560px;'>"
            vaccine_html += "<thead><tr style='background:#0d1b2a;color:white;'>"
            for th in ["#","Vaccine","Age Range","Dose","Description","Image","Appt. Date","Status"]:
                vaccine_html += f"<th style='padding:8px 10px;font-size:0.79rem;text-align:center;white-space:nowrap;'>{th}</th>"
            vaccine_html += "</tr></thead><tbody>"

            for i, v in enumerate(child_vaccines, 1):
                vac_name  = str(v[6]) if v[6] else ""
                min_age   = int(v[1]) if v[1] is not None else 0
                max_age   = int(v[2]) if v[2] is not None else 0
                dose_num  = str(v[3]) if v[3] else ""
                desc      = str(v[4]) if v[4] else ""
                img_path  = str(v[5]) if v[5] else ""
                appt_date = v[7]
                cv_status = str(v[8]).strip().lower() if v[8] else "pending"

                if appt_date:
                    ad  = appt_date if hasattr(appt_date, 'strftime') else datetime.date.fromisoformat(str(appt_date))
                    ads = ad.strftime("%d %b %Y")
                    date_cell = f"<span style='color:#2e7d32;font-weight:600;white-space:nowrap;'><i class='fa-solid fa-calendar-check me-1'></i>{ads}</span>"
                else:
                    date_cell = "<span style='color:#bbb;'>—</span>"

                if cv_status in ("taken", "completed"):
                    badge = "<span class='badge bg-success'>Completed</span>"
                elif cv_status == "notified":
                    badge = "<span class='badge bg-warning text-dark'>Notified</span>"
                elif cv_status == "confirmed":
                    badge = "<span class='badge bg-info text-dark'>Confirmed</span>"
                elif cv_status == "pending":
                    if age_months < 0:
                        badge = "<span class='badge bg-secondary'>Unknown</span>"
                    elif age_months < min_age:
                        badge = "<span class='badge bg-primary'>Upcoming</span>"
                    elif min_age <= age_months <= max_age:
                        badge = "<span class='badge bg-warning text-dark'>Due Now</span>"
                    else:
                        badge = "<span class='badge bg-danger'>Overdue</span>"
                else:
                    badge = f"<span class='badge bg-secondary'>{cv_status.capitalize()}</span>"

                img_tag    = f"<img src='{img_path}' class='vaccine-img' alt='vac'>" if img_path else "<span class='text-muted'>-</span>"
                short_desc = (desc[:60] + "...") if len(desc) > 60 else desc
                bg         = "#f8f9fa" if i % 2 == 0 else "white"

                vaccine_html += f"<tr style='background:{bg};border-bottom:1px solid #eee;'>"
                vaccine_html += f"<td style='padding:7px 9px;text-align:center;font-size:0.8rem;'>{i}</td>"
                vaccine_html += f"<td style='padding:7px 9px;text-align:center;font-size:0.8rem;'><b>{vac_name}</b></td>"
                vaccine_html += f"<td style='padding:7px 9px;text-align:center;font-size:0.8rem;white-space:nowrap;'>{min_age}–{max_age} mo</td>"
                vaccine_html += f"<td style='padding:7px 9px;text-align:center;font-size:0.8rem;'>Dose {dose_num}</td>"
                vaccine_html += f"<td style='padding:7px 9px;font-size:0.76rem;'>{short_desc}</td>"
                vaccine_html += f"<td style='padding:7px 9px;text-align:center;'>{img_tag}</td>"
                vaccine_html += f"<td style='padding:7px 9px;text-align:center;font-size:0.8rem;'>{date_cell}</td>"
                vaccine_html += f"<td style='padding:7px 9px;text-align:center;'>{badge}</td>"
                vaccine_html += "</tr>"

            vaccine_html += "</tbody></table></div>"
            vaccine_html += "<div class='mt-2 small text-muted'>"
            vaccine_html += "<span class='badge bg-primary me-1'>Upcoming</span>Not yet due &nbsp;"
            vaccine_html += "<span class='badge bg-warning text-dark me-1'>Due Now</span>Within age window &nbsp;"
            vaccine_html += "<span class='badge bg-danger me-1'>Overdue</span>Age window passed &nbsp;"
            vaccine_html += "<span class='badge bg-success me-1'>Completed</span>Vaccine taken"
            vaccine_html += "</div>"
        else:
            vaccine_html = "<div class='alert alert-info'><i class='fa-solid fa-circle-info me-2'></i>No vaccine records found. Click <strong>Edit &rarr; Save</strong> on this child to auto-generate the schedule.</div>"

        all_modals += f"""
<div class="modal fade" id="vaccineModal{child_id_val}" tabindex="-1">
  <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header bg-primary text-white">
        <h5 class="modal-title"><i class="fa-solid fa-child me-2"></i>Details &mdash; {child_name}</h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        {child_details_html}
        <hr class="section-divider">
        {vaccine_html}
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">
          <i class="fa-solid fa-xmark me-1"></i>Close
        </button>
      </div>
    </div>
  </div>
</div>"""
        index += 1

    print("""
      </tbody>
    </table>
  </div>
</div>""")

    # ===== MOBILE CARDS =====
    print("""<div class="mobile-child-cards">""")
    index = 1
    for row in children:
        child_id_val  = row[0]
        child_name    = row[1]
        dob           = row[2]
        gender        = row[3]
        weight        = row[4]
        blood_group   = row[5] if row[5] else "Not recorded"

        dob_obj = dob
        if isinstance(dob_obj, str):
            try: dob_obj = datetime.date.fromisoformat(dob_obj)
            except: dob_obj = None

        dob_fmt        = dob_obj.strftime("%d %b %Y") if dob_obj else str(dob)
        weight_display = f"{weight} kg" if weight else "Not recorded"

        cur.execute("""
            SELECT cv.appointment_date, v.vaccine_name
            FROM child_vaccine cv
            JOIN vaccine v ON cv.vaccine_id = v.vaccine_id
            WHERE cv.child_id = %s
              AND LOWER(TRIM(cv.status)) = 'pending'
              AND cv.appointment_date IS NOT NULL
            ORDER BY cv.appointment_date ASC
            LIMIT 1
        """, (child_id_val,))
        next_a = cur.fetchone()
        if next_a and next_a[0]:
            nd  = next_a[0] if hasattr(next_a[0], 'strftime') else datetime.date.fromisoformat(str(next_a[0]))
            nds = nd.strftime("%d %b %Y")
            next_appt_mobile = f'<span class="appt-date-badge"><i class="fa-solid fa-calendar-check"></i>{nds}</span>'
        else:
            next_appt_mobile = '<span style="color:#bbb">—</span>'

        print(f"""
  <div class="mobile-child-card">
    <div class="mobile-child-title"><i class="fa-solid fa-child-reaching"></i> {index}. {child_name}</div>
    <div class="mobile-row"><span class="mobile-label">Date of Birth</span><span class="mobile-value">{dob_fmt}</span></div>
    <div class="mobile-row"><span class="mobile-label">Gender</span><span class="mobile-value">{gender}</span></div>
    <div class="mobile-row"><span class="mobile-label">Blood Group</span><span class="mobile-value"><span class="blood-badge">{blood_group}</span></span></div>
    <div class="mobile-row"><span class="mobile-label">Weight</span><span class="mobile-value">{weight_display}</span></div>
    <div class="mobile-row"><span class="mobile-label">Next Vaccine</span><span class="mobile-value">{next_appt_mobile}</span></div>
    <div class="mobile-actions">
      <a href="parentviewchild.py?parent_id={parent_id}&edit_id={child_id_val}" class="btn-edit"><i class="fa-solid fa-pen"></i> Edit</a>
      <a href="parentviewchild.py?parent_id={parent_id}&delete_id={child_id_val}" onclick="return confirm('Delete this child?')" class="btn-del"><i class="fa-solid fa-trash"></i> Delete</a>
      <button type="button" class="btn-view" data-bs-toggle="modal" data-bs-target="#vaccineModal{child_id_val}"><i class="fa-solid fa-eye"></i> Details</button>
    </div>
  </div>""")
        index += 1
    print("""</div>""")

else:
    print(f"""
<div class="alert alert-info text-center" style="border-radius:10px;">
  <i class="fa fa-inbox me-2 fa-lg"></i>No children found.
  <a href="parentaddchild.py?parent_id={parent_id}" class="alert-link ms-2">Add a child</a>
</div>""")

print(all_modals)

# ========================= DELETED CHILDREN =========================
if deleted:
    print("""
<div class="table-card" style="margin-top:8px;">
  <div class="table-card-header danger"><i class="fa-solid fa-trash"></i> Deleted Children</div>
  <div class="table-wrapper">
    <table class="children-table">
      <thead><tr><th>Name</th><th>DOB</th><th>Gender</th><th>Action</th></tr></thead>
      <tbody>""")
    for row in deleted:
        print(f"""
        <tr>
          <td><b>{row[1]}</b></td><td>{row[2]}</td><td>{row[3]}</td>
          <td><a href="parentviewchild.py?parent_id={parent_id}&restore_id={row[0]}" class="btn-restore">
            <i class="fa-solid fa-rotate-left"></i> Restore</a></td>
        </tr>""")
    print("""</tbody></table></div></div>""")

print("""
</form>
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