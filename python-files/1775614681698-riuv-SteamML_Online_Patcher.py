import sys, os
import customtkinter as ctk
import shutil, configparser, re, glob

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

script_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
os.chdir(script_dir)
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def get_game_exe(gp, en=""):
    if en:
        p = os.path.join(gp, en)
        if os.path.isfile(p):
            return en
    exes = glob.glob(os.path.join(gp, "*.exe"))
    if exes:
        return os.path.basename(exes[0])
    return ""

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SteamML Online Patcher")
        self.geometry("500x260")
        self.resizable(False, False)
        self.game_path = ""
        self.create_widgets()

    def create_widgets(self):
        self.gl = ctk.CTkLabel(self, text="Enter Game Folder Path:")
        self.gl.pack(pady=(20, 5))
        self.gp = ctk.StringVar()
        self.ge = ctk.CTkEntry(self, textvariable=self.gp, width=380)
        self.ge.pack()
        self.sb = ctk.CTkTextbox(self, height=4, width=50)
        self.sb.pack(pady=10)
        self.il = ctk.CTkLabel(self, text="Enter real_app_id:")
        self.il.pack()
        self.iv = ctk.StringVar()
        self.iv.trace_add("write", self.check_ready)
        self.ie = ctk.CTkEntry(self, textvariable=self.iv)
        self.ie.pack()
        self.pb = ctk.CTkButton(self, text="Patch", command=self.patch_game, state="disabled", corner_radius=15)
        self.pb.pack(pady=15)
        self.gp.trace_add("write", self.check_ready)

    def check_ready(self, *a):
        if os.path.isdir(self.gp.get().strip()) and self.iv.get().strip():
            self.pb.configure(state="normal")
        else:
            self.pb.configure(state="disabled")

    def patch_game(self):
        gp = self.gp.get().strip()
        en = get_game_exe(gp, "")
        pf = ["unsteam64.dll", "winhttp.dll", "winmm.dll"]
        patcher_dir = resource_path("PatcherFiles")
        for f in pf:
            s = os.path.join(patcher_dir, f)
            if os.path.isfile(s):
                shutil.copy(s, gp)
        cfg = configparser.ConfigParser()
        cfg["loader"] = {"exe_file": en, "dll_file": "unsteam64.dll"}
        cfg["game"] = {
            "offline_mode": 0,
            "steam_id": "",
            "player_name": "By OPV",
            "real_app_id": self.iv.get().strip(),
            "fake_app_id": 480,
            "language": "english",
            "beta_name": "beta",
            "saves_path": "",
            "game_launch_options": ""
        }
        cfg["dlcs"] = {}
        with open(os.path.join(gp, "unsteam.ini"), "w") as f:
            cfg.write(f)
        self.sb.delete("0.0", "end")
        self.sb.insert("0.0", "Game patched successfully.")

if __name__ == "__main__":
    App().mainloop()