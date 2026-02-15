import os, pyodbc
import subprocess
import ClientsClass 
conn_str_db1_global=""
conn_str_db2_global=""

def check_driver():
    drivers = [x for x in pyodbc.drivers()]
    return any("ODBC Driver 17 for SQL Server" in d or "ODBC Driver 18 for SQL Server" in d for d in drivers)

def install_driver():
    msi_path = os.path.join(os.path.dirname(__file__), "msodbcsql.msi")
    if not os.path.exists(msi_path):
        print("⚠ ODBC installer not found")
        return False
    try:
        subprocess.run(["msiexec", "/i", msi_path, "/quiet", "/norestart"], check=True)
        print("✅ ODBC Driver installed")
        return True
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

if not check_driver():
    print("⚠ ODBC Driver not found, installing...")
    install_driver()

def auto_connect_db():
    """Automatically connect to saved database settings"""
    global conn_str_db1_global, conn_str_db2_global

    def connect_from_file(filename, index):
        if not os.path.exists(filename):
            return None, f"⚠️ No saved DB{index} settings"
        with open(filename, "r") as f:
            data = f.read().strip().split("|")
            if len(data) != 5:
                return None, f"⚠️ Invalid DB{index} format"
            serveraddr, database_name, Auth, user_name, password = data

        if Auth == "Windows Authentication":
            conn_str = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={serveraddr};DATABASE={database_name};"
                f"Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={serveraddr};DATABASE={database_name};"
                f"UID={user_name};PWD={password};Encrypt=no;TrustServerCertificate=yes;"
            )

        try:
            with pyodbc.connect(conn_str, timeout=15):
                pass
            return conn_str, f"✅ Auto-connected to DB{index}"
        except Exception as e:
            return None, f"❌ DB{index} connection failed: {e}"

    conn_str_db1_global, msg1 = connect_from_file("last_db1_settings.txt", 1)
    conn_str_db2_global, msg2 = connect_from_file("last_db2_settings.txt", 2)
    print(f"{msg1}\n{msg2}")

def upload_tests_result_to_db(dummy, station_name, station_result, failed_tests, Client:ClientsClass):
    """
    Inserts a new record in DB2 (VisionResult table)
    with SFC, TESTNAME, RESULT, NCCODE columns.
    
    Args:
        dummy: The SFC/Dummy number
        station_name: Test name (e.g., VisionOuterTest, VisionInnerTest)
        station_result: Overall result (PASS/FAIL)
        failed_tests: Comma-separated string of failed test names
    """
    global conn_str_db2_global

    try:
        # Check DB connection string exists
        if not conn_str_db2_global:
            Client._log_add("ERROR", "❌ No DB2 connection string found")
            return

        # Insert new row
        with pyodbc.connect(conn_str_db2_global, timeout=15) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO VisionResult (SFC, TESTNAME, RESULT, NCCODE)
                    VALUES (?, ?, ?, ?)
                    """,
                    (dummy, station_name, station_result, failed_tests)
                )
                conn.commit()
                Client._log_add("INFO",f"✅ Uploaded to DB → SFC={dummy}, TestName={station_name}, Result={station_result}, FailedTests={failed_tests}")
               
                    
              
                
            except Exception as e:
                Client._log_add("ERROR", f"❌ DB Insert Error: {e}")
                pass
    except Exception as ex:
         Client._log_add("ERROR", f"❌ Error connecting to DB: {ex}")
         pass