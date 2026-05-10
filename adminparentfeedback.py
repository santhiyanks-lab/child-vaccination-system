#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
import sys, pymysql, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
sys.stdout.reconfigure(encoding="utf-8")
print("Content-Type:text/html\r\n\r\n")

import cgi, cgitb
cgitb.enable()

con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()

def qc(sql):
    cur.execute(sql)
    return cur.fetchone()[0]
# Feedback counts
total_fb = qc("SELECT COUNT(*) FROM feedback")
low_fb   = qc("SELECT COUNT(*) FROM feedback WHERE rating < 2")

# ─── EMAIL CONFIG ─────────────────────────────────────────────────────────────
SMTP_HOST  = "smtp.gmail.com"
SMTP_PORT  = 587
SMTP_USER  = "santhiyanks@gmail.com"
SMTP_PASS  = "snnr avxt cqgb ocwy"
ADMIN_EMAIL= "santhiyanks@gmail.com"

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
              <td style="padding:10px 14px;font-size:.88rem;color:#374151">{stars} &nbsp;<strong>({rating}/5)</strong></td>
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
              Respond to the parent's concern promptly.
            </p>
          </div>
          <p style="font-size:.8rem;color:#9ca3af;margin:0;border-top:1px solid #f1f5f9;padding-top:14px">
            This alert was sent by the Child Vaccination System Admin &mdash; Feedback ID #{feedback_id}
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
    except Exception as e:
        return False

# ─── HANDLE ALERT ACTION ──────────────────────────────────────────────────────
form   = cgi.FieldStorage()
action = form.getvalue("action", "")
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
                hosp_email   = row[7],
                hosp_name    = row[6],
                parent_name  = row[3],
                child_name   = row[4],
                vaccine_name = row[5],
                rating       = row[1],
                comment      = row[2],
                feedback_id  = row[0]
            )
            # Mark as notified
            if ok:
                cur.execute("UPDATE feedback SET notified=1 WHERE feedback_id=%s", (fid,))
                con.commit()
                alert_msg = f'<div class="amsg amsg-ok"><i class="fa-solid fa-circle-check"></i> Alert email sent successfully to <strong>{row[6]}</strong> hospital manager for Feedback #{fid}.</div>'
            else:
                alert_msg = f'<div class="amsg amsg-err"><i class="fa-solid fa-triangle-exclamation"></i> Failed to send email. Check SMTP settings.</div>'
        else:
            alert_msg = '<div class="amsg amsg-err">Feedback not found.</div>'

# ─── STATS ───────────────────────────────────────────────────────────────────
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

# ─── ALL FEEDBACKS ────────────────────────────────────────────────────────────
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
    ORDER BY f.submitted_at DESC
""")
feedbacks = cur.fetchall()

total_fb   = len(feedbacks)
low_fb     = sum(1 for f in feedbacks if f[1] < 2)
avg_rating = round(sum(f[1] for f in feedbacks) / total_fb, 1) if total_fb else 0

tp = (f'<a href="adminpendingparent.py" class="talert pa">'
      f'<i class="fa-solid fa-user-clock"></i>'
      f'<span> {pending_parents} Parent Pending</span></a>') if pending_parents else ""
th_alert = (f'<a href="adminpendingmanager.py" class="talert ho">'
            f'<i class="fa-solid fa-hospital"></i>'
            f'<span> {pending_hospitals} Hospital Pending</span></a>') if pending_hospitals else ""

print(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Feedback | Admin</title>
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
    .overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1100}}
    .overlay.active{{display:block}}

    /* SIDEBAR */
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
    .nlink{{display:flex;align-items:center;gap:10px;padding:13px 16px;color:rgba(255,255,255,.88);font-size:.88rem;font-weight:500;transition:background var(--tr),color var(--tr);border-left:3px solid transparent}}
    .nlink:hover,.nlink.active{{background:rgba(255,255,255,.1);color:#fff;border-left-color:var(--ac)}}
    .nlink .ic{{font-size:.95rem;width:20px;text-align:center;flex-shrink:0}}
    .sfooter{{padding:14px 12px;border-top:1px solid rgba(255,255,255,.12)}}
    .btn-logout{{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:10px;background:var(--da);color:#fff;border:none;border-radius:var(--ra);font-size:.88rem;font-weight:600;font-family:var(--fn);cursor:pointer;text-decoration:none;transition:background var(--tr)}}
    .btn-logout:hover{{background:#b71c1c}}

    /* MAIN */
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
    .tbr{{display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
    .abadge{{background:var(--pl);color:var(--p);padding:5px 14px;border-radius:20px;font-size:.82rem;font-weight:600}}
    .talert{{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:20px;font-size:.78rem;font-weight:700}}
    .talert.pa{{background:#fff3e0;color:#e65100}}
    .talert.ho{{background:#e8f5e9;color:#2e7d32}}
    .pc{{padding:24px 20px;flex:1}}

    /* ALERT MESSAGE */
    .amsg{{display:flex;align-items:center;gap:10px;padding:13px 18px;border-radius:var(--ra);margin-bottom:18px;font-size:.9rem;font-weight:600}}
    .amsg-ok{{background:var(--sl);color:var(--su);border:1px solid #a5d6a7}}
    .amsg-err{{background:var(--dl);color:var(--da);border:1px solid #ef9a9a}}

    /* PAGE HEADER */
    .page-hdr{{background:linear-gradient(120deg,#f57f17,#ff8f00);color:#fff;border-radius:var(--ra);padding:22px 28px;margin-bottom:24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}}
    .page-hdr h2{{font-size:1.1rem;font-weight:700;margin-bottom:3px}}
    .page-hdr p{{font-size:.83rem;opacity:.85}}
    .page-hdr-badge{{background:rgba(255,255,255,.2);padding:7px 16px;border-radius:20px;font-size:.83rem;font-weight:700}}

    /* STATS ROW */
    .stats-row{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:14px;margin-bottom:24px}}
    .stat-card{{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);padding:16px 18px;display:flex;align-items:center;gap:14px}}
    .stat-icon{{width:44px;height:44px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.2rem;flex-shrink:0}}
    .stat-icon.yellow{{background:#fff8e1;color:#f57f17}}
    .stat-icon.red{{background:var(--dl);color:var(--da)}}
    .stat-icon.blue{{background:var(--pl);color:var(--p)}}
    .stat-icon.green{{background:var(--sl);color:var(--su)}}
    .stat-val{{font-size:1.5rem;font-weight:800;line-height:1}}
    .stat-lbl{{font-size:.75rem;color:var(--mu);margin-top:3px}}

    /* TOOLBAR */
    .toolbar{{display:flex;align-items:center;gap:12px;margin-bottom:18px;flex-wrap:wrap}}
    .sbox{{position:relative;flex:1;min-width:200px}}
    .sbox i{{position:absolute;left:11px;top:50%;transform:translateY(-50%);color:var(--mu);font-size:.82rem}}
    .sbox input{{width:100%;padding:9px 12px 9px 34px;border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.85rem;background:var(--ca);transition:border-color var(--tr)}}
    .sbox input:focus{{outline:none;border-color:var(--p)}}
    .fsel{{padding:9px 14px;border:1.5px solid var(--bo);border-radius:8px;font-family:var(--fn);font-size:.85rem;background:var(--ca);color:var(--tx);cursor:pointer}}
    .fsel:focus{{outline:none;border-color:var(--p)}}
    .cnt-lbl{{font-size:.84rem;color:var(--mu);font-weight:600;white-space:nowrap}}

    /* FEEDBACK CARDS */
    .fb-card{{background:var(--ca);border-radius:var(--ra);box-shadow:var(--sh);border:1px solid var(--bo);margin-bottom:16px;overflow:hidden;transition:box-shadow var(--tr)}}
    .fb-card:hover{{box-shadow:0 4px 20px rgba(0,0,0,.13)}}
    .fb-card.low{{border-left:4px solid var(--da);background:#fffafa}}
    .fb-card.high{{border-left:4px solid var(--su)}}
    .fb-top{{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;flex-wrap:wrap;gap:10px}}
    .fb-left{{display:flex;align-items:center;gap:14px}}
    .fb-avatar{{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#f57f17,#ff8f00);display:flex;align-items:center;justify-content:center;font-size:1.1rem;font-weight:800;color:#fff;flex-shrink:0}}
    .fb-avatar.low{{background:linear-gradient(135deg,var(--da),#c62828)}}
    .fb-avatar.high{{background:linear-gradient(135deg,var(--su),#1b5e20)}}
    .fb-name{{font-size:.95rem;font-weight:700}}
    .fb-meta{{font-size:.76rem;color:var(--mu);margin-top:2px}}
    .fb-right{{display:flex;align-items:center;gap:10px;flex-wrap:wrap}}
    .stars-big{{font-size:1.2rem;line-height:1}}
    .rating-num{{font-size:.9rem;font-weight:800}}
    .badge-low{{background:var(--dl);color:var(--da);padding:3px 10px;border-radius:20px;font-size:.73rem;font-weight:700}}
    .badge-notified{{background:#fff3e0;color:#e65100;padding:3px 10px;border-radius:20px;font-size:.73rem;font-weight:700}}
    .badge-alerted{{background:#e8f5e9;color:#2e7d32;padding:3px 10px;border-radius:20px;font-size:.73rem;font-weight:700}}
    .badge-edited{{background:var(--pl);color:var(--p);padding:3px 10px;border-radius:20px;font-size:.73rem;font-weight:700}}
    .btn-expand{{display:inline-flex;align-items:center;gap:6px;padding:7px 16px;background:var(--p);color:#fff;border:none;border-radius:8px;font-size:.82rem;font-weight:600;font-family:var(--fn);cursor:pointer;transition:background var(--tr)}}
    .btn-expand:hover{{background:var(--pd)}}

    /* ALERT BUTTON */
    .btn-alert{{display:inline-flex;align-items:center;gap:6px;padding:7px 16px;
      background:#e53935;color:#fff;border:none;border-radius:8px;
      font-size:.82rem;font-weight:600;font-family:var(--fn);cursor:pointer;
      transition:background var(--tr);text-decoration:none}}
    .btn-alert:hover{{background:#b71c1c;color:#fff}}
    .btn-alert.sent{{background:#2e7d32;cursor:default;pointer-events:none}}

    /* DETAIL PANEL */
    .fb-detail{{display:none;border-top:1px solid var(--bo);padding:18px 20px}}
    .fb-detail.open{{display:block}}
    .detail-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px 20px;margin-bottom:14px}}
    .di{{background:var(--bg);border:1px solid var(--bo);border-radius:8px;padding:9px 13px}}
    .di label{{display:block;font-size:.67rem;color:var(--mu);font-weight:700;text-transform:uppercase;letter-spacing:.4px;margin-bottom:3px}}
    .di span{{font-size:.86rem;font-weight:600;color:var(--tx);word-break:break-word}}
    .comment-box{{background:var(--bg);border:1px solid var(--bo);border-radius:8px;padding:12px 16px}}
    .comment-box label{{display:block;font-size:.68rem;color:var(--mu);font-weight:700;text-transform:uppercase;letter-spacing:.4px;margin-bottom:6px}}
    .comment-box p{{font-size:.88rem;color:var(--tx)}}
    .section-title{{font-size:.72rem;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:.8px;margin:14px 0 8px;display:flex;align-items:center;gap:6px}}
    .section-title::after{{content:'';flex:1;height:1px;background:var(--bo)}}

    .empty{{text-align:center;padding:60px 20px;color:var(--mu)}}
    .empty i{{font-size:3rem;opacity:.3;display:block;margin-bottom:14px}}

    footer{{background:#1c1c2e;color:rgba(255,255,255,.6);text-align:center;padding:14px 20px;font-size:.8rem}}

    @media(max-width:1024px){{:root{{--sw:230px}}}}
    @media(max-width:768px){{
      .sidebar{{transform:translateX(-100%)}}.sidebar.open{{transform:translateX(0)}}
      .mwrap{{margin-left:0}}.hamburger{{display:flex}}
      .pc{{padding:16px 12px}}.abadge{{display:none}}
    }}
    @media(max-width:480px){{
      .talert span{{display:none}}.detail-grid{{grid-template-columns:1fr 1fr}}
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
        <a href="admindashboard.py"><i class="fa-solid fa-child"></i> Child Details {sb(total_children)}</a>
        <a href="adminchildparent.py"><i class="fa-solid fa-users"></i> Parent Details</a>
        <a href="adminchildvaccine.py"><i class="fa-solid fa-syringe"></i> Vaccine Details</a>
        <a href="adminchildhospital.py"><i class="fa-solid fa-hospital"></i> Hospital Details</a>
      </div>
    </div>
    <div class="ng open" id="g6">
      <button class="ngt" onclick="tg('g6')">
        <i class="fa-solid fa-star ic"></i> Feedback {nb(total_fb,"or") if total_fb else ""}
        <i class="fa-solid fa-chevron-down ar"></i>
      </button>
      <div class="nsub">
        <a href="adminparentfeedback.py" class="active"><i class="fa-solid fa-list"></i> All Feedback {sb(total_fb)}</a>
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
        <div class="ttitle">Parent Feedback</div>
        <div class="tbcrumb">
          <a href="admindashboard.py">Dashboard</a>
          <span>&rsaquo;</span> Feedback <span>&rsaquo;</span> All Feedback
        </div>
      </div>
    </div>
    <div class="tbr">
      {tp}{th_alert}
      <span class="abadge"><i class="fa-solid fa-shield-halved"></i> Admin</span>
    </div>
  </header>

  <main class="pc">

    {alert_msg}

    <div class="page-hdr">
      <div>
        <h2><i class="fa-solid fa-star"></i>&nbsp; Parent Feedback</h2>
        <p>All vaccination feedback submitted by parents across all hospitals</p>
      </div>
      <span class="page-hdr-badge"><i class="fa-solid fa-comments"></i> {total_fb} Total Feedbacks</span>
    </div>

    <!-- STATS -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon yellow"><i class="fa-solid fa-star"></i></div>
        <div><div class="stat-val">{total_fb}</div><div class="stat-lbl">Total Feedbacks</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon blue"><i class="fa-solid fa-chart-bar"></i></div>
        <div><div class="stat-val">{avg_rating}</div><div class="stat-lbl">Avg Rating</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon red"><i class="fa-solid fa-triangle-exclamation"></i></div>
        <div><div class="stat-val">{low_fb}</div><div class="stat-lbl">Low Ratings (&lt;2)</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green"><i class="fa-solid fa-thumbs-up"></i></div>
        <div><div class="stat-val">{sum(1 for f in feedbacks if f[1]>=4)}</div><div class="stat-lbl">High Ratings (4-5)</div></div>
      </div>
    </div>

    <!-- TOOLBAR -->
    <div class="toolbar">
      <div class="sbox">
        <i class="fa-solid fa-magnifying-glass"></i>
        <input type="text" id="searchInput" placeholder="Search parent, child, vaccine, hospital..." oninput="filterCards()">
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
      <p>No feedback submitted yet.</p>
    </div>
""")
else:
    for i, fb in enumerate(feedbacks):
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
        hospital     = fb[15]
        hosp_state   = fb[16] or "N/A"
        hosp_dist    = fb[17] or "N/A"
        dose         = fb[18] or "N/A"
        appt_date    = str(fb[19])[:10] if fb[19] else "N/A"

        filled    = "⭐" * rating
        empty     = '<span style="color:#d1d5db">' + "★" * (5 - rating) + "</span>"
        card_cls  = "low" if rating < 2 else ("high" if rating >= 4 else "")
        av_cls    = "low" if rating < 2 else ("high" if rating >= 4 else "")
        initial   = parent_name[0].upper() if parent_name else "P"
        data_rating = "low" if rating < 2 else ("high" if rating >= 4 else "mid")
        is_low    = rating < 2

        # Alert button: green "Alerted" if already notified, red "Send Alert" if not
        if is_low:
            if notified:
                alert_btn = '<span class="btn-alert sent"><i class="fa-solid fa-circle-check"></i> Hospital Alerted</span>'
            else:
                alert_btn = f'<a href="adminfeedback.py?action=send_alert&feedback_id={fb_id}" class="btn-alert" onclick="return confirm(\'Send low rating alert to {hospital} manager?\')"><i class="fa-solid fa-bell"></i> Alert Hospital</a>'
        else:
            alert_btn = ""

        print(f"""
    <div class="fb-card {card_cls}"
         data-search="{parent_name.lower()} {child_name.lower()} {vaccine.lower()} {hospital.lower()}"
         data-rating="{data_rating}">
      <div class="fb-top">
        <div class="fb-left">
          <div class="fb-avatar {av_cls}">{initial}</div>
          <div>
            <div class="fb-name">{parent_name}</div>
            <div class="fb-meta">
              👶 {child_name} &bull; 💉 {vaccine} &bull; 🏥 {hospital}
            </div>
            <div class="fb-meta" style="margin-top:2px;">
              🗓️ {submitted}
              {"&nbsp;<span class='badge-edited'>✏️ Edited " + updated + "</span>" if updated else ""}
              {"&nbsp;<span class='badge-alerted'>✅ Hospital Alerted</span>" if notified else ""}
              {"&nbsp;<span class='badge-low'>🚨 Low Rating</span>" if is_low and not notified else ""}
            </div>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
          <div style="text-align:center">
            <div class="stars-big">{filled}{empty}</div>
            <div class="rating-num" style="color:{'var(--da)' if rating<2 else 'var(--su)' if rating>=4 else 'var(--wa)'}">{rating}/5</div>
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

print(f"""
  </main>
  <footer>&copy; 2026 Child Vaccination System &mdash; Admin Panel</footer>
</div>

<script>
const hamburger=document.getElementById('hamburger');
const sidebar=document.getElementById('sidebar');
const overlay=document.getElementById('overlay');
function closeSB(){{sidebar.classList.remove('open');hamburger.classList.remove('open');overlay.classList.remove('active');document.body.style.overflow='';}}
hamburger.addEventListener('click',()=>{{const o=sidebar.classList.toggle('open');hamburger.classList.toggle('open',o);overlay.classList.toggle('active',o);document.body.style.overflow=o?'hidden':'';}});
overlay.addEventListener('click',closeSB);
window.addEventListener('resize',()=>{{if(window.innerWidth>768)closeSB();}});
function tg(id){{const g=document.getElementById(id),o=g.classList.contains('open');document.querySelectorAll('.ng').forEach(x=>x.classList.remove('open'));if(!o)g.classList.add('open');}}

function toggleDetail(btn,detId){{
  const det=document.getElementById(detId);
  const isOpen=det.classList.contains('open');
  det.classList.toggle('open',!isOpen);
  btn.innerHTML=isOpen
    ?'<i class="fa-solid fa-chevron-down"></i> View More'
    :'<i class="fa-solid fa-chevron-up"></i> View Less';
}}

function filterCards(){{
  const q=document.getElementById('searchInput').value.toLowerCase();
  const rf=document.getElementById('ratingFilter').value;
  let visible=0;
  document.querySelectorAll('.fb-card').forEach(card=>{{
    const matchQ=!q||card.dataset.search.includes(q);
    const matchR=!rf||card.dataset.rating===rf;
    const show=matchQ&&matchR;
    card.style.display=show?'':'none';
    if(show)visible++;
  }});
  document.getElementById('cntLbl').textContent=visible+' record'+(visible!==1?'s':'');
}}

const urlParams=new URLSearchParams(window.location.search);
if(urlParams.get('filter')==='low'){{
  document.getElementById('ratingFilter').value='low';
  filterCards();
}}
</script>
</body>
</html>
""")
con.close()