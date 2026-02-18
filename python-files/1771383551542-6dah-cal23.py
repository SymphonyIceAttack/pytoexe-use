import tkinter as tk
from tkinter import ttk
import json
import os

# ================= CONFIG =================
CONFIG_FILE = "config.json"

LIMITS_FILE = "limits.txt"
BASE_FONT = 18
current_scale = 1.0
current_font = "Segoe UI"

SPECIAL_MIDDLES = {3,9,15,21,27,33,39,45,51,57}

topmost = True
dark_mode = False
history = []
move_mode = False
global_alpha = 0.9
auto_alpha_enabled = False

# ================= LOAD CONFIG =================
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
            global_alpha = cfg.get("global_alpha", 0.9)
            auto_alpha_enabled = cfg.get("auto_alpha_enabled", False)
            topmost = cfg.get("topmost", True)
    except:
        pass

# ================= LIMITS =================
if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE) as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0,6,12,18,24,30,36,42,48,54,60]

# ================= MAIN APP =================
class ModernTradingWidget:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Hub")
        self.root.geometry("320x200")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", topmost)
        self.root.attributes("-alpha", global_alpha)
        self.root.config(bg="#121212")

        self.xwin = 0
        self.ywin = 0
        self.setup_ui()
        self.bind_events()

    def setup_ui(self):
        # --- Custom Title Bar ---
        self.title_bar = tk.Frame(self.root, bg="#1E1E1E", height=30)
        self.title_bar.pack(fill="x")
        tk.Label(self.title_bar, text="TRADER CORE v1.0", fg="#555", bg="#1E1E1E",
                 font=(current_font, 8, "bold")).pack(side="left", padx=10)
        # Pin/Unpin
        self.pin_btn = tk.Button(self.title_bar, text="Pin" if not topmost else "Unpin",
                                 bg="#1E1E1E", fg="#888", bd=0, command=self.toggle_pin)
        self.pin_btn.pack(side="right", padx=5, ipadx=5)
        # Close
        close_btn = tk.Button(self.title_bar, text="✕", bg="#1E1E1E", fg="#888", bd=0,
                              command=self.close_app, activebackground="#ff4444")
        close_btn.pack(side="right", padx=5, ipadx=5)

        # --- Main Content Area ---
        self.main_area = tk.Frame(self.root, bg="#121212")
        self.main_area.pack(expand=True, fill="both", padx=10, pady=5)
        self.status_lbl = tk.Label(self.main_area, text="READY", fg="#00FF7F",
                                   bg="#121212", font=(current_font, 20, "bold"))
        self.status_lbl.pack(pady=10)

        # --- Bottom Control Bar ---
        self.control_bar = tk.Frame(self.root, bg="#121212")
        self.control_bar.pack(fill="x", side="bottom", pady=5)

        # Auto-Glass toggle
        self.alpha_toggle_btn = tk.Button(self.control_bar, text=f"Auto-Glass: {'ON' if auto_alpha_enabled else 'OFF'}",
                                          bg="#00FF7F" if auto_alpha_enabled else "#333", fg="white", bd=0, padx=10,
                                          command=self.toggle_auto_alpha, font=(current_font,8))
        self.alpha_toggle_btn.pack(side="left", padx=10)

        # Manual alpha slider
        self.alpha_slider = ttk.Scale(self.control_bar, from_=0.3, to=1.0,
                                      orient="horizontal", command=self.update_alpha)
        self.alpha_slider.set(global_alpha)
        self.alpha_slider.pack(side="right", padx=10, fill="x", expand=True)

    # ================= FUNCTIONS =================
    def toggle_auto_alpha(self):
        global auto_alpha_enabled
        auto_alpha_enabled = not auto_alpha_enabled
        status = "ON" if auto_alpha_enabled else "OFF"
        color = "#00FF7F" if auto_alpha_enabled else "#333"
        self.alpha_toggle_btn.config(text=f"Auto-Glass: {status}", bg=color)

    def toggle_pin(self):
        global topmost
        topmost = not topmost
        self.root.attributes("-topmost", topmost)
        self.pin_btn.config(text="Unpin" if topmost else "Pin")

    def on_mouse_enter(self,event):
        if auto_alpha_enabled:
            self.root.attributes("-alpha",1.0)

    def on_mouse_leave(self,event):
        if auto_alpha_enabled:
            self.root.attributes("-alpha",0.4)
        else:
            self.root.attributes("-alpha", global_alpha)

    def update_alpha(self,val):
        global global_alpha
        global_alpha = float(val)
        if not auto_alpha_enabled:
            self.root.attributes("-alpha", global_alpha)

    # ================= MOVE =================
    def bind_events(self):
        self.title_bar.bind("<Button-1>", self.get_pos)
        self.title_bar.bind("<B1-Motion>", self.move_window)
        self.root.bind("<Enter>", self.on_mouse_enter)
        self.root.bind("<Leave>", self.on_mouse_leave)

    def get_pos(self,event):
        self.xwin = event.x
        self.ywin = event.y

    def move_window(self,event):
        self.root.geometry(f'+{event.x_root - self.xwin}+{event.y_root - self.ywin}')

    # ================= CLOSE APP =================
    def close_app(self):
        self.save_config()
        self.root.destroy()

    def save_config(self):
        cfg = {"global_alpha": global_alpha,
               "auto_alpha_enabled": auto_alpha_enabled,
               "topmost": topmost}
        with open(CONFIG_FILE,"w") as f:
            json.dump(cfg,f)

# ================= RUN =================
if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Horizontal.TScale", background="#121212", foreground="#00FF7F")

    app = ModernTradingWidget(root)
    root.mainloop()
