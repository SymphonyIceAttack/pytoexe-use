import os
import json
import webbrowser
import customtkinter as ctk
from tkinter import messagebox, filedialog
import subprocess

# Настройка темы
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "palworld_config.json"
STEAM_GAME_ID = "1623730"

class PalworldModHelper(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Palworld Mod Helper")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        self.palworld_path = self.load_config()
        
        # Верхняя панель
        self.top_frame = ctk.CTkFrame(self, height=60)
        self.top_frame.pack(fill="x", padx=10, pady=10)
        
        self.title_label = ctk.CTkLabel(self.top_frame, text="Palworld Mod Helper", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(side="left", padx=20, pady=15)
        
        self.play_btn = ctk.CTkButton(self.top_frame, text="🎮 Играть (Steam)", font=ctk.CTkFont(size=16, weight="bold"), 
                                      fg_color="#24a0ed", hover_color="#1b7ab8", command=self.launch_steam)
        self.play_btn.pack(side="right", padx=20, pady=15)
        
        # Настройка пути (если не задан)
        if not self.palworld_path or not os.path.exists(os.path.join(self.palworld_path, "Pal", "Binaries")):
            self.ask_for_path()
            
        # Основной TabView
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_pak = self.tabview.add("Pak Моды")
        self.tab_ue4ss = self.tabview.add("UE4SS")
        self.tab_menu = self.tabview.add("Menu (Читы)")
        self.tab_helper = self.tabview.add("Helper")
        self.tab_links = self.tabview.add("Полезные ссылки")
        
        self.setup_pak_tab()
        self.setup_ue4ss_tab()
        self.setup_menu_tab()
        self.setup_helper_tab()
        self.setup_links_tab()
        
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("palworld_path", "")
        return ""
        
    def save_config(self, path):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"palworld_path": path}, f)
        self.palworld_path = path
        
    def ask_for_path(self):
        messagebox.showinfo("Настройка", "Пожалуйста, укажите путь к папке Palworld (например, C:\\Steam\\steamapps\\common\\Palworld)")
        path = filedialog.askdirectory()
        if path:
            self.save_config(path)
            messagebox.showinfo("Успех", f"Путь сохранен: {path}")
        else:
            messagebox.showwarning("Внимание", "Путь не указан. Некоторые функции будут недоступны.")
            
    def launch_steam(self):
        webbrowser.open(f"steam://rungameid/{STEAM_GAME_ID}")
        
    def get_paks_path(self):
        return os.path.join(self.palworld_path, "Pal", "Content", "Paks") if self.palworld_path else ""
        
    def get_ue4ss_path(self):
        return os.path.join(self.palworld_path, "Pal", "Binaries", "Win64", "ue4ss", "Mods") if self.palworld_path else ""
        
    def get_ue4ss_root(self):
        return os.path.join(self.palworld_path, "Pal", "Binaries", "Win64", "ue4ss") if self.palworld_path else ""

    def setup_pak_tab(self):
        path = self.get_paks_path()
        if path and os.path.exists(path):
            self.text_pak = ctk.CTkTextbox(self.tab_pak, font=ctk.CTkFont(size=14))
            self.text_pak.pack(fill="both", expand=True, padx=20, pady=20)
            self.refresh_pak_list()
        else:
            ctk.CTkLabel(self.tab_pak, text="Папка Paks не найдена. Проверьте путь к игре.", text_color="red").pack(pady=40)
            return
            
        btn_frame = ctk.CTkFrame(self.tab_pak, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(btn_frame, text="🔄 Обновить", command=self.refresh_pak_list).pack(side="left")
        ctk.CTkButton(btn_frame, text="📂 Открыть в проводнике", fg_color="#2b9348", hover_color="#1e6b34", 
                      command=lambda: os.startfile(path)).pack(side="right")

    def refresh_pak_list(self):
        path = self.get_paks_path()
        self.text_pak.delete("1.0", "end")
        if os.path.exists(path):
            files = os.listdir(path)
            self.text_pak.insert("1.0", f"📁 Путь: {path}\n\n" + "\n".join(files) if files else "Папка пуста")
        else:
            self.text_pak.insert("1.0", "Папка не найдена.")

    def setup_ue4ss_tab(self):
        path = self.get_ue4ss_path()
        root_path = self.get_ue4ss_root()
        
        if root_path and os.path.exists(root_path):
            self.text_ue4ss = ctk.CTkTextbox(self.tab_ue4ss, font=ctk.CTkFont(size=14))
            self.text_ue4ss.pack(fill="both", expand=True, padx=20, pady=20)
            self.refresh_ue4ss_list()
        else:
            ctk.CTkLabel(self.tab_ue4ss, text="⚠️ Папка ue4ss не найдена.\nУстановите UE4SS, чтобы функции читов и модов работали.", 
                         text_color="orange", font=ctk.CTkFont(size=16)).pack(pady=40)
            return
            
        btn_frame = ctk.CTkFrame(self.tab_ue4ss, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(btn_frame, text="🔄 Обновить", command=self.refresh_ue4ss_list).pack(side="left")
        ctk.CTkButton(btn_frame, text="📂 Открыть в проводнике", fg_color="#2b9348", hover_color="#1e6b34", 
                      command=lambda: os.startfile(path)).pack(side="right")

    def refresh_ue4ss_list(self):
        path = self.get_ue4ss_path()
        self.text_ue4ss.delete("1.0", "end")
        if os.path.exists(path):
            files = os.listdir(path)
            self.text_ue4ss.insert("1.0", f"📁 Путь: {path}\n\n" + "\n".join(files) if files else "Папка пуста")
        else:
            self.text_ue4ss.insert("1.0", "Папка Mods не найдена.")

    def setup_menu_tab(self):
        root_path = self.get_ue4ss_root()
        ue4ss_exists = root_path and os.path.exists(root_path)
        
        if not ue4ss_exists:
            ctk.CTkLabel(self.tab_menu, text="🚫 Функции недоступны: папка ue4ss не найдена.\nУстановите UE4SS в Palworld\\Pal\\Binaries\\Win64", 
                         text_color="red", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=50)
            return
            
        ctk.CTkLabel(self.tab_menu, text="Управление читами (требует установленный UE4SS Mod)", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        self.var_infinity = ctk.BooleanVar()
        self.var_capture = ctk.BooleanVar()
        self.var_boss = ctk.BooleanVar()
        
        cheats = [
            ("⚡ Infinity Power (Бесконечная выносливость)", self.var_infinity, "Включает бесконечную стамину для игрока"),
            ("🎯 100% Capture (100% захват)", self.var_capture, "Гарантированный захват любого пала или NPC"),
            ("👑 All Boss Capture (Захват боссов)", self.var_boss, "Снимает иммунитет у боссов башен, рейдовых боссов, альфа-палов, вертолёта и защитного дрона. 100% шанс обычной сферой.")
        ]
        
        for text, var, desc in cheats:
            frame = ctk.CTkFrame(self.tab_menu, fg_color="#2a2d2e")
            frame.pack(fill="x", padx=40, pady=10)
            
            ctk.CTkLabel(frame, text=text, font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=20, pady=15)
            ctk.CTkLabel(frame, text=desc, font=ctk.CTkFont(size=12), text_color="gray").pack(side="left", padx=10)
            
            switch = ctk.CTkSwitch(frame, text="Активировать", variable=var, command=self.save_cheat_config)
            switch.pack(side="right", padx=20)
            
        self.save_cheat_config() # Инициализация

    def save_cheat_config(self):
        # Симуляция сохранения конфигурации для UE4SS мода
        root_path = self.get_ue4ss_root()
        if root_path and os.path.exists(root_path):
            config_path = os.path.join(root_path, "ModHelper_Cheats.ini")
            with open(config_path, "w", encoding="utf-8") as f:
                f.write("[Cheats]\n")
                f.write(f"InfinityPower={1 if self.var_infinity.get() else 0}\n")
                f.write(f"100PercentCapture={1 if self.var_capture.get() else 0}\n")
                f.write(f"AllBossCapture={1 if self.var_boss.get() else 0}\n")

    def setup_helper_tab(self):
        # Сегментированный контроль для подкатегорий
        self.helper_seg = ctk.CTkSegmentedButton(self.tab_helper, values=["Разведение", "Шанс поимки", "Предметы и Постройки"], command=self.change_helper_tab)
        self.helper_seg.pack(padx=20, pady=10)
        
        self.helper_frame = ctk.CTkFrame(self.tab_helper, fg_color="transparent")
        self.helper_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.change_helper_tab("Разведение")

    def change_helper_tab(self, choice):
        for widget in self.helper_frame.winfo_children():
            widget.destroy()
            
        if choice == "Разведение":
            ctk.CTkLabel(self.helper_frame, text="Калькулятор разведения Палов", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
            
            frame = ctk.CTkFrame(self.helper_frame)
            frame.pack(pady=10)
            
            ctk.CTkLabel(frame, text="Пал 1:").grid(row=0, column=0, padx=10, pady=10)
            self.pal1 = ctk.CTkComboBox(frame, values=["Lamball", "Cattiva", "Foxparks", "Pengullet", "Gumoss"])
            self.pal1.grid(row=0, column=1, padx=10, pady=10)
            
            ctk.CTkLabel(frame, text="Пал 2:").grid(row=1, column=0, padx=10, pady=10)
            self.pal2 = ctk.CTkComboBox(frame, values=["Lamball", "Cattiva", "Foxparks", "Pengullet", "Gumoss"])
            self.pal2.grid(row=1, column=1, padx=10, pady=10)
            
            ctk.CTkButton(frame, text="Рассчитать", command=self.calculate_breeding).grid(row=2, column=0, columnspan=2, pady=20)
            
            self.breed_result = ctk.CTkLabel(self.helper_frame, text="Результат: ?", font=ctk.CTkFont(size=18, weight="bold"), text_color="#24a0ed")
            self.breed_result.pack(pady=20)
            
        elif choice == "Шанс поимки":
            ctk.CTkLabel(self.helper_frame, text="Калькулятор шанса поимки", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
            
            frame = ctk.CTkFrame(self.helper_frame)
            frame.pack(pady=10)
            
            ctk.CTkLabel(frame, text="Тип сферы:").grid(row=0, column=0, padx=10, pady=10)
            self.sphere_type = ctk.CTkComboBox(frame, values=["Pal Sphere (1x)", "Mega Sphere (1.5x)", "Giga Sphere (2x)", "Ultra Sphere (3x)", "Master Sphere (5x)"])
            self.sphere_type.grid(row=0, column=1, padx=10, pady=10)
            self.sphere_type.set("Pal Sphere (1x)")
            
            ctk.CTkLabel(frame, text="Здоровье врага (%):").grid(row=1, column=0, padx=10, pady=10)
            self.hp_entry = ctk.CTkEntry(frame, width=100)
            self.hp_entry.grid(row=1, column=1, padx=10, pady=10)
            self.hp_entry.insert(0, "100")
            
            ctk.CTkLabel(frame, text="Статус:").grid(row=2, column=0, padx=10, pady=10)
            self.status = ctk.CTkComboBox(frame, values=["Нет", "Сон (+20%)", "Паралич (+15%)", "Огонь (+10%)"])
            self.status.grid(row=2, column=1, padx=10, pady=10)
            
            ctk.CTkButton(frame, text="Рассчитать шанс", command=self.calculate_capture).grid(row=3, column=0, columnspan=2, pady=20)
            
            self.capture_result = ctk.CTkLabel(self.helper_frame, text="Шанс: ?", font=ctk.CTkFont(size=18, weight="bold"), text_color="#24a0ed")
            self.capture_result.pack(pady=20)
            
        elif choice == "Предметы и Постройки":
            ctk.CTkLabel(self.helper_frame, text="База знаний: Предметы и Постройки", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
            
            search_frame = ctk.CTkFrame(self.helper_frame)
            search_frame.pack(fill="x", padx=20, pady=10)
            
            self.search_var = ctk.StringVar()
            self.search_var.trace("w", self.filter_items)
            search_entry = ctk.CTkEntry(search_frame, placeholder_text="Поиск предмета или постройки...", textvariable=self.search_var)
            search_entry.pack(fill="x", padx=10, pady=10)
            
            self.items_listbox = ctk.CTkTextbox(self.helper_frame, height=300, font=ctk.CTkFont(size=14))
            self.items_listbox.pack(fill="both", expand=True, padx=20, pady=10)
            
            self.all_items = [
                "🏠 Деревянная стена (Дерево: 20)",
                "🏠 Деревянная дверь (Дерево: 10)",
                "🔥 Примитивная печь (Камень: 20, Дерево: 10)",
                "⚒️ Верстак (Дерево: 30, Камень: 10)",
                "📦 Ящик для хранения (Дерево: 20)",
                "🍖 Жареное мясо (Мясо: 1)",
                "💊 Лекарство (Лекарственные травы: 3)",
                "⚙️ Древний компонент (Дроп с боссов)",
                "💎 Палкристалл (Добыча в горах)"
            ]
            self.filter_items()

    def filter_items(self, *args):
        query = self.search_var.get().lower()
        filtered = [item for item in self.all_items if query in item.lower()]
        self.items_listbox.delete("1.0", "end")
        self.items_listbox.insert("1.0", "\n".join(filtered) if filtered else "Ничего не найдено")

    def calculate_breeding(self):
        p1 = self.pal1.get()
        p2 = self.pal2.get()
        # Упрощенная логика для демонстрации. В реальном приложении здесь была бы полная база данных.
        if p1 == p2:
            result = p1
        elif (p1 == "Lamball" and p2 == "Cattiva") or (p1 == "Cattiva" and p2 == "Lamball"):
            result = "Gumoss"
        elif (p1 == "Foxparks" and p2 == "Pengullet") or (p1 == "Pengullet" and p2 == "Foxparks"):
            result = "Killamari"
        else:
            result = f"Комбинация {p1} + {p2} (требуется расширение базы данных)"
        self.breed_result.configure(text=f"Результат: {result}")

    def calculate_capture(self):
        try:
            hp = float(self.hp_entry.get())
        except ValueError:
            hp = 100
            
        sphere_multipliers = {"Pal Sphere (1x)": 1.0, "Mega Sphere (1.5x)": 1.5, "Giga Sphere (2x)": 2.0, "Ultra Sphere (3x)": 3.0, "Master Sphere (5x)": 5.0}
        sphere_mult = sphere_multipliers.get(self.sphere_type.get(), 1.0)
        
        status_multipliers = {"Нет": 1.0, "Сон (+20%)": 1.2, "Паралич (+15%)": 1.15, "Огонь (+10%)": 1.1}
        status_mult = status_multipliers.get(self.status.get(), 1.0)
        
        # Упрощенная формула: базовый шанс 10% * множитель сферы * множитель статуса * (100 / HP)
        base_chance = 10.0
        chance = base_chance * sphere_mult * status_mult * (100.0 / max(hp, 1.0))
        chance = min(chance, 100.0) # Не больше 100%
        
        self.capture_result.configure(text=f"Расчетный шанс поимки: {chance:.1f}%")

    def setup_links_tab(self):
        links = [
            ("Nexus Mods (Palworld)", "https://www.nexusmods.com/games/palworld", "#1480d8"),
            ("Palworld.gg (RU)", "https://palworld.gg/ru", "#2b9348"),
            ("Palworld Modding Wiki", "https://pwmodding.wiki/", "#d88c14"),
            ("Palworld Save Pal (Nexus)", "https://www.nexusmods.com/palworld/mods/1827", "#9b59b6")
        ]
        
        ctk.CTkLabel(self.tab_links, text="Полезные ресурсы для моддинга и игры", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=30)
        
        for name, url, color in links:
            btn = ctk.CTkButton(self.tab_links, text=f"🔗 {name}", font=ctk.CTkFont(size=16), 
                                fg_color=color, hover_color=self.adjust_brightness(color, -20),
                                command=lambda u=url: webbrowser.open(u))
            btn.pack(fill="x", padx=100, pady=10)

    def adjust_brightness(self, hex_color, amount):
        # Простая функция для затемнения цвета при наведении
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = max(0, min(255, r + amount))
        g = max(0, min(255, g + amount))
        b = max(0, min(255, b + amount))
        return f"#{r:02x}{g:02x}{b:02x}"

if __name__ == "__main__":
    app = PalworldModHelper()
    app.mainloop()