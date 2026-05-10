#!C:/Users/santh/AppData/Local/Programs/Python/Python311/python.exe
print("Content-Type: application/json\r\n\r\n")

import cgi
import cgitb
import pymysql
import sys
import json

cgitb.enable()
sys.stdout.reconfigure(encoding='utf-8')

form = cgi.FieldStorage()
state = form.getfirst("state", "")

try:
    con = pymysql.connect(host="localhost", user="root", password="", database="child")
    cur = con.cursor()

    # Returns district name + address + pincode for each row in the districts table
    cur.execute(
        "SELECT district, address, pincode FROM districts WHERE state=%s ORDER BY district",
        (state,)
    )
    rows = cur.fetchall()

    result = [
        {
            "district": r[0],
            "address":  r[1] if r[1] else "",
            "pincode":  r[2] if r[2] else ""
        }
        for r in rows
    ]

    print(json.dumps(result))
    con.close()

except Exception as e:
    print(json.dumps([]))