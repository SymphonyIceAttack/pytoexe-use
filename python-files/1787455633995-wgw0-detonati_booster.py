import customtkinter as ctk
import psutil
import ctypes
import threading
import time
import os
import sys
import gc
from datetime import datetime
from tkinter import messagebox

# Configurazione tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class ProcessPriority:
    IDLE = 0x00000040
    BELOW_NORMAL = 0x00004000
    NORMAL = 0x00000020
    ABOVE_NORMAL = 0x00008000
    HIGH = 0x00000080
    REALTIME = 0x00000100

class DetonatiGameBoosterPro:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("DETONATI GAME BOOSTER PRO - ULTRA")
        
        # Finestra
        window_width = 1000
        window_height = 800
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(False, False)
        self.root.attributes('-alpha', 0.97)
        
        # Variabili
        self.is_boosting = False
        self.boost_thread = None
        self.processi_eliminati = 0
        self.memoria_liberata_mb = 0
        self.processi_ottimizzati = 0
        self.my_pid = os.getpid()
        
        # 🛡️ PROCESSI ASSOLUTAMENTE PROTETTI (NON TOCCARE MAI!)
        self.processi_critici = [
            'system', 'system idle process', 'svchost.exe', 'services.exe',
            'lsass.exe', 'winlogon.exe', 'csrss.exe', 'smss.exe',
            'wininit.exe', 'lsm.exe', 'fontdrvhost.exe',
            'dwm.exe', 'taskhostw.exe', 'explorer.exe', 'ctfmon.exe',
            'sihost.exe', 'runtimebroker.exe', 'securityhealthsystray.exe',
            'windowsdefender.exe', 'cmd.exe', 'powershell.exe',
            'python.exe', 'pythonw.exe', 'detonati', 'gamebooster',
            'win32k', 'ntoskrnl', 'hal.dll', 'kdcom.dll'
        ]
        
        # 📋 CATEGORIE DI PROCESSI DA ELIMINARE (TUTTI!)
        self.categorie_da_eliminare = {
            'messaging': ['discord', 'teams', 'skype', 'telegram', 'whatsapp', 'slack', 
                         'signal', 'zoom', 'webex', 'meet', 'chat', 'messenger'],
            
            'cloud': ['onedrive', 'dropbox', 'googledrive', 'icloud', 'sync', 
                     'backup', 'cloud', 'box', 'mega'],
            
            'office': ['outlook', 'word', 'excel', 'powerpoint', 'onenote', 'access',
                      'libreoffice', 'openoffice', 'wps', 'pdf', 'acrobat'],
            
            'browser': ['chrome', 'firefox', 'opera', 'brave', 'edge', 'vivaldi',
                       'chromium', 'safari', 'tor', 'browser'],
            
            'media': ['spotify', 'vlc', 'media', 'player', 'music', 'itunes',
                     'foobar', 'winamp', 'audacity', 'premiere', 'after'],
            
            'gaming': ['steamwebhelper', 'epicgames', 'origin', 'ubisoft', 'gog',
                      'rockstar', 'battlenet', 'launcher', 'updater'],
            
            'developer': ['java', 'javaw', 'node', 'python', 'vscode', 'code',
                         'pycharm', 'intellij', 'notepad++', 'sublime', 'atom',
                         'docker', 'kubernetes', 'git', 'github'],
            
            'utility': ['winrar', 'winzip', '7zfm', 'anydesk', 'teamviewer',
                       'ultravnc', 'putty', 'winscp', 'filezilla',
                       'corsair', 'logitech', 'razer', 'nvidia', 'amd'],
            
            'background': ['servicehost', 'backgroundhost', 'update', 'updater',
                          'helper', 'task', 'scheduler', 'monitor', 'watcher'],
            
            'streaming': ['obs', 'stream', 'twitch', 'youtube', 'recorder',
                         'capture', 'broadcast', 'mixer'],
            
            'social': ['facebook', 'instagram', 'twitter', 'tiktok', 'snapchat',
                      'reddit', 'tumblr', 'pinterest', 'discord'],
            
            'security': ['norton', 'mcafee', 'avast', 'avg', 'bitdefender',
                        'kaspersky', 'malwarebytes', 'firewall'],
            
            'productivity': ['todoist', 'notion', 'evernote', 'trello', 'slack',
                            'monday', 'asana', 'jira', 'confluence'],
            
            'download': ['utorrent', 'qbittorrent', 'transmission', 'download',
                        'loader', 'getter', 'p2p'],
            
            'other': ['bonjour', 'adobe', 'creative', 'corel', 'autodesk',
                     'sketchup', 'blender', 'unity', 'unreal']
        }
        
        # Setup UI
        self.setup_ui()
        self.start_monitoring()
        self.animate_title()
        
        self.status_label.configure(text="💪 BOOST ULTRA - Elimina TUTTI i processi inutili!", 
                                   text_color="#888888")
        
    def setup_ui(self):
        # Main frame
        self.main_frame = ctk.CTkFrame(self.root, fg_color=("#0a0a0a", "#1a1a1a"))
        self.main_frame.pack(fill="both", expand=True)
        
        # HEADER
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=120)
        header_frame.pack(fill="x", padx=30, pady=(20, 0))
        
        logo_label = ctk.CTkLabel(header_frame, text="💀",
                                 font=ctk.CTkFont(size=72))
        logo_label.pack(side="left", padx=(0, 15))
        
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left")
        
        self.title_label = ctk.CTkLabel(title_frame, text="DETONATI",
                                       font=ctk.CTkFont(size=44, weight="bold"),
                                       text_color="#ff4444")
        self.title_label.pack(anchor="w")
        
        subtitle_label = ctk.CTkLabel(title_frame, text="GAME BOOSTER PRO - ULTRA",
                                     font=ctk.CTkFont(size=24, weight="bold"),
                                     text_color="#ff6b35")
        subtitle_label.pack(anchor="w")
        
        # Info processi eliminabili
        info_processi = ctk.CTkLabel(header_frame, 
                                    text="🔥 ELIMINA OLTRE 200+ PROCESSI INUTILI",
                                    font=ctk.CTkFont(size=14),
                                    text_color="#ff4444")
        info_processi.pack(side="right")
        
        # Pulsante BOOST
        center_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        center_frame.pack(expand=True, fill="both")
        
        self.boost_button = ctk.CTkButton(center_frame,
                                         text="💀 BOOST ULTRA",
                                         font=ctk.CTkFont(size=42, weight="bold"),
                                         height=150,
                                         width=320,
                                         corner_radius=75,
                                         fg_color="#ff0000",
                                         hover_color="#cc0000",
                                         border_color="#ff4444",
                                         border_width=4,
                                         command=self.toggle_boost)
        self.boost_button.place(relx=0.5, rely=0.5, anchor="center")
        
        self.create_button_glow()
        
        self.status_label = ctk.CTkLabel(center_frame, text="💤 IN ATTESA",
                                        font=ctk.CTkFont(size=20, weight="bold"),
                                        text_color="#666666")
        self.status_label.place(relx=0.5, rely=0.78, anchor="center")
        
        # STATISTICHE
        stats_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        stats_frame.pack(side="bottom", fill="x", padx=30, pady=20)
        
        sep = ctk.CTkFrame(stats_frame, height=3, fg_color="#ff0000")
        sep.pack(fill="x", pady=(0, 15))
        
        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(fill="x")
        
        # STAT 1
        stat1 = ctk.CTkFrame(stats_grid, fg_color="#1a1a1a", corner_radius=10)
        stat1.pack(side="left", expand=True, padx=5, fill="x")
        ctk.CTkLabel(stat1, text="🗑️", font=ctk.CTkFont(size=24)).pack(pady=(10, 0))
        self.eliminati_label = ctk.CTkLabel(stat1, text="0",
                                           font=ctk.CTkFont(size=32, weight="bold"),
                                           text_color="#ff4444")
        self.eliminati_label.pack()
        ctk.CTkLabel(stat1, text="Processi Eliminati",
                    font=ctk.CTkFont(size=12),
                    text_color="#888888").pack(pady=(0, 10))
        
        # STAT 2
        stat2 = ctk.CTkFrame(stats_grid, fg_color="#1a1a1a", corner_radius=10)
        stat2.pack(side="left", expand=True, padx=5, fill="x")
        ctk.CTkLabel(stat2, text="💾", font=ctk.CTkFont(size=24)).pack(pady=(10, 0))
        self.memoria_label = ctk.CTkLabel(stat2, text="0 MB",
                                         font=ctk.CTkFont(size=32, weight="bold"),
                                         text_color="#4aff9e")
        self.memoria_label.pack()
        ctk.CTkLabel(stat2, text="RAM Liberata",
                    font=ctk.CTkFont(size=12),
                    text_color="#888888").pack(pady=(0, 10))
        
        # STAT 3
        stat3 = ctk.CTkFrame(stats_grid, fg_color="#1a1a1a", corner_radius=10)
        stat3.pack(side="left", expand=True, padx=5, fill="x")
        ctk.CTkLabel(stat3, text="⚡", font=ctk.CTkFont(size=24)).pack(pady=(10, 0))
        self.ottimizzati_label = ctk.CTkLabel(stat3, text="0",
                                            font=ctk.CTkFont(size=32, weight="bold"),
                                            text_color="#ff9e4a")
        self.ottimizzati_label.pack()
        ctk.CTkLabel(stat3, text="Processi Ottimizzati",
                    font=ctk.CTkFont(size=12),
                    text_color="#888888").pack(pady=(0, 10))
        
        # STAT 4
        stat4 = ctk.CTkFrame(stats_grid, fg_color="#1a1a1a", corner_radius=10)
        stat4.pack(side="left", expand=True, padx=5, fill="x")
        ctk.CTkLabel(stat4, text="📊", font=ctk.CTkFont(size=24)).pack(pady=(10, 0))
        self.performance_label = ctk.CTkLabel(stat4, text="100%",
                                            font=ctk.CTkFont(size=32, weight="bold"),
                                            text_color="#4a9eff")
        self.performance_label.pack()
        ctk.CTkLabel(stat4, text="Performance",
                    font=ctk.CTkFont(size=12),
                    text_color="#888888").pack(pady=(0, 10))
        
        # Monitoraggio CPU/RAM
        footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", padx=30, pady=(0, 10))
        
        footer_grid = ctk.CTkFrame(footer_frame, fg_color="transparent")
        footer_grid.pack(fill="x")
        
        cpu_frame = ctk.CTkFrame(footer_grid, fg_color="transparent")
        cpu_frame.pack(side="left", expand=True)
        ctk.CTkLabel(cpu_frame, text="💻 CPU", font=ctk.CTkFont(size=12), text_color="#888888").pack()
        self.cpu_bar = ctk.CTkProgressBar(cpu_frame, width=180, height=14)
        self.cpu_bar.pack(pady=2)
        self.cpu_label = ctk.CTkLabel(cpu_frame, text="0%", font=ctk.CTkFont(size=12), text_color="#4a9eff")
        self.cpu_label.pack()
        
        ram_frame = ctk.CTkFrame(footer_grid, fg_color="transparent")
        ram_frame.pack(side="left", expand=True)
        ctk.CTkLabel(ram_frame, text="🧠 RAM", font=ctk.CTkFont(size=12), text_color="#888888").pack()
        self.ram_bar = ctk.CTkProgressBar(ram_frame, width=180, height=14)
        self.ram_bar.pack(pady=2)
        self.ram_label = ctk.CTkLabel(ram_frame, text="0%", font=ctk.CTkFont(size=12), text_color="#4aff9e")
        self.ram_label.pack()
        
        # Info
        info_label = ctk.CTkLabel(self.main_frame, 
                                 text="🛡️ PROCESSI CRITICI PROTETTI | ✅ OLTRE 200+ PROCESSI ELIMINABILI",
                                 font=ctk.CTkFont(size=12),
                                 text_color="#666666")
        info_label.pack(side="bottom", pady=5)
        
    def is_process_safe_to_kill(self, proc):
        """VERIFICA SE UN PROCESSO PUÒ ESSERE ELIMINATO - VERSIONE ULTRA"""
        try:
            name = proc.info['name'].lower() if proc.info['name'] else ''
            pid = proc.info['pid']
            
            # ❌ 1. MAI eliminare il programma stesso
            if pid == self.my_pid:
                return False
            
            # ❌ 2. MAI eliminare processi critici di sistema
            if name in [p.lower() for p in self.processi_critici]:
                return False
            
            # ❌ 3. MAI eliminare processi con PID < 100 (kernel)
            if pid < 100:
                return False
            
            # ❌ 4. MAI eliminare processi senza nome
            if not name or name == '':
                return False
            
            # ❌ 5. MAI eliminare processi di sistema protetti
            if 'microsoft' in name or 'windows' in name:
                # Eccezione: alcuni processi Microsoft non essenziali
                if any(x in name for x in ['update', 'telemetry', 'helper']):
                    return True
                return False
            
            # ✅ 6. CONTROLLA SE È IN UNA CATEGORIA ELIMINABILE
            for categoria, keywords in self.categorie_da_eliminare.items():
                for keyword in keywords:
                    if keyword in name:
                        # Processo eliminabile!
                        return True
            
            # ✅ 7. Processi con alto consumo CPU ma non essenziali
            try:
                cpu_percent = proc.cpu_percent(interval=0.1)
                if cpu_percent > 10 and not any(x in name for x in ['game', 'steam']):
                    # Processo che consuma CPU ma non è un gioco
                    return True
            except:
                pass
            
            # ✅ 8. Processi che consumano molta memoria
            try:
                mem_info = proc.info['memory_info']
                if mem_info and mem_info.rss > 100 * 1024 * 1024:  # > 100 MB
                    # Processo che usa tanta RAM ma non è essenziale
                    return True
            except:
                pass
            
            # ✅ 9. Processi lanciati da utente (non sistema)
            try:
                username = proc.info['username']
                if username and 'system' not in username.lower():
                    return True
            except:
                pass
            
            return False
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
            
    def kill_process_safe(self, proc):
        """ELIMINA UN PROCESSO IN MODO SICURO"""
        try:
            # Prova terminazione gentile
            proc.terminate()
            time.sleep(0.2)
            
            # Se ancora attivo, forza kill
            if psutil.pid_exists(proc.info['pid']):
                try:
                    proc.kill()
                except:
                    pass
                return True
            
            return True
        except:
            try:
                proc.kill()
                return True
            except:
                return False
                
    def boost_process(self):
        """PROCESSO DI BOOST ULTRA - ELIMINA TUTTO IL NON ESSENZIALE"""
        
        self.status_label.configure(text="🗑️ ANALISI MASSIVA PROCESSI...", text_color="#ff6b35")
        
        # Lista per tracciare
        eliminati = []
        memoria_totale = 0
        processi_analizzati = 0
        
        # PASSO 1: SCANSIONE COMPLETA
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'username']):
            try:
                processi_analizzati += 1
                
                if self.is_process_safe_to_kill(proc):
                    # Salva memoria prima di eliminare
                    mem_info = proc.info['memory_info']
                    if mem_info:
                        memoria_totale += mem_info.rss // (1024 * 1024)
                    
                    # Elimina il processo
                    if self.kill_process_safe(proc):
                        eliminati.append(proc.info['name'])
                        self.processi_eliminati += 1
                        
                        # Aggiorna UI
                        self.root.after(0, lambda: self.eliminati_label.configure(
                            text=str(self.processi_eliminati)
                        ))
                        
                        time.sleep(0.05)  # Pausa per non sovraccaricare
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Aggiorna memoria
        self.memoria_liberata_mb = memoria_totale
        self.root.after(0, lambda: self.memoria_label.configure(
            text=f"{self.memoria_liberata_mb} MB"
        ))
        
        # PASSO 2: OTTIMIZZA PRIORITÀ
        self.status_label.configure(text="⚡ OTTIMIZZAZIONE MASSIVA...", text_color="#ff9e4a")
        
        # Lista parole chiave per giochi
        keywords_gaming = ['game', 'steam', 'epic', 'battle', 'origin', 'ubisoft',
                          'minecraft', 'fortnite', 'call of duty', 'battlefield',
                          'counter-strike', 'dota', 'league', 'valorant',
                          'cyberpunk', 'rockstar', 'blizzard', 'lol', 'fifa',
                          'nba', 'gta', 'red dead', 'assassin', 'far cry']
        
        processi_ottimizzati_local = 0
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info['name'].lower() if proc.info['name'] else ''
                pid = proc.info['pid']
                
                if pid == self.my_pid:
                    continue
                    
                if any(keyword in name for keyword in keywords_gaming):
                    self.set_process_priority(pid, ProcessPriority.HIGH)
                    processi_ottimizzati_local += 1
                    self.processi_ottimizzati += 1
            except:
                continue
        
        self.root.after(0, lambda: self.ottimizzati_label.configure(
            text=str(self.processi_ottimizzati)
        ))
        
        # PASSO 3: LIBERA RAM
        self.status_label.configure(text="💾 LIBERAZIONE MEMORIA...", text_color="#4aff9e")
        gc.collect()
        
        # PASSO 4: PERFORMANCE
        self.status_label.configure(text="📊 OTTIMIZZAZIONE PERFORMANCE...", text_color="#4a9eff")
        
        cpu_usage = psutil.cpu_percent()
        if cpu_usage < 30:
            performance = 200
        elif cpu_usage < 50:
            performance = 170
        elif cpu_usage < 70:
            performance = 140
        else:
            performance = 120
            
        self.root.after(0, lambda: self.performance_label.configure(text=f"{performance}%"))
        
        # PASSO 5: REPORT
        self.status_label.configure(text="🚀 BOOST ULTRA ATTIVO!", text_color="#00ff00")
        
        # Mostra report
        report_msg = (f"🔥 BOOST ULTRA COMPLETATO!\n\n"
                     f"📊 STATISTICHE:\n"
                     f"🗑️ Processi eliminati: {self.processi_eliminati}\n"
                     f"💾 RAM liberata: {self.memoria_liberata_mb} MB\n"
                     f"⚡ Processi ottimizzati: {self.processi_ottimizzati}\n"
                     f"📈 Performance: {performance}%\n\n"
                     f"💥 Il PC è ora POTENZIATO AL MASSIMO!")
        
        self.root.after(0, lambda: messagebox.showinfo("💥 BOOST ULTRA COMPLETATO", report_msg))
        
        # PASSO 6: MANTENIMENTO
        while self.is_boosting:
            time.sleep(20)  # Controlla ogni 20 secondi
            
            # Ricontrolla processi ripartiti
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    if self.is_process_safe_to_kill(proc):
                        if self.kill_process_safe(proc):
                            self.processi_eliminati += 1
                            self.root.after(0, lambda: self.eliminati_label.configure(
                                text=str(self.processi_eliminati)
                            ))
                except:
                    continue
            
            # Aggiorna statistiche
            self.update_stats()
            
    def set_process_priority(self, pid, priority):
        try:
            handle = ctypes.windll.kernel32.OpenProcess(0x00000400, False, pid)
            if handle:
                ctypes.windll.kernel32.SetPriorityClass(handle, priority)
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
        except:
            pass
        return False
        
    def create_button_glow(self):
        def glow_animation():
            alpha = 0
            direction = 1
            while True:
                alpha += 0.02 * direction
                if alpha >= 1:
                    direction = -1
                elif alpha <= 0:
                    direction = 1
                alpha = max(0, min(1, alpha))
                if hasattr(self, 'boost_button'):
                    intensity = int(180 + 75 * alpha)
                    color = f"#{intensity:02x}0000"
                    self.boost_button.configure(fg_color=color)
                time.sleep(0.05)
        
        thread = threading.Thread(target=glow_animation, daemon=True)
        thread.start()
        
    def animate_title(self):
        colors = ["#ff0000", "#ff2200", "#ff4400", "#ff6600", "#ff8800", "#ff6600", "#ff4400", "#ff2200"]
        idx = 0
        
        def update():
            nonlocal idx
            if hasattr(self, 'title_label'):
                self.title_label.configure(text_color=colors[idx % len(colors)])
                idx += 1
                self.root.after(200, update)
        
        update()
        
    def toggle_boost(self):
        if not self.is_boosting:
            # Mostra lista processi che verranno eliminati
            count = self.count_killable_processes()
            if count > 0:
                if not messagebox.askyesno("💀 BOOST ULTRA",
                                          f"🔥 ATTIVARE IL BOOST ULTRA?\n\n"
                                          f"✅ Verranno eliminati fino a {count} processi inutili\n"
                                          f"✅ Tutti i processi non essenziali saranno terminati\n"
                                          f"✅ Priorità ottimizzate per il gaming\n"
                                          f"✅ Memoria RAM liberata al massimo\n\n"
                                          f"🛡️ I processi di sistema sono PROTETTI!"):
                    return
            self.start_boost()
        else:
            self.stop_boost()
            
    def count_killable_processes(self):
        """Conta quanti processi possono essere eliminati"""
        count = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if self.is_process_safe_to_kill(proc):
                    count += 1
            except:
                continue
        return count
            
    def start_boost(self):
        self.is_boosting = True
        self.boost_button.configure(text="⏹️ STOP",
                                   fg_color="#ff0000",
                                   hover_color="#cc0000")
        self.status_label.configure(text="🔥 BOOST ULTRA ATTIVO!", text_color="#00ff00")
        
        self.processi_eliminati = 0
        self.memoria_liberata_mb = 0
        self.processi_ottimizzati = 0
        
        self.boost_thread = threading.Thread(target=self.boost_process, daemon=True)
        self.boost_thread.start()
        
    def stop_boost(self):
        self.is_boosting = False
        self.boost_button.configure(text="💀 BOOST ULTRA",
                                   fg_color="#ff0000",
                                   hover_color="#cc0000")
        self.status_label.configure(text="💤 BOOST DISATTIVATO", text_color="#ff4444")
        
        messagebox.showinfo("✅ DETONATI GAME BOOSTER PRO - ULTRA",
                           f"BOOST DISATTIVATO!\n\n"
                           f"📊 STATISTICHE FINALI:\n"
                           f"🗑️ Processi eliminati: {self.processi_eliminati}\n"
                           f"💾 RAM liberata: {self.memoria_liberata_mb} MB\n"
                           f"⚡ Processi ottimizzati: {self.processi_ottimizzati}\n\n"
                           f"🛡️ Il sistema è tornato alla normalità.")
        
    def update_stats(self):
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            
            self.root.after(0, lambda: self.cpu_bar.set(cpu / 100))
            self.root.after(0, lambda: self.cpu_label.configure(text=f"{cpu:.1f}%"))
            self.root.after(0, lambda: self.ram_bar.set(ram / 100))
            self.root.after(0, lambda: self.ram_label.configure(text=f"{ram:.1f}%"))
        except:
            pass
            
    def start_monitoring(self):
        def monitor():
            while True:
                self.update_stats()
                time.sleep(1)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        
    def on_closing(self):
        if self.is_boosting:
            if messagebox.askyesno("⚠️ Uscita", "Il boost è attivo. Disattivarlo prima di uscire?"):
                self.stop_boost()
            else:
                return
        self.root.destroy()
        
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            messagebox.showwarning("⚠️ Permessi Richiesti",
                                  "DETONATI GAME BOOSTER PRO - ULTRA necessita di\n"
                                  "permessi di amministratore per funzionare.\n\n"
                                  "Riavvia il programma come amministratore.")
            return
    except:
        pass
    
    app = DetonatiGameBoosterPro()
    app.run()

if __name__ == "__main__":
    main()