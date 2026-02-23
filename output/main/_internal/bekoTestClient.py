import socket
import threading
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox

class TCPClient:
    def __init__(self, name, master, row, auto_send_feature=False):
        self.name = name
        self.sock = None
        self.connected = False
        self.auto_sending = False # حالة الإرسال التلقائي

        # IP
        tk.Label(master, text=f"{name} IP:").grid(row=row, column=0, sticky="w")
        self.ip_entry = tk.Entry(master, width=15)
        self.ip_entry.grid(row=row, column=1)
        self.ip_entry.insert(0, "127.0.0.1")

        # Port
        tk.Label(master, text="Port:").grid(row=row, column=2, sticky="w")
        self.port_entry = tk.Entry(master, width=6)
        self.port_entry.grid(row=row, column=3)
        self.port_entry.insert(0, "5555")

        # Connect button
        self.connect_btn = tk.Button(master, text="Connect", command=self.connect, width=10)
        self.connect_btn.grid(row=row, column=4)

        # Log box
        self.log = scrolledtext.ScrolledText(master, width=50, height=8)
        self.log.grid(row=row+1, column=0, columnspan=5, pady=4)

        # Message to send
        self.msg_entry = tk.Entry(master, width=40)
        self.msg_entry.grid(row=row+2, column=0, columnspan=3, sticky="w")
        self.msg_entry.insert(0, "010203") # مثال لـ HEX

        # Send button
        self.send_btn = tk.Button(master, text="Send", command=self.send_msg, width=8)
        self.send_btn.grid(row=row+2, column=3)

        # ميزة الإرسال التلقائي (للكلاينت الأول فقط مثلاً)
        if auto_send_feature:
            self.auto_btn = tk.Button(master, text="Start Auto", command=self.toggle_auto_send, fg="blue")
            self.auto_btn.grid(row=row+2, column=4)
            
            tk.Label(master, text="Sec:").grid(row=row, column=5, sticky="e")
            self.interval_entry = tk.Entry(master, width=4)
            self.interval_entry.grid(row=row, column=6)
            self.interval_entry.insert(0, "1.0")

    def connect(self):
        if self.connected:
            self.disconnect()
            return
        ip = self.ip_entry.get()
        port = int(self.port_entry.get())
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, port))
            self.connected = True
            self.connect_btn.config(text="Disconnect", bg="red", fg="white")
            threading.Thread(target=self.receive_loop, daemon=True).start()
            self._log("Connected!\n")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def disconnect(self):
        self.connected = False
        self.auto_sending = False # وقف الإرسال لو فصلنا
        if self.sock:
            try: self.sock.close()
            except: pass
        self.connect_btn.config(text="Connect", bg="SystemButtonFace", fg="black")
        self._log("Disconnected!\n")

    def send_msg(self, silent=False):
        if not self.connected: return

        msg = self.msg_entry.get().strip()
        if not msg: return

        try:
            data = bytes.fromhex(msg)
            self.sock.sendall(data)
            if not silent: # عشان اللوج ميتمليش بسرعة لو بتبعت تلقائي
                self._log(f"-> {msg}\n")
        except ValueError:
            if not silent: self._log("Send error: Invalid HEX\n")
        except Exception as e:
            self.disconnect()
            self._log(f"Send error: {e}\n")

    def toggle_auto_send(self):
        if not self.connected:
            messagebox.showwarning("Warning", "Connect first!")
            return
        
        if self.auto_sending:
            self.auto_sending = False
            self.auto_btn.config(text="Start Auto", fg="blue")
        else:
            self.auto_sending = True
            self.auto_btn.config(text="Stop Auto", fg="red")
            # تشغيل ثريد منفصل للإرسال التلقائي
            threading.Thread(target=self.auto_send_loop, daemon=True).start()

    def auto_send_loop(self):
        while self.auto_sending and self.connected:
            self.send_msg(silent=False) # خليها True لو مش عايز زحمة في اللوج
            try:
                interval = float(self.interval_entry.get())
                time.sleep(interval)
            except:
                time.sleep(1) # لو حصل خطأ في رقم الثواني

    def _log(self, text):
        self.log.insert(tk.END, text)
        self.log.see(tk.END)

    def receive_loop(self):
        while self.connected:
            try:
                data = self.sock.recv(1024)
                if not data: break
                hex_data = data.hex().upper()
                self.log.after(0, self._log, f"<- {hex_data}\n")
            except:
                break
        self.log.after(0, self.disconnect)

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Industrial TCP Dual Client")

        # Client 1: مفعّل فيه خاصية الإرسال التلقائي
        self.client1 = TCPClient("Client 1", self.root, 0, auto_send_feature=True)
        
        # فاصل بصري
        tk.Frame(self.root, height=2, bd=1, relief="sunken").grid(row=3, column=0, columnspan=7, sticky="we", pady=10)
        
        # Client 2: عادي زي ما هو
        self.client2 = TCPClient("Client 2", self.root, 4, auto_send_feature=False)

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    App().run()