from flask import Flask , render_template_string ,render_template,redirect,Blueprint ,url_for



Manual= Blueprint(
    "Manual",
    __name__,
    static_folder="static",
    template_folder="templates"
)
@Manual.route('/ManualPopup', methods=['GET'])
def page_ManualPopup():
    global Manual_Scanner_MODE
    if Manual_Scanner_MODE:
        return render_template ("Manual_HTML.html", message="ERROR : Auto SCANNING FAILED, PLEASE SCAN MANUALLY")
        #return render_template_string(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .modal-overlay {
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center;
                }
                .modal-box {
                    background: white; padding: 30px; border-radius: 10px; text-align: center;
                    max-width: 400px; font-family: sans-serif;
                }
                .btn-close {
                    background: #aa1f1a; color: white; border: none;
                    padding: 10px 20px; border-radius: 5px;
                }
            </style>
        </head>
        <body>
            <div class="modal-overlay">
                <div class="modal-box">
                    <h2>⚠️ System Alert</h2>
                    <p>{{ message }}</p>

                    <form method="POST" action="/ManualPopup/ack">
                        <button class="btn-close" type="submit">OK</button>
                    </form>
                </div>
            </div>
        </body>
        </html>
        """

    return url_for('home.page_index')
@Manual.route('/ManualPopup/ack', methods=['POST'])
def manual_popup_ack():
    global Manual_Scanner_MODE,Buzzer_Flag_to_OFF
    Buzzer_Flag_to_OFF = True
    Manual_Scanner_MODE = False   # 👈 الفلاج بيتقفل هنا
    return url_for('home.page_index')
@Manual.route('/NoCSV', methods=['GET'])
def page_CSVPopup():
    global NO_CSV_ERROR, last_product_number
    if NO_CSV_ERROR:
        return render_template("NOCSV_HTML.html",message=f"ERROR : NO CSV FILE FOUND FOR SKU {last_product_number}")
        # return render_template_string(
        """
        <!DOCTYPE html>
        <html>
        <body>
            <div class="modal-overlay">
                <div class="modal-box">
                    <h2>⚠️ System Alert</h2>
                    <p>{{ message }}</p>

                    <form method="POST" action="/NoCSV/ack">
                        <button type="submit">OK</button>
                    </form>
                </div>
            </div>
        </body>
        </html>
        """

    return url_for('home.page_index')
@Manual.route('/NoCSV/ack', methods=['POST'])
def csv_popup_ack():
    global NO_CSV_ERROR ,Buzzer_Flag_to_OFF2 
    Buzzer_Flag_to_OFF2 = True
    NO_CSV_ERROR = False   # 👈 يقفل الفلاج
    return url_for('home.page_index')
