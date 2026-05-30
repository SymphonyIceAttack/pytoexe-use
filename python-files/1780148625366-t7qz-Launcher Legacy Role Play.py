import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import os
import json
import threading
import socket
import struct
import webbrowser
import sys

# КОНФИГУРАЦИЯ СЕРВЕРОВ
SERVERS = {
    "1": {
        "name": "Legacy Server 1",
        "ip": "188.127.241.74",
        "port": 4801,
        "max_players": 500,
        "color": "#e74c3c"
    },
    "2": {
        "name": "Legacy Server 2",
        "ip": "188.127.241.74",
        "port": 1557,
        "max_players": 500,
        "color": "#3498db"
    }
}

CONFIG_FILE = "launcher_config.json"
SAMP_DOWNLOAD_URL = "https://adv-rp.com/"

class RealSAMPQuery:
    """Реальный подсчет игроков через список игроков"""
    
    @staticmethod
    def get_real_players(ip, port, timeout=3):
        # Метод 1: Запрос списка игроков (100% реальный онлайн)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            packet = b'SAMP' + socket.inet_aton(ip) + struct.pack('<H', port) + b'\x63'
            sock.sendto(packet, (ip, port))
            data, _ = sock.recvfrom(4096)
            
            if len(data) > 12:
                player_count = struct.unpack('<H', data[11:13])[0]
                sock.close()
                return player_count, 500
            sock.close()
        except:
            pass
        
        # Метод 2: Стандартный запрос
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            packet = b'SAMP' + socket.inet_aton(ip) + struct.pack('<H', port) + b'\x69'
            sock.sendto(packet, (ip, port))
            data, _ = sock.recvfrom(2048)
            
            if len(data) > 11:
                online = struct.unpack('<H', data[11:13])[0]
                max_players = struct.unpack('<H', data[13:15])[0]
                sock.close()
                return online, max_players
            sock.close()
            return 0, 500
        except:
            return 0, 500

class Launcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Legacy Role Play Launcher")
        self.root.geometry("1300x850")
        self.root.minsize(1200, 700)
        self.root.configure(bg="#0a0a0a")
        
        # Загрузка настроек
        self.load_config()
        self.minimize_on_launch = tk.BooleanVar(value=self.config.get("minimize_on_launch", True))
        
        # Создание интерфейса
        self.create_widgets()
        
        # Запуск обновления онлайна
        self.update_all_online()
        
        self.center_window()
    
    def load_config(self):
        default = {
            "samp_path": r"C:\Program Files (x86)\Rockstar Games\GTA San Andreas\samp.exe",
            "minimize_on_launch": True
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = {**default, **json.load(f)}
            except:
                self.config = default
        else:
            self.config = default
        self.samp_path = self.config["samp_path"]
    
    def save_config(self):
        self.config["samp_path"] = self.samp_path
        self.config["minimize_on_launch"] = self.minimize_on_launch.get()
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Успех", "Настройки сохранены!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")
    
    def center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')
    
    def browse_samp(self):
        file_path = filedialog.askopenfilename(
            title="Выберите samp.exe",
            filetypes=[("SAMP Executable", "samp.exe")],
            initialdir="C:\\Program Files (x86)\\Rockstar Games\\GTA San Andreas"
        )
        if file_path:
            self.samp_path = file_path
            self.path_var.set(file_path)
    
    def open_forum(self):
        webbrowser.open("https://legacyrprprp.sampproject.ru/index.php")
    
    def download_samp(self):
        webbrowser.open(SAMP_DOWNLOAD_URL)
    
    def create_widgets(self):
        # Верхняя панель
        top_bar = tk.Frame(self.root, bg="#111111", height=80)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)
        
        # Логотип
        logo_frame = tk.Frame(top_bar, bg="#111111")
        logo_frame.pack(side="left", padx=40, pady=15)
        
        tk.Label(
            logo_frame,
            text="LEGACY",
            font=("Helvetica", 32, "bold"),
            fg="#e74c3c",
            bg="#111111"
        ).pack(side="left")
        
        tk.Label(
            logo_frame,
            text="RP",
            font=("Helvetica", 32, "bold"),
            fg="white",
            bg="#111111"
        ).pack(side="left")
        
        # Кнопка форума
        forum_btn = tk.Button(
            top_bar,
            text="ФОРУМ",
            command=self.open_forum,
            font=("Segoe UI", 10, "bold"),
            bg="#9b59b6",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8
        )
        forum_btn.pack(side="right", padx=(0, 20))
        
        # Статус
        status_frame = tk.Frame(top_bar, bg="#111111")
        status_frame.pack(side="right", padx=(0, 20))
        
        online_dot = tk.Canvas(status_frame, width=10, height=10, bg="#111111", highlightthickness=0)
        online_dot.pack(side="left", padx=(0, 8))
        online_dot.create_oval(1, 1, 9, 9, fill="#2ecc71", outline="")
        
        tk.Label(
            status_frame,
            text="ГОТОВ К ЗАПУСКУ",
            font=("Segoe UI", 10, "bold"),
            fg="#2ecc71",
            bg="#111111"
        ).pack(side="left")
        
        # Линия разделения
        line = tk.Frame(self.root, bg="#1a1a1a", height=2)
        line.pack(fill="x")
        
        # Основной контейнер
        main_container = tk.Frame(self.root, bg="#0a0a0a")
        main_container.pack(fill="both", expand=True, padx=40, pady=30)
        
        # ЛЕВАЯ ПАНЕЛЬ - Сервера
        left_panel = tk.Frame(main_container, bg="#0a0a0a")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 30))
        
        # Заголовок
        tk.Label(
            left_panel,
            text="ДОСТУПНЫЕ СЕРВЕРА",
            font=("Segoe UI", 16, "bold"),
            fg="white",
            bg="#0a0a0a"
        ).pack(anchor="w", pady=(0, 20))
        
        # Карточки серверов
        self.server_cards = {}
        for server_id, server_info in SERVERS.items():
            self.create_server_card(left_panel, server_id, server_info)
        
        # ПРАВАЯ ПАНЕЛЬ - Информация и настройки
        right_panel = tk.Frame(main_container, bg="#0a0a0a", width=420)
        right_panel.pack(side="right", fill="both")
        right_panel.pack_propagate(False)
        
        # Карточка информации
        info_card = tk.Frame(right_panel, bg="#111111", relief="flat")
        info_card.pack(fill="both", expand=True, pady=(0, 15))
        
        tk.Label(
            info_card,
            text="ИНФОРМАЦИЯ",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg="#111111"
        ).pack(anchor="w", pady=(15, 10), padx=20)
        
        # Контент информации
        info_container = tk.Frame(info_card, bg="#111111")
        info_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        # Разделы информации
        sections = [
            ("ОСОБЕННОСТИ СЕРВЕРА", [
                "Реалистичный RolePlay",
                "Продвинутая экономика",
                "300+ кастомных авто",
                "Система домов и бизнесов"
            ]),
            ("ТРЕБОВАНИЯ", [
                "GTA San Andreas 1.0",
                "SA-MP 0.3.7 R1",
                "Windows 7 или выше"
            ]),
            ("ПРАВИЛА", [
                "Запрещены читы и баги",
                "Уважайте других игроков",
                "Следуйте ролевым правилам"
            ])
        ]
        
        for title, items in sections:
            tk.Label(
                info_container,
                text=title,
                font=("Segoe UI", 11, "bold"),
                fg="#e74c3c",
                bg="#111111"
            ).pack(anchor="w", pady=(10, 5))
            
            for item in items:
                tk.Label(
                    info_container,
                    text=f"• {item}",
                    font=("Segoe UI", 9),
                    fg="#bdc3c7",
                    bg="#111111"
                ).pack(anchor="w", pady=2)
        
        # КАРТОЧКА НАСТРОЕК
        settings_card = tk.Frame(right_panel, bg="#111111", relief="flat")
        settings_card.pack(fill="x")
        
        tk.Label(
            settings_card,
            text="НАСТРОЙКИ",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg="#111111"
        ).pack(anchor="w", pady=(15, 10), padx=20)
        
        # Путь к SAMP
        path_frame = tk.Frame(settings_card, bg="#111111")
        path_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        tk.Label(
            path_frame,
            text="ПУТЬ К SAMP.EXE",
            font=("Segoe UI", 10, "bold"),
            fg="#8a9bb5",
            bg="#111111"
        ).pack(anchor="w", pady=(0, 8))
        
        path_select = tk.Frame(path_frame, bg="#111111")
        path_select.pack(fill="x")
        
        self.path_var = tk.StringVar(value=self.samp_path)
        path_entry = tk.Entry(
            path_select,
            textvariable=self.path_var,
            font=("Segoe UI", 10),
            bg="#1a1a1a",
            fg="white",
            relief="flat"
        )
        path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=8)
        
        browse_btn = tk.Button(
            path_select,
            text="ОБЗОР",
            command=self.browse_samp,
            font=("Segoe UI", 10, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8
        )
        browse_btn.pack(side="right")
        
        # Ссылка на скачивание SAMP
        download_frame = tk.Frame(settings_card, bg="#111111")
        download_frame.pack(fill="x", padx=20, pady=(5, 10))
        
        download_link = tk.Label(
            download_frame,
            text="⬇ СКАЧАТЬ SA-MP (если нет)",
            font=("Segoe UI", 9),
            fg="#3498db",
            bg="#111111",
            cursor="hand2"
        )
        download_link.pack(anchor="w")
        download_link.bind("<Button-1>", lambda e: self.download_samp())
        
        # Опция сворачивания
        minimize_frame = tk.Frame(settings_card, bg="#111111")
        minimize_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        minimize_check = tk.Checkbutton(
            minimize_frame,
            text="СВОРАЧИВАТЬ ПРИ ЗАПУСКЕ ИГРЫ",
            variable=self.minimize_on_launch,
            font=("Segoe UI", 10),
            fg="#ecf0f1",
            bg="#111111",
            selectcolor="#111111",
            activebackground="#111111",
            cursor="hand2"
        )
        minimize_check.pack(anchor="w", pady=5)
        
        # БОЛЬШАЯ КНОПКА СОХРАНИТЬ
        save_btn = tk.Button(
            settings_card,
            text="СОХРАНИТЬ НАСТРОЙКИ",
            command=self.save_config,
            font=("Segoe UI", 14, "bold"),
            bg="#2ecc71",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=18
        )
        save_btn.pack(pady=(10, 25), padx=20, fill="x")
        
        # Социальные сети
        social_frame = tk.Frame(right_panel, bg="#0a0a0a")
        social_frame.pack(pady=(15, 0))
        
        for name, url, color in [
            ("DISCORD", "https://discord.gg/legacyrp", "#5865F2"),
            ("ФОРУМ", "https://legacyrprprp.sampproject.ru/index.php", "#9b59b6"),
            ("VK", "https://vk.com/legacyrp", "#4c75a3")
        ]:
            btn = tk.Button(
                social_frame,
                text=name,
                command=lambda u=url: webbrowser.open(u),
                font=("Segoe UI", 9, "bold"),
                bg=color,
                fg="white",
                relief="flat",
                cursor="hand2",
                padx=12,
                pady=8
            )
            btn.pack(side="left", padx=4, expand=True, fill="x")
    
    def create_server_card(self, parent, server_id, server_info):
        # Карточка
        card = tk.Frame(parent, bg="#111111", relief="flat")
        card.pack(fill="x", pady=10)
        
        # Левая цветная полоса
        color_bar = tk.Frame(card, bg=server_info["color"], width=5)
        color_bar.pack(side="left", fill="y")
        
        # Контент
        content = tk.Frame(card, bg="#111111")
        content.pack(side="left", fill="both", expand=True, padx=25, pady=18)
        
        # Название и статус
        header = tk.Frame(content, bg="#111111")
        header.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            header,
            text=server_info["name"],
            font=("Segoe UI", 18, "bold"),
            fg=server_info["color"],
            bg="#111111"
        ).pack(side="left")
        
        # Бейдж статуса
        self.status_badge = tk.Label(
            header,
            text="ЗАГРУЗКА",
            font=("Segoe UI", 9, "bold"),
            fg="#f39c12",
            bg="#1a1a1a",
            padx=12,
            pady=4
        )
        self.status_badge.pack(side="right")
        
        # IP
        tk.Label(
            content,
            text=f"{server_info['ip']}:{server_info['port']}",
            font=("Segoe UI", 11),
            fg="#5a6e8a",
            bg="#111111"
        ).pack(anchor="w", pady=(0, 12))
        
        # Онлайн
        online_frame = tk.Frame(content, bg="#111111")
        online_frame.pack(fill="x")
        
        self.online_label = tk.Label(
            online_frame,
            text="--",
            font=("Segoe UI", 28, "bold"),
            fg="#2ecc71",
            bg="#111111"
        )
        self.online_label.pack(side="left")
        
        tk.Label(
            online_frame,
            text=f"/ {server_info['max_players']}",
            font=("Segoe UI", 14),
            fg="#5a6e8a",
            bg="#111111"
        ).pack(side="left", padx=(8, 0))
        
        tk.Label(
            online_frame,
            text="ИГРОКОВ",
            font=("Segoe UI", 11),
            fg="#5a6e8a",
            bg="#111111"
        ).pack(side="left", padx=(12, 0))
        
        # Кнопка запуска
        play_btn = tk.Button(
            card,
            text="ИГРАТЬ",
            command=lambda sid=server_id: self.launch_game(sid),
            font=("Segoe UI", 13, "bold"),
            bg=server_info["color"],
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=40,
            pady=14
        )
        play_btn.place(relx=0.92, rely=0.5, anchor="center")
        
        # Сохраняем для обновления
        self.server_cards[server_id] = {
            "online_label": self.online_label,
            "status_badge": self.status_badge,
            "ip": server_info["ip"],
            "port": server_info["port"],
            "max_players": server_info["max_players"]
        }
    
    def update_online(self, server_id):
        """Обновление реального онлайна"""
        server = self.server_cards[server_id]
        
        real_online, max_players = RealSAMPQuery.get_real_players(
            server["ip"], 
            server["port"]
        )
        
        def update_label():
            if real_online > 0:
                color = "#2ecc71"
                status = "ОНЛАЙН"
            else:
                color = "#e74c3c"
                status = "ПУСТО"
            
            server["online_label"].config(text=str(real_online), fg=color)
            server["status_badge"].config(text=status, fg=color)
        
        self.root.after(0, update_label)
    
    def update_all_online(self):
        """Обновление онлайна всех серверов"""
        for server_id in self.server_cards:
            thread = threading.Thread(target=self.update_online, args=(server_id,), daemon=True)
            thread.start()
        
        self.root.after(10000, self.update_all_online)
    
    def launch_game(self, server_id):
        server = SERVERS[server_id]
        ip_port = f"{server['ip']}:{server['port']}"
        
        if not os.path.exists(self.samp_path):
            result = messagebox.askyesno(
                "SAMP НЕ НАЙДЕН",
                f"SA-MP не найден по пути:\n{self.samp_path}\n\nХотите скачать SA-MP?"
            )
            if result:
                self.download_samp()
            return
        
        try:
            subprocess.Popen([self.samp_path, ip_port])
            
            if self.minimize_on_launch.get():
                self.root.iconify()
            else:
                self.root.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить SAMP:\n{str(e)}")

def main():
    try:
        root = tk.Tk()
        app = Launcher(root)
        root.mainloop()
    except Exception as e:
        print(f"Ошибка: {e}")
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()