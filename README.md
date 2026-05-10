# child-vaccination-system
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Child Vaccination System - GitHub README</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Sora:wght@300;400;500;600;700&display=swap');

  :root {
    --bg: #0d1117;
    --bg2: #161b22;
    --bg3: #1c2128;
    --border: #30363d;
    --text: #e6edf3;
    --text2: #8b949e;
    --text3: #6e7681;
    --green: #3fb950;
    --green-dim: #238636;
    --blue: #58a6ff;
    --blue-dim: #1f6feb;
    --purple: #bc8cff;
    --orange: #e3b341;
    --red: #f85149;
    --teal: #39d0c5;
    --pink: #ff7b72;
    --accent: #2ea043;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Sora', sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.7;
    font-size: 15px;
  }

  .readme-wrap {
    max-width: 860px;
    margin: 0 auto;
    padding: 40px 24px 80px;
  }

  /* ── HERO ── */
  .hero {
    text-align: center;
    padding: 56px 0 40px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 40px;
  }
  .hero-icon {
    width: 80px; height: 80px;
    background: linear-gradient(135deg, #1a7f37, #2ea043);
    border-radius: 20px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 38px; margin-bottom: 20px;
    box-shadow: 0 0 40px rgba(46,160,67,0.3);
  }
  .hero h1 {
    font-size: 28px; font-weight: 700;
    letter-spacing: -0.5px;
    line-height: 1.3;
    margin-bottom: 10px;
    background: linear-gradient(90deg, #3fb950, #58a6ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
  .hero p {
    color: var(--text2); font-size: 15px; max-width: 580px;
    margin: 0 auto 24px;
  }

  /* ── BADGES ── */
  .badges { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-bottom: 10px; }
  .badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 4px 10px; border-radius: 6px;
    font-size: 12px; font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
  }
  .badge-green  { background: #1a4721; color: #3fb950; border: 1px solid #238636; }
  .badge-blue   { background: #0d2f5e; color: #58a6ff; border: 1px solid #1f6feb; }
  .badge-purple { background: #2d1b5e; color: #bc8cff; border: 1px solid #553098; }
  .badge-orange { background: #3d2d00; color: #e3b341; border: 1px solid #9e6a03; }
  .badge-red    { background: #3d1a1a; color: #f85149; border: 1px solid #8b1b1b; }
  .badge-teal   { background: #0d3030; color: #39d0c5; border: 1px solid #0d6b63; }

  /* ── SECTION ── */
  .section { margin-bottom: 48px; }
  .section-title {
    font-size: 20px; font-weight: 600;
    display: flex; align-items: center; gap: 10px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
  }
  .section-title .dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 8px rgba(63,185,80,0.6);
    flex-shrink: 0;
  }

  /* ── TOC ── */
  .toc {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 40px;
  }
  .toc-title { font-size: 13px; font-weight: 600; color: var(--text2); margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.8px; }
  .toc-list { list-style: none; display: grid; grid-template-columns: 1fr 1fr; gap: 4px 24px; }
  .toc-list li a {
    color: var(--blue); text-decoration: none; font-size: 13.5px;
    display: flex; align-items: center; gap: 6px; padding: 3px 0;
  }
  .toc-list li a:hover { color: var(--text); }
  .toc-list li a::before { content: '→'; color: var(--text3); font-size: 11px; }

  /* ── OVERVIEW CARDS ── */
  .cards-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 10px; }
  .card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px;
    transition: border-color 0.2s;
  }
  .card:hover { border-color: #58a6ff55; }
  .card-icon { font-size: 22px; margin-bottom: 10px; }
  .card-title { font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
  .card-desc { font-size: 12.5px; color: var(--text2); line-height: 1.5; }

  /* ── TECH STACK ── */
  .tech-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .tech-item {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 16px;
    display: flex; gap: 14px; align-items: flex-start;
  }
  .tech-badge {
    flex-shrink: 0; padding: 4px 8px; border-radius: 5px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; font-weight: 600;
  }
  .tech-info .tech-name { font-size: 13.5px; font-weight: 600; color: var(--text); margin-bottom: 2px; }
  .tech-info .tech-desc { font-size: 12px; color: var(--text2); }

  /* ── DB SCHEMA ── */
  .schema-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .schema-table {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
  }
  .schema-header {
    display: flex; align-items: center; gap: 8px;
    background: var(--bg3);
    border-bottom: 1px solid var(--border);
    padding: 10px 14px;
  }
  .schema-header .tname { font-weight: 600; font-size: 13px; }
  .schema-header .tcolor { width: 8px; height: 8px; border-radius: 50%; }
  .schema-field {
    display: flex; justify-content: space-between;
    padding: 6px 14px; border-bottom: 1px solid #21262d;
  }
  .schema-field:last-child { border-bottom: none; }
  .field-name { color: var(--blue); }
  .field-type { color: var(--purple); font-size: 11px; }
  .field-pk { color: var(--orange); font-size: 10px; }
  .field-fk { color: var(--teal); font-size: 10px; }

  /* ── SYSTEM FLOW ── */
  .flow-steps { display: flex; flex-direction: column; gap: 0; }
  .flow-step {
    display: flex; gap: 16px; align-items: flex-start;
    padding: 16px 0;
    border-bottom: 1px solid var(--border);
  }
  .flow-step:last-child { border-bottom: none; }
  .step-num {
    flex-shrink: 0; width: 32px; height: 32px;
    background: var(--green-dim); border: 1px solid var(--green);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 700; color: var(--green);
  }
  .step-content {}
  .step-title { font-size: 13.5px; font-weight: 600; margin-bottom: 3px; }
  .step-desc { font-size: 13px; color: var(--text2); }

  /* ── MODULES ── */
  .modules-grid { display: grid; grid-template-columns: 1fr; gap: 10px; }
  .module-item {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--green);
    border-radius: 0 8px 8px 0;
    padding: 14px 16px;
    display: flex; gap: 16px; align-items: flex-start;
  }
  .module-num {
    flex-shrink: 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; color: var(--green);
    font-weight: 600; padding-top: 2px;
  }
  .module-name { font-size: 13.5px; font-weight: 600; margin-bottom: 4px; }
  .module-desc { font-size: 12.5px; color: var(--text2); line-height: 1.5; }

  /* ── SCREENS (MOCKUP PREVIEWS) ── */
  .screens-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .screen-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
  }
  .screen-bar {
    background: var(--bg3);
    border-bottom: 1px solid var(--border);
    padding: 8px 12px;
    display: flex; align-items: center; gap: 6px;
  }
  .screen-bar .dot-r { width: 8px; height: 8px; border-radius: 50%; background: #f85149; }
  .screen-bar .dot-y { width: 8px; height: 8px; border-radius: 50%; background: #e3b341; }
  .screen-bar .dot-g { width: 8px; height: 8px; border-radius: 50%; background: #3fb950; }
  .screen-bar .url-pill {
    margin-left: 8px; flex: 1; background: var(--bg);
    border: 1px solid var(--border); border-radius: 4px;
    padding: 2px 8px; font-size: 11px; color: var(--text2);
    font-family: 'JetBrains Mono', monospace;
  }
  .screen-body { padding: 16px; }
  .screen-title { font-size: 12px; font-weight: 600; color: var(--text2); margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.6px; }

  /* mini UI previews inside screen cards */
  .mini-nav {
    background: #161b22; border: 1px solid var(--border); border-radius: 6px;
    padding: 8px 10px; display: flex; gap: 12px; align-items: center; margin-bottom: 10px;
  }
  .mini-nav .nav-brand { font-size: 11px; font-weight: 700; color: var(--green); }
  .mini-nav .nav-links { display: flex; gap: 8px; }
  .mini-nav .nav-link { font-size: 10px; color: var(--text2); }
  .mini-stat-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 10px; }
  .mini-stat {
    background: var(--bg3); border: 1px solid var(--border);
    border-radius: 5px; padding: 7px 8px; text-align: center;
  }
  .mini-stat .stat-val { font-size: 15px; font-weight: 700; color: var(--green); }
  .mini-stat .stat-lbl { font-size: 9px; color: var(--text2); }
  .mini-table { width: 100%; border-collapse: collapse; font-size: 10.5px; }
  .mini-table th { color: var(--text2); padding: 5px 6px; text-align: left; border-bottom: 1px solid var(--border); font-weight: 600; }
  .mini-table td { padding: 5px 6px; border-bottom: 1px solid #21262d; color: var(--text); }
  .status-pill {
    display: inline-block; padding: 1px 6px; border-radius: 20px;
    font-size: 9.5px; font-weight: 600;
  }
  .s-pending  { background: #3d2d00; color: #e3b341; }
  .s-done     { background: #1a4721; color: #3fb950; }
  .s-booked   { background: #0d2f5e; color: #58a6ff; }

  /* form mockup */
  .mini-form { display: flex; flex-direction: column; gap: 7px; }
  .mini-form label { font-size: 10px; color: var(--text2); margin-bottom: 2px; display: block; }
  .mini-input {
    width: 100%; background: var(--bg); border: 1px solid var(--border);
    border-radius: 4px; padding: 5px 8px; font-size: 11px; color: var(--text);
    font-family: 'Sora', sans-serif;
  }
  .mini-row { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; }
  .mini-btn {
    background: var(--green-dim); border: 1px solid var(--green);
    color: var(--green); border-radius: 5px;
    padding: 6px 12px; font-size: 11px; font-weight: 600;
    text-align: center; margin-top: 4px;
  }

  /* schedule mockup */
  .mini-schedule { font-size: 10.5px; }
  .schedule-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 5px 0; border-bottom: 1px solid #21262d;
  }
  .schedule-row:last-child { border-bottom: none; }
  .vac-name { color: var(--text); font-weight: 500; }
  .vac-date { color: var(--text2); font-family: 'JetBrains Mono', monospace; font-size: 10px; }

  /* ── INSTALL ── */
  .code-block {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 12px;
  }
  .code-header {
    background: var(--bg3);
    border-bottom: 1px solid var(--border);
    padding: 8px 14px;
    display: flex; justify-content: space-between; align-items: center;
    font-size: 12px; color: var(--text2);
    font-family: 'JetBrains Mono', monospace;
  }
  .code-body {
    padding: 16px 18px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12.5px;
    line-height: 1.9;
    overflow-x: auto;
  }
  .code-body .c-comment { color: #6e7681; }
  .code-body .c-cmd     { color: #58a6ff; }
  .code-body .c-str     { color: #a5d6ff; }
  .code-body .c-var     { color: #e3b341; }
  .code-body .c-kw      { color: #ff7b72; }
  .code-body .c-green   { color: #3fb950; }

  /* ── COMPARISON TABLE ── */
  .compare-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .compare-table th {
    background: var(--bg3);
    border: 1px solid var(--border);
    padding: 10px 14px; text-align: left;
    font-weight: 600; font-size: 12.5px;
  }
  .compare-table td {
    border: 1px solid var(--border);
    padding: 9px 14px; vertical-align: top;
  }
  .compare-table td:first-child { color: var(--text2); }
  .compare-table td:nth-child(2) { color: var(--red); background: #1f0c0c; }
  .compare-table td:nth-child(3) { color: var(--green); background: #0c1f0e; }
  .x-icon { color: var(--red); }
  .check-icon { color: var(--green); }

  /* ── FUTURE ── */
  .future-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .future-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
  }
  .future-card .f-tag {
    font-size: 10px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.8px; margin-bottom: 8px;
    font-family: 'JetBrains Mono', monospace;
  }
  .future-card .f-title { font-size: 13.5px; font-weight: 600; margin-bottom: 6px; }
  .future-card .f-desc { font-size: 12.5px; color: var(--text2); line-height: 1.5; }

  /* ── CONTRIBUTORS ── */
  .contributor {
    display: flex; align-items: center; gap: 14px;
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: 10px; padding: 16px 18px;
    margin-bottom: 12px;
  }
  .avatar {
    width: 48px; height: 48px; border-radius: 50%;
    background: linear-gradient(135deg, #238636, #1f6feb);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; font-weight: 700; color: #fff; flex-shrink: 0;
  }
  .contrib-info .name { font-weight: 600; font-size: 14px; margin-bottom: 2px; }
  .contrib-info .role { font-size: 12px; color: var(--text2); }

  /* ── FOOTER ── */
  .readme-footer {
    border-top: 1px solid var(--border);
    padding-top: 24px;
    text-align: center;
    font-size: 12.5px;
    color: var(--text2);
  }
  .readme-footer a { color: var(--blue); text-decoration: none; }

  /* ── ERD / RELATIONSHIP ── */
  .erd-wrap {
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: 10px; padding: 20px; overflow-x: auto;
  }

  /* print */
  @media print {
    body { background: #fff; color: #000; }
  }
</style>
</head>
<body>
<div class="readme-wrap">

  <!-- ══ HERO ══ -->
  <div class="hero">
    <div class="hero-icon">💉</div>
    <h1>Integrated Digital Platform for Child Vaccination<br>Scheduling, Monitoring & Reporting</h1>
    <p>A full-stack web application that automates child immunization scheduling, appointment booking, dose tracking, and coverage reporting — replacing paper records with a secure, centralized system.</p>
    <div class="badges">
      <span class="badge badge-green">🐍 Python 3.11</span>
      <span class="badge badge-green">🌿 Django 4.2</span>
      <span class="badge badge-blue">🐬 MySQL 8.0</span>
      <span class="badge badge-purple">⚡ Bootstrap 5</span>
      <span class="badge badge-orange">📄 License: MIT</span>
      <span class="badge badge-teal">✅ Status: Active</span>
      <span class="badge badge-red">🎓 MCA Mini Project</span>
    </div>
  </div>

  <!-- ══ TABLE OF CONTENTS ══ -->
  <div class="toc">
    <div class="toc-title">📋 Table of Contents</div>
    <ul class="toc-list">
      <li><a href="#overview">Project Overview</a></li>
      <li><a href="#features">Key Features</a></li>
      <li><a href="#tech">Tech Stack</a></li>
      <li><a href="#screens">Screenshots</a></li>
      <li><a href="#db">Database Schema</a></li>
      <li><a href="#flow">System Flow</a></li>
      <li><a href="#modules">Modules</a></li>
      <li><a href="#install">Installation</a></li>
      <li><a href="#compare">Old vs New</a></li>
      <li><a href="#future">Future Scope</a></li>
    </ul>
  </div>

  <!-- ══ OVERVIEW ══ -->
  <div class="section" id="overview">
    <div class="section-title"><span class="dot"></span>Project Overview</div>
    <div class="cards-grid">
      <div class="card">
        <div class="card-icon">🗓️</div>
        <div class="card-title">Auto Schedule Generation</div>
        <div class="card-desc">Calculates every vaccine due date from a child's date of birth instantly on registration.</div>
      </div>
      <div class="card">
        <div class="card-icon">🔔</div>
        <div class="card-title">Smart Notifications</div>
        <div class="card-desc">Automated email & SMS reminders sent to parents before each dose is due.</div>
      </div>
      <div class="card">
        <div class="card-icon">🏥</div>
        <div class="card-title">Hospital Management</div>
        <div class="card-desc">Admin-approved hospital workflow with appointment calendars and dose completion tracking.</div>
      </div>
      <div class="card">
        <div class="card-icon">👨‍👩‍👧</div>
        <div class="card-title">Parent Portal</div>
        <div class="card-desc">Parents can register children, view schedules, and book appointments at any hospital.</div>
      </div>
      <div class="card">
        <div class="card-icon">📊</div>
        <div class="card-title">Coverage Reports</div>
        <div class="card-desc">Admin dashboard with real-time immunization coverage data by region and vaccine type.</div>
      </div>
      <div class="card">
        <div class="card-icon">🔒</div>
        <div class="card-title">Role-Based Access</div>
        <div class="card-desc">Three distinct user roles — Admin, Hospital, Parent — each with isolated data access.</div>
      </div>
    </div>
  </div>

  <!-- ══ TECH STACK ══ -->
  <div class="section" id="tech">
    <div class="section-title"><span class="dot"></span>Tech Stack</div>
    <div class="tech-grid">
      <div class="tech-item">
        <span class="tech-badge badge-green">PY</span>
        <div class="tech-info">
          <div class="tech-name">Python 3.11 + Django 4.2</div>
          <div class="tech-desc">Backend framework — MVT architecture, ORM, session auth, URL routing</div>
        </div>
      </div>
      <div class="tech-item">
        <span class="tech-badge badge-blue">SQL</span>
        <div class="tech-info">
          <div class="tech-name">MySQL 8.0</div>
          <div class="tech-desc">Relational database — 5 tables with FK relationships and referential integrity</div>
        </div>
      </div>
      <div class="tech-item">
        <span class="tech-badge badge-purple">UI</span>
        <div class="tech-info">
          <div class="tech-name">HTML5 + CSS3 + Bootstrap 5</div>
          <div class="tech-desc">Responsive frontend — works on desktop, tablet, and mobile</div>
        </div>
      </div>
      <div class="tech-item">
        <span class="tech-badge badge-orange">JS</span>
        <div class="tech-info">
          <div class="tech-name">JavaScript (Vanilla)</div>
          <div class="tech-desc">Form validation, dynamic schedule display, real-time field updates</div>
        </div>
      </div>
      <div class="tech-item">
        <span class="tech-badge badge-teal">⚙</span>
        <div class="tech-info">
          <div class="tech-name">Celery + Redis</div>
          <div class="tech-desc">Background task queue for scheduled dose reminder emails and SMS dispatch</div>
        </div>
      </div>
      <div class="tech-item">
        <span class="tech-badge badge-red">IDE</span>
        <div class="tech-info">
          <div class="tech-name">VS Code + WAMP Server</div>
          <div class="tech-desc">Development environment — local Apache, MySQL, and phpMyAdmin</div>
        </div>
      </div>
    </div>
  </div>

  <!-- ══ SCREENSHOTS / UI MOCKUPS ══ -->
  <div class="section" id="screens">
    <div class="section-title"><span class="dot"></span>Screenshots</div>
    <div class="screens-grid">

      <!-- Admin Dashboard -->
      <div class="screen-card">
        <div class="screen-bar">
          <span class="dot-r"></span><span class="dot-y"></span><span class="dot-g"></span>
          <span class="url-pill">localhost:8000/admin/dashboard</span>
        </div>
        <div class="screen-body">
          <div class="screen-title">Admin Dashboard</div>
          <div class="mini-nav">
            <span class="nav-brand">💉 VacciTrack</span>
            <div class="nav-links">
              <span class="nav-link">Hospitals</span>
              <span class="nav-link">Vaccines</span>
              <span class="nav-link">Reports</span>
            </div>
          </div>
          <div class="mini-stat-row">
            <div class="mini-stat"><div class="stat-val">142</div><div class="stat-lbl">Children</div></div>
            <div class="mini-stat"><div class="stat-val" style="color:var(--blue)">12</div><div class="stat-lbl">Hospitals</div></div>
            <div class="mini-stat"><div class="stat-val" style="color:var(--orange)">3</div><div class="stat-lbl">Pending</div></div>
          </div>
          <table class="mini-table">
            <tr><th>Hospital</th><th>Status</th></tr>
            <tr><td>City Health Centre</td><td><span class="status-pill s-done">Approved</span></td></tr>
            <tr><td>PHC Erode North</td><td><span class="status-pill s-pending">Pending</span></td></tr>
            <tr><td>District Hospital</td><td><span class="status-pill s-done">Approved</span></td></tr>
          </table>
        </div>
      </div>

      <!-- Child Registration -->
      <div class="screen-card">
        <div class="screen-bar">
          <span class="dot-r"></span><span class="dot-y"></span><span class="dot-g"></span>
          <span class="url-pill">localhost:8000/parent/add-child</span>
        </div>
        <div class="screen-body">
          <div class="screen-title">Child Registration Form</div>
          <div class="mini-form">
            <div class="mini-row">
              <div><label>Child Name</label><input class="mini-input" value="Ananya R." readonly></div>
              <div><label>Date of Birth</label><input class="mini-input" value="2025-01-15" readonly></div>
            </div>
            <div class="mini-row">
              <div><label>Gender</label><input class="mini-input" value="Female" readonly></div>
              <div><label>Blood Group</label><input class="mini-input" value="B+" readonly></div>
            </div>
            <div><label>Weight (kg)</label><input class="mini-input" value="3.2" readonly></div>
            <div><label>Identification Mark</label><input class="mini-input" value="Mole on left cheek" readonly></div>
            <div class="mini-btn">✓ Register &amp; Generate Schedule</div>
          </div>
        </div>
      </div>

      <!-- Vaccination Schedule -->
      <div class="screen-card">
        <div class="screen-bar">
          <span class="dot-r"></span><span class="dot-y"></span><span class="dot-g"></span>
          <span class="url-pill">localhost:8000/parent/schedule/child/4</span>
        </div>
        <div class="screen-body">
          <div class="screen-title">Auto-Generated Vaccination Schedule</div>
          <div class="mini-schedule">
            <div class="schedule-row">
              <div><div class="vac-name">BCG</div><div class="vac-date">At birth → 2025-01-15</div></div>
              <span class="status-pill s-done">✓ Done</span>
            </div>
            <div class="schedule-row">
              <div><div class="vac-name">OPV Dose 1</div><div class="vac-date">6 weeks → 2025-02-26</div></div>
              <span class="status-pill s-done">✓ Done</span>
            </div>
            <div class="schedule-row">
              <div><div class="vac-name">DPT Dose 2</div><div class="vac-date">10 weeks → 2025-03-26</div></div>
              <span class="status-pill s-booked">Booked</span>
            </div>
            <div class="schedule-row">
              <div><div class="vac-name">Hepatitis B D3</div><div class="vac-date">14 weeks → 2025-04-23</div></div>
              <span class="status-pill s-pending">Pending</span>
            </div>
            <div class="schedule-row">
              <div><div class="vac-name">Measles</div><div class="vac-date">9 months → 2025-10-15</div></div>
              <span class="status-pill s-pending">Pending</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Appointment Booking -->
      <div class="screen-card">
        <div class="screen-bar">
          <span class="dot-r"></span><span class="dot-y"></span><span class="dot-g"></span>
          <span class="url-pill">localhost:8000/parent/book-appointment</span>
        </div>
        <div class="screen-body">
          <div class="screen-title">Book Appointment</div>
          <div class="mini-form">
            <div><label>Child</label><input class="mini-input" value="Ananya R. (ID: C-004)" readonly></div>
            <div><label>Vaccine Due</label><input class="mini-input" value="DPT Dose 2" readonly></div>
            <div><label>Select Hospital</label><input class="mini-input" value="City Health Centre, Erode" readonly></div>
            <div class="mini-row">
              <div><label>Date</label><input class="mini-input" value="2025-03-26" readonly></div>
              <div><label>Time</label><input class="mini-input" value="10:30 AM" readonly></div>
            </div>
            <div class="mini-btn">📅 Confirm Appointment</div>
          </div>
        </div>
      </div>

    </div>
  </div>

  <!-- ══ DATABASE SCHEMA ══ -->
  <div class="section" id="db">
    <div class="section-title"><span class="dot"></span>Database Schema</div>
    <div class="schema-grid">

      <div class="schema-table">
        <div class="schema-header">
          <span class="tcolor" style="background:#3fb950"></span>
          <span class="tname">parent</span>
          <span style="font-size:10px;color:var(--text2);margin-left:auto">18 fields</span>
        </div>
        <div class="schema-field"><span class="field-name">parent_id</span><span class="field-type">INT <span class="field-pk">PK</span></span></div>
        <div class="schema-field"><span class="field-name">father_name</span><span class="field-type">VARCHAR(50)</span></div>
        <div class="schema-field"><span class="field-name">mother_name</span><span class="field-type">VARCHAR(50)</span></div>
        <div class="schema-field"><span class="field-name">mobile_number</span><span class="field-type">VARCHAR(15)</span></div>
        <div class="schema-field"><span class="field-name">email</span><span class="field-type">VARCHAR(50)</span></div>
        <div class="schema-field"><span class="field-name">state / district</span><span class="field-type">VARCHAR(50)</span></div>
        <div class="schema-field"><span class="field-name">username / password</span><span class="field-type">VARCHAR(50)</span></div>
        <div class="schema-field"><span class="field-name">status</span><span class="field-type">ENUM</span></div>
      </div>

      <div class="schema-table">
        <div class="schema-header">
          <span class="tcolor" style="background:#58a6ff"></span>
          <span class="tname">hospital</span>
          <span style="font-size:10px;color:var(--text2);margin-left:auto">18 fields</span>
        </div>
        <div class="schema-field"><span class="field-name">hospital_id</span><span class="field-type">INT <span class="field-pk">PK</span></span></div>
        <div class="schema-field"><span class="field-name">hospital_name</span><span class="field-type">VARCHAR(255)</span></div>
        <div class="schema-field"><span class="field-name">state / district</span><span class="field-type">VARCHAR(50)</span></div>
        <div class="schema-field"><span class="field-name">license_proof</span><span class="field-type">VARCHAR(255)</span></div>
        <div class="schema-field"><span class="field-name">owner_name</span><span class="field-type">VARCHAR(100)</span></div>
        <div class="schema-field"><span class="field-name">owner_email</span><span class="field-type">VARCHAR(100)</span></div>
        <div class="schema-field"><span class="field-name">username / password</span><span class="field-type">VARCHAR(50)</span></div>
        <div class="schema-field"><span class="field-name">status</span><span class="field-type">ENUM(pending/approved)</span></div>
      </div>

      <div class="schema-table">
        <div class="schema-header">
          <span class="tcolor" style="background:#bc8cff"></span>
          <span class="tname">child</span>
          <span style="font-size:10px;color:var(--text2);margin-left:auto">13 fields</span>
        </div>
        <div class="schema-field"><span class="field-name">child_id</span><span class="field-type">INT <span class="field-pk">PK</span></span></div>
        <div class="schema-field"><span class="field-name">parent_id</span><span class="field-type">INT <span class="field-fk">FK</span></span></div>
        <div class="schema-field"><span class="field-name">vaccine_id</span><span class="field-type">INT <span class="field-fk">FK</span></span></div>
        <div class="schema-field"><span class="field-name">child_name</span><span class="field-type">VARCHAR(100)</span></div>
        <div class="schema-field"><span class="field-name">dob</span><span class="field-type">DATE ⭐ key field</span></div>
        <div class="schema-field"><span class="field-name">gender</span><span class="field-type">ENUM</span></div>
        <div class="schema-field"><span class="field-name">blood_group</span><span class="field-type">VARCHAR(20)</span></div>
        <div class="schema-field"><span class="field-name">status</span><span class="field-type">ENUM(pending/notified/completed)</span></div>
      </div>

      <div class="schema-table">
        <div class="schema-header">
          <span class="tcolor" style="background:#e3b341"></span>
          <span class="tname">vaccine</span>
          <span style="font-size:10px;color:var(--text2);margin-left:auto">11 fields</span>
        </div>
        <div class="schema-field"><span class="field-name">vaccine_id</span><span class="field-type">INT <span class="field-pk">PK</span></span></div>
        <div class="schema-field"><span class="field-name">vaccine_name</span><span class="field-type">VARCHAR(100)</span></div>
        <div class="schema-field"><span class="field-name">age_group</span><span class="field-type">VARCHAR(50)</span></div>
        <div class="schema-field"><span class="field-name">dose_number</span><span class="field-type">VARCHAR(50)</span></div>
        <div class="schema-field"><span class="field-name">due_days</span><span class="field-type">VARCHAR(20) ⭐</span></div>
        <div class="schema-field"><span class="field-name">interval_days</span><span class="field-type">VARCHAR(20) ⭐</span></div>
        <div class="schema-field"><span class="field-name">min / max age</span><span class="field-type">INT / VARCHAR</span></div>
        <div class="schema-field"><span class="field-name">status</span><span class="field-type">ENUM(confirmed/deleted)</span></div>
      </div>

    </div>

    <!-- appointment spans full width -->
    <div style="margin-top:14px">
      <div class="schema-table" style="max-width:100%">
        <div class="schema-header">
          <span class="tcolor" style="background:#39d0c5"></span>
          <span class="tname">appointment</span>
          <span style="font-size:10px;color:var(--text2);margin-left:auto">9 fields — joins all 4 tables above</span>
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr)">
          <div class="schema-field"><span class="field-name">appo_id</span><span class="field-type">INT <span class="field-pk">PK</span></span></div>
          <div class="schema-field"><span class="field-name">child_id</span><span class="field-type">INT <span class="field-fk">FK</span></span></div>
          <div class="schema-field"><span class="field-name">vaccine_id</span><span class="field-type">INT <span class="field-fk">FK</span></span></div>
          <div class="schema-field"><span class="field-name">parent_id</span><span class="field-type">INT <span class="field-fk">FK</span></span></div>
          <div class="schema-field"><span class="field-name">hospital_id</span><span class="field-type">INT <span class="field-fk">FK</span></span></div>
          <div class="schema-field"><span class="field-name">appointment_date</span><span class="field-type">DATE</span></div>
          <div class="schema-field"><span class="field-name">appointment_time</span><span class="field-type">TIME</span></div>
          <div class="schema-field"><span class="field-name">rescheduled_on</span><span class="field-type">DATETIME</span></div>
          <div class="schema-field"><span class="field-name">status</span><span class="field-type">VARCHAR (Booked/Completed)</span></div>
        </div>
      </div>
    </div>
  </div>

  <!-- ══ SYSTEM FLOW ══ -->
  <div class="section" id="flow">
    <div class="section-title"><span class="dot"></span>System Flow</div>
    <div class="flow-steps">
      <div class="flow-step">
        <div class="step-num">1</div>
        <div class="step-content">
          <div class="step-title">Hospital Registration</div>
          <div class="step-desc">A hospital submits a registration form with name, address, license proof, and owner details. Status is set to <code style="font-family:JetBrains Mono,monospace;font-size:11px;background:var(--bg3);padding:1px 5px;border-radius:3px">pending</code>.</div>
        </div>
      </div>
      <div class="flow-step">
        <div class="step-num">2</div>
        <div class="step-content">
          <div class="step-title">Admin Approval</div>
          <div class="step-desc">Admin reviews and approves the hospital. Status changes to <code style="font-family:JetBrains Mono,monospace;font-size:11px;background:var(--bg3);padding:1px 5px;border-radius:3px">approved</code>. Hospital can now log in.</div>
        </div>
      </div>
      <div class="flow-step">
        <div class="step-num">3</div>
        <div class="step-content">
          <div class="step-title">Parent & Child Registration</div>
          <div class="step-desc">Parent registers an account, then adds their child's details including the critical <strong>Date of Birth</strong> field.</div>
        </div>
      </div>
      <div class="flow-step">
        <div class="step-num">4</div>
        <div class="step-content">
          <div class="step-title">⚡ Auto Schedule Generation</div>
          <div class="step-desc">On child save, the system reads every vaccine in the <code style="font-family:JetBrains Mono,monospace;font-size:11px;background:var(--bg3);padding:1px 5px;border-radius:3px">vaccine</code> table and computes: <strong>due_date = dob + due_days</strong>. Full schedule generated instantly.</div>
        </div>
      </div>
      <div class="flow-step">
        <div class="step-num">5</div>
        <div class="step-content">
          <div class="step-title">🔔 Automated Reminders</div>
          <div class="step-desc">Celery task runs daily. When a dose is 7 days away → email + SMS sent to parent. Overdue doses trigger follow-up alerts.</div>
        </div>
      </div>
      <div class="flow-step">
        <div class="step-num">6</div>
        <div class="step-content">
          <div class="step-title">Appointment Booking</div>
          <div class="step-desc">Parent selects a hospital, picks a date & time. Appointment record created in DB linking child + vaccine + hospital + parent.</div>
        </div>
      </div>
      <div class="flow-step">
        <div class="step-num">7</div>
        <div class="step-content">
          <div class="step-title">Dose Administration & Completion</div>
          <div class="step-desc">Hospital marks the appointment as <code style="font-family:JetBrains Mono,monospace;font-size:11px;background:var(--bg3);padding:1px 5px;border-radius:3px">completed</code>. Child's schedule updates. Coverage report auto-refreshes.</div>
        </div>
      </div>
      <div class="flow-step">
        <div class="step-num">8</div>
        <div class="step-content">
          <div class="step-title">📊 Coverage Reporting</div>
          <div class="step-desc">Admin views real-time coverage rates by vaccine, region, hospital, and age group — no manual counting required.</div>
        </div>
      </div>
    </div>
  </div>

  <!-- ══ MODULES ══ -->
  <div class="section" id="modules">
    <div class="section-title"><span class="dot"></span>Modules</div>
    <div class="modules-grid">
      <div class="module-item">
        <div class="module-num">01</div>
        <div>
          <div class="module-name">Admin Module</div>
          <div class="module-desc">Hospital approval workflow, vaccine master management, user oversight, and coverage report generation.</div>
        </div>
      </div>
      <div class="module-item">
        <div class="module-num">02</div>
        <div>
          <div class="module-name">User Authentication Module</div>
          <div class="module-desc">Secure login/logout for all three roles with session management and encrypted password storage.</div>
        </div>
      </div>
      <div class="module-item">
        <div class="module-num">03</div>
        <div>
          <div class="module-name">Parent Management Module</div>
          <div class="module-desc">Parent registration, profile management, and a dashboard showing all registered children and their statuses.</div>
        </div>
      </div>
      <div class="module-item">
        <div class="module-num">04</div>
        <div>
          <div class="module-name">Child Registration Module</div>
          <div class="module-desc">Captures child health data and triggers automatic vaccination schedule generation upon saving.</div>
        </div>
      </div>
      <div class="module-item">
        <div class="module-num">05</div>
        <div>
          <div class="module-name">Vaccine Management Module</div>
          <div class="module-desc">Vaccine master CRUD with the core scheduling algorithm: <code style="font-family:JetBrains Mono,monospace;font-size:11px;background:var(--bg);padding:1px 5px;border-radius:3px">due_date = dob + due_days</code>, subsequent doses use <code style="font-family:JetBrains Mono,monospace;font-size:11px;background:var(--bg);padding:1px 5px;border-radius:3px">interval_days</code>.</div>
        </div>
      </div>
      <div class="module-item">
        <div class="module-num">06</div>
        <div>
          <div class="module-name">Appointment Module</div>
          <div class="module-desc">End-to-end appointment lifecycle — booking, rescheduling, cancellation, and completion marking by hospitals.</div>
        </div>
      </div>
      <div class="module-item">
        <div class="module-num">07</div>
        <div>
          <div class="module-name">Notification Module</div>
          <div class="module-desc">Celery-powered background scheduler that checks daily for upcoming due dates and dispatches email + SMS reminders automatically.</div>
        </div>
      </div>
    </div>
  </div>

  <!-- ══ INSTALLATION ══ -->
  <div class="section" id="install">
    <div class="section-title"><span class="dot"></span>Installation & Setup</div>

    <div class="code-block">
      <div class="code-header"><span>bash</span><span>Step 1 — Clone & enter project</span></div>
      <div class="code-body">
        <span class="c-comment"># Clone the repository</span><br>
        <span class="c-cmd">git clone</span> <span class="c-str">https://github.com/your-username/child-vaccination-system.git</span><br>
        <span class="c-cmd">cd</span> child-vaccination-system
      </div>
    </div>

    <div class="code-block">
      <div class="code-header"><span>bash</span><span>Step 2 — Virtual environment & dependencies</span></div>
      <div class="code-body">
        <span class="c-comment"># Create and activate virtual environment</span><br>
        <span class="c-cmd">python</span> -m venv venv<br>
        <span class="c-cmd">source</span> venv/bin/activate &nbsp;&nbsp;<span class="c-comment"># Windows: venv\Scripts\activate</span><br><br>
        <span class="c-comment"># Install all dependencies</span><br>
        <span class="c-cmd">pip install</span> -r requirements.txt
      </div>
    </div>

    <div class="code-block">
      <div class="code-header"><span>python</span><span>Step 3 — Database configuration (settings.py)</span></div>
      <div class="code-body">
        <span class="c-kw">DATABASES</span> = {<br>
        &nbsp;&nbsp;<span class="c-str">'default'</span>: {<br>
        &nbsp;&nbsp;&nbsp;&nbsp;<span class="c-str">'ENGINE'</span>: <span class="c-str">'django.db.backends.mysql'</span>,<br>
        &nbsp;&nbsp;&nbsp;&nbsp;<span class="c-str">'NAME'</span>: <span class="c-str">'vaccination_db'</span>,<br>
        &nbsp;&nbsp;&nbsp;&nbsp;<span class="c-str">'USER'</span>: <span class="c-str">'root'</span>,<br>
        &nbsp;&nbsp;&nbsp;&nbsp;<span class="c-str">'PASSWORD'</span>: <span class="c-var">'your_password'</span>,<br>
        &nbsp;&nbsp;&nbsp;&nbsp;<span class="c-str">'HOST'</span>: <span class="c-str">'localhost'</span>,<br>
        &nbsp;&nbsp;&nbsp;&nbsp;<span class="c-str">'PORT'</span>: <span class="c-str">'3306'</span>,<br>
        &nbsp;&nbsp;}<br>
        }
      </div>
    </div>

    <div class="code-block">
      <div class="code-header"><span>bash</span><span>Step 4 — Migrate & run</span></div>
      <div class="code-body">
        <span class="c-comment"># Create database tables</span><br>
        <span class="c-cmd">python</span> manage.py makemigrations<br>
        <span class="c-cmd">python</span> manage.py migrate<br><br>
        <span class="c-comment"># Create admin superuser</span><br>
        <span class="c-cmd">python</span> manage.py createsuperuser<br><br>
        <span class="c-comment"># Start the development server</span><br>
        <span class="c-cmd">python</span> manage.py runserver<br><br>
        <span class="c-green">✓ Open: http://127.0.0.1:8000</span>
      </div>
    </div>
  </div>

  <!-- ══ COMPARISON TABLE ══ -->
  <div class="section" id="compare">
    <div class="section-title"><span class="dot"></span>Old System vs This System</div>
    <table class="compare-table">
      <thead>
        <tr>
          <th>Feature</th>
          <th>❌ Old Manual System</th>
          <th>✅ This System</th>
        </tr>
      </thead>
      <tbody>
        <tr><td>Vaccination records</td><td>Paper cards — easily lost or damaged</td><td>Permanent MySQL database — never lost</td></tr>
        <tr><td>Due date calculation</td><td>Manual — often wrong intervals</td><td>Automatic from DOB — always accurate</td></tr>
        <tr><td>Reminders to parents</td><td>None — parents must remember</td><td>Auto email + SMS 7 days before due</td></tr>
        <tr><td>Record access</td><td>Single hospital register only</td><td>Centralised — any approved hospital</td></tr>
        <tr><td>Appointment booking</td><td>Walk-in only</td><td>Online booking at any hospital</td></tr>
        <tr><td>Coverage reporting</td><td>Manual counting of registers</td><td>Real-time admin dashboard reports</td></tr>
        <tr><td>Overdue dose tracking</td><td>Not possible</td><td>Automatic overdue alerts flagged</td></tr>
        <tr><td>Data security</td><td>No backup, can be forged</td><td>Encrypted, backed up, role-secured</td></tr>
      </tbody>
    </table>
  </div>

  <!-- ══ FUTURE SCOPE ══ -->
  <div class="section" id="future">
    <div class="section-title"><span class="dot"></span>Future Scope</div>
    <div class="future-grid">
      <div class="future-card">
        <div class="f-tag" style="color:var(--green)">📱 Mobile</div>
        <div class="f-title">Android & iOS App</div>
        <div class="f-desc">Push notifications directly to parent lock screens. Offline schedule viewing for areas with poor connectivity.</div>
      </div>
      <div class="future-card">
        <div class="f-tag" style="color:var(--blue)">🔗 Integration</div>
        <div class="f-title">ABDM / Health ID Link</div>
        <div class="f-desc">Integrate with India's Ayushman Bharat Digital Mission for cross-country record access using Aadhaar Health ID.</div>
      </div>
      <div class="future-card">
        <div class="f-tag" style="color:var(--purple)">🤖 AI</div>
        <div class="f-title">Drop-out Risk Prediction</div>
        <div class="f-desc">ML model to identify children likely to miss future doses based on historical drop-out patterns — enabling proactive outreach.</div>
      </div>
      <div class="future-card">
        <div class="f-tag" style="color:var(--orange)">📲 QR Code</div>
        <div class="f-title">Digital Vaccine Card</div>
        <div class="f-desc">Printable QR-code vaccine card per child — scan at any hospital for instant record access, replacing paper cards entirely.</div>
      </div>
    </div>
  </div>

  <!-- ══ PROJECT INFO ══ -->
  <div class="section">
    <div class="section-title"><span class="dot"></span>Project Info</div>
    <div class="contributor">
      <div class="avatar">S</div>
      <div class="contrib-info">
        <div class="name">Your Name — Register Number</div>
        <div class="role">Developer · MCA 2024–2026 · Department of Computer Applications</div>
      </div>
    </div>
    <div class="contributor" style="margin-top:8px">
      <div class="avatar" style="background:linear-gradient(135deg,#1f6feb,#553098)">G</div>
      <div class="contrib-info">
        <div class="name">Guide Name, MCA., M.Phil., B.Ed.</div>
        <div class="role">Assistant Professor · Department of Computer Applications · [College Name] (Autonomous), Erode</div>
      </div>
    </div>
  </div>

  <!-- ══ FOOTER ══ -->
  <div class="readme-footer">
    <p>Built with 🐍 Python + Django &nbsp;·&nbsp; 🐬 MySQL &nbsp;·&nbsp; ⚡ Bootstrap 5</p>
    <p style="margin-top:6px">Department of Computer Applications &nbsp;·&nbsp; [College Name] (Autonomous), Erode &nbsp;·&nbsp; October 2025</p>
    <p style="margin-top:10px;color:var(--text3)">⭐ Star this repo if it helped you &nbsp;·&nbsp; <a href="#">Report Issues</a> &nbsp;·&nbsp; <a href="#">MIT License</a></p>
  </div>

</div>
</body>
</html>
