from helpers import tcp_log_print 
import threading
import time 
from ClientsClass import TCPClient
import pyodbc
import socket
from helpers import TIME_SETTINGS, clear_station1_csv_for_new_dummy,clear_station2_csv_for_new_dummy, received_tests_station1,conn_str_db1_global,conn_str_db2_global,auto_load_csv_by_product_number
from helpers import Ip_vision_inner,Port_vision_inner,Ip_vision_outer,Port_vision_outer
from ClientsClass import received_tests_station2,received_tests_station1

db_lock = threading.Lock()


ClientStation1 =TCPClient(Ip_vision_inner,Port_vision_inner)
ClientStation2 =TCPClient(Ip_vision_outer,Port_vision_outer)

class VisionDataHandler:
    """Handles data from vision master systems (ports 7940, 7950)"""
    
    def __init__(self):
        self.station_one_data = {"raw": "", "dummy": "", "product": "", "db_status": ""}
        self.station_two_data = {"raw": "", "dummy": "", "product": "", "db_status": ""}
        self.lock = threading.Lock()
        # timestamps for each dummy
        self.last_dummy_time_station_one = {}  # dict {dummy_number: timestamp}
        self.last_dummy_time_station_two = {}

    def process_station_one_data(self, data: bytes):
        """Process data from vision check 1 (port 7940)"""
        global last_product_number, current_dummy_station_one, waiting_for_station_one_result,dummy_number,last_raw_data1,last_dummy_number
        
        try:
            text = data.decode("utf-8", errors="ignore").strip()
            if len(text) > 14:
                text = text[:14]
            
            with self.lock:
                self.station_one_data["raw"] = text
                last_raw_data1 = text
            TCPClient._log_add("INFO", f"Vision Station Outer control data: '{text}'")
            
            if text.startswith("R"):
                parts = text.split("-")
                dummy_number = parts[0].strip()
                now = time.time()


                with self.lock:
                     last_time = self.last_dummy_time_station_one.get(dummy_number, 0)
                     if dummy_number == last_dummy_number:
                        if now - last_time <60:

                           return
                        else:
                            TCPClient._log_add("WARNING", f"⚠️ Duplicate dummy ignored: {dummy_number}")

                            return 
                # ✅ CLEAR CSV FOR NEW DUMMY
                clear_station1_csv_for_new_dummy(dummy_number)
       
                
               
                self.last_dummy_time_station_one[dummy_number] = now
                self.station_one_data["dummy"] = dummy_number
                last_dummy_number = dummy_number
                waiting_for_station_one_result = True
                current_dummy_station_one = dummy_number
                received_tests_station1.clear()
                TCPClient._log_add("INFO", f"Station Outer Control: Extracted dummy '{dummy_number}'")
                
                if conn_str_db1_global:
                    with db_lock:
                        try:
                            with pyodbc.connect(conn_str_db1_global, timeout=TIME_SETTINGS['dbTimeout']) as conn:
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
                                TCPClient._log_add("INFO", status)
                                
                                auto_load_csv_by_product_number(last_product_number, "S1", ClientStation1)
                            else:
                                status = f"❌ Dummy '{dummy_number}' not found"
                                with self.lock:
                                    self.station_one_data["db_status"] = status
                                TCPClient._log_add("WARNING", status)
                                
                        except Exception as db_ex:
                            status = f"❌ DB query error: {db_ex}"
                            with self.lock:
                                self.station_one_data["db_status"] = status
                            TCPClient._log_add("ERROR", status)
                else:
                    with self.lock:
                        self.station_one_data["db_status"] = "❌ No DB connection"
                        
        except Exception as e:
            TCPClient._log_add("ERROR", f"Error processing Station Outer Control data: {e}")
    
    def process_station_two_data(self, data: bytes):
        """Process data from vision check 2 (port 7950)"""
        global last_product_number2, current_dummy_station_two, waiting_for_station_two_result,dummy_number,last_raw_data2,last_dummy_number2
        
        try:
            text = data.decode("utf-8", errors="ignore").strip()
            if len(text) > 14:
                text = text[:14]
            
            with self.lock:
                self.station_two_data["raw"] = text
                last_raw_data2= text
            TCPClient._log_add("INFO", f"Vision Station Two data: '{text}'")
            
            if text.startswith("R"):
                parts = text.split("-")
                dummy_number = parts[0].strip()
                now2 = time.time()

                with self.lock:
                     last_time2 = self.last_dummy_time_station_two.get(dummy_number, 0)
                     if dummy_number == last_dummy_number2:
                        if now2 - last_time2 <= 60:
                            return
                        else:
                            TCPClient._log_add("WARNING", f"⚠️ Duplicate dummy ignored: {dummy_number}")

                            return 
                # ✅ CLEAR CSV FOR NEW DUMMY  ← 🆕 NEW LINE
                clear_station2_csv_for_new_dummy(dummy_number)
          
                self.last_dummy_time_station_two[dummy_number] = now2
                self.station_two_data["dummy"] = dummy_number
                waiting_for_station_two_result = True
                current_dummy_station_two = dummy_number
                received_tests_station2.clear()
                last_dummy_number2 = dummy_number
                TCPClient._log_add("INFO", f"Station Two: Extracted dummy '{dummy_number}'")
                
                time.sleep(0.1)  # Prevent DB contention
                
                if conn_str_db1_global:
                    with db_lock:
                        try:
                            with pyodbc.connect(conn_str_db1_global, timeout=TIME_SETTINGS['dbTimeout']) as conn:
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
                                TCPClient._log_add("INFO", status)
                                
                                auto_load_csv_by_product_number(last_product_number2, "S2", ClientStation2)
                            else:
                                status = f"❌ Dummy '{dummy_number}' not found"
                                with self.lock:
                                    self.station_two_data["db_status"] = status
                                TCPClient._log_add("WARNING", status)
                                
                        except Exception as db_ex:
                            status = f"❌ DB query error: {db_ex}"
                            with self.lock:
                                self.station_two_data["db_status"] = status
                            TCPClient._log_add("ERROR", status)
                else:
                    with self.lock:
                        self.station_two_data["db_status"] = "❌ No DB connection"
                        
        except Exception as e:
            TCPClient._log_add("ERROR", f"Error processing Station Two data: {e}")
    
    def get_status(self):
        """Get current status of both stations"""
        with self.lock:
            return {
                "station_one": self.station_one_data.copy(),
                "station_two": self.station_two_data.copy()
            }







# Global handler instance
vision_handler = VisionDataHandler()

# Vision server addresses (global) 
IP_VISION_1 = "127.0.0.1"
PORT_VISION_1 = 5555
IP_VISION_2 = "127.0.0.1"
PORT_VISION_2 = 1234

# ---------------- Vision Master Listener ----------------
def vision_listener_thread():
    """Thread to listen to both Vision Masters"""
    global vision_handler
    
    # Initialize connection variables
    connected_1 = False
    connected_2 = False
    sock_vision_1 = None
    sock_vision_2 = None
    
    TCPClient._log_add("INFO", "Vision listener thread started for both servers")

    while True:
        try:
            # Connect to Vision 1
            if not connected_1:
                try:
                    TCPClient._log_add("INFO", f"Connecting to Vision 1 ({IP_VISION_1}:{PORT_VISION_1})")
                    s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s1.settimeout(0.5)
                    s1.connect((IP_VISION_1, PORT_VISION_1))
                    s1.settimeout(1)
                    sock_vision_1 = s1
                    connected_1 = True
                    TCPClient._log_add("INFO", f"✅ Connected to Vision 1")
                except Exception as e:
                    TCPClient._log_add("ERROR", f"Vision 1 connection failed: {e}")
                    time.sleep(5)
                    continue
            
            # Connect to Vision 2
            if not connected_2:
                try:
                    TCPClient._log_add("INFO", f"Connecting to Vision 2 ({IP_VISION_2}:{PORT_VISION_2})")
                    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s2.settimeout(10)
                    s2.connect((IP_VISION_2, PORT_VISION_2))
                    s2.settimeout(1)
                    sock_vision_2 = s2
                    connected_2 = True
                    TCPClient._log_add("INFO", f"✅ Connected to Vision 2")
                except Exception as e:
                    TCPClient._log_add("ERROR", f"Vision 2 connection failed: {e}")
                    time.sleep(5)
                    continue
            
            # Listen for data from both
            try:
                if connected_1 and sock_vision_1:
                    try:
                        data1 = sock_vision_1.recv(1024)
                        if data1:
                            vision_handler.process_station_one_data(data1)
                        else:
                            TCPClient._log_add("WARNING", "Vision 1 disconnected")
                            connected_1 = False
                            if sock_vision_1:
                                sock_vision_1.close()
                                sock_vision_1 = None
                    except socket.timeout:
                        pass
                    except Exception as e:
                        TCPClient._log_add("ERROR", f"Vision 1 recv error: {e}")
                        connected_1 = False
                        if sock_vision_1:
                            sock_vision_1.close()
                            sock_vision_1 = None
                
                if connected_2 and sock_vision_2:
                    try:
                        data2 = sock_vision_2.recv(1024)
                        if data2:
                            vision_handler.process_station_two_data(data2)
                        else:
                            TCPClient._log_add("WARNING", "Vision 2 disconnected")
                            connected_2 = False
                            if sock_vision_2:
                                sock_vision_2.close()
                                sock_vision_2 = None
                    except socket.timeout:
                        pass
                    except Exception as e:
                        TCPClient._log_add("ERROR", f"Vision 2 recv error: {e}")
                        connected_2 = False
                        if sock_vision_2:
                            sock_vision_2.close()
                            sock_vision_2 = None
                
            except Exception as e:
                TCPClient._log_add("ERROR", f"Vision listener error: {e}")
                time.sleep(1)
                
        except Exception as e:
            TCPClient._log_add("ERROR", f"Vision listener main loop error: {e}")
            time.sleep(5)