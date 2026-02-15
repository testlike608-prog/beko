from flask import Blueprint
from flask import render_template, request, redirect, url_for, session
import  os
import helpers as hlb
home = Blueprint(
    "home",
    __name__,
    static_folder="static",
    template_folder="templates"
)

@home.get("/home")
def page_index():
    csv_files = []
    for file in os.listdir(hlb.CSV_SOURCE_DIR):
        if file.endswith(".csv"):
            file_path = os.path.join(hlb.CSV_SOURCE_DIR, file)
            if os.path.isfile(file_path):
                csv_files.append({
                    "name": file,
                    "path": f"/programs/{file}",
                    "size": os.path.getsize(file_path)
                })

    csv_files.sort(
        key=lambda x: os.path.getmtime(os.path.join(hlb.CSV_SOURCE_DIR, x["name"])),
        reverse=True
    )
    
    username = session.get('username', None)
    auth = session.get('auth', None)
    return render_template(
        "INDEX_HTML.html",
        username=username,
        auth=auth,
        csv_files=csv_files,
       # default_device_ip=IO_MODULE_IP,
       # default_device_port=IO_MODULE_PORT

    )