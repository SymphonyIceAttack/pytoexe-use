import os
import sys
import subprocess
import threading
import uuid
import shutil
import webbrowser
import customtkinter as ctk
from tkinter import messagebox, filedialog, Toplevel, Canvas
import minecraft_launcher_lib
import math
import json  # <-- dodane do obsługi kont

# ===================== KONFIG =====================
LOGO_PATH = "logo.png"
PAYPAL_LINK = "https://paypal.me/WojtaseKK"  # Twój PayPal.Me
ACCOUNTS_FILE = "accounts.json"  # plik do logowania

# ===================== FUNKCJE POMOCNICZE =====================
def get_clients_dir():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.getcwd()
    return os.path.join(base_path, "clients")

# ===================== KONTO =====================
def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "w") as f:
            json.dump({}, f)
    with open(ACCOUNTS_FILE, "r") as f:
        return json.load(f)

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=4)

def show_login_window(parent):
    login_win = Toplevel(parent)
    login_win.title("Logowanie / Rejestracja")
    login_win.geometry("300x200+800+50")
    login_win.resizable(False, False)

    ctk.CTkLabel(login_win, text="Login:").pack(pady=5)
    login_entry = ctk.CTkEntry(login_win)
    login_entry.pack(pady=5)

    ctk.CTkLabel(login_win, text="Hasło:").pack(pady=5)
    password_entry = ctk.CTkEntry(login_win, show="*")
    password_entry.pack(pady=5)

    accounts = load_accounts()

    def login():
        username = login_entry.get().strip()
        password = password_entry.get().strip()
        if username in accounts and accounts[username] == password:
            parent.nick.delete(0, "end")
            parent.nick.insert(0, username)
            messagebox.showinfo("Sukces", f"Zalogowano jako {username}")
            login_win.destroy()
        else:
            messagebox.showerror("Błąd", "Niepoprawny login lub hasło")

    def register():
        username = login_entry.get().strip()
        password = password_entry.get().strip()
        if username in accounts:
            messagebox.showerror("Błąd", "Konto już istnieje")
        elif not username or not password:
            messagebox.showwarning("Błąd", "Wypełnij oba pola")
        else:
            accounts[username] = password
            save_accounts(accounts)
            messagebox.showinfo("Sukces", f"Konto {username} utworzone!")

    button_frame = ctk.CTkFrame(login_win)
    button_frame.pack(pady=10)
    ctk.CTkButton(button_frame, text="Zaloguj", command=login).pack(side="left", padx=5)
    ctk.CTkButton(button_frame, text="Zarejestruj", command=register).pack(side="left", padx=5)

# ===================== ANIMACJA STARTOWA =====================
def show_startup_animation(root, callback=None):
    anim_win = Toplevel(root)
    anim_win.overrideredirect(True)
    anim_win.geometry("200x200+500+200")
    anim_win.attributes("-topmost", True)

    canvas = Canvas(anim_win, width=200, height=200, bg="black", highlightthickness=0)
    canvas.pack()

    size = 60
    angle = 0
    steps = 36
    loops = 3

    def animate_step(step=0, loop=0):
        nonlocal angle
        canvas.delete("all")
        center = 100
        offset = size / 2
        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        corners = [
            (center + (-offset * cos_a - -offset * sin_a), center + (-offset * sin_a + -offset * cos_a)),
            (center + ( offset * cos_a - -offset * sin_a), center + ( offset * sin_a + -offset * cos_a)),
            (center + ( offset * cos_a -  offset * sin_a), center + ( offset * sin_a +  offset * cos_a)),
            (center + (-offset * cos_a -  offset * sin_a), center + (-offset * sin_a +  offset * cos_a))
        ]

        canvas.create_polygon(corners, fill="#8B4513", outline="white")
        angle += 10

        if step < steps:
            root.after(50, lambda: animate_step(step + 1, loop))
        else:
            if loop < loops - 1:
                root.after(50, lambda: animate_step(0, loop + 1))
            else:
                anim_win.destroy()
                if callback:
                    callback()

    animate_step()

# ===================== XLAUNCHER =====================
class XLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.title("XLauncher")
        self.geometry("800x850")
        self.resizable(True, True)

        self.minecraft_dir = os.path.join(os.getcwd(), ".minecraft")
        self.local_clients_dir = get_clients_dir()

        self.clients_list = []
        self.client_vars = {}
        self.user_added_mods = {}

        # Zmienna RAM
        self.max_ram = ctk.StringVar(value="4")  # domyślnie 4 GB

        self.create_ui()
        self.load_versions()
        self.load_clients()

        show_startup_animation(self, callback=self.deiconify)

    # ---------- UI ----------
    def create_ui(self):
        # Animowany napis świecący biało/zielono
        self.animated_label = ctk.CTkLabel(self, text="XLauncher 🚀", font=("Segoe UI", 30, "bold"))
        self.animated_label.pack(pady=15)
        self.animate_text_color()

        # ---------- Przycisk logowania w prawym górnym rogu ----------
        login_btn = ctk.CTkButton(self, text="Logowanie", width=100, command=lambda: show_login_window(self))
        login_btn.place(x=680, y=15)

        # Zakładki
        self.tabview = ctk.CTkTabview(self, width=780, height=700)
        self.tabview.pack(padx=10, pady=10)
        self.tabview.add("Główne")
        self.tabview.add("Mody")
        self.tabview.add("Chat")
        self.tabview.add("Ustawienia")
        self.tabview.add("Wspieranie")  # nowa zakładka

        # ---------- Główne ----------
        main_tab = self.tabview.tab("Główne")
        self.nick = ctk.CTkEntry(main_tab, width=400, placeholder_text="Nick (offline)")
        self.nick.pack(pady=10)

        self.version_box = ctk.CTkComboBox(main_tab, width=400)
        self.version_box.pack(pady=10)

        self.progress = ctk.CTkProgressBar(main_tab, width=600)
        self.progress.pack(pady=25)

        self.status = ctk.CTkLabel(main_tab, text="Gotowy")
        self.status.pack(pady=5)

        self.launch_btn = ctk.CTkButton(
            main_tab,
            text="▶ Uruchom Minecraft",
            height=50,
            command=self.launch
        )
        self.launch_btn.pack(pady=15)

        # ---------- Mody ----------
        mods_tab = self.tabview.tab("Mody")
        ctk.CTkLabel(mods_tab, text="Klient / mody:", font=("Segoe UI", 16)).pack(pady=8)
        self.checkbox_frame = ctk.CTkFrame(mods_tab)
        self.checkbox_frame.pack(padx=20, fill="x")

        ctk.CTkButton(mods_tab, text="➕ Dodaj własny mod (.jar)", command=self.add_custom_mod).pack(pady=5)
        self.dir_label = ctk.CTkLabel(mods_tab, text=self.minecraft_dir, wraplength=700)
        self.dir_label.pack(pady=15)
        ctk.CTkButton(mods_tab, text="📂 Zmień katalog gry", command=self.choose_dir).pack(pady=5)

        # ---------- Chat ----------
        chat_tab = self.tabview.tab("Chat")
        ctk.CTkLabel(chat_tab, text="Chat graczy", font=("Segoe UI", 16, "bold")).pack(pady=10)
        self.chat_box = ctk.CTkTextbox(chat_tab, width=700, height=300, state="disabled")
        self.chat_box.pack(pady=10)
        self.chat_entry = ctk.CTkEntry(chat_tab, width=500, placeholder_text="Wpisz wiadomość…")
        self.chat_entry.pack(side="left", padx=10, pady=5)
        ctk.CTkButton(chat_tab, text="Wyślij", command=self.send_chat_message).pack(side="left", pady=5)

        # ---------- Ustawienia ----------
        settings_tab = self.tabview.tab("Ustawienia")
        ctk.CTkLabel(settings_tab, text="Ustawienia launchera", font=("Segoe UI", 16, "bold")).pack(pady=15)
        ram_frame = ctk.CTkFrame(settings_tab)
        ram_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(ram_frame, text="Maksymalna pamięć RAM (GB):").pack(side="left", padx=5)
        self.ram_entry = ctk.CTkEntry(ram_frame, width=50, textvariable=self.max_ram)
        self.ram_entry.pack(side="left", padx=5)

        # ---------- Wspieranie ----------
        support_tab = self.tabview.tab("Wspieranie")
        ctk.CTkLabel(support_tab, text="Wspieraj rozwój launchera!", font=("Segoe UI", 16, "bold")).pack(pady=10)
        ctk.CTkLabel(support_tab, text="Kliknij kwotę, aby wpłacić:").pack(pady=5)
        for amount in [1, 5, 10]:
            btn = ctk.CTkButton(support_tab, text=f"{amount} zł", width=200,
                                command=lambda a=amount: self.open_paypal(a))
            btn.pack(pady=5)

    # ---------- Animacja napisu biało-zielono ----------
    def animate_text_color(self, text="XLauncher 🚀", color_state=True):
        color = "white" if color_state else "#00FF00"
        self.animated_label.configure(text=text, text_color=color)
        self.after(500, lambda: self.animate_text_color(text, not color_state))

    # ---------- Chat ----------
    def send_chat_message(self):
        msg = self.chat_entry.get().strip()
        if msg:
            nick = self.nick.get().strip() or "Gracz"
            full_msg = f"{nick}: {msg}"
            self.display_message(full_msg)
            self.chat_entry.delete(0, "end")

    def display_message(self, msg):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", msg + "\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    # ---------- Helpers ----------
    def set_progress(self, val):
        self.after(0, lambda: self.progress.set(val))

    def set_status(self, txt):
        self.after(0, lambda: self.status.configure(text=txt))

    def choose_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.minecraft_dir = path
            self.dir_label.configure(text=path)

    def load_versions(self):
        try:
            versions = minecraft_launcher_lib.utils.get_version_list()
            releases = [v["id"] for v in versions if v["type"] == "release"]
            self.version_box.configure(values=releases)
            if releases:
                self.version_box.set(releases[0])
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def load_clients(self):
        for w in self.checkbox_frame.winfo_children():
            w.destroy()

        self.client_vars.clear()
        self.clients_list.clear()

        if os.path.exists(self.local_clients_dir):
            jars = [f for f in os.listdir(self.local_clients_dir) if f.endswith(".jar")]
        else:
            jars = []

        for jar in jars:
            name = os.path.splitext(jar)[0]
            self.clients_list.append(name)
            var = ctk.StringVar(value="0")
            cb = ctk.CTkCheckBox(self.checkbox_frame, text=name, variable=var)
            cb.pack(anchor="w")
            self.client_vars[name] = var

        for name, path in self.user_added_mods.items():
            if name not in self.client_vars:
                var = ctk.StringVar(value="1")
                cb = ctk.CTkCheckBox(self.checkbox_frame, text=name, variable=var)
                cb.pack(anchor="w")
                self.client_vars[name] = var

        if not self.client_vars:
            ctk.CTkLabel(self.checkbox_frame, text="Brak modów w folderze clients").pack(pady=10)

    def add_custom_mod(self):
        path = filedialog.askopenfilename(filetypes=[("Jar files", "*.jar")])
        if path:
            name = os.path.splitext(os.path.basename(path))[0]
            self.user_added_mods[name] = path
            self.load_clients()

    # ---------- Launch ----------
    def launch(self):
        threading.Thread(target=self._launch, daemon=True).start()

    def _launch(self):
        try:
            nick = self.nick.get().strip()
            if not nick:
                messagebox.showerror("Błąd", "Podaj nick")
                return

            version = self.version_box.get()
            mc_dir = self.minecraft_dir
            ram_value = self.max_ram.get()
            try:
                ram_gb = int(ram_value)
            except ValueError:
                ram_gb = 4
                messagebox.showwarning("Ustawienia RAM", "Niepoprawna wartość RAM, ustawiono 4 GB")

            self.set_status("Instalowanie Fabric…")
            minecraft_launcher_lib.fabric.install_fabric(version, mc_dir)

            loader = minecraft_launcher_lib.fabric.get_latest_loader_version()

            mods_dir = os.path.join(mc_dir, "mods")
            os.makedirs(mods_dir, exist_ok=True)

            for f in os.listdir(mods_dir):
                os.remove(os.path.join(mods_dir, f))

            all_mods = {n: os.path.join(self.local_clients_dir, n + ".jar") for n in self.clients_list}
            all_mods.update(self.user_added_mods)

            for name, path in all_mods.items():
                if self.client_vars.get(name).get() == "1":
                    shutil.copy2(path, os.path.join(mods_dir, name + ".jar"))

            options = {
                "username": nick,
                "uuid": str(uuid.uuid4()),
                "token": "",
                "jvmArguments": [f"-Xmx{ram_gb}G"]
            }

            cmd = minecraft_launcher_lib.command.get_minecraft_command(
                version=f"fabric-loader-{loader}-{version}",
                minecraft_directory=mc_dir,
                options=options
            )

            subprocess.Popen(cmd)
            self.set_status("Gra uruchomiona 😎")
            self.set_progress(1.0)

        except Exception as e:
            messagebox.showerror("Błąd", str(e))
            self.set_status("Błąd")
            self.set_progress(0)

    # ---------- PayPal ----------
    def open_paypal(self, amount):
        url = f"{PAYPAL_LINK}/{amount}PLN"
        webbrowser.open(url)

# ===================== START =====================
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    XLauncher().mainloop()
