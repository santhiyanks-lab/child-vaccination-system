#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
import sys, pymysql, cgi, cgitb
sys.stdout.reconfigure(encoding="utf-8")
print("Content-Type:text/html\r\n\r\n")
cgitb.enable()

con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()

form = cgi.FieldStorage()
oid = form.getvalue("hospital_id")

if not oid:
    print("<h3 style='color:red;text-align:center;margin-top:60px;'>Hospital ID Missing! Please login again.</h3>")
    exit()

oid = int(oid)  # ← FIX: cast to int so SQL comparison works correctly

# Hospital info
cur.execute("SELECT * FROM hospital WHERE hospital_id=%s", (oid,))
hospital      = cur.fetchone()
hospital_name = hospital[1] if hospital else "Hospital"

# Vaccine stats (for sidebar badges)
cur.execute("SELECT COUNT(*) FROM child_vaccine WHERE hospital_id=%s AND status='pending'", (oid,))
pending = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM child_vaccine WHERE hospital_id=%s AND status='confirmed'", (oid,))
confirmed = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM child_vaccine WHERE hospital_id=%s AND status='completed'", (oid,))
completed = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM child_vaccine WHERE hospital_id=%s AND status='rescheduled'", (oid,))
rescheduled = cur.fetchone()[0]

# Hospital feedback stats (for sidebar)
cur.execute("SELECT COUNT(*) FROM hospitalfeedback WHERE hospital_id=%s", (oid,))
total_hfb = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM hospitalfeedback WHERE hospital_id=%s AND resolved=0", (oid,))
unresolved = cur.fetchone()[0]

# ── MAIN FIX: Simplified query — no correlated subquery that could silently fail ──
cur.execute("""
    SELECT
        f.feedback_id,
        f.rating,
        f.comment,
        f.submitted_at,
        f.updated_at,
        f.notified,
        p.father_name,
        p.email,
        p.mobile_number,
        c.child_name,
        c.dob,
        c.gender,
        c.blood_group,
        v.vaccine_name,
        v.minimum_age,
        cv.dose_number,
        cv.appointment_date
    FROM feedback f
    JOIN parent   p  ON f.parent_id  = p.parent_id
    JOIN children c  ON f.child_id   = c.child_id
    JOIN vaccine  v  ON f.vaccine_id = v.vaccine_id
    LEFT JOIN child_vaccine cv
           ON cv.child_id   = f.child_id
          AND cv.vaccine_id  = f.vaccine_id
          AND cv.hospital_id = f.hospital_id
    WHERE f.hospital_id = %s
    ORDER BY f.submitted_at DESC
""", (oid,))
feedbacks = cur.fetchall()

total_fb   = len(feedbacks)
low_fb     = sum(1 for f in feedbacks if f[1] < 2)
avg_rating = round(sum(f[1] for f in feedbacks) / total_fb, 1) if total_fb else 0
high_fb    = sum(1 for f in feedbacks if f[1] >= 4)

print(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Parent Feedback | {hospital_name}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
  <style>
    :root {{
      --sidebar-w: 260px;
      --topbar-h: 60px;
      --primary: #1565c0;
      --bg: #f0f4f8;
      --da: #e53935; --dl: #ffebee;
      --su: #2e7d32; --sl: #e8f5e9;
      --wa: #f57f17; --wl: #fff8e1;
      --bo: #dde3ea; --ca: #fff;
      --mu: #6b7280; --tx: #1c1c1c;
      --ra: 10px; --sh: 0 2px 16px rgba(0,0,0,.09);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--tx); }}
    a {{ text-decoration: none; color: inherit; }}

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
    .topbar-right a {{ color:#cfd8dc; font-size:.85rem; padding:6px 14px; border:1px solid #37474f; border-radius:6px; transition:all .2s; }}
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
    .sidebar .nav-link {{ color:#b0bec5; border-radius:8px; padding:9px 12px; font-size:.87rem; display:flex; align-items:center; gap:10px; transition:all .2s; margin-bottom:2px; }}
    .sidebar .nav-link i {{ width:18px; text-align:center; font-size:.9rem; }}
    .sidebar .nav-link:hover, .sidebar .nav-link.active {{ background:var(--primary); color:#fff; }}
    .sidebar-group summary {{ list-style:none; color:#b0bec5; padding:9px 12px; border-radius:8px; display:flex; align-items:center; gap:10px; cursor:pointer; font-size:.87rem; transition:background .2s; margin-bottom:2px; user-select:none; }}
    .sidebar-group summary::-webkit-details-marker {{ display:none; }}
    .sidebar-group summary:hover {{ background:#1c2d3e; color:#fff; }}
    .sidebar-group summary .caret {{ margin-left:auto; transition:transform .25s; font-size:.75rem; }}
    .sidebar-group[open] summary .caret {{ transform:rotate(90deg); }}
    .sidebar-group[open] summary {{ color:#fff; background:#1c2d3e; }}
    .sub-links {{ padding:4px 0 4px 28px; }}
    .sub-links a {{ display:flex; align-items:center; gap:8px; color:#78909c; font-size:.83rem; padding:7px 10px; border-radius:6px; transition:all .2s; margin-bottom:1px; }}
    .sub-links a:hover, .sub-links a.active {{ color:#fff; background:rgba(255,255,255,.07); }}
    .sub-links a i {{ width:14px; font-size:.8rem; }}
    .sidebar-divider {{ border:none; border-top:1px solid #1c2d3e; margin:10px 0; }}
    .sidebar-overlay {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,.55); z-index:999; backdrop-filter:blur(2px); }}

    /* MAIN */
    .main {{ margin-left:var(--sidebar-w); margin-top:var(--topbar-h); padding:28px 24px; min-height:calc(100vh - var(--topbar-h)); }}

    /* PAGE HEADER */
    .page-hdr {{
      background: linear-gradient(120deg,#1565c0,#0d47a1); color:#fff;
      border-radius: var(--ra); padding: 22px 28px; margin-bottom: 24px;
      display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;
    }}
    .page-hdr h2 {{ font-size:1.1rem; font-weight:700; margin-bottom:3px; }}
    .page-hdr p  {{ font-size:.83rem; opacity:.85; margin:0; }}
    .page-hdr-badge {{ background:rgba(255,255,255,.2); padding:7px 16px; border-radius:20px; font-size:.83rem; font-weight:700; }}

    /* LOW ALERT */
    .low-banner {{ display:flex; align-items:center; gap:12px; background:var(--dl); border:1px solid #ef9a9a; border-radius:var(--ra); padding:12px 18px; margin-bottom:18px; font-size:.88rem; color:var(--da); }}
    .low-banner i {{ font-size:1.1rem; flex-shrink:0; }}

    /* STATS */
    .stats-row {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:14px; margin-bottom:24px; }}
    .stat-card {{ background:var(--ca); border-radius:var(--ra); box-shadow:var(--sh); border:1px solid var(--bo); padding:16px 18px; display:flex; align-items:center; gap:14px; text-decoration:none; color:inherit; transition:transform .2s,box-shadow .2s; }}
    .stat-card:hover {{ transform:translateY(-2px); box-shadow:0 6px 20px rgba(0,0,0,.12); color:inherit; }}
    .stat-icon {{ width:44px; height:44px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:1.2rem; flex-shrink:0; }}
    .stat-val {{ font-size:1.5rem; font-weight:800; line-height:1; }}
    .stat-lbl {{ font-size:.75rem; color:var(--mu); margin-top:3px; }}

    /* TOOLBAR */
    .toolbar {{ display:flex; align-items:center; gap:12px; margin-bottom:18px; flex-wrap:wrap; }}
    .sbox {{ position:relative; flex:1; min-width:200px; }}
    .sbox i {{ position:absolute; left:11px; top:50%; transform:translateY(-50%); color:var(--mu); font-size:.82rem; }}
    .sbox input {{ width:100%; padding:9px 12px 9px 34px; border:1.5px solid var(--bo); border-radius:8px; font-family:'Segoe UI',sans-serif; font-size:.85rem; background:var(--ca); transition:border-color .25s; }}
    .sbox input:focus {{ outline:none; border-color:var(--primary); }}
    .fsel {{ padding:9px 14px; border:1.5px solid var(--bo); border-radius:8px; font-family:'Segoe UI',sans-serif; font-size:.85rem; background:var(--ca); color:var(--tx); cursor:pointer; }}
    .fsel:focus {{ outline:none; border-color:var(--primary); }}
    .cnt-lbl {{ font-size:.84rem; color:var(--mu); font-weight:600; white-space:nowrap; }}

    /* FEEDBACK CARDS */
    .fb-card {{ background:var(--ca); border-radius:var(--ra); box-shadow:var(--sh); border:1px solid var(--bo); margin-bottom:16px; overflow:hidden; transition:box-shadow .25s; }}
    .fb-card:hover {{ box-shadow:0 4px 20px rgba(0,0,0,.13); }}
    .fb-card.low  {{ border-left:4px solid var(--da); background:#fffafa; }}
    .fb-card.high {{ border-left:4px solid var(--su); }}
    .fb-top {{ display:flex; align-items:center; justify-content:space-between; padding:14px 20px; flex-wrap:wrap; gap:10px; }}
    .fb-left {{ display:flex; align-items:center; gap:14px; }}
    .fb-avatar {{ width:44px; height:44px; border-radius:50%; background:linear-gradient(135deg,#1565c0,#0d47a1); display:flex; align-items:center; justify-content:center; font-size:1.1rem; font-weight:800; color:#fff; flex-shrink:0; }}
    .fb-avatar.low  {{ background:linear-gradient(135deg,var(--da),#c62828); }}
    .fb-avatar.high {{ background:linear-gradient(135deg,var(--su),#1b5e20); }}
    .fb-name {{ font-size:.95rem; font-weight:700; }}
    .fb-meta {{ font-size:.76rem; color:var(--mu); margin-top:2px; }}
    .stars-big {{ font-size:1.2rem; line-height:1; }}
    .rating-num {{ font-size:.9rem; font-weight:800; }}
    .badge-low      {{ background:var(--dl); color:var(--da); padding:3px 10px; border-radius:20px; font-size:.73rem; font-weight:700; }}
    .badge-notified {{ background:#fff3e0; color:#e65100; padding:3px 10px; border-radius:20px; font-size:.73rem; font-weight:700; }}
    .badge-edited   {{ background:#e3f2fd; color:#1565c0; padding:3px 10px; border-radius:20px; font-size:.73rem; font-weight:700; }}
    .btn-expand {{ display:inline-flex; align-items:center; gap:6px; padding:7px 16px; background:var(--primary); color:#fff; border:none; border-radius:8px; font-size:.82rem; font-weight:600; font-family:'Segoe UI',sans-serif; cursor:pointer; transition:background .25s; }}
    .btn-expand:hover {{ background:#0d47a1; }}

    /* DETAIL PANEL */
    .fb-detail {{ display:none; border-top:1px solid var(--bo); padding:18px 20px; }}
    .fb-detail.open {{ display:block; }}
    .detail-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(190px,1fr)); gap:10px 20px; margin-bottom:14px; }}
    .di {{ background:var(--bg); border:1px solid var(--bo); border-radius:8px; padding:9px 13px; }}
    .di label {{ display:block; font-size:.67rem; color:var(--mu); font-weight:700; text-transform:uppercase; letter-spacing:.4px; margin-bottom:3px; }}
    .di span {{ font-size:.86rem; font-weight:600; color:var(--tx); word-break:break-word; }}
    .comment-box {{ background:var(--bg); border:1px solid var(--bo); border-radius:8px; padding:12px 16px; }}
    .comment-box p {{ font-size:.88rem; color:var(--tx); margin:0; }}
    .section-title {{ font-size:.72rem; font-weight:700; color:var(--mu); text-transform:uppercase; letter-spacing:.8px; margin:14px 0 8px; display:flex; align-items:center; gap:6px; }}
    .section-title::after {{ content:''; flex:1; height:1px; background:var(--bo); }}

    .empty {{ text-align:center; padding:60px 20px; color:var(--mu); }}
    .empty i {{ font-size:3rem; opacity:.3; display:block; margin-bottom:14px; }}

    footer {{ background:#1c1c2e; color:rgba(255,255,255,.6); text-align:center; padding:14px 20px; font-size:.8rem; }}

    @media (max-width:991px) {{
      .sidebar {{ transform:translateX(-100%); }}
      .sidebar.open {{ transform:translateX(0); }}
      .sidebar-overlay.open {{ display:block; }}
      .main {{ margin-left:0; }}
      .hamburger {{ display:block; }}
    }}
    @media (max-width:576px) {{
      .main {{ padding:16px 12px; }}
      .detail-grid {{ grid-template-columns:1fr 1fr; }}
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

  <a href="hospital_dash.py?hospital_id={oid}" class="nav-link">
    <i class="fa fa-gauge"></i> Dashboard
  </a>
  <a href="hospital_profile.py?hospital_id={oid}" class="nav-link">
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
      <a href="hospitalpendingvaccine.py?hospital_id={oid}">
        <i class="fa-solid fa-clock"></i> Pending
        {'<span style="margin-left:auto;background:#f97316;color:#fff;font-size:.65rem;font-weight:700;min-width:17px;height:17px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;padding:0 4px;">' + str(pending) + '</span>' if pending > 0 else ''}
      </a>
      <a href="hospitalconfirmedvaccine.py?hospital_id={oid}">
        <i class="fa-solid fa-check"></i> Confirmed
        {'<span style="margin-left:auto;background:#1565c0;color:#fff;font-size:.65rem;font-weight:700;min-width:17px;height:17px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;padding:0 4px;">' + str(confirmed) + '</span>' if confirmed > 0 else ''}
      </a>
      <a href="hospitalrescheduledvaccine.py?hospital_id={oid}">
        <i class="fa-solid fa-calendar-days"></i> Rescheduled
        {'<span style="margin-left:auto;background:#7c3aed;color:#fff;font-size:.65rem;font-weight:700;min-width:17px;height:17px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;padding:0 4px;">' + str(rescheduled) + '</span>' if rescheduled > 0 else ''}
      </a>
      <a href="hospitalcompletedvaccine.py?hospital_id={oid}">
        <i class="fa-solid fa-circle-check"></i> Completed
        {'<span style="margin-left:auto;background:#2e7d32;color:#fff;font-size:.65rem;font-weight:700;min-width:17px;height:17px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;padding:0 4px;">' + str(completed) + '</span>' if completed > 0 else ''}
      </a>
    </div>
  </details>

  <hr class="sidebar-divider">
  <div class="sidebar-label">Feedback</div>

  <details class="sidebar-group" open>
    <summary>
      <i class="fa-solid fa-star"></i> Feedback
      {'<span class="badge bg-danger ms-auto" style="font-size:.7rem;">' + str(unresolved + low_fb) + '</span>' if (unresolved + low_fb) > 0 else ''}
      <i class="fa fa-chevron-right caret"></i>
    </summary>
    <div class="sub-links">
      <a href="hospitalparentfeedback.py?hospital_id={oid}" class="active">
        <i class="fa-solid fa-comments"></i> Parent Feedback
        {'<span style="margin-left:auto;background:#e53935;color:#fff;font-size:.65rem;font-weight:700;min-width:17px;height:17px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;padding:0 4px;">' + str(low_fb) + '</span>' if low_fb > 0 else ''}
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

  <div class="page-hdr">
    <div>
      <h2><i class="fa-solid fa-comments"></i>&nbsp; Parent Feedback</h2>
      <p>Feedback submitted by parents for vaccinations at <strong>{hospital_name}</strong></p>
    </div>
    <span class="page-hdr-badge"><i class="fa-solid fa-star"></i> {total_fb} Total</span>
  </div>
""")

if low_fb:
    print(f"""
  <div class="low-banner">
    <i class="fa-solid fa-triangle-exclamation"></i>
    <span>You have <strong>{low_fb} low rating(s)</strong> (below 2 stars). Please review and take action to improve patient experience.</span>
  </div>
""")

print(f"""
  <!-- STATS -->
  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-icon" style="background:#e3f2fd;"><i class="fa-solid fa-comments" style="color:#1565c0;"></i></div>
      <div><div class="stat-val" style="color:#1565c0;">{total_fb}</div><div class="stat-lbl">Total</div></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon" style="background:#fff8e1;"><i class="fa-solid fa-star" style="color:#f57f17;"></i></div>
      <div><div class="stat-val" style="color:#f57f17;">{avg_rating}</div><div class="stat-lbl">Avg Rating</div></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon" style="background:var(--dl);"><i class="fa-solid fa-triangle-exclamation" style="color:var(--da);"></i></div>
      <div><div class="stat-val" style="color:var(--da);">{low_fb}</div><div class="stat-lbl">Low (&lt;2 Stars)</div></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon" style="background:var(--sl);"><i class="fa-solid fa-thumbs-up" style="color:var(--su);"></i></div>
      <div><div class="stat-val" style="color:var(--su);">{high_fb}</div><div class="stat-lbl">High (4-5 Stars)</div></div>
    </div>
  </div>

  <!-- TOOLBAR -->
  <div class="toolbar">
    <div class="sbox">
      <i class="fa-solid fa-magnifying-glass"></i>
      <input type="text" id="searchInput" placeholder="Search parent name, child, vaccine..." oninput="filterCards()">
    </div>
    <select class="fsel" id="ratingFilter" onchange="filterCards()">
      <option value="">All Ratings</option>
      <option value="low">Low (&lt;2 stars)</option>
      <option value="mid">Mid (2-3 stars)</option>
      <option value="high">High (4-5 stars)</option>
    </select>
    <span class="cnt-lbl" id="cntLbl">{total_fb} records</span>
  </div>
""")

if not feedbacks:
    print("""
  <div class="empty">
    <i class="fa-solid fa-star-half-stroke"></i>
    <p>No parent feedback received yet for this hospital.</p>
  </div>
""")
else:
    for fb in feedbacks:
        fb_id        = fb[0]
        rating       = fb[1]
        comment      = fb[2] or ""
        submitted    = str(fb[3])[:16]
        updated      = str(fb[4])[:16] if fb[4] else None
        notified     = fb[5]
        parent_name  = fb[6]
        parent_email = fb[7]
        parent_mob   = fb[8]
        child_name   = fb[9]
        child_dob    = str(fb[10]) if fb[10] else "N/A"
        child_gender = fb[11] or "N/A"
        child_blood  = fb[12] or "N/A"
        vaccine      = fb[13]
        min_age      = fb[14] or "N/A"
        dose         = fb[15] or "N/A"
        appt_date    = str(fb[16])[:10] if fb[16] else "N/A"

        filled      = "⭐" * rating
        empty       = '<span style="color:#d1d5db">' + "★" * (5 - rating) + "</span>"
        card_cls    = "low" if rating < 2 else ("high" if rating >= 4 else "")
        av_cls      = "low" if rating < 2 else ("high" if rating >= 4 else "")
        initial     = parent_name[0].upper() if parent_name else "P"
        data_rating = "low" if rating < 2 else ("high" if rating >= 4 else "mid")
        rating_color= "var(--da)" if rating < 2 else ("var(--su)" if rating >= 4 else "var(--wa)")

        print(f"""
  <div class="fb-card {card_cls}"
       data-search="{parent_name.lower()} {child_name.lower()} {vaccine.lower()}"
       data-rating="{data_rating}">
    <div class="fb-top">
      <div class="fb-left">
        <div class="fb-avatar {av_cls}">{initial}</div>
        <div>
          <div class="fb-name">{parent_name}</div>
          <div class="fb-meta">👶 {child_name} &bull; 💉 {vaccine}</div>
          <div class="fb-meta" style="margin-top:2px;">
            🗓️ {submitted}
            {"&nbsp;<span class='badge-edited'>✏️ Edited " + updated + "</span>" if updated else ""}
            {"&nbsp;<span class='badge-notified'>⚠️ Notified</span>" if notified else ""}
            {"&nbsp;<span class='badge-low'>🚨 Low Rating</span>" if rating < 2 else ""}
          </div>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
        <div style="text-align:center;">
          <div class="stars-big">{filled}{empty}</div>
          <div class="rating-num" style="color:{rating_color};">{rating}/5</div>
        </div>
        <button class="btn-expand" onclick="toggleDetail(this,'fbdet{fb_id}')">
          <i class="fa-solid fa-chevron-down"></i> View More
        </button>
      </div>
    </div>

    <div class="fb-detail" id="fbdet{fb_id}">
      <div class="section-title"><i class="fa-solid fa-user"></i> Parent Details</div>
      <div class="detail-grid">
        <div class="di"><label>Father Name</label><span>{parent_name}</span></div>
        <div class="di"><label>Email</label><span>{parent_email}</span></div>
        <div class="di"><label>Mobile</label><span>{parent_mob}</span></div>
      </div>

      <div class="section-title"><i class="fa-solid fa-child"></i> Child Details</div>
      <div class="detail-grid">
        <div class="di"><label>Child Name</label><span>{child_name}</span></div>
        <div class="di"><label>Date of Birth</label><span>{child_dob}</span></div>
        <div class="di"><label>Gender</label><span>{child_gender}</span></div>
        <div class="di"><label>Blood Group</label><span>{child_blood}</span></div>
      </div>

      <div class="section-title"><i class="fa-solid fa-syringe"></i> Vaccine Details</div>
      <div class="detail-grid">
        <div class="di"><label>Vaccine Name</label><span>{vaccine}</span></div>
        <div class="di"><label>Min Age</label><span>{min_age}</span></div>
        <div class="di"><label>Dose No.</label><span>{dose}</span></div>
        <div class="di"><label>Appointment Date</label><span>{appt_date}</span></div>
      </div>

      <div class="section-title"><i class="fa-solid fa-comment"></i> Comment</div>
      <div class="comment-box">
        <p>{"<em style='color:#9ca3af;'>No comment provided</em>" if not comment else comment}</p>
      </div>
    </div>
  </div>
""")

print(f"""
</main>
<footer>&copy; 2026 Child Vaccination System &mdash; {hospital_name}</footer>

<script>
function toggleSidebar() {{
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('overlay').classList.toggle('open');
}}

function toggleDetail(btn, detId) {{
  const det = document.getElementById(detId);
  const isOpen = det.classList.contains('open');
  det.classList.toggle('open', !isOpen);
  btn.innerHTML = isOpen
    ? '<i class="fa-solid fa-chevron-down"></i> View More'
    : '<i class="fa-solid fa-chevron-up"></i> View Less';
}}

function filterCards() {{
  const q  = document.getElementById('searchInput').value.toLowerCase();
  const rf = document.getElementById('ratingFilter').value;
  let visible = 0;
  document.querySelectorAll('.fb-card').forEach(card => {{
    const matchQ = !q  || card.dataset.search.includes(q);
    const matchR = !rf || card.dataset.rating === rf;
    const show   = matchQ && matchR;
    card.style.display = show ? '' : 'none';
    if (show) visible++;
  }});
  document.getElementById('cntLbl').textContent = visible + ' record' + (visible !== 1 ? 's' : '');
}}

const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('filter') === 'low') {{
  document.getElementById('ratingFilter').value = 'low';
  filterCards();
}}
</script>
</body>
</html>
""")
con.close()