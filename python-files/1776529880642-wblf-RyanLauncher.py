import customtkinter as ctk
import minecraft_launcher_lib
import subprocess
import threading
import os
import uuid
import shutil
import sys
import urllib.request
import zipfile

# ==========================================
# КОНФИГУРАЦИЯ
# ==========================================
LAUNCHER_NAME = "RyanLauncher"
GAME_DIR = os.path.join(os.path.dirname(__file__), "minecraft_data")
MODS_DIR = os.path.join(GAME_DIR, "mods")
RUNTIME_DIR = os.path.join(GAME_DIR, "runtime") 

os.makedirs(MODS_DIR, exist_ok=True)
os.makedirs(RUNTIME_DIR, exist_ok=True)

# Список доступных версий
VERSIONS = ["1.16.5", "1.21.1", "1.21.4", "1.21.8", "1.21.11"]

RYAN_LOGO_ASCII = r"""
██████  ██    ██  █████  ███    ██
██   ██  ██  ██  ██   ██ ████   ██
██████    ████   ███████ ██ ██  ██
██   ██    ██    ██   ██ ██  ██ ██
██   ██    ██    ██   ██ ██   ████
    ██       █████  ██    ██ ███    ██  ██████ ██   ██ ███████ ██████
    ██      ██   ██ ██    ██ ████   ██ ██      ██   ██ ██      ██   ██
    ██      ███████ ██    ██ ██ ██  ██ ██      ███████ ███████ ██████
    ██      ██   ██ ██    ██ ██  ██ ██ \\      ██   ██ ██      ██   ██
    ███████ ██   ██  ██████  ██   ████  ██████ ██   ██ ███████ ██   ██
"""

ctk.set_appearance_mode("dark")

# --- ЛОГИКА ПОИСКА JAVA 21 ---
def check_is_java_21(java_path):
    try:
        out = subprocess.check_output([java_path, "-version"], stderr=subprocess.STDOUT).decode()
        return "21." in out or '"21"' in out
    except:
        return False

def get_local_java():
    if not os.path.exists(RUNTIME_DIR): return None
    for root, dirs, files in os.walk(RUNTIME_DIR):
        if "java.exe" in files:
            path = os.path.join(root, "java.exe")
            if check_is_java_21(path): return path
    return None

def find_system_java():
    sys_java = shutil.which("java")
    if sys_java and check_is_java_21(sys_java): return sys_java
        
    common_paths = [
        r"C:\Program Files\Java\jdk-21\bin\java.exe",
        r"C:\Program Files\Eclipse Adoptium\jdk-21.0.0-hotspot\bin\java.exe"
    ]
    for path in common_paths:
        if os.path.exists(path) and check_is_java_21(path): return path
    return None

# --- ИНТЕРФЕЙС ЛАУНЧЕРА ---
class RyanLauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title(LAUNCHER_NAME)
        w, h = 650, 600 # Сделал окно чуть выше для красивой панели
        self.geometry(f"{w}x{h}+{(self.winfo_screenwidth()-w)//2}+{(self.winfo_screenheight()-h)//2}")
        self.overrideredirect(True) 
        self.configure(fg_color="#010101")
        
        try: self.attributes("-transparentcolor", "#010101") 
        except: pass 

        self.container = ctk.CTkFrame(self, fg_color="#0a0a0a", corner_radius=20, border_width=2, border_color="#2a2a2a")
        self.container.pack(expand=True, fill="both", padx=10, pady=10)

        # Кнопка закрытия
        self.exit_btn = ctk.CTkButton(self.container, text="X", width=30, height=30, corner_radius=10, 
                                      fg_color="#ff3333", hover_color="#cc0000", command=self.destroy)
        self.exit_btn.place(relx=0.95, rely=0.05, anchor="center")

        # Логотип
        self.logo_lbl = ctk.CTkLabel(self.container, text=RYAN_LOGO_ASCII, 
                                     font=ctk.CTkFont(family="Courier New", size=8, weight="bold"), text_color="#00FF00")
        self.logo_lbl.pack(pady=(20, 10))
        
        # Перетаскивание окна
        for widget in [self.logo_lbl, self.container]:
            widget.bind("<Button-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.drag)

        # Ввод никнейма
        self.user_input = ctk.CTkEntry(self.container, placeholder_text="Enter Nickname", 
                                       width=300, height=45, corner_radius=15, justify="center")
        self.user_input.pack(pady=(15, 10))
        self.user_input.insert(0, "RyanPlayer")

        # ==========================================
        # 🎛️ КРАСИВАЯ ПАНЕЛЬ НАСТРОЕК
        # ==========================================
        self.panel = ctk.CTkFrame(self.container, fg_color="#151515", corner_radius=15, border_width=1, border_color="#333333")
        self.panel.pack(pady=10, fill="x", padx=60) # padx=60 делает панель не на всю ширину, а по центру
        
        # 1. Выбор версии
        self.version_var = ctk.StringVar(value=VERSIONS[2]) # По умолчанию 1.21.4
        self.version_menu = ctk.CTkOptionMenu(self.panel, variable=self.version_var, values=VERSIONS, 
                                              width=120, height=32, corner_radius=8,
                                              fg_color="#2b2b2b", button_color="#3b3b3b", button_hover_color="#4b4b4b", dropdown_fg_color="#2b2b2b")
        self.version_menu.pack(side="left", padx=15, pady=15)
        
        # 2. Выбор ОЗУ
        self.ram_var = ctk.StringVar(value="4G")
        self.ram_menu = ctk.CTkOptionMenu(self.panel, variable=self.ram_var, values=["2GB", "4GB", "6GB", "8GB"], 
                                          width=80, height=32, corner_radius=8,
                                          fg_color="#2b2b2b", button_color="#3b3b3b", button_hover_color="#4b4b4b", dropdown_fg_color="#2b2b2b")
        self.ram_menu.pack(side="left", padx=5, pady=15)

        # 3. Кнопка папки модов
        self.mods_btn = ctk.CTkButton(self.panel, text="📁 Mods", width=100, height=32, corner_radius=8,
                                      fg_color="#3b3b3b", hover_color="#555555", command=self.open_mods_folder)
        self.mods_btn.pack(side="right", padx=15, pady=15)
        # ==========================================

        # Статус и прогресс
        self.status = ctk.CTkLabel(self.container, text="READY TO INITIALIZE", 
                                   font=ctk.CTkFont(family="Consolas", size=12), text_color="#00FF00")
        self.status.pack(pady=(15, 5))

        self.progress = ctk.CTkProgressBar(self.container, width=400, height=10, progress_color="#00FF00")
        self.progress.set(0)
        self.progress.pack(pady=5)

        # Кнопка запуска
        self.launch_btn = ctk.CTkButton(self.container, text="LAUNCH GAME", command=self.start_launch_thread, 
                                        width=250, height=50, corner_radius=25, font=ctk.CTkFont(size=14, weight="bold"),
                                        fg_color="#00FF00", text_color="black", hover_color="#00CC00")
        self.launch_btn.pack(pady=20)

    # --- УТИЛИТЫ ---
    def open_mods_folder(self):
        os.makedirs(MODS_DIR, exist_ok=True) 
        if sys.platform == "win32": os.startfile(MODS_DIR)
        elif sys.platform == "darwin": subprocess.run(["open", MODS_DIR])
        else: subprocess.run(["xdg-open", MODS_DIR])

    def start_drag(self, e): self.x, self.y = e.x, e.y
    def drag(self, e):
        self.geometry(f"+{self.winfo_x() + (e.x - self.x)}+{self.winfo_y() + (e.y - self.y)}")

    def safe_log(self, text, color="#00FF00"):
        self.after(0, lambda: self.status.configure(text=text, text_color=color))

    def safe_btn_state(self, state):
        self.after(0, lambda: self.launch_btn.configure(state=state))

    def set_max_progress(self, max_val):
        self.max_prog = max_val

    def safe_progress(self, current):
        max_val = getattr(self, 'max_prog', 100)
        if max_val > 0: self.after(0, lambda: self.progress.set(current / max_val))

    def download_java(self):
        self.safe_log("DOWNLOADING PORTABLE JAVA 21...", "yellow")
        self.progress.set(0)
        
        java_url = "https://api.adoptium.net/v3/binary/latest/21/ga/windows/x64/jre/hotspot/normal/eclipse?project=jdk"
        zip_path = os.path.join(RUNTIME_DIR, "java21.zip")
        
        try:
            with urllib.request.urlopen(java_url) as response, open(zip_path, 'wb') as out_file:
                total_length = response.headers.get('content-length')
                if total_length: self.set_max_progress(int(total_length))
                
                downloaded = 0
                while True:
                    data = response.read(8192)
                    if not data: break
                    downloaded += len(data)
                    out_file.write(data)
                    if total_length: self.safe_progress(downloaded)
                    
            self.safe_log("EXTRACTING JAVA 21...", "yellow")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(RUNTIME_DIR)
                
            os.remove(zip_path)
            return get_local_java()
        except Exception as e:
            print(f"Java Download Error: {e}")
            return None

    # --- ЗАПУСК ---
    def start_launch_thread(self):
        if not self.user_input.get().strip(): return
        self.safe_btn_state("disabled")
        threading.Thread(target=self.launch_game, daemon=True).start()

    def launch_game(self):
        username = self.user_input.get().strip()
        ram = self.ram_var.get()
        selected_version = self.version_var.get() # <--- БЕРЕМ ВЕРСИЮ ИЗ МЕНЮ
        
        try:
            self.safe_log("CHECKING JAVA VERSION...", "yellow")
            java_path = get_local_java() or find_system_java()
            
            if not java_path:
                java_path = self.download_java()
                if not java_path: raise Exception("Failed to download Java 21!")

            # Установка выбранной версии
            self.safe_log(f"INSTALLING VANILLA {selected_version}...", "yellow")
            callbacks = {
                "setStatus": lambda text: self.safe_log(f"STATUS: {text[:40]}...", "yellow"),
                "setProgress": self.safe_progress,
                "setMax": self.set_max_progress
            }
            minecraft_launcher_lib.install.install_minecraft_version(selected_version, GAME_DIR, callback=callbacks)
            
            self.safe_log(f"INJECTING FABRIC FOR {selected_version}...", "yellow")
            minecraft_launcher_lib.fabric.install_fabric(selected_version, GAME_DIR)
            
            self.safe_log("PREPARING TO LAUNCH...", "yellow")
            installed = minecraft_launcher_lib.utils.get_installed_versions(GAME_DIR)
            
            # Ищем нужный Fabric профиль
            fabric_id = next((v['id'] for v in installed if "fabric" in v['id'] and selected_version in v['id']), None)
            
            if not fabric_id: raise Exception(f"Fabric installation failed for {selected_version}!")

            options = {
                "username": username,
                "uuid": str(uuid.uuid3(uuid.NAMESPACE_DNS, username)),
                "token": "0",
                "executablePath": java_path,
                "jvmArguments": [f"-Xmx{ram}"] 
            }
            
            command = minecraft_launcher_lib.command.get_minecraft_command(fabric_id, GAME_DIR, options)
            self.safe_log(f"STARTING {selected_version}!", "#00FF00")
            
            self.after(0, self.withdraw) 
            subprocess.run(command)
            
            self.after(0, self.deiconify) 
            self.safe_log("WELCOME BACK! READY TO PLAY.", "#00FF00")
            
        except Exception as e:
            self.safe_log(f"ERROR: {str(e)[:45]}", "#FF3333")
            print(f"Full error: {e}") 
        finally:
            self.safe_btn_state("normal")

if __name__ == "__main__":
    app = RyanLauncherApp()
    app.mainloop()