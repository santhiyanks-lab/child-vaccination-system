#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
import sys, cgi, cgitb, pymysql
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
print("content-type:text/html\r\n\r\n")
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

# Handle form submission
msg = ""
msg_type = ""
if form.getvalue("vaccine_name"):
    try:
        vname   = form.getvalue("vaccine_name", "").strip()
        vdesc   = form.getvalue("description", "").strip()
        vage    = form.getvalue("minimum_age", "0").strip()
        vdose   = form.getvalue("doses", "1").strip()
        vstatus = "confirmed"
        cur.execute(
            "INSERT INTO vaccine (vaccine_name, description, minimum_age, doses, status) VALUES (%s,%s,%s,%s,%s)",
            (vname, vdesc, vage, vdose, vstatus)
        )
        con.commit()
        msg = f"Vaccine '<strong>{vname}</strong>' added successfully!"
        msg_type = "success"
        total_vaccines = qc("SELECT COUNT(*) FROM vaccine WHERE status='confirmed'")
    except Exception as e:
        con.rollback()
        msg = f"Error adding vaccine: {e}"
        msg_type = "error"

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
<title>Add Vaccine</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
:root{
  --p:#1565c0;--pd:#0d47a1;--pl:#e3f2fd;--ac:#ff6f00;
  --sw:260px;--hh:60px;--tx:#1c1c1c;--mu:#6b7280;
  --bg:#f0f4f8;--ca:#fff;--bo:#dde3ea;
  --da:#e53935;--su:#2e7d32;--sl:#e8f5e9;
  --ra:10px;--sh:0 2px 16px rgba(0,0,0,.09);
  --tr:.25s ease;--fn:'Segoe UI',Arial,sans-serif
}
html{scroll-behavior:smooth}
body{font-family:var(--fn);background:var(--bg);color:var(--tx);min-height:100vh;line-height:1.6}
a{text-decoration:none;color:inherit}
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1100}
.overlay.active{display:block}

/* ===== SIDEBAR ===== */
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

/* ===== MAIN ===== */
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

/* ===== ADD VACCINE SECTION ===== */
.av-banner{background:linear-gradient(120deg,var(--p),var(--pd));color:#fff;border-radius:var(--ra);padding:22px 28px;margin-bottom:24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;position:relative;overflow:hidden}
.av-banner::after{content:'';position:absolute;right:-40px;top:-40px;width:180px;height:180px;background:rgba(255,255,255,.06);border-radius:50%}
.av-banner h2{font-size:1.1rem;font-weight:700;margin-bottom:4px}
.av-banner p{font-size:.83rem;opacity:.8}
.av-banner-badge{background:rgba(255,255,255,.18);padding:7px 16px;border-radius:20px;font-size:.83rem;font-weight:700;white-space:nowrap}
.form-card{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);overflow:hidden;margin-bottom:24px}
.form-card-head{background:linear-gradient(90deg,var(--p),var(--pd));color:#fff;padding:14px 20px;display:flex;align-items:center;gap:10px;font-size:.95rem;font-weight:700}
.form-body{padding:28px 24px}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.form-group{display:flex;flex-direction:column;gap:6px}
.form-group.full{grid-column:1/-1}
.form-group label{font-size:.78rem;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:.4px}
.form-group label span{color:var(--da)}
.form-group input,.form-group select,.form-group textarea{
  padding:10px 14px;border:1.5px solid var(--bo);border-radius:8px;
  font-family:var(--fn);font-size:.9rem;background:var(--ca);color:var(--tx);
  transition:border-color var(--tr),box-shadow var(--tr)}
.form-group input:focus,.form-group select:focus,.form-group textarea:focus{
  outline:none;border-color:var(--p);box-shadow:0 0 0 3px rgba(21,101,192,.1)}
.form-group textarea{resize:vertical;min-height:90px}
.form-actions{display:flex;align-items:center;gap:12px;padding:18px 24px;border-top:1px solid var(--bo);background:#fafbfc;flex-wrap:wrap}
.btn-submit{display:inline-flex;align-items:center;gap:8px;padding:10px 28px;background:var(--p);color:#fff;border:none;border-radius:8px;font-family:var(--fn);font-size:.9rem;font-weight:700;cursor:pointer;transition:background var(--tr)}
.btn-submit:hover{background:var(--pd)}
.btn-reset{display:inline-flex;align-items:center;gap:8px;padding:10px 22px;background:var(--bg);color:var(--mu);border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.9rem;font-weight:600;cursor:pointer;transition:background var(--tr)}
.btn-reset:hover{background:var(--bo)}
.alert{display:flex;align-items:center;gap:10px;padding:12px 18px;border-radius:8px;margin-bottom:20px;font-size:.88rem;font-weight:600}
.alert.success{background:var(--sl);color:var(--su);border:1px solid #a5d6a7}
.alert.error{background:#ffebee;color:#c62828;border:1px solid #ef9a9a}
.alert i{font-size:1rem;flex-shrink:0}
.stats-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:14px;margin-bottom:24px}
.stat-card{background:var(--ca);border-radius:var(--ra);padding:16px;display:flex;align-items:center;gap:12px;box-shadow:var(--sh);border:1px solid var(--bo)}
.stat-icon{width:42px;height:42px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;flex-shrink:0}
.stat-icon.re{background:#ffebee;color:#b71c1c}
.stat-icon.gr{background:#e8f5e9;color:#2e7d32}
.stat-icon.bl{background:#e3f2fd;color:#1565c0}
.stat-info h3{font-size:1.25rem;font-weight:700;line-height:1}
.stat-info p{font-size:.74rem;color:var(--mu);margin-top:3px}

/* ===== CHILDREN SECTION ===== */
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

/* ===== CHILD CARD ===== */
.child-card{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);margin-bottom:16px;overflow:hidden}
.ccard-head{background:linear-gradient(90deg,var(--p),var(--pd));color:#fff;padding:14px 20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}
.ccard-left{display:flex;align-items:center;gap:14px}
.avatar{width:44px;height:44px;border-radius:50%;background:rgba(255,255,255,.2);border:2px solid rgba(255,255,255,.4);display:flex;align-items:center;justify-content:center;font-size:1.15rem;font-weight:800;color:#fff;flex-shrink:0}
.ccard-name{font-size:.96rem;font-weight:700}
.ccard-sub{font-size:.75rem;opacity:.8;margin-top:2px}
.ccard-right{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.btn-vm{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;background:rgba(255,255,255,.18);color:#fff;border:1px solid rgba(255,255,255,.35);border-radius:7px;font-size:.81rem;font-weight:600;font-family:var(--fn);cursor:pointer;transition:background var(--tr)}
.btn-vm:hover{background:rgba(255,255,255,.3)}
.btn-vm .vmi{transition:transform var(--tr)}
.btn-vm.open .vmi{transform:rotate(180deg)}
.ccard-body{display:none;grid-template-columns:1fr 1fr 1fr;border-top:1px solid var(--bo)}
.ccard-body.open{display:grid}
.csec{padding:16px 18px;border-right:1px solid var(--bo)}
.csec:last-child{border-right:none}
.csec-title{font-size:.71rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--p);margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid var(--pl);display:flex;align-items:center;gap:6px}
.dg{display:grid;grid-template-columns:1fr 1fr;gap:7px 14px}
.di label{display:block;font-size:.67rem;color:var(--mu);font-weight:700;text-transform:uppercase;letter-spacing:.4px;margin-bottom:2px}
.di span{font-size:.84rem;font-weight:600;color:var(--tx);word-break:break-word}
.di.full{grid-column:1/-1}
.vsumbadges{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.vsb{display:flex;align-items:center;gap:4px;padding:3px 10px;border-radius:20px;font-size:.73rem;font-weight:700}
.vsb.tk{background:#e8f5e9;color:#2e7d32}
.vsb.nt{background:#fff3e0;color:#e65100}
.vsb.pd{background:#fff8e1;color:#f57f17}
.vtable{width:100%;border-collapse:collapse;font-size:.82rem}
.vtable th{background:#f0f4f8;color:var(--p);padding:7px 10px;text-align:left;font-size:.72rem;font-weight:700;text-transform:uppercase;border-bottom:2px solid var(--bo)}
.vtable td{padding:7px 10px;border-bottom:1px solid var(--bo)}
.vtable tbody tr:hover{background:var(--pl)}
.vtable tbody tr:last-child td{border-bottom:none}
.bx{display:inline-flex;align-items:center;padding:3px 10px;border-radius:20px;font-size:.74rem;font-weight:700}
.bp{background:#fff8e1;color:#f57f17}.ba{background:#e8f5e9;color:#2e7d32}
.br{background:#ffebee;color:#c62828}.bn{background:#fff3e0;color:#e65100}
.bt{background:#e8f5e9;color:#2e7d32}.bgy{background:#f3f4f6;color:#555}
.empty{text-align:center;padding:60px 20px;color:var(--mu)}
.empty i{font-size:3rem;opacity:.3;display:block;margin-bottom:14px}
footer{background:#1c1c2e;color:rgba(255,255,255,.6);text-align:center;padding:14px 20px;font-size:.8rem}

@media(max-width:1024px){.ccard-body.open{grid-template-columns:1fr 1fr}}
@media(max-width:768px){
  .sidebar{transform:translateX(-100%)}.sidebar.open{transform:translateX(0)}
  .mwrap{margin-left:0}.hamburger{display:flex}.abadge{display:none}
  .ccard-body.open{grid-template-columns:1fr}
  .csec{border-right:none;border-bottom:1px solid var(--bo)}
  .csec:last-child{border-bottom:none}
  .form-grid{grid-template-columns:1fr}
  .form-group.full{grid-column:1}
}
@media(max-width:480px){
  .talert span{display:none}.pc{padding:14px 12px}
  .dg{grid-template-columns:1fr}
  .stats-row{grid-template-columns:1fr 1fr}
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
    <div class="ng open" id="g3">
      <button class="ngt" onclick="tg('g3')">
        <i class="fa-solid fa-syringe ic"></i> Vaccinations
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a href="adminaddvaccine.py" class="active"><i class="fa-solid fa-plus"></i> Add Vaccine</a>
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
      <span class="ttitle" id="page-title">Add Vaccine</span>
    </div>
    <div class="tbr">
      {tp}{th_alert}
      <span class="abadge"><i class="fa-solid fa-shield-halved"></i> Admin</span>
    </div>
  </header>
  <main class="pc">
""")

# ======================================================
# SECTION 1 — ADD VACCINE (active by default)
# ======================================================
msg_html = ""
if msg:
    icon = "fa-circle-check" if msg_type == "success" else "fa-circle-exclamation"
    msg_html = f'<div class="alert {msg_type}"><i class="fa-solid {icon}"></i> {msg}</div>'

print(f"""
<div class="section active" id="sec-addvaccine">

  <div class="av-banner">
    <div>
      <h2><i class="fa-solid fa-syringe"></i>&nbsp; Add New Vaccine</h2>
      <p>Fill in the details below to register a new vaccine to the system.</p>
    </div>
    <span class="av-banner-badge"><i class="fa-solid fa-syringe"></i> {total_vaccines} Vaccines</span>
  </div>

  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-icon re"><i class="fa-solid fa-syringe"></i></div>
      <div class="stat-info"><h3>{total_vaccines}</h3><p>Total Vaccines</p></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon gr"><i class="fa-solid fa-circle-check"></i></div>
      <div class="stat-info"><h3>{total_completed}</h3><p>Completed</p></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon bl"><i class="fa-solid fa-child"></i></div>
      <div class="stat-info"><h3>{total_children}</h3><p>Children</p></div>
    </div>
  </div>

  {msg_html}

  <div class="form-card">
    <div class="form-card-head">
      <i class="fa-solid fa-plus-circle"></i> Vaccine Registration Form
    </div>
    <form method="post" action="adminaddvaccine.py">
      <div class="form-body">
        <div class="form-grid">
          <div class="form-group">
            <label>Vaccine Name <span>*</span></label>
            <input type="text" name="vaccine_name" placeholder="e.g. BCG, Polio, MMR" required>
          </div>
          <div class="form-group">
            <label>Minimum Age (months) <span>*</span></label>
            <input type="number" name="minimum_age" placeholder="e.g. 0, 6, 12" min="0" max="216" required>
          </div>
          <div class="form-group">
            <label>Number of Doses <span>*</span></label>
            <select name="doses" required>
              <option value="">Select doses</option>
              <option value="1">1 Dose</option>
              <option value="2">2 Doses</option>
              <option value="3">3 Doses</option>
              <option value="4">4 Doses</option>
              <option value="5">5 Doses</option>
            </select>
          </div>
          <div class="form-group full">
            <label>Description</label>
            <textarea name="description" placeholder="Brief description of this vaccine, its purpose, and any special notes..."></textarea>
          </div>
        </div>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn-submit">
          <i class="fa-solid fa-plus"></i> Add Vaccine
        </button>
        <button type="reset" class="btn-reset">
          <i class="fa-solid fa-rotate-left"></i> Reset
        </button>
        <a href="adminviewvaccine.py" style="margin-left:auto;display:inline-flex;align-items:center;gap:6px;padding:10px 18px;background:var(--bg);color:var(--p);border:1.5px solid var(--p);border-radius:8px;font-size:.88rem;font-weight:600;">
          <i class="fa-solid fa-list"></i> View All Vaccines
        </a>
      </div>
    </form>
  </div>

</div><!-- /sec-addvaccine -->
""")

# ======================================================
# SECTION 2 — CHILDREN DETAILS
# ======================================================
print(f"""
<div class="section" id="sec-children">
  <div class="page-hdr">
    <div>
      <h2><i class="fa-solid fa-children"></i>&nbsp; Registered Children</h2>
      <p>Click <strong>View More</strong> to expand Child, Parent &amp; Vaccine details</p>
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

        vaccines   = vax_by_child.get(cid, [])
        v_total    = len(vaccines)
        v_taken    = sum(1 for v in vaccines if v["status"]=="taken")
        v_notified = sum(1 for v in vaccines if v["status"]=="notified")
        v_pending  = v_total - v_taken - v_notified
        vac_st     = " ".join(set(v["status"] or "pending" for v in vaccines)) if vaccines else "pending"

        h    = hosp_by_child.get(cid, {})
        hn   = h.get("name",     "Not assigned yet")
        hnum = h.get("number",   "&mdash;")
        hst  = h.get("state",    "&mdash;")
        hdi  = h.get("district", "&mdash;")

        vrows = ""
        for idx, v in enumerate(vaccines, 1):
            vs = v["status"] or "pending"
            vd = v["date"]   or "&mdash;"
            bc = "bt" if vs=="taken" else ("bn" if vs=="notified" else "bp")
            vrows += (f"<tr><td>{idx}</td><td><strong>{v['name']}</strong></td>"
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
        <div class="avatar">{initial}</div>
        <div>
          <div class="ccard-name">
            <i class="fa-solid {gicon}" style="font-size:.82rem;opacity:.75"></i>&nbsp; {cname}
          </div>
          <div class="ccard-sub">DOB: {dob} &bull; Blood: {blood} &bull; {weight} kg &bull; {gender}</div>
        </div>
      </div>
      <div class="ccard-right">
        <span class="bx bgy"><i class="fa-solid fa-syringe"></i>&nbsp; {v_total} Vaccines</span>
        <span class="bx {pbc}">Parent: {pstatus.capitalize()}</span>
        <button class="btn-vm" onclick="toggleCard(this,'body{cid}')">
          <i class="fa-solid fa-chevron-down vmi"></i> View More
        </button>
      </div>
    </div>

    <div class="ccard-body" id="body{cid}">
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
  const titles={'sec-addvaccine':'Add Vaccine','sec-children':'Child Details'};
  document.getElementById('page-title').textContent=titles[id]||'Add Vaccine';
  document.querySelectorAll('.nsub a').forEach(a=>a.classList.remove('active'));
  if(id==='sec-children'){
    document.getElementById('link-children').classList.add('active');
    document.querySelectorAll('.ng').forEach(x=>x.classList.remove('open'));
    document.getElementById('g5').classList.add('open');
  } else if(id==='sec-addvaccine'){
    document.querySelectorAll('.ng').forEach(x=>x.classList.remove('open'));
    document.getElementById('g3').classList.add('open');
  }
  window.scrollTo(0,0);
  closeSB();
}

function toggleCard(btn, bodyId){
  const body=document.getElementById(bodyId);
  const isOpen=body.classList.contains('open');
  body.classList.toggle('open',!isOpen);
  btn.classList.toggle('open',!isOpen);
  btn.innerHTML=isOpen
    ?'<i class="fa-solid fa-chevron-down vmi"></i> View More'
    :'<i class="fa-solid fa-chevron-up vmi open"></i> View Less';
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