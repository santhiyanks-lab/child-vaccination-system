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

    # -------- DATABASE CONNECTION --------
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

    # -------- CHECK EMAIL EXISTS --------
    cur.execute("SELECT parent_id, father_name FROM parent WHERE email=%s", (email,))
    data = cur.fetchone()

    if data:

        parent_id, father_name = data

        # -------- GENERATE NEW TEMP PASSWORD --------
        new_password = "PRT" + str(random.randint(1000, 9999))

        # -------- UPDATE DATABASE --------
        cur.execute("UPDATE parent SET password=%s WHERE parent_id=%s",
                    (new_password, parent_id))
        con.commit()

        # -------- EMAIL CONFIG --------
        sender_email = "santhiyanks@gmail.com"
        sender_password = "snnr avxt cqgb ocwy"

        message = f"""
Dear {father_name},

Your Parent Account password has been reset.

New Temporary Password:
{new_password}

Please login and change your password immediately.

Thank You.
"""

        msg = MIMEText(message)
        msg['Subject'] = "Parent Password Reset"
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
