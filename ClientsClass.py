import socket
import threading
import time
import queue
import pyodbc
import os
import db
import helpers as hlb
import re
from typing import Dict
import textwrap 
from queue import Empty
import Manual
from flask import url_for, Flask



global queue_manual
global queue_manual2 
global NO_CSV_ERROR
NO_CSV_ERROR = False
global NO_CSV_ERROR2
NO_CSV_ERROR2 = False
global Buzzer_Flag_to_OFF
global Buzzer_Flag_to_OFF2
global is_waiting
global Manual_Scanner_MODE, Manual_Scanner_MODE2
Manual_Scanner_MODE = False
Manual_Scanner_MODE2 = False
is_waiting = True
is_waiting2 = True


Buzzer_Flag_to_OFF = False
#Scanner_IP & Port
Ip_Scanner1 = "192.168.1.16"  #"192.168.1.16"
Port_Scanner1 = 7940         #7940
Ip_Scanner2 = "192.168.1.17"   #"192.168.1.17"
Port_Scanner2 = 7950         #7950

#Vision Master_IP & Port
Ip_vision_inner = "127.0.0.1"
Port_vision_inner = 30
Ip_vision_outer = "127.0.0.1"
Port_vision_outer = 20

Ip_vision_inner_SN = "127.0.0.1"
Port_vision_inner_SN = 50
Ip_vision_outer_SN = "127.0.0.1"
Port_vision_outer_SN = 40

#I/O Module_IP & Port
Ip_read_IO = "192.168.1.30"#"192.168.1.30"
Port_read_IO = 502
Ip_write_IO = "192.168.1.30"#"192.168.1.30"
Port_write_IO = 502

#I/O commands
#Read
CMD_READ_DI0=               "000300000006010200000001"                      #Read DI0 in I/O Module
CMD_READ_DI1=               "000400000006010200010001"                      #Read DI1 in I/O Module
CMD_Read_Inputs=            "000300000006010300220001"                      #the commaned needed to read registers 


#write single output ON
ON_LIGHTING_S1 =            "00010000000601050008FF00" #D0 ON
ON_LIGHTING_S2   =            "00010000000601050001FF00" #D1 ON 
ON_BUZZER_S1   =            "00010000000601050002FF00" #D2 ON
ON_BUZZER_S2 =            "00010000000601050003FF00" #D3 ON
ON_SCANNER_S1  =            "00010000000601050004FF00" #D4 ON
ON_SCANNER_S2  =            "00010000000601050005FF00" #D5 ON
ON_TESTDONE_S1 =            "00010000000601050006FF00" #D6 ON
ON_TESTDONE_S2 =            "00010000000601050007FF00" #D7 ON
ON_FAILURE     =            "00010000000601050008FF00" #D8 ON
#WRITE SINGLE OUTPUT OFF
OFF_LIGHTING_S1 =            "000100000006010500080000" #D0 OFF
OFF_BUZZER_S2   =            "000100000006010500010000" #D1 OFF
OFF_BUZZER_S1   =            "000100000006010500020000" #D2 OFF
OFF_LIGHTING_S2 =            "000100000006010500030000" #D3 OFF
OFF_SCANNER_S1  =            "000100000006010500040000" #D4 OFF
OFF_SCANNER_S2  =            "000100000006010500050000" #D5 OFF
OFF_TESTDONE_S1 =            "000100000006010500060000" #D6 OFF
OFF_TESTDONE_S2 =            "000100000006010500070000" #D7 OFF
OFF_FAILURE     =            "000100000006010500080000" #D8 OFF
CMD_OFF_ALL=                "000100000009010F00000010020000"                # all bins off 
'''
#Write
CMD_WRITE_ALL=              "000100000009010F00000010020000"                #Turn all the outputs OFF 
CMD_COMBINED_FIRST_S1 =     "000100000009010F00000010020100"                #DO0 lighting station outer control RELAY1
CMD_COMBINED_FIRST_S2 =     "000100000009010F00000010020200"                #DO1 buzzer station inner control  RELAY2
CMD_IMMEDIATE=              "000100000009010F00000010020400"                #DO2 Buzzer station outer control RELAY3
CMD_IMMEDIATE_OK=           "000100000009010F00000010020800"                #DO3 lighting inner contrtol RELAY 4
#Write to trig the Scanner
CMD_SCANNER_S1=             "000100000009010F00000010021000"                #DO4 SCANNER STATION OUTER CONTROL 
CMD_SCANNER_S2=             "000100000009010F00000010022000"                #DO5 SCANNER STATION inner CONTROL 
#Write Test Done
CMD_TestDone_S1=            "000100000009010F00000010024000"                #DO6 test done feedback STATION OUTER CONTROL 
CMD_TestDone_S2=            "000100000009010F00000010028000"                #DO7 test done feedback STATION inner CONTROL 

CMD_Feedback_PLC=           "000100000009010F00000010020001"                #DO8 feedback CONTROL 
CMD_ACTION_S1=              "000100000009010F00000010021100"                #DO0 & DO4  0001 0001 0000 0000
CMD_ACTION_S2=              "000100000009010F00000010028800"                #DO3 & DO7  1000 1000 0000 0000
CMD_Failure_Action=         "000100000009010F00000010024001"                #testdone signal & feedback

CMD_OFF_ALL=                "000100000009010F00000010020000"                # all bins off 
'''
last_product_number=0
current_dummy_station_one=0
waiting_for_station_one_result=0
dummy_number=0
last_raw_data1=0
last_dummy_number=0

last_product_number2=0
current_dummy_station_two=0
waiting_for_station_two_result=0
dummy_number=0
last_raw_data2=0
last_dummy_number2=0

image_SN1=0
image_SN2= 0

received_tests_station1 = set()
received_tests_station2 = set()
'''
test_results_dict = {}
zero_values_list  = []
'''
# Thread-safe lock for database operations
db_lock = threading.Lock()


queue_manual_FOR_FAILURE  = queue.Queue()
queue_manual_FOR_Proessing  = queue.Queue()
queue_manual2_FOR_FAILURE  = queue.Queue()
queue_manual2_FOR_Proessing = queue.Queue()
#functions 
# ---------------- Auto-load CSV by ProductNumber ----------------
def auto_load_csv_by_product_number(product_number: str, part: str, server_instance , queue: queue): # server_instance = client intense
    """Automatically load CSV file based on ProductNumber"""
    global NO_CSV_ERROR, NO_CSV_ERROR2,Buzzer_Flag_to_OFF
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
        csv_path  = os.path.join(hlb.PROGRAMS_DIR, "CreateProgram", filename)
       

        
        server_instance._log_add("INFO", f"Looking for CSV file: {filename}")
        
        while not os.path.isfile(csv_path):
            server_instance._log_add("WARNING", f"CSV file not found: {filename}")
            if part == "S1":
                NO_CSV_ERROR = True
            elif part == "S2":
                NO_CSV_ERROR2 = True

            server = TCPClient(Ip_write_IO, Port_write_IO )
            if part == "S1":
                server.send_request(ON_BUZZER_S1,is_hex=True)
                
            if part == "S2":
               server.send_request(ON_BUZZER_S2,is_hex=True)
            while True:
                if Buzzer_Flag_to_OFF:
                    if part == "S1":
                        server.send_request(OFF_BUZZER_S1,is_hex=True)
                
                    if part == "S2":
                        server.send_request(OFF_BUZZER_S2,is_hex=True)
                    Buzzer_Flag_to_OFF = False
                    break
            time.sleep(120)
        csv_data = hlb._load_csv_file(csv_path)
        
        if part == "S1":
            order = ["Color", "Data logo", "Inverter logo", "Power logo","Front Logo"]
        else:
            order = ["Eva cover", "Drawer printing", "Color logo", "Fan cover", "Shelve color"]
            
        codes = "".join(_get_code(csv_data.get(k, "")) for k in order if _get_code(csv_data.get(k, "")) != "")
        
        server_instance.current_program_label = filename
        server_instance.current_program_data = csv_data
        
        server_instance._log_add("AUTO_LOAD", f"PRODUCT_NUMBER_CSV_LOADED_{part}: {filename} {codes}")
        server_instance._log_add("INFO", f"Auto-loaded program: {filename} with codes: {codes}")
        #codes= textwrap.wrap(codes, width=2)
        queue.put(codes)
        auto_send_codes(codes, filename, csv_data, part, server_instance)
        return codes
    except Exception as e:
        server_instance._log_add("ERROR", f"Error in auto_load_csv_by_product_number: {e}")
    

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

def auto_send_codes(codes: list, filename: str, csv_data: Dict[str, str], part: str, server_instance):
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
            "char_delay_ms": hlb.TIME_SETTINGS['s1CharDelay'] if part == "S1" else hlb.TIME_SETTINGS['s2CharDelay'],
            "retries": 1,
            "program_part": part,
            "program_label": filename,
            "program_data": csv_data,
            "event": threading.Event(),
            "result": None
        }
        
        #server_instance.send_request(task["message"])
        
        if task["event"].wait(timeout=hlb.TIME_SETTINGS['sendTimeout']):
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


'''
def clients_forward():
                try:
                    if is_from_csv:
                        self._log_add("INFO", f"CSV delay: 500ms")
                        time.sleep(0.5)
                    
                    if encoding == "hex":
                        blob = parse_hex(message)
                        results["clients"] = self.send_to_all(blob)
                        client_outcome["ok"] = any(v.get("ok") for v in results["clients"].values())
                        save_to_result_files(program_label, f"HEX_SENT: {message}", program_data)
                    else:
                        with self._clients_lock:
                            ids = list(self.clients.keys())
                        per_client_results = {cid: [] for cid in ids}
                        for i in range(0, len(message), 2):
                            pair = message[i:i + 2]
                            data = pair.encode("utf-8", errors="ignore")
                            for cid in ids:
                                ok, msg = self.send_to_client(cid, data)
                                per_client_results[cid].append({"ok": ok, "msg": msg, "chunk": pair})
                            time.sleep(delay / 1000.0)
                        results["clients"] = per_client_results
                        client_outcome["ok"] = any(any(item["ok"] for item in arr) for arr in per_client_results.values())
                        save_to_result_files(program_label, f"TEXT_SENT: {message}", program_data)
                except Exception as e:
                    client_outcome["ok"] = False
                    self._log_add("ERROR", f"Client forward error: {e}")

'''


















# General Class
class  TCPClient():
    def __init__(self, ip, port, timeout=None, buffer_size=4096):
        """
        :param timeout: لو خليته None هيفضل مستني للأبد لحد ما السيرفر يرد
        """
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.buffer_size = buffer_size
        self.sock = None  # هنا هنحتفظ بالسوكيت عشان يفضل مفتوح
        self.connected = False
        self._send_queue: "queue.Queue[dict]" = queue.Queue()
        self._log_lock = threading.Lock()
        self._log_seq = 0
        self._log = list()
        self.name =""
        self.current_program_label =""
        self.current_program_data=""

        self.shared_queue = queue.Queue()
        self.shared_queue2= queue.Queue() #FOR DUMMY shared between scanner and data proccesing function 
        self.shared_queue3= queue.Queue() # for dummies shared between scanner and i/o writer function

    def connect(self):
        """دالة لفتح الاتصال مرة واحدة"""
        try:
            if self.connected:
                print(f"[{self.ip}] Already connected.")
                return True
            
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout) # تحديد وقت الانتظار (أو None للانتظار الدائم)
            self.sock.connect((self.ip, self.port))
            self.connected = True
            print(f"[{self.ip}] : [{self.port}] Connected successfully.")
            return True
        except Exception as e:
            print(f"[{self.ip}] : [{self.port}] Connection Failed: {e}")
            self.connected = False
            return False
            
    def ensure_connected(self):
        """تتأكد إننا متصلين، ولو مش متصلين تحاول للأبد"""
        while not self.connected:
            self._log_add("INFO", f"Trying to reconnect to {self.ip}...")
            if self.connect():
                self._log_add("INFO", "✅ Reconnected successfully!")
                break
            else:
                self._log_add("WARNING", "❌ Retrying in 5 seconds...")
                time.sleep(5)    
    
    def start_reconnection_watchdog(self):
        """تشغيل خيط المراقبة في الخلفية"""
        thread = threading.Thread(target=self._connection_monitor, daemon=True)
        thread.start()

    def _connection_monitor(self):
        """الدالة اللي بتراقب الاتصال كل كام ثانية"""
        while True:
            if not self.connected:
                # لو لقيناه فصل، نصلحه
                self.ensure_connected()
            else:
                # لو متصل، نتأكد إنه "فعلاً" لسه شغال
                try:
                    # محاولة إرسال بايت فارغ للتأكد من الـ Socket
                    # MSG_PEEK بتشوف الداتا من غير ما تسحبها، أو ابعت حرف تافه لو السيرفر بيسمح
                    self.sock.send(b'', socket.MSG_OOB) 
                except Exception:
                    self._log_add("WARNING", "⚠️ Connection lost in background!")
                    self.connected = False
            
            time.sleep(3) # افحص كل 3 ثواني
    
    def _get_sock(self):
         
        local_ip, local_port = self.sock.getsockname()
        return local_ip,local_port
   
    def send_request(self, message , is_hex=False):
        """
        إرسال واستقبال فقط (بدون إغلاق الاتصال)
        """
        if not self.connected or self.sock is None:
            print(f"[{self.ip}]:[{self.port}] Error: Not connected! Trying to connect...")
            self.ensure_connected()
           

        try:
            # 1. تجهيز الرسالة
            data_to_send = None
            if isinstance(message, bytes):
                data_to_send = message
            elif is_hex:
                data_to_send = bytes.fromhex(message)
            else:
                data_to_send = message.encode('utf-8')
                #data_to_send = [chunk.encode('utf-8') for chunk in message]

            # 2. الإرسال
           
            self.sock.sendall(data_to_send)

            # 3. الاستقبال (هنا هيفضل مستني لحد ما السيرفر يرد)
            # طالما timeout=None أو وقت كبير، هيفضل واقف هنا (Blocking)
            response = self.sock.recv(self.buffer_size)

            return  response

        except (socket.timeout):
            print(f"[{self.ip}]:[{self.port}] Timeout: Server took too long to respond.")
            return None

        except (OSError, BrokenPipeError, ConnectionResetError, socket.error) as e:
            # ⚠️ هنا أهم تعديل: لو حصل أي خطأ في السوكيت (السيرفر قفل أو السلك اتشال)
            print(f"[{self.ip}]:[{self.port}] Connection Lost ({e}). Reconnecting...")
            
            self.connected = False
            if self.sock:
                try:
                    self.sock.close()
                except:
                    pass
                self.sock = None
            
            # محاولة إعادة الاتصال فوراً
            self.ensure_connected()
            
            # اختياري: ممكن تخليها تحاول تبعت الرسالة تاني بعد ما رجع الاتصال
            # return self.send_request(message, is_hex) 
            return None

        except Exception as e:
            print(f"[{self.ip}]:[{self.port}] General Error: {e}")
            return None
    
    '''
    def _start_monitoring(self):
        """بدء خيط المراقبة"""
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._stop_monitor.clear()
            self._monitor_thread = threading.Thread(target=self._monitor_connections, daemon=True)
            self._monitor_thread.start()

    def _monitor_connections(self):
        """فانكشن المراقبة اللي بتشيك على حالة الاتصال كل فترة"""
        print(f"[{self.ip}] Connection monitor started.")
        while not self._stop_monitor.is_set():
            if self.connected and self.sock:
                try:
                    # بنبعث "بيانات فارغة" عشان نختبر لو السوكيت لسه شغال (Keep-alive check)
                    # MSG_PEEK بيشوف البيانات من غير ما يسحبها من البافر
                    self.sock.send(b"", socket.MSG_DONTWAIT)
                except (OSError, BrokenPipeError):
                    print(f"[{self.ip}] Monitor detected broken connection!")
                    self.connected = False
                    # هنا ممكن تختار تنادي self.connect() تاني لو عايز Auto-reconnect
                    break
            time.sleep(5)  # شيك كل 5 ثواني مثلاً
     
   '''
    
    def disconnect(self):
        """إغلاق الاتصال وإيقاف المونيتور"""
        self._stop_monitor.set() # وقف اللوب في المونيتور
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.sock = None
        self.connected = False
        print(f"[{self.ip}] Connection Closed.")

    def _log_add(self, level: str, msg: str):
        with self._log_lock:
            self._log_seq += 1
            self._log.append((self._log_seq, time.time(), level, msg))
            if len(self._log) > 5000:
                self._log = self._log[-3000:]
        print(f"[{self.name}][{level}] {msg}")
    
    def start_listening(self, callback=None):
        """
        دالة لبدء عملية الاستماع في Thread منفصل
        :param callback: دالة اختيارية يتم استدعاؤها فور استلام بيانات
        """
        self.receive_queue = queue.Queue() # كيو لاستقبال البيانات
        self.listen_thread = threading.Thread(target=self._listen_loop, args=(callback,), daemon=True)
        self.listen_thread.start()
        self._log_add("INFO", f"[{self.ip}] : [{self.port}] Started listening for incoming data...")
        

    def _listen_loop(self, callback):
        """الـ Loop الداخلي اللي بيفضل مستني داتا"""
        while self.connected:
            try:
                # الكود هيفضل واقف هنا لحد ما السيرفر يبعت حاجة
                data = self.sock.recv(self.buffer_size)
                
                if not data:
                    # لو السيرفر بعت داتا فاضية معناها قفل الاتصال
                    print(f"[{self.ip}] Server closed the connection.")
                    self.connected = False
                    break
                
                if callback:
                    callback(data)
                # إضافة البيانات للكيو
                #self.receive_queue.put(data)

                # اختياري: تسجيل اللوج
                # self._log_add("INFO", f"Received data: {data}")

            except socket.timeout:
                continue # لو حصل تايم أوت يرجع يحاول يستقبل تاني
            except Exception as e:
                if self.connected:
                    print(f"[{self.ip}] Listening Error: {e}")
                    self.connected = False
                break

    def get_last_received(self, block=False, timeout=None):
        """دالة لسحب آخر داتا وصلت من الكيو"""
        try:
            return self.receive_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None


##################################################################
class App():
    def __init__(self):
        
        #Scanner
        self.client_scanner_station1 = TCPClient(Ip_Scanner1, Port_Scanner1 )
        self.client_scanner_station2 = TCPClient(Ip_Scanner2, Port_Scanner2 )
           
        #Vision master
        self.client_Vision_station1 = TCPClient( Ip_vision_outer, Port_vision_outer)
        self.client_Vision_station2 = TCPClient(Ip_vision_inner, Port_vision_inner )

        self.client_Vision_station1_SN = TCPClient( Ip_vision_outer_SN, Port_vision_outer_SN)
        self.client_Vision_station2_SN = TCPClient(Ip_vision_inner_SN, Port_vision_inner_SN )
        
        """Handles data from vision master systems (ports 20, 30)"""
        self.station_one_data = {"raw": "", "dummy": "", "product": "", "db_status": ""}
        self.station_two_data = {"raw": "", "dummy": "", "product": "", "db_status": ""}
        
        
        self.lock = threading.Lock()
        
        # timestamps for each dummy
        self.last_dummy_time_station_one = {}  # dict {dummy_number: timestamp}
        self.last_dummy_time_station_two = {}

        #I/O Moudule
        self.client_read_io = TCPClient(Ip_read_IO, Port_read_IO )
        self.client_write_io = TCPClient(Ip_write_IO, Port_write_IO )

        #auto connnect with data base
        #self.auto_connect_db()
        #db.auto_connect_db()

        #self.test_results_dict = dict()

    def Start_connetion(self):
        
        """تفريغ كافة الـ Queues لضمان بداية نظيفة"""
        queues_to_clear = [
            self.client_scanner_station1.shared_queue,
            self.client_scanner_station1.shared_queue2,
            self.client_scanner_station2.shared_queue,
            self.client_scanner_station2.shared_queue2,
            self.client_Vision_station1.shared_queue,
            self.client_Vision_station2.shared_queue,
            queue_manual_FOR_FAILURE,
            queue_manual_FOR_Proessing,
            queue_manual2_FOR_FAILURE,
            queue_manual2_FOR_Proessing
        ]

        for q in queues_to_clear:
            with q.mutex: # حماية العملية لضمان عدم حدوث تداخل
                q.queue.clear() # طريقة سريعة لمسح محتويات الكيو داخلياً
                q.all_tasks_done.notify_all() # إبلاغ أي Thread منتظر بأن المهام انتهت
                q.unfinished_tasks = 0
            
        # 1. قائمة بكل الكلاينتس اللي عندك
        all_clients = [
            self.client_scanner_station1, self.client_scanner_station2,
            self.client_Vision_station1, self.client_Vision_station2,
            self.client_read_io, self.client_write_io
        ]
        # 2. قفل أولي لكل السوكيتات لضمان بداية نظيفة
        print("Performing initial hard-reset on all sockets...")
        for client in all_clients:
            try:
                if client.sock:
                    client.sock.close()
                client.connected = False
                client.sock = None
            except:
                pass

        self.client_scanner_station1.start_reconnection_watchdog()
        self.client_read_io.start_reconnection_watchdog()
        
        self.client_write_io.start_reconnection_watchdog()
        self.client_Vision_station1.start_reconnection_watchdog()
        self.client_Vision_station2.start_reconnection_watchdog()
        self.client_scanner_station2.start_reconnection_watchdog()  
        self.client_Vision_station1_SN.start_reconnection_watchdog()
        self.client_Vision_station2_SN.start_reconnection_watchdog()
        
        self.client_scanner_station1.start_listening(self._scanner_station_1)
        self.client_scanner_station2.start_listening(self._scanner_station_2)
        self.client_Vision_station1_SN.start_listening(self._SN_Proccess1)
        self.client_Vision_station2_SN.start_listening(self._SN_Proccess2)      

        self.client_write_io.send_request(CMD_OFF_ALL,is_hex=True)


       
        
        
# servers handling
    def _IO_read (self):
        self.client_read_io._log_add("INFO", f"start reading from io")
        last_DI0 = b"\0x00"
        last_DI1 = b"\0x00"
        while self.client_read_io.connected:
            try:

                DI0_respond=self.client_read_io.send_request(message= CMD_READ_DI0, is_hex= True)
                #self.client_read_io._log_add("INFO", f"the io reading [{DI0_respond}]")
                #self.client_read_io._log_add("INFO", f"the io reading [{DI0_respond[-1:]}]")
                #self.client_read_io._log_add("INFO", f"[{ DI0_respond [-1:]== b"\x01" and  last_DI0 == b"\x00"}]" )
                if DI0_respond [-1:]== b"\x01" and  last_DI0 == b"\x00" :
                     threading.Thread(target =self._IO_Writer_station_1, daemon= True).start()
                     self.client_read_io._log_add("INFO", f"found fridg in station 1")
                last_DI0 = DI0_respond [-1:]
                
                time.sleep(0.01)

                DI1_respond = self.client_read_io.send_request(message= CMD_READ_DI1,is_hex= True)
                if DI1_respond [-1:]== b"\x01" and  last_DI1 == b"\x00":
                    threading.Thread(target =self._IO_Writer_station_2, daemon= True).start()
                    self.client_read_io._log_add("INFO", f"found fridg in station 2")
                last_DI1 = DI1_respond [-1:]
            except:
                self.client_read_io._log_add("INFO", f"زفت")

    def _vision_station_1(self):
        """
        تستقبل نص من الـ Queue، تقسمه حرفين حرفين، وترسله إلى Vision Master 1
        """
        

        while self.client_Vision_station1.connected:
            try:
                message_from_queue = self.client_scanner_station1.shared_queue.get()
                # 1. التأكد أن الرسالة نصية وليست فارغة
                if not message_from_queue:
                    self.client_Vision_station1._log_add("INFO", f"there is no message from queue")
                else:
                    message_list= textwrap.wrap(message_from_queue, width=2)
                    if "00" in message_list:
                        message_list.remove("00")
                    test_results_list = list()
                    for i in range(len(message_list)):
                        self.client_Vision_station1._log_add("INFO", f"Sending to Vision Master 1: {message_list[i]}")
                        test_results_list.append (self.client_Vision_station1.send_request(message_list[i])) 
                    

                    string_test_results_list = list()
                    for i in range(len(test_results_list)):
                        string_test_results_list.append(test_results_list[i].decode("utf-8", errors="ignore"))
                    #self.client_Vision_station1._log_add("INFO", f"Sending to Vision Master 1: [{ test_results_list}]")
                    self.client_scanner_station1.shared_queue.task_done()
                    
                    test_results_dict = {item.split('-')[0]: item.split('-')[1] for item in string_test_results_list}   #convert list to dictinary
                    #zero_values_list = [k for k, v in my_dict.items() if v == "0"]
                    
                    #zero_values_list = [k for k, v in my_dict.items() if v == "0"]
                   
                    self.client_Vision_station1.shared_queue.put(test_results_dict)
                    self.client_Vision_station1._log_add("INFO", f"Sending to Vision Master 2: [{ test_results_dict}]")
                    '''
                    self.client_Vision_station1.shared_queue.put(test_results_dict)
                    
                    TEST = self.client_Vision_station1.shared_queue.get()
                    self.client_Vision_station1._log_add("INFO", f"DATA IN THE Q👌👌😒😒😍😒😒😍🤦‍♀️🙌: [{TEST}]")
                    '''
                    
                    time.sleep(1)
    
                    thread = threading.Thread(target=self.data_processing_station1, daemon= True)
                    thread.start()
                    thread.join()
                    test_results_list.clear()
                    test_results_dict.clear()
            except Exception as e:
                if hasattr(self.client_Vision_station1, '_log_add'):
                    self.client_Vision_station1._log_add("ERROR", f"Error in _vision_station_1: {e}")
                else:
                    print(f"Error in _vision_station_1: {e}")


    def _vision_station_2(self):
        """
        تستقبل نص من الـ Queue، تقسمه حرفين حرفين، وترسله إلى Vision Master 1
        """
        while self.client_Vision_station2.connected:
            try:
                message_from_queue = self.client_scanner_station2.shared_queue.get()
                # 1. التأكد أن الرسالة نصية وليست فارغة
                if not message_from_queue:
                    self.client_Vision_station2._log_add("INFO", f"there is no message from queue")
                else:
                    message_list= textwrap.wrap(message_from_queue, width=2)
                    if "00" in message_list:
                        message_list.remove("00")
                    test_results_list = list()

                   
                   
                    for i in range(len(message_list)):
                        self.client_Vision_station2._log_add("INFO", f"Sending to Vision Master 2: {message_list[i]}")
                        test_results_list.append (self.client_Vision_station2.send_request(message_list[i])) 
                    
                    #string_test_results_list = ''.join(byte.decode() for byte in test_results_list)
                    string_test_results_list = list()
                    for i in range(len(test_results_list)):
                        string_test_results_list.append(test_results_list[i].decode("utf-8", errors="ignore"))
                    
                    
                    
                    self.client_Vision_station2._log_add("INFO", f"Sending to Vision Master 2: [{ string_test_results_list}]")
                    self.client_scanner_station2.shared_queue.task_done()

                    test_results_dict = {item.split('-')[0]: item.split('-')[1] for item in string_test_results_list}   #convert list to dictinary
                    #zero_values_list = [k for k, v in my_dict.items() if v == "0"]
                    self.client_Vision_station2._log_add("INFO", f"Sending to Vision Master 2: [{ test_results_dict}]")


                    self.client_Vision_station2.shared_queue.put(test_results_dict)
                    
                    thread = threading.Thread(target=self.data_processing_station2, daemon= True)
                    thread.start()
                    thread.join()
                    test_results_list.clear()
                    test_results_dict.clear()
                   
                   
            except Exception as e:
                if hasattr(self.client_Vision_station2, '_log_add'):
                    self.client_Vision_station2._log_add("ERROR", f"Error in _vision_station_2: {e}")
                else:
                    print(f"Error in _vision_station_2: {e}")

 
 #finished
    def _scanner_station_1(self, data : bytes):
        """Process data from vision check 1 (port 7940)"""
        global last_product_number, current_dummy_station_one, waiting_for_station_one_result,dummy_number,last_raw_data1,last_dummy_number
        try:
            text = data.decode("utf-8", errors="ignore").strip()
            if len(text) > 14:
                text = text[:14]
            
            with self.lock:
                self.station_two_data["raw"] = text
                last_raw_data2= text
            self.client_scanner_station1._log_add("INFO", f"Vision Station one data: '{text}'")
            
            if text.startswith("R"):
                parts = text.split("-")
                dummy_number = parts[0].strip()
                now2 = time.time()
                
                self.client_scanner_station1.shared_queue2.put(dummy_number)
                self.client_scanner_station1.shared_queue3.put(dummy_number)

                with self.lock:
                     '''
                     last_time2 = self.last_dummy_time_station_two.get(dummy_number, 0)
                     if dummy_number == last_dummy_number2:
                        if now2 - last_time2 <= 60:
                            return
                        else:
                            tcp_server._log_add("WARNING", f"⚠️ Duplicate dummy ignored: {dummy_number}")

                            return 
                    '''
               
                # ✅ CLEAR CSV FOR NEW DUMMY  ← 🆕 NEW LINE
                hlb.clear_station2_csv_for_new_dummy(dummy_number)
          
                self.last_dummy_time_station_one[dummy_number] = now2
                self.station_one_data["dummy"] = dummy_number
                waiting_for_station_one_result = True
                current_dummy_station_one = dummy_number
                received_tests_station1.clear()
                last_dummy_number = dummy_number
                self.client_scanner_station1._log_add("INFO", f"Station : Extracted dummy '{dummy_number}'")
                
                #time.sleep(0.1)  # Prevent DB contention
                
                if db.conn_str_db1_global:
                    with db_lock:
                        try:
                            with pyodbc.connect(db.conn_str_db1_global, timeout=hlb.TIME_SETTINGS['dbTimeout']) as conn:
                                cursor = conn.cursor()
                                cursor.execute(
                                    "SELECT ProductNumber FROM SFCNumbers WHERE LTRIM(RTRIM(Number)) = ?",
                                    (dummy_number,)
                                )
                                row = cursor.fetchone()

                            if row:
                                last_product_number = row[0]
                                status = f"✅ Found ProductNumber: {last_product_number}"
                                with self.lock:
                                    self.station_one_data["product"] = last_product_number
                                    self.station_one_data["db_status"] = status
                                self.client_scanner_station1._log_add("INFO", status)
                                
                                auto_load_csv_by_product_number(last_product_number, "S1", self.client_Vision_station1, self.client_scanner_station1.shared_queue)
                            else:
                                status = f"❌ Dummy '{dummy_number}' not found"
                                with self.lock:
                                    self.station_one_data["db_status"] = status
                                self.client_scanner_station1._log_add("WARNING", status)
                                
                        except Exception as db_ex:
                            status = f"❌ DB query error: {db_ex}"
                            with self.lock:
                                self.station_one_data["db_status"] = status
                            self.client_scanner_station1._log_add("ERROR", status)
                else:
                    with self.lock:
                        self.station_one_data["db_status"] = "❌ No DB connection"
                        
        except Exception as e:
            self.client_scanner_station1._log_add("ERROR", f"Error processing Station Two data: {e}")

    def Manual_scanner_station_1(self, data : bytes):
            """Process data from vision check 1 (port 7940)"""
            global last_product_number, current_dummy_station_one, waiting_for_station_one_result,dummy_number,last_raw_data1,last_dummy_number
            try:
                text = data.decode("utf-8", errors="ignore").strip()
                if len(text) > 14:
                    text = text[:14]
                
                with self.lock:
                    self.station_two_data["raw"] = text
                    last_raw_data2= text
                self.client_scanner_station1._log_add("INFO", f"Vision Station one data: '{text}'")
                
                if text.startswith("R"):
                    parts = text.split("-")
                    dummy_number = parts[0].strip()
                    now2 = time.time()

                    with self.lock:
                        '''
                        last_time2 = self.last_dummy_time_station_two.get(dummy_number, 0)
                        if dummy_number == last_dummy_number2:
                            if now2 - last_time2 <= 60:
                                return
                            else:
                                tcp_server._log_add("WARNING", f"⚠️ Duplicate dummy ignored: {dummy_number}")

                                return 
                        '''
                
                    # ✅ CLEAR CSV FOR NEW DUMMY  ← 🆕 NEW LINE
                    hlb.clear_station2_csv_for_new_dummy(dummy_number)
            
                    self.last_dummy_time_station_one[dummy_number] = now2
                    self.station_one_data["dummy"] = dummy_number
                    waiting_for_station_one_result = True
                    current_dummy_station_one = dummy_number
                    received_tests_station1.clear()
                    last_dummy_number = dummy_number
                    self.client_scanner_station1._log_add("INFO", f"Station : Extracted dummy '{dummy_number}'")
                    
                    #time.sleep(0.1)  # Prevent DB contention
                    
                    if db.conn_str_db1_global:
                        with db_lock:
                            try:
                                with pyodbc.connect(db.conn_str_db1_global, timeout=hlb.TIME_SETTINGS['dbTimeout']) as conn:
                                    cursor = conn.cursor()
                                    cursor.execute(
                                        "SELECT ProductNumber FROM SFCNumbers WHERE LTRIM(RTRIM(Number)) = ?",
                                        (dummy_number,)
                                    )
                                    row = cursor.fetchone()

                                if row:
                                    last_product_number = row[0]
                                    status = f"✅ Found ProductNumber: {last_product_number}"
                                    with self.lock:
                                        self.station_one_data["product"] = last_product_number
                                        self.station_one_data["db_status"] = status
                                    self.client_scanner_station1._log_add("INFO", status)
                                    
                                    auto_load_csv_by_product_number(last_product_number, "S1", self.client_Vision_station1, self.client_scanner_station1.shared_queue)
                                else:
                                    status = f"❌ Dummy '{dummy_number}' not found"
                                    with self.lock:
                                        self.station_one_data["db_status"] = status
                                    self.client_scanner_station1._log_add("WARNING", status)
                                    
                            except Exception as db_ex:
                                status = f"❌ DB query error: {db_ex}"
                                with self.lock:
                                    self.station_one_data["db_status"] = status
                                self.client_scanner_station1._log_add("ERROR", status)
                    else:
                        with self.lock:
                            self.station_one_data["db_status"] = "❌ No DB connection"
                            
            except Exception as e:
                self.client_scanner_station1._log_add("ERROR", f"Error processing Station Two data: {e}")

    def _scanner_station_2(self, data : bytes):
        """Process data from vision check 2 (port 7950)"""
        global last_product_number2, current_dummy_station_two, waiting_for_station_two_result,dummy_number,last_raw_data2,last_dummy_number2
        
        try:
            text = data.decode("utf-8", errors="ignore").strip()
            if len(text) > 14:
                text = text[:14]
            
            with self.lock:
                self.station_two_data["raw"] = text
                last_raw_data2= text
            self.client_scanner_station2._log_add("INFO", f"Vision Station Two data: '{text}'")
            
            if text.startswith("R"):
                parts = text.split("-")
                dummy_number = parts[0].strip()
                now2 = time.time()
                
                self.client_scanner_station2.shared_queue2.put(dummy_number)
                self.client_scanner_station2.shared_queue3.put(dummy_number)

                with self.lock:
                     '''
                     last_time2 = self.last_dummy_time_station_two.get(dummy_number, 0)
                     if dummy_number == last_dummy_number2:
                        if now2 - last_time2 <= 60:
                            return
                        else:
                            tcp_server._log_add("WARNING", f"⚠️ Duplicate dummy ignored: {dummy_number}")

                            return 
                    '''
               
                # ✅ CLEAR CSV FOR NEW DUMMY  ← 🆕 NEW LINE
                hlb.clear_station2_csv_for_new_dummy(dummy_number)
          
                self.last_dummy_time_station_two[dummy_number] = now2
                self.station_two_data["dummy"] = dummy_number
                waiting_for_station_two_result = True
                current_dummy_station_two = dummy_number
                received_tests_station2.clear()
                last_dummy_number2 = dummy_number
                self.client_scanner_station2._log_add("INFO", f"Station Two: Extracted dummy '{dummy_number}'")
                
                #time.sleep(0.1)  # Prevent DB contention
                
                if db.conn_str_db1_global:
                    with db_lock:
                        try:
                            with pyodbc.connect(db.conn_str_db1_global, timeout=hlb.TIME_SETTINGS['dbTimeout']) as conn:
                                cursor = conn.cursor()
                                cursor.execute(
                                    "SELECT ProductNumber FROM SFCNumbers WHERE LTRIM(RTRIM(Number)) = ?",
                                    (dummy_number,)
                                )
                                row = cursor.fetchone()

                            if row:
                                last_product_number2 = row[0]
                                status = f"✅ Found ProductNumber: {last_product_number2}"
                                with self.lock:
                                    self.station_two_data["product"] = last_product_number2
                                    self.station_two_data["db_status"] = status
                                self.client_scanner_station2._log_add("INFO", status)
                                
                                auto_load_csv_by_product_number(last_product_number2, "S2", self.client_Vision_station2, self.client_scanner_station2.shared_queue)
                            else:
                                status = f"❌ Dummy '{dummy_number}' not found"
                                with self.lock:
                                    self.station_two_data["db_status"] = status
                                self.client_scanner_station2._log_add("WARNING", status)
                                
                        except Exception as db_ex:
                            status = f"❌ DB query error: {db_ex}"
                            with self.lock:
                                self.station_two_data["db_status"] = status
                            self.client_scanner_station2._log_add("ERROR", status)
                else:
                    with self.lock:
                        self.station_two_data["db_status"] = "❌ No DB connection"
                        
        except Exception as e:
            self.client_scanner_station2._log_add("ERROR", f"Error processing Station Two data: {e}")

    def Manual_scanner_station_2(self, data : bytes):
            """Process data from vision check 2 (port 7950)"""
            global last_product_number2, current_dummy_station_two, waiting_for_station_two_result,dummy_number,last_raw_data2,last_dummy_number2
            
            try:
                text = data.decode("utf-8", errors="ignore").strip()
                if len(text) > 14:
                    text = text[:14]
                
                with self.lock:
                    self.station_two_data["raw"] = text
                    last_raw_data2= text
                self.client_scanner_station2._log_add("INFO", f"Vision Station Two data: '{text}'")
                
                if text.startswith("R"):
                    parts = text.split("-")
                    dummy_number = parts[0].strip()
                    now2 = time.time()
                    
                    

                    with self.lock:
                        '''
                        last_time2 = self.last_dummy_time_station_two.get(dummy_number, 0)
                        if dummy_number == last_dummy_number2:
                            if now2 - last_time2 <= 60:
                                return
                            else:
                                tcp_server._log_add("WARNING", f"⚠️ Duplicate dummy ignored: {dummy_number}")

                                return 
                        '''
                
                    # ✅ CLEAR CSV FOR NEW DUMMY  ← 🆕 NEW LINE
                    hlb.clear_station2_csv_for_new_dummy(dummy_number)
            
                    self.last_dummy_time_station_two[dummy_number] = now2
                    self.station_two_data["dummy"] = dummy_number
                    waiting_for_station_two_result = True
                    current_dummy_station_two = dummy_number
                    received_tests_station2.clear()
                    last_dummy_number2 = dummy_number
                    self.client_scanner_station2._log_add("INFO", f"Station Two: Extracted dummy '{dummy_number}'")
                    
                    #time.sleep(0.1)  # Prevent DB contention
                    
                    if db.conn_str_db1_global:
                        with db_lock:
                            try:
                                with pyodbc.connect(db.conn_str_db1_global, timeout=hlb.TIME_SETTINGS['dbTimeout']) as conn:
                                    cursor = conn.cursor()
                                    cursor.execute(
                                        "SELECT ProductNumber FROM SFCNumbers WHERE LTRIM(RTRIM(Number)) = ?",
                                        (dummy_number,)
                                    )
                                    row = cursor.fetchone()

                                if row:
                                    last_product_number2 = row[0]
                                    status = f"✅ Found ProductNumber: {last_product_number2}"
                                    with self.lock:
                                        self.station_two_data["product"] = last_product_number2
                                        self.station_two_data["db_status"] = status
                                    self.client_scanner_station2._log_add("INFO", status)
                                    
                                    auto_load_csv_by_product_number(last_product_number2, "S2", self.client_Vision_station2, self.client_scanner_station2.shared_queue)
                                else:
                                    status = f"❌ Dummy '{dummy_number}' not found"
                                    with self.lock:
                                        self.station_two_data["db_status"] = status
                                    self.client_scanner_station2._log_add("WARNING", status)
                                    
                            except Exception as db_ex:
                                status = f"❌ DB query error: {db_ex}"
                                with self.lock:
                                    self.station_two_data["db_status"] = status
                                self.client_scanner_station2._log_add("ERROR", status)
                    else:
                        with self.lock:
                            self.station_two_data["db_status"] = "❌ No DB connection"
                            
            except Exception as e:
                self.client_scanner_station2._log_add("ERROR", f"Error processing Station Two data: {e}")


    def _SN_Proccess1(self,data:bytes):
         global image_SN1
         try:
             text = data.decode("utf-8", errors="ignore").strip()
             Chunks=text.split("-")
             
             if Chunks[0] == "SN":
                 image_SN1 = Chunks[1]
                 self.client_Vision_station1_SN._log_add("ERROR",f"Image serial Number Station1 {image_SN1}")
             else:
                 self.client_Vision_station1_SN._log_add("ERROR",f"UNEXPECTED INCOMING DATA FROM [{Ip_vision_outer_SN}]:{Port_vision_outer_SN}")
         except Exception as e:
                self.client_Vision_station1_SN._log_add("ERROR",f"{e}")
          
    def _SN_Proccess2(self,data:bytes):
         
        global image_SN2
        try:
             text = data.decode("utf-8", errors="ignore").strip()
             Chunks=text.split("-")
             
             if Chunks[0] == "SN":
                 image_SN2 = Chunks[1]
                 self.client_Vision_station1_SN._log_add("ERROR",f"Image serial Number Station2 {image_SN2}")
             else:
                 self.client_Vision_station1_SN._log_add("ERROR",f"UNEXPECTED INCOMING DATA FROM [{Ip_vision_outer_SN}]:{Port_vision_outer_SN}")
        except Exception as e:
                self.client_Vision_station1_SN._log_add("ERROR",f"{e}")
          
    
    def _IO_Writer_station_1(self):
        
       #self.client_write_io.send_request(message=CMD_ACTION_S1, is_hex=True)
        """
            Handle Station 1 device action with proper image waiting logic
            """
        self.client_write_io._log_add("FATAL", f"entered the seq of station 1")

        global Manual_Scanner_MODE, NO_CSV_ERROR, Buzzer_Flag_to_OFF
        global image_SN1, queue_manual_FOR_FAILURE, is_waiting  # Make sure we can access these

        try:
            
            # ---- initial sequence ----
            self.client_write_io.send_request(ON_LIGHTING_S1,is_hex=True)   # lighting ON
            self.client_write_io.send_request(ON_SCANNER_S1,is_hex=True)    #  scanner ON
            time.sleep(0.5)
            self.client_write_io.send_request(OFF_SCANNER_S1,is_hex=True)    #  scanner ON
            self.client_scanner_station1._log_add("info", f"light on")

            time.sleep(0.5)
            try:
                
                dummy= ""
                if  not self.client_scanner_station1.shared_queue3.empty():
                    
                     queue = self.client_scanner_station1.shared_queue3
                     dummy = queue.get_nowait()
                     #self.client_scanner_station1.shared_queue3.task_done()
                     
                     self.client_scanner_station1._log_add("FATAL", f"I GOT THE DUMMY [{dummy}]")
                     self.client_write_io.send_request(OFF_SCANNER_S1,is_hex=True)    # scanner Off
                else:
                    #queue_manual_FOR_FAILURE.queue.clear() # طريقة سريعة لمسح محتويات الكيو داخلياً
                    #queue_manual_FOR_FAILURE.all_tasks_done.notify_all() # إبلاغ أي Thread منتظر بأن المهام انتهت
                    self.client_write_io.send_request(OFF_SCANNER_S1,is_hex=True)    # scanner Off
                    
                    self.client_scanner_station1._log_add("info", f"Manual_Scanner_MODE [{Manual_Scanner_MODE}]")
                    
                    Manual_Scanner_MODE = True
                    while  is_waiting:
                        
                        self.client_write_io.send_request(ON_BUZZER_S1,is_hex=True)  # buzzer on
                    
                    self.client_write_io.send_request(OFF_BUZZER_S1,is_hex=True)  # buzzer off
       
                    self.client_scanner_station1._log_add("info", f"لولوللللولووللولولولولي")
                    
                    queue = queue_manual_FOR_FAILURE
                    dummy = queue.get()    
                        #queue_manual_FOR_FAILURE.task_done()                  
                    self.client_write_io.send_request(OFF_SCANNER_S1,is_hex=True)    # scanner Off
                    self.client_scanner_station1._log_add("info", f"{type(dummy)}")  # R0124090500055
                    text = dummy.encode("utf-8")
                    self.Manual_scanner_station_1(text)
                    self.client_scanner_station1._log_add("info", f"وصلناااااا")  # R0124090500055

                        
            except Exception as e:
                   self.client_scanner_station1._log_add("FATAL", f"ERROR WHILE SCANNING DUMMY NUMBER: {e}")
        except Exception as e:
            self.client_write_io._log_add("FATAL", f"S1 device init error: {e}")
            self.client_write_io.send_request(CMD_OFF_ALL,is_hex=True)
            return

        # ✅ FIX: Capture the starting state before waiting
        start_time = time.time()
        initial_image_state = image_SN1  # Remember what image_SN1 was at the start
        image_timeout = hlb.TIME_SETTINGS['ImageTimeout']
        
        self.client_write_io._log_add("INFO", f"Waiting for new image. Current state: {initial_image_state}")

        # ---- wait for NEW image ----
        # ✅ FIX: Proper loop with three conditions:
        # 1. Wait while we haven't received a new image
        # 2. New image means: image_SN1 changed from initial_image_state
        # 3. AND image_SN1 is not None
        image_received = False
        
        while not image_received:
            current_time = time.time()
            
            # Check if we got a new image
            if image_SN1 is not None and image_SN1 != initial_image_state:
                self.client_write_io._log_add("INFO", f"New image received: {image_SN1}")
                self.client_write_io.send_request(OFF_LIGHTING_S1,is_hex=True)   # lighting OFF
                self.client_write_io.send_request(ON_TESTDONE_S1,is_hex=True) 
                plc_signal_period = hlb.TIME_SETTINGS['PlcSignal']
                time.sleep(plc_signal_period)
                self.client_write_io.send_request(OFF_TESTDONE_S1,is_hex=True) 
                result =  hlb._failure_mode_station2_check(target_dummy=dummy, Client= self.client_scanner_station1)
                if result == "FAIL" :
                     self.client_write_io.send_request(ON_FAILURE,is_hex=True) 
                     plc_signal_period = hlb.TIME_SETTINGS['PlcSignal']
                     self.client_write_io.send_request(OFF_FAILURE,is_hex=True) 
                image_received = True
                queue.task_done()
            '''
            # Check for timeout
            if current_time - start_time > image_timeout:
                self._log_add("WARNING", f"Image timeout after {image_timeout} seconds")
                break
            '''
            # Wait a bit before checking again
            time.sleep(0.1)

        # ---- image received successfully ----
        last_image_SN1 = image_SN1
        self.client_write_io._log_add("INFO", f"Image processing complete for: {image_SN1}")
        
    
    
    def _IO_Writer_station_2(self):
             #self.client_write_io.send_request(message=CMD_ACTION_S1, is_hex=True)
        """
            Handle Station 1 device action with proper image waiting logic
            """
        self.client_write_io._log_add("FATAL", f"entered the seq of station 1")

        global Manual_Scanner_MODE2, NO_CSV_ERROR, Buzzer_Flag_to_OFF
        global image_SN2, queue_manual2_FOR_FAILURE, is_waiting2  # Make sure we can access these

        try:
            
            # ---- initial sequence ----
            self.client_write_io.send_request(ON_LIGHTING_S2,is_hex=True)   # lighting ON
            self.client_write_io.send_request(ON_SCANNER_S2,is_hex=True)    #  scanner ON
            time.sleep(0.5)
            self.client_write_io.send_request(OFF_SCANNER_S2,is_hex=True)    #  scanner ON
            self.client_scanner_station1._log_add("info", f"light on")

            time.sleep(0.5)
            try:
                
                dummy= ""
                if  not self.client_scanner_station2.shared_queue3.empty():
                    
                     queue = self.client_scanner_station2.shared_queue3
                     dummy = queue.get_nowait()
                     #self.client_scanner_station1.shared_queue3.task_done()
                     
                     self.client_scanner_station2._log_add("FATAL", f"I GOT THE DUMMY [{dummy}]")
                     self.client_write_io.send_request(OFF_SCANNER_S2,is_hex=True)    # scanner Off
                else:
                    #queue_manual_FOR_FAILURE.queue.clear() # طريقة سريعة لمسح محتويات الكيو داخلياً
                    #queue_manual_FOR_FAILURE.all_tasks_done.notify_all() # إبلاغ أي Thread منتظر بأن المهام انتهت
                    self.client_write_io.send_request(OFF_SCANNER_S2,is_hex=True)    # scanner Off
                    
                    self.client_scanner_station2._log_add("info", f"Manual_Scanner_MODE [{Manual_Scanner_MODE}]")
                    
                    Manual_Scanner_MODE2 = True
                    while  is_waiting2:
                        
                        self.client_write_io.send_request(ON_BUZZER_S2,is_hex=True)  # buzzer on
                    
                    self.client_write_io.send_request(OFF_BUZZER_S2,is_hex=True)  # buzzer off
       
                    self.client_scanner_station2._log_add("info", f"لولوللللولووللولولولولي")
                    
                    queue = queue_manual_FOR_FAILURE
                    dummy = queue.get()    
                        #queue_manual_FOR_FAILURE.task_done()                 
                    self.client_write_io.send_request(OFF_SCANNER_S2,is_hex=True)    # scanner Off
                    self.client_scanner_station2._log_add("info", f"{type(dummy)}")  # R0124090500055
                    text = dummy.encode("utf-8")    
                    self.Manual_scanner_station_2(text)
                    self.client_scanner_station2._log_add("info", f"وصلناااااا")  # R0124090500055

                        
            except Exception as e:
                   self.client_scanner_station2._log_add("FATAL", f"ERROR WHILE SCANNING DUMMY NUMBER: {e}")
        except Exception as e:
            self.client_write_io._log_add("FATAL", f"S2 device init error: {e}")
            self.client_write_io.send_request(CMD_OFF_ALL,is_hex=True)
            return

        # ✅ FIX: Capture the starting state before waiting
        start_time = time.time()
        initial_image_state = image_SN2  # Remember what image_SN1 was at the start
        image_timeout = hlb.TIME_SETTINGS['ImageTimeout']
        
        self.client_write_io._log_add("INFO", f"Waiting for new image. Current state: {initial_image_state}")

        # ---- wait for NEW image ----
        # ✅ FIX: Proper loop with three conditions:
        # 1. Wait while we haven't received a new image
        # 2. New image means: image_SN1 changed from initial_image_state
        # 3. AND image_SN1 is not None
        image_received = False
        
        while not image_received:
            current_time = time.time()
            
            # Check if we got a new image
            if image_SN2 is not None and image_SN2 != initial_image_state:
                self.client_write_io._log_add("INFO", f"New image received: {image_SN1}")
                self.client_write_io.send_request(OFF_LIGHTING_S2,is_hex=True)   # lighting OFF
                self.client_write_io.send_request(ON_TESTDONE_S2,is_hex=True) 
                plc_signal_period = hlb.TIME_SETTINGS['PlcSignal']
                time.sleep(plc_signal_period)
                self.client_write_io.send_request(OFF_TESTDONE_S2,is_hex=True) 
               
                image_received = True
                queue.task_done()
            '''
            # Check for timeout
            if current_time - start_time > image_timeout:
                self._log_add("WARNING", f"Image timeout after {image_timeout} seconds")
                break
            '''
            # Wait a bit before checking again
            time.sleep(0.1)

        # ---- image received successfully ----
        last_image_SN1 = image_SN2
        self.client_write_io._log_add("INFO", f"Image processing complete for: {image_SN2}")
    

    def data_processing_station1(self):
            self.client_scanner_station1._log_add("INFO", "Station 1 processing thread started")
         
            test_results_dict = {}
            self.client_scanner_station1._log_add("INFO", "قبل التراااااي")
            try:
                self.client_scanner_station1._log_add("INFO", "مستني داتا من Vision 1")

                # 1. الأفضل نستخدم blocking get مع timeout بدل الـ empty()
                # كدة الثريد هينام ويفوق أول ما داتا تيجي، وده أحسن للبروسيسور
                try:
                    # بيستنى داتا من Vision Station 1 لمدة ثانية
                    test_results_dict = self.client_Vision_station1.shared_queue.get(timeout=30)
                    self.client_scanner_station1._log_add("INFO", f"AAAAAAAAAAAAAAAA😊{test_results_dict}")
                except Empty: 
                    # لو مفيش داتا جات في خلال ثانية، يرجع يلف تاني}
                    self.client_scanner_station1._log_add("INFO", "AAAAAAAAAAAAAAAA😊")

                if test_results_dict and isinstance(test_results_dict, dict):                    
                    # 2. استخراج الاختبارات الفاشلة
                    zero_values_list = [k for k, v in test_results_dict.items() if v == "0"]
                    failed_tests = ", ".join(zero_values_list)
                    station_name = "VisionOuterTest"
                    if zero_values_list:

                        station_result = "FAIL" 
                    else :
                        station_result = "PASS" 
                       
                    # 3. سحب رقم الـ Dummy (تأكد أن الكيو ده فيه داتا فعلاً)
                    try:
                        dummy = self.client_scanner_station1.shared_queue2.get_nowait()
                        
                        # 4. الرفع لقاعدة البيانات
                        db.upload_tests_result_to_db(
                            dummy=dummy,
                            station_name=station_name,
                            station_result=station_result,
                            failed_tests=failed_tests,
                            Client=self.client_scanner_station1
                        )
                        

                        # تأكيد إتمام المهمة للكيو الخاص بالـ dummy
                        self.client_scanner_station1.shared_queue2.task_done()
                    except:
                        dummy = queue_manual_FOR_Proessing.get_nowait()
                        
                        # 4. الرفع لقاعدة البيانات
                        db.upload_tests_result_to_db(
                            dummy=dummy,
                            station_name=station_name,
                            station_result=station_result,
                            failed_tests=failed_tests,
                            Client=self.client_scanner_station1)
                        self.client_scanner_station1._log_add("WARNING", "No dummy ID found in shared_queue2")

                    # تأكيد إتمام المهمة للكيو الخاص بالنتائج
                        queue_manual_FOR_Proessing.task_done()
            
            except Exception as e:
                self.client_scanner_station1._log_add("ERROR", f"Error in processing: {e}")
                time.sleep(1) # عشان لو حصل خطأ متكرر ميعلقش الجهاز




    def data_processing_station2(self):
        self.client_scanner_station2._log_add("INFO", "Station 2 processing thread started")
         
        test_results_dict = {}
        self.client_scanner_station2._log_add("INFO", "قبل التراااااي")
        try:
                self.client_scanner_station2._log_add("INFO", "مستني داتا من Vision 2")

                # 1. الأفضل نستخدم blocking get مع timeout بدل الـ empty()
                # كدة الثريد هينام ويفوق أول ما داتا تيجي، وده أحسن للبروسيسور
                try:
                    # بيستنى داتا من Vision Station 1 لمدة ثانية
                    test_results_dict = self.client_Vision_station2.shared_queue.get(timeout=30)
                    self.client_scanner_station2._log_add("INFO", f"AAAAAAAAAAAAAAAA😊{test_results_dict}")
                except Empty: 
                    # لو مفيش داتا جات في خلال ثانية، يرجع يلف تاني}
                    self.client_scanner_station2._log_add("INFO", "AAAAAAAAAAAAAAAA😊")

                if test_results_dict and isinstance(test_results_dict, dict):                    
                    # 2. استخراج الاختبارات الفاشلة
                    zero_values_list = [k for k, v in test_results_dict.items() if v == "0"]
                    failed_tests = ", ".join(zero_values_list)
                    station_name = "VisionOuterTest"
                    if zero_values_list:

                        station_result = "FAIL" 
                    else :
                        station_result = "PASS" 
                       
                    # 3. سحب رقم الـ Dummy (تأكد أن الكيو ده فيه داتا فعلاً)
                    try:
                        dummy = self.client_scanner_station2.shared_queue2.get_nowait()
                        
                        hlb.insert_csv_station2_dummies(dummy=dummy, station_result= station_result)
                        # 4. الرفع لقاعدة البيانات
                        db.upload_tests_result_to_db(
                            dummy=dummy,
                            station_name=station_name,
                            station_result=station_result,
                            failed_tests=failed_tests,
                            Client=self.client_scanner_station1
                        )
                        

                        # تأكيد إتمام المهمة للكيو الخاص بالـ dummy
                        self.client_scanner_station1.shared_queue2.task_done()
                    except:
                        dummy = queue_manual2_FOR_Proessing.get_nowait()
                        hlb.insert_csv_station2_dummies(dummy=dummy, station_result= station_result)
                        
                        # 4. الرفع لقاعدة البيانات
                        db.upload_tests_result_to_db(
                            dummy=dummy,
                            station_name=station_name,
                            station_result=station_result,
                            failed_tests=failed_tests,
                            Client=self.client_scanner_station1)
                        #self.client_scanner_station2._log_add("WARNING", "No dummy ID found in shared_queue2")

                    # تأكيد إتمام المهمة للكيو الخاص بالنتائج
                        queue_manual2_FOR_Proessing.task_done()
            
        except Exception as e:
                self.client_scanner_station2._log_add("ERROR", f"Error in processing: {e}")
                time.sleep(1) # عشان لو حصل خطأ متكرر ميعلقش الجهاز

   
    '''
#database handling
    def auto_connect_db(self):
        """Automatically connect to saved database settings"""
        global conn_str_db1_global, conn_str_db2_global
        conn_str_db1_global, msg1 = self.connect_from_file("last_db1_settings.txt", 1)
        conn_str_db2_global, msg2 = self.connect_from_file("last_db2_settings.txt", 2)
        print(f"{msg1}\n{msg2}")

    def connect_from_file(self, filename, index):
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

    '''    

    def run(self):
        self.root.mainloop()

##################################################################





