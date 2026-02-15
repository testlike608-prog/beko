import time 

# -------------------- LOG FUNCTION --------------------
def tcp_log_print(msg):
    print(msg, flush=True)
# -------------------- CONNECTION MONITOR --------------------
def _monitor_connections():
    """Checks both server connections and reconnects automatically."""
    global sock1, sock3, server1_connected, server3_connected, running

    while running:
        if server1_connected:
            try:
                sock1.send(b"ping")
            except Exception:
                tcp_log_print(" Lost connection to Server1, retrying...")
                server1_connected = False
                if sock1:
                    sock1.close()
                    sock1 = None

        if server3_connected:
            try:
                sock3.send(b"ping")
            except Exception:
                tcp_log_print(" Lost connection to Server2, retrying...")
                server3_connected = False
                if sock3:
                    sock3.close()
                    sock3 = None

        time.sleep(10)
