import sys
import os
import shutil
import configparser
import glob
import json
import tkinter as tk
from tkinter import filedialog, messagebox

# ------------------- Функция для поиска ресурсов -------------------
def resource_path(relative_path):
    """Возвращает абсолютный путь к файлу/папке, учитывая компиляцию PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def find_patcher_files_folder():
    """
    Ищет папку 'PatcherFiles' в нескольких местах.
    Возвращает путь к папке или None, если не найдена.
    """
    # Список мест для поиска
    candidates = [
        # Рядом со скриптом/executable
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "PatcherFiles"),
        # В родительской папке
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "PatcherFiles"),
        # В текущей рабочей директории
        os.path.join(os.getcwd(), "PatcherFiles"),
        # В папке, где лежит сам скрипт (для PyInstaller --onefile)
        resource_path("PatcherFiles")
    ]
    # Убираем дубликаты
    candidates = list(dict.fromkeys(candidates))
    
    for folder in candidates:
        if os.path.isdir(folder):
            # Проверим, есть ли внутри хотя бы один .dll
            dlls = glob.glob(os.path.join(folder, "*.dll"))
            if dlls:
                return folder
    return None

def save_settings(settings_file, path):
    """Сохраняет путь к папке PatcherFiles в JSON"""
    try:
        with open(settings_file, 'w') as f:
            json.dump({"patcher_path": path}, f)
    except:
        pass

def load_settings(settings_file):
    """Загружает сохранённый путь к папке PatcherFiles"""
    try:
        with open(settings_file, 'r') as f:
            data = json.load(f)
            return data.get("patcher_path", "")
    except:
        return ""

# ------------------- Основная логика -------------------
def get_game_exe(gp, en=""):
    if en:
        p = os.path.join(gp, en)
        if os.path.isfile(p):
            return en
    exes = glob.glob(os.path.join(gp, "*.exe"))
    if exes:
        return os.path.basename(exes[0])
    return ""

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SteamML Online Patcher (Smart)")
        self.geometry("550x400")
        self.resizable(False, False)
        
        # Файл для сохранения настроек
        self.settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "patcher_settings.json")
        self.patcher_folder = None
        
        self.create_widgets()
        self.load_patcher_folder()
        
    def create_widgets(self):
        # Путь к игре
        tk.Label(self, text="Game Folder Path:").pack(pady=(20,5))
        self.path_entry = tk.Entry(self, width=60)
        self.path_entry.pack(pady=5)
        btn_browse_game = tk.Button(self, text="Browse Game Folder", command=self.browse_game_folder)
        btn_browse_game.pack(pady=2)
        
        # real_app_id
        tk.Label(self, text="real_app_id:").pack(pady=(10,0))
        self.id_entry = tk.Entry(self, width=20)
        self.id_entry.pack(pady=5)
        
        # Кнопка для выбора папки PatcherFiles (если не найдена автоматически)
        self.patcher_status = tk.Label(self, text="", fg="blue")
        self.patcher_status.pack(pady=5)
        btn_browse_patcher = tk.Button(self, text="Select PatcherFiles Folder Manually", command=self.browse_patcher_folder)
        btn_browse_patcher.pack(pady=2)
        
        # Кнопка Patch
        self.patch_btn = tk.Button(self, text="Patch", command=self.patch_game, state="disabled", bg="lightgreen")
        self.patch_btn.pack(pady=15)
        
        # Лог
        self.log_text = tk.Text(self, height=8, width=70)
        self.log_text.pack(pady=10)
        
        # Привязка проверки
        self.path_entry.bind("<KeyRelease>", self.check_ready)
        self.id_entry.bind("<KeyRelease>", self.check_ready)
        
    def browse_game_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)
            self.check_ready()
    
    def browse_patcher_folder(self):
        folder = filedialog.askdirectory(title="Select folder containing unsteam64.dll, winhttp.dll, winmm.dll")
        if folder:
            # Проверим, что там есть хотя бы один из нужных dll
            needed = ["unsteam64.dll", "winhttp.dll", "winmm.dll"]
            found = any(os.path.isfile(os.path.join(folder, f)) for f in needed)
            if found:
                self.patcher_folder = folder
                save_settings(self.settings_file, folder)
                self.patcher_status.config(text=f"PatcherFiles folder set to: {folder}", fg="green")
                self.log_text.insert(tk.END, f"✓ Patcher folder manually set: {folder}\n")
                self.check_ready()
            else:
                messagebox.showerror("Error", f"Selected folder does not contain any of needed DLLs: {', '.join(needed)}")
    
    def load_patcher_folder(self):
        # Сначала ищем автоматически
        found = find_patcher_files_folder()
        if found:
            self.patcher_folder = found
            self.patcher_status.config(text=f"✓ PatcherFiles found at: {found}", fg="green")
            self.log_text.insert(tk.END, f"Auto-detected Patcher folder: {found}\n")
        else:
            # Пробуем загрузить сохранённый путь
            saved = load_settings(self.settings_file)
            if saved and os.path.isdir(saved):
                self.patcher_folder = saved
                self.patcher_status.config(text=f"✓ Using saved Patcher folder: {saved}", fg="green")
            else:
                self.patcher_folder = None
                self.patcher_status.config(text="⚠ PatcherFiles folder not found. Please select manually.", fg="red")
        self.check_ready()
    
    def check_ready(self, event=None):
        game_ok = os.path.isdir(self.path_entry.get().strip())
        id_ok = bool(self.id_entry.get().strip())
        patcher_ok = self.patcher_folder is not None and os.path.isdir(self.patcher_folder)
        if game_ok and id_ok and patcher_ok:
            self.patch_btn.config(state="normal")
        else:
            self.patch_btn.config(state="disabled")
    
    def patch_game(self):
        gp = self.path_entry.get().strip()
        en = get_game_exe(gp, "")
        if not en:
            self.log_text.insert(tk.END, "❌ Error: No .exe found in game folder.\n")
            return
        
        # Копируем DLL из patcher_folder в папку игры
        needed_dlls = ["unsteam64.dll", "winhttp.dll", "winmm.dll"]
        missing = []
        for dll in needed_dlls:
            src = os.path.join(self.patcher_folder, dll)
            if os.path.isfile(src):
                try:
                    shutil.copy(src, gp)
                    self.log_text.insert(tk.END, f"✓ Copied {dll}\n")
                except Exception as e:
                    self.log_text.insert(tk.END, f"❌ Failed to copy {dll}: {e}\n")
                    return
            else:
                missing.append(dll)
        
        if missing:
            self.log_text.insert(tk.END, f"❌ Missing DLLs in Patcher folder: {', '.join(missing)}\n")
            return
        
        # Создаём unsteam.ini
        cfg = configparser.ConfigParser()
        cfg["loader"] = {"exe_file": en, "dll_file": "unsteam64.dll"}
        cfg["game"] = {
            "offline_mode": 0,
            "steam_id": "",
            "player_name": "By OPV",
            "real_app_id": self.id_entry.get().strip(),
            "fake_app_id": 480,
            "language": "english",
            "beta_name": "beta",
            "saves_path": "",
            "game_launch_options": ""
        }
        cfg["dlcs"] = {}
        ini_path = os.path.join(gp, "unsteam.ini")
        try:
            with open(ini_path, "w") as f:
                cfg.write(f)
            self.log_text.insert(tk.END, f"✓ Created {ini_path}\n")
        except Exception as e:
            self.log_text.insert(tk.END, f"❌ Failed to write unsteam.ini: {e}\n")
            return
        
        self.log_text.insert(tk.END, "\n✅ Game patched successfully!\n")
        messagebox.showinfo("Success", "Game patched successfully!")

if __name__ == "__main__":
    App().mainloop()