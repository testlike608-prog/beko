from flask import Blueprint
from flask import render_template, request, redirect, url_for, session
import csv
import datetime



LOGINS_FILE = "logins.csv"


CreateUser = Blueprint(
    "CreateUser",
    __name__,
    static_folder="static",
    template_folder="templates"
)

@CreateUser.route('/create_user', methods=['GET', 'POST'])
def create_user():
    # Admins and developers are allowed to create new users
    auth_role = session.get("auth")
    if auth_role not in ("admin", "dev"):
        return "Access denied", 403
    error = ""
    NewUser_data = {"username": "", "password": "", "auth": ""}
    message=""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        auth = request.form.get('Authentication', '').strip()
        NewUser_data = {"username": username, "password": password, "auth": auth}

        if not username or not password or not auth:
            error = "Please fill all fields"
        else:
            with open(LOGINS_FILE, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([username, password, auth, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
<<<<<<< HEAD
                message = "User created  successfully!"
            return render_template("CREATE_USER_HTML.html",message=message, NewUser_data=NewUser_data)
=======
                message = "✅ User created  successfully!"
            return render_template("CREATE_USER_HTML.html", message=message, auth=auth_role, NewUser_data=NewUser_data)
>>>>>>> 9bf21a6 (ADD debug mode)

    return render_template("CREATE_USER_HTML.html", error=error, auth=auth_role, NewUser_data=NewUser_data)