from flask import Blueprint
from flask import render_template, redirect, url_for
from flask import Flask, request, jsonify, render_template_string, send_from_directory, session
from typing import Dict,Tuple,List
import os,re
from helpers import _save_csv_file,_csv_path,load_tests
import csv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROGRAMS_DIR = BASE_DIR
#Globals
CSV_CACHE: Dict[Tuple[str, str], Dict] = {}
CSV_CACHE_MAX = 256
CreateProgram = Blueprint("CreateProgram", 
    __name__,
    static_folder="static",
    template_folder="templates"
)


# ---------------- CSV Functions ----------------
def _csv_path(sku: str, part: str) -> str:
    safe_sku = re.sub(r'[^\w\-]', '', sku or "")
    return os.path.join(PROGRAMS_DIR, f"{safe_sku}{part}.csv")

def _load_csv_file(path: str) -> Dict[str, str]:
    out = {}
    with open(path, "r", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r, None)
        for row in r:
            if len(row) == 2:
                out[row[0]] = row[1]
    return out

def _save_csv_file(path: str, rows: List[Tuple[str, str]]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Label", "Value"])
        for k, v in rows:
            w.writerow([k, v])

def _get_label(val: str) -> str:
    """Extract label from 'Label|Code' format"""
    if not val:
        return ""
    parts = str(val).split("|", 1)
    return parts[0].strip() if len(parts) == 2 else val

def _get_code(val: str) -> str:
    """Extract code from 'Label|Code' format"""
    if not val:
        return ""
    parts = str(val).split("|", 1)
    return parts[1].strip() if len(parts) == 2 else ""

def get_program_cached(sku: str, part: str):
    part = (part or "").upper()
    if part not in ("S1", "S2"):
        raise FileNotFoundError("part must be S1 or S2")
    path = _csv_path(sku, part)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{os.path.basename(path)} not found")
    mtime = os.path.getmtime(path)
    key = (sku, part)
    e = CSV_CACHE.get(key)
    if e and e.get("mtime") == mtime:
        return e
    if len(CSV_CACHE) > CSV_CACHE_MAX:
        victim = sorted(CSV_CACHE.items(), key=lambda kv: kv[1].get("mtime", 0.0))[0][0]
        CSV_CACHE.pop(victim, None)
    data = _load_csv_file(path)

    if part == "S1":
        order = ["Front Logo", "Color", "Data logo", "Inverter logo", "Power logo"]
    else:
        order = ["Eva cover", "Drawer printing", "Color logo", "Fan cover", "Shelve color"]

    codes = "".join(_get_code(data.get(k, "")) for k in order if _get_code(data.get(k, "")) != "")
    e = {"mtime": mtime, "data": data, "codes": codes, "path": path}
    CSV_CACHE[key] = e
    return e

@CreateProgram.get("/programs/<path:filename>")
def download_program(filename):
    return send_from_directory(PROGRAMS_DIR, filename, as_attachment=True)

@CreateProgram.route("/create_program", methods=["GET", "POST"])
def page_create_program():
    tests = load_tests()
    if request.method == "POST":
        sku = request.form.get("sku", "").strip()
    
        # S1 fields to S1.csv
        ModelName = request.form.get("ModelName", "").strip()
        front_logo = request.form.get("front_logo", "").strip()
        display_logo = request.form.get("display_logo", "").strip()
        color = request.form.get("color", "").strip()
        data_logo = request.form.get("data_logo", "").strip()
        inverter_logo = request.form.get("inverter_logo", "").strip()
        power_logo = request.form.get("power_logo", "").strip()

        # S2 fields to S2.csv
        eva_cover = request.form.get("eva_cover", "").strip()
        drawer_printing = request.form.get("drawer_printing", "").strip()
        color_logo = request.form.get("color_logo", "").strip()
        fan_cover = request.form.get("fan_cover", "").strip()
        shelve_color = request.form.get("shelve_color", "").strip()

        errors = []
        if not sku:
            errors.append("SKU is required.")
        required = [
            ("Model Name", ModelName),
            ("Front Logo", front_logo), ("Display logo", display_logo),
            ("Color", color), ("Data logo", data_logo),
            ("Inverter logo", inverter_logo), ("Power logo", power_logo),
            ("Eva cover", eva_cover), ("Drawer printing", drawer_printing),
            ("Color logo", color_logo), ("Fan cover", fan_cover),
            ("Shelve color", shelve_color),
        ]
        for label, val in required:
            if not val:
                errors.append(f"{label} is required.")

        if errors:
            return render_template(
                "CREATE_PROGRAM_HTML.html", errors=errors, submitted=False, sku=sku,
                ModelName=ModelName, front_logo=front_logo, display_logo=display_logo,
                color=color, data_logo=data_logo, inverter_logo=inverter_logo,
                power_logo=power_logo, eva_cover=eva_cover, drawer_printing=drawer_printing,
                color_logo=color_logo, fan_cover=fan_cover, shelve_color=shelve_color,
                tests=tests
            )

        safe_sku = re.sub(r'[^\w\-]', '', sku)
        filename_s1 = f"{safe_sku}S1.csv"
        filename_s2 = f"{safe_sku}S2.csv"
        path_s1 = os.path.join(PROGRAMS_DIR, filename_s1)
        path_s2 = os.path.join(PROGRAMS_DIR, filename_s2)

        try:
            _save_csv_file(path_s1, [
                ("Model Name", ModelName),
                ("Front Logo", front_logo),
                ("Display logo", display_logo),
                ("Color", color),
                ("Data logo", data_logo),
                ("Inverter logo", inverter_logo),
                ("Power logo", power_logo),
            ])
            save_success_s1 = f"S1 saved: {filename_s1}"
            #tcp_server._log_add("INFO", f"Saved {filename_s1}")
        except Exception as e:
            save_success_s1 = None
            #tcp_server._log_add("ERROR", f"Failed saving {filename_s1}: {e}")

        try:
            _save_csv_file(path_s2, [
                ("Model Name", ModelName),
                ("Eva cover", eva_cover),
                ("Drawer printing", drawer_printing),
                ("Color logo", color_logo),
                ("Fan cover", fan_cover),
                ("Shelve color", shelve_color),
            ])
            save_success_s2 = f"S2 saved: {filename_s2}"
            #tcp_server._log_add("INFO", f"Saved {filename_s2}")
        except Exception as e:
            save_success_s2 = None
            #tcp_server._log_add("ERROR", f"Failed saving {filename_s2}: {e}")

        # ===============================
        # handle all dynamic tests (fixed + new)
        # ===============================
        for test in tests:
            print("=== TESTS FROM JSON ===", tests)

            station = test.get("station", "").upper()
            test_name = test.get("name", "")
            field_key = test_name.replace(" ", "_")
            selected_value = request.form.get(field_key)
            if not selected_value:
                continue

            parts = selected_value.split("|", 1)
            if len(parts) == 2:
                opt_name, opt_code = parts
            else:
                opt_name, opt_code = parts[0], ""
            target_path = path_s1 if station == "S1" else path_s2
            row = (test_name, f"{opt_name}|{opt_code}" if opt_code else opt_name)

            try:
                _save_csv_file(target_path, [row], append=True)
                #tcp_server._log_add("INFO", f"Saved {test_name} ({opt_name}, {opt_code}) to {target_path}"  )
            except Exception as e:
                    print("fdfsdf")
                    #tcp_server._log_add("ERROR", f"Failed saving {test_name}: {e}")
       # ===============================
        #CSV_CACHE.pop((sku, "S1"), None)
       # CSV_CACHE.pop((sku, "S2"), None)

        return render_template(
            "CREATE_PROGRAM_HTML.html",
            submitted=True,
            sku=sku,
            ModelName=ModelName,
            front_logo=front_logo, display_logo=display_logo, color=color,
            data_logo=data_logo, inverter_logo=inverter_logo, power_logo=power_logo,
            eva_cover=eva_cover, drawer_printing=drawer_printing,
            color_logo=color_logo, fan_cover=fan_cover, shelve_color=shelve_color,
            save_success_s1=save_success_s1, save_success_s2=save_success_s2,
            filename_s1=filename_s1, filename_s2=filename_s2, tests=tests
        )

    return render_template("CREATE_PROGRAM_HTML.html", submitted=False, errors=None, tests=tests)