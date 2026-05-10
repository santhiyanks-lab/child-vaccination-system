#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
import cgi, cgitb, pymysql, smtplib
import sys
from email.mime.text import MIMEText
from collections import defaultdict

cgitb.enable()
sys.stdout.reconfigure(encoding="utf-8")

print("Content-type:text/html\r\n\r\n")

form = cgi.FieldStorage()
con  = pymysql.connect(host="localhost", user="root", password="", database="child")
cur  = con.cursor()

def qc(sql):
    cur.execute(sql)
    return cur.fetchone()[0]

total_fb = qc("SELECT COUNT(*) FROM feedback")
low_fb   = qc("SELECT COUNT(*) FROM feedback WHERE rating < 2")

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

def generate_hospital_credentials(hospital_name, state, district, owner_phone_number, hospital_id):
    hname_part    = hospital_name[:3].lower()      if hospital_name      else "hos"
    state_part    = state[:3].lower()               if state              else "sta"
    district_part = district[:3].lower()            if district           else "dis"
    ophone_part   = owner_phone_number[-4:]         if owner_phone_number else "0000"
    username = f"{hname_part}_{state_part}_{district_part}_{hospital_id}"
    password = f"{hname_part}{ophone_part}"
    return username, password

SENDER_EMAIL    = "santhiyanks@gmail.com"
SENDER_PASSWORD = "snnr avxt cqgb ocwy"

def send_email(to_email, subject, body):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"]    = SENDER_EMAIL
        msg["To"]      = to_email
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        return True, None
    except Exception as e:
        return False, str(e)

# ===== FORM PROCESSING =====
redirect_script = ""
cid       = form.getvalue("cid")
approve   = form.getvalue("approve")
reject    = form.getvalue("reject")

if approve and cid:
    cur.execute(
        "SELECT hospital_name, owner_email, username, password FROM hospital WHERE hospital_id=%s", (cid,)
    )
    data = cur.fetchone()
    if data:
        name, email, saved_user, saved_pass = data[0], data[1], data[2], data[3]
        cur.execute("UPDATE hospital SET status='approved' WHERE hospital_id=%s", (cid,))
        con.commit()
        body = (
            f"Hello {name},\n\n"
            f"Your Hospital Account has been Approved.\n\n"
            f"Username : {saved_user}\n"
            f"Password : {saved_pass}\n\n"
            f"Please keep these credentials safe and use them to log in.\n\n"
            f"Thank you,\nChild Vaccination System"
        )
        ok, err = send_email(email, "Hospital Account Approved - Child Vaccination System", body)
        msg = "Hospital Approved and Email Sent!" if ok else f"Hospital Approved but Email Failed: {err}"
        safe_msg = msg.replace("'", "\\'").replace('"', '\\"')
        redirect_script = f'<script>alert("{safe_msg}");window.location.href="adminpendingmanager.py";</script>'

elif reject and cid:
    cur.execute("SELECT hospital_name, owner_email FROM hospital WHERE hospital_id=%s", (cid,))
    data = cur.fetchone()
    if data:
        name, email = data[0], data[1]
        cur.execute("UPDATE hospital SET status='rejected' WHERE hospital_id=%s", (cid,))
        con.commit()
        body = (
            f"Hello {name},\n\n"
            f"Your hospital registration has been rejected.\n"
            f"You may reapply with correct documents.\n\n"
            f"Thank you,\nChild Vaccination System"
        )
        ok, err = send_email(email, "Hospital Registration Update - Child Vaccination System", body)
        msg = "Hospital Rejected and Email Sent!" if ok else f"Hospital Rejected but Email Failed: {err}"
        safe_msg = msg.replace("'", "\\'").replace('"', '\\"')
        redirect_script = f'<script>alert("{safe_msg}");window.location.href="adminpendingmanager.py";</script>'

# Fetch pending hospitals
cur.execute("SELECT * FROM hospital WHERE status='pending'")
rows = cur.fetchall()

# State and district options for filter bar
cur.execute("SELECT DISTINCT state FROM hospital WHERE status='pending' AND state IS NOT NULL ORDER BY state")
pending_states = [r[0] for r in cur.fetchall()]

cur.execute("SELECT DISTINCT state, district FROM hospital WHERE status='pending' AND state IS NOT NULL AND district IS NOT NULL ORDER BY state, district")
pending_state_districts = cur.fetchall()

pending_state_opts = ""
for s in pending_states:
    pending_state_opts += f'<option value="{s.lower()}">{s}</option>'

pending_district_opts = ""
for sd in pending_state_districts:
    pending_district_opts += f'<option value="{sd[1].lower()}" data-state="{sd[0].lower()}">{sd[1]}</option>'

# Children details
cur.execute("""
    SELECT c.child_id, c.child_name, c.dob, c.weight,
           c.gender, c.blood_group, c.identification_mark,
           p.father_name, p.mother_name, p.email,
           p.mobile_number, p.state, p.district, p.address, p.occupation,
           p.status AS parent_status
    FROM children c
    LEFT JOIN parent p ON c.parent_id = p.parent_id
    ORDER BY c.child_id DESC
""")
all_children = cur.fetchall()

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
  <title>Pending Hospitals</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    *,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
    :root{{
      --p:#1565c0;--pd:#0d47a1;--pl:#e3f2fd;--ac:#ff6f00;
      --sw:260px;--hh:60px;--tx:#1c1c1c;--mu:#6b7280;
      --bg:#f0f4f8;--ca:#fff;--bo:#dde3ea;
      --da:#e53935;--su:#2e7d32;--wa:#f57f17;--wl:#fff8e1;
      --ra:10px;--sh:0 2px 16px rgba(0,0,0,.09);
      --tr:.25s ease;--fn:'Segoe UI',Arial,sans-serif
    }}
    html{{scroll-behavior:smooth}}
    body{{font-family:var(--fn);background:var(--bg);color:var(--tx);min-height:100vh;line-height:1.6}}
    a{{text-decoration:none;color:inherit}}
    img{{max-width:100%;height:auto;display:block;object-fit:cover}}
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
    .tbcrumb span{{margin:0 5px}}
    .hamburger{{display:none;flex-direction:column;gap:5px;background:transparent;border:none;cursor:pointer;padding:6px;border-radius:6px}}
    .hamburger span{{display:block;width:22px;height:2px;background:var(--tx);border-radius:2px;transition:transform var(--tr),opacity var(--tr)}}
    .hamburger.open span:nth-child(1){{transform:translateY(7px) rotate(45deg)}}
    .hamburger.open span:nth-child(2){{opacity:0}}
    .hamburger.open span:nth-child(3){{transform:translateY(-7px) rotate(-45deg)}}
    .tbr{{display:flex;align-items:center;gap:10px}}
    .abadge{{background:var(--pl);color:var(--p);padding:5px 14px;border-radius:20px;font-size:.82rem;font-weight:600}}
    .pc{{padding:24px 20px;flex:1}}
    .section{{display:none}}.section.active{{display:block}}
    .page-hdr{{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:20px;flex-wrap:wrap}}
    .page-hdr-left{{display:flex;align-items:center;gap:14px}}
    .page-hdr-icon{{width:48px;height:48px;border-radius:12px;background:var(--wl);color:var(--wa);display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0}}
    .page-hdr h2{{font-size:clamp(1rem,2.5vw,1.35rem);font-weight:700}}
    .page-hdr p{{font-size:.83rem;color:var(--mu);margin-top:2px}}
    .cnt-badge{{background:var(--wl);color:var(--wa);padding:6px 16px;border-radius:20px;font-size:.85rem;font-weight:700;white-space:nowrap}}
    /* ── Filter bar (same as approvedmanager) ── */
    .filter-bar{{display:flex;align-items:center;gap:10px;margin-bottom:14px;flex-wrap:wrap;background:var(--ca);border:1px solid var(--bo);border-radius:var(--ra);padding:12px 16px;box-shadow:0 1px 6px rgba(0,0,0,.05)}}
    .filter-bar label{{font-size:.78rem;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:.4px;white-space:nowrap}}
    .sbox{{position:relative;flex:1;min-width:160px}}
    .sbox i{{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:var(--mu);font-size:.82rem}}
    .sbox input{{width:100%;padding:8px 12px 8px 32px;border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.86rem;background:var(--ca);transition:border-color var(--tr)}}
    .sbox input:focus{{outline:none;border-color:var(--p)}}
    .fsel{{padding:8px 12px;border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.86rem;background:var(--ca);color:var(--tx);cursor:pointer;min-width:140px}}
    .fsel:focus{{outline:none;border-color:var(--p)}}
    .btn-clear{{padding:8px 14px;background:var(--da);color:#fff;border:none;border-radius:8px;font-size:.82rem;font-weight:600;font-family:var(--fn);cursor:pointer;transition:background var(--tr);white-space:nowrap}}
    .btn-clear:hover{{background:#c62828}}
    .cnt-lbl{{font-size:.83rem;color:var(--mu);font-weight:600;white-space:nowrap;margin-left:auto}}
    /* ── Table card ── */
    .tcard{{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);overflow:hidden}}
    .tcard-head{{background:linear-gradient(90deg,#e65100,var(--wa));color:#fff;padding:14px 20px;display:flex;align-items:center;gap:10px;font-size:.95rem;font-weight:700}}
    .tw{{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}}
    table{{width:100%;border-collapse:collapse;min-width:540px}}
    thead{{background:#263238;color:#fff}}
    th{{padding:12px 14px;text-align:left;font-size:.82rem;font-weight:600;text-transform:uppercase;letter-spacing:.4px;white-space:nowrap}}
    td{{padding:12px 14px;font-size:.88rem;border-bottom:1px solid var(--bo);white-space:nowrap;vertical-align:middle}}
    tbody tr:hover{{background:var(--wl)}}
    tbody tr:last-child td{{border-bottom:none}}
    .snum{{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;background:var(--wl);color:var(--wa);border-radius:50%;font-size:.78rem;font-weight:700}}
    .badge-pending{{display:inline-flex;align-items:center;gap:5px;padding:4px 12px;background:var(--wl);color:var(--wa);border-radius:20px;font-size:.78rem;font-weight:700}}
    .hosp-name{{display:inline-flex;align-items:center;gap:9px}}
    .hosp-icon{{width:32px;height:32px;border-radius:8px;background:var(--wl);color:var(--wa);display:flex;align-items:center;justify-content:center;font-size:.85rem;flex-shrink:0}}
    .btn-view{{display:inline-flex;align-items:center;gap:6px;padding:7px 14px;background:var(--pl);color:var(--p);border:1px solid var(--p);border-radius:7px;font-family:var(--fn);font-size:.82rem;font-weight:600;cursor:pointer;transition:background var(--tr),color var(--tr);white-space:nowrap}}
    .btn-view:hover{{background:var(--p);color:#fff}}
    .empty-state{{text-align:center;padding:56px 20px;color:var(--mu)}}
    .empty-state i{{font-size:3rem;margin-bottom:14px;color:var(--bo);display:block}}
    .empty-state h3{{font-size:1rem;font-weight:700;margin-bottom:6px;color:var(--tx)}}
    /* Modal */
    .modal-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:2000;align-items:center;justify-content:center;padding:16px}}
    .modal-overlay.active{{display:flex}}
    .modal-box{{background:var(--ca);border-radius:var(--ra);width:100%;max-width:780px;max-height:92vh;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,.2);animation:slideUp .25s ease}}
    @keyframes slideUp{{from{{transform:translateY(40px);opacity:0}}to{{transform:translateY(0);opacity:1}}}}
    .modal-head{{background:linear-gradient(90deg,#263238,#37474f);color:#fff;padding:16px 20px;display:flex;align-items:center;justify-content:space-between;border-radius:var(--ra) var(--ra) 0 0;flex-shrink:0}}
    .modal-head h4{{font-size:1rem;font-weight:700}}
    .modal-close{{background:rgba(255,255,255,.2);border:none;color:#fff;width:28px;height:28px;border-radius:50%;cursor:pointer;font-size:.9rem;display:flex;align-items:center;justify-content:center;transition:background var(--tr)}}
    .modal-close:hover{{background:rgba(255,255,255,.35)}}
    .modal-box>form{{display:flex;flex-direction:column;flex:1 1 auto;min-height:0;overflow:hidden}}
    .modal-body{{padding:20px;flex:1 1 auto;overflow-y:auto;overflow-x:hidden;-webkit-overflow-scrolling:touch;min-height:0}}
    .modal-footer{{padding:14px 20px;border-top:1px solid var(--bo);display:flex;gap:10px;justify-content:flex-end;flex-wrap:wrap;flex-shrink:0}}
    .modal-section-title{{font-size:.8rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--p);margin:16px 0 10px;padding-bottom:6px;border-bottom:2px solid var(--pl)}}
    .modal-section-title:first-child{{margin-top:0}}
    .detail-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px 20px}}
    .detail-item label{{display:block;font-size:.72rem;color:var(--mu);font-weight:600;text-transform:uppercase;letter-spacing:.4px;margin-bottom:2px}}
    .detail-item span{{font-size:.9rem;font-weight:500;color:var(--tx)}}
    .docs-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:14px;margin-top:10px}}
    .doc-item{{text-align:center}}
    .doc-item img{{width:100%;height:110px;object-fit:cover;border-radius:8px;border:2px solid var(--bo);margin:0 auto}}
    .doc-item p{{font-size:.75rem;color:var(--mu);margin-top:6px;font-weight:600}}
    .cred-box{{background:#f0f7ff;border:1.5px dashed #1976d2;border-radius:10px;padding:16px 18px;margin-top:4px}}
    .cred-row{{display:flex;align-items:center;gap:14px;margin-bottom:10px}}
    .cred-row:last-child{{margin-bottom:0}}
    .cred-label{{font-size:.72rem;color:var(--mu);font-weight:700;text-transform:uppercase;letter-spacing:.4px;flex-shrink:0;width:80px}}
    .cred-val{{font-family:monospace;font-weight:700;color:#0d47a1;font-size:.96rem;word-break:break-all}}
    .cred-note{{font-size:.74rem;color:#1565c0;margin-top:10px;line-height:1.5}}
    .btn-approve{{display:inline-flex;align-items:center;gap:6px;padding:9px 22px;background:var(--su);color:#fff;border:none;border-radius:8px;font-family:var(--fn);font-size:.9rem;font-weight:700;cursor:pointer;transition:background var(--tr)}}
    .btn-approve:hover{{background:#1b5e20}}
    .btn-reject{{display:inline-flex;align-items:center;gap:6px;padding:9px 22px;background:var(--da);color:#fff;border:none;border-radius:8px;font-family:var(--fn);font-size:.9rem;font-weight:700;cursor:pointer;transition:background var(--tr)}}
    .btn-reject:hover{{background:#b71c1c}}
    .btn-cancel{{display:inline-flex;align-items:center;gap:6px;padding:9px 18px;background:var(--ca);color:var(--mu);border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.9rem;font-weight:600;cursor:pointer;transition:background var(--tr)}}
    .btn-cancel:hover{{background:var(--bg);color:var(--tx)}}
    /* Children section */
    .page-hdr2{{background:linear-gradient(120deg,var(--p),var(--pd));color:#fff;border-radius:var(--ra);padding:22px 28px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}}
    .page-hdr2 h2{{font-size:1.1rem;font-weight:700;margin-bottom:3px}}
    .page-hdr2 p{{font-size:.83rem;opacity:.8}}
    .page-hdr2-badge{{background:rgba(255,255,255,.18);padding:7px 16px;border-radius:20px;font-size:.83rem;font-weight:700}}
    .ctoolbar{{display:flex;align-items:center;gap:12px;margin-bottom:18px;flex-wrap:wrap}}
    .csbox{{position:relative;flex:1;min-width:200px}}
    .csbox i{{position:absolute;left:11px;top:50%;transform:translateY(-50%);color:var(--mu);font-size:.82rem}}
    .csbox input{{width:100%;padding:9px 12px 9px 34px;border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.85rem;background:var(--ca)}}
    .csbox input:focus{{outline:none;border-color:var(--p)}}
    .cnt-lbl2{{font-size:.84rem;color:var(--mu);font-weight:600;white-space:nowrap}}
    .child-card{{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);margin-bottom:16px;overflow:hidden}}
    .ccard-top{{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;flex-wrap:wrap;gap:10px}}
    .ccard-left{{display:flex;align-items:center;gap:14px}}
    .avatar{{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--p),var(--pd));border:2px solid var(--pl);display:flex;align-items:center;justify-content:center;font-size:1.15rem;font-weight:800;color:#fff;flex-shrink:0}}
    .ccard-name{{font-size:.96rem;font-weight:700;color:var(--tx)}}
    .ccard-sub{{font-size:.76rem;color:var(--mu);margin-top:2px}}
    .ccard-right{{display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
    .btn-viewmore{{display:inline-flex;align-items:center;gap:6px;padding:7px 16px;background:var(--p);color:#fff;border:none;border-radius:8px;font-size:.82rem;font-weight:600;font-family:var(--fn);cursor:pointer;transition:background var(--tr)}}
    .btn-viewmore:hover{{background:var(--pd)}}
    .ccard-details{{display:none;border-top:1px solid var(--bo)}}
    .ccard-details.open{{display:block}}
    .detail-tabs{{display:flex;border-bottom:2px solid var(--bo);background:#fafbfc}}
    .dtab{{flex:1;background:transparent;border:none;border-bottom:3px solid transparent;margin-bottom:-2px;padding:11px 10px;font-family:var(--fn);font-size:.83rem;font-weight:600;color:var(--mu);cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;transition:color var(--tr),border-color var(--tr),background var(--tr);white-space:nowrap}}
    .dtab:hover{{color:var(--p);background:var(--pl)}}
    .dtab.active{{color:var(--p);border-bottom-color:var(--ac);background:#f0f7ff}}
    .dpanel{{display:none;padding:18px 20px}}
    .dpanel.active{{display:block}}
    .dg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px 20px;margin-bottom:4px}}
    .di{{background:var(--bg);border:1px solid var(--bo);border-radius:8px;padding:9px 13px}}
    .di label{{display:block;font-size:.67rem;color:var(--mu);font-weight:700;text-transform:uppercase;letter-spacing:.4px;margin-bottom:3px}}
    .di span{{font-size:.86rem;font-weight:600;color:var(--tx);word-break:break-word}}
    .di.full{{grid-column:1/-1}}
    .vsumbadges{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}}
    .vsb{{display:flex;align-items:center;gap:5px;padding:5px 14px;border-radius:20px;font-size:.76rem;font-weight:700}}
    .vsb.tk{{background:#e8f5e9;color:#2e7d32}}.vsb.nt{{background:#fff3e0;color:#e65100}}.vsb.pd{{background:#fff8e1;color:#f57f17}}
    .vtable{{width:100%;border-collapse:collapse;font-size:.83rem}}
    .vtable th{{background:#f0f4f8;color:var(--p);padding:8px 12px;text-align:left;font-size:.74rem;font-weight:700;text-transform:uppercase;border-bottom:2px solid var(--bo)}}
    .vtable td{{padding:8px 12px;border-bottom:1px solid var(--bo)}}
    .vtable tbody tr:hover{{background:var(--pl)}}
    .vtable tbody tr:last-child td{{border-bottom:none}}
    .bx{{display:inline-flex;align-items:center;padding:3px 10px;border-radius:20px;font-size:.74rem;font-weight:700}}
    .bp{{background:#fff8e1;color:#f57f17}}.ba{{background:#e8f5e9;color:#2e7d32}}
    .br{{background:#ffebee;color:#c62828}}.bn{{background:#fff3e0;color:#e65100}}
    .bt{{background:#e8f5e9;color:#2e7d32}}.bgy{{background:#f3f4f6;color:#555}}
    footer{{background:#1c1c2e;color:rgba(255,255,255,.6);text-align:center;padding:14px 20px;font-size:.8rem}}
    @media(max-width:1024px){{:root{{--sw:230px}}}}
    @media(max-width:768px){{
      .sidebar{{transform:translateX(-100%)}}.sidebar.open{{transform:translateX(0)}}
      .mwrap{{margin-left:0}}.hamburger{{display:flex}}
      .pc{{padding:16px 12px}}.abadge{{display:none}}
      .filter-bar{{flex-direction:column;align-items:stretch}}
      .fsel,.sbox{{width:100%;min-width:unset}}
      .detail-tabs{{overflow-x:auto}}.modal-box{{max-height:96vh}}
    }}
    @media(max-width:480px){{
      .page-hdr-icon{{display:none}}
      th,td{{padding:10px;font-size:.82rem}}
      .detail-grid{{grid-template-columns:1fr}}
      .docs-grid{{grid-template-columns:repeat(2,1fr)}}
      .modal-footer{{flex-direction:column}}
      .btn-approve,.btn-reject,.btn-cancel{{width:100%;justify-content:center}}
      .dg{{grid-template-columns:1fr 1fr}}
    }}
  </style>
</head>
<body>

{redirect_script}

<div class="overlay" id="overlay"></div>

<!-- SIDEBAR -->
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
        <a href="adminpendingmanager.py" class="active"><i class="fa-solid fa-clock"></i> Pending Manager {sb(pending_hospitals)}</a>
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

<!-- MAIN -->
<div class="mwrap">
  <header class="topbar">
    <div class="tbl">
      <button class="hamburger" id="hamburger"><span></span><span></span><span></span></button>
      <div>
        <div class="ttitle" id="page-title">Pending Hospitals</div>
        <div class="tbcrumb">
          <a href="admin_dash.py">Dashboard</a><span>&rsaquo;</span>
          <span id="breadcrumb-sub">Hospital &rsaquo; Pending</span>
        </div>
      </div>
    </div>
    <div class="tbr">
      <span class="abadge"><i class="fa-solid fa-shield-halved"></i> Admin</span>
    </div>
  </header>

  <main class="pc">
    <!-- SECTION: PENDING HOSPITALS -->
    <div class="section active" id="sec-pending">
      <div class="page-hdr">
        <div class="page-hdr-left">
          <div class="page-hdr-icon"><i class="fa-solid fa-hospital"></i></div>
          <div>
            <h2>Pending Hospitals</h2>
            <p>Filter by state and district, or search by hospital name / email / phone.</p>
          </div>
        </div>
        <span class="cnt-badge" id="rowCount"><i class="fa-solid fa-clock"></i> {len(rows)} Pending</span>
      </div>

      <!-- Filter Bar -->
      <div class="filter-bar">
        <label><i class="fa-solid fa-filter"></i> Filter</label>
        <div class="sbox">
          <i class="fa-solid fa-magnifying-glass"></i>
          <input type="text" id="searchInput" placeholder="Search hospital name, email, phone..." oninput="filterTable()">
        </div>
        <select class="fsel" id="stateFilter" onchange="updateDistricts(); filterTable()">
          <option value="">All States</option>
          {pending_state_opts}
        </select>
        <select class="fsel" id="districtFilter" onchange="filterTable()">
          <option value="">All Districts</option>
          {pending_district_opts}
        </select>
        <button class="btn-clear" onclick="clearFilters()"><i class="fa-solid fa-xmark"></i> Clear</button>
        <span class="cnt-lbl" id="filterCount">{len(rows)} records</span>
      </div>

      <div class="tcard">
        <div class="tcard-head"><i class="fa-solid fa-clock"></i> Pending Hospital List</div>
        <div class="tw">
          <table id="mainTable">
            <thead>
              <tr>
                <th>#</th>
                <th><i class="fa-solid fa-hospital"></i> Hospital Name</th>
                <th><i class="fa-solid fa-location-dot"></i> State</th>
                <th><i class="fa-solid fa-map"></i> District</th>
                <th><i class="fa-solid fa-envelope"></i> Owner Email</th>
                <th><i class="fa-solid fa-phone"></i> Phone</th>
                <th>Status</th>
                <th><i class="fa-solid fa-gears"></i> Action</th>
              </tr>
            </thead>
            <tbody id="tableBody">
""")

if rows:
    for idx, row in enumerate(rows, start=1):
        hospital_id        = row[0]
        hospital_name      = row[1]
        state              = row[2] or ""
        district           = row[3] or ""
        owner_phone_number = row[13]
        owner_email        = row[14]
        print(f"""
              <tr data-state="{state.lower()}" data-district="{district.lower()}">
                <td><span class="snum">{idx}</span></td>
                <td><div class="hosp-name"><div class="hosp-icon"><i class="fa-solid fa-hospital"></i></div><strong>{hospital_name}</strong></div></td>
                <td>{state or "&mdash;"}</td>
                <td>{district or "&mdash;"}</td>
                <td>{owner_email}</td>
                <td>{owner_phone_number}</td>
                <td><span class="badge-pending"><i class="fa-solid fa-clock"></i> Pending</span></td>
                <td><button class="btn-view" onclick="openModal('modal{hospital_id}')"><i class="fa-solid fa-eye"></i> View &amp; Decide</button></td>
              </tr>""")
else:
    print("""
              <tr><td colspan="8">
                <div class="empty-state">
                  <i class="fa-solid fa-circle-check"></i>
                  <h3>No Pending Hospitals</h3>
                  <p>All hospital registrations have been reviewed.</p>
                </div>
              </td></tr>""")

print("""
            </tbody>
          </table>
        </div>
      </div>
    </div><!-- /sec-pending -->
""")

# SECTION: CHILDREN DETAILS
print(f"""
    <div class="section" id="sec-children">
      <div class="page-hdr2">
        <div>
          <h2><i class="fa-solid fa-children"></i>&nbsp; Registered Children</h2>
          <p>Click <strong>View More</strong> on any child to see parent, vaccine &amp; hospital details</p>
        </div>
        <span class="page-hdr2-badge"><i class="fa-solid fa-child"></i> {total_children} Total</span>
      </div>
      <div class="ctoolbar">
        <div class="csbox">
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
        <span class="cnt-lbl2" id="cntLbl">{len(all_children)} records</span>
      </div>
""")

for r in all_children:
    cid      = r[0]
    cname    = r[1]  or "&mdash;"
    dob      = r[2]  or "&mdash;"
    weight   = r[3]  or "&mdash;"
    gender   = r[4]  or "&mdash;"
    blood    = r[5]  or "&mdash;"
    father   = r[7]  or "&mdash;"
    mother   = r[8]  or "&mdash;"
    email    = r[9]  or "&mdash;"
    mobile   = r[10] or "&mdash;"
    state    = r[11] or "&mdash;"
    district = r[12] or "&mdash;"
    address  = r[13] or "&mdash;"
    occ      = r[14] or "&mdash;"
    pstatus  = r[15] or "pending"
    pbc      = {"approved":"ba","rejected":"br","pending":"bp"}.get(pstatus,"bp")
    gicon    = "fa-mars" if str(r[4]).lower()=="male" else ("fa-venus" if str(r[4]).lower()=="female" else "fa-genderless")
    initial  = str(r[1])[0].upper() if r[1] else "?"
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
    vrows = ""
    for vi, v in enumerate(vaccines, 1):
        vs = v["status"] or "pending"
        vd = v["date"]   or "&mdash;"
        bc = "bt" if vs=="taken" else ("bn" if vs=="notified" else "bp")
        vrows += (f"<tr><td>{vi}</td><td><strong>{v['name']}</strong></td>"
                  f"<td>{v['age']} mo.</td><td>{vd}</td>"
                  f"<td><span class='bx {bc}'>{vs.capitalize()}</span></td></tr>")
    if not vrows:
        vrows = "<tr><td colspan='5' style='text-align:center;color:#bbb;padding:14px'>No vaccines assigned yet</td></tr>"

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
              <div class="ccard-name"><i class="fa-solid {gicon}" style="font-size:.85rem;opacity:.7"></i>&nbsp;{cname}</div>
              <div class="ccard-sub">DOB: {dob} &bull; Blood: {blood} &bull; {weight} kg &bull; {gender}</div>
            </div>
          </div>
          <div class="ccard-right">
            <span class="bx bgy"><i class="fa-solid fa-syringe"></i>&nbsp; {v_total} Vaccines</span>
            <span class="bx {pbc}">Parent: {pstatus.capitalize()}</span>
            <button class="btn-viewmore" onclick="toggleDetails(this,'cdet{cid}')">
              <i class="fa-solid fa-chevron-down vm-icon"></i> View More
            </button>
          </div>
        </div>
        <div class="ccard-details" id="cdet{cid}">
          <div class="detail-tabs" id="ctabs{cid}">
            <button class="dtab active" onclick="switchDTab({cid},'parent')"><i class="fa-solid fa-users"></i> Parent</button>
            <button class="dtab" onclick="switchDTab({cid},'vaccine')"><i class="fa-solid fa-syringe"></i> Vaccine</button>
            <button class="dtab" onclick="switchDTab({cid},'hospital')"><i class="fa-solid fa-hospital"></i> Hospital</button>
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
                <thead><tr><th>#</th><th>Vaccine Name</th><th>Due Age</th><th>Date Taken</th><th>Status</th></tr></thead>
                <tbody>{vrows}</tbody>
              </table>
            </div>
          </div>
          <div class="dpanel" id="cdp{cid}-hospital">
            <div class="dg">
              <div class="di"><label>Hospital Name</label><span>{hn}</span></div>
              <div class="di"><label>Contact Number</label><span>{hnum}</span></div>
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
""")

# HOSPITAL MODALS
for row in rows:
    hospital_id           = row[0]
    hospital_name         = row[1]
    state                 = row[2]
    district              = row[3]
    address               = row[4]
    pincode               = row[5]
    hospital_number       = row[6]
    license_proof         = row[7]
    year_of_establishment = row[8]
    hospital_image        = row[9]
    owner_name            = row[10]
    owner_profile         = row[11]
    owner_address         = row[12]
    owner_phone_number    = row[13]
    owner_email           = row[14]
    username              = row[15] or ""
    password              = row[16] or ""

    print(f"""
<div class="modal-overlay" id="modal{hospital_id}">
  <div class="modal-box">
    <div class="modal-head">
      <h4><i class="fa-solid fa-hospital"></i> {hospital_name} &mdash; Details</h4>
      <button class="modal-close" onclick="closeModal('modal{hospital_id}')">&#x2715;</button>
    </div>
    <form method="post" action="adminpendingmanager.py">
      <div class="modal-body">
        <div class="modal-section-title"><i class="fa-solid fa-hospital"></i> Hospital Information</div>
        <div class="detail-grid">
          <div class="detail-item"><label>Hospital Name</label><span>{hospital_name}</span></div>
          <div class="detail-item"><label>State</label><span>{state}</span></div>
          <div class="detail-item"><label>District</label><span>{district}</span></div>
          <div class="detail-item"><label>Pincode</label><span>{pincode}</span></div>
          <div class="detail-item"><label>Hospital Number</label><span>{hospital_number}</span></div>
          <div class="detail-item"><label>Year Established</label><span>{year_of_establishment}</span></div>
          <div class="detail-item" style="grid-column:1/-1"><label>Address</label><span>{address}</span></div>
        </div>
        <div class="modal-section-title"><i class="fa-solid fa-user-tie"></i> Owner Information</div>
        <div class="detail-grid">
          <div class="detail-item"><label>Owner Name</label><span>{owner_name}</span></div>
          <div class="detail-item"><label>Phone</label><span>{owner_phone_number}</span></div>
          <div class="detail-item"><label>Email</label><span>{owner_email}</span></div>
          <div class="detail-item" style="grid-column:1/-1"><label>Address</label><span>{owner_address}</span></div>
        </div>
        <div class="modal-section-title"><i class="fa-solid fa-image"></i> Documents &amp; Images</div>
        <div class="docs-grid">
          <div class="doc-item">
            <img src="./images/{license_proof}" alt="License" onerror="this.src='images/noimage.png'">
            <p>License Proof</p>
          </div>
          <div class="doc-item">
            <img src="./images/{hospital_image}" alt="Hospital" onerror="this.src='images/noimage.png'">
            <p>Hospital Image</p>
          </div>
          <div class="doc-item">
            <img src="./images/{owner_profile}" alt="Owner" onerror="this.src='images/noimage.png'">
            <p>Owner Profile</p>
          </div>
        </div>
        <div class="modal-section-title"><i class="fa-solid fa-key"></i> Login Credentials (set during registration)</div>
        <div class="cred-box">
          <div class="cred-row">
            <span class="cred-label">Username</span>
            <span class="cred-val">{username}</span>
          </div>
          <div class="cred-row">
            <span class="cred-label">Password</span>
            <span class="cred-val">{password}</span>
          </div>
          <div class="cred-note">
            <i class="fa-solid fa-circle-info"></i>&nbsp;
            These credentials were generated and shown to the hospital during registration.
            They will be emailed exactly as shown above on approval.
          </div>
        </div>
        <input type="hidden" name="cid" value="{hospital_id}">
      </div>
      <div class="modal-footer">
        <button type="button" class="btn-cancel" onclick="closeModal('modal{hospital_id}')">
          <i class="fa-solid fa-xmark"></i> Cancel
        </button>
        <button type="submit" name="reject" value="Reject" class="btn-reject">
          <i class="fa-solid fa-ban"></i> Reject
        </button>
        <button type="submit" name="approve" value="Approve" class="btn-approve">
          <i class="fa-solid fa-check"></i> Approve &amp; Send Email
        </button>
      </div>
    </form>
  </div>
</div>""")

print("""
<script>
const hamburger = document.getElementById('hamburger');
const sidebar   = document.getElementById('sidebar');
const overlay   = document.getElementById('overlay');
function closeSB() {
  sidebar.classList.remove('open'); hamburger.classList.remove('open');
  overlay.classList.remove('active'); document.body.style.overflow = '';
}
hamburger.addEventListener('click', () => {
  const o = sidebar.classList.toggle('open');
  hamburger.classList.toggle('open', o); overlay.classList.toggle('active', o);
  document.body.style.overflow = o ? 'hidden' : '';
});
overlay.addEventListener('click', closeSB);
window.addEventListener('resize', () => { if (window.innerWidth > 768) closeSB(); });

function tg(id) {
  const g = document.getElementById(id), o = g.classList.contains('open');
  document.querySelectorAll('.ng').forEach(x => x.classList.remove('open'));
  if (!o) g.classList.add('open');
}
function showSection(id) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  const titles      = { 'sec-pending': 'Pending Hospitals', 'sec-children': 'Child Details' };
  const breadcrumbs = { 'sec-pending': 'Hospital &rsaquo; Pending', 'sec-children': 'Children &rsaquo; Child Details' };
  document.getElementById('page-title').textContent = titles[id] || 'Pending Hospitals';
  document.getElementById('breadcrumb-sub').innerHTML = breadcrumbs[id] || '';
  document.querySelectorAll('.nsub a').forEach(a => a.classList.remove('active'));
  if (id === 'sec-children') {
    document.getElementById('link-children').classList.add('active');
    document.querySelectorAll('.ng').forEach(x => x.classList.remove('open'));
    document.getElementById('g5').classList.add('open');
  }
  window.scrollTo(0, 0); closeSB();
}
function openModal(id)  { document.getElementById(id).classList.add('active');    document.body.style.overflow = 'hidden'; }
function closeModal(id) { document.getElementById(id).classList.remove('active'); document.body.style.overflow = ''; }
document.querySelectorAll('.modal-overlay').forEach(m => {
  m.addEventListener('click', function(e) { if (e.target === this) closeModal(this.id); });
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') document.querySelectorAll('.modal-overlay.active').forEach(m => closeModal(m.id));
});

/* ── Filter bar functions ── */
function updateDistricts() {
  const st = document.getElementById('stateFilter').value.toLowerCase();
  const distSel = document.getElementById('districtFilter');
  Array.from(distSel.options).forEach(opt => {
    if (!opt.value) return;
    opt.style.display = (!st || opt.dataset.state === st) ? '' : 'none';
  });
  const cur = distSel.options[distSel.selectedIndex];
  if (cur && cur.value && cur.style.display === 'none') distSel.value = '';
}
function filterTable() {
  const q  = document.getElementById('searchInput').value.toLowerCase();
  const st = document.getElementById('stateFilter').value.toLowerCase();
  const di = document.getElementById('districtFilter').value.toLowerCase();
  let visible = 0;
  document.querySelectorAll('#tableBody tr').forEach(row => {
    const text    = row.textContent.toLowerCase();
    const rowSt   = (row.dataset.state    || '').toLowerCase();
    const rowDi   = (row.dataset.district || '').toLowerCase();
    const matchQ  = !q  || text.includes(q);
    const matchSt = !st || rowSt === st;
    const matchDi = !di || rowDi === di;
    const show    = matchQ && matchSt && matchDi;
    row.style.display = show ? '' : 'none';
    if (show) visible++;
  });
  document.getElementById('rowCount').innerHTML   = '<i class="fa-solid fa-clock"></i> ' + visible + ' Pending';
  document.getElementById('filterCount').textContent = visible + ' record' + (visible !== 1 ? 's' : '');
}
function clearFilters() {
  document.getElementById('searchInput').value  = '';
  document.getElementById('stateFilter').value  = '';
  updateDistricts();
  document.getElementById('districtFilter').value = '';
  filterTable();
}

function toggleDetails(btn, detId) {
  const det = document.getElementById(detId), isOpen = det.classList.contains('open');
  det.classList.toggle('open', !isOpen); btn.classList.toggle('open', !isOpen);
  btn.innerHTML = isOpen
    ? '<i class="fa-solid fa-chevron-down vm-icon"></i> View More'
    : '<i class="fa-solid fa-chevron-up vm-icon open"></i> View Less';
}
function switchDTab(cid, tabName) {
  const panels = ['parent','vaccine','hospital'];
  const btns   = document.getElementById('ctabs'+cid).querySelectorAll('.dtab');
  panels.forEach((p,i) => {
    const el = document.getElementById('cdp'+cid+'-'+p);
    if (el) el.classList.toggle('active', p===tabName);
    if (btns[i]) btns[i].classList.toggle('active', p===tabName);
  });
}
function filterCards() {
  const q  = document.getElementById('childSearch').value.toLowerCase();
  const gf = document.getElementById('genderFilter').value.toLowerCase();
  const vf = document.getElementById('vacFilter').value.toLowerCase();
  const cards = document.querySelectorAll('.child-card');
  let visible = 0;
  cards.forEach(c => {
    const matchQ = !q  || c.dataset.name.includes(q) || c.dataset.father.includes(q)
                       || c.dataset.mobile.includes(q) || c.dataset.blood.includes(q);
    const matchG = !gf || c.dataset.gender === gf;
    const matchV = !vf || (c.dataset.vacstatus||'').includes(vf);
    const show   = matchQ && matchG && matchV;
    c.style.display = show ? '' : 'none';
    if (show) visible++;
  });
  document.getElementById('cntLbl').textContent = visible + ' record' + (visible!==1?'s':'');
}
</script>
</body>
</html>
""")

con.close()