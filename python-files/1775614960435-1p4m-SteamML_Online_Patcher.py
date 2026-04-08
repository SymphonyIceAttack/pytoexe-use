import sys, os, shutil, configparser, glob
import tkinter as tk
from tkinter import messagebox, filedialog

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

script_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
os.chdir(script_dir)

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
        self.title("SteamML Online Patcher")
        self.geometry("500x260")
        self.resizable(False, False)
        self.create_widgets()

    def create_widgets(self):
        # Метка и поле для пути
        tk.Label(self, text="Enter Game Folder Path:").pack(pady=(20, 5))
        self.path_entry = tk.Entry(self, width=60)
        self.path_entry.pack(pady=5)
        btn_browse = tk.Button(self, text="Browse", command=self.browse_folder)
        btn_browse.pack(pady=2)

        # Текстовое поле для вывода сообщений
        self.log_text = tk.Text(self, height=4, width=60)
        self.log_text.pack(pady=10)

        # Метка и поле для real_app_id
        tk.Label(self, text="Enter real_app_id:").pack()
        self.id_entry = tk.Entry(self, width=20)
        self.id_entry.pack(pady=5)

        # Кнопка патча
        self.patch_btn = tk.Button(self, text="Patch", command=self.patch_game, state="disabled")
        self.patch_btn.pack(pady=15)

        # Привязываем проверку ввода
        self.path_entry.bind("<KeyRelease>", self.check_ready)
        self.id_entry.bind("<KeyRelease>", self.check_ready)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)
            self.check_ready()

    def check_ready(self, event=None):
        if os.path.isdir(self.path_entry.get().strip()) and self.id_entry.get().strip():
            self.patch_btn.config(state="normal")
        else:
            self.patch_btn.config(state="disabled")

    def patch_game(self):
        gp = self.path_entry.get().strip()
        en = get_game_exe(gp, "")
        pf = ["unsteam64.dll", "winhttp.dll", "winmm.dll"]
        patcher_dir = resource_path("PatcherFiles")
        for f in pf:
            s = os.path.join(patcher_dir, f)
            if os.path.isfile(s):
                try:
                    shutil.copy(s, gp)
                except Exception as e:
                    self.log_text.insert(tk.END, f"Ошибка копирования {f}: {e}\n")
                    return

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
        try:
            with open(os.path.join(gp, "unsteam.ini"), "w") as f:
                cfg.write(f)
        except Exception as e:
            self.log_text.insert(tk.END, f"Ошибка записи unsteam.ini: {e}\n")
            return

        self.log_text.delete("1.0", tk.END)
        self.log_text.insert("1.0", "Game patched successfully.")

if __name__ == "__main__":
    App().mainloop()