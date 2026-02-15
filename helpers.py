import csv 
import os,re,json
from typing import List,Tuple,Dict
import threading
import pandas as pd
import ClientsClass

#Globals
CSV_CACHE: Dict[Tuple[str, str], Dict] = {}
CSV_CACHE_MAX = 256
conn_str_db1_global = None
conn_str_db2_global = None
TIME_SETTINGS = {
    'deviceConnectTimeout': 5.0,
    'deviceRecvTimeout': 1.0,
    'clientSocketTimeout': 1.0,
    'reconnectBaseDelay': 0.5,
    'maxBackoff': 30,
    'reconnectCheckInterval': 1,
    'defaultCharDelay': 100,
    's1CharDelay': 100,
    's2CharDelay': 100,
    'frameDelay': 1,
    'followupDelay': 30,
    'statusRefresh': 1500,
    'logPolling': 800,
    'server4Refresh': 2000,
    'sendTimeout': 25,
    'autoSendGap': 120,
    'dbTimeout': 10,
    'ImageTimeout':10, 
    'PlcSignal' : 0.1
}
STATION1_FILE ="Station1.csv"
STATION2_FILE ="Station2.csv"
STATION2_dummies_FILE ="Station2_dummies.csv"





last_dummy_number = None
last_dummy_number2 = None
last_product_number = None
last_product_number2 = None
last_received_data = "No data received yet"

# SQL Connection specific variables
last_raw_data = "No data received yet"
last_raw_data2 = "No data received yet"
last_dummy_extracted = "No dummy extracted yet"
last_dummy_extracted2 = "No dummy extracted yet"
last_db_status = "No database operation yet"
last_db_status2 = "No database operation yet"
first_10_digits ="NO DUMMY EXTRACTED YET"
#FOR checing the new image 
image_SN1 = None
last_image_SN1 = None
image_SN2 = None
last_image_SN2 = None

# Add image counters to detect changes
image_counter_SN1 = 0
image_counter_SN2 = 0

#station2 failure indication
Station2_failure = False
#Errors Flags 
NO_CSV_ERROR = False
Manual_Scanner_MODE =False

















#-----------------Time settings file---------------
TIME_SETTINGS_FILE = "time_settings.json"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROGRAMS_DIR = BASE_DIR
CSV_SOURCE_DIR = os.path.join(PROGRAMS_DIR, "CreateProgram")
TESTS_FILE = "tests.json"
#-----------------check if Statin1.csv exist---------------
if not os.path.exists(STATION1_FILE):
    with open(STATION1_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["DummyNumber", "TestName", "Result"])

#-----------------check if Statin2.csv exist---------------
if not os.path.exists(STATION2_FILE):
    with open(STATION2_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["DummyNumber", "TestName", "Result"])
#-----------------check if Statin2_dummies.csv exist---------------
if not os.path.exists(STATION2_dummies_FILE):
    with open(STATION2_dummies_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["DummyNumber" , "StationResult"])

# -------------------- LOG FUNCTION --------------------
def tcp_log_print(msg):
    print(msg, flush=True)
    
#jason file for tests
def load_tests():
    if not os.path.exists(TESTS_FILE):
        return []
    with open(TESTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tests(tests):
    with open(TESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(tests, f, ensure_ascii=False, indent=2)
#get the path
def _csv_path(sku: str, part: str) -> str:
    safe_sku = re.sub(r'[^\w\-]', '', sku or "")
    return os.path.join(PROGRAMS_DIR, f"{safe_sku}{part}.csv")
#save the data of sku in csv 
def _save_csv_file(path: str, rows: List[Tuple[str, str]]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Label", "Value"])
        for k, v in rows:
            w.writerow([k, v])
    
#-------------------Insert received data in csv-----------
def insert_csv_station1(Dummy, Test, Res):
    with open("Station1.csv", mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([Dummy, Test, Res])


def insert_csv_station2(dummy, test, res):
    with open("Station2.csv", mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([dummy, test, res])


def delete_row_if_contains(file_path, target_element):
    rows_to_keep = []
    
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if not row:
                continue
            
            # لو العنصر مش موجود في أي مكان في الصف، هنحتفظ بيه
            if target_element not in row:
                rows_to_keep.append(row)

    with open(file_path, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows_to_keep)

def insert_csv_station2_dummies(dummy, StationRes):
    with open("Station2_dummies.csv", mode='a', newline='', encoding='utf-8') as file:
        
        

        delete_row_if_contains("Station2_dummies.csv", dummy )
        writer = csv.writer(file)
        writer.writerow([dummy, StationRes])
#-------------------Clear CSV when new dummy starts-----------
def clear_station1_csv_for_new_dummy(new_dummy):
    """
    """#Clear Station1.csv and start fresh for new dummy
    """
    global current_processing_dummy_station1
    
    # Only clear if it's a different dummy
    if current_processing_dummy_station1 != new_dummy:
        current_processing_dummy_station1 = new_dummy
        
        # Clear the file and write header
        with open(STATION1_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["DummyNumber", "TestName", "Result"])
        
        """
    pass


def clear_station2_csv_for_new_dummy(new_dummy):
    pass
    '''
    """Clear Station2.csv and start fresh for new dummy"""
    global current_processing_dummy_station2
    
    # Only clear if it's a different dummy
    if current_processing_dummy_station2 != new_dummy:
        current_processing_dummy_station2 = new_dummy
        
        # Clear the file and write header
        with open(STATION2_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["DummyNumber", "TestName", "Result"])
    '''

def _load_csv_file(path: str) -> Dict[str, str]:
    out = {}
    with open(path, "r", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r, None)
        for row in r:
            if len(row) == 2:
                out[row[0]] = row[1]
    return out

def auto_send_codes(codes: str, filename: str, csv_data: Dict[str, str], part: str, server_instance):
    """Automatically send loaded codes to appropriate server"""
    try:
        if not codes:
            server_instance._log_add("WARNING", "No codes to send automatically")
            return False
            
        server_instance._log_add("INFO", f"Auto-sending codes: {codes}")
        
        task = {
            "message": codes,
            "target": "combined",
            "encoding": "utf-8",
            "char_delay_ms": TIME_SETTINGS['s1CharDelay'] if part == "S1" else TIME_SETTINGS['s2CharDelay'],
            "retries": 1,
            "program_part": part,
            "program_label": filename,
            "program_data": csv_data,
            "event": threading.Event(),
            "result": None
        }
        
        server_instance._send_queue.put(task)
        
        if task["event"].wait(timeout=TIME_SETTINGS['sendTimeout']):
            result = task.get("result")
            if result and result.get("ok"):
                server_instance._log_add("INFO", f"Auto-send successful: {codes}")
                return True
            else:
                error_msg = result.get("msg", "Unknown error") if result else "No result"
                server_instance._log_add("ERROR", f"Auto-send failed: {error_msg}")
                return False
        else:
            server_instance._log_add("ERROR", "Auto-send timed out")
            return False
            
    except Exception as e:
        server_instance._log_add("ERROR", f"Error in auto_send_codes: {e}")
        return False

def _get_code(val: str) -> str:
    """Extract code from 'Label|Code' format"""
    if not val:
        return ""
    parts = str(val).split("|", 1)
    return parts[1].strip() if len(parts) == 2 else ""



    """Automatically load CSV file based on ProductNumber"""
    try:
        if not product_number:
            server_instance._log_add("ERROR", "No ProductNumber provided for CSV auto-load")
            return False
            
        safe_product = re.sub(r'[^\w\-]', '', product_number or "")
        if not safe_product:
            server_instance._log_add("ERROR", f"Invalid ProductNumber: {product_number}")
            return False
            
        if part not in ["S1", "S2"]:
            server_instance._log_add("INFO", f"Auto-load only supports S1/S2, not {part}")
            return False
            
        filename = f"{safe_product}{part}.csv"
        csv_path = os.path.join(PROGRAMS_DIR, filename)
        
        server_instance._log_add("INFO", f"Looking for CSV file: {filename}")
        
        if not os.path.isfile(csv_path):
            server_instance._log_add("WARNING", f"CSV file not found: {filename}")
            return False
            
        csv_data = _load_csv_file(csv_path)
        
        if part == "S1":
            order = ["Front Logo", "Color", "Data logo", "Inverter logo", "Power logo"]
        else:
            order = ["Eva cover", "Drawer printing", "Color logo", "Fan cover", "Shelve color"]
            
        codes = "".join(_get_code(csv_data.get(k, "")) for k in order if _get_code(csv_data.get(k, "")) != "")
        
        server_instance.current_program_label = filename
        server_instance.current_program_data = csv_data
        
        server_instance._log_add("AUTO_LOAD", f"PRODUCT_NUMBER_CSV_LOADED_{part}: {filename} {codes}")
        server_instance._log_add("INFO", f"Auto-loaded program: {filename} with codes: {codes}")
        
        auto_send_codes(codes, filename, csv_data, part, server_instance)
        return codes
        
    except Exception as e:
        server_instance._log_add("ERROR", f"Error in auto_load_csv_by_product_number: {e}")
        return False
    




def _failure_mode_station2_check(target_dummy=None , Client= None):
    
    """
    Check if Station2 failed for the given dummy.
    Returns: True if failed, False otherwise
    """
    try:
        # Read the Station2 dummies CSV
        station2_dummies_data = pd.read_csv(STATION2_dummies_FILE)
        
        if station2_dummies_data.empty:
            return False
        
        # Filter for the specific dummy
        if target_dummy:
            dummy_row = station2_dummies_data[
                station2_dummies_data['DummyNumber'] == target_dummy
            ]
            
            if dummy_row.empty:
                return False
            
            # Check the result column (assuming it's 'StationResult')
            result = dummy_row.iloc[0]['StationResult']
            
            return result 
        
        return False
        
    except Exception as e:
        Client._log_add("ERROR", f"Error checking Station2 failure: {e}")
        return False
    #عايزة اعمل او بين الريزيلتس لو واحدة فيهم pass يبقى pass 