"""
ioSetting
---------
إعدادات الـ I/O mapping + مسارات VisionMaster، كلها في config.json.

شكل الملف الجديد:
    {
        "io_mapping":    { "LIGHTING_S1": 8, ... },
        "vision_master": { "assembly_dir": "", "solution_path": "", ... }
    }

الملف القديم كان dictionary مسطّح فيه الـ mapping بس. load_mapping() بتكتشف
الشكل القديم وبتحوّله أوتوماتيكيًا لأول مرة، فمفيش أي إعدادات بتضيع.

مهم: مسارات VisionMaster اتحطّت في قسم منفصل عن الـ mapping عن قصد —
لأن save_mapping_to_file() بتكتب القاموس كله، والواجهة بتعمل parseInt()
لكل الحقول، فلو المسارات كانت جوه نفس القاموس كانت هتتحول لـ NaN.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from flask import Blueprint, request, jsonify

# 1. تعريف البلو برينت بدل Flask app (لسه مستخدم في النسخة القديمة main.py)
io_mapping_bp = Blueprint('io_mapping', __name__)

CONFIG_FILE = 'config.json'

# الإعدادات الافتراضية
default_mapping = {
    "LIGHTING_S1": 8, "LIGHTING_S2": 1, "BUZZER_S1": 2, "BUZZER_S2": 3,
    "SCANNER_S1": 4, "SCANNER_S2": 5, "TESTDONE_S1": 6, "TESTDONE_S2": 7, "FAILURE": 16,
    "READ_DI0": 0, "READ_DI1": 1, "READ_INPUTS_REG": 34
}

default_vision_master = {
    "assembly_dir": "",     # فاضي = اكتشاف أوتوماتيكي من Program Files
    "solution_path": "",    # مسار ملف .solw / .sol
}

io_mapping: Dict[str, Any] = {}
vision_master_config: Dict[str, Any] = {}


# ----------------------------------------------------------------------
# تحميل / حفظ
# ----------------------------------------------------------------------
def _read_config_file() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[ioSetting] تعذّرت قراءة {CONFIG_FILE} ({exc}) — هنستخدم الافتراضي")
        return {}


def load_mapping():
    """تحميل الإعدادات من config.json مع دعم الشكل القديم المسطّح."""
    global io_mapping, vision_master_config

    data = _read_config_file()

    if not data:
        io_mapping = default_mapping.copy()
        vision_master_config = default_vision_master.copy()
        return

    if "io_mapping" in data:
        # الشكل الجديد
        io_mapping = {**default_mapping, **(data.get("io_mapping") or {})}
        vision_master_config = {
            **default_vision_master,
            **(data.get("vision_master") or {}),
        }
    else:
        # الشكل القديم: الملف كله عبارة عن mapping
        print("[ioSetting] تحويل config.json للشكل الجديد (io_mapping / vision_master)")
        io_mapping = {**default_mapping, **data}
        vision_master_config = default_vision_master.copy()
        save_config_to_file()


def save_config_to_file():
    """كتابة الملف كله (الـ mapping + إعدادات VisionMaster)."""
    payload = {
        "io_mapping": io_mapping,
        "vision_master": vision_master_config,
    }
    tmp_path = CONFIG_FILE + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as file:
        json.dump(payload, file, indent=4, ensure_ascii=False)
    os.replace(tmp_path, CONFIG_FILE)


def save_mapping_to_file():
    """
    محتفظين بالاسم القديم عشان الكود الموجود (io_setting_router) ما يتكسرش.
    بقت بتكتب الملف كله مش الـ mapping بس، فمسارات VisionMaster ما بتتمسحش.
    """
    save_config_to_file()


# ----------------------------------------------------------------------
# إعدادات VisionMaster
# ----------------------------------------------------------------------
def get_vision_master_config() -> Dict[str, Any]:
    """نسخة من إعدادات VisionMaster (بيستخدمها vision_master.py)."""
    return {**default_vision_master, **vision_master_config}


def save_vision_master_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    """تحديث إعدادات VisionMaster وحفظها. بترجع الإعدادات بعد التحديث."""
    global vision_master_config

    clean: Dict[str, Any] = {}
    for key in ("assembly_dir", "solution_path"):
        if key in payload:
            clean[key] = str(payload.get(key) or "").strip()

    vision_master_config = {**get_vision_master_config(), **clean}
    save_config_to_file()
    return get_vision_master_config()


# تحميل الإعدادات عند عمل Import للملف
load_mapping()


# ----------------------------------------------------------------------
# الدالة الشاملة لبناء الكود
# ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
# 2. تغيير @app.route إلى @io_mapping_bp.route (النسخة القديمة Flask)
# ----------------------------------------------------------------------
@io_mapping_bp.route('/save_mapping', methods=['POST'])
def save_mapping():
    global io_mapping
    io_mapping.update(request.json)
    save_mapping_to_file()
    return jsonify({"status": "success"})


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
