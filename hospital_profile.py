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
hid = form.getvalue("hospital_id")

if not hid:
    print("""<script>alert("Invalid Access");location.href="hospital_login.py";</script>""")
    exit()

hid = int(hid)  # cast to int

# ================= UPDATE ADDRESS =================
if form.getvalue("update_address"):
    addr = form.getvalue("addressn")
    hid_addr = form.getvalue("hid")
    cur.execute("UPDATE hospital SET address=%s WHERE hospital_id=%s", (addr, hid_addr))
    con.commit()
    print(f"<script>alert('Address Updated');location.href='hospital_profile.py?hospital_id={hid_addr}';</script>")
    exit()

# ================= UPDATE PASSWORD =================
if form.getvalue("update_pass"):
    newp = form.getvalue("newpass")
    hid_pass = form.getvalue("hidp")
    cur.execute("UPDATE hospital SET password=%s WHERE hospital_id=%s", (newp, hid_pass))
    con.commit()
    cur.execute("SELECT hospital_name, owner_email FROM hospital WHERE hospital_id=%s", (hid_pass,))
    data = cur.fetchone()
    if data:
        hospital_name, email = data
        sender_email    = "santhiyanks@gmail.com"
        sender_password = "mwfh csxz smxf xqhp"
        message = f"""
Dear {hospital_name},

Your hospital account password has been successfully changed.

New Password: {newp}

If you did not make this change, please contact admin immediately.

Thank You.
"""
        msg = MIMEText(message)
        msg['Subject'] = "Hospital Password Changed"
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
    print(f"<script>alert('Password Updated Successfully. Email Sent.');location.href='hospital_profile.py?hospital_id={hid_pass}';</script>")
    exit()

# ================= UPDATE IMAGE =================
if form.getvalue("update_img"):
    img   = form['photo']
    fname = os.path.basename(img.filename)
    open("images/" + fname, "wb").write(img.file.read())
    hid_img = form.getvalue("hidimg")
    cur.execute("UPDATE hospital SET owner_profile=%s WHERE hospital_id=%s", (fname, hid_img))
    con.commit()
    print(f"<script>alert('Profile Image Updated');location.href='hospital_profile.py?hospital_id={hid_img}';</script>")
    exit()

# ================= FETCH HOSPITAL DATA =================
cur.execute("SELECT * FROM hospital WHERE hospital_id=%s", (hid,))
rows = cur.fetchall()
hospital_name = rows[0][1] if rows else "Hospital"

# ================= VACCINE STATS =================
cur.execute("SELECT COUNT(*) FROM child_vaccine WHERE hospital_id=%s AND status='pending'", (hid,))
pending = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM child_vaccine WHERE hospital_id=%s AND status='confirmed'", (hid,))
confirmed = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM child_vaccine WHERE hospital_id=%s AND status='completed'", (hid,))
completed = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM child_vaccine WHERE hospital_id=%s AND status='rescheduled'", (hid,))
rescheduled = cur.fetchone()[0]

# ================= HOSPITAL FEEDBACK STATS =================
cur.execute("SELECT COUNT(*) FROM hospitalfeedback WHERE hospital_id=%s", (hid,))
total_hfb = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM hospitalfeedback WHERE hospital_id=%s AND resolved=0", (hid,))
unresolved = cur.fetchone()[0]

# ================= PARENT FEEDBACK STATS =================
cur.execute("SELECT COUNT(*) FROM feedback WHERE hospital_id=%s", (hid,))
parent_fb_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM feedback WHERE hospital_id=%s AND rating < 2", (hid,))
parent_fb_low = cur.fetchone()[0]

cur.execute("SELECT ROUND(AVG(rating),1) FROM feedback WHERE hospital_id=%s", (hid,))
row2 = cur.fetchone()
parent_fb_avg = float(row2[0]) if row2 and row2[0] else 0.0

cur.execute("SELECT COUNT(*) FROM feedback WHERE hospital_id=%s AND rating >= 4", (hid,))
parent_fb_high = cur.fetchone()[0]

# ================= RECENT PARENT FEEDBACK (last 5) =================
cur.execute("""
    SELECT f.feedback_id, f.rating, f.comment, f.submitted_at,
           p.father_name, c.child_name, v.vaccine_name
    FROM feedback f
    JOIN parent   p ON f.parent_id  = p.parent_id
    JOIN children c ON f.child_id   = c.child_id
    JOIN vaccine  v ON f.vaccine_id = v.vaccine_id
    WHERE f.hospital_id = %s
    ORDER BY f.submitted_at DESC
    LIMIT 5
""", (hid,))
recent_parent_fb = cur.fetchall()

# ================= HTML =================
print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hospital Profile</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
  :root {{
    --sidebar-w: 260px;
    --topbar-h: 60px;
    --primary: #1565c0;
    --primary-dark: #0d47a1;
    --bg: #f0f4f8;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: var(--bg); color: #1e293b; }}

  /* TOPBAR */
  .topbar {{
    position: fixed; top: 0; left: 0; right: 0;
    height: var(--topbar-h); background: #0d1b2a;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 16px; z-index: 1100; box-shadow: 0 2px 10px rgba(0,0,0,.3);
  }}
  .topbar-left {{ display: flex; align-items: center; gap: 12px; }}
  .topbar img {{ height:40px; width:40px; border-radius:50%; border:2px solid rgba(255,255,255,.4); object-fit:cover; }}
  .topbar .brand {{ color:#fff; font-size:1rem; font-weight:700; }}
  .topbar .subbrand {{ color:#90a4ae; font-size:.75rem; display:block; }}
  .hamburger {{ background:none; border:none; color:#fff; font-size:1.4rem; cursor:pointer; padding:4px 8px; border-radius:6px; display:none; transition:background .2s; }}
  .hamburger:hover {{ background:rgba(255,255,255,.1); }}
  .topbar-right a {{ color:#cfd8dc; text-decoration:none; font-size:.85rem; padding:6px 14px; border:1px solid #37474f; border-radius:6px; transition:all .2s; }}
  .topbar-right a:hover {{ background:#e53935; border-color:#e53935; color:#fff; }}

  /* SIDEBAR */
  .sidebar {{
    position: fixed; top: var(--topbar-h); left: 0;
    width: var(--sidebar-w); height: calc(100vh - var(--topbar-h));
    background: #0d1b2a; overflow-y: auto; z-index: 1000;
    transition: transform .3s ease; padding: 16px 12px 24px;
    scrollbar-width: thin; scrollbar-color: #1e3a5f transparent;
  }}
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
  .sub-links a i {{ width:14px; font-size:.8rem; }}
  .sidebar-divider {{ border:none; border-top:1px solid #1c2d3e; margin:10px 0; }}
  .sidebar-overlay {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,.55); z-index:999; backdrop-filter:blur(2px); }}

  /* MAIN */
  .main {{ margin-left:var(--sidebar-w); margin-top:var(--topbar-h); padding:28px 24px; min-height:calc(100vh - var(--topbar-h)); transition:margin-left .3s; }}

  /* PAGE HEADER */
  .page-header {{ display:flex; align-items:center; gap:14px; margin-bottom:24px; }}
  .page-header-icon {{ background:linear-gradient(135deg,var(--primary),#42a5f5); color:#fff; width:48px; height:48px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:1.2rem; flex-shrink:0; box-shadow:0 4px 12px rgba(21,101,192,.3); }}
  .page-header h4 {{ font-size:1.25rem; font-weight:700; margin:0 0 2px; }}
  .page-header p {{ font-size:.85rem; color:#64748b; margin:0; }}

  /* PROFILE CARD */
  .profile-wrap {{ max-width:860px; margin:0 auto; }}
  .profile-hero {{ background:linear-gradient(135deg,#0d47a1,#1976d2); border-radius:16px 16px 0 0; padding:32px 24px; text-align:center; color:#fff; position:relative; }}
  .profile-hero .avatar-wrap {{ position:relative; display:inline-block; }}
  .profile-hero img {{ width:110px; height:110px; border-radius:50%; border:4px solid rgba(255,255,255,.8); object-fit:cover; box-shadow:0 4px 16px rgba(0,0,0,.25); }}
  .profile-hero .change-img-btn {{ position:absolute; bottom:4px; right:4px; background:#fff; color:var(--primary); border:none; border-radius:50%; width:28px; height:28px; font-size:.75rem; display:flex; align-items:center; justify-content:center; cursor:pointer; box-shadow:0 2px 6px rgba(0,0,0,.2); transition:all .2s; }}
  .profile-hero .change-img-btn:hover {{ background:var(--primary); color:#fff; }}
  .profile-hero h4 {{ margin:12px 0 4px; font-size:1.2rem; font-weight:700; }}
  .profile-hero .badge {{ font-size:.8rem; padding:5px 14px; border-radius:20px; }}
  .profile-body {{ background:#fff; border-radius:0 0 16px 16px; box-shadow:0 4px 20px rgba(0,0,0,.08); overflow:hidden; }}
  .detail-row {{ display:flex; align-items:center; padding:14px 24px; border-bottom:1px solid #f1f5f9; gap:12px; flex-wrap:wrap; }}
  .detail-row:last-child {{ border-bottom:none; }}
  .detail-icon {{ width:36px; height:36px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:.9rem; flex-shrink:0; }}
  .detail-content {{ flex:1; min-width:0; }}
  .detail-label {{ font-size:.72rem; color:#94a3b8; font-weight:700; text-transform:uppercase; letter-spacing:.8px; margin-bottom:2px; }}
  .detail-value {{ font-size:.92rem; color:#1e293b; font-weight:500; word-break:break-word; }}
  .detail-action {{ flex-shrink:0; }}
  .btn-edit {{ background:#f1f5f9; border:none; color:#475569; border-radius:8px; padding:6px 14px; font-size:.8rem; font-weight:600; cursor:pointer; transition:all .2s; display:flex; align-items:center; gap:5px; text-decoration:none; }}
  .btn-edit:hover {{ background:var(--primary); color:#fff; }}

  /* FEEDBACK WIDGET — identical to dashboard */
  .fb-widget {{ background:#fff; border-radius:14px; box-shadow:0 2px 12px rgba(0,0,0,.08); border:1px solid #e2e8f0; overflow:hidden; }}
  .fb-widget-hdr {{ display:flex; align-items:center; justify-content:space-between; padding:16px 20px; border-bottom:1px solid #f1f5f9; flex-wrap:wrap; gap:8px; }}
  .fb-widget-hdr h6 {{ font-size:.95rem; font-weight:700; margin:0; display:flex; align-items:center; gap:8px; }}
  .fb-mini-badges {{ display:flex; gap:8px; flex-wrap:wrap; }}
  .fb-mini-badge {{ display:inline-flex; align-items:center; gap:5px; padding:4px 11px; border-radius:20px; font-size:.75rem; font-weight:700; }}
  .fb-low-alert {{ display:flex; align-items:center; gap:10px; background:#fff5f5; border-bottom:1px solid #fed7d7; padding:9px 20px; font-size:.83rem; color:#c53030; }}
  .fb-low-alert a {{ color:#c53030; font-weight:700; text-decoration:underline; margin-left:auto; }}
  .fb-row {{ display:flex; align-items:center; gap:12px; padding:11px 20px; border-bottom:1px solid #f8fafc; transition:background .15s; }}
  .fb-row:last-child {{ border-bottom:none; }}
  .fb-row:hover {{ background:#f8fafc; }}
  .fb-row.fb-row-low {{ background:#fff5f5; border-left:3px solid #e53935; }}
  .fb-avatar {{ width:38px; height:38px; border-radius:50%; background:linear-gradient(135deg,#1565c0,#0d47a1); color:#fff; font-weight:800; font-size:.9rem; display:flex; align-items:center; justify-content:center; flex-shrink:0; }}
  .fb-avatar.low {{ background:linear-gradient(135deg,#e53935,#c62828); }}
  .fb-info {{ flex:1; min-width:0; }}
  .fb-parent-name {{ font-size:.87rem; font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .fb-sub {{ font-size:.73rem; color:#64748b; margin-top:1px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .fb-comment {{ font-size:.75rem; color:#4b5563; font-style:italic; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .fb-right {{ text-align:right; flex-shrink:0; }}
  .fb-stars {{ font-size:.85rem; line-height:1; }}
  .fb-date {{ font-size:.7rem; color:#94a3b8; margin-top:3px; }}
  .fb-widget-footer {{ padding:12px 20px; background:#f8fafc; border-top:1px solid #f1f5f9; text-align:center; }}
  .fb-widget-footer a {{ font-size:.84rem; font-weight:700; color:var(--primary); text-decoration:none; display:inline-flex; align-items:center; gap:6px; }}
  .fb-widget-footer a:hover {{ color:var(--primary-dark); text-decoration:underline; }}
  .fb-empty {{ text-align:center; padding:32px 20px; color:#94a3b8; font-size:.86rem; }}
  .fb-empty i {{ display:block; font-size:2rem; opacity:.25; margin-bottom:8px; }}

  /* STAT MINI CARDS */
  .mini-stat-row {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(140px,1fr)); gap:12px; margin-bottom:20px; max-width:860px; margin-left:auto; margin-right:auto; }}
  .mini-stat {{ background:#fff; border-radius:12px; box-shadow:0 2px 10px rgba(0,0,0,.07); padding:14px 16px; display:flex; align-items:center; gap:12px; text-decoration:none; color:inherit; transition:transform .2s,box-shadow .2s; }}
  .mini-stat:hover {{ transform:translateY(-2px); box-shadow:0 6px 18px rgba(0,0,0,.11); color:inherit; }}
  .mini-stat-icon {{ width:38px; height:38px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:1rem; flex-shrink:0; }}
  .mini-stat-val {{ font-size:1.3rem; font-weight:800; line-height:1; }}
  .mini-stat-lbl {{ font-size:.72rem; color:#64748b; margin-top:2px; }}

  /* MODALS */
  .modal-content {{ border:none; border-radius:14px; background:#1a1a40; color:#fff; box-shadow:0 8px 32px rgba(0,0,0,.4); }}
  .modal-header {{ border-bottom:1px solid rgba(255,255,255,.12); padding:16px 20px 12px; }}
  .modal-footer {{ border-top:1px solid rgba(255,255,255,.12); }}
  .modal-title {{ font-size:1rem; font-weight:700; }}
  .modal .form-control {{ background:rgba(255,255,255,.08); border:1.5px solid rgba(255,255,255,.15); color:#fff; border-radius:8px; }}
  .modal .form-control:focus {{ border-color:#42a5f5; box-shadow:0 0 0 3px rgba(66,165,245,.15); background:rgba(255,255,255,.1); color:#fff; }}
  .modal .form-control::placeholder {{ color:#78909c; }}
  .modal .form-label {{ font-size:.85rem; color:#b0bec5; font-weight:600; }}

  @media (max-width:991px) {{
    .sidebar {{ transform:translateX(-100%); }}
    .sidebar.open {{ transform:translateX(0); }}
    .sidebar-overlay.open {{ display:block; }}
    .main {{ margin-left:0; }}
    .hamburger {{ display:block; }}
  }}
  @media (max-width:576px) {{
    .main {{ padding:16px 12px; }}
    .profile-hero {{ padding:24px 16px; }}
    .profile-hero img {{ width:90px; height:90px; }}
    .detail-row {{ padding:12px 16px; }}
  }}
</style>
</head>
<body>

<!-- TOPBAR -->
<div class="topbar">
  <div class="topbar-left">
    <button class="hamburger" onclick="toggleSidebar()"><i class="fa fa-bars"></i></button>
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

<!-- SIDEBAR -->
<nav class="sidebar" id="sidebar">
  <div class="sidebar-label">Menu</div>
  <a href="hospital_dash.py?hospital_id={hid}" class="nav-link">
    <i class="fa fa-gauge"></i> Dashboard
  </a>
  <a href="hospital_profile.py?hospital_id={hid}" class="nav-link active">
    <i class="fa fa-hospital"></i> My Profile
  </a>

  <hr class="sidebar-divider">
  <div class="sidebar-label">Vaccinations</div>
  <details class="sidebar-group">
    <summary>
      <i class="fa-solid fa-syringe"></i> Vaccine Details
      <i class="fa fa-chevron-right caret"></i>
    </summary>
    <div class="sub-links">
      <a href="hospitalpendingvaccine.py?hospital_id={hid}">
        <i class="fa-solid fa-clock"></i> Pending
        {'<span style="margin-left:auto;background:#f97316;color:#fff;font-size:.65rem;font-weight:700;min-width:17px;height:17px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;padding:0 4px;">' + str(pending) + '</span>' if pending > 0 else ''}
      </a>
      <a href="hospitalconfirmedvaccine.py?hospital_id={hid}">
        <i class="fa-solid fa-check"></i> Confirmed
        {'<span style="margin-left:auto;background:#1565c0;color:#fff;font-size:.65rem;font-weight:700;min-width:17px;height:17px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;padding:0 4px;">' + str(confirmed) + '</span>' if confirmed > 0 else ''}
      </a>
      <a href="hospitalrescheduledvaccine.py?hospital_id={hid}">
        <i class="fa-solid fa-calendar-days"></i> Rescheduled
        {'<span style="margin-left:auto;background:#7c3aed;color:#fff;font-size:.65rem;font-weight:700;min-width:17px;height:17px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;padding:0 4px;">' + str(rescheduled) + '</span>' if rescheduled > 0 else ''}
      </a>
      <a href="hospitalcompletedvaccine.py?hospital_id={hid}">
        <i class="fa-solid fa-circle-check"></i> Completed
        {'<span style="margin-left:auto;background:#2e7d32;color:#fff;font-size:.65rem;font-weight:700;min-width:17px;height:17px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;padding:0 4px;">' + str(completed) + '</span>' if completed > 0 else ''}
      </a>
    </div>
  </details>

  <hr class="sidebar-divider">
  <div class="sidebar-label">Feedback</div>
  <details class="sidebar-group" {'open' if parent_fb_count > 0 else ''}>
    <summary>
      <i class="fa-solid fa-star"></i> Feedback
      {'<span class="badge bg-danger ms-auto" style="font-size:.7rem;">' + str(unresolved + parent_fb_low) + '</span>' if (unresolved + parent_fb_low) > 0 else ''}
      <i class="fa fa-chevron-right caret"></i>
    </summary>
    <div class="sub-links">
      <a href="hospitalparentfeedback.py?hospital_id={hid}">
        <i class="fa-solid fa-comments"></i> Parent Feedback
        {'<span style="margin-left:auto;background:#e53935;color:#fff;font-size:.65rem;font-weight:700;min-width:17px;height:17px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;padding:0 4px;">' + str(parent_fb_low) + '</span>' if parent_fb_low > 0 else ''}
      </a>
    </div>
  </details>

  <hr class="sidebar-divider">
  <a href="home.py" class="nav-link" style="color:#ef9a9a;">
    <i class="fa fa-right-from-bracket"></i> Logout
  </a>
</nav>

<!-- MAIN -->
<main class="main">

  <div class="page-header">
    <div class="page-header-icon"><i class="fa fa-hospital"></i></div>
    <div>
      <h4>Hospital Profile</h4>
      <p>View and manage your hospital account details</p>
    </div>
  </div>
""")

# ================= PROFILE CARD =================
for j in rows:
    print(f"""
  <div class="profile-wrap">
    <div class="profile-hero">
      <div class="avatar-wrap">
        <img src="./images/{j[11]}" alt="Profile Photo" onerror="this.src='./images/default.png'">
        <button class="change-img-btn" data-bs-toggle="modal" data-bs-target="#imageModal{hid}" title="Change Photo">
          <i class="fa fa-camera"></i>
        </button>
      </div>
      <h4>{j[1]}</h4>
      <span class="badge bg-warning text-dark">Hospital Admin</span>
    </div>

    <div class="profile-body">
      <div class="detail-row">
        <div class="detail-icon" style="background:#e3f2fd;"><i class="fa fa-envelope" style="color:#1565c0;"></i></div>
        <div class="detail-content">
          <div class="detail-label">Email</div>
          <div class="detail-value">{j[14]}</div>
        </div>
      </div>
      <div class="detail-row">
        <div class="detail-icon" style="background:#e8f5e9;"><i class="fa fa-phone" style="color:#2e7d32;"></i></div>
        <div class="detail-content">
          <div class="detail-label">Phone Number</div>
          <div class="detail-value">{j[6]}</div>
        </div>
      </div>
      <div class="detail-row">
        <div class="detail-icon" style="background:#fff8e1;"><i class="fa fa-map-marker-alt" style="color:#f57f17;"></i></div>
        <div class="detail-content">
          <div class="detail-label">Address</div>
          <div class="detail-value">{j[4]}</div>
        </div>
        <div class="detail-action">
          <button class="btn-edit" data-bs-toggle="modal" data-bs-target="#addressModal{hid}">
            <i class="fa fa-edit"></i> Edit
          </button>
        </div>
      </div>
      <div class="detail-row">
        <div class="detail-icon" style="background:#fce4ec;"><i class="fa fa-lock" style="color:#c62828;"></i></div>
        <div class="detail-content">
          <div class="detail-label">Password</div>
          <div class="detail-value" style="letter-spacing:4px;">••••••••</div>
        </div>
        <div class="detail-action">
          <button class="btn-edit" data-bs-toggle="modal" data-bs-target="#passModal{hid}">
            <i class="fa fa-key"></i> Change
          </button>
        </div>
      </div>
    </div>
  </div>
""")

# ================= FEEDBACK SECTION =================
print(f"""
  <!-- FEEDBACK MINI STATS -->
  <div class="mini-stat-row mt-4">
    <a href="hospitalparentfeedback.py?hospital_id={hid}" class="mini-stat">
      <div class="mini-stat-icon" style="background:#eff6ff;"><i class="fa-solid fa-comments" style="color:#1565c0;"></i></div>
      <div><div class="mini-stat-val" style="color:#1565c0;">{parent_fb_count}</div><div class="mini-stat-lbl">Total Feedback</div></div>
    </a>
    <a href="hospitalparentfeedback.py?hospital_id={hid}" class="mini-stat">
      <div class="mini-stat-icon" style="background:#fefce8;"><i class="fa-solid fa-star" style="color:#d97706;"></i></div>
      <div><div class="mini-stat-val" style="color:#d97706;">{parent_fb_avg}</div><div class="mini-stat-lbl">Avg Rating</div></div>
    </a>
    <a href="hospitalparentfeedback.py?hospital_id={hid}&filter=high" class="mini-stat">
      <div class="mini-stat-icon" style="background:#f0fdf4;"><i class="fa-solid fa-thumbs-up" style="color:#16a34a;"></i></div>
      <div><div class="mini-stat-val" style="color:#16a34a;">{parent_fb_high}</div><div class="mini-stat-lbl">High Ratings</div></div>
    </a>
    <a href="hospitalparentfeedback.py?hospital_id={hid}&filter=low" class="mini-stat">
      <div class="mini-stat-icon" style="background:#fef2f2;"><i class="fa-solid fa-triangle-exclamation" style="color:#dc2626;"></i></div>
      <div><div class="mini-stat-val" style="color:#dc2626;">{parent_fb_low}</div><div class="mini-stat-lbl">Low Ratings</div></div>
    </a>
  </div>

  <!-- RECENT PARENT FEEDBACK WIDGET -->
  <h6 class="fw-bold text-muted mb-3" style="font-size:.8rem;letter-spacing:1px;text-transform:uppercase;max-width:860px;margin-left:auto;margin-right:auto;">
    Recent Parent Feedback
  </h6>
  <div class="fb-widget mb-4" style="max-width:860px;margin-left:auto;margin-right:auto;">
    <div class="fb-widget-hdr">
      <h6>
        <i class="fa-solid fa-comments" style="color:#16a34a;"></i>
        Parent Feedback
        {'<span style="background:#fef2f2;color:#dc2626;font-size:.72rem;padding:2px 9px;border-radius:10px;font-weight:700;">' + str(parent_fb_low) + ' low</span>' if parent_fb_low > 0 else ''}
      </h6>
      <div class="fb-mini-badges">
        <span class="fb-mini-badge" style="background:#eff6ff;color:#1565c0;">
          <i class="fa-solid fa-comments"></i> {parent_fb_count} Total
        </span>
        <span class="fb-mini-badge" style="background:#fefce8;color:#d97706;">
          <i class="fa-solid fa-star"></i> {parent_fb_avg} Avg
        </span>
        {'<span class="fb-mini-badge" style="background:#f0fdf4;color:#16a34a;"><i class="fa-solid fa-thumbs-up"></i> ' + str(parent_fb_high) + ' High</span>' if parent_fb_high else ''}
        {'<span class="fb-mini-badge" style="background:#fef2f2;color:#dc2626;"><i class="fa-solid fa-triangle-exclamation"></i> ' + str(parent_fb_low) + ' Low</span>' if parent_fb_low else ''}
      </div>
    </div>

    {('<div class="fb-low-alert"><i class="fa-solid fa-triangle-exclamation"></i><span><strong>' + str(parent_fb_low) + ' low rating(s)</strong> require immediate attention.</span><a href="hospitalparentfeedback.py?hospital_id=' + str(hid) + '&filter=low">Review now →</a></div>') if parent_fb_low > 0 else ''}
""")

if not recent_parent_fb:
    print("""
    <div class="fb-empty">
      <i class="fa-solid fa-star-half-stroke"></i>
      No parent feedback received yet.
    </div>
""")
else:
    for fb in recent_parent_fb:
        rating       = fb[1]
        comment      = fb[2] or ""
        submitted    = str(fb[3])[:16]
        parent_name  = fb[4]
        child_name   = fb[5]
        vaccine_name = fb[6]
        initial      = parent_name[0].upper() if parent_name else "P"
        filled       = "⭐" * rating
        empty_stars  = '<span style="color:#d1d5db">' + "★" * (5 - rating) + "</span>"
        row_cls      = "fb-row-low" if rating < 2 else ""
        av_cls       = "low" if rating < 2 else ""
        short_comment = (comment[:55] + "…") if len(comment) > 55 else comment

        print(f"""
    <div class="fb-row {row_cls}">
      <div class="fb-avatar {av_cls}">{initial}</div>
      <div class="fb-info">
        <div class="fb-parent-name">{parent_name}</div>
        <div class="fb-sub">👶 {child_name} &bull; 💉 {vaccine_name}</div>
        {'<div class="fb-comment">"' + short_comment + '"</div>' if comment else ''}
      </div>
      <div class="fb-right">
        <div class="fb-stars">{filled}{empty_stars}</div>
        <div class="fb-date">{submitted}</div>
      </div>
    </div>
""")

print(f"""
    <div class="fb-widget-footer">
      <a href="hospitalparentfeedback.py?hospital_id={hid}">
        View All Parent Feedback &nbsp;<i class="fa-solid fa-arrow-right"></i>
      </a>
    </div>
  </div>
""")

# ================= MODALS =================
print(f"""
<!-- ADDRESS MODAL -->
<div class="modal fade" id="addressModal{hid}" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <form method="post">
        <div class="modal-header">
          <h5 class="modal-title"><i class="fa fa-map-marker-alt me-2 text-warning"></i>Change Address</h5>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <label class="form-label">New Address</label>
          <textarea name="addressn" class="form-control" rows="3" placeholder="Enter new address" required></textarea>
          <input type="hidden" name="hid" value="{hid}">
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <input type="submit" name="update_address" value="Update Address" class="btn btn-primary">
        </div>
      </form>
    </div>
  </div>
</div>

<!-- PASSWORD MODAL -->
<div class="modal fade" id="passModal{hid}" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <form method="post">
        <div class="modal-header">
          <h5 class="modal-title"><i class="fa fa-key me-2 text-warning"></i>Change Password</h5>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <label class="form-label">New Password</label>
          <input type="password" name="newpass" class="form-control" placeholder="Enter new password" required>
          <input type="hidden" name="hidp" value="{hid}">
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <input type="submit" name="update_pass" value="Update Password" class="btn btn-warning">
        </div>
      </form>
    </div>
  </div>
</div>

<!-- IMAGE MODAL -->
<div class="modal fade" id="imageModal{hid}" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <form method="post" enctype="multipart/form-data">
        <div class="modal-header">
          <h5 class="modal-title"><i class="fa fa-camera me-2 text-info"></i>Change Profile Photo</h5>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <label class="form-label">Select New Image</label>
          <input type="file" name="photo" class="form-control" accept="image/*" required>
          <input type="hidden" name="hidimg" value="{hid}">
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <input type="submit" name="update_img" value="Upload Photo" class="btn btn-info">
        </div>
      </form>
    </div>
  </div>
</div>

</main>

<script>
function toggleSidebar() {{
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('overlay').classList.toggle('open');
}}
</script>
</body>
</html>
""")
con.close()