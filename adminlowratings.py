#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
import sys, pymysql, smtplib, cgi, cgitb
from collections import defaultdict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
sys.stdout.reconfigure(encoding="utf-8")
print("Content-Type:text/html\r\n\r\n")
cgitb.enable()

con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()

def qc(sql):
    cur.execute(sql)
    return cur.fetchone()[0]

# ─── EMAIL CONFIG ─────────────────────────────────────────────────────────────
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "santhiyanks@gmail.com"
SMTP_PASS = "snnr avxt cqgb ocwy"

def send_alert_to_hospital(hosp_email, hosp_name, parent_name, child_name,
                            vaccine_name, rating, comment, feedback_id):
    try:
        stars = "⭐" * rating + "☆" * (5 - rating)
        html = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f4f6fa;padding:20px;margin:0">
        <div style="max-width:620px;margin:auto;background:#fff;border-radius:14px;
                    padding:32px;box-shadow:0 4px 20px rgba(0,0,0,.1)">
          <div style="background:#e53935;border-radius:10px;padding:16px 20px;margin-bottom:24px">
            <h2 style="color:#fff;margin:0;font-size:1.2rem">
              🚨 Low Rating Alert — Immediate Attention Required
            </h2>
          </div>
          <p style="color:#374151;font-size:.95rem;margin-bottom:20px">
            Dear <strong>{hosp_name}</strong>,<br><br>
            The admin has flagged a <strong>low rating</strong> feedback received at your hospital
            and requests your immediate attention.
          </p>
          <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
            <tr style="background:#fff3e0">
              <td style="padding:10px 14px;font-weight:700;font-size:.88rem;color:#e65100;width:40%">Rating</td>
              <td style="padding:10px 14px;font-size:.88rem">{stars} &nbsp;<strong>({rating}/5)</strong></td>
            </tr>
            <tr style="background:#f9fafb">
              <td style="padding:10px 14px;font-weight:700;font-size:.88rem;color:#374151">Parent Name</td>
              <td style="padding:10px 14px;font-size:.88rem;color:#374151">{parent_name}</td>
            </tr>
            <tr style="background:#fff">
              <td style="padding:10px 14px;font-weight:700;font-size:.88rem;color:#374151">Child Name</td>
              <td style="padding:10px 14px;font-size:.88rem;color:#374151">{child_name}</td>
            </tr>
            <tr style="background:#f9fafb">
              <td style="padding:10px 14px;font-weight:700;font-size:.88rem;color:#374151">Vaccine</td>
              <td style="padding:10px 14px;font-size:.88rem;color:#374151">{vaccine_name}</td>
            </tr>
            <tr style="background:#fff">
              <td style="padding:10px 14px;font-weight:700;font-size:.88rem;color:#374151">Comment</td>
              <td style="padding:10px 14px;font-size:.88rem;color:#374151;font-style:italic">
                {comment or '<em style="color:#9ca3af">No comment provided</em>'}
              </td>
            </tr>
          </table>
          <div style="background:#fff3e0;border:1px solid #ffcc80;border-radius:8px;padding:14px 18px;margin-bottom:20px">
            <p style="margin:0;font-size:.88rem;color:#e65100">
              <strong>⚠️ Action Required:</strong> Please review this feedback and take
              appropriate steps to improve patient experience at your hospital.
            </p>
          </div>
          <p style="font-size:.8rem;color:#9ca3af;margin:0;border-top:1px solid #f1f5f9;padding-top:14px">
            This alert was sent by the Child Vaccination System Admin — Feedback ID #{feedback_id}
          </p>
        </div>
        </body></html>"""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 Low Rating Alert (Feedback #{feedback_id}) — Action Required"
        msg["From"]    = SMTP_USER
        msg["To"]      = hosp_email
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, [hosp_email], msg.as_string())
        return True
    except Exception:
        return False

# ─── HANDLE ALERT ACTION ──────────────────────────────────────────────────────
form      = cgi.FieldStorage()
action    = form.getvalue("action", "")
alert_msg = ""

if action == "send_alert":
    fid = form.getvalue("feedback_id", "")
    if fid:
        cur.execute("""
            SELECT f.feedback_id, f.rating, f.comment,
                   p.father_name, c.child_name, v.vaccine_name,
                   h.hospital_name, h.email
            FROM feedback f
            JOIN parent   p ON f.parent_id   = p.parent_id
            JOIN children c ON f.child_id    = c.child_id
            JOIN vaccine  v ON f.vaccine_id  = v.vaccine_id
            JOIN hospital h ON f.hospital_id = h.hospital_id
            WHERE f.feedback_id = %s
        """, (fid,))
        row = cur.fetchone()
        if row:
            ok = send_alert_to_hospital(
                hosp_email   = row[7], hosp_name    = row[6],
                parent_name  = row[3], child_name   = row[4],
                vaccine_name = row[5], rating       = row[1],
                comment      = row[2], feedback_id  = row[0]
            )
            if ok:
                cur.execute("UPDATE feedback SET notified=1 WHERE feedback_id=%s", (fid,))
                con.commit()
                alert_msg = f'<div class="amsg amsg-ok"><i class="fa-solid fa-circle-check"></i> Alert email sent to <strong>{row[6]}</strong> hospital manager for Feedback #{fid}.</div>'
            else:
                alert_msg = '<div class="amsg amsg-err"><i class="fa-solid fa-triangle-exclamation"></i> Failed to send email. Check SMTP settings.</div>'

# ─── COUNTS ───────────────────────────────────────────────────────────────────
pending_parents    = qc("SELECT COUNT(*) FROM parent WHERE status='pending'")
approved_parents   = qc("SELECT COUNT(*) FROM parent WHERE status='approved'")
rejected_parents   = qc("SELECT COUNT(*) FROM parent WHERE status='rejected'")
pending_hospitals  = qc("SELECT COUNT(*) FROM hospital WHERE status='pending'")
approved_hospitals = qc("SELECT COUNT(*) FROM hospital WHERE status='approved'")
rejected_hospitals = qc("SELECT COUNT(*) FROM hospital WHERE status='rejected'")
total_notified     = qc("SELECT COUNT(*) FROM child_vaccine WHERE status='notified'")
total_children     = qc("SELECT COUNT(*) FROM children")
total_completed    = qc("SELECT COUNT(*) FROM child_vaccine WHERE status='completed'")
total_fb           = qc("SELECT COUNT(*) FROM feedback")
low_fb             = qc("SELECT COUNT(*) FROM feedback WHERE rating < 2")

def nb(n, cls=""):
    return f'<span class="nbadge {cls}">{n}</span>' if n else ""
def sb(n):
    return f'<span class="nbadge" style="margin-left:auto">{n}</span>' if n else ""

# ─── FEEDBACK DATA ────────────────────────────────────────────────────────────
cur.execute("""
    SELECT f.feedback_id, f.rating, f.comment, f.submitted_at, f.updated_at, f.notified,
           p.father_name, p.email, p.mobile_number,
           c.child_name, c.dob, c.gender, c.blood_group,
           v.vaccine_name, v.minimum_age,
           h.hospital_name, h.state, h.district,
           cv.dose_number, cv.appointment_date
    FROM feedback f
    JOIN parent   p  ON f.parent_id   = p.parent_id
    JOIN children c  ON f.child_id    = c.child_id
    JOIN vaccine  v  ON f.vaccine_id  = v.vaccine_id
    JOIN hospital h  ON f.hospital_id = h.hospital_id
    LEFT JOIN child_vaccine cv ON cv.id = (
        SELECT id FROM child_vaccine
        WHERE child_id=f.child_id AND vaccine_id=f.vaccine_id AND hospital_id=f.hospital_id
        ORDER BY appointment_date DESC LIMIT 1
    )
    WHERE f.rating < 2
    ORDER BY f.submitted_at DESC
""")
feedbacks   = cur.fetchall()
total_low   = len(feedbacks)
alerted     = sum(1 for f in feedbacks if f[5])
not_alerted = total_low - alerted

# ─── CHILDREN DATA ────────────────────────────────────────────────────────────
cur.execute("""
    SELECT c.child_id, c.child_name, c.dob, c.weight, c.gender,
           c.blood_group, c.identification_mark,
           p.father_name, p.mother_name, p.email, p.mobile_number,
           p.state, p.district, p.address, p.occupation, p.status
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
        FROM child_vaccine a
        JOIN hospital h ON a.hospital_id = h.hospital_id
        WHERE a.status IN ('notified','taken','completed')
    """)
    for r in cur.fetchall():
        hosp_by_child[r[0]] = {"name": r[1], "number": r[2], "state": r[3], "district": r[4]}
except Exception:
    pass

tp = (f'<a href="adminpendingparent.py" class="talert pa">'
      f'<i class="fa-solid fa-user-clock"></i>'
      f'<span> {pending_parents} Parent Pending</span></a>') if pending_parents else ""
th_alert = (f'<a href="adminpendingmanager.py" class="talert ho">'
            f'<i class="fa-solid fa-hospital"></i>'
            f'<span> {pending_hospitals} Hospital Pending</span></a>') if pending_hospitals else ""

# ─── HTML ─────────────────────────────────────────────────────────────────────
print("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Low Ratings | Admin</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    *,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
    :root{
      --p:#1565c0;--pd:#0d47a1;--pl:#e3f2fd;--ac:#ff6f00;
      --sw:260px;--hh:60px;--tx:#1c1c1c;--mu:#6b7280;
      --bg:#f0f4f8;--ca:#fff;--bo:#dde3ea;
      --da:#e53935;--dl:#ffebee;--su:#2e7d32;--sl:#e8f5e9;
      --wa:#f57f17;--wl:#fff8e1;
      --ra:10px;--sh:0 2px 16px rgba(0,0,0,.09);
      --tr:.25s ease;--fn:'Segoe UI',Arial,sans-serif
    }
    html{scroll-behavior:smooth}
    body{font-family:var(--fn);background:var(--bg);color:var(--tx);min-height:100vh;line-height:1.6}
    a{text-decoration:none;color:inherit}
    .overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1100}
    .overlay.active{display:block}

    /* SIDEBAR */
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
    .nbadge.or{background:var(--ac)}.nbadge.gr{background:#2e7d32}.nbadge.gy{background:#777}
    .sfooter{padding:14px 12px;border-top:1px solid rgba(255,255,255,.12)}
    .btn-logout{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:10px;background:var(--da);color:#fff;border:none;border-radius:var(--ra);font-size:.88rem;font-weight:600;font-family:var(--fn);cursor:pointer;text-decoration:none;transition:background var(--tr)}
    .btn-logout:hover{background:#b71c1c}

    /* MAIN */
    .mwrap{margin-left:var(--sw);display:flex;flex-direction:column;min-height:100vh}
    .topbar{height:var(--hh);background:var(--ca);border-bottom:1px solid var(--bo);position:sticky;top:0;z-index:900;display:flex;align-items:center;justify-content:space-between;padding:0 20px;box-shadow:0 1px 8px rgba(0,0,0,.06)}
    .tbl{display:flex;align-items:center;gap:12px}
    .ttitle{font-size:1rem;font-weight:700;color:var(--da)}
    .hamburger{display:none;flex-direction:column;gap:5px;background:transparent;border:none;cursor:pointer;padding:6px;border-radius:6px}
    .hamburger span{display:block;width:22px;height:2px;background:var(--tx);border-radius:2px;transition:transform var(--tr),opacity var(--tr)}
    .hamburger.open span:nth-child(1){transform:translateY(7px) rotate(45deg)}
    .hamburger.open span:nth-child(2){opacity:0}
    .hamburger.open span:nth-child(3){transform:translateY(-7px) rotate(-45deg)}
    .tbr{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
    .abadge{background:var(--dl);color:var(--da);padding:5px 14px;border-radius:20px;font-size:.82rem;font-weight:600}
    .talert{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:20px;font-size:.78rem;font-weight:700}
    .talert.pa{background:#fff3e0;color:#e65100}
    .talert.ho{background:#e8f5e9;color:#2e7d32}
    .pc{padding:24px 20px;flex:1}

    /* SECTIONS */
    .section{display:none}.section.active{display:block}

    /* ALERT MESSAGE */
    .amsg{display:flex;align-items:center;gap:10px;padding:13px 18px;border-radius:var(--ra);margin-bottom:18px;font-size:.9rem;font-weight:600}
    .amsg-ok{background:var(--sl);color:var(--su);border:1px solid #a5d6a7}
    .amsg-err{background:var(--dl);color:var(--da);border:1px solid #ef9a9a}

    /* PAGE HEADER */
    .page-hdr{border-radius:var(--ra);padding:22px 28px;margin-bottom:24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
    .page-hdr.red{background:linear-gradient(120deg,#b71c1c,#e53935);color:#fff}
    .page-hdr.blue{background:linear-gradient(120deg,var(--p),var(--pd));color:#fff}
    .page-hdr h2{font-size:1.1rem;font-weight:700;margin-bottom:3px}
    .page-hdr p{font-size:.83rem;opacity:.85;margin:0}
    .page-hdr-badge{background:rgba(255,255,255,.2);padding:7px 16px;border-radius:20px;font-size:.83rem;font-weight:700}

    /* STATS */
    .stats-row{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:14px;margin-bottom:24px}
    .stat-card{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);padding:16px 18px;display:flex;align-items:center;gap:14px}
    .stat-icon{width:44px;height:44px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.2rem;flex-shrink:0}
    .stat-val{font-size:1.5rem;font-weight:800;line-height:1}
    .stat-lbl{font-size:.75rem;color:var(--mu);margin-top:3px}

    /* TOOLBAR */
    .toolbar{display:flex;align-items:center;gap:12px;margin-bottom:18px;flex-wrap:wrap}
    .sbox{position:relative;flex:1;min-width:200px}
    .sbox i{position:absolute;left:11px;top:50%;transform:translateY(-50%);color:var(--mu);font-size:.82rem}
    .sbox input{width:100%;padding:9px 12px 9px 34px;border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.85rem;background:var(--ca);transition:border-color var(--tr)}
    .sbox input:focus{outline:none;border-color:var(--p)}
    .fsel{padding:9px 14px;border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.85rem;background:var(--ca);color:var(--tx);cursor:pointer}
    .fsel:focus{outline:none;border-color:var(--p)}
    .cnt-lbl{font-size:.84rem;color:var(--mu);font-weight:600;white-space:nowrap}

    /* FEEDBACK CARDS */
    .fb-card{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);border-left:4px solid var(--da);background:#fffafa;margin-bottom:16px;overflow:hidden;transition:box-shadow var(--tr)}
    .fb-card:hover{box-shadow:0 4px 20px rgba(0,0,0,.13)}
    .fb-card.done{border-left-color:var(--su);background:#f9fff9}
    .fb-top{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;flex-wrap:wrap;gap:10px}
    .fb-left{display:flex;align-items:center;gap:14px}
    .fb-avatar{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--da),#c62828);display:flex;align-items:center;justify-content:center;font-size:1.1rem;font-weight:800;color:#fff;flex-shrink:0}
    .fb-avatar.done{background:linear-gradient(135deg,var(--su),#1b5e20)}
    .fb-name{font-size:.95rem;font-weight:700}
    .fb-meta{font-size:.76rem;color:var(--mu);margin-top:2px}
    .stars-big{font-size:1.2rem;line-height:1}
    .rating-num{font-size:.9rem;font-weight:800;color:var(--da)}
    .badge-alerted{background:var(--sl);color:var(--su);padding:3px 10px;border-radius:20px;font-size:.73rem;font-weight:700}
    .badge-pending{background:var(--dl);color:var(--da);padding:3px 10px;border-radius:20px;font-size:.73rem;font-weight:700}
    .badge-edited{background:var(--pl);color:var(--p);padding:3px 10px;border-radius:20px;font-size:.73rem;font-weight:700}
    .btn-expand{display:inline-flex;align-items:center;gap:6px;padding:7px 16px;background:var(--p);color:#fff;border:none;border-radius:8px;font-size:.82rem;font-weight:600;font-family:var(--fn);cursor:pointer;transition:background var(--tr)}
    .btn-expand:hover{background:var(--pd)}
    .btn-alert{display:inline-flex;align-items:center;gap:6px;padding:7px 16px;background:var(--da);color:#fff;border:none;border-radius:8px;font-size:.82rem;font-weight:600;font-family:var(--fn);cursor:pointer;transition:background var(--tr);text-decoration:none}
    .btn-alert:hover{background:#b71c1c;color:#fff}
    .btn-alert.sent{background:var(--su);cursor:default;pointer-events:none}
    .fb-detail{display:none;border-top:1px solid var(--bo);padding:18px 20px}
    .fb-detail.open{display:block}
    .detail-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px 20px;margin-bottom:14px}
    .di{background:var(--bg);border:1px solid var(--bo);border-radius:8px;padding:9px 13px}
    .di label{display:block;font-size:.67rem;color:var(--mu);font-weight:700;text-transform:uppercase;letter-spacing:.4px;margin-bottom:3px}
    .di span{font-size:.86rem;font-weight:600;color:var(--tx);word-break:break-word}
    .comment-box{background:#fff5f5;border:1px solid #fca5a5;border-radius:8px;padding:12px 16px}
    .comment-box p{font-size:.88rem;color:var(--tx)}
    .section-title{font-size:.72rem;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:.8px;margin:14px 0 8px;display:flex;align-items:center;gap:6px}
    .section-title::after{content:'';flex:1;height:1px;background:var(--bo)}

    /* CHILDREN CARDS */
    .child-card{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);margin-bottom:16px;overflow:hidden}
    .ccard-top{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;flex-wrap:wrap;gap:10px}
    .ccard-left{display:flex;align-items:center;gap:14px}
    .avatar{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--p),var(--pd));border:2px solid var(--pl);display:flex;align-items:center;justify-content:center;font-size:1.15rem;font-weight:800;color:#fff;flex-shrink:0}
    .ccard-name{font-size:.96rem;font-weight:700}
    .ccard-sub{font-size:.76rem;color:var(--mu);margin-top:2px}
    .ccard-right{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
    .bx{display:inline-flex;align-items:center;padding:3px 10px;border-radius:20px;font-size:.74rem;font-weight:700}
    .bp{background:#fff8e1;color:#f57f17}.ba{background:#e8f5e9;color:#2e7d32}
    .br{background:#ffebee;color:#c62828}.bn{background:#fff3e0;color:#e65100}
    .bt{background:#e8f5e9;color:#2e7d32}.bgy{background:#f3f4f6;color:#555}
    .btn-viewmore{display:inline-flex;align-items:center;gap:6px;padding:7px 16px;background:var(--p);color:#fff;border:none;border-radius:8px;font-size:.82rem;font-weight:600;font-family:var(--fn);cursor:pointer;transition:background var(--tr)}
    .btn-viewmore:hover{background:var(--pd)}
    .ccard-details{display:none;border-top:1px solid var(--bo)}
    .ccard-details.open{display:block}
    .detail-tabs{display:flex;border-bottom:2px solid var(--bo);background:#fafbfc}
    .dtab{flex:1;background:transparent;border:none;border-bottom:3px solid transparent;margin-bottom:-2px;padding:11px 10px;font-family:var(--fn);font-size:.83rem;font-weight:600;color:var(--mu);cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;transition:color var(--tr),border-color var(--tr),background var(--tr);white-space:nowrap}
    .dtab:hover{color:var(--p);background:var(--pl)}
    .dtab.active{color:var(--p);border-bottom-color:var(--ac);background:#f0f7ff}
    .dpanel{display:none;padding:18px 20px}
    .dpanel.active{display:block}
    .dg{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px 20px}
    .dg .di.full{grid-column:1/-1}
    .vsumbadges{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
    .vsb{display:flex;align-items:center;gap:5px;padding:5px 14px;border-radius:20px;font-size:.76rem;font-weight:700}
    .vsb.tk{background:#e8f5e9;color:#2e7d32}.vsb.nt{background:#fff3e0;color:#e65100}.vsb.pd{background:#fff8e1;color:#f57f17}
    .vtable{width:100%;border-collapse:collapse;font-size:.83rem}
    .vtable th{background:#f0f4f8;color:var(--p);padding:8px 12px;text-align:left;font-size:.74rem;font-weight:700;text-transform:uppercase;border-bottom:2px solid var(--bo)}
    .vtable td{padding:8px 12px;border-bottom:1px solid var(--bo)}
    .vtable tbody tr:hover{background:var(--pl)}
    .vtable tbody tr:last-child td{border-bottom:none}

    .empty{text-align:center;padding:80px 20px;color:var(--mu)}
    .empty i{font-size:3.5rem;opacity:.25;display:block;margin-bottom:16px}
    .empty h3{font-size:1.1rem;font-weight:700;margin-bottom:6px;color:var(--su)}
    .empty p{font-size:.88rem}
    footer{background:#1c1c2e;color:rgba(255,255,255,.6);text-align:center;padding:14px 20px;font-size:.8rem}

    @media(max-width:1024px){:root{--sw:230px}}
    @media(max-width:768px){
      .sidebar{transform:translateX(-100%)}.sidebar.open{transform:translateX(0)}
      .mwrap{margin-left:0}.hamburger{display:flex}
      .pc{padding:16px 12px}.abadge{display:none}
      .detail-tabs{overflow-x:auto}
    }
    @media(max-width:480px){
      .talert span{display:none}.detail-grid,.dg{grid-template-columns:1fr 1fr}
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
    <div class="ng open" id="g6">
      <button class="ngt" onclick="tg('g6')">
        <i class="fa-solid fa-star ic"></i> Feedback {nb(low_fb,"or") if low_fb else ""}
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a href="adminparentfeedback.py"><i class="fa-solid fa-list"></i> All Feedback {sb(total_fb)}</a>
        <a onclick="showSection('sec-lowratings')" id="link-lowratings" class="active">
          <i class="fa-solid fa-triangle-exclamation"></i> Low Ratings {nb(total_low) if total_low else ""}
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
      <span class="ttitle" id="page-title"><i class="fa-solid fa-triangle-exclamation"></i> Low Rating Alerts</span>
    </div>
    <div class="tbr">
      {tp}{th_alert}
      <span class="abadge"><i class="fa-solid fa-shield-halved"></i> Admin</span>
    </div>
  </header>
  <main class="pc">
""")

# ======================================================
# SECTION 1 — LOW RATINGS
# ======================================================
print(f"""
<div class="section active" id="sec-lowratings">

  {alert_msg}

  <div class="page-hdr red">
    <div>
      <h2><i class="fa-solid fa-triangle-exclamation"></i>&nbsp; Low Rating Feedback</h2>
      <p>Feedbacks with rating below 2 stars — alert hospital managers to take action</p>
    </div>
    <span class="page-hdr-badge">🚨 {total_low} Low Rating{'s' if total_low != 1 else ''}</span>
  </div>

  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-icon" style="background:var(--dl);color:var(--da)"><i class="fa-solid fa-triangle-exclamation"></i></div>
      <div><div class="stat-val" style="color:var(--da)">{total_low}</div><div class="stat-lbl">Total Low Ratings</div></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon" style="background:var(--dl);color:var(--da)"><i class="fa-solid fa-bell"></i></div>
      <div><div class="stat-val" style="color:var(--da)">{not_alerted}</div><div class="stat-lbl">Pending Alerts</div></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon" style="background:var(--sl);color:var(--su)"><i class="fa-solid fa-circle-check"></i></div>
      <div><div class="stat-val" style="color:var(--su)">{alerted}</div><div class="stat-lbl">Hospitals Alerted</div></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon" style="background:var(--pl);color:var(--p)"><i class="fa-solid fa-comments"></i></div>
      <div><div class="stat-val" style="color:var(--p)">{total_fb}</div><div class="stat-lbl">Total Feedbacks</div></div>
    </div>
  </div>

  <div class="toolbar">
    <div class="sbox">
      <i class="fa-solid fa-magnifying-glass"></i>
      <input type="text" id="fbSearch" placeholder="Search parent, child, vaccine, hospital..." oninput="filterFeedback()">
    </div>
    <select class="fsel" id="alertFilter" onchange="filterFeedback()">
      <option value="">All</option>
      <option value="pending">Pending Alert</option>
      <option value="alerted">Already Alerted</option>
    </select>
    <span class="cnt-lbl" id="fbCntLbl">{total_low} records</span>
  </div>
""")

if not feedbacks:
    print("""
  <div class="empty">
    <i class="fa-solid fa-face-smile-beam"></i>
    <h3>No Low Ratings!</h3>
    <p>All feedback has a rating of 2 stars or above. Great job!</p>
  </div>
""")
else:
    for fb in feedbacks:
        fb_id        = fb[0];  rating      = fb[1];  comment     = fb[2] or ""
        submitted    = str(fb[3])[:16]
        updated      = str(fb[4])[:16] if fb[4] else None
        notified     = fb[5]
        parent_name  = fb[6];  parent_email = fb[7]; parent_mob  = fb[8]
        child_name   = fb[9];  child_dob    = str(fb[10]) if fb[10] else "N/A"
        child_gender = fb[11] or "N/A"; child_blood = fb[12] or "N/A"
        vaccine      = fb[13]; min_age      = fb[14] or "N/A"
        hospital     = fb[15]; hosp_state   = fb[16] or "N/A"; hosp_dist = fb[17] or "N/A"
        dose         = fb[18] or "N/A"; appt_date = str(fb[19])[:10] if fb[19] else "N/A"

        filled     = "⭐" * rating
        empty_s    = '<span style="color:#d1d5db">' + "★" * (5 - rating) + "</span>"
        initial    = parent_name[0].upper() if parent_name else "P"
        card_cls   = "done" if notified else ""
        av_cls     = "done" if notified else ""
        data_alert = "alerted" if notified else "pending"

        if notified:
            alert_btn = '<span class="btn-alert sent"><i class="fa-solid fa-circle-check"></i> Hospital Alerted</span>'
        else:
            alert_btn = (f'<a href="adminlowratings.py?action=send_alert&feedback_id={fb_id}" '
                         f'class="btn-alert" '
                         f'onclick="return confirm(\'Send low rating alert to {hospital} manager?\')"> '
                         f'<i class="fa-solid fa-bell"></i> Alert Hospital</a>')

        print(f"""
  <div class="fb-card {card_cls}"
       data-search="{parent_name.lower()} {child_name.lower()} {vaccine.lower()} {hospital.lower()}"
       data-alert="{data_alert}">
    <div class="fb-top">
      <div class="fb-left">
        <div class="fb-avatar {av_cls}">{initial}</div>
        <div>
          <div class="fb-name">{parent_name}</div>
          <div class="fb-meta">👶 {child_name} &bull; 💉 {vaccine} &bull; 🏥 {hospital}</div>
          <div class="fb-meta" style="margin-top:3px;">
            🗓️ {submitted}
            {"&nbsp;<span class='badge-edited'>✏️ Edited " + updated + "</span>" if updated else ""}
            {"&nbsp;<span class='badge-alerted'>✅ Hospital Alerted</span>" if notified else "&nbsp;<span class='badge-pending'>🚨 Action Needed</span>"}
          </div>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
        <div style="text-align:center;">
          <div class="stars-big">{filled}{empty_s}</div>
          <div class="rating-num">{rating}/5</div>
        </div>
        {alert_btn}
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
      <div class="section-title"><i class="fa-solid fa-syringe"></i> Vaccine &amp; Hospital Details</div>
      <div class="detail-grid">
        <div class="di"><label>Vaccine Name</label><span>{vaccine}</span></div>
        <div class="di"><label>Min Age</label><span>{min_age}</span></div>
        <div class="di"><label>Dose No.</label><span>{dose}</span></div>
        <div class="di"><label>Appointment Date</label><span>{appt_date}</span></div>
        <div class="di"><label>Hospital</label><span>{hospital}</span></div>
        <div class="di"><label>State</label><span>{hosp_state}</span></div>
        <div class="di"><label>District</label><span>{hosp_dist}</span></div>
      </div>
      <div class="section-title"><i class="fa-solid fa-comment"></i> Comment</div>
      <div class="comment-box">
        <p>{"<em style='color:#9ca3af'>No comment provided</em>" if not comment else comment}</p>
      </div>
    </div>
  </div>
""")

print("</div><!-- /sec-lowratings -->")

# ======================================================
# SECTION 2 — CHILDREN DETAILS (exact same as admin_dash)
# ======================================================
print(f"""
<div class="section" id="sec-children">
  <div class="page-hdr blue">
    <div>
      <h2><i class="fa-solid fa-children"></i>&nbsp; Registered Children</h2>
      <p>Click <strong>View More</strong> on any child to see parent, vaccine &amp; hospital details</p>
    </div>
    <span class="page-hdr-badge"><i class="fa-solid fa-child"></i> {total_children} Total</span>
  </div>
  <div class="toolbar">
    <div class="sbox">
      <i class="fa-solid fa-magnifying-glass"></i>
      <input type="text" id="childSearch" placeholder="Search child name, father, mobile, blood group..." oninput="filterChildren()">
    </div>
    <select class="fsel" id="genderFilter" onchange="filterChildren()">
      <option value="">All Genders</option>
      <option value="male">Male</option>
      <option value="female">Female</option>
    </select>
    <select class="fsel" id="vacFilter" onchange="filterChildren()">
      <option value="">All Vaccine Status</option>
      <option value="taken">Has Taken</option>
      <option value="notified">Notified</option>
      <option value="pending">Pending</option>
    </select>
    <span class="cnt-lbl" id="childCntLbl">{len(children_raw)} records</span>
  </div>
""")

if not children_raw:
    print('<div class="empty"><i class="fa-solid fa-child-reaching"></i><p>No registered children found.</p></div>')
else:
    for r in children_raw:
        cid      = r[0]
        cname    = r[1]  or "&mdash;"
        dob      = str(r[2]) if r[2] else "&mdash;"
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

        pbc     = {"approved":"ba","rejected":"br","pending":"bp"}.get(pstatus,"bp")
        gicon   = "fa-mars" if str(r[4] or "").lower()=="male" else ("fa-venus" if str(r[4] or "").lower()=="female" else "fa-genderless")
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
            vd = str(v["date"]) if v["date"] else "&mdash;"
            bc = "bt" if vs=="taken" else ("bn" if vs=="notified" else "bp")
            vrows += (f"<tr><td>{idx}</td><td><strong>{v['name']}</strong></td>"
                      f"<td>{v['age']} mo.</td><td>{vd}</td>"
                      f"<td><span class='bx {bc}'>{vs.capitalize()}</span></td></tr>")
        if not vrows:
            vrows = "<tr><td colspan='5' style='text-align:center;color:#bbb;padding:14px'>No vaccines assigned yet</td></tr>"

        print(f"""
  <div class="child-card"
       data-name="{str(r[1] or '').lower()}"
       data-father="{str(r[7] or '').lower()}"
       data-mobile="{mobile}"
       data-blood="{str(r[5] or '').lower()}"
       data-gender="{str(r[4] or '').lower()}"
       data-vacstatus="{vac_st}">
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
        <button class="btn-viewmore" onclick="toggleDetails(this,'det{cid}')">
          <i class="fa-solid fa-chevron-down vm-icon"></i> View More
        </button>
      </div>
    </div>
    <div class="ccard-details" id="det{cid}">
      <div class="detail-tabs" id="tabs{cid}">
        <button class="dtab active" onclick="switchDTab({cid},'parent')"><i class="fa-solid fa-users"></i> Parent</button>
        <button class="dtab" onclick="switchDTab({cid},'vaccine')"><i class="fa-solid fa-syringe"></i> Vaccine</button>
        <button class="dtab" onclick="switchDTab({cid},'hospital')"><i class="fa-solid fa-hospital"></i> Hospital</button>
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
  const titles={
    'sec-lowratings':'Low Rating Alerts',
    'sec-children':'Child Details'
  };
  const icons={
    'sec-lowratings':'<i class="fa-solid fa-triangle-exclamation"></i> ',
    'sec-children':'<i class="fa-solid fa-children"></i> '
  };
  document.getElementById('page-title').innerHTML=(icons[id]||'')+titles[id];
  document.querySelectorAll('.nsub a').forEach(a=>a.classList.remove('active'));
  const linkMap={
    'sec-lowratings':'link-lowratings',
    'sec-children':'link-children'
  };
  const groupMap={
    'sec-lowratings':'g6',
    'sec-children':'g5'
  };
  document.querySelectorAll('.ng').forEach(x=>x.classList.remove('open'));
  if(linkMap[id]) document.getElementById(linkMap[id]).classList.add('active');
  if(groupMap[id]) document.getElementById(groupMap[id]).classList.add('open');
  window.scrollTo(0,0);
  closeSB();
}

// Feedback expand/collapse
function toggleDetail(btn,detId){
  const det=document.getElementById(detId);
  const isOpen=det.classList.contains('open');
  det.classList.toggle('open',!isOpen);
  btn.innerHTML=isOpen
    ?'<i class="fa-solid fa-chevron-down"></i> View More'
    :'<i class="fa-solid fa-chevron-up"></i> View Less';
}

// Feedback filter
function filterFeedback(){
  const q=document.getElementById('fbSearch').value.toLowerCase();
  const af=document.getElementById('alertFilter').value;
  let visible=0;
  document.querySelectorAll('.fb-card').forEach(card=>{
    const matchQ=!q||card.dataset.search.includes(q);
    const matchA=!af||card.dataset.alert===af;
    const show=matchQ&&matchA;
    card.style.display=show?'':'none';
    if(show)visible++;
  });
  document.getElementById('fbCntLbl').textContent=visible+' record'+(visible!==1?'s':'');
}

// Children expand/collapse
function toggleDetails(btn,detId){
  const det=document.getElementById(detId);
  const isOpen=det.classList.contains('open');
  det.classList.toggle('open',!isOpen);
  btn.innerHTML=isOpen
    ?'<i class="fa-solid fa-chevron-down vm-icon"></i> View More'
    :'<i class="fa-solid fa-chevron-up vm-icon"></i> View Less';
}

// Children tab switch
function switchDTab(cid,tabName){
  const panels=['parent','vaccine','hospital'];
  const btns=document.getElementById('tabs'+cid).querySelectorAll('.dtab');
  panels.forEach((p,i)=>{
    const el=document.getElementById('dp'+cid+'-'+p);
    if(el) el.classList.toggle('active',p===tabName);
    if(btns[i]) btns[i].classList.toggle('active',p===tabName);
  });
}

// Children filter
function filterChildren(){
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
  document.getElementById('childCntLbl').textContent=visible+' record'+(visible!==1?'s':'');
}
</script>
</body>
</html>
""")

con.close()