import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import os
import sys
import threading
import time
import re

class VRManager:
    def __init__(self, root):
        self.root = root
        self.root.title("VR Manager 1.0 - Meta Quest 3")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Imposta icona (se disponibile)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Variabili
        self.adb_path = self.find_adb()
        self.quest_ip = self.load_saved_ip()
        self.connected = False
        
        # Setup UI
        self.setup_styles()
        self.create_widgets()
        
        # Verifica ADB all'avvio
        if self.adb_path:
            self.check_adb()
        else:
            self.prompt_adb_path()
    
    def setup_styles(self):
        """Configura stili e colori"""
        self.bg_color = "#1a1a2e"
        self.fg_color = "#eeeeee"
        self.accent_color = "#0f3460"
        self.success_color = "#00b894"
        self.error_color = "#d63031"
        self.warning_color = "#f39c12"
        
        self.root.configure(bg=self.bg_color)
        
        # Font personalizzati
        self.title_font = ("Segoe UI", 16, "bold")
        self.header_font = ("Segoe UI", 12, "bold")
        self.normal_font = ("Segoe UI", 10)
    
    def create_widgets(self):
        """Crea tutti gli elementi dell'interfaccia"""
        
        # Frame principale con padding
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # ========== HEADER ==========
        header_frame = tk.Frame(main_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title = tk.Label(header_frame, text="VR MANAGER 1.0", 
                        font=self.title_font, fg=self.accent_color, bg=self.bg_color)
        title.pack()
        
        subtitle = tk.Label(header_frame, text="Meta Quest 3 - Wireless Control Panel", 
                           font=self.normal_font, fg=self.fg_color, bg=self.bg_color)
        subtitle.pack()
        
        # ========== SEZIONE CONNESSIONE ==========
        conn_frame = tk.LabelFrame(main_frame, text="Connessione Wireless", 
                                   font=self.header_font, bg=self.bg_color, 
                                   fg=self.fg_color, bd=2, relief=tk.GROOVE)
        conn_frame.pack(fill=tk.X, pady=(0, 15))
        
        # IP Input
        ip_frame = tk.Frame(conn_frame, bg=self.bg_color)
        ip_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(ip_frame, text="Quest IP:", font=self.normal_font, 
                bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT, padx=(0, 10))
        
        self.ip_var = tk.StringVar(value=self.quest_ip)
        self.ip_entry = tk.Entry(ip_frame, textvariable=self.ip_var, 
                                 font=self.normal_font, width=20, 
                                 bg="#2d2d44", fg=self.fg_color, insertbackground=self.fg_color)
        self.ip_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_ip_btn = tk.Button(ip_frame, text="Salva IP", command=self.save_ip,
                                     bg=self.accent_color, fg="white", font=self.normal_font,
                                     padx=10, cursor="hand2")
        self.save_ip_btn.pack(side=tk.LEFT)
        
        # Pulsanti connessione
        btn_frame = tk.Frame(conn_frame, bg=self.bg_color)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        self.connect_btn = tk.Button(btn_frame, text="🔌 Connetti Wireless", 
                                     command=self.connect_wireless,
                                     bg=self.success_color, fg="white", 
                                     font=self.normal_font, padx=15, pady=5, cursor="hand2")
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.fix_btn = tk.Button(btn_frame, text="🔧 Ripristino via Cavo", 
                                 command=self.fix_connection,
                                 bg=self.warning_color, fg="white", 
                                 font=self.normal_font, padx=15, pady=5, cursor="hand2")
        self.fix_btn.pack(side=tk.LEFT)
        
        self.status_label = tk.Label(conn_frame, text="⚪ Non connesso", 
                                     bg=self.bg_color, fg=self.warning_color, 
                                     font=self.normal_font)
        self.status_label.pack(pady=(0, 10))
        
        # ========== SEZIONE STRUMENTI ==========
        tools_frame = tk.LabelFrame(main_frame, text="Strumenti Quest 3", 
                                    font=self.header_font, bg=self.bg_color,
                                    fg=self.fg_color, bd=2, relief=tk.GROOVE)
        tools_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Riga 1 - Risoluzione
        row1 = tk.Frame(tools_frame, bg=self.bg_color)
        row1.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(row1, text="Risoluzione", font=self.normal_font, 
                bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT, padx=(0, 20))
        
        self.res_var = tk.StringVar(value="Default (1728x1824)")
        res_menu = ttk.Combobox(row1, textvariable=self.res_var, 
                                 values=["Default (1728x1824)", "HD (2048x2048)", 
                                         "2K (2560x2560)", "Custom"], 
                                 width=25, state="readonly")
        res_menu.pack(side=tk.LEFT, padx=(0, 10))
        res_menu.bind("<<ComboboxSelected>>", self.on_res_change)
        
        self.apply_res_btn = tk.Button(row1, text="Applica Risoluzione", 
                                       command=self.apply_resolution,
                                       bg=self.accent_color, fg="white",
                                       font=self.normal_font, padx=10, cursor="hand2")
        self.apply_res_btn.pack(side=tk.LEFT)
        
        # Riga 2 - Refresh Rate
        row2 = tk.Frame(tools_frame, bg=self.bg_color)
        row2.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(row2, text="Refresh Rate", font=self.normal_font,
                bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT, padx=(0, 20))
        
        self.hz_var = tk.StringVar(value="72 Hz")
        hz_menu = ttk.Combobox(row2, textvariable=self.hz_var,
                               values=["72 Hz", "80 Hz", "90 Hz", "120 Hz"],
                               width=25, state="readonly")
        hz_menu.pack(side=tk.LEFT, padx=(0, 10))
        
        self.apply_hz_btn = tk.Button(row2, text="Applica Refresh Rate", 
                                      command=self.apply_refresh_rate,
                                      bg=self.accent_color, fg="white",
                                      font=self.normal_font, padx=10, cursor="hand2")
        self.apply_hz_btn.pack(side=tk.LEFT)
        
        # Riga 3 - CPU/GPU Level
        row3 = tk.Frame(tools_frame, bg=self.bg_color)
        row3.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(row3, text="Performance Mode", font=self.normal_font,
                bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT, padx=(0, 20))
        
        self.perf_var = tk.StringVar(value="Normal")
        perf_menu = ttk.Combobox(row3, textvariable=self.perf_var,
                                 values=["Normal", "Performance (CPU/GPU)", 
                                         "Power Saving", "Extreme (4/5)"],
                                 width=25, state="readonly")
        perf_menu.pack(side=tk.LEFT, padx=(0, 10))
        
        self.apply_perf_btn = tk.Button(row3, text="Applica Profilo", 
                                        command=self.apply_performance,
                                        bg=self.accent_color, fg="white",
                                        font=self.normal_font, padx=10, cursor="hand2")
        self.apply_perf_btn.pack(side=tk.LEFT)
        
        # Separatore
        separator = ttk.Separator(tools_frame, orient='horizontal')
        separator.pack(fill=tk.X, padx=15, pady=10)
        
        # Riga 4 - Screenshot e APK
        row4 = tk.Frame(tools_frame, bg=self.bg_color)
        row4.pack(fill=tk.X, padx=15, pady=10)
        
        self.screenshot_btn = tk.Button(row4, text="📸 Screenshot", 
                                        command=self.take_screenshot,
                                        bg=self.accent_color, fg="white",
                                        font=self.normal_font, padx=15, cursor="hand2")
        self.screenshot_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.install_btn = tk.Button(row4, text="📦 Installa APK", 
                                     command=self.install_apk,
                                     bg=self.accent_color, fg="white",
                                     font=self.normal_font, padx=15, cursor="hand2")
        self.install_btn.pack(side=tk.LEFT)
        
        # Riga 5 - SideQuest
        row5 = tk.Frame(tools_frame, bg=self.bg_color)
        row5.pack(fill=tk.X, padx=15, pady=10)
        
        self.sidequest_btn = tk.Button(row5, text="🎮 Avvia SideQuest (Wireless)", 
                                       command=self.start_sidequest,
                                       bg="#6c5ce7", fg="white",
                                       font=self.normal_font, padx=15, pady=5, cursor="hand2")
        self.sidequest_btn.pack(side=tk.LEFT)
        
        # ========== LOG CONSOLE ==========
        log_frame = tk.LabelFrame(main_frame, text="Console", 
                                  font=self.header_font, bg=self.bg_color,
                                  fg=self.fg_color, bd=2, relief=tk.GROOVE)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=8, bg="#0d0d1a", 
                                fg="#0f0", font=("Consolas", 9),
                                insertbackground=self.fg_color)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar per log
        scrollbar = tk.Scrollbar(self.log_text, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Pulsante clear log
        clear_btn = tk.Button(main_frame, text="Pulisci Log", command=self.clear_log,
                              bg="#333", fg="white", font=self.normal_font, cursor="hand2")
        clear_btn.pack(pady=(5, 0))
        
        # Barra di stato in basso
        self.status_bar = tk.Label(self.root, text="Pronto", bd=1, relief=tk.SUNKEN,
                                   anchor=tk.W, bg="#2d2d44", fg=self.fg_color)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def log(self, message, type="info"):
        """Aggiunge un messaggio al log con colore"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            "info": "#0f0",
            "error": "#f44",
            "warning": "#fc4",
            "success": "#4f8"
        }
        
        self.log_text.insert(tk.END, f"[{timestamp}] ", colors["info"])
        self.log_text.insert(tk.END, f"{message}\n", colors.get(type, "#fff"))
        self.log_text.see(tk.END)
        self.root.update()
    
    def find_adb(self):
        """Cerca ADB nelle posizioni comuni"""
        paths = [
            os.path.join(os.path.dirname(sys.argv[0]), "platform-tools", "adb.exe"),
            os.path.join(os.path.dirname(sys.argv[0]), "adb.exe"),
            r"C:\platform-tools\adb.exe",
            os.path.join(os.environ.get("USERPROFILE", ""), "Downloads", "platform-tools", "adb.exe"),
            os.path.join(os.environ.get("USERPROFILE", ""), "Desktop", "platform-tools", "adb.exe"),
            "adb.exe"  # spera che sia nel PATH
        ]
        
        for path in paths:
            if os.path.exists(path):
                self.log(f"ADB trovato: {path}", "success")
                return path
        
        self.log("ADB non trovato!", "error")
        return None
    
    def prompt_adb_path(self):
        """Chiede all'utente il percorso di ADB"""
        path = filedialog.askopenfilename(
            title="Seleziona adb.exe",
            filetypes=[("Executable", "adb.exe"), ("All Files", "*.*")]
        )
        if path and os.path.exists(path):
            self.adb_path = path
            self.log(f"ADB impostato manualmente: {path}", "success")
            self.check_adb()
        else:
            messagebox.showerror("Errore", "ADB non trovato! Scarica Platform Tools da:\n"
                                           "https://developer.android.com/studio/releases/platform-tools")
    
    def load_saved_ip(self):
        """Carica IP salvato"""
        config_path = os.path.join(os.path.dirname(sys.argv[0]), "quest_ip.txt")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return f.read().strip()
        return ""
    
    def save_ip(self):
        """Salva IP corrente"""
        ip = self.ip_var.get().strip()
        if ip:
            config_path = os.path.join(os.path.dirname(sys.argv[0]), "quest_ip.txt")
            with open(config_path, "w") as f:
                f.write(ip)
            self.quest_ip = ip
            self.log(f"IP salvato: {ip}", "success")
            self.status_bar.config(text=f"IP salvato: {ip}")
    
    def run_adb(self, command, timeout=10):
        """Esegue un comando ADB e ritorna l'output"""
        if not self.adb_path:
            self.log("ADB non disponibile!", "error")
            return None, "ADB not found"
        
        full_cmd = f'"{self.adb_path}" {command}'
        try:
            result = subprocess.run(full_cmd, shell=True, capture_output=True, 
                                   text=True, timeout=timeout)
            return result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            self.log(f"Timeout: {command}", "warning")
            return None, "Timeout"
        except Exception as e:
            self.log(f"Errore: {e}", "error")
            return None, str(e)
    
    def check_adb(self):
        """Verifica che ADB funzioni"""
        stdout, stderr = self.run_adb("version")
        if stdout and "Android Debug Bridge" in stdout:
            self.log("ADB funzionante!", "success")
            self.status_bar.config(text="ADB pronto")
            return True
        else:
            self.log("Problemi con ADB!", "error")
            self.status_bar.config(text="ADB non disponibile")
            return False
    
    def connect_wireless(self):
        """Connessione wireless al Quest"""
        ip = self.ip_var.get().strip()
        if not ip:
            messagebox.showwarning("Attenzione", "Inserisci l'IP del Quest!")
            return
        
        self.status_bar.config(text=f"Connessione a {ip}:5555...")
        self.log(f"Connessione a {ip}:5555...", "info")
        
        def connect():
            self.connect_btn.config(state=tk.DISABLED, text="🔄 Connessione...")
            stdout, stderr = self.run_adb(f"connect {ip}:5555")
            
            if stdout and ("connected" in stdout.lower() or "already connected" in stdout.lower()):
                self.connected = True
                self.status_label.config(text="✅ Connesso wireless", fg=self.success_color)
                self.log(f"Connesso a {ip}:5555", "success")
                self.status_bar.config(text=f"Connesso a {ip}")
                
                # Verifica dispositivi
                devices, _ = self.run_adb("devices")
                self.log(f"Dispositivi:\n{devices}", "info")
            else:
                self.log(f"Connessione fallita: {stdout or stderr}", "error")
                self.status_bar.config(text="Connessione fallita - prova ripristino via cavo")
                messagebox.showwarning("Connessione fallita", 
                                      "Connessione wireless fallita.\n"
                                      "Usa 'Ripristino via Cavo' per abilitare la modalita wireless.")
            
            self.connect_btn.config(state=tk.NORMAL, text="🔌 Connetti Wireless")
        
        threading.Thread(target=connect, daemon=True).start()
    
    def fix_connection(self):
        """Ripristina connessione via cavo e abilita wireless"""
        self.log("Avvio ripristino via cavo...", "warning")
        messagebox.showinfo("Ripristino", 
                           "1. Collega il cavo USB al Quest\n"
                           "2. Premi OK\n\n"
                           "Il tool abilitera la connessione wireless.")
        
        def fix():
            self.fix_btn.config(state=tk.DISABLED, text="🔄 Ripristino...")
            
            # kill-server e start-server
            self.run_adb("kill-server")
            time.sleep(1)
            self.run_adb("start-server")
            
            # Abilita TCPIP
            stdout, stderr = self.run_adb("tcpip 5555")
            self.log(f"TCPIP: {stdout}", "info")
            
            # Pausa per scollegare (chiede all'utente)
            self.root.after(0, lambda: messagebox.showinfo("Ora scollega", 
                                                          "Scollega il cavo USB dal Quest e premi OK"))
            
            time.sleep(3)
            
            # Riconnetti wireless
            ip = self.ip_var.get().strip()
            if ip:
                stdout, stderr = self.run_adb(f"connect {ip}:5555")
                self.log(f"Riconnessione: {stdout}", "info")
                
                if stdout and "connected" in stdout.lower():
                    self.connected = True
                    self.status_label.config(text="✅ Connesso wireless", fg=self.success_color)
                    self.log("Ripristino completato!", "success")
            
            self.fix_btn.config(state=tk.NORMAL, text="🔧 Ripristino via Cavo")
        
        threading.Thread(target=fix, daemon=True).start()
    
    def apply_resolution(self):
        """Applica nuova risoluzione"""
        if not self.connected:
            messagebox.showwarning("Attenzione", "Connetti prima il Quest!")
            return
        
        res = self.res_var.get()
        res_map = {
            "Default (1728x1824)": "1728 1824",
            "HD (2048x2048)": "2048 2048",
            "2K (2560x2560)": "2560 2560"
        }
        
        if res in res_map:
            w, h = res_map[res].split()
            cmd = f"shell setprop debug.oculus.textureWidth {w} && shell setprop debug.oculus.textureHeight {h}"
        elif res == "Custom":
            dialog = tk.Toplevel(self.root)
            dialog.title("Risoluzione Custom")
            dialog.geometry("300x150")
            dialog.configure(bg=self.bg_color)
            
            tk.Label(dialog, text="Larghezza:", bg=self.bg_color, fg=self.fg_color).pack(pady=5)
            w_entry = tk.Entry(dialog)
            w_entry.pack(pady=5)
            tk.Label(dialog, text="Altezza:", bg=self.bg_color, fg=self.fg_color).pack(pady=5)
            h_entry = tk.Entry(dialog)
            h_entry.pack(pady=5)
            
            def apply_custom():
                w = w_entry.get()
                h = h_entry.get()
                if w and h:
                    self.run_adb(f"shell setprop debug.oculus.textureWidth {w}")
                    self.run_adb(f"shell setprop debug.oculus.textureHeight {h}")
                    self.log(f"Risoluzione custom applicata: {w}x{h}", "success")
                    dialog.destroy()
            
            tk.Button(dialog, text="Applica", command=apply_custom, bg=self.success_color, fg="white").pack(pady=10)
            return
        
        stdout, stderr = self.run_adb(cmd)
        self.log(f"Risoluzione applicata: {res}", "success" if "error" not in str(stderr).lower() else "error")
    
    def apply_refresh_rate(self):
        """Applica refresh rate"""
        if not self.connected:
            messagebox.showwarning("Attenzione", "Connetti prima il Quest!")
            return
        
        hz = self.hz_var.get().replace(" Hz", "")
        cmd = f"shell setprop debug.oculus.refreshRate {hz}"
        stdout, stderr = self.run_adb(cmd)
        self.log(f"Refresh rate impostato a {hz}Hz", "success" if "error" not in str(stderr).lower() else "error")
    
    def apply_performance(self):
        """Applica profilo performance"""
        if not self.connected:
            messagebox.showwarning("Attenzione", "Connetti prima il Quest!")
            return
        
        profile = self.perf_var.get()
        perf_map = {
            "Normal": "0",
            "Performance (CPU/GPU)": "1",
            "Power Saving": "2",
            "Extreme (4/5)": "4 5"
        }
        
        if "Extreme" in profile:
            cmd = "shell setprop debug.oculus.cpuLevel 4 && shell setprop debug.oculus.gpuLevel 5"
        else:
            level = perf_map[profile]
            cmd = f"shell setprop debug.oculus.cpuLevel {level} && shell setprop debug.oculus.gpuLevel {level}"
        
        stdout, stderr = self.run_adb(cmd)
        self.log(f"Profilo performance: {profile}", "success")
    
    def take_screenshot(self):
        """Fai screenshot e salva"""
        if not self.connected:
            messagebox.showwarning("Attenzione", "Connetti prima il Quest!")
            return
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quest_screenshot_{timestamp}.png"
        
        self.log("Salvataggio screenshot...", "info")
        stdout, stderr = self.run_adb(f"exec-out screencap -p > {filename}")
        
        if os.path.exists(filename):
            self.log(f"Screenshot salvato: {filename}", "success")
            self.status_bar.config(text=f"Screenshot salvato: {filename}")
        else:
            self.log("Errore durante lo screenshot", "error")
    
    def install_apk(self):
        """Installa un APK sul Quest"""
        if not self.connected:
            messagebox.showwarning("Attenzione", "Connetti prima il Quest!")
            return
        
        file_path = filedialog.askopenfilename(
            title="Seleziona APK da installare",
            filetypes=[("APK files", "*.apk"), ("All files", "*.*")]
        )
        
        if file_path:
            self.log(f"Installazione di {os.path.basename(file_path)}...", "info")
            
            def install():
                self.install_btn.config(state=tk.DISABLED, text="🔄 Installazione...")
                stdout, stderr = self.run_adb(f'install "{file_path}"', timeout=60)
                
                if "Success" in stdout:
                    self.log(f"APK installato con successo!", "success")
                else:
                    self.log(f"Errore installazione: {stdout}", "error")
                
                self.install_btn.config(state=tk.NORMAL, text="📦 Installa APK")
            
            threading.Thread(target=install, daemon=True).start()
    
    def start_sidequest(self):
        """Avvia SideQuest (se installato)"""
        # Cerca SideQuest in posizioni comuni
        sq_paths = [
            r"C:\Program Files\SideQuest\SideQuest.exe",
            r"C:\Users\%USERNAME%\AppData\Local\Programs\sidequest\SideQuest.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "sidequest", "SideQuest.exe")
        ]
        
        sq_path = None
        for path in sq_paths:
            expanded = os.path.expandvars(path)
            if os.path.exists(expanded):
                sq_path = expanded
                break
        
        if sq_path:
            self.log("Avvio SideQuest...", "info")
            subprocess.Popen([sq_path], shell=True)
            self.status_bar.config(text="SideQuest avviato")
        else:
            result = messagebox.askyesno("SideQuest non trovato", 
                                        "SideQuest non sembra essere installato sul PC.\n"
                                        "Vuoi aprire il sito per scaricarlo?")
            if result:
                import webbrowser
                webbrowser.open("https://sidequestvr.com/download")
    
    def on_res_change(self, event):
        """Quando cambia selezione risoluzione"""
        if self.res_var.get() == "Custom":
            # custom sarà gestito nel apply
            pass
    
    def clear_log(self):
        """Pulisce la console"""
        self.log_text.delete(1.0, tk.END)
        self.log("Log pulito", "info")


def main():
    root = tk.Tk()
    app = VRManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()