from flask import Blueprint, request, jsonify
import json
import os

# 1. تعريف البلو برينت بدل Flask app
io_mapping_bp = Blueprint('io_mapping', __name__)

CONFIG_FILE = 'config.json'

# الإعدادات الافتراضية
default_mapping = {
    "LIGHTING_S1": 8, "LIGHTING_S2": 1, "BUZZER_S1": 2, "BUZZER_S2": 3,
    "SCANNER_S1": 4, "SCANNER_S2": 5, "TESTDONE_S1": 6, "TESTDONE_S2": 7, "FAILURE": 16,
    "READ_DI0": 0, "READ_DI1": 1, "READ_INPUTS_REG": 34
}

io_mapping = {}

def load_mapping():
    global io_mapping
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            io_mapping = json.load(file)
    else:
        io_mapping = default_mapping.copy()

def save_mapping_to_file():
    with open(CONFIG_FILE, 'w') as file:
        json.dump(io_mapping, file, indent=4)

# تحميل الإعدادات عند عمل Import للملف
load_mapping()

# 2. تغيير @app.route إلى @io_mapping_bp.route
@io_mapping_bp.route('/save_mapping', methods=['POST'])
def save_mapping():
    global io_mapping
    io_mapping.update(request.json)
    save_mapping_to_file()
    return jsonify({"status": "success"})

# الدالة الشاملة لبناء الكود
def generate_modbus_command(function_name, action):
    if function_name not in io_mapping:
        return "Error: Function not mapped"

    pin_number = io_mapping[function_name]
    pin_hex = f"{pin_number:04X}"  
    
    header = "00010000000601" 
    
    if action == "ON":
        return header + "05" + pin_hex + "FF00"      
    elif action == "OFF":
        return header + "05" + pin_hex + "0000"      
    elif action == "READ_DI":
        return header + "02" + pin_hex + "0001"      
    elif action == "READ_REG":
        return header + "03" + pin_hex + "0001"      
    
    return "Error: Unknown action"

@io_mapping_bp.route('/command', methods=['POST'])
def execute_command():
    data = request.json
    func_name = data.get("function") 
    action = data.get("action")      
    
    hex_command = generate_modbus_command(func_name, action)
    print(f"[{action}] Command for {func_name}: {hex_command}")
    
    # هنا كود الإرسال للموديول
    return jsonify({"command": hex_command})

@io_mapping_bp.route('/off_all', methods=['POST'])
def off_all():
    cmd_off_all = "000100000009010F00000010020000"
    print(f"Sending OFF ALL Command: {cmd_off_all}")
    
    return jsonify({"command": cmd_off_all, "status": "All Off Sent"})

# (ملاحظة: شيلنا جزء app.run عشان الملف ده مجرد Blueprint مش هيشتغل لوحده)