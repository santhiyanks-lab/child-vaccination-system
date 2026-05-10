#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
print("Content-Type:text/html\r\n\r\n")

import pymysql, cgi, cgitb, os, sys, smtplib
from email.mime.text import MIMEText

sys.stdout.reconfigure(encoding='utf-8')
cgitb.enable()

# ================= DATABASE =================
con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()

form = cgi.FieldStorage()
pid = form.getvalue("parent_id")

if not pid:
    print("<script>alert('Invalid Access');location.href='parent_dash.py';</script>")
    exit()

# ================= UPDATE ADDRESS =================
if form.getvalue("update_address"):
    addr    = form.getvalue("addressn")
    pid_tmp = form.getvalue("hid")
    cur.execute("UPDATE parent SET address=%s WHERE parent_id=%s", (addr, pid_tmp))
    con.commit()
    print(f"<script>alert('Address Updated');location.href='parent_profile.py?parent_id={pid_tmp}';</script>")
    exit()

# ================= UPDATE PASSWORD =================
if form.getvalue("update_pass"):
    newp    = form.getvalue("newpass")
    pid_tmp = form.getvalue("hidp")
    cur.execute("UPDATE parent SET password=%s WHERE parent_id=%s", (newp, pid_tmp))
    con.commit()
    cur.execute("SELECT father_name, email FROM parent WHERE parent_id=%s", (pid_tmp,))
    data = cur.fetchone()
    if data:
        father_name, email = data
        sender_email    = "santhiyanks@gmail.com"
        sender_password = "mwfh csxz smxf xqhp"
        message = f"Dear {father_name},\n\nYour password has been changed.\n\nNew Password: {newp}\n\nIf you did not do this, contact admin immediately.\n\nThank You."
        msg = MIMEText(message)
        msg['Subject'] = "Parent Password Changed"
        msg['From']    = sender_email
        msg['To']      = email
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
            server.quit()
        except:
            pass
    print(f"<script>alert('Password Updated. Email Sent.');location.href='parent_profile.py?parent_id={pid_tmp}';</script>")
    exit()

# ================= UPDATE IMAGE =================
if form.getvalue("update_img"):
    img     = form['photo']
    fname   = os.path.basename(img.filename)
    pid_tmp = form.getvalue("hidimg")
    open("images/" + fname, "wb").write(img.file.read())
    cur.execute("UPDATE parent SET parent_profile=%s WHERE parent_id=%s", (fname, pid_tmp))
    con.commit()
    print(f"<script>alert('Profile Image Updated');location.href='parent_profile.py?parent_id={pid_tmp}';</script>")
    exit()

# ================= FETCH PARENT DATA =================
cur.execute("SELECT * FROM parent WHERE parent_id=%s", (pid,))
rows = cur.fetchall()

# ================= HTML =================
print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Parent Profile</title>
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

  /* ===== PROFILE HERO ===== */
  .profile-hero {{
    background: linear-gradient(135deg, #1b5e20, #2e7d32);
    border-radius: 16px 16px 0 0;
    padding: 32px 24px 20px;
    display: flex; align-items: center; gap: 20px;
    flex-wrap: wrap; position: relative; overflow: hidden;
  }}
  .profile-hero::before {{
    content: ''; position: absolute; top: -30px; right: -30px;
    width: 150px; height: 150px;
    background: rgba(255,255,255,.06); border-radius: 50%;
  }}
  .avatar-wrap {{ position: relative; flex-shrink: 0; }}
  .avatar-wrap img {{
    width: 100px; height: 100px; border-radius: 50%;
    border: 3px solid rgba(255,255,255,.5); object-fit: cover;
  }}
  .avatar-btn {{
    position: absolute; bottom: 2px; right: 2px;
    width: 30px; height: 30px; border-radius: 50%;
    background: #1565c0; border: 2px solid #fff;
    color: #fff; font-size: .75rem;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; transition: background .2s;
  }}
  .avatar-btn:hover {{ background: #0d47a1; }}
  .hero-info h5 {{ color: #fff; font-size: 1.15rem; font-weight: 700; margin: 0 0 4px; }}
  .hero-info .badge-parent {{
    background: rgba(255,255,255,.2); color: #fff;
    padding: 3px 12px; border-radius: 20px; font-size: .78rem; font-weight: 600;
  }}
  .hero-info p {{ color: rgba(255,255,255,.75); font-size: .83rem; margin: 6px 0 0; }}

  /* ===== DETAIL ROWS ===== */
  .profile-body {{
    background: #fff;
    border-radius: 0 0 16px 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,.1);
    overflow: hidden;
    margin-bottom: 24px;
  }}
  .detail-row {{
    display: flex; align-items: center;
    padding: 16px 20px; border-bottom: 1px solid #f1f5f9;
    gap: 14px; flex-wrap: wrap;
  }}
  .detail-row:last-child {{ border: none; }}
  .detail-icon {{
    width: 38px; height: 38px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: .9rem; flex-shrink: 0;
  }}
  .detail-content {{ flex: 1; min-width: 0; }}
  .detail-label {{ font-size: .72rem; color: #94a3b8; font-weight: 700; letter-spacing: .8px; text-transform: uppercase; margin-bottom: 2px; }}
  .detail-value {{ font-size: .92rem; color: #1e293b; font-weight: 500; word-break: break-word; }}
  .detail-actions {{ display: flex; gap: 6px; flex-shrink: 0; flex-wrap: wrap; }}
  .btn-edit {{
    background: #e3f2fd; color: #1565c0; border: none;
    border-radius: 8px; padding: 5px 14px; font-size: .8rem;
    font-weight: 600; cursor: pointer; transition: all .2s; white-space: nowrap;
  }}
  .btn-edit:hover {{ background: #1565c0; color: #fff; }}

  /* ===== MODALS ===== */
  .modal-content {{
    border: none; border-radius: 14px;
    background: #1a1a40; color: #fff;
    box-shadow: 0 8px 32px rgba(0,0,0,.3);
    animation: zoomIn .25s ease;
  }}
  @keyframes zoomIn {{
    from {{ transform: scale(.92); opacity: 0; }}
    to   {{ transform: scale(1);   opacity: 1; }}
  }}
  .modal-header {{
    border-bottom: 1px solid rgba(255,255,255,.1); padding: 16px 20px;
  }}
  .modal-header h5 {{ font-size: .95rem; font-weight: 700; margin: 0; }}
  .modal-footer {{ border-top: 1px solid rgba(255,255,255,.1); padding: 12px 20px; }}
  .modal .form-control {{
    background: rgba(255,255,255,.08);
    border: 1.5px solid rgba(255,255,255,.15);
    color: #fff; border-radius: 8px; font-size: .9rem;
  }}
  .modal .form-control:focus {{
    background: rgba(255,255,255,.12);
    border-color: #42a5f5; box-shadow: none; color: #fff;
  }}
  .modal .form-control::placeholder {{ color: rgba(255,255,255,.4); }}
  .modal .form-label {{ font-size: .85rem; color: rgba(255,255,255,.7); font-weight: 600; }}

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
    .profile-hero {{ padding: 24px 16px 16px; gap: 14px; }}
    .avatar-wrap img {{ width: 80px; height: 80px; }}
    .detail-row {{ padding: 12px 14px; }}
    .detail-actions {{ width: 100%; }}
    .btn-edit {{ flex: 1; text-align: center; justify-content: center; }}
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
  <a href="parent_dash.py?parent_id={pid}" class="nav-link">
    <i class="fa fa-gauge"></i> Dashboard
  </a>
  <a href="parent_profile.py?parent_id={pid}" class="nav-link active">
    <i class="fa fa-user"></i> My Profile
  </a>

  <hr class="sidebar-divider">
  <details class="sidebar-group">
    <summary>
      <i class="fa-solid fa-child"></i> Child
      <i class="fa fa-chevron-right caret"></i>
    </summary>
    <div class="sub-links">
      <a href="parentaddchild.py?parent_id={pid}"><i class="fa fa-plus"></i> Add Child</a>
      <a href="parentviewchild.py?parent_id={pid}"><i class="fa fa-eye"></i> View Child</a>
    </div>
  </details>

  <hr class="sidebar-divider">
  <details class="sidebar-group">
    <summary>
      <i class="fa-solid fa-calendar-check"></i> Appointments
      <i class="fa fa-chevron-right caret"></i>
    </summary>
    <div class="sub-links">
      <a href="parentaddappointments.py?parent_id={pid}"><i class="fa fa-plus"></i> Add Appointment</a>
      <a href="parentpendingappointments.py?parent_id={pid}"><i class="fa fa-clock"></i> Pending</a>
      <a href="parentcompletedappointments.py?parent_id={pid}"><i class="fa fa-circle-check"></i> Completed</a>
    </div>
  </details>

  <hr class="sidebar-divider">
  <a href="parentnotify.py?parent_id={pid}" class="nav-link">
    <i class="fa-solid fa-bell"></i> Notifications
  </a>

  <hr class="sidebar-divider">
  <a href="parentfeedback.py?parent_id={pid}" class="nav-link">
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
    <div class="page-header-icon"><i class="fa fa-user"></i></div>
    <div>
      <h4>My Profile</h4>
      <p>View and manage your personal information</p>
    </div>
  </div>
""")

# ================= PROFILE CARD =================
for j in rows:
    father_name  = j[1]  if j[1]  else "-"
    mother_name  = j[2]  if j[2]  else "-"
    email        = j[6]  if j[6]  else "-"
    phone        = j[7]  if j[7]  else "-"
    state        = j[9]  if j[9]  else "-"
    district     = j[10] if j[10] else "-"
    address      = j[11] if j[11] else "-"
    profile_img  = j[14] if j[14] else "default.jpg"

    print(f"""
  <div style="max-width:780px;">

    <!-- Hero -->
    <div class="profile-hero">
      <div class="avatar-wrap">
        <img src="./images/{profile_img}" alt="Profile"
             onerror="this.src='./images/default.jpg'">
        <button class="avatar-btn"
                data-bs-toggle="modal"
                data-bs-target="#imageModal{pid}"
                title="Change Photo">
          <i class="fa fa-camera"></i>
        </button>
      </div>
      <div class="hero-info">
        <h5>{father_name}</h5>
        <span class="badge-parent">Parent Account</span>
        <p><i class="fa fa-envelope me-1"></i>{email}</p>
        <p><i class="fa fa-phone me-1"></i>{phone}</p>
      </div>
    </div>

    <!-- Detail Rows -->
    <div class="profile-body">

      <div class="detail-row">
        <div class="detail-icon" style="background:#e3f2fd;">
          <i class="fa fa-user" style="color:#1565c0;"></i>
        </div>
        <div class="detail-content">
          <div class="detail-label">Father's Name</div>
          <div class="detail-value">{father_name}</div>
        </div>
      </div>

      <div class="detail-row">
        <div class="detail-icon" style="background:#fce4ec;">
          <i class="fa fa-user" style="color:#c62828;"></i>
        </div>
        <div class="detail-content">
          <div class="detail-label">Mother's Name</div>
          <div class="detail-value">{mother_name}</div>
        </div>
      </div>

      <div class="detail-row">
        <div class="detail-icon" style="background:#e8f5e9;">
          <i class="fa fa-envelope" style="color:#2e7d32;"></i>
        </div>
        <div class="detail-content">
          <div class="detail-label">Email Address</div>
          <div class="detail-value">{email}</div>
        </div>
      </div>

      <div class="detail-row">
        <div class="detail-icon" style="background:#fff3e0;">
          <i class="fa fa-phone" style="color:#e65100;"></i>
        </div>
        <div class="detail-content">
          <div class="detail-label">Phone Number</div>
          <div class="detail-value">{phone}</div>
        </div>
      </div>

      <div class="detail-row">
        <div class="detail-icon" style="background:#f3e5f5;">
          <i class="fa fa-map" style="color:#6a1b9a;"></i>
        </div>
        <div class="detail-content">
          <div class="detail-label">State / District</div>
          <div class="detail-value">{state} &nbsp;/&nbsp; {district}</div>
        </div>
      </div>

      <div class="detail-row">
        <div class="detail-icon" style="background:#e8eaf6;">
          <i class="fa fa-location-dot" style="color:#283593;"></i>
        </div>
        <div class="detail-content">
          <div class="detail-label">Address</div>
          <div class="detail-value">{address}</div>
        </div>
        <div class="detail-actions">
          <button class="btn-edit"
                  data-bs-toggle="modal"
                  data-bs-target="#addressModal{pid}">
            <i class="fa fa-pen me-1"></i>Edit
          </button>
        </div>
      </div>

      <div class="detail-row">
        <div class="detail-icon" style="background:#fff8e1;">
          <i class="fa fa-lock" style="color:#f57f17;"></i>
        </div>
        <div class="detail-content">
          <div class="detail-label">Password</div>
          <div class="detail-value">&#9679;&#9679;&#9679;&#9679;&#9679;&#9679;&#9679;&#9679;</div>
        </div>
        <div class="detail-actions">
          <button class="btn-edit"
                  data-bs-toggle="modal"
                  data-bs-target="#passModal{pid}">
            <i class="fa fa-key me-1"></i>Change
          </button>
        </div>
      </div>

      <div class="detail-row">
        <div class="detail-icon" style="background:#e8f5e9;">
          <i class="fa fa-image" style="color:#2e7d32;"></i>
        </div>
        <div class="detail-content">
          <div class="detail-label">Profile Photo</div>
          <div class="detail-value">Click to update your profile picture</div>
        </div>
        <div class="detail-actions">
          <button class="btn-edit"
                  data-bs-toggle="modal"
                  data-bs-target="#imageModal{pid}">
            <i class="fa fa-camera me-1"></i>Change
          </button>
        </div>
      </div>

    </div>
  </div>
""")

# ================= MODALS =================
print(f"""
<!-- Address Modal -->
<div class="modal fade" id="addressModal{pid}" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header">
        <h5><i class="fa fa-location-dot me-2"></i>Update Address</h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <form method="post">
        <div class="modal-body">
          <label class="form-label">New Address</label>
          <textarea name="addressn" class="form-control" rows="3"
                    placeholder="Enter new address..." required></textarea>
          <input type="hidden" name="hid" value="{pid}">
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <button type="submit" name="update_address" class="btn btn-primary">
            <i class="fa fa-save me-1"></i> Save Address
          </button>
        </div>
      </form>
    </div>
  </div>
</div>

<!-- Password Modal -->
<div class="modal fade" id="passModal{pid}" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header">
        <h5><i class="fa fa-key me-2"></i>Change Password</h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <form method="post" enctype="multipart/form-data">
        <div class="modal-body">
          <label class="form-label">New Password</label>
          <input type="password" name="newpass" class="form-control"
                 placeholder="Enter new password..." required>
          <input type="hidden" name="hidp" value="{pid}">
          <div class="alert mt-3 mb-0"
               style="background:rgba(255,193,7,.12);border:1px solid rgba(255,193,7,.3);
                      border-radius:8px;padding:10px 14px;font-size:.83rem;color:#ffd54f;">
            <i class="fa fa-envelope me-1"></i> A notification email will be sent to your registered address.
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <button type="submit" name="update_pass" class="btn btn-warning text-dark fw-bold">
            <i class="fa fa-key me-1"></i> Update Password
          </button>
        </div>
      </form>
    </div>
  </div>
</div>

<!-- Image Modal -->
<div class="modal fade" id="imageModal{pid}" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header">
        <h5><i class="fa fa-camera me-2"></i>Change Profile Photo</h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <form method="post" enctype="multipart/form-data">
        <div class="modal-body">
          <label class="form-label">Select New Photo</label>
          <input type="file" name="photo" class="form-control"
                 accept="image/*" required>
          <input type="hidden" name="hidimg" value="{pid}">
          <p style="font-size:.8rem;color:rgba(255,255,255,.5);margin-top:8px;">
            Accepted formats: JPG, PNG, GIF
          </p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <button type="submit" name="update_img" class="btn btn-info text-white fw-bold">
            <i class="fa fa-upload me-1"></i> Upload Photo
          </button>
        </div>
      </form>
    </div>
  </div>
</div>
""")

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