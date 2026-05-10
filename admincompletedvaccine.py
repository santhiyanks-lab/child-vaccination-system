#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
import sys, os.path
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
print("Content-type:text/html\r\n\r\n")
import cgi, cgitb, pymysql
from datetime import date

cgitb.enable()
con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()
form = cgi.FieldStorage()

def qc(sql):
    cur.execute(sql)
    return cur.fetchone()[0]
# Feedback counts
total_fb = qc("SELECT COUNT(*) FROM feedback")
low_fb   = qc("SELECT COUNT(*) FROM feedback WHERE rating < 2")

def qc(sql):
    cur.execute(sql)
    return cur.fetchone()[0]

pending_parents    = qc("SELECT COUNT(*) FROM parent WHERE status='pending'")
approved_parents   = qc("SELECT COUNT(*) FROM parent WHERE status='approved'")
rejected_parents   = qc("SELECT COUNT(*) FROM parent WHERE status='rejected'")
pending_hospitals  = qc("SELECT COUNT(*) FROM hospital WHERE status='pending'")
approved_hospitals = qc("SELECT COUNT(*) FROM hospital WHERE status='approved'")
rejected_hospitals = qc("SELECT COUNT(*) FROM hospital WHERE status='rejected'")
total_notified     = qc("SELECT COUNT(*) FROM child_vaccine WHERE status='notified'")
total_children     = qc("SELECT COUNT(*) FROM children")
total_completed    = qc("SELECT COUNT(*) FROM child_vaccine WHERE status='completed'")

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

# Fetch all completed appointments
cur.execute("""
    SELECT
        cv.id, cv.appointment_date, cv.appointment_time,
        cv.reschedule_date, cv.reschedule_time,
        cv.dose_number,
        c.child_id, c.child_name, c.dob, c.gender, c.blood_group, c.weight,
        p.father_name, p.mobile_number, p.email,
        p.state, p.district,
        v.vaccine_name,
        h.hospital_name, h.district AS hosp_district, h.state AS hosp_state
    FROM child_vaccine cv
    JOIN children c  ON cv.child_id    = c.child_id
    JOIN parent p    ON c.parent_id    = p.parent_id
    JOIN vaccine v   ON cv.vaccine_id  = v.vaccine_id
    JOIN hospital h  ON cv.hospital_id = h.hospital_id
    WHERE cv.status = 'completed'
    ORDER BY cv.id DESC
""")
records = cur.fetchall()

# Children data
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

print(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Completed Vaccinations</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    *,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
    :root{{
      --p:#1565c0;--pd:#0d47a1;--pl:#e3f2fd;--ac:#ff6f00;
      --sw:260px;--hh:60px;--tx:#1c1c1c;--mu:#6b7280;
      --bg:#f0f4f8;--ca:#fff;--bo:#dde3ea;
      --da:#e53935;--dl:#ffebee;--su:#2e7d32;--sl:#e8f5e9;
      --wa:#f57f17;--wl:#fff8e1;
      --ra:10px;--sh:0 2px 16px rgba(0,0,0,.09);
      --tr:.25s ease;--fn:'Segoe UI',Arial,sans-serif
    }}
    html{{scroll-behavior:smooth}}
    body{{font-family:var(--fn);background:var(--bg);color:var(--tx);min-height:100vh;line-height:1.6}}
    a{{text-decoration:none;color:inherit}}
    img{{max-width:100%;height:auto;display:block;object-fit:cover}}
    .overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1100}}
    .overlay.active{{display:block}}

    /* ===== SIDEBAR ===== */
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
    .nbadge.or{{background:var(--ac)}}.nbadge.gr{{background:#2e7d32}}.nbadge.gy{{background:#777}}.nbadge.te{{background:#00838f}}
    .sfooter{{padding:14px 12px;border-top:1px solid rgba(255,255,255,.12)}}
    .btn-logout{{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:10px;background:var(--da);color:#fff;border:none;border-radius:var(--ra);font-size:.88rem;font-weight:600;font-family:var(--fn);cursor:pointer;text-decoration:none;transition:background var(--tr)}}
    .btn-logout:hover{{background:#b71c1c}}

    /* ===== MAIN ===== */
    .mwrap{{margin-left:var(--sw);display:flex;flex-direction:column;min-height:100vh}}
    .topbar{{height:var(--hh);background:var(--ca);border-bottom:1px solid var(--bo);position:sticky;top:0;z-index:900;display:flex;align-items:center;justify-content:space-between;padding:0 20px;box-shadow:0 1px 8px rgba(0,0,0,.06)}}
    .tbl{{display:flex;align-items:center;gap:12px}}
    .ttitle{{font-size:1rem;font-weight:700;color:var(--p)}}
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

    /* PAGE HEADER */
    .page-hdr{{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:20px;flex-wrap:wrap}}
    .page-hdr-left{{display:flex;align-items:center;gap:14px}}
    .page-hdr-icon{{width:48px;height:48px;border-radius:12px;background:var(--sl);color:var(--su);display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0}}
    .page-hdr h2{{font-size:clamp(1rem,2.5vw,1.35rem);font-weight:700}}
    .page-hdr p{{font-size:.83rem;color:var(--mu);margin-top:2px}}
    .cnt-badge{{background:var(--sl);color:var(--su);padding:6px 16px;border-radius:20px;font-size:.85rem;font-weight:700;white-space:nowrap}}

    /* INFO BANNER */
    .info-banner{{display:flex;align-items:center;gap:12px;background:var(--sl);border:1px solid #a5d6a7;border-radius:var(--ra);padding:12px 18px;margin-bottom:18px;font-size:.88rem;color:var(--su)}}
    .info-banner i{{font-size:1.1rem;flex-shrink:0}}

    /* TOOLBAR */
    .toolbar{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px;flex-wrap:wrap}}
    .sbox{{position:relative}}
    .sbox i{{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:var(--mu);font-size:.85rem}}
    .sbox input{{padding:8px 12px 8px 32px;border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.88rem;background:var(--ca);width:220px;transition:border-color var(--tr)}}
    .sbox input:focus{{outline:none;border-color:var(--p)}}

    /* TABLE */
    .tcard{{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);overflow:hidden}}
    .tcard-head{{background:linear-gradient(90deg,#1b5e20,var(--su));color:#fff;padding:14px 20px;display:flex;align-items:center;gap:10px;font-size:.95rem;font-weight:700}}
    .tw{{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}}
    table{{width:100%;border-collapse:collapse;min-width:700px}}
    thead{{background:#263238;color:#fff}}
    th{{padding:12px 14px;text-align:left;font-size:.82rem;font-weight:600;text-transform:uppercase;letter-spacing:.4px;white-space:nowrap}}
    td{{padding:12px 14px;font-size:.88rem;border-bottom:1px solid var(--bo);white-space:nowrap;vertical-align:middle}}
    tbody tr:hover{{background:var(--sl)}}
    tbody tr:last-child td{{border-bottom:none}}
    .child-avatar{{display:inline-flex;align-items:center;gap:9px}}
    .avatar-circle{{width:32px;height:32px;border-radius:50%;background:var(--sl);color:var(--su);display:flex;align-items:center;justify-content:center;font-size:.78rem;font-weight:700;flex-shrink:0}}
    .snum{{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;background:var(--sl);color:var(--su);border-radius:50%;font-size:.78rem;font-weight:700}}
    .badge-completed{{display:inline-flex;align-items:center;gap:5px;padding:4px 12px;background:var(--sl);color:var(--su);border-radius:20px;font-size:.78rem;font-weight:700}}
    .btn-view{{display:inline-flex;align-items:center;gap:6px;padding:7px 14px;background:var(--sl);color:var(--su);border:1px solid var(--su);border-radius:7px;font-family:var(--fn);font-size:.82rem;font-weight:600;cursor:pointer;transition:background var(--tr),color var(--tr);white-space:nowrap}}
    .btn-view:hover{{background:var(--su);color:#fff}}
    .empty-state{{text-align:center;padding:56px 20px;color:var(--mu)}}
    .empty-state i{{font-size:3rem;margin-bottom:14px;color:var(--bo);display:block}}
    .empty-state h3{{font-size:1rem;font-weight:700;margin-bottom:6px;color:var(--tx)}}
    .empty-state p{{font-size:.88rem}}

    /* MODAL */
    .modal-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:2000;align-items:center;justify-content:center;padding:16px}}
    .modal-overlay.active{{display:flex}}
    .modal-box{{background:var(--ca);border-radius:var(--ra);width:100%;max-width:680px;max-height:90vh;display:flex;flex-direction:column;box-shadow:0 8px 40px rgba(0,0,0,.2);animation:slideUp .25s ease}}
    @keyframes slideUp{{from{{transform:translateY(40px);opacity:0}}to{{transform:translateY(0);opacity:1}}}}
    .modal-head{{background:linear-gradient(90deg,#1b5e20,var(--su));color:#fff;padding:16px 20px;display:flex;align-items:center;justify-content:space-between;border-radius:var(--ra) var(--ra) 0 0;flex-shrink:0}}
    .modal-head h4{{font-size:1rem;font-weight:700}}
    .modal-close{{background:rgba(255,255,255,.2);border:none;color:#fff;width:28px;height:28px;border-radius:50%;cursor:pointer;font-size:.9rem;display:flex;align-items:center;justify-content:center;transition:background var(--tr)}}
    .modal-close:hover{{background:rgba(255,255,255,.35)}}
    .modal-body{{padding:20px;overflow-y:auto;flex:1}}
    .modal-section-title{{font-size:.8rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--su);margin:16px 0 10px;padding-bottom:6px;border-bottom:2px solid var(--sl)}}
    .modal-section-title:first-child{{margin-top:0}}
    .detail-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px 20px}}
    .detail-item label{{display:block;font-size:.72rem;color:var(--mu);font-weight:600;text-transform:uppercase;letter-spacing:.4px;margin-bottom:2px}}
    .detail-item span{{font-size:.9rem;font-weight:500;color:var(--tx)}}
    .info-box{{background:var(--sl);border:1px solid #a5d6a7;border-radius:8px;padding:14px 16px;margin-bottom:10px}}
    .info-box-title{{font-size:.75rem;font-weight:700;color:var(--su);text-transform:uppercase;letter-spacing:.4px;margin-bottom:8px}}
    .info-box .detail-grid .detail-item span{{color:var(--su);font-weight:700}}

    /* ===== CHILDREN SECTION ===== */
    .page-hdr2{{background:linear-gradient(120deg,var(--p),var(--pd));color:#fff;border-radius:var(--ra);padding:22px 28px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}}
    .page-hdr2 h2{{font-size:1.1rem;font-weight:700;margin-bottom:3px}}
    .page-hdr2 p{{font-size:.83rem;opacity:.8}}
    .page-hdr2-badge{{background:rgba(255,255,255,.18);padding:7px 16px;border-radius:20px;font-size:.83rem;font-weight:700}}
    .ch-toolbar{{display:flex;align-items:center;gap:12px;margin-bottom:18px;flex-wrap:wrap}}
    .ch-sbox{{position:relative;flex:1;min-width:200px}}
    .ch-sbox i{{position:absolute;left:11px;top:50%;transform:translateY(-50%);color:var(--mu);font-size:.82rem}}
    .ch-sbox input{{width:100%;padding:9px 12px 9px 34px;border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.85rem;background:var(--ca)}}
    .ch-sbox input:focus{{outline:none;border-color:var(--p)}}
    .fsel{{padding:9px 14px;border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.85rem;background:var(--ca);color:var(--tx);cursor:pointer}}
    .fsel:focus{{outline:none;border-color:var(--p)}}
    .cnt-lbl{{font-size:.84rem;color:var(--mu);font-weight:600;white-space:nowrap}}

    /* ===== CHILD CARD ===== */
    .child-card{{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);margin-bottom:16px;overflow:hidden}}
    .ccard-head{{background:linear-gradient(90deg,var(--p),var(--pd));color:#fff;padding:14px 20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}}
    .ccard-left{{display:flex;align-items:center;gap:14px}}
    .ccard-avatar{{width:44px;height:44px;border-radius:50%;background:rgba(255,255,255,.2);border:2px solid rgba(255,255,255,.4);display:flex;align-items:center;justify-content:center;font-size:1.15rem;font-weight:800;color:#fff;flex-shrink:0}}
    .ccard-name{{font-size:.96rem;font-weight:700}}
    .ccard-sub{{font-size:.75rem;opacity:.8;margin-top:2px}}
    .ccard-right{{display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
    .btn-vm{{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;background:rgba(255,255,255,.18);color:#fff;border:1px solid rgba(255,255,255,.35);border-radius:7px;font-size:.81rem;font-weight:600;font-family:var(--fn);cursor:pointer;transition:background var(--tr)}}
    .btn-vm:hover{{background:rgba(255,255,255,.3)}}
    .ccard-body{{display:none;grid-template-columns:1fr 1fr 1fr;border-top:1px solid var(--bo)}}
    .ccard-body.open{{display:grid}}
    .csec{{padding:16px 18px;border-right:1px solid var(--bo)}}
    .csec:last-child{{border-right:none}}
    .csec-title{{font-size:.71rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--p);margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid var(--pl);display:flex;align-items:center;gap:6px}}
    .dg{{display:grid;grid-template-columns:1fr 1fr;gap:7px 14px}}
    .di label{{display:block;font-size:.67rem;color:var(--mu);font-weight:700;text-transform:uppercase;letter-spacing:.4px;margin-bottom:2px}}
    .di span{{font-size:.84rem;font-weight:600;color:var(--tx);word-break:break-word}}
    .di.full{{grid-column:1/-1}}
    .vsumbadges{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}}
    .vsb{{display:flex;align-items:center;gap:4px;padding:3px 10px;border-radius:20px;font-size:.73rem;font-weight:700}}
    .vsb.tk{{background:#e8f5e9;color:#2e7d32}}
    .vsb.nt{{background:#fff3e0;color:#e65100}}
    .vsb.pd{{background:#fff8e1;color:#f57f17}}
    .vtable{{width:100%;border-collapse:collapse;font-size:.82rem}}
    .vtable th{{background:#f0f4f8;color:var(--p);padding:7px 10px;text-align:left;font-size:.72rem;font-weight:700;text-transform:uppercase;border-bottom:2px solid var(--bo)}}
    .vtable td{{padding:7px 10px;border-bottom:1px solid var(--bo)}}
    .vtable tbody tr:hover{{background:var(--pl)}}
    .vtable tbody tr:last-child td{{border-bottom:none}}
    .bx{{display:inline-flex;align-items:center;padding:3px 10px;border-radius:20px;font-size:.74rem;font-weight:700}}
    .bp{{background:#fff8e1;color:#f57f17}}.ba{{background:#e8f5e9;color:#2e7d32}}
    .br{{background:#ffebee;color:#c62828}}.bn{{background:#fff3e0;color:#e65100}}
    .bt{{background:#e8f5e9;color:#2e7d32}}.bgy{{background:#f3f4f6;color:#555}}
    .empty{{text-align:center;padding:60px 20px;color:var(--mu)}}
    .empty i{{font-size:3rem;opacity:.3;display:block;margin-bottom:14px}}

    footer{{background:#1c1c2e;color:rgba(255,255,255,.6);text-align:center;padding:14px 20px;font-size:.8rem}}

    @media(max-width:1024px){{.ccard-body.open{{grid-template-columns:1fr 1fr}}}}
    @media(max-width:768px){{
      .sidebar{{transform:translateX(-100%)}}.sidebar.open{{transform:translateX(0)}}
      .mwrap{{margin-left:0}}.hamburger{{display:flex}}.abadge{{display:none}}
      .ccard-body.open{{grid-template-columns:1fr}}
      .csec{{border-right:none;border-bottom:1px solid var(--bo)}}
      .csec:last-child{{border-bottom:none}}
      .sbox input{{width:160px}}
    }}
    @media(max-width:480px){{
      .talert span{{display:none}}.pc{{padding:14px 12px}}
      .page-hdr-icon{{display:none}}.sbox input{{width:130px}}
      th,td{{padding:10px;font-size:.82rem}}
      .detail-grid{{grid-template-columns:1fr}}
      .modal-box{{max-height:95vh}}
      .dg{{grid-template-columns:1fr}}
    }}
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
    <div class="ng open" id="g4">
      <button class="ngt" onclick="tg('g4')">
        <i class="fa-solid fa-bell ic"></i> Notification {nb(total_notified,"or")}
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a href="adminnotification.py"><i class="fa-solid fa-paper-plane"></i> Notify {sb(total_notified)}</a>
        <a href="adminnotifiedchild.py"><i class="fa-solid fa-child"></i> Notified Child</a>
        <a href="admincompletedvaccine.py" class="active"><i class="fa-solid fa-circle-check"></i> Completed {nb(total_completed,"gr")}</a>
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
  </nav>
  <div class="sfooter">
    <a href="home.py" class="btn-logout"><i class="fa-solid fa-right-from-bracket"></i> Logout</a>
  </div>
</aside>

<div class="mwrap">
  <header class="topbar">
    <div class="tbl">
      <button class="hamburger" id="hamburger"><span></span><span></span><span></span></button>
      <span class="ttitle" id="page-title">Completed Vaccinations</span>
    </div>
    <div class="tbr">
      {tp}{th_alert}
      <span class="abadge"><i class="fa-solid fa-shield-halved"></i> Admin</span>
    </div>
  </header>

  <main class="pc">
""")

# ======================================================
# SECTION 1 — COMPLETED VACCINATIONS (active)
# ======================================================
print(f"""
<div class="section active" id="sec-completed">
  <div class="page-hdr">
    <div class="page-hdr-left">
      <div class="page-hdr-icon"><i class="fa-solid fa-circle-check"></i></div>
      <div>
        <h2>Completed Vaccinations</h2>
        <p>Appointments marked as completed by parents.</p>
      </div>
    </div>
    <span class="cnt-badge" id="rowCount">
      <i class="fa-solid fa-circle-check"></i> -- Completed
    </span>
  </div>

  <div class="info-banner">
    <i class="fa-solid fa-circle-info"></i>
    <span>These vaccination appointments have been confirmed as completed by the parent after visiting the hospital.</span>
  </div>

  <div class="toolbar">
    <div class="sbox">
      <i class="fa-solid fa-magnifying-glass"></i>
      <input type="text" id="searchInput" placeholder="Search by child, vaccine, hospital..." oninput="filterTable()">
    </div>
  </div>

  <div class="tcard">
    <div class="tcard-head">
      <i class="fa-solid fa-circle-check"></i> Completed Vaccination Records
    </div>
    <div class="tw">
      <table id="mainTable">
        <thead>
          <tr>
            <th>#</th>
            <th><i class="fa-solid fa-child"></i> Child</th>
            <th><i class="fa-solid fa-syringe"></i> Vaccine</th>
            <th><i class="fa-solid fa-hospital"></i> Hospital</th>
            <th><i class="fa-solid fa-calendar"></i> Appointment</th>
            <th><i class="fa-solid fa-pills"></i> Dose</th>
            <th>Status</th>
            <th><i class="fa-solid fa-eye"></i> Details</th>
          </tr>
        </thead>
        <tbody id="tableBody">
""")

if records:
    for idx, row in enumerate(records, start=1):
        cv_id         = row[0]
        appt_date     = row[1]
        res_date      = row[3]
        dose          = row[5] if row[5] else "1"
        child_name    = row[7]
        initials      = child_name[0].upper() if child_name else "C"
        vaccine_name  = row[17]
        hospital_name = row[18]
        display_date  = res_date if res_date else appt_date

        print(f"""
            <tr>
              <td><span class="snum">{idx}</span></td>
              <td>
                <div class="child-avatar">
                  <div class="avatar-circle">{initials}</div>
                  <strong>{child_name}</strong>
                </div>
              </td>
              <td>{vaccine_name}</td>
              <td>{hospital_name}</td>
              <td>{display_date}</td>
              <td>Dose {dose}</td>
              <td><span class="badge-completed"><i class="fa-solid fa-circle-check"></i> Completed</span></td>
              <td>
                <button class="btn-view" onclick="openModal('modal{cv_id}')">
                  <i class="fa-solid fa-eye"></i> View
                </button>
              </td>
            </tr>
        """)
else:
    print("""
            <tr><td colspan="8">
              <div class="empty-state">
                <i class="fa-solid fa-circle-check"></i>
                <h3>No Completed Vaccinations</h3>
                <p>No appointments have been marked as completed by parents yet.</p>
              </div>
            </td></tr>
    """)

print("""
        </tbody>
      </table>
    </div>
  </div>
</div><!-- /sec-completed -->
""")

# ======================================================
# SECTION 2 — CHILDREN DETAILS
# ======================================================
print(f"""
<div class="section" id="sec-children">
  <div class="page-hdr2">
    <div>
      <h2><i class="fa-solid fa-children"></i>&nbsp; Registered Children</h2>
      <p>Click <strong>View More</strong> to expand Child, Parent &amp; Vaccine details</p>
    </div>
    <span class="page-hdr2-badge"><i class="fa-solid fa-child"></i> {total_children} Total</span>
  </div>
  <div class="ch-toolbar">
    <div class="ch-sbox">
      <i class="fa-solid fa-magnifying-glass"></i>
      <input type="text" id="childSearch" placeholder="Search child name, father, mobile, blood group..." oninput="filterCards()">
    </div>
    <select class="fsel" id="genderFilter" onchange="filterCards()">
      <option value="">All Genders</option>
      <option value="male">Male</option>
      <option value="female">Female</option>
    </select>
    <select class="fsel" id="vacFilter" onchange="filterCards()">
      <option value="">All Vaccine Status</option>
      <option value="taken">Has Taken</option>
      <option value="notified">Notified</option>
      <option value="pending">Pending</option>
    </select>
    <span class="cnt-lbl" id="cntLbl">{len(children_raw)} records</span>
  </div>
""")

if not children_raw:
    print('<div class="empty"><i class="fa-solid fa-child-reaching"></i><p>No registered children found.</p></div>')
else:
    for r in children_raw:
        cid      = r[0]
        cname    = r[1]  or "&mdash;"
        dob      = r[2]  or "&mdash;"
        weight   = r[3]  or "&mdash;"
        gender   = r[4]  or "&mdash;"
        blood    = r[5]  or "&mdash;"
        idmark   = r[6]  or "&mdash;"
        father   = r[7]  or "&mdash;"
        mother   = r[8]  or "&mdash;"
        email    = r[9]  or "&mdash;"
        mobile   = r[10] or "&mdash;"
        state    = r[11] or "&mdash;"
        district = r[12] or "&mdash;"
        address  = r[13] or "&mdash;"
        occ      = r[14] or "&mdash;"
        pstatus  = r[15] or "pending"

        pbc     = {"approved":"ba","rejected":"br","pending":"bp"}.get(pstatus,"bp")
        gicon   = "fa-mars" if str(r[4]).lower()=="male" else ("fa-venus" if str(r[4]).lower()=="female" else "fa-genderless")
        initial = str(r[1])[0].upper() if r[1] else "?"

        vaccines   = vax_by_child.get(cid, [])
        v_total    = len(vaccines)
        v_taken    = sum(1 for v in vaccines if v["status"]=="taken")
        v_notified = sum(1 for v in vaccines if v["status"]=="notified")
        v_pending  = v_total - v_taken - v_notified
        vac_st     = " ".join(set(v["status"] or "pending" for v in vaccines)) if vaccines else "pending"

        vrows = ""
        for vi, v in enumerate(vaccines, 1):
            vs = v["status"] or "pending"
            vd = v["date"]   or "&mdash;"
            bc = "bt" if vs=="taken" else ("bn" if vs=="notified" else "bp")
            vrows += (f"<tr><td>{vi}</td><td><strong>{v['name']}</strong></td>"
                      f"<td>{v['age']} mo.</td><td>{vd}</td>"
                      f"<td><span class='bx {bc}'>{vs.capitalize()}</span></td></tr>")
        if not vrows:
            vrows = "<tr><td colspan='5' style='text-align:center;color:#bbb;padding:12px'>No vaccines assigned yet</td></tr>"

        print(f"""
  <div class="child-card"
       data-name="{str(r[1] or '').lower()}"
       data-father="{str(r[7] or '').lower()}"
       data-mobile="{mobile}"
       data-blood="{str(r[5] or '').lower()}"
       data-gender="{str(r[4] or '').lower()}"
       data-vacstatus="{vac_st}">
    <div class="ccard-head">
      <div class="ccard-left">
        <div class="ccard-avatar">{initial}</div>
        <div>
          <div class="ccard-name"><i class="fa-solid {gicon}" style="font-size:.82rem;opacity:.75"></i>&nbsp; {cname}</div>
          <div class="ccard-sub">DOB: {dob} &bull; Blood: {blood} &bull; {weight} kg &bull; {gender}</div>
        </div>
      </div>
      <div class="ccard-right">
        <span class="bx bgy"><i class="fa-solid fa-syringe"></i>&nbsp; {v_total} Vaccines</span>
        <span class="bx {pbc}">Parent: {pstatus.capitalize()}</span>
        <button class="btn-vm" onclick="toggleCard(this,'cbody{cid}')">
          <i class="fa-solid fa-chevron-down"></i> View More
        </button>
      </div>
    </div>
    <div class="ccard-body" id="cbody{cid}">
      <div class="csec">
        <div class="csec-title"><i class="fa-solid fa-child"></i> Child Details</div>
        <div class="dg">
          <div class="di"><label>Full Name</label><span>{cname}</span></div>
          <div class="di"><label>Date of Birth</label><span>{dob}</span></div>
          <div class="di"><label>Gender</label><span>{gender}</span></div>
          <div class="di"><label>Blood Group</label><span>{blood}</span></div>
          <div class="di"><label>Weight</label><span>{weight} kg</span></div>
          <div class="di"><label>ID Mark</label><span>{idmark}</span></div>
        </div>
      </div>
      <div class="csec">
        <div class="csec-title"><i class="fa-solid fa-users"></i> Parent Details</div>
        <div class="dg">
          <div class="di"><label>Father</label><span>{father}</span></div>
          <div class="di"><label>Mother</label><span>{mother}</span></div>
          <div class="di"><label>Mobile</label><span>{mobile}</span></div>
          <div class="di"><label>Email</label><span style="font-size:.78rem">{email}</span></div>
          <div class="di"><label>Occupation</label><span>{occ}</span></div>
          <div class="di"><label>State / District</label><span>{state} / {district}</span></div>
          <div class="di full"><label>Address</label><span>{address}</span></div>
        </div>
      </div>
      <div class="csec">
        <div class="csec-title"><i class="fa-solid fa-syringe"></i> Vaccine Details</div>
        <div class="vsumbadges">
          <span class="vsb tk"><i class="fa-solid fa-check-circle"></i> {v_taken} Taken</span>
          <span class="vsb nt"><i class="fa-solid fa-bell"></i> {v_notified} Notified</span>
          <span class="vsb pd"><i class="fa-solid fa-clock"></i> {v_pending} Pending</span>
        </div>
        <div style="overflow-x:auto;border:1px solid var(--bo);border-radius:7px">
          <table class="vtable">
            <thead><tr><th>#</th><th>Vaccine</th><th>Due Age</th><th>Date</th><th>Status</th></tr></thead>
            <tbody>{vrows}</tbody>
          </table>
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
""")

# ---- MODALS (unchanged) ----
for row in records:
    cv_id         = row[0]
    appt_date     = row[1]
    appt_time     = row[2]
    res_date      = row[3]
    res_time      = row[4]
    dose          = row[5] if row[5] else "1"
    child_name    = row[7]
    child_dob     = row[8]
    gender        = row[9]
    blood_group   = row[10]
    weight        = row[11]
    father_name   = row[12]
    mobile        = row[13]
    email         = row[14]
    parent_state  = row[15]
    parent_dist   = row[16]
    vaccine_name  = row[17]
    hospital_name = row[18]
    hosp_dist     = row[19]
    hosp_state    = row[20]

    display_date = res_date if res_date else appt_date
    display_time = res_time if res_time else appt_time

    rescheduled_block = ""
    if res_date:
        rescheduled_block = f"""
      <div class="info-box" style="background:#fff3e0;border-color:#ffcc80;">
        <div class="info-box-title" style="color:#e65100;"><i class="fa-solid fa-calendar-days"></i> Rescheduled Details</div>
        <div class="detail-grid">
          <div class="detail-item"><label>Rescheduled Date</label><span style="color:#e65100;font-weight:700;">{res_date}</span></div>
          <div class="detail-item"><label>Rescheduled Time</label><span style="color:#e65100;font-weight:700;">{res_time if res_time else 'N/A'}</span></div>
        </div>
      </div>"""

    print(f"""
<div class="modal-overlay" id="modal{cv_id}">
  <div class="modal-box">
    <div class="modal-head">
      <h4><i class="fa-solid fa-circle-check"></i> {child_name} &mdash; Completed Vaccination</h4>
      <button class="modal-close" onclick="closeModal('modal{cv_id}')">&#x2715;</button>
    </div>
    <div class="modal-body">
      <div class="info-box">
        <div class="info-box-title"><i class="fa-solid fa-syringe"></i> Vaccination Summary</div>
        <div class="detail-grid">
          <div class="detail-item"><label>Vaccine</label><span>{vaccine_name}</span></div>
          <div class="detail-item"><label>Dose</label><span>Dose {dose}</span></div>
          <div class="detail-item"><label>Original Date</label><span>{appt_date}</span></div>
          <div class="detail-item"><label>Original Time</label><span>{appt_time if appt_time else 'N/A'}</span></div>
          <div class="detail-item"><label>Hospital</label><span>{hospital_name}</span></div>
          <div class="detail-item"><label>Hospital District</label><span>{hosp_dist}, {hosp_state}</span></div>
        </div>
      </div>
      {rescheduled_block}
      <div class="modal-section-title"><i class="fa-solid fa-child"></i> Child Information</div>
      <div class="detail-grid">
        <div class="detail-item"><label>Child Name</label><span>{child_name}</span></div>
        <div class="detail-item"><label>Date of Birth</label><span>{child_dob}</span></div>
        <div class="detail-item"><label>Gender</label><span>{gender}</span></div>
        <div class="detail-item"><label>Blood Group</label><span>{blood_group}</span></div>
        <div class="detail-item"><label>Weight</label><span>{weight} kg</span></div>
      </div>
      <div class="modal-section-title"><i class="fa-solid fa-users"></i> Parent Information</div>
      <div class="detail-grid">
        <div class="detail-item"><label>Father Name</label><span>{father_name}</span></div>
        <div class="detail-item"><label>Mobile</label><span>{mobile}</span></div>
        <div class="detail-item"><label>Email</label><span>{email}</span></div>
        <div class="detail-item"><label>Location</label><span>{parent_dist}, {parent_state}</span></div>
      </div>
    </div>
  </div>
</div>
""")

print("""
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
  const titles={'sec-completed':'Completed Vaccinations','sec-children':'Child Details'};
  document.getElementById('page-title').textContent=titles[id]||'Completed Vaccinations';
  document.querySelectorAll('.nsub a').forEach(a=>a.classList.remove('active'));
  if(id==='sec-children'){
    document.getElementById('link-children').classList.add('active');
    document.querySelectorAll('.ng').forEach(x=>x.classList.remove('open'));
    document.getElementById('g5').classList.add('open');
  } else if(id==='sec-completed'){
    document.querySelectorAll('.ng').forEach(x=>x.classList.remove('open'));
    document.getElementById('g4').classList.add('open');
  }
  window.scrollTo(0,0);
  closeSB();
}

const allRows=document.querySelectorAll('#tableBody tr');
document.getElementById('rowCount').innerHTML='<i class="fa-solid fa-circle-check"></i> '+allRows.length+' Completed';

function filterTable(){
  const val=document.getElementById('searchInput').value.toLowerCase();
  let visible=0;
  document.querySelectorAll('#tableBody tr').forEach(row=>{
    const match=row.textContent.toLowerCase().includes(val);
    row.style.display=match?'':'none';
    if(match)visible++;
  });
  document.getElementById('rowCount').innerHTML='<i class="fa-solid fa-circle-check"></i> '+visible+' Completed';
}

function openModal(id){document.getElementById(id).classList.add('active');document.body.style.overflow='hidden';}
function closeModal(id){document.getElementById(id).classList.remove('active');document.body.style.overflow='';}
document.querySelectorAll('.modal-overlay').forEach(m=>{
  m.addEventListener('click',function(e){if(e.target===this)closeModal(this.id);});
});
document.addEventListener('keydown',e=>{
  if(e.key==='Escape')document.querySelectorAll('.modal-overlay.active').forEach(m=>closeModal(m.id));
});

function toggleCard(btn, bodyId){
  const body=document.getElementById(bodyId);
  const isOpen=body.classList.contains('open');
  body.classList.toggle('open',!isOpen);
  btn.innerHTML=isOpen
    ?'<i class="fa-solid fa-chevron-down"></i> View More'
    :'<i class="fa-solid fa-chevron-up"></i> View Less';
}

function filterCards(){
  const q=document.getElementById('childSearch').value.toLowerCase();
  const gf=document.getElementById('genderFilter').value.toLowerCase();
  const vf=document.getElementById('vacFilter').value.toLowerCase();
  const cards=document.querySelectorAll('.child-card');
  let visible=0;
  cards.forEach(c=>{
    const matchQ=!q||c.dataset.name.includes(q)||c.dataset.father.includes(q)||c.dataset.mobile.includes(q)||c.dataset.blood.includes(q);
    const matchG=!gf||c.dataset.gender===gf;
    const matchV=!vf||(c.dataset.vacstatus||'').includes(vf);
    const show=matchQ&&matchG&&matchV;
    c.style.display=show?'':'none';
    if(show)visible++;
  });
  document.getElementById('cntLbl').textContent=visible+' record'+(visible!==1?'s':'');
}
</script>
</body>
</html>
""")

con.close()