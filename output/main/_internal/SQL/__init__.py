import pyodbc
from flask import Blueprint
from flask import render_template, request
from helpers import TIME_SETTINGS







SQL = Blueprint("SQL", 
    __name__,
    static_folder="static",
    template_folder="templates"
)

@SQL.route("/sql_connection", methods=["GET", "POST"])
def sql_connection():
    global conn_str_db1_global, conn_str_db2_global, message, last_dummy_number, last_dummy_number2
    global sock1, sock3, listener_thread, running, server1_connected, server3_connected
    global last_raw_data, last_raw_data2, last_dummy_extracted, last_dummy_extracted2, last_db_status, last_db_status2
    message = ""
    if request.method == "POST":
        action = request.form.get("action")

        # If Reset button pressed
        if request.form.get("reset") == "true":
            return render_template("SQL_CONNECTION_HTML.html", 
                                        message="", form_data={}, 
                                        last_dummy_number=last_dummy_number,
                                        last_dummy_number2=last_dummy_number2,
                                        server1_connected=server1_connected,
                                        server3_connected=server3_connected,
                                        conn_str_db1_global=conn_str_db1_global,
                                        conn_str_db2_global=conn_str_db2_global,
                                        last_raw_data=last_raw_data,
                                        last_raw_data2=last_raw_data2,
                                        last_dummy_extracted=last_dummy_extracted,
                                        last_dummy_extracted2=last_dummy_extracted2,
                                        last_db_status=last_db_status,
                                        last_db_status2=last_db_status2
                                   
                                       )

        #DATABASE CONNECTION
        if action == "db":
            server1_addr = request.form.get("server_addr1")
            db1_name = request.form.get("database1")
            server2_addr = request.form.get("server_addr2")
            db2_name = request.form.get("database2")
            Auth = request.form.get("Authentication")
            user_name = request.form.get("login")
            password = request.form.get("password")

            try:
                # Build connection strings for both servers
                if Auth == "Windows Authentication":
                    conn_str1 = (
                        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                        f"SERVER={server1_addr};DATABASE={db1_name};"
                        f"Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;"
                    )
                    conn_str2 = (
                        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                        f"SERVER={server2_addr};DATABASE={db2_name};"
                        f"Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;"
                    )
                else:
                    conn_str1 = (
                        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                        f"SERVER={server1_addr};DATABASE={db1_name};"
                        f"UID={user_name};PWD={password};Encrypt=no;TrustServerCertificate=yes;"
                    )
                    conn_str2 = (
                        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                        f"SERVER={server2_addr};DATABASE={db2_name};"
                        f"UID={user_name};PWD={password};Encrypt=no;TrustServerCertificate=yes;"
                    )

                # Test both connections separately
                pyodbc.connect(conn_str1, timeout=TIME_SETTINGS['dbTimeout']).close()
                pyodbc.connect(conn_str2, timeout=TIME_SETTINGS['dbTimeout']).close()

                conn_str_db1_global = conn_str1
                conn_str_db2_global = conn_str2
                message = "DATABASE CONNECTION SUCCESSFUL (Server 1 & Server 2)"

                # Save last successful settings for both servers
                with open("last_db1_settings.txt", "w") as f:
                    f.write(f"{server1_addr}|{db1_name}|{Auth}|{user_name}|{password}")

                with open("last_db2_settings.txt", "w") as f:
                    f.write(f"{server2_addr}|{db2_name}|{Auth}|{user_name}|{password}")

            except Exception as ex:
                message = f"Database connection failed: {ex}"

    return render_template("SQL_CONNECTION_HTML.html",
                                message=message,
                                form_data=request.form,
                    )