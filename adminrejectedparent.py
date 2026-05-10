#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
import sys, pymysql
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
print("Content-type:text/html\r\n\r\n")

con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()

def qc(sql):
    cur.execute(sql)
    return cur.fetchone()[0]

total_fb          = qc("SELECT COUNT(*) FROM feedback")
low_fb            = qc("SELECT COUNT(*) FROM feedback WHERE rating < 2")
pending_parents   = qc("SELECT COUNT(*) FROM parent WHERE status='pending'")
approved_parents  = qc("SELECT COUNT(*) FROM parent WHERE status='approved'")
rejected_parents  = qc("SELECT COUNT(*) FROM parent WHERE status='rejected'")
pending_hospitals = qc("SELECT COUNT(*) FROM hospital WHERE status='pending'")
approved_hospitals= qc("SELECT COUNT(*) FROM hospital WHERE status='approved'")
rejected_hospitals= qc("SELECT COUNT(*) FROM hospital WHERE status='rejected'")
total_notified    = qc("SELECT COUNT(*) FROM child_vaccine WHERE status='notified'")
total_children    = qc("SELECT COUNT(*) FROM children")
total_completed   = qc("SELECT COUNT(*) FROM child_vaccine WHERE status='completed'")

cur.execute("SELECT * FROM parent WHERE status='Rejected'")
rows = cur.fetchall()

# Unique states from rejected parents
cur.execute("SELECT DISTINCT state FROM parent WHERE status='Rejected' AND state IS NOT NULL ORDER BY state")
all_states = [r[0] for r in cur.fetchall()]

# State-district pairs for dynamic filtering
cur.execute("SELECT DISTINCT state, district FROM parent WHERE status='Rejected' AND state IS NOT NULL AND district IS NOT NULL ORDER BY state, district")
all_state_districts = cur.fetchall()

cur.execute("""
    SELECT c.child_id, c.child_name, c.dob, c.weight, c.gender,
           c.blood_group, c.identification_mark,
           p.father_name, p.mobile_number, p.state, p.district,
           p.status AS parent_status
    FROM children c
    LEFT JOIN parent p ON c.parent_id = p.parent_id
    ORDER BY c.child_id DESC
""")
children_raw = cur.fetchall()

def nb(n, cls=""):
    return f'<span class="nbadge {cls}">{n}</span>' if n else ""
def sb(n):
    return f'<span class="nbadge" style="margin-left:auto">{n}</span>' if n else ""

tp = (f'<a href="adminpendingparent.py" class="talert pa">'
      f'<i class="fa-solid fa-user-clock"></i>'
      f'<span> {pending_parents} Parent Pending</span></a>') if pending_parents else ""
th_alert = (f'<a href="adminpendingmanager.py" class="talert ho">'
            f'<i class="fa-solid fa-hospital"></i>'
            f'<span> {pending_hospitals} Hospital Pending</span></a>') if pending_hospitals else ""

# Build state options
state_opts = '<option value="">All States</option>'
for s in all_states:
    state_opts += f'<option value="{s.lower()}">{s}</option>'

# Build district options with data-state attribute
district_opts = '<option value="">All Districts</option>'
for sd in all_state_districts:
    s_val = sd[0].lower()
    d_val = sd[1].lower()
    district_opts += f'<option value="{d_val}" data-state="{s_val}">{sd[1]}</option>'

print(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Rejected Parents</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    *,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
    :root{{
      --p:#1565c0;--pd:#0d47a1;--pl:#e3f2fd;--ac:#ff6f00;
      --sw:260px;--hh:60px;--tx:#1c1c1c;--mu:#6b7280;
      --bg:#f0f4f8;--ca:#fff;--bo:#dde3ea;
      --da:#e53935;--dl:#ffebee;--su:#2e7d32;
      --ra:10px;--sh:0 2px 16px rgba(0,0,0,.09);
      --tr:.25s ease;--fn:'Segoe UI',Arial,sans-serif
    }}
    html{{scroll-behavior:smooth}}
    body{{font-family:var(--fn);background:var(--bg);color:var(--tx);min-height:100vh;line-height:1.6}}
    a{{text-decoration:none;color:inherit}}
    .overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1100}}
    .overlay.active{{display:block}}
    .sidebar{{width:var(--sw);height:100vh;position:fixed;top:0;left:0;
      background:linear-gradient(180deg,#0d2a6e 0%,#1565c0 60%,#0d47a1 100%);
      display:flex;flex-direction:column;z-index:1200;
      overflow-y:auto;overflow-x:hidden;transition:transform var(--tr);
      scrollbar-width:thin;scrollbar-color:rgba(255,255,255,.2) transparent}}
    .sidebar::-webkit-scrollbar{{width:4px}}
    .sidebar::-webkit-scrollbar-thumb{{background:rgba(255,255,255,.2);border-radius:2px}}
    .sbrand{{display:flex;align-items:center;gap:12px;padding:18px 16px 14px;border-bottom:1px solid rgba(255,255,255,.15)}}
    .sbrand img{{width:42px;height:42px;border-radius:50%;border:2px solid rgba(255,255,255,.4);flex-shrink:0}}
    .sbrand span{{font-size:.95rem;font-weight:700;color:#fff;line-height:1.3}}
    .sbrand small{{display:block;font-size:.72rem;color:rgba(255,255,255,.6);font-weight:400}}
    .snav{{flex:1;padding:10px 0}}
    .ng{{border-bottom:1px solid rgba(255,255,255,.07)}}
    .ngt{{width:100%;background:transparent;border:none;cursor:pointer;display:flex;align-items:center;gap:10px;padding:13px 16px;color:rgba(255,255,255,.88);font-size:.88rem;font-weight:500;font-family:var(--fn);transition:background var(--tr),color var(--tr);text-align:left}}
    .ngt:hover,.ng.open .ngt{{background:rgba(255,255,255,.1);color:#fff}}
    .ngt .ic{{font-size:.95rem;width:20px;text-align:center;flex-shrink:0}}
    .ngt .ar{{margin-left:auto;font-size:.68rem;transition:transform var(--tr);flex-shrink:0}}
    .ng.open .ngt .ar{{transform:rotate(180deg)}}
    .nsub{{max-height:0;overflow:hidden;transition:max-height .35s ease;background:rgba(0,0,0,.15)}}
    .ng.open .nsub{{max-height:400px}}
    .nsub a{{display:flex;align-items:center;gap:8px;padding:9px 16px 9px 48px;color:rgba(255,255,255,.72);font-size:.83rem;transition:background var(--tr),color var(--tr);border-left:3px solid transparent;cursor:pointer}}
    .nsub a:hover,.nsub a.active{{background:rgba(255,255,255,.1);color:#fff;border-left-color:var(--ac)}}
    .nbadge{{background:#e53935;color:#fff;font-size:.67rem;font-weight:700;min-width:18px;height:18px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;padding:0 5px}}
    .nbadge.or{{background:var(--ac)}}.nbadge.gr{{background:#2e7d32}}.nbadge.gy{{background:#777}}
    .sfooter{{padding:14px 12px;border-top:1px solid rgba(255,255,255,.12)}}
    .btn-logout{{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:10px;background:var(--da);color:#fff;border:none;border-radius:var(--ra);font-size:.88rem;font-weight:600;font-family:var(--fn);cursor:pointer;text-decoration:none;transition:background var(--tr)}}
    .btn-logout:hover{{background:#b71c1c}}
    .mwrap{{margin-left:var(--sw);display:flex;flex-direction:column;min-height:100vh}}
    .topbar{{height:var(--hh);background:var(--ca);border-bottom:1px solid var(--bo);position:sticky;top:0;z-index:900;display:flex;align-items:center;justify-content:space-between;padding:0 20px;box-shadow:0 1px 8px rgba(0,0,0,.06)}}
    .tbl{{display:flex;align-items:center;gap:12px}}
    .ttitle{{font-size:1rem;font-weight:700;color:var(--p)}}
    .tbcrumb{{font-size:.8rem;color:var(--mu)}}
    .tbcrumb a{{color:var(--p)}}
    .hamburger{{display:none;flex-direction:column;gap:5px;background:transparent;border:none;cursor:pointer;padding:6px;border-radius:6px}}
    .hamburger span{{display:block;width:22px;height:2px;background:var(--tx);border-radius:2px;transition:transform var(--tr),opacity var(--tr)}}
    .hamburger.open span:nth-child(1){{transform:translateY(7px) rotate(45deg)}}
    .hamburger.open span:nth-child(2){{opacity:0}}
    .hamburger.open span:nth-child(3){{transform:translateY(-7px) rotate(-45deg)}}
    .tbr{{display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
    .abadge{{background:var(--pl);color:var(--p);padding:5px 14px;border-radius:20px;font-size:.82rem;font-weight:600}}
    .talert{{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:20px;font-size:.78rem;font-weight:700}}
    .talert.pa{{background:#fff3e0;color:#e65100}}
    .talert.ho{{background:#e8f5e9;color:#2e7d32}}
    .pc{{padding:24px 20px;flex:1}}
    .section{{display:none}}.section.active{{display:block}}
    .page-hdr-red{{background:linear-gradient(120deg,var(--da),#c62828);color:#fff;border-radius:var(--ra);padding:22px 28px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}}
    .page-hdr-red h2{{font-size:1.1rem;font-weight:700;margin-bottom:3px}}
    .page-hdr-red p{{font-size:.83rem;opacity:.8}}
    .page-hdr-badge{{background:rgba(255,255,255,.18);padding:7px 16px;border-radius:20px;font-size:.83rem;font-weight:700;white-space:nowrap}}
    .info-banner{{display:flex;align-items:center;gap:12px;background:var(--dl);border:1px solid #ef9a9a;border-radius:var(--ra);padding:12px 18px;margin-bottom:18px;font-size:.88rem;color:var(--da)}}
    .info-banner i{{font-size:1.1rem;flex-shrink:0}}
    .filter-bar{{display:flex;align-items:center;gap:10px;margin-bottom:16px;flex-wrap:wrap;background:var(--ca);border:1px solid var(--bo);border-radius:var(--ra);padding:12px 16px;box-shadow:0 1px 6px rgba(0,0,0,.05)}}
    .filter-bar label{{font-size:.78rem;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:.4px;white-space:nowrap}}
    .sbox{{position:relative;flex:1;min-width:160px}}
    .sbox i{{position:absolute;left:11px;top:50%;transform:translateY(-50%);color:var(--mu);font-size:.82rem}}
    .sbox input{{width:100%;padding:9px 12px 9px 34px;border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.85rem;background:var(--ca);transition:border-color var(--tr)}}
    .sbox input:focus{{outline:none;border-color:var(--da)}}
    .fsel{{padding:8px 12px;border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.86rem;background:var(--ca);color:var(--tx);cursor:pointer;min-width:140px}}
    .fsel:focus{{outline:none;border-color:var(--da)}}
    .btn-clear{{padding:8px 14px;background:var(--da);color:#fff;border:none;border-radius:8px;font-size:.82rem;font-weight:600;font-family:var(--fn);cursor:pointer;white-space:nowrap}}
    .btn-clear:hover{{background:#c62828}}
    .cnt-lbl{{font-size:.83rem;color:var(--mu);font-weight:600;white-space:nowrap;margin-left:auto}}
    .tcard{{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);overflow:hidden}}
    .tcard-head{{background:linear-gradient(90deg,var(--da),#c62828);color:#fff;padding:14px 20px;display:flex;align-items:center;gap:10px;font-size:.95rem;font-weight:700}}
    .tw{{width:100%;overflow-x:auto}}
    table{{width:100%;border-collapse:collapse;min-width:650px}}
    thead{{background:#263238;color:#fff}}
    th{{padding:12px 14px;text-align:left;font-size:.82rem;font-weight:600;text-transform:uppercase;letter-spacing:.4px;white-space:nowrap}}
    td{{padding:12px 14px;font-size:.88rem;border-bottom:1px solid var(--bo);white-space:nowrap;vertical-align:middle}}
    tbody tr:hover{{background:#fff5f5}}
    tbody tr:last-child td{{border-bottom:none}}
    .snum{{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;background:var(--dl);color:var(--da);border-radius:50%;font-size:.78rem;font-weight:700}}
    .badge-rej{{display:inline-flex;align-items:center;gap:5px;padding:4px 12px;background:var(--dl);color:var(--da);border-radius:20px;font-size:.78rem;font-weight:700}}
    .empty-state{{text-align:center;padding:56px 20px;color:var(--mu)}}
    .empty-state i{{font-size:3rem;margin-bottom:14px;color:var(--bo);display:block}}
    .empty-state h3{{font-size:1rem;font-weight:700;margin-bottom:6px}}
    .page-hdr-blue{{background:linear-gradient(120deg,var(--p),var(--pd));color:#fff;border-radius:var(--ra);padding:22px 28px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}}
    .page-hdr-blue h2{{font-size:1.1rem;font-weight:700;margin-bottom:3px}}
    .page-hdr-blue p{{font-size:.83rem;opacity:.8}}
    .child-card{{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);margin-bottom:16px;overflow:hidden}}
    .ccard-top{{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;flex-wrap:wrap;gap:10px}}
    .ccard-left{{display:flex;align-items:center;gap:14px}}
    .avatar-blue{{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--p),var(--pd));border:2px solid var(--pl);display:flex;align-items:center;justify-content:center;font-size:1.15rem;font-weight:800;color:#fff;flex-shrink:0}}
    .ccard-name{{font-size:.96rem;font-weight:700;color:var(--tx)}}
    .ccard-sub{{font-size:.76rem;color:var(--mu);margin-top:2px}}
    .ccard-right{{display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
    .btn-viewmore{{display:inline-flex;align-items:center;gap:6px;padding:7px 16px;background:var(--p);color:#fff;border:none;border-radius:8px;font-size:.82rem;font-weight:600;font-family:var(--fn);cursor:pointer;transition:background var(--tr)}}
    .btn-viewmore:hover{{background:var(--pd)}}
    .ccard-details{{display:none;border-top:1px solid var(--bo)}}
    .ccard-details.open{{display:block}}
    .dpanel{{padding:18px 20px}}
    .dg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px 20px}}
    .di{{background:var(--bg);border:1px solid var(--bo);border-radius:8px;padding:9px 13px}}
    .di label{{display:block;font-size:.67rem;color:var(--mu);font-weight:700;text-transform:uppercase;letter-spacing:.4px;margin-bottom:3px}}
    .di span{{font-size:.86rem;font-weight:600;color:var(--tx);word-break:break-word}}
    .di.full{{grid-column:1/-1}}
    .bx{{display:inline-flex;align-items:center;padding:3px 10px;border-radius:20px;font-size:.74rem;font-weight:700}}
    .bp{{background:#fff8e1;color:#f57f17}}.ba{{background:#e8f5e9;color:#2e7d32}}
    .br{{background:#ffebee;color:#c62828}}.bgy{{background:#f3f4f6;color:#555}}
    .vm-icon{{transition:transform var(--tr)}}
    .empty{{text-align:center;padding:60px 20px;color:var(--mu)}}
    .empty i{{font-size:3rem;opacity:.3;display:block;margin-bottom:14px}}
    footer{{background:#1c1c2e;color:rgba(255,255,255,.6);text-align:center;padding:14px 20px;font-size:.8rem}}
    @media(max-width:768px){{
      .sidebar{{transform:translateX(-100%)}}.sidebar.open{{transform:translateX(0)}}
      .mwrap{{margin-left:0}}.hamburger{{display:flex}}.abadge{{display:none}}
      .filter-bar{{flex-direction:column;align-items:stretch}}
      .fsel,.sbox{{width:100%;min-width:unset}}
      th,td{{padding:10px;font-size:.82rem}}
    }}
    @media(max-width:480px){{.talert span{{display:none}}.pc{{padding:14px 12px}}}}
  </style>
</head>
<body>
<div class="overlay" id="overlay"></div>
<aside class="sidebar" id="sidebar">
  <div class="sbrand">
    <img src="./images/logo.jpg" alt="logo" onerror="this.style.display='none'">
    <span>Child Vaccination<small>Admin Panel</small></span>
  </div>
  <nav class="snav">
    <div class="ng open" id="g1">
      <button class="ngt" onclick="tg('g1')">
        <i class="fa-solid fa-user-group ic"></i> Parents {nb(pending_parents)}
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a href="adminpendingparent.py"><i class="fa-solid fa-clock"></i> Pending {sb(pending_parents)}</a>
        <a href="adminapprovedparent.py"><i class="fa-solid fa-check"></i> Approved {nb(approved_parents,"gr")}</a>
        <a href="adminrejectedparent.py" class="active" id="link-rejected"><i class="fa-solid fa-xmark"></i> Rejected {nb(rejected_parents,"gy")}</a>
      </div>
    </div>
    <div class="ng" id="g2">
      <button class="ngt" onclick="tg('g2')">
        <i class="fa-solid fa-hospital ic"></i> Hospital {nb(pending_hospitals,"or")}
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a href="adminpendingmanager.py"><i class="fa-solid fa-clock"></i> Pending Manager {sb(pending_hospitals)}</a>
        <a href="adminapprovedmanager.py"><i class="fa-solid fa-check"></i> Approved Manager {nb(approved_hospitals,"gr")}</a>
        <a href="adminrejectedmanager.py"><i class="fa-solid fa-xmark"></i> Rejected Manager {nb(rejected_hospitals,"gy")}</a>
      </div>
    </div>
    <div class="ng" id="g3">
      <button class="ngt" onclick="tg('g3')">
        <i class="fa-solid fa-syringe ic"></i> Vaccinations
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a href="adminaddvaccine.py"><i class="fa-solid fa-plus"></i> Add Vaccine</a>
        <a href="adminviewvaccine.py"><i class="fa-solid fa-eye"></i> View Vaccine</a>
        <a href="admindeletedvaccine.py"><i class="fa-solid fa-trash"></i> Deleted Vaccine</a>
      </div>
    </div>
    <div class="ng" id="g4">
      <button class="ngt" onclick="tg('g4')">
        <i class="fa-solid fa-bell ic"></i> Notification {nb(total_notified,"or")}
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a href="adminnotification.py"><i class="fa-solid fa-paper-plane"></i> Notify {sb(total_notified)}</a>
        <a href="adminnotifiedchild.py"><i class="fa-solid fa-child"></i> Notified Child</a>
        <a href="admincompletedvaccine.py"><i class="fa-solid fa-circle-check"></i> Completed {nb(total_completed,"gr")}</a>
      </div>
    </div>
    <div class="ng" id="g5">
      <button class="ngt" onclick="tg('g5')">
        <i class="fa-solid fa-children ic"></i> Children {nb(total_children,"gr")}
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a onclick="showSection('sec-children')" id="link-children">
          <i class="fa-solid fa-child"></i> Child Details {sb(total_children)}
        </a>
      </div>
    </div>
    <div class="ng" id="g6">
      <button class="ngt" onclick="tg('g6')">
        <i class="fa-solid fa-star ic"></i> Feedback {nb(low_fb) if low_fb else ""}
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a href="adminparentfeedback.py"><i class="fa-solid fa-list"></i> All Feedback {sb(total_fb)}</a>
        <a href="adminlowratings.py"><i class="fa-solid fa-triangle-exclamation"></i> Low Ratings {nb(low_fb) if low_fb else ""}</a>
      </div>
    </div>
  </nav>
  <div class="sfooter">
    <a href="home.py" class="btn-logout"><i class="fa-solid fa-right-from-bracket"></i> Logout</a>
  </div>
</aside>

<div class="mwrap">
  <header class="topbar">
    <div class="tbl">
      <button class="hamburger" id="hamburger"><span></span><span></span><span></span></button>
      <div>
        <div class="ttitle" id="page-title">Rejected Parents</div>
        <div class="tbcrumb"><a href="admindashboard.py">Dashboard</a> &rsaquo; Parents &rsaquo; Rejected</div>
      </div>
    </div>
    <div class="tbr">
      {tp}{th_alert}
      <span class="abadge"><i class="fa-solid fa-shield-halved"></i> Admin</span>
    </div>
  </header>
  <main class="pc">
""")

print(f"""
<div class="section active" id="sec-rejected">
  <div class="page-hdr-red">
    <div>
      <h2><i class="fa-solid fa-user-xmark"></i>&nbsp; Rejected Parents</h2>
      <p>Filter by state and district to find specific rejected parents.</p>
    </div>
    <span class="page-hdr-badge" id="cntBadge"><i class="fa-solid fa-ban"></i> {len(rows)} Rejected</span>
  </div>
  <div class="info-banner">
    <i class="fa-solid fa-triangle-exclamation"></i>
    <span>These parent registrations were <strong>rejected</strong>. Go to
      <a href="adminpendingparent.py" style="color:var(--da);font-weight:700;">Pending Parents</a>
      to review new applications.</span>
  </div>

  <div class="filter-bar">
    <label><i class="fa-solid fa-filter"></i> Filter</label>
    <div class="sbox">
      <i class="fa-solid fa-magnifying-glass"></i>
      <input type="text" id="searchInput" placeholder="Search name, email, mobile..." oninput="filterTable()">
    </div>
    <select class="fsel" id="stateFilter" onchange="updateDistricts('stateFilter','districtFilter'); filterTable()">
      {state_opts}
    </select>
    <select class="fsel" id="districtFilter" onchange="filterTable()">
      {district_opts}
    </select>
    <button class="btn-clear" onclick="clearFilters()"><i class="fa-solid fa-xmark"></i> Clear</button>
    <span class="cnt-lbl" id="cntLbl">{len(rows)} records</span>
  </div>

  <div class="tcard">
    <div class="tcard-head"><i class="fa-solid fa-user-xmark"></i> Rejected Parent List</div>
    <div class="tw">
      <table id="mainTable">
        <thead>
          <tr>
            <th>#</th>
            <th><i class="fa-solid fa-user"></i> Father Name</th>
            <th><i class="fa-solid fa-envelope"></i> Email</th>
            <th><i class="fa-solid fa-phone"></i> Mobile</th>
            <th><i class="fa-solid fa-location-dot"></i> State</th>
            <th><i class="fa-solid fa-map-pin"></i> District</th>
            <th><i class="fa-solid fa-id-badge"></i> Username</th>
            <th><i class="fa-solid fa-lock"></i> Password</th>
            <th><i class="fa-solid fa-circle-xmark"></i> Status</th>
          </tr>
        </thead>
        <tbody id="tableBody">
""")

if rows:
    for idx, row in enumerate(rows, start=1):
        father_name = row[1]  if len(row) > 1  else "—"
        email       = row[6]  if len(row) > 6  else "—"
        mobile      = row[7]  if len(row) > 7  else "—"
        state_v     = row[9]  if len(row) > 9  else "—"
        district_v  = row[10] if len(row) > 10 else "—"
        username    = row[15] if len(row) > 15 and row[15] else "—"
        password    = row[16] if len(row) > 16 and row[16] else "—"
        print(f"""
          <tr data-state="{str(state_v).lower()}" data-district="{str(district_v).lower()}">
            <td><span class="snum">{idx}</span></td>
            <td><strong>{father_name}</strong></td>
            <td>{email}</td>
            <td>{mobile}</td>
            <td>{state_v}</td>
            <td>{district_v}</td>
            <td>{username}</td>
            <td>{password}</td>
            <td><span class="badge-rej"><i class="fa-solid fa-ban"></i> Rejected</span></td>
          </tr>
""")
else:
    print("""
          <tr><td colspan="9">
            <div class="empty-state">
              <i class="fa-solid fa-user-slash"></i>
              <h3>No Rejected Parents</h3>
              <p>No parent registrations have been rejected yet.</p>
            </div>
          </td></tr>
""")

print("""
        </tbody>
      </table>
    </div>
  </div>
</div><!-- /sec-rejected -->
""")

print(f"""
<div class="section" id="sec-children">
  <div class="page-hdr-blue">
    <div>
      <h2><i class="fa-solid fa-children"></i>&nbsp; Registered Children</h2>
      <p>Click <strong>View More</strong> on any child to see their details</p>
    </div>
    <span class="page-hdr-badge"><i class="fa-solid fa-child"></i> {total_children} Total</span>
  </div>
  <div class="filter-bar">
    <div class="sbox">
      <i class="fa-solid fa-magnifying-glass"></i>
      <input type="text" id="childSearch" placeholder="Search child name, father, mobile..." oninput="filterChildCards()">
    </div>
    <select class="fsel" id="genderFilter" onchange="filterChildCards()">
      <option value="">All Genders</option>
      <option value="male">Male</option>
      <option value="female">Female</option>
    </select>
    <span class="cnt-lbl" id="cntLbl2">{len(children_raw)} records</span>
  </div>
""")

if not children_raw:
    print('<div class="empty"><i class="fa-solid fa-child-reaching"></i><p>No registered children found.</p></div>')
else:
    for r in children_raw:
        cid=r[0]; cname=r[1] or "—"; dob=r[2] or "—"; weight=r[3] or "—"
        gender=r[4] or "—"; blood=r[5] or "—"; idmark=r[6] or "—"
        father=r[7] or "—"; mobile=r[8] or "—"; state=r[9] or "—"
        district=r[10] or "—"; pstatus=r[11] or "pending"
        pbc={"approved":"ba","rejected":"br","pending":"bp"}.get(pstatus,"bp")
        gicon="fa-mars" if str(r[4]).lower()=="male" else ("fa-venus" if str(r[4]).lower()=="female" else "fa-genderless")
        initial=str(r[1])[0].upper() if r[1] else "?"

        print(f"""
  <div class="child-card"
       data-name="{str(r[1]).lower()}"
       data-father="{str(r[7] or '').lower()}"
       data-mobile="{mobile}"
       data-blood="{str(r[5] or '').lower()}"
       data-gender="{str(r[4] or '').lower()}">
    <div class="ccard-top">
      <div class="ccard-left">
        <div class="avatar-blue">{initial}</div>
        <div>
          <div class="ccard-name"><i class="fa-solid {gicon}" style="font-size:.85rem;opacity:.7"></i>&nbsp;{cname}</div>
          <div class="ccard-sub">DOB: {dob} &bull; Blood: {blood} &bull; {weight} kg &bull; {gender}</div>
        </div>
      </div>
      <div class="ccard-right">
        <span class="bx {pbc}">Parent: {pstatus.capitalize()}</span>
        <button class="btn-viewmore" onclick="toggleCDetails(this,'cdet{cid}')">
          <i class="fa-solid fa-chevron-down vm-icon"></i> View More
        </button>
      </div>
    </div>
    <div class="ccard-details" id="cdet{cid}">
      <div class="dpanel">
        <div class="dg">
          <div class="di"><label>Child Name</label><span>{cname}</span></div>
          <div class="di"><label>Date of Birth</label><span>{dob}</span></div>
          <div class="di"><label>Gender</label><span>{gender}</span></div>
          <div class="di"><label>Blood Group</label><span>{blood}</span></div>
          <div class="di"><label>Weight</label><span>{weight} kg</span></div>
          <div class="di"><label>ID Mark</label><span>{idmark}</span></div>
          <div class="di"><label>Father Name</label><span>{father}</span></div>
          <div class="di"><label>Mobile</label><span>{mobile}</span></div>
          <div class="di"><label>State</label><span>{state}</span></div>
          <div class="di"><label>District</label><span>{district}</span></div>
          <div class="di"><label>Parent Status</label><span><span class="bx {pbc}">{pstatus.capitalize()}</span></span></div>
        </div>
      </div>
    </div>
  </div>
""")

print("""
</div><!-- /sec-children -->
  </main>
  <footer>&copy; 2026 Child Vaccination System &mdash; Admin Panel</footer>
</div>

<script>
const hamburger=document.getElementById('hamburger');
const sidebar=document.getElementById('sidebar');
const overlay=document.getElementById('overlay');
function closeSB(){sidebar.classList.remove('open');hamburger.classList.remove('open');overlay.classList.remove('active');document.body.style.overflow='';}
hamburger.addEventListener('click',()=>{const o=sidebar.classList.toggle('open');hamburger.classList.toggle('open',o);overlay.classList.toggle('active',o);document.body.style.overflow=o?'hidden':'';});
overlay.addEventListener('click',closeSB);
window.addEventListener('resize',()=>{if(window.innerWidth>768)closeSB();});
function tg(id){const g=document.getElementById(id),o=g.classList.contains('open');document.querySelectorAll('.ng').forEach(x=>x.classList.remove('open'));if(!o)g.classList.add('open');}
function showSection(id){
  document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.querySelectorAll('.nsub a').forEach(a=>a.classList.remove('active'));
  if(id==='sec-children'){
    document.getElementById('link-children').classList.add('active');
    document.querySelectorAll('.ng').forEach(x=>x.classList.remove('open'));
    document.getElementById('g5').classList.add('open');
  }
  window.scrollTo(0,0); closeSB();
}

/* ── Dynamic district filter ── */
function updateDistricts(stateSelId, distSelId) {
  const st = document.getElementById(stateSelId).value.toLowerCase();
  const distSel = document.getElementById(distSelId);
  Array.from(distSel.options).forEach(opt => {
    if (!opt.value) return;
    opt.style.display = (!st || opt.dataset.state === st) ? '' : 'none';
  });
  const cur = distSel.options[distSel.selectedIndex];
  if (cur && cur.value && cur.style.display === 'none') distSel.value = '';
}

function filterTable(){
  const q  = document.getElementById('searchInput').value.toLowerCase();
  const st = document.getElementById('stateFilter').value.toLowerCase();
  const di = document.getElementById('districtFilter').value.toLowerCase();
  let visible=0;
  document.querySelectorAll('#tableBody tr').forEach(row=>{
    const matchQ  = !q  || row.textContent.toLowerCase().includes(q);
    const matchSt = !st || (row.dataset.state||'')===st;
    const matchDi = !di || (row.dataset.district||'')===di;
    const show=matchQ&&matchSt&&matchDi;
    row.style.display=show?'':'none';
    if(show)visible++;
  });
  document.getElementById('cntLbl').textContent=visible+' record'+(visible!==1?'s':'');
  document.getElementById('cntBadge').innerHTML='<i class="fa-solid fa-ban"></i> '+visible+' Rejected';
}
function clearFilters(){
  document.getElementById('searchInput').value='';
  document.getElementById('stateFilter').value='';
  updateDistricts('stateFilter','districtFilter');
  document.getElementById('districtFilter').value='';
  filterTable();
}

function toggleCDetails(btn,detId){
  const det=document.getElementById(detId);
  const isOpen=det.classList.contains('open');
  det.classList.toggle('open',!isOpen);
  btn.innerHTML=isOpen?'<i class="fa-solid fa-chevron-down vm-icon"></i> View More':'<i class="fa-solid fa-chevron-up vm-icon"></i> View Less';
}
function filterChildCards(){
  const q=document.getElementById('childSearch').value.toLowerCase();
  const gf=document.getElementById('genderFilter').value.toLowerCase();
  let visible=0;
  document.querySelectorAll('.child-card').forEach(c=>{
    const matchQ=!q||c.dataset.name.includes(q)||c.dataset.father.includes(q)||c.dataset.mobile.includes(q)||c.dataset.blood.includes(q);
    const matchG=!gf||c.dataset.gender===gf;
    const show=matchQ&&matchG;
    c.style.display=show?'':'none';
    if(show)visible++;
  });
  document.getElementById('cntLbl2').textContent=visible+' record'+(visible!==1?'s':'');
}
</script>
</body>
</html>
""")

con.close()