#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe

from datetime import timedelta, datetime
import pymysql
import cgi
import cgitb
import sys

cgitb.enable()
sys.stdout.reconfigure(encoding='utf-8')
print("Content-Type:text/html\r\n\r\n")

# ================= FORM DATA =================
form = cgi.FieldStorage()
hid = form.getfirst("parent_id")

# ================= CLEAN AND VALIDATE parent_id =================
if not hid:
    print("<h3 style='color:red;'>Parent ID Missing in URL</h3>")
    exit()

parent_id = hid.replace("[","").replace("]","").replace("'","").strip()

try:
    parent_id = int(parent_id)
except:
    print("<h3 style='color:red;'>Invalid Parent ID</h3>")
    exit()

# ================= DATABASE CONNECTION =================
con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()

# ================= CHECK PARENT EXISTS =================
cur.execute("SELECT parent_id FROM parent WHERE parent_id=%s", (parent_id,))
parent_exists = cur.fetchone()
if not parent_exists:
    print("<h3 style='color:red;'>Parent Not Found in Database</h3>")
    exit()

# ================= GET CHILD COUNT FOR AUTO-INCREMENT DISPLAY =================
cur.execute("SELECT COUNT(*) FROM children WHERE parent_id=%s", (parent_id,))
child_count_row = cur.fetchone()
next_child_no = (child_count_row[0] + 1) if child_count_row else 1

# ================= SAVE CHILD =================
error_msg = ""
if form.getfirst("save"):
    child_name          = form.getfirst("child_name", "").strip()
    dob_str             = form.getfirst("dob", "").strip()
    weight_str          = form.getfirst("weight", "").strip()
    gender              = form.getfirst("gender", "").strip()
    blood_group         = form.getfirst("blood_group", "").strip()
    identification_mark = form.getfirst("identification_mark", "").strip()

    # ---- Validate DOB ----
    dob_error = ""
    dob = None
    if not dob_str:
        dob_error = "Date of Birth is required."
    else:
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            today = datetime.today().date()
            if dob > today:
                dob_error = "Date of Birth cannot be a future date."
            else:
                age_years = (today - dob).days / 365.25
                if age_years > 18:
                    dob_error = "Child must be under 18 years of age."
                elif (today - dob).days < 0:
                    dob_error = "Invalid Date of Birth."
        except ValueError:
            dob_error = "Invalid Date of Birth format."

    # ---- Validate Weight ----
    weight_error = ""
    weight = None
    if not weight_str:
        weight_error = "Weight is required."
    else:
        try:
            weight = float(weight_str)
            if weight < 1.0:
                weight_error = "Weight must be at least 1 kg. A newborn's minimum recorded weight is 1 kg."
            elif weight > 50.0:
                weight_error = "Weight cannot exceed 50 kg for a child."
        except ValueError:
            weight_error = "Invalid weight value."

    # ---- Validate Gender ----
    gender_error = ""
    valid_genders = ["Male", "Female", "Other"]
    if not gender or gender not in valid_genders:
        gender_error = "Please select a valid gender (Male, Female, or Other)."

    # ---- Validate Blood Group ----
    blood_group_error = ""
    valid_bg = ["A+","A-","B+","B-","AB+","AB-","O+","O-","No Idea"]
    if not blood_group or blood_group not in valid_bg:
        blood_group_error = "Please select a valid blood group."

    # ---- Validate other fields ----
    name_error = "" if child_name else "Child Name is required."
    mark_error = "" if identification_mark else "Identification Mark is required."

    # ---- If no errors, save ----
    if not any([dob_error, weight_error, gender_error, blood_group_error, name_error, mark_error]):
        try:
            # Get child_no = count of existing children for this parent + 1
            cur.execute("SELECT COUNT(*) FROM children WHERE parent_id=%s", (parent_id,))
            existing = cur.fetchone()
            child_no = (existing[0] + 1) if existing else 1

            cur.execute("""
                INSERT INTO children
                (parent_id, child_no, child_name, dob, weight, gender, blood_group, identification_mark)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (parent_id, child_no, child_name, dob_str, weight, gender, blood_group, identification_mark))

            child_id = cur.lastrowid

            cur.execute("SELECT vaccine_id FROM vaccine WHERE status='confirmed'")
            vaccines = cur.fetchall()

            for vaccine in vaccines:
                vaccine_id = vaccine[0]
                cur.execute("""
                    INSERT INTO child_vaccine (child_id, parent_id, vaccine_id, status)
                    VALUES (%s, %s, %s, 'pending')
                """, (child_id, parent_id, vaccine_id))

            con.commit()

            print(f"""
            <script>
            alert("Child #{child_no} Added Successfully & Vaccine Schedule Created");
            window.location.href="parentviewchild.py?parent_id={parent_id}";
            </script>
            """)
            exit()

        except Exception as e:
            con.rollback()
            error_msg = f"Database Error: {e}"
    else:
        # Collect all errors into one message for server-side fallback
        all_errors = [e for e in [name_error, dob_error, weight_error, gender_error, blood_group_error, mark_error] if e]
        error_msg = " | ".join(all_errors)

# ================= HTML =================
print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Add Child</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
  :root {{
    --sidebar-w: 260px;
    --topbar-h: 60px;
    --primary: #1565c0;
    --bg: #f0f4f8;
    --error: #dc2626;
    --error-bg: #fef2f2;
    --error-border: #fca5a5;
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
    display: flex; flex-direction: column; align-items: center;
  }}

  /* ===== PAGE HEADER ===== */
  .page-header {{
    display: flex; align-items: center; gap: 14px;
    margin-bottom: 24px; width: 100%; max-width: 680px;
  }}
  .page-header-icon {{
    background: linear-gradient(135deg, #1565c0, #42a5f5);
    color: #fff; width: 48px; height: 48px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; flex-shrink: 0;
    box-shadow: 0 4px 12px rgba(21,101,192,.3);
  }}
  .page-header h4 {{ font-size: 1.2rem; font-weight: 700; margin: 0 0 2px; }}
  .page-header p {{ font-size: .85rem; color: #64748b; margin: 0; }}

  /* ===== FORM CARD ===== */
  .form-card {{
    background: #fff; border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,.08);
    padding: 32px; width: 100%; max-width: 680px;
  }}
  .form-label {{
    font-weight: 600; color: #334155; margin-bottom: 6px; display: block;
  }}
  .form-select, .form-control {{
    border-radius: 8px; border: 1.5px solid #e2e8f0;
    padding: 10px 14px; font-size: .92rem;
    transition: border-color .2s, box-shadow .2s; width: 100%;
  }}
  .form-select:focus, .form-control:focus {{
    border-color: #1565c0;
    box-shadow: 0 0 0 3px rgba(21,101,192,.12); outline: none;
  }}
  .form-select.is-invalid, .form-control.is-invalid {{
    border-color: var(--error) !important;
    background-color: var(--error-bg);
  }}
  .invalid-feedback {{
    display: block; color: var(--error); font-size: .8rem;
    margin-top: 4px; display: flex; align-items: center; gap: 4px;
  }}

  /* Child Number Badge */
  .child-no-badge {{
    display: flex; align-items: center; gap: 10px;
    background: linear-gradient(135deg, #e8f4fd, #dbeafe);
    border: 1.5px solid #93c5fd; border-radius: 10px;
    padding: 12px 16px; margin-bottom: 20px;
  }}
  .child-no-badge .badge-icon {{
    background: #1565c0; color: #fff; width: 36px; height: 36px;
    border-radius: 8px; display: flex; align-items: center;
    justify-content: center; font-size: 1rem; font-weight: 700; flex-shrink: 0;
  }}
  .child-no-badge .badge-text {{ font-size: .85rem; color: #1e40af; }}
  .child-no-badge .badge-text strong {{ font-size: 1.1rem; }}

  /* Server error alert */
  .alert-server {{
    background: var(--error-bg); border: 1px solid var(--error-border);
    color: var(--error); border-radius: 10px; padding: 12px 16px;
    font-size: .88rem; margin-bottom: 20px; display: flex; gap: 8px;
    align-items: flex-start;
  }}

  .btn-save {{
    background: linear-gradient(135deg, #1565c0, #1976d2);
    color: #fff; border: none; border-radius: 10px;
    padding: 13px; font-size: 1rem; font-weight: 600;
    width: 100%; cursor: pointer;
    transition: opacity .2s, transform .1s;
    margin-top: 8px; display: flex;
    align-items: center; justify-content: center; gap: 8px;
  }}
  .btn-save:hover {{ opacity: .9; transform: translateY(-1px); }}
  .btn-save:active {{ transform: translateY(0); }}

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
    .form-card {{ padding: 20px 16px; }}
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
    <div><span class="brand">Child Vaccination</span></div>
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
  <details class="sidebar-group" open>
    <summary>
      <i class="fa-solid fa-child"></i> Child
      <i class="fa fa-chevron-right caret"></i>
    </summary>
    <div class="sub-links">
      <a href="parentaddchild.py?parent_id={parent_id}" style="color:#fff;background:rgba(255,255,255,.1);">
        <i class="fa fa-plus"></i> Add Child
      </a>
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
    <div class="page-header-icon"><i class="fa fa-child-reaching"></i></div>
    <div>
      <h4>Add Child</h4>
      <p>Register a new child and assign vaccination schedule</p>
    </div>
  </div>

  <div class="form-card">

    <!-- Child Number Badge -->
    <div class="child-no-badge">
      <div class="badge-icon">#{next_child_no}</div>
      <div class="badge-text">
        <div style="color:#64748b; font-size:.78rem; margin-bottom:2px;">CHILD NUMBER (Auto)</div>
        <strong>Child No. {next_child_no}</strong> will be assigned to this child
      </div>
    </div>

    <!-- Server-side error (fallback) -->
    {"" if not error_msg else f'<div class="alert-server"><i class="fa fa-circle-exclamation mt-1"></i><div>{error_msg}</div></div>'}

    <form method="post" action="parentaddchild.py?parent_id={parent_id}" id="childForm" novalidate>
      <input type="hidden" name="parent_id" value="{parent_id}">

      <div class="row g-3 mb-3">
        <div class="col-12 col-sm-6">
          <label class="form-label"><i class="fa fa-user-tag me-1 text-primary"></i>Child Name <span class="text-danger">*</span></label>
          <input type="text" name="child_name" id="child_name" class="form-control"
                 placeholder="Enter child's full name" autocomplete="off">
          <div class="invalid-feedback" id="err_name"></div>
        </div>
        <div class="col-12 col-sm-6">
          <label class="form-label"><i class="fa fa-calendar me-1 text-primary"></i>Date of Birth <span class="text-danger">*</span></label>
          <input type="date" name="dob" id="dob" class="form-control">
          <div class="invalid-feedback" id="err_dob"></div>
        </div>
      </div>

      <div class="row g-3 mb-3">
        <div class="col-12 col-sm-6">
          <label class="form-label"><i class="fa fa-weight-scale me-1 text-primary"></i>Weight (kg) <span class="text-danger">*</span></label>
          <input type="number" step="0.1" name="weight" id="weight" class="form-control"
                 placeholder="Min: 1.0 kg — Max: 50.0 kg">
          <div class="invalid-feedback" id="err_weight"></div>
          <small class="text-muted" style="font-size:.75rem;">
            <i class="fa fa-circle-info me-1"></i>Valid range: 1.0 kg to 50.0 kg
          </small>
        </div>
        <div class="col-12 col-sm-6">
          <label class="form-label"><i class="fa fa-venus-mars me-1 text-primary"></i>Gender <span class="text-danger">*</span></label>
          <select name="gender" id="gender" class="form-select">
            <option value="">-- Select Gender --</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Other">Other</option>
          </select>
          <div class="invalid-feedback" id="err_gender"></div>
        </div>
      </div>

      <div class="mb-3">
        <label class="form-label"><i class="fa fa-droplet me-1 text-primary"></i>Blood Group <span class="text-danger">*</span></label>
        <select name="blood_group" id="blood_group" class="form-select">
          <option value="">-- Select Blood Group --</option>
          <option value="A+">A+</option>
          <option value="A-">A-</option>
          <option value="B+">B+</option>
          <option value="B-">B-</option>
          <option value="AB+">AB+</option>
          <option value="AB-">AB-</option>
          <option value="O+">O+</option>
          <option value="O-">O-</option>
          <option value="No Idea">No Idea</option>
        </select>
        <div class="invalid-feedback" id="err_blood"></div>
      </div>

      <div class="mb-4">
        <label class="form-label"><i class="fa fa-fingerprint me-1 text-primary"></i>Identification Mark <span class="text-danger">*</span></label>
        <input type="text" name="identification_mark" id="identification_mark" class="form-control"
               placeholder="e.g. Mole on left cheek">
        <div class="invalid-feedback" id="err_mark"></div>
      </div>

      <button type="submit" name="save" value="1" class="btn-save" id="saveBtn">
        <i class="fa fa-floppy-disk"></i> Save Child
      </button>
    </form>
  </div>

</main>

<script>
// ====== Sidebar toggle ======
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

// ====== Set max date for DOB = today ======
(function() {{
  const dobInput = document.getElementById('dob');
  const today = new Date().toISOString().split('T')[0];
  dobInput.setAttribute('max', today);
}})();

// ====== Helper: show/clear field error ======
function showErr(fieldId, errId, msg) {{
  const field = document.getElementById(fieldId);
  const err   = document.getElementById(errId);
  field.classList.add('is-invalid');
  err.innerHTML = '<i class="fa fa-triangle-exclamation"></i> ' + msg;
}}
function clearErr(fieldId, errId) {{
  const field = document.getElementById(fieldId);
  const err   = document.getElementById(errId);
  field.classList.remove('is-invalid');
  err.innerHTML = '';
}}

// ====== Real-time validation ======
document.getElementById('child_name').addEventListener('input', function() {{
  if (this.value.trim()) clearErr('child_name','err_name');
  else showErr('child_name','err_name','Child Name is required.');
}});

document.getElementById('dob').addEventListener('change', function() {{
  const val = this.value;
  if (!val) {{ showErr('dob','err_dob','Date of Birth is required.'); return; }}
  const dob   = new Date(val);
  const today = new Date();
  today.setHours(0,0,0,0);
  if (dob > today) {{
    showErr('dob','err_dob','Date of Birth cannot be a future date.');
    this.value = '';
    return;
  }}
  const ageMs    = today - dob;
  const ageYears = ageMs / (1000 * 60 * 60 * 24 * 365.25);
  if (ageYears > 18) {{
    showErr('dob','err_dob','Child must be under 18 years of age.');
    this.value = '';
    return;
  }}
  clearErr('dob','err_dob');
}});

document.getElementById('weight').addEventListener('input', function() {{
  const val = parseFloat(this.value);
  if (!this.value) {{
    showErr('weight','err_weight','Weight is required.'); return;
  }}
  if (isNaN(val) || val < 1.0) {{
    showErr('weight','err_weight','Weight must be at least 1.0 kg. A child cannot weigh less than 1 kg.');
    return;
  }}
  if (val > 50.0) {{
    showErr('weight','err_weight','Weight cannot exceed 50 kg for a child.');
    return;
  }}
  clearErr('weight','err_weight');
}});

document.getElementById('gender').addEventListener('change', function() {{
  if (!this.value) showErr('gender','err_gender','Please select a gender.');
  else clearErr('gender','err_gender');
}});

document.getElementById('blood_group').addEventListener('change', function() {{
  if (!this.value) showErr('blood_group','err_blood','Please select a blood group.');
  else clearErr('blood_group','err_blood');
}});

document.getElementById('identification_mark').addEventListener('input', function() {{
  if (this.value.trim()) clearErr('identification_mark','err_mark');
  else showErr('identification_mark','err_mark','Identification Mark is required.');
}});

// ====== Full form validation on submit ======
document.getElementById('childForm').addEventListener('submit', function(e) {{
  let valid = true;

  // Child Name
  const name = document.getElementById('child_name').value.trim();
  if (!name) {{ showErr('child_name','err_name','Child Name is required.'); valid = false; }}
  else clearErr('child_name','err_name');

  // DOB
  const dobVal = document.getElementById('dob').value;
  if (!dobVal) {{
    showErr('dob','err_dob','Date of Birth is required.'); valid = false;
  }} else {{
    const dob   = new Date(dobVal);
    const today = new Date(); today.setHours(0,0,0,0);
    if (dob > today) {{
      showErr('dob','err_dob','Date of Birth cannot be a future date.'); valid = false;
    }} else {{
      const ageYears = (today - dob) / (1000 * 60 * 60 * 24 * 365.25);
      if (ageYears > 18) {{
        showErr('dob','err_dob','Child must be under 18 years of age.'); valid = false;
      }} else clearErr('dob','err_dob');
    }}
  }}

  // Weight
  const wVal = document.getElementById('weight').value;
  const w    = parseFloat(wVal);
  if (!wVal) {{
    showErr('weight','err_weight','Weight is required.'); valid = false;
  }} else if (isNaN(w) || w < 1.0) {{
    showErr('weight','err_weight','Weight must be at least 1.0 kg.'); valid = false;
  }} else if (w > 50.0) {{
    showErr('weight','err_weight','Weight cannot exceed 50 kg.'); valid = false;
  }} else clearErr('weight','err_weight');

  // Gender
  const gender = document.getElementById('gender').value;
  if (!gender) {{ showErr('gender','err_gender','Please select a gender.'); valid = false; }}
  else clearErr('gender','err_gender');

  // Blood Group
  const bg = document.getElementById('blood_group').value;
  if (!bg) {{ showErr('blood_group','err_blood','Please select a blood group.'); valid = false; }}
  else clearErr('blood_group','err_blood');

  // Identification Mark
  const mark = document.getElementById('identification_mark').value.trim();
  if (!mark) {{ showErr('identification_mark','err_mark','Identification Mark is required.'); valid = false; }}
  else clearErr('identification_mark','err_mark');

  if (!valid) {{
    e.preventDefault();
    // Scroll to first error
    const firstErr = document.querySelector('.is-invalid');
    if (firstErr) firstErr.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
  }}
}});
</script>
</body>
</html>
""")

con.close()