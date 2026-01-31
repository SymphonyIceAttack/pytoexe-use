import serial
import serial.tools.list_ports
import threading
import time
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

DB_FILE = "data.db"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_record(timestamp, value, max_records):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("INSERT INTO records (timestamp, value) VALUES (?, ?)",
              (timestamp, value))

    # Overwrite logic: keep only last N records
    c.execute("""
        DELETE FROM records
        WHERE id NOT IN (
            SELECT id FROM records
            ORDER BY id DESC
            LIMIT ?
        )
    """, (max_records,))

    conn.commit()
    conn.close()

# ---------------- SERIAL THREAD ----------------
class SerialReader(threading.Thread):
    def __init__(self, port, baud, max_records, status_callback):
        super().__init__(daemon=True)
        self.port = port
        self.baud = baud
        self.max_records = max_records
        self.status_callback = status_callback
        self.running = True
        self.ser = None

    def run(self):
        while self.running:
            try:
                if self.ser is None or not self.ser.is_open:
                    self.status_callback("Connecting...")
                    self.ser = serial.Serial(self.port, self.baud, timeout=1)
                    self.status_callback("Connected")

                line = self.ser.readline().decode(errors="ignore").strip()
                if line:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    insert_record(ts, line, self.max_records)
                    self.status_callback(f"Logged: {line}")

            except serial.SerialException:
                self.status_callback("Disconnected – retrying...")
                time.sleep(2)
            except Exception as e:
                self.status_callback(f"Error: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False
        try:
            if self.ser:
                self.ser.close()
        except:
            pass

# ---------------- GUI ----------------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Data Logger")
        self.reader = None

        ttk.Label(root, text="COM Port").grid(row=0, column=0, padx=5, pady=5)
        self.port_cb = ttk.Combobox(root, values=self.get_ports(), width=15)
        self.port_cb.grid(row=0, column=1)
        self.port_cb.current(0 if self.port_cb["values"] else -1)

        ttk.Label(root, text="Baud Rate").grid(row=1, column=0, padx=5, pady=5)
        self.baud_entry = ttk.Entry(root)
        self.baud_entry.insert(0, "9600")
        self.baud_entry.grid(row=1, column=1)

        ttk.Label(root, text="Max Records").grid(row=2, column=0, padx=5, pady=5)
        self.max_entry = ttk.Entry(root)
        self.max_entry.insert(0, "1000")
        self.max_entry.grid(row=2, column=1)

        self.start_btn = ttk.Button(root, text="Start", command=self.start)
        self.start_btn.grid(row=3, column=0, pady=10)

        self.stop_btn = ttk.Button(root, text="Stop", command=self.stop, state="disabled")
        self.stop_btn.grid(row=3, column=1)

        self.status = ttk.Label(root, text="Idle", relief="sunken", anchor="w")
        self.status.grid(row=4, column=0, columnspan=2, sticky="we", padx=5, pady=5)

    def get_ports(self):
        return [p.device for p in serial.tools.list_ports.comports()]

    def set_status(self, text):
        self.status.config(text=text)

    def start(self):
        try:
            port = self.port_cb.get()
            baud = int(self.baud_entry.get())
            max_records = int(self.max_entry.get())

            if not port:
                raise ValueError("No COM port selected")

            self.reader = SerialReader(
                port, baud, max_records, self.set_status
            )
            self.reader.start()

            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def stop(self):
        if self.reader:
            self.reader.stop()
            self.reader = None

        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.set_status("Stopped")

# ---------------- MAIN ----------------
if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    App(root)
    root.mainloop()
