import customtkinter as ctk
import pydivert
import threading
import random
import time

# Default settings
LAG_MS = 390
PACKET_LOSS = 64

running = False
thread = None

def lag_loop():
    global running

    with pydivert.WinDivert("inbound") as w:
        while running:
            try:
                packet = w.recv()

                # Packet loss check
                if random.randint(1, 100) <= PACKET_LOSS:
                    continue

                # Lag
                time.sleep(LAG_MS / 1000.0)

                w.send(packet)

            except Exception:
                pass


def start():
    global running, thread
    if running:
        return

    running = True
    thread = threading.Thread(target=lag_loop, daemon=True)
    thread.start()


def stop():
    global running
    running = False


# UI
ctk.set_appearance_mode("dark")
app = ctk.CTk()
app.title("Inbound Lag Tool")
app.geometry("220x120")

start_btn = ctk.CTkButton(app, text="Start", command=start)
start_btn.pack(pady=15)

stop_btn = ctk.CTkButton(app, text="Stop", command=stop)
stop_btn.pack(pady=10)

app.mainloop()
