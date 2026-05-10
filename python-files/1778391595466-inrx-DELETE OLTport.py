# olt_auto_clean.py
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import time
import paramiko
import re

DEFAULT_USER = "muikadmin"
DEFAULT_PWD = "Muikadmin@123"

class SimpleOLTCleaner:
    def __init__(self, root):
        self.root = root
        root.title("OLT Auto Cleaner - Birlik QFY")
        root.geometry("800x600")

        # Katta matn maydoni - OLT ma'lumotlarini joylashtirish uchun
        tk.Label(root, text="OLT Ma'lumotlarini Shu Maydonga Joylashtiring:", font=("Arial", 10, "bold")).pack(pady=5)
        
        self.info_text = tk.Text(root, height=6, width=90, bg='lightyellow')
        self.info_text.pack(pady=5, padx=10, fill="x")
        self.info_text.insert("1.0", """JZZF-472-OLT_MA5800-X7_3 (OLT_Birlik_QFY) (10.40.149.132):1/14(18) 
(Абдураҳмон Жомий (Навқурон - 1) кўчаси(Бирлик қишлоғи) 18)
ORTIQCHA MATNLAR...""")
        
        # Extract tugmasi
        self.extract_btn = tk.Button(root, text="🔍 IP va Portni Ajratib Olish", command=self.extract_info, 
                                    bg="lightblue", font=("Arial", 10, "bold"))
        self.extract_btn.pack(pady=5)
        
        # Ajratilgan ma'lumotlar
        info_frame = tk.Frame(root)
        info_frame.pack(pady=10, fill="x", padx=10)
        
        tk.Label(info_frame, text="OLT IP:", font=("Arial", 10)).grid(row=0, column=0, sticky="w")
        self.ip_label = tk.Label(info_frame, text="❌ aniqlanmadi", fg="red", font=("Arial", 10, "bold"))
        self.ip_label.grid(row=0, column=1, sticky="w", padx=5)
        
        tk.Label(info_frame, text="GPON Port:", font=("Arial", 10)).grid(row=1, column=0, sticky="w")
        self.port_label = tk.Label(info_frame, text="❌ aniqlanmadi", fg="red", font=("Arial", 10, "bold"))
        self.port_label.grid(row=1, column=1, sticky="w", padx=5)
        
        tk.Label(info_frame, text="ONT ID:", font=("Arial", 10)).grid(row=2, column=0, sticky="w")
        self.ont_label = tk.Label(info_frame, text="❌ aniqlanmadi", fg="red", font=("Arial", 10, "bold"))
        self.ont_label.grid(row=2, column=1, sticky="w", padx=5)
        
        # Ulanish va tozalash tugmalari
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)
        
        self.connect_btn = tk.Button(btn_frame, text="🔌 OLTga Ulanish", command=self.connect_olt, 
                                    bg="green", fg="white", font=("Arial", 10, "bold"), state="disabled")
        self.connect_btn.pack(side="left", padx=5)
        
        self.clean_btn = tk.Button(btn_frame, text="🗑️ ONTni Tozalash", command=self.start_clean, 
                                  bg="red", fg="white", font=("Arial", 10, "bold"), state="disabled")
        self.clean_btn.pack(side="left", padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(root, length=700, mode='determinate')
        self.progress.pack(pady=10)
        
        # Log maydoni
        tk.Label(root, text="📋 Jarayon Logi:", font=("Arial", 10, "bold")).pack()
        self.log = scrolledtext.ScrolledText(root, height=15)
        self.log.pack(fill="both", expand=True, padx=10, pady=5)
        
        # SSH
        self.ssh = None
        self.shell = None
        self.olt_ip = None
        self.gpon_port = None
        self.ont_id = None
        
    def log_write(self, msg):
        """Log yozish"""
        self.log.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {msg}\n")
        self.log.see(tk.END)
        
    def extract_info(self):
        """Matndan IP va portni ajratib olish"""
        text = self.info_text.get("1.0", tk.END)
        
        # IP ni qidirish (10.40.149.132 format)
        ip_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        ip_match = re.search(ip_pattern, text)
        
        # Portni qidirish (1/14 yoki 1/14(18) format)
        port_pattern = r'(\d+/\d+)(?:\((\d+)\))?'
        port_match = re.search(port_pattern, text)
        
        if ip_match:
            self.olt_ip = ip_match.group(1)
            self.ip_label.config(text=self.olt_ip, fg="green")
            self.log_write(f"✅ OLT IP aniqlandi: {self.olt_ip}")
        else:
            self.ip_label.config(text="❌ topilmadi", fg="red")
            self.log_write("❌ OLT IP topilmadi!")
            return
            
        if port_match:
            self.gpon_port = port_match.group(1)
            self.port_label.config(text=self.gpon_port, fg="green")
            self.log_write(f"✅ GPON port aniqlandi: {self.gpon_port}")
            
            # ONT ID (qavs ichidagi raqam)
            if port_match.group(2):
                self.ont_id = port_match.group(2)
                self.ont_label.config(text=self.ont_id, fg="green")
                self.log_write(f"✅ ONT ID aniqlandi: {self.ont_id}")
            else:
                # Agar ONT ID bo'lmasa, so'rash
                self.ont_label.config(text="❓ kiritilmagan", fg="orange")
                self.log_write("⚠️ ONT ID topilmadi, qo'lda kiritishingiz kerak")
        else:
            self.port_label.config(text="❌ topilmadi", fg="red")
            self.log_write("❌ GPON port topilmadi!")
            return
            
        # Tugmalarni faollashtirish
        self.connect_btn.config(state="normal")
        
    def connect_olt(self):
        """OLTga ulanish"""
        if not self.olt_ip:
            self.log_write("❌ Avval IP ni aniqlang!")
            return
            
        self.log_write(f"🔌 {self.olt_ip} ga ulanish...")
        self.connect_btn.config(state="disabled")
        
        def _connect():
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(self.olt_ip, username=DEFAULT_USER, password=DEFAULT_PWD,
                              look_for_keys=False, allow_agent=False, timeout=10)
                
                self.shell = client.invoke_shell()
                time.sleep(1)
                self.shell.recv(65536)  # Bufferni tozalash
                
                self.ssh = client
                self.log_write("✅ OLTga ulanish muvaffaqiyatli!")
                self.root.after(0, lambda: self.clean_btn.config(state="normal"))
                
            except Exception as e:
                self.log_write(f"❌ Ulanish xatosi: {e}")
                self.root.after(0, lambda: self.connect_btn.config(state="normal"))
                
        threading.Thread(target=_connect, daemon=True).start()
        
    def send_cmd(self, cmd, wait_time=0.5):
        """Buyruq yuborish"""
        if self.shell:
            self.shell.send(cmd + "\n")
            time.sleep(wait_time)
            
    def read_output(self, timeout=3):
        """Chiqishni o'qish"""
        result = ""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.shell and self.shell.recv_ready():
                try:
                    result += self.shell.recv(65536).decode(errors="ignore")
                except:
                    pass
            time.sleep(0.1)
        return result
        
    def start_clean(self):
        """Tozalash jarayonini boshlash"""
        if not self.gpon_port or not self.ont_id:
            self.log_write("❌ Port yoki ONT ID aniqlanmagan!")
            return
            
        self.clean_btn.config(state="disabled")
        threading.Thread(target=self.clean_ont, daemon=True).start()
        
    def clean_ont(self):
        """ONT ni tozalash"""
        try:
            port_parts = self.gpon_port.split("/")
            iface = f"{port_parts[0]}/{port_parts[1]}"
            ont_idx = port_parts[2] if len(port_parts) > 2 else "1"
            
            self.log_write("🚀 Tozalash jarayoni boshlandi...")
            self.progress['value'] = 0
            
            # Enable
            self.log_write("🔧 Enable rejimiga o'tish...")
            self.send_cmd("enable")
            self.read_output()
            self.progress['value'] = 20
            
            # Config
            self.log_write("🔧 Config rejimiga o'tish...")
            self.send_cmd("config")
            self.read_output()
            self.progress['value'] = 40
            
            # Service-port ni o'chirish
            self.log_write(f"🗑️ Service-port o'chirilmoqda: {self.gpon_port} ONT {self.ont_id}")
            self.send_cmd(f"undo service-port port {self.gpon_port} ont {self.ont_id}")
            out = self.read_output()
            
            if "gemport" in out.lower():
                self.log_write("📌 Gemport tanlanmoqda...")
                self.send_cmd("gemport")
                self.read_output()
                self.send_cmd("1")
                self.read_output()
                
            self.progress['value'] = 60
            
            # GPON interface
            self.log_write(f"🔧 GPON interface {iface} ga o'tish...")
            self.send_cmd(f"interface gpon {iface}")
            self.read_output()
            self.progress['value'] = 80
            
            # ONT delete
            self.log_write(f"🗑️ ONT {ont_idx}/{self.ont_id} o'chirilmoqda...")
            self.send_cmd(f"ont delete {ont_idx} {self.ont_id}")
            out = self.read_output()
            
            if "success" in out.lower() or "delete" in out.lower():
                self.log_write("✅ ONT muvaffaqiyatli o'chirildi!")
            else:
                self.log_write("⚠️ ONT o'chirish holati noma'lum")
                
            # Quit
            self.send_cmd("quit")
            self.read_output()
            
            self.progress['value'] = 100
            self.log_write("✅ Tozalash jarayoni tugallandi!")
            
        except Exception as e:
            self.log_write(f"❌ Xatolik: {e}")
        finally:
            self.root.after(0, lambda: self.clean_btn.config(state="normal"))

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleOLTCleaner(root)
    root.mainloop()