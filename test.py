import helpers as hlb
import os
import re
import time



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



if __name__ == "__main__":
# ---------------- Auto-load CSV by ProductNumber ----------------
        safe_product = re.sub(r'[^\w\-]', '', "950003659" or "")

           
        
        
        filename = f"{safe_product}{"S1"}.csv"
        csv_path  = os.path.join(hlb.PROGRAMS_DIR, "CreateProgram", filename)
        csv_data = hlb._load_csv_file(csv_path)
        
        # 1. الحصول على جميع العناوين (الأعمدة) من ملف الـ CSV
        # نفترض أن csv_data عبارة عن قاموس (Dictionary) يمثل الصف
        all_columns = list(csv_data.keys())
        
        # 2. تحديد الكلمة التي تريد البحث عنها لنقلها للآخر
        target_word = "Front Logo" # يمكنك تغييرها لما يناسبك أو جعلها متغيرًا
        target_word2 = "Shelve color"
        
        # 3. إعادة ترتيب القائمة: استبعاد الكلمة ثم إضافتها في النهاية
        order = [col for col in all_columns if col != target_word]
        
        if target_word in all_columns:
            order.append(target_word)
        


        codes = "".join(_get_code(csv_data.get(k, "")) for k in order if _get_code(csv_data.get(k, "")) != "")

        print("Codes in new order:", codes)
        print("Order of columns:", order)
      
      
            

        
  