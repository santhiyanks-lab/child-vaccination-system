#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe

import cgi
import cgitb
import pymysql
import smtplib
import random
from email.mime.text import MIMEText

cgitb.enable()
print("Content-type:text/html\r\n\r\n")

form = cgi.FieldStorage()

if "send_reset" in form:

    email = form.getvalue("forgot_email")

    # ---------------- DATABASE CONNECTION ----------------
    try:
        con = pymysql.connect(
            host="localhost",
            user="root",
            password="",
            database="child"
        )
        cur = con.cursor()
    except:
        print("<script>alert('Database Connection Failed');</script>")
        exit()

    # ---------------- CHECK EMAIL EXISTS ----------------
    cur.execute("SELECT hospital_name FROM hospital WHERE owner_email=%s", (email,))
    data = cur.fetchone()

    if data:

        hospital_name = data[0]

        # ---------------- GENERATE NEW TEMP PASSWORD ----------------
        new_password = "HSP" + str(random.randint(1000, 9999))

        # ---------------- UPDATE PASSWORD IN DATABASE ----------------
        cur.execute("UPDATE hospital SET password=%s WHERE owner_email=%s",
                    (new_password, email))
        con.commit()

        # ---------------- EMAIL CONFIG ----------------
        sender_email = "santhiyanks@gmail.com"
        sender_password = "snnr avxt cqgb ocwy"

        message = f"""
Dear {hospital_name},

Your password has been reset successfully.

New Temporary Password:
{new_password}

Please login and change your password immediately.

Thank You.
"""

        msg = MIMEText(message)
        msg['Subject'] = "Hospital Password Reset"
        msg['From'] = sender_email
        msg['To'] = email

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
            server.quit()

            print("""
            <script>
            alert('New Password Sent to Your Email');
            window.location.href='home.py';
            </script>
            """)

        except Exception as e:
            print(f"<script>alert('Email Sending Failed: {str(e)}');</script>")

    else:
        print("""
        <script>
        alert('Email Not Registered');
        window.location.href='home.py';
        </script>
        """)

    con.close()

else:
    print("""
    <script>
    alert('Invalid Request');
    window.location.href='home.py';
    </script>
    """)
