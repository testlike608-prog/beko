from flask import Flask , render_template_string ,render_template,redirect,Blueprint ,url_for, jsonify, request
import queue
import ClientsClass as cc

Manual= Blueprint(
    "Manual",
    __name__,
    static_folder="static",
    template_folder="templates"
)
@Manual.route('/ManualPopup', methods=['GET'])
def page_ManualPopup():
    if cc.Manual_Scanner_MODE:
        return render_template("Manual_HTML.html", message="ERROR : Auto SCANNING FAILED")
    
    # لو الـ flag اتقفل أو حد دخل المسار بالغلط والـ flag بـ False، يرجعه للرئيسية
    return redirect(url_for('home.page_index')) 

@Manual.route('/NoCSV', methods=['GET'])
def page_CSVPopup():
    if cc.NO_CSV_ERROR:
        return render_template("NOCSV_HTML.html", message=f"ERROR : NO CSV FILE FOUND")
    
    return redirect(url_for('home.page_index'))
@Manual.route('/ManualPopup/ack', methods=['POST'])
def manual_popup_ack():
    
    cc.Buzzer_Flag_to_OFF = True
    cc.Manual_Scanner_MODE = False   # 👈 الفلاج بيتقفل هنا
    return url_for('home.page_index')



    return url_for('home.page_index')
@Manual.route('/NoCSV/ack', methods=['POST'])
def csv_popup_ack():
    cc.Buzzer_Flag_to_OFF2 = True
    cc.NO_CSV_ERROR = False   # 👈 يقفل الفلاج
    return url_for('home.page_index')



@Manual.route('/check-flags')
def check_flags():
    # تأكدي إننا بنقرأ القيم من كلاس cc اللي فيه القيم الحقيقية
    res = jsonify({
        "manual_scanner": cc.Manual_Scanner_MODE,
        "no_csv_error": cc.NO_CSV_ERROR  # ضفت cc هنا عشان ما يحصلش Error
    })
    
    # ده مجرد برنت ليكي عشان تتأكدي في الـ Terminal إن القيمة بقت True
    print(f"Checking Flags: Scanner={cc.Manual_Scanner_MODE}, CSV={cc.NO_CSV_ERROR}")
    
    return res

# 2. تعريف الـ Queue عشان نخزن فيه الداتا


@Manual.route('/api/station', methods=['POST'])
def handle_station_data():
    # لازم نستخدم كلمة global عشان نقدر نعدل على المتغير اللي بره الفانكشن
    
    
    # نستقبل الداتا اللي جاية من الجافا سكريبت
    data_received = request.json.get('station_data')
    
    if data_received:
        # 3. نغير قيمة الـ global variable لـ False
        
        
        # 4. نحط الداتا في الـ Queue
        cc.queue_manual_FOR_FAILURE.put(data_received)
        cc.is_waiting = False
        
        # طباعة للتأكيد في الـ Console بتاع البايثون
        print(f"Global Variable 'is_waiting' is now: {cc.is_waiting}")
        print(f"Data added to queue. Queue size: {cc.queue_manual_FOR_FAILURE.qsize()}")
        print(f"Data content: {data_received}")
        
        # نرد على الجافا سكريبت إن كله تمام
        return jsonify({"status": "success", "message": "تم إضافة الداتا وتغيير المتغير"}), 200
        
    return jsonify({"status": "error", "message": "لم يتم استلام أي بيانات"}), 400

@Manual.route('/api/station2', methods=['POST'])
def handle_station_data2():
    # لازم نستخدم كلمة global عشان نقدر نعدل على المتغير اللي بره الفانكشن
    
    
    # نستقبل الداتا اللي جاية من الجافا سكريبت
    data_received = request.json.get('station_data')
    
    if data_received:
        # 3. نغير قيمة الـ global variable لـ False
        
        
        # 4. نحط الداتا في الـ Queue
        cc.queue_manual2_FOR_FAILURE.put(data_received)
        cc.is_waiting = False
        
        # طباعة للتأكيد في الـ Console بتاع البايثون
        print(f"Global Variable 'is_waiting' is now: {cc.is_waiting}")
        print(f"Data added to queue. Queue size: {cc.queue_manual2_FOR_FAILURE.qsize()}")
        print(f"Data content: {data_received}")
        
        # نرد على الجافا سكريبت إن كله تمام
        return jsonify({"status": "success", "message": "تم إضافة الداتا وتغيير المتغير"}), 200
        
    return jsonify({"status": "error", "message": "لم يتم استلام أي بيانات"}), 400
