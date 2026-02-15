from flask import Blueprint
from flask import render_template, request, redirect, url_for, session
import  os
import helpers as hlb
from ClientsClass import queue_manual, queue_manual2
import queue, jsonify

home = Blueprint(
    "home",
    __name__,
    static_folder="static",
    template_folder="templates"
)


@home.route('/add_to_queue', methods=['POST'])
def add_to_queue():
    data = request.json
    dummy_number = data.get('dummy_number')
    
    if not dummy_number:
        return jsonify({"status": "error", "message": "No data"}), 400

    try:
        # إضافة الرقم للكيو (block=False عشان ميعلقش الـ Request لو الكيو مليان)
        queue_manual.put(value=dummy_number, block=False)
        
        print(f"📥 New Item Added: {dummy_number}")
        print(f"📦 Total in Queue: {queue_manual.qsize()}")
        
        return jsonify({
            "status": "success", 
            "current_count": queue_manual.qsize()
        }), 200
    except queue.Full:
        return jsonify({"status": "error", "message": "Queue is full!"}), 500
    
@home.route('/add_to_queue2', methods=['POST'])
def add_to_queue():
    data = request.json
    dummy_number = data.get('dummy_number')
    
    if not dummy_number:
        return jsonify({"status": "error", "message": "No data"}), 400

    try:
        # إضافة الرقم للكيو (block=False عشان ميعلقش الـ Request لو الكيو مليان)
        queue_manual2.put(value=dummy_number, block=False)
        
        print(f"📥 New Item Added: {dummy_number}")
        print(f"📦 Total in Queue: {queue_manual2.qsize()}")
        
        return jsonify({
            "status": "success", 
            "current_count": queue_manual2.qsize()
        }), 200
    except queue.Full:
        return jsonify({"status": "error", "message": "Queue is full!"}), 500
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