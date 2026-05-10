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
total_completed   = qc("SELECT COUNT(*) FROM child_vaccine WHERE status='completed'")
total_children    = qc("SELECT COUNT(*) FROM children")

cur.execute("SELECT * FROM hospital WHERE status='Rejected'")
rows = cur.fetchall()

# Unique states from rejected hospitals
cur.execute("SELECT DISTINCT state FROM hospital WHERE status='Rejected' AND state IS NOT NULL ORDER BY state")
all_states = [r[0] for r in cur.fetchall()]

# State-district pairs for dynamic filtering
cur.execute("SELECT DISTINCT state, district FROM hospital WHERE status='Rejected' AND state IS NOT NULL AND district IS NOT NULL ORDER BY state, district")
all_state_districts = cur.fetchall()

cur.execute("""
    SELECT c.child_id, c.child_name, c.dob, c.weight, c.gender,
           c.blood_group, c.identification_mark,
           p.father_name, p.mother_name, p.email,
           p.mobile_number, p.state, p.district, p.address, p.occupation,
           p.status AS parent_status
    FROM children c
    LEFT JOIN parent p ON c.parent_id = p.parent_id
    ORDER BY c.child_id DESC
""")
children_raw = cur.fetchall()

cur.execute("""
    SELECT cv.child_id, v.vaccine_name, v.minimum_age, cv.status, cv.taken_date
    FROM child_vaccine cv
    LEFT JOIN vaccine v ON cv.vaccine_id = v.vaccine_id
    ORDER BY v.minimum_age ASC
""")
vax_by_child = defaultdict(list)
for r in cur.fetchall():
    vax_by_child[r[0]].append({"name": r[1], "age": r[2], "status": r[3], "date": r[4]})

hosp_by_child = {}
try:
    cur.execute("""
        SELECT a.child_id, h.hospital_name, h.hospital_number, h.state, h.district
        FROM appointments a
        LEFT JOIN hospital h ON a.hospital_id = h.hospital_id
        WHERE h.hospital_id IS NOT NULL
    """)
    for r in cur.fetchall():
        hosp_by_child[r[0]] = {"name": r[1], "number": r[2], "state": r[3], "district": r[4]}
except Exception:
    pass

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
  <title>Rejected Hospital Managers</title>
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
    .hosp-card{{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);margin-bottom:16px;overflow:hidden}}
    .hcard-top{{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;flex-wrap:wrap;gap:10px}}
    .hcard-left{{display:flex;align-items:center;gap:14px}}
    .avatar-red{{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--da),#c62828);border:2px solid var(--dl);display:flex;align-items:center;justify-content:center;font-size:1.15rem;font-weight:800;color:#fff;flex-shrink:0}}
    .avatar-blue{{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--p),var(--pd));border:2px solid var(--pl);display:flex;align-items:center;justify-content:center;font-size:1.15rem;font-weight:800;color:#fff;flex-shrink:0}}
    .hcard-name{{font-size:.96rem;font-weight:700;color:var(--tx)}}
    .hcard-sub{{font-size:.76rem;color:var(--mu);margin-top:2px}}
    .hcard-right{{display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
    .badge-rej{{display:inline-flex;align-items:center;gap:5px;padding:4px 12px;background:var(--dl);color:var(--da);border-radius:20px;font-size:.78rem;font-weight:700}}
    .btn-viewmore-red{{display:inline-flex;align-items:center;gap:6px;padding:7px 16px;background:var(--da);color:#fff;border:none;border-radius:8px;font-size:.82rem;font-weight:600;font-family:var(--fn);cursor:pointer;transition:background var(--tr)}}
    .btn-viewmore-red:hover{{background:#c62828}}
    .btn-viewmore-blue{{display:inline-flex;align-items:center;gap:6px;padding:7px 16px;background:var(--p);color:#fff;border:none;border-radius:8px;font-size:.82rem;font-weight:600;font-family:var(--fn);cursor:pointer;transition:background var(--tr)}}
    .btn-viewmore-blue:hover{{background:var(--pd)}}
    .vm-icon{{transition:transform var(--tr)}}
    .hcard-details{{display:none;border-top:1px solid var(--bo)}}
    .hcard-details.open{{display:block}}
    .detail-tabs{{display:flex;border-bottom:2px solid var(--bo);background:#fafbfc;overflow-x:auto}}
    .dtab-red{{flex:1;background:transparent;border:none;border-bottom:3px solid transparent;margin-bottom:-2px;padding:11px 10px;font-family:var(--fn);font-size:.83rem;font-weight:600;color:var(--mu);cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;transition:color var(--tr),border-color var(--tr),background var(--tr);white-space:nowrap}}
    .dtab-red:hover{{color:var(--da);background:var(--dl)}}
    .dtab-red.active{{color:var(--da);border-bottom-color:var(--ac);background:#fff5f5}}
    .dtab-blue{{flex:1;background:transparent;border:none;border-bottom:3px solid transparent;margin-bottom:-2px;padding:11px 10px;font-family:var(--fn);font-size:.83rem;font-weight:600;color:var(--mu);cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;transition:color var(--tr),border-color var(--tr),background var(--tr);white-space:nowrap}}
    .dtab-blue:hover{{color:var(--p);background:var(--pl)}}
    .dtab-blue.active{{color:var(--p);border-bottom-color:var(--ac);background:#f0f7ff}}
    .dpanel{{display:none;padding:18px 20px}}
    .dpanel.active{{display:block}}
    .dg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px 20px;margin-bottom:4px}}
    .di{{background:var(--bg);border:1px solid var(--bo);border-radius:8px;padding:9px 13px}}
    .di label{{display:block;font-size:.67rem;color:var(--mu);font-weight:700;text-transform:uppercase;letter-spacing:.4px;margin-bottom:3px}}
    .di span{{font-size:.86rem;font-weight:600;color:var(--tx);word-break:break-word}}
    .di.full{{grid-column:1/-1}}
    .pwd-reveal{{background:none;border:1px solid var(--bo);border-radius:6px;padding:4px 10px;font-size:.78rem;color:var(--mu);cursor:pointer;margin-top:6px;font-family:var(--fn)}}
    .pwd-reveal:hover{{background:var(--dl);color:var(--da)}}
    .empty-state{{text-align:center;padding:56px 20px;color:var(--mu)}}
    .empty-state i{{font-size:3rem;margin-bottom:14px;color:var(--bo);display:block}}
    .empty-state h3{{font-size:1rem;font-weight:700;margin-bottom:6px}}
    .page-hdr-blue{{background:linear-gradient(120deg,var(--p),var(--pd));color:#fff;border-radius:var(--ra);padding:22px 28px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}}
    .page-hdr-blue h2{{font-size:1.1rem;font-weight:700;margin-bottom:3px}}
    .page-hdr-blue p{{font-size:.83rem;opacity:.8}}
    .child-card{{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);margin-bottom:16px;overflow:hidden}}
    .ccard-top{{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;flex-wrap:wrap;gap:10px}}
    .ccard-left{{display:flex;align-items:center;gap:14px}}
    .ccard-name{{font-size:.96rem;font-weight:700;color:var(--tx)}}
    .ccard-sub{{font-size:.76rem;color:var(--mu);margin-top:2px}}
    .ccard-right{{display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
    .ccard-details{{display:none;border-top:1px solid var(--bo)}}
    .ccard-details.open{{display:block}}
    .bx{{display:inline-flex;align-items:center;padding:3px 10px;border-radius:20px;font-size:.74rem;font-weight:700}}
    .bp{{background:#fff8e1;color:#f57f17}}.ba{{background:#e8f5e9;color:#2e7d32}}
    .br{{background:#ffebee;color:#c62828}}.bn{{background:#fff3e0;color:#e65100}}
    .bt{{background:#e8f5e9;color:#2e7d32}}.bgy{{background:#f3f4f6;color:#555}}
    .vsumbadges{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}}
    .vsb{{display:flex;align-items:center;gap:5px;padding:5px 14px;border-radius:20px;font-size:.76rem;font-weight:700}}
    .vsb.tk{{background:#e8f5e9;color:#2e7d32}}.vsb.nt{{background:#fff3e0;color:#e65100}}.vsb.pd{{background:#fff8e1;color:#f57f17}}
    .vtable{{width:100%;border-collapse:collapse;font-size:.83rem}}
    .vtable th{{background:#f0f4f8;color:var(--p);padding:8px 12px;text-align:left;font-size:.74rem;font-weight:700;text-transform:uppercase;border-bottom:2px solid var(--bo)}}
    .vtable td{{padding:8px 12px;border-bottom:1px solid var(--bo)}}
    .vtable tbody tr:hover{{background:var(--pl)}}
    .vtable tbody tr:last-child td{{border-bottom:none}}
    .empty{{text-align:center;padding:60px 20px;color:var(--mu)}}
    .empty i{{font-size:3rem;opacity:.3;display:block;margin-bottom:14px}}
    footer{{background:#1c1c2e;color:rgba(255,255,255,.6);text-align:center;padding:14px 20px;font-size:.8rem}}
    @media(max-width:768px){{
      .sidebar{{transform:translateX(-100%)}}.sidebar.open{{transform:translateX(0)}}
      .mwrap{{margin-left:0}}.hamburger{{display:flex}}.abadge{{display:none}}
      .filter-bar{{flex-direction:column;align-items:stretch}}
      .fsel,.sbox{{width:100%;min-width:unset}}
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
    <div class="ng" id="g1">
      <button class="ngt" onclick="tg('g1')">
        <i class="fa-solid fa-user-group ic"></i> Parents {nb(pending_parents)}
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a href="adminpendingparent.py"><i class="fa-solid fa-clock"></i> Pending {sb(pending_parents)}</a>
        <a href="adminapprovedparent.py"><i class="fa-solid fa-check"></i> Approved {nb(approved_parents,"gr")}</a>
        <a href="adminrejectedparent.py"><i class="fa-solid fa-xmark"></i> Rejected {nb(rejected_parents,"gy")}</a>
      </div>
    </div>
    <div class="ng open" id="g2">
      <button class="ngt" onclick="tg('g2')">
        <i class="fa-solid fa-hospital ic"></i> Hospital {nb(pending_hospitals,"or")}
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a href="adminpendingmanager.py"><i class="fa-solid fa-clock"></i> Pending Manager {sb(pending_hospitals)}</a>
        <a href="adminapprovedmanager.py"><i class="fa-solid fa-check"></i> Approved Manager {nb(approved_hospitals,"gr")}</a>
        <a href="adminrejectedmanager.py" class="active" id="link-rejected"><i class="fa-solid fa-xmark"></i> Rejected Manager {nb(rejected_hospitals,"gy")}</a>
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
        <div class="ttitle" id="page-title">Rejected Hospital Managers</div>
        <div class="tbcrumb"><a href="admindashboard.py">Dashboard</a> &rsaquo; Hospital &rsaquo; Rejected</div>
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
      <h2><i class="fa-solid fa-hospital-user"></i>&nbsp; Rejected Hospital Managers</h2>
      <p>Filter by state and district to find specific rejected hospitals.</p>
    </div>
    <span class="page-hdr-badge" id="cntBadge"><i class="fa-solid fa-ban"></i> {len(rows)} Rejected</span>
  </div>
  <div class="info-banner">
    <i class="fa-solid fa-triangle-exclamation"></i>
    <span>These registrations were <strong>rejected</strong>. Go to
      <a href="adminpendingmanager.py" style="color:var(--da);font-weight:700;">Pending Hospitals</a>
      to review new applications.</span>
  </div>

  <div class="filter-bar">
    <label><i class="fa-solid fa-filter"></i> Filter</label>
    <div class="sbox">
      <i class="fa-solid fa-magnifying-glass"></i>
      <input type="text" id="searchInput" placeholder="Search hospital, owner, email..." oninput="filterCards()">
    </div>
    <select class="fsel" id="stateFilter" onchange="updateDistricts('stateFilter','districtFilter'); filterCards()">
      {state_opts}
    </select>
    <select class="fsel" id="districtFilter" onchange="filterCards()">
      {district_opts}
    </select>
    <button class="btn-clear" onclick="clearFilters()"><i class="fa-solid fa-xmark"></i> Clear</button>
    <span class="cnt-lbl" id="cntLbl">{len(rows)} records</span>
  </div>
""")

if rows:
    for idx, row in enumerate(rows, start=1):
        rid      = row[0]
        hname    = row[1]  if len(row) > 1  else "—"
        state_v  = row[2]  if len(row) > 2  else "—"
        district_v = row[3] if len(row) > 3 else "—"
        owner    = row[10] if len(row) > 10 else "—"
        email    = row[14] if len(row) > 14 else "—"
        phone    = row[6]  if len(row) > 6  else "—"
        address  = row[4]  if len(row) > 4  else "—"
        username = row[15] if len(row) > 15 and row[15] else "—"
        password = row[16] if len(row) > 16 and row[16] else "—"
        hnum     = row[6]  if len(row) > 6  else "—"
        initial  = str(hname)[0].upper() if hname and hname != "—" else "H"

        print(f"""
  <div class="hosp-card"
       data-name="{str(hname).lower()}"
       data-owner="{str(owner).lower()}"
       data-email="{str(email).lower()}"
       data-phone="{str(phone).lower()}"
       data-state="{str(state_v).lower()}"
       data-district="{str(district_v).lower()}">
    <div class="hcard-top">
      <div class="hcard-left">
        <div class="avatar-red">{initial}</div>
        <div>
          <div class="hcard-name"><i class="fa-solid fa-hospital" style="font-size:.85rem;opacity:.6"></i>&nbsp;{hname}</div>
          <div class="hcard-sub">Owner: {owner} &bull; {phone} &bull; {district_v}, {state_v}</div>
        </div>
      </div>
      <div class="hcard-right">
        <span class="badge-rej"><i class="fa-solid fa-ban"></i> Rejected</span>
        <button class="btn-viewmore-red" onclick="toggleDetails(this,'det{rid}')">
          <i class="fa-solid fa-chevron-down vm-icon"></i> View More
        </button>
      </div>
    </div>
    <div class="hcard-details" id="det{rid}">
      <div class="detail-tabs" id="tabs{rid}">
        <button class="dtab-red active" onclick="switchTab({rid},'info','red')"><i class="fa-solid fa-hospital"></i> Hospital Info</button>
        <button class="dtab-red" onclick="switchTab({rid},'contact','red')"><i class="fa-solid fa-address-card"></i> Contact</button>
        <button class="dtab-red" onclick="switchTab({rid},'account','red')"><i class="fa-solid fa-lock"></i> Account</button>
      </div>
      <div class="dpanel active" id="dp{rid}-info">
        <div class="dg">
          <div class="di"><label>Hospital Name</label><span>{hname}</span></div>
          <div class="di"><label>Owner / Manager</label><span>{owner}</span></div>
          <div class="di"><label>Phone</label><span>{hnum}</span></div>
          <div class="di"><label>State</label><span>{state_v}</span></div>
          <div class="di"><label>District</label><span>{district_v}</span></div>
          <div class="di"><label>Status</label><span><span class="badge-rej"><i class="fa-solid fa-ban"></i> Rejected</span></span></div>
          <div class="di full"><label>Address</label><span>{address}</span></div>
        </div>
      </div>
      <div class="dpanel" id="dp{rid}-contact">
        <div class="dg">
          <div class="di"><label>Email</label><span>{email}</span></div>
          <div class="di"><label>Mobile</label><span>{phone}</span></div>
          <div class="di"><label>State</label><span>{state_v}</span></div>
          <div class="di"><label>District</label><span>{district_v}</span></div>
        </div>
      </div>
      <div class="dpanel" id="dp{rid}-account">
        <div class="dg">
          <div class="di"><label>Username</label><span>{username}</span></div>
          <div class="di">
            <label>Password</label>
            <span id="pwd-{rid}" style="letter-spacing:3px;color:var(--mu)">&#9679;&#9679;&#9679;&#9679;&#9679;&#9679;&#9679;&#9679;</span><br>
            <button class="pwd-reveal" onclick="togglePwd({rid},'{password}')"><i class="fa-solid fa-eye"></i> Show</button>
          </div>
        </div>
      </div>
    </div>
  </div>
""")
else:
    print('<div class="empty-state"><i class="fa-solid fa-circle-check"></i><h3>No Rejected Hospitals</h3><p>No hospital registrations have been rejected yet.</p></div>')

print("</div><!-- /sec-rejected -->")

print(f"""
<div class="section" id="sec-children">
  <div class="page-hdr-blue">
    <div>
      <h2><i class="fa-solid fa-children"></i>&nbsp; Registered Children</h2>
      <p>Click <strong>View More</strong> on any child to see parent, vaccine &amp; hospital details</p>
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
    <select class="fsel" id="vacFilter" onchange="filterChildCards()">
      <option value="">All Vaccine Status</option>
      <option value="taken">Has Taken</option>
      <option value="notified">Notified</option>
      <option value="pending">Pending</option>
    </select>
    <span class="cnt-lbl" id="cntLbl2">{len(children_raw)} records</span>
  </div>
""")

if not children_raw:
    print('<div class="empty"><i class="fa-solid fa-child-reaching"></i><p>No registered children found.</p></div>')
else:
    for r in children_raw:
        cid=r[0]; cname=r[1] or "—"; dob=r[2] or "—"; weight=r[3] or "—"
        gender=r[4] or "—"; blood=r[5] or "—"
        father=r[7] or "—"; mother=r[8] or "—"; email=r[9] or "—"
        mobile=r[10] or "—"; state=r[11] or "—"; district=r[12] or "—"
        address=r[13] or "—"; occ=r[14] or "—"; pstatus=r[15] or "pending"
        pbc={"approved":"ba","rejected":"br","pending":"bp"}.get(pstatus,"bp")
        gicon="fa-mars" if str(r[4]).lower()=="male" else ("fa-venus" if str(r[4]).lower()=="female" else "fa-genderless")
        initial=str(r[1])[0].upper() if r[1] else "?"
        vaccines=vax_by_child.get(cid,[]); v_total=len(vaccines)
        v_taken=sum(1 for v in vaccines if v["status"]=="taken")
        v_notified=sum(1 for v in vaccines if v["status"]=="notified")
        v_pending=v_total-v_taken-v_notified
        vac_statuses=" ".join(set(v["status"] or "pending" for v in vaccines)) if vaccines else "pending"
        h=hosp_by_child.get(cid,{}); hn=h.get("name","Not assigned yet")
        hnum=h.get("number","—"); hst=h.get("state","—"); hdi=h.get("district","—")
        vrows=""
        for vi,v in enumerate(vaccines,1):
            vs=v["status"] or "pending"; vd=v["date"] or "—"
            bc="bt" if vs=="taken" else ("bn" if vs=="notified" else "bp")
            vrows+=(f"<tr><td>{vi}</td><td><strong>{v['name']}</strong></td>"
                    f"<td>{v['age']} mo.</td><td>{vd}</td>"
                    f"<td><span class='bx {bc}'>{vs.capitalize()}</span></td></tr>")
        if not vrows:
            vrows="<tr><td colspan='5' style='text-align:center;color:#bbb;padding:14px'>No vaccines assigned yet</td></tr>"

        print(f"""
  <div class="child-card"
       data-name="{str(r[1]).lower()}"
       data-father="{str(r[7] or '').lower()}"
       data-mobile="{mobile}"
       data-blood="{str(r[5] or '').lower()}"
       data-gender="{str(r[4] or '').lower()}"
       data-vacstatus="{vac_statuses}">
    <div class="ccard-top">
      <div class="ccard-left">
        <div class="avatar-blue">{initial}</div>
        <div>
          <div class="ccard-name"><i class="fa-solid {gicon}" style="font-size:.85rem;opacity:.7"></i>&nbsp;{cname}</div>
          <div class="ccard-sub">DOB: {dob} &bull; Blood: {blood} &bull; {weight} kg &bull; {gender}</div>
        </div>
      </div>
      <div class="ccard-right">
        <span class="bx bgy"><i class="fa-solid fa-syringe"></i>&nbsp; {v_total} Vaccines</span>
        <span class="bx {pbc}">Parent: {pstatus.capitalize()}</span>
        <button class="btn-viewmore-blue" onclick="toggleCDetails(this,'cdet{cid}')">
          <i class="fa-solid fa-chevron-down vm-icon"></i> View More
        </button>
      </div>
    </div>
    <div class="ccard-details" id="cdet{cid}">
      <div class="detail-tabs" id="ctabs{cid}">
        <button class="dtab-blue active" onclick="switchCTab({cid},'parent')"><i class="fa-solid fa-users"></i> Parent</button>
        <button class="dtab-blue" onclick="switchCTab({cid},'vaccine')"><i class="fa-solid fa-syringe"></i> Vaccine</button>
        <button class="dtab-blue" onclick="switchCTab({cid},'hospital')"><i class="fa-solid fa-hospital"></i> Hospital</button>
      </div>
      <div class="dpanel active" id="cdp{cid}-parent">
        <div class="dg">
          <div class="di"><label>Father Name</label><span>{father}</span></div>
          <div class="di"><label>Mother Name</label><span>{mother}</span></div>
          <div class="di"><label>Mobile</label><span>{mobile}</span></div>
          <div class="di"><label>Email</label><span>{email}</span></div>
          <div class="di"><label>Occupation</label><span>{occ}</span></div>
          <div class="di"><label>State</label><span>{state}</span></div>
          <div class="di"><label>District</label><span>{district}</span></div>
          <div class="di"><label>Parent Status</label><span><span class="bx {pbc}">{pstatus.capitalize()}</span></span></div>
          <div class="di full"><label>Address</label><span>{address}</span></div>
        </div>
      </div>
      <div class="dpanel" id="cdp{cid}-vaccine">
        <div class="vsumbadges">
          <span class="vsb tk"><i class="fa-solid fa-check-circle"></i> {v_taken} Taken</span>
          <span class="vsb nt"><i class="fa-solid fa-bell"></i> {v_notified} Notified</span>
          <span class="vsb pd"><i class="fa-solid fa-clock"></i> {v_pending} Pending</span>
        </div>
        <div style="overflow-x:auto;border:1px solid var(--bo);border-radius:8px">
          <table class="vtable">
            <thead><tr><th>#</th><th>Vaccine</th><th>Due Age</th><th>Date</th><th>Status</th></tr></thead>
            <tbody>{vrows}</tbody>
          </table>
        </div>
      </div>
      <div class="dpanel" id="cdp{cid}-hospital">
        <div class="dg">
          <div class="di"><label>Hospital Name</label><span>{hn}</span></div>
          <div class="di"><label>Contact</label><span>{hnum}</span></div>
          <div class="di"><label>State</label><span>{hst}</span></div>
          <div class="di"><label>District</label><span>{hdi}</span></div>
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
function toggleDetails(btn,detId){
  const det=document.getElementById(detId);
  const isOpen=det.classList.contains('open');
  det.classList.toggle('open',!isOpen);
  btn.innerHTML=isOpen?'<i class="fa-solid fa-chevron-down vm-icon"></i> View More':'<i class="fa-solid fa-chevron-up vm-icon"></i> View Less';
}
function switchTab(id,tabName,color){
  const panels=['info','contact','account'];
  const cls='dtab-'+color;
  const btns=document.getElementById('tabs'+id).querySelectorAll('.'+cls);
  panels.forEach((p,i)=>{
    const el=document.getElementById('dp'+id+'-'+p);
    if(el) el.classList.toggle('active',p===tabName);
    if(btns[i]) btns[i].classList.toggle('active',p===tabName);
  });
}
function togglePwd(id,pwd){
  const el=document.getElementById('pwd-'+id);
  const btn=el.nextElementSibling;
  const showing=el.style.letterSpacing==='normal';
  el.innerHTML=showing?'&#9679;&#9679;&#9679;&#9679;&#9679;&#9679;&#9679;&#9679;':pwd;
  el.style.letterSpacing=showing?'3px':'normal';
  el.style.color=showing?'var(--mu)':'var(--tx)';
  btn.innerHTML=showing?'<i class="fa-solid fa-eye"></i> Show':'<i class="fa-solid fa-eye-slash"></i> Hide';
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

function filterCards(){
  const q  = document.getElementById('searchInput').value.toLowerCase();
  const st = document.getElementById('stateFilter').value.toLowerCase();
  const di = document.getElementById('districtFilter').value.toLowerCase();
  let visible=0;
  document.querySelectorAll('.hosp-card').forEach(c=>{
    const matchQ  = !q  || c.dataset.name.includes(q)||c.dataset.owner.includes(q)||c.dataset.email.includes(q)||c.dataset.phone.includes(q);
    const matchSt = !st || (c.dataset.state||'')===st;
    const matchDi = !di || (c.dataset.district||'')===di;
    const show=matchQ&&matchSt&&matchDi;
    c.style.display=show?'':'none';
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
  filterCards();
}
function toggleCDetails(btn,detId){
  const det=document.getElementById(detId);
  const isOpen=det.classList.contains('open');
  det.classList.toggle('open',!isOpen);
  btn.innerHTML=isOpen?'<i class="fa-solid fa-chevron-down vm-icon"></i> View More':'<i class="fa-solid fa-chevron-up vm-icon"></i> View Less';
}
function switchCTab(cid,tabName){
  const panels=['parent','vaccine','hospital'];
  const btns=document.getElementById('ctabs'+cid).querySelectorAll('.dtab-blue');
  panels.forEach((p,i)=>{
    const el=document.getElementById('cdp'+cid+'-'+p);
    if(el) el.classList.toggle('active',p===tabName);
    if(btns[i]) btns[i].classList.toggle('active',p===tabName);
  });
}
function filterChildCards(){
  const q=document.getElementById('childSearch').value.toLowerCase();
  const gf=document.getElementById('genderFilter').value.toLowerCase();
  const vf=document.getElementById('vacFilter').value.toLowerCase();
  let visible=0;
  document.querySelectorAll('.child-card').forEach(c=>{
    const matchQ=!q||c.dataset.name.includes(q)||c.dataset.father.includes(q)||c.dataset.mobile.includes(q)||c.dataset.blood.includes(q);
    const matchG=!gf||c.dataset.gender===gf;
    const matchV=!vf||(c.dataset.vacstatus||'').includes(vf);
    const show=matchQ&&matchG&&matchV;
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