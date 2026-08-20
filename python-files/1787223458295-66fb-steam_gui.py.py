import tkinter as tk
from tkinter import messagebox, ttk
import threading
import steam
import steam.client
from steam.enums.emsg import EMsg
from steam.core.msg import MsgProto
from steam.protobufs import steammessages_clientserver_pb2 as client_pb2
import time
import sys

class SteamFarmApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Steam Idle Bot by Fox")
        self.root.geometry("400x350")
        self.root.resizable(False, False)
        
        # Переменные
        self.bot = None
        self.is_running = False
        
        # Интерфейс
        tk.Label(root, text="Логин Steam:", font=("Arial", 10)).pack(pady=5)
        self.entry_login = tk.Entry(root, width=40)
        self.entry_login.pack(pady=2)
        
        tk.Label(root, text="Пароль:", font=("Arial", 10)).pack(pady=5)
        self.entry_pass = tk.Entry(root, width=40, show="*")
        self.entry_pass.pack(pady=2)
        
        tk.Label(root, text="AppID игр (через запятую):", font=("Arial", 10)).pack(pady=5)
        self.entry_apps = tk.Entry(root, width=40)
        self.entry_apps.insert(0, "730, 570, 440")
        self.entry_apps.pack(pady=2)
        
        self.status_label = tk.Label(root, text="Статус: Ожидание", fg="gray", font=("Arial", 9))
        self.status_label.pack(pady=10)
        
        self.log_text = tk.Text(root, height=8, width=50, state=tk.DISABLED)
        self.log_text.pack(pady=5)
        
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)
        
        self.btn_start = tk.Button(btn_frame, text="Запустить фарм", command=self.start_farm, bg="#4CAF50", fg="white", width=15)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        
        self.btn_stop = tk.Button(btn_frame, text="Стоп", command=self.stop_farm, bg="#f44336", fg="white", width=15, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def start_farm(self):
        login = self.entry_login.get().strip()
        password = self.entry_pass.get().strip()
        apps_str = self.entry_apps.get().strip()
        
        if not login or not password:
            messagebox.showerror("Ошибка", "Введи логин и пароль!")
            return
            
        try:
            app_ids = [int(x.strip()) for x in apps_str.split(",") if x.strip()]
        except ValueError:
            messagebox.showerror("Ошибка", "AppID должны быть числами!")
            return

        self.is_running = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.status_label.config(text="Статус: Подключение...", fg="blue")
        
        # Запуск в отдельном потоке, чтобы интерфейс не завис
        thread = threading.Thread(target=self.run_bot, args=(login, password, app_ids))
        thread.daemon = True
        thread.start()

    def run_bot(self, login, password, app_ids):
        try:
            self.log(f"[INFO] Логинимся как {login}...")
            self.bot = steam.client.SteamClient()
            
            # Пробуем логин
            try:
                self.bot.login(login, password)
            except steam.exceptions.LoginError as e:
                if "email" in str(e).lower() or "auth_code" in str(e).lower():
                    # В реальном GUI сложно сделать input(), поэтому пока просто ошибка
                    # Для простоты оставим консольный ввод или сделаем через диалог в будущем
                    self.log("[ERROR] Требуется код с почты. Запусти консольную версию для первого входа.")
                    self.stop_farm_ui()
                    return
                else:
                    raise e
            
            self.log("[SUCCESS] Успешный логин!")
            self.status_label.config(text="Статус: Фарм идёт", fg="green")
            
            # Отправляем статус игры
            games_played = client_pb2.CMsgClientGamesPlayed()
            for app_id in app_ids:
                game = games_played.games_played.add()
                game.game_id = app_id
            
            self.bot.send(MsgProto(EMsg.ClientGamesPlayed), games_played)
            self.log(f"[OK] Запущен фарм {len(app_ids)} игр.")
            
            # Цикл поддержания соединения
            while self.is_running:
                self.bot.run_forever(timeout=1)
                time.sleep(1)
                
        except Exception as e:
            self.log(f"[ERROR] {e}")
            self.stop_farm_ui()

    def stop_farm(self):
        self.is_running = False
        if self.bot:
            try:
                games_played = client_pb2.CMsgClientGamesPlayed()
                self.bot.send(MsgProto(EMsg.ClientGamesPlayed), games_played)
                self.bot.disconnect()
            except:
                pass
        self.stop_farm_ui()
        self.log("[STOP] Фарм остановлен.")

    def stop_farm_ui(self):
        self.is_running = False
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.status_label.config(text="Статус: Остановлено", fg="gray")

if __name__ == "__main__":
    root = tk.Tk()
    app = SteamFarmApp(root)
    root.mainloop()