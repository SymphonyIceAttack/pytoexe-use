import tkinter as tk
from tkinter import ttk
import json
import os

SETTINGS_FILE = "trader_settings.json"

class ModernTradingWidget:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Hub")
        self.root.geometry("320x200")
        self.root.overrideredirect(True)
        self.root.config(bg="#121212")
        
        # ---------------- VARIABLES ----------------
        self.auto_alpha_enabled = False
        self.global_alpha = 0.9
        self.topmost = True

        # Load settings if exist
        self.load_settings()
        self.root.attributes("-topmost", self.topmost)
        self.root.attributes("-alpha", self.global_alpha)
        
        # ---------------- UI ----------------
        self.setup_ui()
        
        # Mouse bindings
        self.root.bind("<Enter>", self.on_mouse_enter)
        self.root.bind("<Leave>", self.on_mouse_leave)
        self.title_bar.bind("<Button-1>", self.get_pos)
        self.title_bar.bind("<B1-Motion>", self.move_window)

        # On close save settings
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        # Title Bar
        self.title_bar = tk.Frame(self.root, bg="#1E1E1E", height=30)
        self.title_bar.pack(fill="x")
        tk.Label(self.title_bar, text="TRADER CORE v1.0", fg="#555", bg="#1E1E1E", font=("Segoe UI",8,"bold")).pack(side="left", padx=10)
        close_btn = tk.Button(self.title_bar, text="✕", bg="#1E1E1E", fg="#888", bd=0, command=self.root.destroy, activebackground="#ff4444")
        close_btn.pack(side="right", padx=5, ipadx=5)

        # Main Area
        self.main_area = tk.Frame(self.root, bg="#121212")
        self.main_area.pack(expand=True, fill="both", padx=10, pady=5)
        self.status_lbl = tk.Label(self.main_area, text="READY", fg="#00FF7F", bg="#121212", font=("Segoe UI",20,"bold"))
        self.status_lbl.pack(pady=10)

        # Control Bar
        self.control_bar = tk.Frame(self.root, bg="#121212")
        self.control_bar.pack(fill="x", side="bottom", pady=5)
        self.alpha_toggle_btn = tk.Button(self.control_bar, text=f"Auto-Glass: {'ON' if self.auto_alpha_enabled else 'OFF'}",
                                          bg="#00FF7F" if self.auto_alpha_enabled else "#333", fg="white", bd=0, padx=10,
                                          command=self.toggle_auto_alpha, font=("Segoe UI",8))
        self.alpha_toggle_btn.pack(side="left", padx=10)

        # Slider for transparency
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Horizontal.TScale", background="#121212", foreground="#00FF7F")
        self.alpha_slider = ttk.Scale(self.control_bar, from_=0.3, to=1.0, orient="horizontal", command=self.update_alpha)
        self.alpha_slider.set(self.global_alpha)
        self.alpha_slider.pack(side="right", padx=10, fill="x", expand=True)

        # Pin/Unpin toggle
        self.pin_btn = tk.Button(self.control_bar, text="Pin" if self.topmost else "Unpin", command=self.toggle_pin,
                                 bg="#333", fg="white", bd=0, padx=10, font=("Segoe UI",8))
        self.pin_btn.pack(side="left", padx=5)

    # ---------------- FUNCTIONS ----------------
    def toggle_auto_alpha(self):
        self.auto_alpha_enabled = not self.auto_alpha_enabled
        status = "ON" if self.auto_alpha_enabled else "OFF"
        color = "#00FF7F" if self.auto_alpha_enabled else "#333"
        self.alpha_toggle_btn.config(text=f"Auto-Glass: {status}", bg=color)

    def toggle_pin(self):
        self.topmost = not self.topmost
        self.root.attributes("-topmost", self.topmost)
        self.pin_btn.config(text="Pin" if self.topmost else "Unpin")

    def on_mouse_enter(self, event):
        if self.auto_alpha_enabled:
            self.root.attributes("-alpha", 1.0)

    def on_mouse_leave(self, event):
        if self.auto_alpha_enabled:
            self.root.attributes("-alpha", 0.4)
        else:
            self.root.attributes("-alpha", self.global_alpha)

    def update_alpha(self, val):
        self.global_alpha = float(val)
        if not self.auto_alpha_enabled:
            self.root.attributes("-alpha", self.global_alpha)

    # ---------------- MOVE ----------------
    def get_pos(self, event):
        self.xwin = event.x
        self.ywin = event.y

    def move_window(self, event):
        self.root.geometry(f'+{event.x_root - self.xwin}+{event.y_root - self.ywin}')

    # ---------------- SETTINGS ----------------
    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE,"r") as f:
                    data = json.load(f)
                    self.global_alpha = data.get("alpha",0.9)
                    self.auto_alpha_enabled = data.get("auto_alpha",False)
                    self.topmost = data.get("topmost",True)
            except:
                pass

    def save_settings(self):
        data = {"alpha":self.global_alpha, "auto_alpha":self.auto_alpha_enabled, "topmost":self.topmost}
        with open(SETTINGS_FILE,"w") as f:
            json.dump(data,f)

    def on_close(self):
        self.save_settings()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ModernTradingWidget(root)
    root.mainloop()
