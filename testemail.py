#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe

print("Content-type:text/html\r\n\r\n")

import cgi
import pymysql
import smtplib
from email.mime.text import MIMEText

# FORM DATA
form = cgi.FieldStorage()

# DATABASE CONNECTION
con = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    database="child"
)



sender = "santhiyanks@gmail.com"
password = " snnr avxt cqgb ocwy"
receiver = "santhiyanks@gmail.com"

msg = MIMEText("Test Email Working")
msg["Subject"] = "Test"
msg["From"] = sender
msg["To"] = receiver

server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login(sender, password)
server.sendmail(sender, receiver, msg.as_string())
server.quit()

print("Email Sent Successfully")