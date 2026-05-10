#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
import sys, cgi, cgitb, pymysql
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
print("content-type:text/html\r\n\r\n")
cgitb.enable()

con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()

def qc(sql):
    cur.execute(sql)
    return cur.fetchone()[0]

pending_parents    = qc("SELECT COUNT(*) FROM parent WHERE status='pending'")
approved_parents   = qc("SELECT COUNT(*) FROM parent WHERE status='approved'")
rejected_parents   = qc("SELECT COUNT(*) FROM parent WHERE status='rejected'")
total_parents      = qc("SELECT COUNT(*) FROM parent")
pending_hospitals  = qc("SELECT COUNT(*) FROM hospital WHERE status='pending'")
approved_hospitals = qc("SELECT COUNT(*) FROM hospital WHERE status='approved'")
rejected_hospitals = qc("SELECT COUNT(*) FROM hospital WHERE status='rejected'")
total_hospitals    = qc("SELECT COUNT(*) FROM hospital")
total_vaccines     = qc("SELECT COUNT(*) FROM vaccine WHERE status='confirmed'")
total_notified     = qc("SELECT COUNT(*) FROM child_vaccine WHERE status='notified'")
total_children     = qc("SELECT COUNT(*) FROM children")
vaccines_taken     = qc("SELECT COUNT(*) FROM child_vaccine WHERE status='taken'")
total_completed    = qc("SELECT COUNT(*) FROM child_vaccine WHERE status='completed'")
total_fb           = qc("SELECT COUNT(*) FROM feedback")
low_fb             = qc("SELECT COUNT(*) FROM feedback WHERE rating < 2")

# All children with parent info
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

# Vaccines per child
cur.execute("""
    SELECT cv.child_id, v.vaccine_name, v.minimum_age, cv.status, cv.taken_date
    FROM child_vaccine cv
    LEFT JOIN vaccine v ON cv.vaccine_id = v.vaccine_id
    ORDER BY v.minimum_age ASC
""")
vax_by_child = defaultdict(list)
for r in cur.fetchall():
    vax_by_child[r[0]].append({"name": r[1], "age": r[2], "status": r[3], "date": r[4]})

# Primary hospital per child
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

# ---- Cross-hospital history for ALL children ----
child_ids_all = [r[0] for r in children_raw]
cross_hosp_by_child = defaultdict(list)

if child_ids_all:
    fmt = ','.join(['%s'] * len(child_ids_all))
    cur.execute(f"""
        SELECT
            cv.child_id,
            v.dose_number,
            v.vaccine_name,
            h.hospital_name,
            h.address,
            cv.taken_date,
            cv.appointment_date,
            cv.status
        FROM child_vaccine cv
        LEFT JOIN vaccine  v ON cv.vaccine_id  = v.vaccine_id
        LEFT JOIN hospital h ON cv.hospital_id = h.hospital_id
        WHERE cv.child_id IN ({fmt})
          AND h.hospital_id IS NOT NULL
          AND LOWER(TRIM(cv.status)) IN ('completed','confirmed','taken')
        ORDER BY cv.child_id ASC, v.dose_number ASC
    """, child_ids_all)

    for r in cur.fetchall():
        cid_r      = r[0]
        date_given = str(r[5]) if r[5] else (str(r[6]) if r[6] else "-")
        cross_hosp_by_child[cid_r].append({
            "dose_number"  : r[1] if r[1] else "-",
            "vaccine_name" : r[2] if r[2] else "Unknown",
            "hospital_name": r[3] if r[3] else "Unknown Hospital",
            "address"      : r[4] if r[4] else "Address not available",
            "date_given"   : date_given,
            "status"       : r[7] if r[7] else "-",
        })

# Recent registrations
cur.execute("""
    SELECT p.father_name, c.child_name, p.mobile_number, p.status
    FROM parent p
    LEFT JOIN children c ON p.parent_id = c.parent_id
    ORDER BY p.parent_id DESC LIMIT 5
""")
recent = cur.fetchall()

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

print("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Admin Dashboard</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
:root{
  --p:#1565c0;--pd:#0d47a1;--pl:#e3f2fd;--ac:#ff6f00;
  --sw:260px;--hh:60px;--tx:#1c1c1c;--mu:#6b7280;
  --bg:#f0f4f8;--ca:#fff;--bo:#dde3ea;
  --da:#e53935;--su:#2e7d32;
  --ra:10px;--sh:0 2px 16px rgba(0,0,0,.09);
  --tr:.25s ease;--fn:'Segoe UI',Arial,sans-serif
}
html{scroll-behavior:smooth}
body{font-family:var(--fn);background:var(--bg);color:var(--tx);min-height:100vh;line-height:1.6}
a{text-decoration:none;color:inherit}
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1100}
.overlay.active{display:block}
.sidebar{width:var(--sw);height:100vh;position:fixed;top:0;left:0;
  background:linear-gradient(180deg,#0d2a6e 0%,#1565c0 60%,#0d47a1 100%);
  display:flex;flex-direction:column;z-index:1200;
  overflow-y:auto;overflow-x:hidden;transition:transform var(--tr);
  scrollbar-width:thin;scrollbar-color:rgba(255,255,255,.2) transparent}
.sidebar::-webkit-scrollbar{width:4px}
.sidebar::-webkit-scrollbar-thumb{background:rgba(255,255,255,.2);border-radius:2px}
.sbrand{display:flex;align-items:center;gap:12px;padding:18px 16px 14px;border-bottom:1px solid rgba(255,255,255,.15)}
.sbrand img{width:42px;height:42px;border-radius:50%;border:2px solid rgba(255,255,255,.4);flex-shrink:0}
.sbrand span{font-size:.95rem;font-weight:700;color:#fff;line-height:1.3}
.sbrand small{display:block;font-size:.72rem;color:rgba(255,255,255,.6);font-weight:400}
.snav{flex:1;padding:10px 0}
.ng{border-bottom:1px solid rgba(255,255,255,.07)}
.ngt{width:100%;background:transparent;border:none;cursor:pointer;display:flex;align-items:center;gap:10px;padding:13px 16px;color:rgba(255,255,255,.88);font-size:.88rem;font-weight:500;font-family:var(--fn);transition:background var(--tr),color var(--tr);text-align:left}
.ngt:hover,.ng.open .ngt{background:rgba(255,255,255,.1);color:#fff}
.ngt .ic{font-size:.95rem;width:20px;text-align:center;flex-shrink:0}
.ngt .ar{margin-left:auto;font-size:.68rem;transition:transform var(--tr);flex-shrink:0}
.ng.open .ngt .ar{transform:rotate(180deg)}
.nsub{max-height:0;overflow:hidden;transition:max-height .35s ease;background:rgba(0,0,0,.15)}
.ng.open .nsub{max-height:400px}
.nsub a{display:flex;align-items:center;gap:8px;padding:9px 16px 9px 48px;color:rgba(255,255,255,.72);font-size:.83rem;transition:background var(--tr),color var(--tr);border-left:3px solid transparent;cursor:pointer}
.nsub a:hover,.nsub a.active{background:rgba(255,255,255,.1);color:#fff;border-left-color:var(--ac)}
.nbadge{background:#e53935;color:#fff;font-size:.67rem;font-weight:700;min-width:18px;height:18px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;padding:0 5px}
.nbadge.or{background:var(--ac)}.nbadge.gr{background:#2e7d32}.nbadge.gy{background:#777}.nbadge.te{background:#00838f}
.sfooter{padding:14px 12px;border-top:1px solid rgba(255,255,255,.12)}
.btn-logout{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:10px;background:var(--da);color:#fff;border:none;border-radius:var(--ra);font-size:.88rem;font-weight:600;font-family:var(--fn);cursor:pointer;text-decoration:none;transition:background var(--tr)}
.btn-logout:hover{background:#b71c1c}
.mwrap{margin-left:var(--sw);display:flex;flex-direction:column;min-height:100vh}
.topbar{height:var(--hh);background:var(--ca);border-bottom:1px solid var(--bo);position:sticky;top:0;z-index:900;display:flex;align-items:center;justify-content:space-between;padding:0 20px;box-shadow:0 1px 8px rgba(0,0,0,.06)}
.tbl{display:flex;align-items:center;gap:12px}
.ttitle{font-size:1rem;font-weight:700;color:var(--p)}
.hamburger{display:none;flex-direction:column;gap:5px;background:transparent;border:none;cursor:pointer;padding:6px;border-radius:6px}
.hamburger span{display:block;width:22px;height:2px;background:var(--tx);border-radius:2px;transition:transform var(--tr),opacity var(--tr)}
.hamburger.open span:nth-child(1){transform:translateY(7px) rotate(45deg)}
.hamburger.open span:nth-child(2){opacity:0}
.hamburger.open span:nth-child(3){transform:translateY(-7px) rotate(-45deg)}
.tbr{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.abadge{background:var(--pl);color:var(--p);padding:5px 14px;border-radius:20px;font-size:.82rem;font-weight:600}
.talert{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:20px;font-size:.78rem;font-weight:700}
.talert.pa{background:#fff3e0;color:#e65100}
.talert.ho{background:#e8f5e9;color:#2e7d32}
.pc{padding:24px 20px;flex:1}
.section{display:none}.section.active{display:block}
.wbanner{background:linear-gradient(120deg,var(--p),var(--pd));color:#fff;border-radius:var(--ra);padding:28px 32px;margin-bottom:24px;position:relative;overflow:hidden}
.wbanner::after{content:'';position:absolute;right:-40px;top:-40px;width:200px;height:200px;background:rgba(255,255,255,.06);border-radius:50%}
.wbanner h2{font-size:clamp(1.1rem,2.5vw,1.5rem);margin-bottom:6px}
.wbanner p{font-size:.88rem;opacity:.8}
.sgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:16px;margin-bottom:24px}
.scard{background:var(--ca);border-radius:var(--ra);padding:18px 16px;display:flex;align-items:center;gap:14px;box-shadow:var(--sh);border:1px solid var(--bo);transition:transform var(--tr)}
.scard:hover{transform:translateY(-3px)}
.si{width:46px;height:46px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.15rem;flex-shrink:0}
.si.bl{background:#e3f2fd;color:#1565c0}.si.gr{background:#e8f5e9;color:#2e7d32}
.si.or{background:#fff3e0;color:#e65100}.si.re{background:#ffebee;color:#b71c1c}
.si.pu{background:#f3e5f5;color:#6a1b9a}.si.te{background:#e0f7fa;color:#00838f}
.si.ye{background:#fff8e1;color:#f57f17}
.sinfo h3{font-size:1.35rem;font-weight:700;line-height:1}
.sinfo p{font-size:.76rem;color:var(--mu);margin-top:4px}
.stitle{font-size:1rem;font-weight:700;color:var(--p);margin-bottom:14px;display:flex;align-items:center;gap:8px}
.stitle::before{content:'';display:inline-block;width:4px;height:18px;background:var(--ac);border-radius:2px}
.agrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:14px;margin-bottom:24px}
.abtn{background:var(--ca);border:1px solid var(--bo);border-radius:var(--ra);padding:18px 14px;text-align:center;display:block;color:var(--tx);transition:background var(--tr),transform var(--tr);cursor:pointer}
.abtn:hover{background:var(--pl);border-color:var(--p);transform:translateY(-2px)}
.abtn i{font-size:1.5rem;color:var(--p);margin-bottom:10px}
.abtn span{display:block;font-size:.82rem;font-weight:600}
.tcard{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);overflow:hidden;margin-bottom:24px}
.thdiv{padding:14px 20px;border-bottom:1px solid var(--bo);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}
.tht{font-weight:700;font-size:.92rem;display:flex;align-items:center;gap:8px}
.tw{width:100%;overflow-x:auto}
table{width:100%;border-collapse:collapse;min-width:500px}
thead{background:var(--p);color:#fff}
th,td{padding:11px 14px;text-align:left;font-size:.86rem;border-bottom:1px solid var(--bo);white-space:nowrap}
tbody tr:hover{background:var(--pl)}
tbody tr:last-child td{border-bottom:none}
.bx{display:inline-flex;align-items:center;padding:3px 10px;border-radius:20px;font-size:.74rem;font-weight:700}
.bp{background:#fff8e1;color:#f57f17}.ba{background:#e8f5e9;color:#2e7d32}
.br{background:#ffebee;color:#c62828}.bn{background:#fff3e0;color:#e65100}
.bt{background:#e8f5e9;color:#2e7d32}.bgy{background:#f3f4f6;color:#555}
.page-hdr{background:linear-gradient(120deg,var(--p),var(--pd));color:#fff;border-radius:var(--ra);padding:22px 28px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
.page-hdr h2{font-size:1.1rem;font-weight:700;margin-bottom:3px}
.page-hdr p{font-size:.83rem;opacity:.8}
.page-hdr-badge{background:rgba(255,255,255,.18);padding:7px 16px;border-radius:20px;font-size:.83rem;font-weight:700}
.toolbar{display:flex;align-items:center;gap:12px;margin-bottom:18px;flex-wrap:wrap}
.sbox{position:relative;flex:1;min-width:200px}
.sbox i{position:absolute;left:11px;top:50%;transform:translateY(-50%);color:var(--mu);font-size:.82rem}
.sbox input{width:100%;padding:9px 12px 9px 34px;border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.85rem;background:var(--ca)}
.sbox input:focus{outline:none;border-color:var(--p)}
.fsel{padding:9px 14px;border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.85rem;background:var(--ca);color:var(--tx);cursor:pointer}
.fsel:focus{outline:none;border-color:var(--p)}
.cnt-lbl{font-size:.84rem;color:var(--mu);font-weight:600;white-space:nowrap}
.child-card{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);margin-bottom:16px;overflow:hidden}
.ccard-top{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;flex-wrap:wrap;gap:10px}
.ccard-left{display:flex;align-items:center;gap:14px}
.avatar{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--p),var(--pd));border:2px solid var(--pl);display:flex;align-items:center;justify-content:center;font-size:1.15rem;font-weight:800;color:#fff;flex-shrink:0}
.ccard-name{font-size:.96rem;font-weight:700;color:var(--tx)}
.ccard-sub{font-size:.76rem;color:var(--mu);margin-top:2px}
.ccard-right{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.btn-viewmore{display:inline-flex;align-items:center;gap:6px;padding:7px 16px;background:var(--p);color:#fff;border:none;border-radius:8px;font-size:.82rem;font-weight:600;font-family:var(--fn);cursor:pointer;transition:background var(--tr)}
.btn-viewmore:hover{background:var(--pd)}
.btn-viewmore .vm-icon{transition:transform var(--tr)}
.btn-viewmore.open .vm-icon{transform:rotate(180deg)}
.ccard-details{display:none;border-top:1px solid var(--bo)}
.ccard-details.open{display:block}
.detail-tabs{display:flex;border-bottom:2px solid var(--bo);background:#fafbfc}
.dtab{flex:1;background:transparent;border:none;border-bottom:3px solid transparent;margin-bottom:-2px;padding:11px 10px;font-family:var(--fn);font-size:.83rem;font-weight:600;color:var(--mu);cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;transition:color var(--tr),border-color var(--tr),background var(--tr);white-space:nowrap}
.dtab:hover{color:var(--p);background:var(--pl)}
.dtab.active{color:var(--p);border-bottom-color:var(--ac);background:#f0f7ff}
.dpanel{display:none;padding:18px 20px}
.dpanel.active{display:block}
.dg{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px 20px;margin-bottom:4px}
.di{background:var(--bg);border:1px solid var(--bo);border-radius:8px;padding:9px 13px}
.di label{display:block;font-size:.67rem;color:var(--mu);font-weight:700;text-transform:uppercase;letter-spacing:.4px;margin-bottom:3px}
.di span{font-size:.86rem;font-weight:600;color:var(--tx);word-break:break-word}
.di.full{grid-column:1/-1}
.vsumbadges{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.vsb{display:flex;align-items:center;gap:5px;padding:5px 14px;border-radius:20px;font-size:.76rem;font-weight:700}
.vsb.tk{background:#e8f5e9;color:#2e7d32}
.vsb.nt{background:#fff3e0;color:#e65100}
.vsb.pd{background:#fff8e1;color:#f57f17}
.vtable{width:100%;border-collapse:collapse;font-size:.83rem}
.vtable th{background:#f0f4f8;color:var(--p);padding:8px 12px;text-align:left;font-size:.74rem;font-weight:700;text-transform:uppercase;border-bottom:2px solid var(--bo)}
.vtable td{padding:8px 12px;border-bottom:1px solid var(--bo)}
.vtable tbody tr:hover{background:var(--pl)}
.vtable tbody tr:last-child td{border-bottom:none}
.empty{text-align:center;padding:60px 20px;color:var(--mu)}
.empty i{font-size:3rem;opacity:.3;display:block;margin-bottom:14px}

/* ---- Cross-hospital tab styles ---- */
.ch-alert{background:#fff3e0;border-left:4px solid #e65100;border-radius:6px;padding:9px 13px;font-size:.82rem;color:#7c4700;display:flex;align-items:flex-start;gap:8px;margin-bottom:12px;line-height:1.5}
.ch-alert i{margin-top:2px;flex-shrink:0}
.ch-table{width:100%;border-collapse:collapse;font-size:.82rem}
.ch-table thead th{background:#ffe0b2;color:#bf360c;padding:7px 10px;font-size:.71rem;font-weight:700;text-transform:uppercase;letter-spacing:.4px;border-bottom:2px solid #ffcc80;white-space:nowrap}
.ch-table tbody td{padding:8px 10px;border-bottom:1px solid #ffe082;vertical-align:top}
.ch-table tbody tr:last-child td{border-bottom:none}
.ch-table tbody tr:hover{background:#fff3e0}
.ch-hosp{font-weight:600;color:#bf360c;font-size:.83rem}
.ch-addr{font-size:.76rem;color:#64748b;margin-top:2px}
.no-ch{text-align:center;padding:14px 0;font-size:.83rem;color:#94a3b8}
.badge-cross{background:#fff3e0;color:#e65100;padding:2px 9px;border-radius:20px;font-size:.72rem;font-weight:700}
/* ---- end cross-hospital ---- */

footer{background:#1c1c2e;color:rgba(255,255,255,.6);text-align:center;padding:14px 20px;font-size:.8rem}
@media(max-width:768px){
  .sidebar{transform:translateX(-100%)}.sidebar.open{transform:translateX(0)}
  .mwrap{margin-left:0}.hamburger{display:flex}.abadge{display:none}
  .detail-tabs{overflow-x:auto}
}
@media(max-width:480px){
  .sgrid{grid-template-columns:1fr 1fr}.agrid{grid-template-columns:repeat(2,1fr)}
  .talert span{display:none}.pc{padding:14px 12px}
  .dg{grid-template-columns:1fr 1fr}
}
</style>
</head>
<body>
<div class="overlay" id="overlay"></div>
""")

print(f"""
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
        <i class="fa-solid fa-star ic"></i> Feedback
        {nb(low_fb) if low_fb else ""}
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
      <span class="ttitle" id="page-title">Admin Dashboard</span>
    </div>
    <div class="tbr">
      {tp}{th_alert}
      <span class="abadge"><i class="fa-solid fa-shield-halved"></i> Admin</span>
    </div>
  </header>
  <main class="pc">
""")

# ======================================================
# SECTION 1 — DASHBOARD
# ======================================================
print(f"""
<div class="section active" id="sec-dashboard">
  <div class="wbanner">
    <div>
      <h2>Welcome, Administrator &#128075;</h2>
      <p>Manage parents, hospitals, vaccinations and notifications from this panel.</p>
    </div>
  </div>
  <div class="sgrid">
    <div class="scard"><div class="si bl"><i class="fa-solid fa-user-group"></i></div><div class="sinfo"><h3>{total_parents}</h3><p>Total Parents</p></div></div>
    <div class="scard"><div class="si or"><i class="fa-solid fa-user-clock"></i></div><div class="sinfo"><h3>{pending_parents}</h3><p>Pending Parents</p></div></div>
    <div class="scard"><div class="si gr"><i class="fa-solid fa-hospital"></i></div><div class="sinfo"><h3>{total_hospitals}</h3><p>Total Hospitals</p></div></div>
    <div class="scard"><div class="si or"><i class="fa-solid fa-hospital-user"></i></div><div class="sinfo"><h3>{pending_hospitals}</h3><p>Pending Hospitals</p></div></div>
    <div class="scard"><div class="si re"><i class="fa-solid fa-syringe"></i></div><div class="sinfo"><h3>{total_vaccines}</h3><p>Vaccines</p></div></div>
    <div class="scard"><div class="si pu"><i class="fa-solid fa-child"></i></div><div class="sinfo"><h3>{total_children}</h3><p>Children</p></div></div>
    <div class="scard"><div class="si gr"><i class="fa-solid fa-circle-check"></i></div><div class="sinfo"><h3>{total_completed}</h3><p>Completed</p></div></div>
    <div class="scard"><div class="si ye"><i class="fa-solid fa-star"></i></div><div class="sinfo"><h3>{total_fb}</h3><p>Total Feedback</p></div></div>
  </div>
  <p class="stitle">Quick Actions</p>
  <div class="agrid">
    <a href="adminpendingparent.py"      class="abtn"><i class="fa-solid fa-user-clock"></i><span>Pending Parents</span></a>
    <a href="adminpendingmanager.py"     class="abtn"><i class="fa-solid fa-hospital-user"></i><span>Pending Managers</span></a>
    <a href="adminaddvaccine.py"         class="abtn"><i class="fa-solid fa-plus-circle"></i><span>Add Vaccine</span></a>
    <a href="adminnotification.py"       class="abtn"><i class="fa-solid fa-paper-plane"></i><span>Send Notification</span></a>
    <a href="adminviewvaccine.py"        class="abtn"><i class="fa-solid fa-list"></i><span>View Vaccines</span></a>
    <a href="admincompletedvaccine.py"   class="abtn"><i class="fa-solid fa-circle-check"></i><span>Completed Vaccines</span></a>
    <a onclick="showSection('sec-children')" class="abtn"><i class="fa-solid fa-child-reaching"></i><span>View Children</span></a>
    <a href="adminfeedback.py"           class="abtn"><i class="fa-solid fa-star"></i><span>View Feedback</span></a>
  </div>
  <p class="stitle">Recent Parent Registrations</p>
  <div class="tcard">
    <div class="thdiv"><span class="tht"><i class="fa-solid fa-clock-rotate-left"></i>&nbsp; Latest Requests</span></div>
    <div class="tw"><table>
      <thead><tr><th>#</th><th>Father Name</th><th>Child Name</th><th>Contact</th><th>Status</th></tr></thead>
      <tbody>
""")
if recent:
    for i, r in enumerate(recent, 1):
        cn = r[1] or "&mdash;"
        s  = r[3]
        bc = {"pending":"bp","approved":"ba","rejected":"br"}.get(s,"bp")
        print(f"<tr><td>{i}</td><td><strong>{r[0]}</strong></td><td>{cn}</td>"
              f"<td>{r[2]}</td><td><span class='bx {bc}'>{s.capitalize()}</span></td></tr>")
else:
    print("<tr><td colspan='5' style='text-align:center;color:#aaa;padding:20px'>No registrations yet.</td></tr>")

print("""
      </tbody>
    </table></div>
  </div>
</div>
""")

# ======================================================
# SECTION 2 — CHILDREN DETAILS (with cross-hospital tab)
# ======================================================
print(f"""
<div class="section" id="sec-children">
  <div class="page-hdr">
    <div>
      <h2><i class="fa-solid fa-children"></i>&nbsp; Registered Children</h2>
      <p>Click <strong>View More</strong> on any child — the <strong>Other Hosp. Doses</strong> tab shows cross-hospital vaccine history</p>
    </div>
    <span class="page-hdr-badge"><i class="fa-solid fa-child"></i> {total_children} Total</span>
  </div>
  <div class="toolbar">
    <div class="sbox">
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

        vaccines     = vax_by_child.get(cid, [])
        v_total      = len(vaccines)
        v_taken      = sum(1 for v in vaccines if v["status"]=="taken")
        v_notified   = sum(1 for v in vaccines if v["status"]=="notified")
        v_pending    = v_total - v_taken - v_notified
        vac_statuses = " ".join(set(v["status"] or "pending" for v in vaccines)) if vaccines else "pending"

        h    = hosp_by_child.get(cid, {})
        hn   = h.get("name",     "Not assigned yet")
        hnum = h.get("number",   "&mdash;")
        hst  = h.get("state",    "&mdash;")
        hdi  = h.get("district", "&mdash;")

        # vaccine tab rows
        vrows = ""
        for idx, v in enumerate(vaccines, 1):
            vs = v["status"] or "pending"
            vd = v["date"]   or "&mdash;"
            bc = "bt" if vs=="taken" else ("bn" if vs=="notified" else "bp")
            vrows += (f"<tr><td>{idx}</td><td><strong>{v['name']}</strong></td>"
                      f"<td>{v['age']} mo.</td><td>{vd}</td>"
                      f"<td><span class='bx {bc}'>{vs.capitalize()}</span></td></tr>")
        if not vrows:
            vrows = "<tr><td colspan='5' style='text-align:center;color:#bbb;padding:14px'>No vaccines assigned yet</td></tr>"

        # cross-hospital tab
        cross_doses = cross_hosp_by_child.get(cid, [])
        cross_count = len(cross_doses)

        if cross_doses:
            hosp_groups = {}
            for d in cross_doses:
                hosp_groups.setdefault(d["hospital_name"], 0)
                hosp_groups[d["hospital_name"]] += 1

            ch_alert = (
                f'<div class="ch-alert">'
                f'<i class="fa-solid fa-triangle-exclamation"></i>'
                f'<span>This child has <strong>{cross_count} dose(s)</strong> administered at '
                f'<strong>{len(hosp_groups)} other hospital(s)</strong>. '
                f'Full details are shown below.</span>'
                f'</div>'
            )
            ch_rows = ""
            for d in cross_doses:
                ch_rows += (
                    f"<tr>"
                    f"<td><span class='bx bn'>Dose {d['dose_number']}</span></td>"
                    f"<td><strong>{d['vaccine_name']}</strong></td>"
                    f"<td>"
                    f"<div class='ch-hosp'><i class='fa-solid fa-hospital' style='font-size:.78rem;margin-right:5px;'></i>{d['hospital_name']}</div>"
                    f"<div class='ch-addr'><i class='fa-solid fa-location-dot' style='font-size:.74rem;margin-right:4px;'></i>{d['address']}</div>"
                    f"</td>"
                    f"<td>{d['date_given']}</td>"
                    f"<td><span class='bx bt'>{d['status'].capitalize()}</span></td>"
                    f"</tr>"
                )
            cross_tab_html = f"""
            {ch_alert}
            <div style="overflow-x:auto;border:1px solid #ffe082;border-radius:8px;">
              <table class="ch-table">
                <thead>
                  <tr>
                    <th>Dose No.</th>
                    <th>Vaccine</th>
                    <th>Hospital Name &amp; Address</th>
                    <th>Date Given</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>{ch_rows}</tbody>
              </table>
            </div>"""
            cross_badge = (f'&nbsp;<span class="badge-cross">'
                           f'<i class="fa-solid fa-hospital" style="font-size:.68rem;"></i>'
                           f' {cross_count} other hosp.</span>')
            cross_tab_label = (f'<i class="fa-solid fa-code-branch"></i> Other Hosp. Doses'
                               f'<span class="badge-cross" style="margin-left:4px;">{cross_count}</span>')
            cross_tab_style = 'color:#e65100;'
        else:
            cross_tab_html  = '<div class="no-ch"><i class="fa-solid fa-circle-check" style="color:#1d9e75;margin-right:6px;"></i>No doses from other hospitals recorded for this child.</div>'
            cross_badge     = ""
            cross_tab_label = '<i class="fa-solid fa-code-branch"></i> Other Hosp. Doses'
            cross_tab_style = ''

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
        <div class="avatar">{initial}</div>
        <div>
          <div class="ccard-name">
            <i class="fa-solid {gicon}" style="font-size:.85rem;opacity:.7"></i>&nbsp;{cname}
            {cross_badge}
          </div>
          <div class="ccard-sub">
            DOB: {dob} &bull; Blood: {blood} &bull; {weight} kg &bull; {gender}
          </div>
        </div>
      </div>
      <div class="ccard-right">
        <span class="bx bgy"><i class="fa-solid fa-syringe"></i>&nbsp; {v_total} Vaccines</span>
        <span class="bx {pbc}">Parent: {pstatus.capitalize()}</span>
        <button class="btn-viewmore" onclick="toggleDetails(this,'det{cid}')">
          <i class="fa-solid fa-chevron-down vm-icon"></i> View More
        </button>
      </div>
    </div>

    <div class="ccard-details" id="det{cid}">
      <div class="detail-tabs" id="tabs{cid}">
        <button class="dtab active" onclick="switchDTab({cid},'parent')">
          <i class="fa-solid fa-users"></i> Parent
        </button>
        <button class="dtab" onclick="switchDTab({cid},'vaccine')">
          <i class="fa-solid fa-syringe"></i> Vaccine
        </button>
        <button class="dtab" onclick="switchDTab({cid},'hospital')">
          <i class="fa-solid fa-hospital"></i> Hospital
        </button>
        <button class="dtab" onclick="switchDTab({cid},'crosshosp')" style="{cross_tab_style}">
          {cross_tab_label}
        </button>
      </div>

      <div class="dpanel active" id="dp{cid}-parent">
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

      <div class="dpanel" id="dp{cid}-vaccine">
        <div class="vsumbadges">
          <span class="vsb tk"><i class="fa-solid fa-check-circle"></i> {v_taken} Taken</span>
          <span class="vsb nt"><i class="fa-solid fa-bell"></i> {v_notified} Notified</span>
          <span class="vsb pd"><i class="fa-solid fa-clock"></i> {v_pending} Pending</span>
        </div>
        <div style="overflow-x:auto;border:1px solid var(--bo);border-radius:8px">
          <table class="vtable">
            <thead><tr><th>#</th><th>Vaccine Name</th><th>Due Age</th><th>Date Taken</th><th>Status</th></tr></thead>
            <tbody>{vrows}</tbody>
          </table>
        </div>
      </div>

      <div class="dpanel" id="dp{cid}-hospital">
        <div class="dg">
          <div class="di"><label>Current Hospital</label><span>{hn}</span></div>
          <div class="di"><label>Contact Number</label><span>{hnum}</span></div>
          <div class="di"><label>State</label><span>{hst}</span></div>
          <div class="di"><label>District</label><span>{hdi}</span></div>
        </div>
      </div>

      <div class="dpanel" id="dp{cid}-crosshosp">
        {cross_tab_html}
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
  const titles={'sec-dashboard':'Admin Dashboard','sec-children':'Child Details'};
  document.getElementById('page-title').textContent=titles[id]||'Admin Dashboard';
  document.querySelectorAll('.nsub a').forEach(a=>a.classList.remove('active'));
  if(id==='sec-children'){
    document.getElementById('link-children').classList.add('active');
    document.querySelectorAll('.ng').forEach(x=>x.classList.remove('open'));
    document.getElementById('g5').classList.add('open');
  }
  window.scrollTo(0,0);
  closeSB();
}

const pn=window.location.pathname.split('/').pop();
document.querySelectorAll('.nsub a[href]').forEach(a=>{
  if(a.getAttribute('href')===pn){a.classList.add('active');a.closest('.ng').classList.add('open');}
});

function toggleDetails(btn,detId){
  const det=document.getElementById(detId);
  const isOpen=det.classList.contains('open');
  det.classList.toggle('open',!isOpen);
  btn.classList.toggle('open',!isOpen);
  btn.innerHTML=isOpen
    ?'<i class="fa-solid fa-chevron-down vm-icon"></i> View More'
    :'<i class="fa-solid fa-chevron-up vm-icon open"></i> View Less';
}

function switchDTab(cid,tabName){
  const panels=['parent','vaccine','hospital','crosshosp'];
  const btns=document.getElementById('tabs'+cid).querySelectorAll('.dtab');
  panels.forEach((p,i)=>{
    const el=document.getElementById('dp'+cid+'-'+p);
    if(el)el.classList.toggle('active',p===tabName);
    if(btns[i])btns[i].classList.toggle('active',p===tabName);
  });
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