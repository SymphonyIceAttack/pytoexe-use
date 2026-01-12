import sys
import os
import traceback

# ==================== ЗАЩИТА ОТ ЗАКРЫТИЯ ====================
# Если скрипт упадет, он не закроет окно, а покажет ошибку
def main_wrapper():
    try:
        real_main()
    except Exception as e:
        print("\n" + "="*50)
        print("!!! КРИТИЧЕСКАЯ ОШИБКА !!!")
        print(traceback.format_exc())
        print("="*50)
        input("Нажмите ENTER, чтобы закрыть окно...")

# ==================== ПРОВЕРКА ИМПОРТОВ ====================
try:
    import ctypes
    import threading
    import time
    import json
    import subprocess
    import shutil
    import uuid
    import logging
    from flask import Flask, request, jsonify
    import customtkinter as ctk
    import requests
    import minecraft_launcher_lib
except ImportError as e:
    print(f"ОШИБКА: Не установлена библиотека: {e.name}")
    print(f"Запустите командную строку от имени администратора и введите:")
    print(f"pip install flask minecraft-launcher-lib requests customtkinter")
    input("Нажмите Enter...")
    sys.exit()

# ==================== ПРАВА АДМИНИСТРАТОРА ====================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate():
    if not is_admin():
        print("Перезапуск с правами Администратора...")
        # Получаем полный путь к скрипту
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([script] + sys.argv[1:])
        
        # Запускаем через ShellExecute
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        except Exception as e:
            print(f"Не удалось получить права: {e}")
            input("Нажмите Enter...")
        sys.exit()

# ==================== НАСТРОЙКИ ПУТЕЙ ====================
# Важно! При запуске от админа, os.getcwd() может быть System32.
# Поэтому мы вычисляем папку, где лежит сам файл скрипта.
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GAME_DIR = os.path.join(BASE_DIR, 'minecraft_client')
DB_FILE = os.path.join(BASE_DIR, 'users.json')

CLIENT_TITLE = "Admin Launcher"
GAME_VERSION = "1.16.5"
SERVER_PORT = 5000
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"

# ==================== СЕРВЕР ====================
app_server = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def load_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

@app_server.route('/register', methods=['POST'])
def register():
    data = request.json
    users = load_db()
    if data['username'] in users:
        return jsonify({"status": "error", "message": "Логин занят"}), 400
    
    users[data['username']] = {"password": data['password'], "hwid": data['hwid']}
    save_db(users)
    return jsonify({"status": "success"})

@app_server.route('/login', methods=['POST'])
def login():
    data = request.json
    users = load_db()
    u = data['username']
    
    if u not in users: return jsonify({"message": "Пользователь не найден"}), 404
    if users[u]['password'] != data['password']: return jsonify({"message": "Неверный пароль"}), 401
    if users[u].get('hwid') != data['hwid']: return jsonify({"message": "HWID ошибка (Чужой ПК)"}), 403
    
    return jsonify({"status": "success"})

def run_server():
    try:
        app_server.run(port=SERVER_PORT, use_reloader=False)
    except OSError:
        print("Ошибка: Порт 5000 занят. Возможно лаунчер уже открыт.")

# ==================== GUI ====================
ctk.set_appearance_mode("Dark")

class Launcher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Administrator Launcher")
        self.geometry("350x450")
        
        self.label = ctk.CTkLabel(self, text="ADMIN ACCESS", font=("Impact", 24), text_color="red")
        self.label.pack(pady=20)

        self.user = ctk.CTkEntry(self, placeholder_text="Login")
        self.user.pack(pady=10)
        self.pwd = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.pwd.pack(pady=10)

        self.btn = ctk.CTkButton(self, text="LOGIN", command=lambda: self.auth(False), fg_color="red")
        self.btn.pack(pady=10)
        
        self.btn_reg = ctk.CTkButton(self, text="REGISTER", command=lambda: self.auth(True), fg_color="gray")
        self.btn_reg.pack(pady=5)

        self.status = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status.pack(side="bottom", pady=10)
        
        self.prog = ctk.CTkProgressBar(self)
        self.prog.pack_forget()

    def auth(self, is_reg):
        u, p = self.user.get(), self.pwd.get()
        if not u or not p: return
        
        endpoint = "register" if is_reg else "login"
        self.status.configure(text="Connecting...", text_color="yellow")
        
        def thread_func():
            try:
                hwid = str(uuid.getnode())
                res = requests.post(f"{SERVER_URL}/{endpoint}", json={"username": u, "password": p, "hwid": hwid})
                if res.status_code == 200:
                    self.status.configure(text="Success!", text_color="green")
                    if not is_reg: self.start_game(u)
                else:
                    msg = res.json().get("message", "Error")
                    self.status.configure(text=msg, text_color="red")
            except Exception as e:
                self.status.configure(text=f"Server Error: {e}", text_color="red")
        
        threading.Thread(target=thread_func).start()

    def start_game(self, username):
        if not shutil.which("java"):
            self.status.configure(text="Error: Java not installed!", text_color="red")
            return
        
        self.prog.pack(pady=10)
        
        def dl_call(c, m):
            if m > 0: self.prog.set(c/m)

        try:
            if not os.path.exists(GAME_DIR): os.makedirs(GAME_DIR)
            
            minecraft_launcher_lib.install.install_minecraft_version(
                versionid=GAME_VERSION, minecraft_directory=GAME_DIR, callback={'setProgress': dl_call}
            )
            
            opts = {"username": username, "uuid": str(uuid.uuid4()), "token": "", "launcherName": "AdminClient", "gameDirectory": GAME_DIR}
            cmd = minecraft_launcher_lib.command.get_minecraft_command(GAME_VERSION, GAME_DIR, opts)
            
            self.withdraw()
            subprocess.call(cmd)
            sys.exit()
        except Exception as e:
            self.deiconify()
            self.status.configure(text=f"Launch Error: {e}", text_color="red")
            print(traceback.format_exc())

# ==================== ТОЧКА ВХОДА ====================
def real_main():
    # 1. Сначала получаем админку
    elevate()
    
    print(f"Рабочая папка: {BASE_DIR}")
    print("Запуск сервера...")
    
    # 2. Запускаем сервер
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    
    # 3. GUI
    app = Launcher()
    app.mainloop()

if __name__ == "__main__":
    main_wrapper()