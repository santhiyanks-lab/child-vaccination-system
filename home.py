#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
import os
import os.path
import sys
import cgi
import cgitb
import pymysql

cgitb.enable()

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
print("Content-Type: text/html; charset=utf-8\r\n\r\n")

con = pymysql.connect(host="localhost", user="root", password="", database="child")
cur = con.cursor()
form = cgi.FieldStorage()

redirect_script = ""

# ─────────────────────────────────────────────
#  ADMIN LOGIN
# ─────────────────────────────────────────────
if form.getvalue("login") == "Login":
    username = form.getvalue("username", "").strip()
    password = form.getvalue("password", "").strip()
    if username == "admin" and password == "child@369":
        redirect_script = '<script>alert("Login Successful!"); window.location.href="admin_dash.py";</script>'
    else:
        redirect_script = '<script>alert("Invalid Username or Password!");</script>'

# ─────────────────────────────────────────────
#  PARENT REGISTER
#  USERNAME : first3(father_name) _ first3(state) _ first3(district) _ parent_id
#  PASSWORD : first3(father_name) + last4(mobile)
# ─────────────────────────────────────────────
elif form.getvalue("parent_register") is not None:
    try:
        Father_name   = form.getvalue("father_name")
        Father_age    = form.getvalue("father_age")
        Mother_name   = form.getvalue("mother_name")
        Mother_age    = form.getvalue("mother_age")
        Mother_weight = form.getvalue("mother_weight")
        Email         = form.getvalue("email")
        Mobile_number = form.getvalue("mobile_number")
        Occupation    = form.getvalue("occupation")
        State         = form.getvalue("state")
        District      = form.getvalue("district")
        Address       = form.getvalue("address")
        Pincode       = form.getvalue("pincode")

        cur.execute("SELECT MAX(parent_id) FROM parent")
        maxid = cur.fetchone()[0]
        parent_id = 1 if maxid is None else maxid + 1

        fname_part    = Father_name[:3].lower()   if Father_name   else "par"
        state_part    = State[:3].lower()          if State         else "sta"
        district_part = District[:3].lower()       if District      else "dis"
        mobile_part   = Mobile_number[-4:]         if Mobile_number else "0000"

        Username = f"{fname_part}_{state_part}_{district_part}_{parent_id}"
        Password = f"{fname_part}{mobile_part}"

        os.makedirs("images", exist_ok=True)
        image1 = form['father_aadhar_image']
        fn1 = os.path.basename(image1.filename)
        open("images/" + fn1, "wb").write(image1.file.read())
        image2 = form['parent_profile']
        fn2 = os.path.basename(image2.filename)
        open("images/" + fn2, "wb").write(image2.file.read())

        q = """INSERT INTO parent
               (father_name,father_age,mother_name,mother_age,mother_weight,
                email,mobile_number,occupation,state,district,address,pincode,
                father_aadhar_image,parent_profile,username,password,status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending')"""
        cur.execute(q,(Father_name,Father_age,Mother_name,Mother_age,Mother_weight,
                       Email,Mobile_number,Occupation,State,District,Address,Pincode,
                       fn1,fn2,Username,Password))
        con.commit()
        redirect_script = (
            f'<script>alert("Registration Successful!\\n\\n'
            f'Your Username : {Username}\\n'
            f'Your Password : {Password}\\n\\n'
            f'Please save these credentials.\\n'
            f'Wait for Admin Approval before logging in."); '
            f'window.location.href="home.py";</script>'
        )
    except Exception as e:
        redirect_script = f'<script>alert("Registration Failed: {str(e)}");</script>'

# ─────────────────────────────────────────────
#  PARENT LOGIN
# ─────────────────────────────────────────────
elif form.getvalue("submitsl") is not None:
    username = form.getvalue("emailsl", "").strip()
    password = form.getvalue("passsl", "").strip()
    cur.execute("SELECT parent_id, status FROM parent WHERE username=%s AND password=%s", (username, password))
    res = cur.fetchone()
    if res:
        parent_id, status = res[0], res[1]
        if status == 'approved':
            redirect_script = f'<script>alert("Login Successful!"); window.location.href="parent_dash.py?parent_id={parent_id}";</script>'
        elif status == 'pending':
            redirect_script = '<script>alert("Your account is pending admin approval.");</script>'
        elif status == 'rejected':
            redirect_script = '<script>alert("Your account has been rejected. Please contact the admin.");</script>'
    else:
        redirect_script = '<script>alert("Invalid Username or Password!");</script>'

# ─────────────────────────────────────────────
#  HOSPITAL REGISTER
#  USERNAME : first3(hospital_name) _ first3(state) _ first3(district) _ hospital_id
#  PASSWORD : first3(hospital_name) + last4(owner_phone)
# ─────────────────────────────────────────────
elif form.getvalue("hospital_register") is not None:
    try:
        Hospital_name         = form.getvalue("hospital_name")
        State                 = form.getvalue("state")
        District              = form.getvalue("district")
        Address               = form.getvalue("address")
        Pincode               = form.getvalue("pincode")
        Hospital_number       = form.getvalue("hospital_number")
        Year_of_establishment = form.getvalue("year_of_establishment")
        Owner_name            = form.getvalue("owner_name")
        Owner_address         = form.getvalue("owner_address")
        Owner_phone_number    = form.getvalue("owner_phone_number")
        Owner_email           = form.getvalue("owner_email")

        cur.execute("SELECT MAX(hospital_id) FROM hospital")
        maxid = cur.fetchone()[0]
        hospital_id = 1 if maxid is None else maxid + 1

        hname_part    = Hospital_name[:3].lower()    if Hospital_name      else "hos"
        state_part    = State[:3].lower()             if State              else "sta"
        district_part = District[:3].lower()          if District           else "dis"
        ophone_part   = Owner_phone_number[-4:]       if Owner_phone_number else "0000"

        Username = f"{hname_part}_{state_part}_{district_part}_{hospital_id}"
        Password = f"{hname_part}{ophone_part}"

        os.makedirs("images", exist_ok=True)
        image3 = form['license_proof']
        fn3 = os.path.basename(image3.filename)
        open("images/" + fn3, "wb").write(image3.file.read())
        image4 = form['hospital_image']
        fn4 = os.path.basename(image4.filename)
        open("images/" + fn4, "wb").write(image4.file.read())
        image5 = form['owner_profile']
        fn5 = os.path.basename(image5.filename)
        open("images/" + fn5, "wb").write(image5.file.read())

        q = """INSERT INTO hospital
               (hospital_name,state,district,address,pincode,hospital_number,
                license_proof,year_of_establishment,hospital_image,owner_name,
                owner_profile,owner_address,owner_phone_number,owner_email,
                username,password,status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending')"""
        cur.execute(q,(Hospital_name,State,District,Address,Pincode,Hospital_number,
                       fn3,Year_of_establishment,fn4,Owner_name,fn5,Owner_address,
                       Owner_phone_number,Owner_email,Username,Password))
        con.commit()
        redirect_script = (
            f'<script>alert("Registration Successful!\\n\\n'
            f'Your Username : {Username}\\n'
            f'Your Password : {Password}\\n\\n'
            f'Please save these credentials.\\n'
            f'Wait for Admin Approval before logging in."); '
            f'window.location.href="home.py";</script>'
        )
    except Exception as e:
        redirect_script = f'<script>alert("Registration Failed: {str(e)}");</script>'

# ─────────────────────────────────────────────
#  HOSPITAL LOGIN
# ─────────────────────────────────────────────
elif form.getvalue("submitil") is not None:
    username = form.getvalue("emailil", "").strip()
    password = form.getvalue("passil", "").strip()
    cur.execute("SELECT hospital_id, status FROM hospital WHERE username=%s AND password=%s", (username, password))
    res = cur.fetchone()
    if res:
        hospital_id, status = res[0], res[1]
        if status == 'approved':
            redirect_script = f'<script>alert("Login Successful!"); window.location.href="hospital_dash.py?hospital_id={hospital_id}";</script>'
        elif status == 'pending':
            redirect_script = '<script>alert("Your account is pending admin approval.");</script>'
        elif status == 'rejected':
            redirect_script = '<script>alert("Your account has been rejected. Please contact the admin.");</script>'
    else:
        redirect_script = '<script>alert("Invalid Username or Password!");</script>'


print(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Child Vaccination System</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <style>
        :root {{
            --primary: #1565c0;
            --primary-light: #1976d2;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Segoe UI', sans-serif; background: #f0f4f8; color: #1e293b; }}

        .navbar {{
            background: linear-gradient(135deg, #0d47a1, #1565c0) !important;
            box-shadow: 0 2px 12px rgba(0,0,0,.25);
            padding: 10px 16px;
        }}
        .navbar-brand {{ font-size: 1.15rem; font-weight: 700; }}
        .nav-link {{ font-size: .92rem; padding: 8px 12px !important; border-radius: 6px; transition: background .2s; }}
        .nav-link:hover {{ background: rgba(255,255,255,.12); }}
        .navbar-logo {{ height: 42px; width: 42px; border-radius: 50%; border: 2px solid rgba(255,255,255,.5); object-fit: cover; }}

        .carousel-item img {{ object-fit: cover; max-height: 480px; min-height: 220px; width: 100%; }}
        .carousel-caption {{ background: rgba(0,0,0,.5); border-radius: 12px; padding: 14px 20px; bottom: 20px; }}
        .carousel-caption h3 {{ font-size: clamp(1rem,3vw,1.6rem); font-weight: 700; }}
        .carousel-caption p {{ font-size: clamp(.8rem,2vw,1rem); margin: 0; }}

        .section-title {{ font-size: clamp(1.2rem,3vw,1.6rem); font-weight: 700; color: var(--primary); }}

        .info-card {{ border: none; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,.09); transition: transform .2s,box-shadow .2s; height: 100%; }}
        .info-card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,.13); }}
        .info-card img {{ height: 180px; object-fit: cover; width: 100%; }}
        .info-card .card-body {{ padding: 18px; }}
        .info-card .card-title {{ font-weight: 700; font-size: 1rem; color: #1e293b; }}

        .about-section {{ background: #fff; border-radius: 16px; padding: 40px 32px; box-shadow: 0 2px 12px rgba(0,0,0,.07); }}
        .about-section p {{ color: #475569; line-height: 1.8; font-size: .95rem; }}

        .contact-card {{ border: none; border-radius: 14px; box-shadow: 0 4px 16px rgba(0,0,0,.09); padding: 28px 32px; }}
        .contact-card p {{ font-size: .95rem; margin-bottom: 12px; color: #334155; }}

        .stats-strip {{ background: linear-gradient(135deg,#0d47a1,#1565c0); color: #fff; padding: 28px 0; border-radius: 14px; }}
        .stat-item h3 {{ font-size: clamp(1.4rem,4vw,2rem); font-weight: 800; margin: 0; }}
        .stat-item p {{ font-size: .85rem; margin: 0; opacity: .85; }}

        footer {{ background: #0d1b2a; color: #94a3b8; padding: 28px 16px; text-align: center; margin-top: 60px; }}
        footer a {{ color: #fbbf24; text-decoration: none; }}
        footer a:hover {{ color: #fcd34d; }}

        .login-portal-card {{ border: none; border-radius: 14px; box-shadow: 0 4px 16px rgba(0,0,0,.09); padding: 28px 20px; text-align: center; cursor: pointer; transition: transform .2s,box-shadow .2s; background: #fff; height: 100%; }}
        .login-portal-card:hover {{ transform: translateY(-4px); box-shadow: 0 10px 28px rgba(0,0,0,.14); }}
        .portal-icon {{ font-size: 2.8rem; margin-bottom: 12px; }}
        .portal-title {{ font-weight: 700; font-size: 1.05rem; margin-bottom: 6px; }}
        .portal-desc {{ font-size: .84rem; color: #64748b; }}

        .form-control, .form-select {{ border-radius: 8px; border: 1.5px solid #e2e8f0; font-size: .9rem; }}
        .form-control:focus, .form-select:focus {{ border-color: var(--primary-light); box-shadow: 0 0 0 3px rgba(21,101,192,.12); }}
        .form-control:disabled, .form-select:disabled {{ background: #f8fafc; cursor: not-allowed; opacity: .7; }}

        .dob-error   {{ display: none; font-size: .8rem; color: #dc3545; margin-top: 4px; }}
        .dob-success {{ display: none; font-size: .8rem; color: #198754; margin-top: 4px; }}
        .is-invalid-dob {{ border-color: #dc3545 !important; }}
        .is-valid-dob   {{ border-color: #198754 !important; }}

        .autofill-badge {{
            display: none;
            font-size: .75rem;
            color: #0d6efd;
            margin-top: 3px;
            font-style: italic;
        }}
        .autofill-badge.visible {{ display: block; }}

        .modal-header {{ border-bottom: none; padding-bottom: 8px; }}
        .modal-footer {{ border-top: none; }}
        .modal-content {{ border-radius: 16px; border: none; }}

        .modal-dialog-scrollable .modal-content {{
            max-height: 88vh; display: flex; flex-direction: column; overflow: hidden;
        }}
        .modal-dialog-scrollable .modal-content > form {{
            display: flex; flex-direction: column; flex: 1 1 auto; min-height: 0; overflow: hidden;
        }}
        .modal-dialog-scrollable .modal-header,
        .modal-dialog-scrollable .modal-footer {{ flex-shrink: 0; }}
        .modal-dialog-scrollable .modal-body {{
            flex: 1 1 auto; overflow-y: auto; overflow-x: hidden;
            -webkit-overflow-scrolling: touch; min-height: 0;
        }}

        @media (max-width: 576px) {{
            .carousel-caption {{ display: none !important; }}
            .about-section {{ padding: 24px 16px; }}
            .contact-card {{ padding: 20px 16px; }}
            .modal-dialog-scrollable .modal-content {{ max-height: 92vh; }}
        }}
        @media (max-width: 767px) {{ .modal-dialog {{ margin: 10px auto; }} }}
    </style>
</head>
<body>

{redirect_script}

<!-- NAVBAR -->
<nav class="navbar navbar-expand-lg navbar-dark">
    <div class="container">
        <div class="d-flex align-items-center gap-2">
            <img src="./images/logo.jpg" class="navbar-logo" alt="Logo" onerror="this.style.display='none'">
            <a class="navbar-brand fw-bold" href="home.py">Child Vaccination</a>
        </div>
        <button class="navbar-toggler border-0" data-bs-toggle="collapse" data-bs-target="#menu" aria-label="Toggle menu">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="menu">
            <ul class="navbar-nav ms-auto align-items-lg-center gap-1">
                <li class="nav-item"><a class="nav-link text-white" href="home.py"><i class="fa-solid fa-house me-1"></i>Home</a></li>
                <li class="nav-item"><a class="nav-link text-white" href="#about"><i class="fa-solid fa-people-group me-1"></i>About Us</a></li>
                <li class="nav-item"><a class="nav-link text-white" href="#contact"><i class="fa-solid fa-phone me-1"></i>Contact Us</a></li>
                <li class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle text-white" data-bs-toggle="dropdown" href="#">
                        <i class="fa-solid fa-right-to-bracket me-1"></i>Login / Register
                    </a>
                    <ul class="dropdown-menu dropdown-menu-end shadow">
                        <li><a class="dropdown-item" data-bs-toggle="modal" data-bs-target="#adminModal"><i class="fa-solid fa-user-shield me-2 text-primary"></i>Admin Login</a></li>
                        <li><a class="dropdown-item" data-bs-toggle="modal" data-bs-target="#hospitalLoginModal"><i class="fa-solid fa-hospital me-2 text-success"></i>Hospital Login</a></li>
                        <li><a class="dropdown-item" data-bs-toggle="modal" data-bs-target="#parentLoginModal"><i class="fa-solid fa-person me-2 text-warning"></i>Parent Login</a></li>
                    </ul>
                </li>
            </ul>
        </div>
    </div>
</nav>

<!-- CAROUSEL -->
<div id="vaccinationCarousel" class="carousel slide" data-bs-ride="carousel">
    <div class="carousel-indicators">
        <button type="button" data-bs-target="#vaccinationCarousel" data-bs-slide-to="0" class="active"></button>
        <button type="button" data-bs-target="#vaccinationCarousel" data-bs-slide-to="1"></button>
        <button type="button" data-bs-target="#vaccinationCarousel" data-bs-slide-to="2"></button>
    </div>
    <div class="carousel-inner">
        <div class="carousel-item active">
            <img src="./images/parents.jpg" alt="Parents">
            <div class="carousel-caption d-none d-sm-block">
                <h3>Protect Your Child</h3>
                <p>Vaccination saves lives and builds a healthy future.</p>
            </div>
        </div>
        <div class="carousel-item">
            <img src="./images/Newborn baby.jpg" alt="Newborn">
            <div class="carousel-caption d-none d-sm-block">
                <h3>Timely Vaccination</h3>
                <p>Follow the vaccination schedule for full protection.</p>
            </div>
        </div>
        <div class="carousel-item">
            <img src="./images/baby.jpg" alt="Baby">
            <div class="carousel-caption d-none d-sm-block">
                <h3>Healthy Childhood</h3>
                <p>Vaccines prevent dangerous childhood diseases.</p>
            </div>
        </div>
    </div>
    <button class="carousel-control-prev" type="button" data-bs-target="#vaccinationCarousel" data-bs-slide="prev">
        <span class="carousel-control-prev-icon"></span>
    </button>
    <button class="carousel-control-next" type="button" data-bs-target="#vaccinationCarousel" data-bs-slide="next">
        <span class="carousel-control-next-icon"></span>
    </button>
</div>

<!-- STATS -->
<div class="container my-4">
    <div class="stats-strip">
        <div class="row text-center g-0">
            <div class="col-4 stat-item border-end border-white border-opacity-25">
                <h3>500+</h3><p>Registered Parents</p>
            </div>
            <div class="col-4 stat-item border-end border-white border-opacity-25">
                <h3>120+</h3><p>Partner Hospitals</p>
            </div>
            <div class="col-4 stat-item">
                <h3>20+</h3><p>Vaccines Tracked</p>
            </div>
        </div>
    </div>
</div>

<!-- PORTALS -->
<div class="container my-5">
    <h2 class="section-title text-center mb-4">Access Your Portal</h2>
    <div class="row g-3 justify-content-center">
        <div class="col-12 col-sm-6 col-md-4">
            <div class="login-portal-card" data-bs-toggle="modal" data-bs-target="#adminModal">
                <div class="portal-icon text-primary"><i class="fa-solid fa-user-shield"></i></div>
                <div class="portal-title">Admin</div>
                <div class="portal-desc">Manage approvals, vaccines, and notifications</div>
                <div class="mt-3"><span class="btn btn-sm btn-primary px-4">Login</span></div>
            </div>
        </div>
        <div class="col-12 col-sm-6 col-md-4">
            <div class="login-portal-card" data-bs-toggle="modal" data-bs-target="#hospitalLoginModal">
                <div class="portal-icon text-success"><i class="fa-solid fa-hospital"></i></div>
                <div class="portal-title">Hospital</div>
                <div class="portal-desc">Manage vaccine records and child schedules</div>
                <div class="mt-3"><span class="btn btn-sm btn-success px-4">Login / Register</span></div>
            </div>
        </div>
        <div class="col-12 col-sm-6 col-md-4">
            <div class="login-portal-card" data-bs-toggle="modal" data-bs-target="#parentLoginModal">
                <div class="portal-icon text-warning"><i class="fa-solid fa-person"></i></div>
                <div class="portal-title">Parent</div>
                <div class="portal-desc">Track your child's vaccination schedule</div>
                <div class="mt-3"><span class="btn btn-sm btn-warning px-4">Login / Register</span></div>
            </div>
        </div>
    </div>
</div>

<!-- INFO CARDS -->
<div class="container my-5">
    <h2 class="section-title text-center mb-4">Why Vaccinate?</h2>
    <div class="row g-4">
        <div class="col-12 col-sm-6 col-lg-4">
            <div class="card info-card">
                <img src="./images/parents.jpg" alt="Parents">
                <div class="card-body">
                    <h5 class="card-title">Why Vaccination?</h5>
                    <p class="card-text text-muted" style="font-size:.88rem;">Vaccination protects children from serious diseases and builds immunity for life.</p>
                </div>
            </div>
        </div>
        <div class="col-12 col-sm-6 col-lg-4">
            <div class="card info-card">
                <img src="./images/vaccines.png" alt="Vaccines">
                <div class="card-body">
                    <h5 class="card-title">Vaccination Schedule</h5>
                    <p class="card-text text-muted" style="font-size:.88rem;">Follow the correct vaccination timeline for complete protection at every stage.</p>
                </div>
            </div>
        </div>
        <div class="col-12 col-sm-6 col-lg-4">
            <div class="card info-card">
                <img src="./images/safe.png" alt="Safe">
                <div class="card-body">
                    <h5 class="card-title">Safe &amp; Effective</h5>
                    <p class="card-text text-muted" style="font-size:.88rem;">Vaccines are rigorously tested, safe, and recommended by doctors worldwide.</p>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- ABOUT -->
<div class="container my-5" id="about">
    <div class="about-section">
        <div class="row align-items-center g-4">
            <div class="col-12 col-md-8">
                <h2 class="section-title mb-3">About Our System</h2>
                <p>The Child Vaccination System helps parents track their child's vaccination schedule, connects hospitals to manage vaccine records, and ensures every child receives timely immunization. Our platform bridges the gap between healthcare providers and families to create a healthier generation.</p>
            </div>
            <div class="col-12 col-md-4 text-center">
                <i class="fa-solid fa-syringe text-success" style="font-size:clamp(3rem,8vw,5rem);"></i>
            </div>
        </div>
    </div>
</div>

<!-- CONTACT -->
<div class="container my-5" id="contact">
    <h2 class="section-title text-center mb-4">Contact Us</h2>
    <div class="row justify-content-center">
        <div class="col-12 col-sm-10 col-md-6">
            <div class="card contact-card">
                <p><i class="fa-solid fa-envelope me-2 text-primary"></i>child23@gmail.com</p>
                <p><i class="fa-solid fa-phone me-2 text-success"></i>+91 00000 00000</p>
                <p class="mb-0"><i class="fa-solid fa-location-dot me-2 text-danger"></i>Tamil Nadu, India</p>
            </div>
        </div>
    </div>
</div>

<!-- FOOTER -->
<footer>
    <p>&copy; 2026 Child Vaccination System &nbsp;|&nbsp; All Rights Reserved</p>
    <p class="mt-2"><a href="#about">About</a> &nbsp;|&nbsp; <a href="#contact">Contact</a></p>
</footer>


<!-- ===== ADMIN LOGIN MODAL ===== -->
<div class="modal fade" id="adminModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header bg-primary text-white rounded-top">
                <h5 class="modal-title"><i class="fa-solid fa-user-shield me-2"></i>Admin Login</h5>
                <button class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <form method="post" action="home.py">
                <div class="modal-body pt-3">
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Username</label>
                        <input type="text" name="username" class="form-control" placeholder="Enter: admin" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Password</label>
                        <input type="password" name="password" class="form-control" placeholder="Enter password" required>
                    </div>
                </div>
                <div class="modal-footer pt-0">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <input type="submit" name="login" value="Login" class="btn btn-primary px-4">
                </div>
            </form>
        </div>
    </div>
</div>

<!-- ===== HOSPITAL LOGIN MODAL ===== -->
<div class="modal fade" id="hospitalLoginModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header bg-success text-white rounded-top">
                <h5 class="modal-title"><i class="fa-solid fa-hospital me-2"></i>Hospital Login</h5>
                <button class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <form method="post" action="home.py">
                <div class="modal-body pt-3">
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Username</label>
                        <input type="text" name="emailil" class="form-control" placeholder="Hospital Username" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Password</label>
                        <input type="password" name="passil" class="form-control" placeholder="Password" required>
                    </div>
                    <p class="text-center mb-0 small">Don't have an account?
                        <a href="#" data-bs-dismiss="modal" data-bs-toggle="modal" data-bs-target="#hospitalRegisterModal">Register now</a>
                    </p>
                </div>
                <div class="modal-footer flex-column pt-0">
                    <input type="submit" name="submitil" value="Login" class="btn btn-success w-100">
                    <a href="#" class="text-decoration-none mt-2 small" data-bs-dismiss="modal"
                       data-bs-toggle="modal" data-bs-target="#hospitalForgotModal">Forgot Password?</a>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- ===== HOSPITAL FORGOT PASSWORD MODAL ===== -->
<div class="modal fade" id="hospitalForgotModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title fw-bold">Hospital - Forgot Password</h5>
                <button class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form action="hospital_forgot.py" method="post">
                <div class="modal-body">
                    <label class="form-label fw-semibold">Registered Email</label>
                    <input type="email" name="forgot_email" class="form-control" placeholder="Enter Registered Email" required>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <input type="submit" name="send_reset" value="Send Password" class="btn btn-primary">
                </div>
            </form>
        </div>
    </div>
</div>

<!-- ===== PARENT LOGIN MODAL ===== -->
<div class="modal fade" id="parentLoginModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header bg-warning rounded-top">
                <h5 class="modal-title fw-bold"><i class="fa-solid fa-person me-2"></i>Parent Login</h5>
                <button class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form method="post" action="home.py">
                <div class="modal-body pt-3">
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Username</label>
                        <input type="text" name="emailsl" class="form-control" placeholder="Parent Username" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-semibold">Password</label>
                        <input type="password" name="passsl" class="form-control" placeholder="Password" required>
                    </div>
                    <p class="text-center mb-0 small">Don't have an account?
                        <a href="#" data-bs-dismiss="modal" data-bs-toggle="modal" data-bs-target="#parentRegisterModal">Register now</a>
                    </p>
                </div>
                <div class="modal-footer flex-column pt-0">
                    <input type="submit" name="submitsl" value="Login" class="btn btn-warning w-100">
                    <a href="#" class="text-decoration-none mt-2 small" data-bs-dismiss="modal"
                       data-bs-toggle="modal" data-bs-target="#parentForgotModal">Forgot Password?</a>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- ===== PARENT FORGOT PASSWORD MODAL ===== -->
<div class="modal fade" id="parentForgotModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title fw-bold">Parent - Forgot Password</h5>
                <button class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form action="parent_forgot.py" method="post">
                <div class="modal-body">
                    <label class="form-label fw-semibold">Registered Email</label>
                    <input type="email" name="forgot_email" class="form-control" placeholder="Enter Registered Email" required>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <input type="submit" name="send_reset" value="Reset Password" class="btn btn-primary">
                </div>
            </form>
        </div>
    </div>
</div>

<!-- ===== HOSPITAL REGISTER MODAL ===== -->
<div class="modal fade" id="hospitalRegisterModal" tabindex="-1">
    <div class="modal-dialog modal-lg modal-dialog-scrollable modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header bg-success text-white rounded-top">
                <h5 class="modal-title"><i class="fa-solid fa-hospital me-2"></i>Hospital Registration</h5>
                <button class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <form method="post" action="home.py" enctype="multipart/form-data">
                <div class="modal-body">
                    <div class="row g-3">
                        <div class="col-12">
                            <label class="form-label fw-semibold">Hospital Name</label>
                            <input type="text" class="form-control" name="hospital_name" placeholder="Hospital Name" required>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">State</label>
                            <select class="form-select" id="h_state" name="state" onchange="loadDistricts('h')" required>
                                <option value="">Select State</option>
                                <option>Andhra Pradesh</option><option>Arunachal Pradesh</option><option>Assam</option>
                                <option>Bihar</option><option>Chhattisgarh</option><option>Goa</option>
                                <option>Gujarat</option><option>Haryana</option><option>Himachal Pradesh</option>
                                <option>Jharkhand</option><option>Karnataka</option><option>Kerala</option>
                                <option>Madhya Pradesh</option><option>Maharashtra</option><option>Manipur</option>
                                <option>Meghalaya</option><option>Mizoram</option><option>Nagaland</option>
                                <option>Odisha</option><option>Punjab</option><option>Rajasthan</option>
                                <option>Sikkim</option><option>Tamil Nadu</option><option>Telangana</option>
                                <option>Tripura</option><option>Uttar Pradesh</option><option>Uttarakhand</option>
                                <option>West Bengal</option>
                            </select>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">District</label>
                            <select class="form-select" id="h_district" name="district" required>
                                <option value="">Select District</option>
                            </select>
                        </div>
                        <div class="col-12">
                            <label class="form-label fw-semibold">Hospital Address</label>
                            <textarea class="form-control" name="address" id="h_address" rows="2"
                                      placeholder="Select a district above to auto-fill" required></textarea>
                            <div class="autofill-badge" id="h_address_badge">
                                <i class="fa-solid fa-wand-magic-sparkles me-1"></i>Auto-filled from district &mdash; you may edit
                            </div>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Pincode</label>
                            <input type="text" class="form-control" name="pincode" id="h_pincode"
                                   placeholder="Select district to auto-fill" required>
                            <div class="autofill-badge" id="h_pincode_badge">
                                <i class="fa-solid fa-wand-magic-sparkles me-1"></i>Auto-filled &mdash; verify if needed
                            </div>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Hospital Number</label>
                            <input type="tel" class="form-control" name="hospital_number" placeholder="Phone Number" maxlength="10" required>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Year of Establishment</label>
                            <input type="text" class="form-control" name="year_of_establishment" placeholder="e.g. 2005" required>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">License Proof</label>
                            <input type="file" class="form-control" name="license_proof" accept=".jpg,.jpeg,.png,.pdf" required>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Hospital Image</label>
                            <input type="file" class="form-control" name="hospital_image" accept=".jpg,.jpeg,.png" required>
                        </div>
                        <div class="col-12"><hr class="my-1"><p class="fw-semibold mb-0 text-muted small">Owner Details</p></div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Owner Name</label>
                            <input type="text" class="form-control" name="owner_name" placeholder="Owner Name" required>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Owner Profile Photo</label>
                            <input type="file" class="form-control" name="owner_profile" accept=".jpg,.jpeg,.png" required>
                        </div>
                        <div class="col-12">
                            <label class="form-label fw-semibold">Owner Address</label>
                            <input type="text" class="form-control" name="owner_address" placeholder="Owner Address" required>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Owner Phone Number</label>
                            <input type="tel" class="form-control" name="owner_phone_number" placeholder="Phone Number" maxlength="10" required>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Owner Email</label>
                            <input type="email" class="form-control" name="owner_email" placeholder="Email" required>
                        </div>
                        <div class="col-12">
                            <div class="alert alert-info py-2 mb-0">
                                <small><i class="fa-solid fa-circle-info me-1"></i>
                                Username format: <strong>hospitalname_state_district_id</strong> &nbsp;|&nbsp;
                                Your credentials will be shown after registration.</small>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <input type="submit" name="hospital_register" value="Register" class="btn btn-success px-4">
                </div>
            </form>
        </div>
    </div>
</div>

<!-- ===== PARENT REGISTER MODAL ===== -->
<div class="modal fade" id="parentRegisterModal" tabindex="-1">
    <div class="modal-dialog modal-lg modal-dialog-scrollable modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header bg-warning rounded-top">
                <h5 class="modal-title fw-bold"><i class="fa-solid fa-person me-2"></i>Parent Registration</h5>
                <button class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form method="post" action="home.py" enctype="multipart/form-data" id="parentRegisterForm">
                <div class="modal-body">
                    <div class="row g-3">
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Father Name</label>
                            <input type="text" class="form-control" name="father_name" placeholder="Father Name" required>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Father Date of Birth</label>
                            <input type="date" class="form-control" name="father_age" id="father_dob" required>
                            <div class="dob-error"   id="father_dob_error"><i class="fa-solid fa-circle-exclamation me-1"></i><span></span></div>
                            <div class="dob-success" id="father_dob_success"><i class="fa-solid fa-circle-check me-1"></i><span></span></div>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Mother Name</label>
                            <input type="text" class="form-control" name="mother_name" placeholder="Mother Name" required>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Mother Date of Birth</label>
                            <input type="date" class="form-control" name="mother_age" id="mother_dob" required>
                            <div class="dob-error"   id="mother_dob_error"><i class="fa-solid fa-circle-exclamation me-1"></i><span></span></div>
                            <div class="dob-success" id="mother_dob_success"><i class="fa-solid fa-circle-check me-1"></i><span></span></div>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Mother Weight (kg)</label>
                            <input type="number" class="form-control" name="mother_weight"
                                   placeholder="Weight in kg (30-200)" min="30" max="200" step="0.1" required>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Email</label>
                            <input type="email" class="form-control" name="email" placeholder="Email Address" required>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Mobile Number</label>
                            <input type="tel" class="form-control" name="mobile_number"
                                   placeholder="10-digit mobile" maxlength="10" required>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Father Occupation</label>
                            <input type="text" class="form-control" name="occupation" placeholder="Occupation" required>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Father Aadhar Image</label>
                            <input type="file" class="form-control" name="father_aadhar_image" accept=".jpg,.jpeg,.png,.pdf" required>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Profile Image</label>
                            <input type="file" class="form-control" name="parent_profile" accept=".jpg,.jpeg,.png" required>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">State</label>
                            <select class="form-select" id="p_state" name="state" onchange="loadDistricts('p')" required>
                                <option value="">Select State</option>
                                <option>Andhra Pradesh</option><option>Arunachal Pradesh</option><option>Assam</option>
                                <option>Bihar</option><option>Chhattisgarh</option><option>Goa</option>
                                <option>Gujarat</option><option>Haryana</option><option>Himachal Pradesh</option>
                                <option>Jharkhand</option><option>Karnataka</option><option>Kerala</option>
                                <option>Madhya Pradesh</option><option>Maharashtra</option><option>Manipur</option>
                                <option>Meghalaya</option><option>Mizoram</option><option>Nagaland</option>
                                <option>Odisha</option><option>Punjab</option><option>Rajasthan</option>
                                <option>Sikkim</option><option>Tamil Nadu</option><option>Telangana</option>
                                <option>Tripura</option><option>Uttar Pradesh</option><option>Uttarakhand</option>
                                <option>West Bengal</option>
                            </select>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">District</label>
                            <select class="form-select" id="p_district" name="district" required>
                                <option value="">Select District</option>
                            </select>
                        </div>
                        <div class="col-12">
                            <label class="form-label fw-semibold">Address</label>
                            <textarea class="form-control" name="address" id="p_address" rows="2"
                                      placeholder="Select a district above to auto-fill" required></textarea>
                            <div class="autofill-badge" id="p_address_badge">
                                <i class="fa-solid fa-wand-magic-sparkles me-1"></i>Auto-filled from district &mdash; you may edit
                            </div>
                        </div>
                        <div class="col-12 col-sm-6">
                            <label class="form-label fw-semibold">Pincode</label>
                            <input type="text" class="form-control" name="pincode" id="p_pincode"
                                   placeholder="Select district to auto-fill" required>
                            <div class="autofill-badge" id="p_pincode_badge">
                                <i class="fa-solid fa-wand-magic-sparkles me-1"></i>Auto-filled &mdash; verify if needed
                            </div>
                        </div>
                        <div class="col-12">
                            <div class="alert alert-info py-2 mb-0">
                                <small><i class="fa-solid fa-circle-info me-1"></i>
                                Username format: <strong>fathername_state_district_id</strong> &nbsp;|&nbsp;
                                Your credentials will be shown after registration.</small>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <input type="submit" name="parent_register" value="Register" class="btn btn-warning px-4">
                </div>
            </form>
        </div>
    </div>
</div>


<script>
    async function loadDistricts(prefix) {{
        const stateEl    = document.getElementById(prefix + '_state');
        const districtEl = document.getElementById(prefix + '_district');
        const state      = stateEl.value;

        districtEl.innerHTML = '<option value="">Loading...</option>';
        districtEl.disabled  = true;
        clearAddressFields(prefix);

        if (!state) {{
            districtEl.innerHTML = '<option value="">Select District</option>';
            districtEl.disabled  = false;
            return;
        }}

        try {{
            const resp = await fetch('get_districts.py?state=' + encodeURIComponent(state));
            const data = await resp.json();

            districtEl.innerHTML = '<option value="">Select District</option>';

            if (!data || data.length === 0) {{
                districtEl.innerHTML = '<option value="">No districts found for this state</option>';
            }} else {{
                data.forEach(function(item) {{
                    const o           = document.createElement('option');
                    o.value           = item.district;
                    o.textContent     = item.district;
                    o.dataset.address = item.address || '';
                    o.dataset.pincode = item.pincode || '';
                    districtEl.appendChild(o);
                }});
            }}
        }} catch (err) {{
            console.error('District fetch error:', err);
            districtEl.innerHTML = '<option value="">Error loading districts — try again</option>';
        }} finally {{
            districtEl.disabled = false;
        }}

        if (!districtEl.dataset.listenerAttached) {{
            districtEl.addEventListener('change', function () {{
                const sel = this.options[this.selectedIndex];
                if (sel && sel.dataset.address) {{
                    fillAddressFields(prefix, sel.dataset.address, sel.dataset.pincode);
                }} else {{
                    clearAddressFields(prefix);
                }}
            }});
            districtEl.dataset.listenerAttached = 'true';
        }}
    }}

    function fillAddressFields(prefix, address, pincode) {{
        const addrEl    = document.getElementById(prefix + '_address');
        const pinEl     = document.getElementById(prefix + '_pincode');
        const addrBadge = document.getElementById(prefix + '_address_badge');
        const pinBadge  = document.getElementById(prefix + '_pincode_badge');
        if (addrEl)    {{ addrEl.value = address; }}
        if (pinEl)     {{ pinEl.value  = pincode; }}
        if (addrBadge) addrBadge.classList.add('visible');
        if (pinBadge && pincode) pinBadge.classList.add('visible');
    }}

    function clearAddressFields(prefix) {{
        const addrEl    = document.getElementById(prefix + '_address');
        const pinEl     = document.getElementById(prefix + '_pincode');
        const addrBadge = document.getElementById(prefix + '_address_badge');
        const pinBadge  = document.getElementById(prefix + '_pincode_badge');
        if (addrEl)    {{ addrEl.value = ''; addrEl.placeholder = 'Select a district above to auto-fill'; }}
        if (pinEl)     {{ pinEl.value  = ''; pinEl.placeholder  = 'Select district to auto-fill'; }}
        if (addrBadge) addrBadge.classList.remove('visible');
        if (pinBadge)  pinBadge.classList.remove('visible');
    }}

    function calcAge(dob) {{
        const d = new Date(dob), t = new Date();
        let a = t.getFullYear() - d.getFullYear();
        const m = t.getMonth() - d.getMonth();
        if (m < 0 || (m === 0 && t.getDate() < d.getDate())) a--;
        return a;
    }}

    function showDobFeedback(inId, errId, okId, msg, isErr) {{
        const inp = document.getElementById(inId);
        const err = document.getElementById(errId);
        const ok  = document.getElementById(okId);
        if (isErr) {{
            inp.classList.add('is-invalid-dob'); inp.classList.remove('is-valid-dob');
            err.querySelector('span').textContent = msg;
            err.style.display = 'block'; ok.style.display = 'none';
        }} else {{
            inp.classList.remove('is-invalid-dob'); inp.classList.add('is-valid-dob');
            ok.querySelector('span').textContent = msg;
            ok.style.display = 'block'; err.style.display = 'none';
        }}
    }}

    function clearDobFeedback(inId, errId, okId) {{
        document.getElementById(inId).classList.remove('is-invalid-dob','is-valid-dob');
        document.getElementById(errId).style.display = 'none';
        document.getElementById(okId).style.display  = 'none';
    }}

    function validateDob(inId, errId, okId, label) {{
        const val = document.getElementById(inId).value;
        if (!val) {{ clearDobFeedback(inId, errId, okId); return false; }}
        const today = new Date().toISOString().split('T')[0];
        if (val > today) {{
            showDobFeedback(inId, errId, okId, label + "'s date of birth cannot be a future date.", true);
            return false;
        }}
        const age = calcAge(val);
        if (age < 18) {{
            showDobFeedback(inId, errId, okId, label + " must be at least 18 years old (age: " + age + ").", true);
            return false;
        }}
        if (age > 60) {{
            showDobFeedback(inId, errId, okId, label + "'s age (" + age + ") seems too high. Please verify.", true);
            return false;
        }}
        showDobFeedback(inId, errId, okId, label + " age: " + age + " years \u2014 OK", false);
        return true;
    }}

    document.addEventListener('DOMContentLoaded', function () {{

        const today   = new Date();
        const maxDate = today.toISOString().split('T')[0];
        const minDate = new Date(today.getFullYear()-100, today.getMonth(), today.getDate())
                        .toISOString().split('T')[0];
        ['father_dob','mother_dob'].forEach(function(id) {{
            const el = document.getElementById(id);
            if (el) {{ el.max = maxDate; el.min = minDate; }}
        }});

        const fDob = document.getElementById('father_dob');
        const mDob = document.getElementById('mother_dob');
        if (fDob) fDob.addEventListener('change', function() {{
            validateDob('father_dob','father_dob_error','father_dob_success','Father');
        }});
        if (mDob) mDob.addEventListener('change', function() {{
            validateDob('mother_dob','mother_dob_error','mother_dob_success','Mother');
        }});

        const pForm = document.getElementById('parentRegisterForm');
        if (pForm) {{
            pForm.addEventListener('submit', function(e) {{
                const fOk = validateDob('father_dob','father_dob_error','father_dob_success','Father');
                const mOk = validateDob('mother_dob','mother_dob_error','mother_dob_success','Mother');

                const wEl = pForm.querySelector('input[name="mother_weight"]');
                const w   = parseFloat(wEl ? wEl.value : '');
                let wErr  = '';
                if (isNaN(w))          wErr = "Mother's weight is required.";
                else if (w < 30)       wErr = "Mother's weight (" + w + " kg) is too low. Minimum is 30 kg.";
                else if (w > 200)      wErr = "Mother's weight (" + w + " kg) is too high. Maximum is 200 kg.";
                else if (!Number.isInteger(w * 10)) wErr = "Enter weight up to 1 decimal place only (e.g. 58.5).";

                if (!fOk || !mOk || wErr) {{
                    e.preventDefault();
                    if (wErr) alert(wErr);
                    const firstErr = pForm.querySelector('.dob-error[style*="block"]');
                    if (firstErr) firstErr.scrollIntoView({{behavior:'smooth',block:'center'}});
                }}
            }});
        }}
    }});
</script>
</body>
</html>
""")

con.close()