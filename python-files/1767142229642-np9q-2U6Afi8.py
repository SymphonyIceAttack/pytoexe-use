import time
import sys
import hashlib
import os
from pynput.mouse import Button, Controller as MouseController
from pynput import mouse
from keyauth.api import Keyauth
import customtkinter as ctk
import mss
from PIL import Image
import threading
import webbrowser

# KeyAuth Setup (wie gehabt)
def get_file_hash():
    with open(sys.argv[0], "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

keyauthapp = Keyauth(
    name="triggerbot",
    owner_id="JqTWT66SNH",
    secret="c076eeba8cc1ca50939a3f18d0cc1fdac02b4914fed676354551491ddd830252",
    version="1.0",
    file_hash=get_file_hash()
)

# TriggerBot Setup (wie gehabt)
TARGET_COLOR = (255, 0, 0)
TOLERANCE = 100
mouse_controller = MouseController()
running = False
right_button_held = False
click_delay = 0.05

def on_click(x, y, button, pressed):
    global right_button_held
    if button == mouse.Button.right:
        right_button_held = pressed

mouse.Listener(on_click=on_click).start()

def color_matches(color1, color2, tolerance=TOLERANCE):
    return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(color1, color2))

def get_center_pixel_color():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        x, y = monitor['width'] // 2, monitor['height'] // 2
        region = {"top": y, "left": x, "width": 1, "height": 1}
        img = sct.grab(region)
        pixel = Image.frombytes("RGB", (1, 1), img.rgb).getpixel((0, 0))
        return pixel

def triggerbot_loop():
    global running, click_delay
    while running:
        if right_button_held:
            pixel = get_center_pixel_color()
            if color_matches(pixel, TARGET_COLOR):
                mouse_controller.press(Button.left)
                time.sleep(click_delay)
                mouse_controller.release(Button.left)
                time.sleep(click_delay)
        time.sleep(0.01)

def start_triggerbot():
    global running
    if not running:
        running = True
        threading.Thread(target=triggerbot_loop, daemon=True).start()

def stop_triggerbot():
    global running
    running = False


# GUI Teil

# Grundlayout auf Schwarz-Weiß, Buttons / Labels in Menu-Farbe
ctk.set_appearance_mode("dark")  # Dark Mode für SW-Grundton
ctk.set_default_color_theme("dark-blue")  # Startfarbe (wird überschrieben)

class TriggerBotApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("209 TriggerBot V2")
        self.geometry("300x450")
        self.resizable(False, False)
        self.saved_key_path = os.path.join(os.getenv("APPDATA"), "triggerbot_key.txt")

        self.menu_color = "#FF0000"  # Startfarbe Rot (Menüfarbe)
        
        self.license_var = ctk.StringVar()
        self.delay_var = ctk.DoubleVar(value=click_delay)
        self.status_var = ctk.StringVar(value="🔴 Status: Inaktiv")
        self.trigger_button_text = ctk.StringVar(value="▶ TriggerBot starten")
        self.delay_label_var = ctk.StringVar(value=f"Schuss-Delay: {click_delay:.2f}s")

        self.build_login_ui()

    # Interface zum Login
    def build_login_ui(self):
        self.clear_ui()
        ctk.CTkLabel(self, text="🔒 Login mit Lizenzschlüssel", font=ctk.CTkFont(size=15, weight="bold"), text_color="white").pack(pady=20)
        ctk.CTkEntry(self, textvariable=self.license_var, width=200).pack(pady=10)

        if os.path.exists(self.saved_key_path):
            with open(self.saved_key_path, "r") as f:
                self.license_var.set(f.read().strip())

        ctk.CTkButton(self, text="✅ Lizenz merken", command=self.save_license_key, fg_color=self.menu_color).pack(pady=5)
        ctk.CTkButton(self, text="🟩 Login", command=self.login, fg_color=self.menu_color).pack(pady=10)

    # Hauptmenü mit Triggerbot Controls
    def build_main_ui(self):
        self.clear_ui()
        ctk.CTkLabel(self, text="🎯 09 TriggerBot V2", font=ctk.CTkFont(size=17, weight="bold"), text_color="white").pack(pady=10)
        ctk.CTkLabel(self, textvariable=self.status_var, text_color="white").pack(pady=5)

        ctk.CTkButton(self, textvariable=self.trigger_button_text, command=self.toggle_triggerbot, fg_color=self.menu_color).pack(pady=5)
        ctk.CTkButton(self, text="🔒 Logout", command=self.build_login_ui, fg_color=self.menu_color).pack(pady=5)
        ctk.CTkButton(self, text="🛑 TriggerBot beenden", command=self.stop_bot_and_close, fg_color=self.menu_color).pack(pady=5)
        ctk.CTkButton(self, text="⚙ Einstellungen", command=self.build_settings_ui, fg_color=self.menu_color).pack(pady=5)
        ctk.CTkButton(self, text="📎 Discord", command=lambda: webbrowser.open("https://discord.gg/rxwGWQ75y8"), fg_color=self.menu_color).pack(pady=5)

        ctk.CTkLabel(self, text="Hinweis: Bot schießt nur bei gehaltener rechter Maustaste und erkannter Ziel-Farbe.", wraplength=250, text_color="white", font=("Arial", 10)).pack(pady=10)
        ctk.CTkLabel(self, text="Entwickelt von Pala | discord.gg/rxwGWQ75y8", font=("Arial", 8), text_color="gray").pack(pady=5)

    # Einstellungen mit Delay + Farbwahl
    def build_settings_ui(self):
        self.clear_ui()
        ctk.CTkLabel(self, text="⚙ Einstellungen", font=ctk.CTkFont(size=15, weight="bold"), text_color="white").pack(pady=10)
        
        # Delay Slider
        ctk.CTkLabel(self, textvariable=self.delay_label_var, text_color="white").pack(pady=5)
        ctk.CTkSlider(self, from_=0.01, to=0.5, number_of_steps=49, variable=self.delay_var, command=self.update_delay).pack(pady=5)

        # Farbwahl Button, öffnet Farbdialog
        ctk.CTkButton(self, text="🎨 Menüfarbe ändern", command=self.open_color_picker, fg_color=self.menu_color).pack(pady=10)

        ctk.CTkButton(self, text="⬅ Zurück", command=self.build_main_ui, fg_color=self.menu_color).pack(pady=10)

    def open_color_picker(self):
        # tkinter Farbdialog nutzen
        from tkinter import colorchooser
        color_code = colorchooser.askcolor(title="Wähle Menüfarbe")
        if color_code[1] is not None:
            self.menu_color = color_code[1]
            self.build_settings_ui()  # UI neu bauen, damit Buttons die neue Farbe nutzen

    def toggle_triggerbot(self):
        global running
        if not running:
            start_triggerbot()
            self.status_var.set("🟢 Status: Aktiv")
            self.trigger_button_text.set("⏹ TriggerBot stoppen")
        else:
            stop_triggerbot()
            self.status_var.set("🔴 Status: Inaktiv")
            self.trigger_button_text.set("▶ TriggerBot starten")

    def update_delay(self, value):
        global click_delay
        click_delay = float(value)
        self.delay_label_var.set(f"Schuss-Delay: {click_delay:.2f}s")

    def login(self):
        key = self.license_var.get().strip()
        try:
            keyauthapp.license(key)
            self.build_main_ui()
        except Exception as e:
            from customtkinter import CTkMessagebox
            CTkMessagebox(title="Fehler", message=f"Login fehlgeschlagen:\n{e}", icon="cancel")

    def save_license_key(self):
        with open(self.saved_key_path, "w") as f:
            f.write(self.license_var.get())

    def stop_bot_and_close(self):
        stop_triggerbot()
        self.destroy()

    def clear_ui(self):
        for widget in self.winfo_children():
            widget.destroy()


if __name__ == '__main__':
    app = TriggerBotApp()
    app.mainloop()