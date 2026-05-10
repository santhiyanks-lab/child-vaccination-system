#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
print("Content-Type: text/html\r\n\r\n")

import cgi, cgitb, pymysql, sys
sys.stdout.reconfigure(encoding='utf-8')
cgitb.enable()

# ─── DB ──────────────────────────────────────────────────────────────────────
con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()

form = cgi.FieldStorage()
oid  = form.getvalue("hospital_id")

if oid is None:
    print("<h3 style='color:red;text-align:center;margin-top:50px;'>Hospital ID Missing! Please login again.</h3>")
    exit()

# ─── Hospital info ────────────────────────────────────────────────────────────
cur.execute("SELECT * FROM hospital WHERE hospital_id=%s", (oid,))
hospital      = cur.fetchone()
hospital_name = hospital[1] if hospital else "Hospital"

# ─── Vaccine stats ────────────────────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM child_vaccine WHERE hospital_id=%s AND status='pending'",     (oid,))
pending     = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM child_vaccine WHERE hospital_id=%s AND status='confirmed'",   (oid,))
confirmed   = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM child_vaccine WHERE hospital_id=%s AND status='completed'",   (oid,))
completed   = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM child_vaccine WHERE hospital_id=%s AND status='rescheduled'", (oid,))
rescheduled = cur.fetchone()[0]

# ─── Hospital Feedback stats ──────────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM hospitalfeedback WHERE hospital_id=%s", (oid,))
total_fb    = cur.fetchone()[0]

cur.execute("SELECT ROUND(AVG(rating),1) FROM hospitalfeedback WHERE hospital_id=%s", (oid,))
row         = cur.fetchone()
avg_rating  = float(row[0]) if row and row[0] else 0.0

cur.execute("SELECT COUNT(*) FROM hospitalfeedback WHERE hospital_id=%s AND resolved=0", (oid,))
unresolved  = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM hospitalfeedback WHERE hospital_id=%s AND rating<=2", (oid,))
low_ratings = cur.fetchone()[0]

# ─── Parent feedback stats ────────────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM feedback WHERE hospital_id=%s", (oid,))
parent_fb_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM feedback WHERE hospital_id=%s AND rating<2", (oid,))
parent_fb_low = cur.fetchone()[0]

cur.execute("SELECT ROUND(AVG(rating),1) FROM feedback WHERE hospital_id=%s", (oid,))
row2 = cur.fetchone()
parent_fb_avg = float(row2[0]) if row2 and row2[0] else 0.0

cur.execute("SELECT COUNT(*) FROM feedback WHERE hospital_id=%s AND rating>=4", (oid,))
parent_fb_high = cur.fetchone()[0]

# ─── Recent parent feedback (last 5) ─────────────────────────────────────────
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
""", (oid,))
recent_parent_fb = cur.fetchall()

print(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hospital Dashboard</title>
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
  .topbar .brand {{ color:#fff; font-size:1rem; font-weight:700; white-space:nowrap; }}
  .topbar .subbrand {{ color:#90a4ae; font-size:.78rem; display:block; }}
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
  .page-header {{ display:flex; align-items:flex-start; gap:14px; margin-bottom:24px; flex-wrap:wrap; }}
  .page-header-icon {{ background:linear-gradient(135deg,var(--primary),#42a5f5); color:#fff; width:52px; height:52px; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:1.4rem; flex-shrink:0; box-shadow:0 4px 12px rgba(21,101,192,.3); }}
  .page-header-text h4 {{ font-size:1.3rem; font-weight:700; color:#1e293b; margin:0 0 4px; }}
  .page-header-text p {{ font-size:.88rem; color:#64748b; margin:0; }}

  /* WELCOME */
  .welcome-card {{
    background: linear-gradient(135deg, #0d47a1, #1976d2);
    border-radius: 16px; padding: 28px 32px; color: #fff;
    box-shadow: 0 4px 20px rgba(13,71,161,.3); position: relative; overflow: hidden;
  }}
  .welcome-card::before {{ content:''; position:absolute; top:-40px; right:-40px; width:180px; height:180px; background:rgba(255,255,255,.06); border-radius:50%; }}
  .welcome-card::after  {{ content:''; position:absolute; bottom:-60px; right:60px; width:240px; height:240px; background:rgba(255,255,255,.04); border-radius:50%; }}
  .welcome-card h3 {{ font-size:clamp(1.1rem,3vw,1.5rem); font-weight:700; margin:0 0 6px; }}
  .welcome-card p  {{ font-size:.9rem; opacity:.85; margin:0; }}

  /* STAT CARDS */
  .stat-card {{
    border:none; border-radius:14px; padding:20px;
    display:flex; align-items:center; gap:16px;
    box-shadow:0 2px 12px rgba(0,0,0,.08); transition:transform .2s,box-shadow .2s;
    background:#fff; cursor:pointer; text-decoration:none; color:inherit; height:100%;
  }}
  .stat-card:hover {{ transform:translateY(-3px); box-shadow:0 8px 24px rgba(0,0,0,.12); color:inherit; }}
  .stat-icon {{ width:52px; height:52px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:1.3rem; flex-shrink:0; }}
  .stat-info h3 {{ font-size:1.6rem; font-weight:800; margin:0; line-height:1; }}
  .stat-info p  {{ font-size:.8rem; color:#64748b; margin:4px 0 0; font-weight:500; }}

  /* QUICK LINKS */
  .quick-link {{
    background:#fff; border:none; border-radius:12px; padding:18px 16px;
    text-align:center; text-decoration:none; color:#1e293b;
    box-shadow:0 2px 10px rgba(0,0,0,.07); transition:all .2s;
    display:flex; flex-direction:column; align-items:center; gap:10px; height:100%;
  }}
  .quick-link:hover {{ transform:translateY(-3px); box-shadow:0 8px 20px rgba(0,0,0,.12); color:#1e293b; }}
  .quick-link .ql-icon {{ width:48px; height:48px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:1.2rem; }}
  .quick-link span {{ font-size:.85rem; font-weight:600; }}

  /* FEEDBACK WIDGET */
  .fb-widget {{
    background:#fff; border-radius:14px;
    box-shadow:0 2px 12px rgba(0,0,0,.08);
    border:1px solid #e2e8f0; overflow:hidden;
  }}
  .fb-widget-hdr {{
    display:flex; align-items:center; justify-content:space-between;
    padding:16px 20px; border-bottom:1px solid #f1f5f9; flex-wrap:wrap; gap:8px;
  }}
  .fb-widget-hdr h6 {{
    font-size:.95rem; font-weight:700; margin:0;
    display:flex; align-items:center; gap:8px;
  }}
  .fb-mini-badges {{ display:flex; gap:8px; flex-wrap:wrap; }}
  .fb-mini-badge {{
    display:inline-flex; align-items:center; gap:5px;
    padding:4px 11px; border-radius:20px; font-size:.75rem; font-weight:700;
  }}
  .fb-low-alert {{
    display:flex; align-items:center; gap:10px;
    background:#fff5f5; border-bottom:1px solid #fed7d7;
    padding:9px 20px; font-size:.83rem; color:#c53030;
  }}
  .fb-low-alert a {{ color:#c53030; font-weight:700; text-decoration:underline; margin-left:auto; }}
  .fb-row {{
    display:flex; align-items:center; gap:12px;
    padding:11px 20px; border-bottom:1px solid #f8fafc;
    transition:background .15s;
  }}
  .fb-row:last-child {{ border-bottom:none; }}
  .fb-row:hover {{ background:#f8fafc; }}
  .fb-row.fb-row-low {{ background:#fff5f5; border-left:3px solid #e53935; }}
  .fb-avatar {{
    width:38px; height:38px; border-radius:50%;
    background:linear-gradient(135deg,#1565c0,#0d47a1);
    color:#fff; font-weight:800; font-size:.9rem;
    display:flex; align-items:center; justify-content:center; flex-shrink:0;
  }}
  .fb-avatar.low {{ background:linear-gradient(135deg,#e53935,#c62828); }}
  .fb-info {{ flex:1; min-width:0; }}
  .fb-parent-name {{ font-size:.87rem; font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .fb-sub {{ font-size:.73rem; color:#64748b; margin-top:1px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .fb-comment {{ font-size:.75rem; color:#4b5563; font-style:italic; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .fb-right {{ text-align:right; flex-shrink:0; }}
  .fb-stars {{ font-size:.85rem; line-height:1; }}
  .fb-date  {{ font-size:.7rem; color:#94a3b8; margin-top:3px; }}
  .fb-widget-footer {{
    padding:12px 20px; background:#f8fafc;
    border-top:1px solid #f1f5f9; text-align:center;
  }}
  .fb-widget-footer a {{
    font-size:.84rem; font-weight:700; color:var(--primary);
    text-decoration:none; display:inline-flex; align-items:center; gap:6px;
  }}
  .fb-widget-footer a:hover {{ color:var(--primary-dark); text-decoration:underline; }}
  .fb-empty {{ text-align:center; padding:32px 20px; color:#94a3b8; font-size:.86rem; }}
  .fb-empty i {{ display:block; font-size:2rem; opacity:.25; margin-bottom:8px; }}

  @media (max-width:991px) {{
    .sidebar {{ transform:translateX(-100%); }}
    .sidebar.open {{ transform:translateX(0); }}
    .sidebar-overlay.open {{ display:block; }}
    .main {{ margin-left:0; }}
    .hamburger {{ display:block; }}
  }}
  @media (max-width:576px) {{
    .main {{ padding:16px 12px; }}
    .welcome-card {{ padding:20px 18px; }}
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

  <a href="hospital_dash.py?hospital_id={oid}" class="nav-link active">
    <i class="fa fa-gauge"></i> Dashboard
  </a>
  <a href="hospital_profile.py?hospital_id={oid}" class="nav-link">
    <i class="fa fa-hospital"></i> My Profile
  </a>

  <hr class="sidebar-divider">
  <div class="sidebar-label">Vaccinations</div>

  <details class="sidebar-group" open>
    <summary>
      <i class="fa-solid fa-syringe"></i> Vaccine Details
      <i class="fa fa-chevron-right caret"></i>
    </summary>
    <div class="sub-links">
      <a href="hospitalpendingvaccine.py?hospital_id={oid}">
        <i class="fa-solid fa-clock"></i> Pending
      </a>
      <a href="hospitalconfirmedvaccine.py?hospital_id={oid}">
        <i class="fa-solid fa-check"></i> Confirmed
      </a>
      <a href="hospitalrescheduledvaccine.py?hospital_id={oid}">
        <i class="fa-solid fa-calendar-days"></i> Rescheduled
      </a>
      <a href="hospitalcompletedvaccine.py?hospital_id={oid}">
        <i class="fa-solid fa-circle-check"></i> Completed
      </a>
    </div>
  </details>

  <hr class="sidebar-divider">
  <div class="sidebar-label">Feedback</div>

  <details class="sidebar-group" {'open' if (total_fb > 0 or parent_fb_count > 0) else ''}>
    <summary>
      <i class="fa-solid fa-star"></i> Feedback
      {'<span class="badge bg-danger ms-auto" style="font-size:.7rem;">' + str(unresolved + parent_fb_low) + '</span>' if (unresolved + parent_fb_low) > 0 else ''}
      <i class="fa fa-chevron-right caret"></i>
    </summary>
    <div class="sub-links">
      <a href="hospitalparentfeedback.py?hospital_id={oid}">
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

  <div class="welcome-card mb-4">
    <h3>Welcome back, {hospital_name} 👋</h3>
    <p>Manage your vaccine schedule and patient records from this dashboard.</p>
  </div>

  <div class="page-header">
    <div class="page-header-icon"><i class="fa fa-gauge"></i></div>
    <div class="page-header-text">
      <h4>Dashboard Overview</h4>
      <p>Summary of all vaccination activities for your hospital</p>
    </div>
  </div>

  <!-- Row 1: Appointment Stats -->
  <div class="row g-3 mb-3">
    <div class="col-6 col-lg-3">
      <a href="hospitalpendingvaccine.py?hospital_id={oid}" class="stat-card">
        <div class="stat-icon" style="background:#fff3e0;">
          <i class="fa-solid fa-clock" style="color:#e65100;"></i>
        </div>
        <div class="stat-info">
          <h3 style="color:#e65100;">{pending}</h3>
          <p>Pending</p>
        </div>
      </a>
    </div>
    <div class="col-6 col-lg-3">
      <a href="hospitalconfirmedvaccine.py?hospital_id={oid}" class="stat-card">
        <div class="stat-icon" style="background:#e3f2fd;">
          <i class="fa-solid fa-check" style="color:#1565c0;"></i>
        </div>
        <div class="stat-info">
          <h3 style="color:#1565c0;">{confirmed}</h3>
          <p>Confirmed</p>
        </div>
      </a>
    </div>
    <div class="col-6 col-lg-3">
      <a href="hospitalrescheduledvaccine.py?hospital_id={oid}" class="stat-card">
        <div class="stat-icon" style="background:#f3e5f5;">
          <i class="fa-solid fa-calendar-days" style="color:#6a1b9a;"></i>
        </div>
        <div class="stat-info">
          <h3 style="color:#6a1b9a;">{rescheduled}</h3>
          <p>Rescheduled</p>
        </div>
      </a>
    </div>
    <div class="col-6 col-lg-3">
      <a href="hospitalcompletedvaccine.py?hospital_id={oid}" class="stat-card">
        <div class="stat-icon" style="background:#e8f5e9;">
          <i class="fa-solid fa-circle-check" style="color:#2e7d32;"></i>
        </div>
        <div class="stat-info">
          <h3 style="color:#2e7d32;">{completed}</h3>
          <p>Completed</p>
        </div>
      </a>
    </div>
  </div>

  <!-- Row 2: Feedback Stats -->
  <div class="row g-3 mb-4">
    <div class="col-6 col-lg-3">
      <a href="hospitalfeedback.py?hospital_id={oid}" class="stat-card">
        <div class="stat-icon" style="background:#fefce8;">
          <i class="fa-solid fa-star" style="color:#f59e0b;"></i>
        </div>
        <div class="stat-info">
          <h3 style="color:#f59e0b;">{avg_rating}</h3>
          <p>Avg Rating</p>
        </div>
      </a>
    </div>
    <div class="col-6 col-lg-3">
      <a href="hospitalfeedback.py?hospital_id={oid}" class="stat-card">
        <div class="stat-icon" style="background:#eff6ff;">
          <i class="fa-solid fa-comments" style="color:#1565c0;"></i>
        </div>
        <div class="stat-info">
          <h3 style="color:#1565c0;">{total_fb}</h3>
          <p>Total Feedback</p>
        </div>
      </a>
    </div>
    <div class="col-6 col-lg-3">
      <a href="hospitalfeedback.py?hospital_id={oid}&filter=unresolved" class="stat-card">
        <div class="stat-icon" style="background:#fef2f2;">
          <i class="fa-solid fa-hourglass-half" style="color:#dc2626;"></i>
        </div>
        <div class="stat-info">
          <h3 style="color:#dc2626;">{unresolved}</h3>
          <p>Unresolved</p>
        </div>
      </a>
    </div>
    <div class="col-6 col-lg-3">
      <a href="hospitalparentfeedback.py?hospital_id={oid}" class="stat-card">
        <div class="stat-icon" style="background:#f0fdf4;">
          <i class="fa-solid fa-user-pen" style="color:#16a34a;"></i>
        </div>
        <div class="stat-info">
          <h3 style="color:#16a34a;">{parent_fb_count}</h3>
          <p>Parent Feedback</p>
        </div>
      </a>
    </div>
  </div>

  <!-- ═══════════════ RECENT PARENT FEEDBACK WIDGET ═══════════════ -->
  <h6 class="fw-bold text-muted mb-3" style="font-size:.8rem;letter-spacing:1px;text-transform:uppercase;">
    Recent Parent Feedback
  </h6>
  <div class="fb-widget mb-4">
    <!-- Header with mini stats -->
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

    <!-- Low-rating alert strip -->
    {('<div class="fb-low-alert"><i class="fa-solid fa-triangle-exclamation"></i><span><strong>' + str(parent_fb_low) + ' low rating(s)</strong> require immediate attention.</span><a href="hospitalparentfeedback.py?hospital_id=' + str(oid) + '&filter=low">Review now →</a></div>') if parent_fb_low > 0 else ''}

    <!-- Recent rows -->
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
        fb_id        = fb[0]
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
    <!-- Footer -->
    <div class="fb-widget-footer">
      <a href="hospitalparentfeedback.py?hospital_id={oid}">
        View All Parent Feedback &nbsp;<i class="fa-solid fa-arrow-right"></i>
      </a>
    </div>
  </div>
  <!-- ═══════════════ END FEEDBACK WIDGET ═══════════════════════ -->

  <!-- Quick Access -->
  <div class="mb-3">
    <h6 class="fw-bold text-muted mb-3" style="font-size:.8rem;letter-spacing:1px;text-transform:uppercase;">Quick Access</h6>
    <div class="row g-3">
      <div class="col-6 col-sm-4 col-md-3">
        <a href="hospital_profile.py?hospital_id={oid}" class="quick-link">
          <div class="ql-icon" style="background:#e3f2fd;"><i class="fa fa-hospital" style="color:#1565c0;"></i></div>
          <span>My Profile</span>
        </a>
      </div>
      <div class="col-6 col-sm-4 col-md-3">
        <a href="hospitalpendingvaccine.py?hospital_id={oid}" class="quick-link">
          <div class="ql-icon" style="background:#fff3e0;"><i class="fa-solid fa-clock" style="color:#e65100;"></i></div>
          <span>Pending Vaccines</span>
        </a>
      </div>
      <div class="col-6 col-sm-4 col-md-3">
        <a href="hospitalfeedback.py?hospital_id={oid}" class="quick-link">
          <div class="ql-icon" style="background:#fefce8;"><i class="fa-solid fa-star" style="color:#f59e0b;"></i></div>
          <span>Hospital Feedback</span>
        </a>
      </div>
      <div class="col-6 col-sm-4 col-md-3">
        <a href="hospitalparentfeedback.py?hospital_id={oid}" class="quick-link">
          <div class="ql-icon" style="background:#f0fdf4;"><i class="fa-solid fa-comments" style="color:#16a34a;"></i></div>
          <span>Parent Feedback</span>
        </a>
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