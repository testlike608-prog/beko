import webbrowser 
import threading 
import sys
from flask import Flask,redirect
from auth import auth
from flash import flash
from home import home 
from SQL import SQL
from CreateUser import CreateUser
from CreateProgram import CreateProgram
from ClientsClass import App
import db ,ClientsClass
from waitress import serve

app = Flask(__name__,template_folder="templates",static_folder="static")
app.secret_key = "your-secret-key-here"

app.register_blueprint(auth) # login app
app.register_blueprint(flash) #splash page
app.register_blueprint(home) #index
app.register_blueprint(CreateProgram) #create program App
app.register_blueprint(CreateUser) #create User App
app.register_blueprint(SQL)



@app.route("/")
def log():
    return redirect("/login")  

def main():
    ClientsApp = App()   
    ClientsApp.Start_connetion()
    threading.Thread(target= ClientsApp._IO_read, daemon= True).start()
    threading.Thread(target=ClientsApp._vision_station_2, daemon= True).start()
    threading.Thread(target=ClientsApp._vision_station_1, daemon= True).start()
    #threading.Thread(target=ClientsApp.data_processing_station1, daemon= True).start()F
    #threading.Thread(target=ClientsApp.data_processing_station1, daemon=True).start()س
    
if __name__ == "__main__":

    threading.Timer(1, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    threading.Thread(target=main, daemon= False).start()
    #threading.Thread(target=app.run(debug=False), daemon= True).start()
    
    #app.run(debug= False)
    serve(app,host="127.0.0.1",port=5000)
    