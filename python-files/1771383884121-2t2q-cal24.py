import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from datetime import datetime
import os
import json

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
            dark_mode = cfg.get("dark_mode", False)
            current_font = cfg.get("current_font", "Segoe UI")
            current_scale = cfg.get("current_scale", 1.0)
    except:
        pass

# ================= LIMITS =================
if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE) as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0,6,12,18,24,30,36,42,48,54,60]

# ================= MAIN APP =================
class TradingWidget:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Hub")
        self.root.geometry("400x320")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", topmost)
        self.root.attributes("-alpha", global_alpha)
        self.root.config(bg="#121212" if dark_mode else "white")

        self.xwin = 0
        self.ywin = 0
        self.history = []
        self.setup_ui()
        self.bind_events()
        self.update_colors()

    def setup_ui(self):
        # -------- Title Bar --------
        self.title_bar = tk.Frame(self.root, bg="#1E1E1E" if dark_mode else "#DDD", height=30)
        self.title_bar.pack(fill="x")
        tk.Label(self.title_bar, text="TRADER CORE v1.0", fg="#555", bg=self.title_bar.cget("bg"),
                 font=(current_font, 8, "bold")).pack(side="left", padx=10)
        # Pin/Unpin
        self.pin_btn = tk.Button(self.title_bar, text="Unpin" if topmost else "Pin",
                                 bg=self.title_bar.cget("bg"), fg="#888", bd=0, command=self.toggle_pin)
        self.pin_btn.pack(side="right", padx=5, ipadx=5)
        # Close
        close_btn = tk.Button(self.title_bar, text="✕", bg=self.title_bar.cget("bg"), fg="#888", bd=0,
                              command=self.close_app, activebackground="#ff4444")
        close_btn.pack(side="right", padx=5, ipadx=5)

        # -------- Entry + Calculate --------
        self.entry = tk.Entry(self.root, font=(current_font, BASE_FONT), justify="center")
        self.entry.pack(pady=10)
        self.entry.bind("<Return>", self.calculate)

        self.calc_button = tk.Button(self.root, text="=", font=(current_font, BASE_FONT), width=4,
                                     command=self.calculate)
        self.calc_button.pack(pady=5)

        # -------- Three boxes --------
        self.frame_boxes = tk.Frame(self.root)
        self.frame_boxes.pack(pady=5)
        self.left_var = tk.StringVar(value="-")
        self.mid_var = tk.StringVar(value="-")
        self.right_var = tk.StringVar(value="-")
        self.left_label = tk.Label(self.frame_boxes, textvariable=self.left_var, font=(current_font, BASE_FONT),
                                   width=6, bg="grey", fg="white")
        self.left_label.pack(side="left", padx=5)
        self.mid_label = tk.Label(self.frame_boxes, textvariable=self.mid_var, font=(current_font, BASE_FONT),
                                  width=6, bg="white", fg="black")
        self.mid_label.pack(side="left", padx=5)
        self.right_label = tk.Label(self.frame_boxes, textvariable=self.right_var, font=(current_font, BASE_FONT),
                                    width=6, bg="grey", fg="white")
        self.right_label.pack(side="left", padx=5)

        # -------- History Panel --------
        self.history_text = tk.Text(self.root, height=6, state="disabled", font=(current_font, 10))
        self.history_text.pack(fill="both", padx=10, pady=5)
        self.clear_history_btn = tk.Button(self.root, text="Clear History", command=self.clear_history)
        self.clear_history_btn.pack(pady=5)

        # -------- Bottom Controls --------
        self.control_bar = tk.Frame(self.root)
        self.control_bar.pack(fill="x", side="bottom", pady=5)
        self.alpha_toggle_btn = tk.Button(self.control_bar, text=f"Auto-Glass: {'ON' if auto_alpha_enabled else 'OFF'}",
                                          bg="#00FF7F" if auto_alpha_enabled else "#333", fg="white", bd=0, padx=10,
                                          command=self.toggle_auto_alpha, font=(current_font,8))
        self.alpha_toggle_btn.pack(side="left", padx=10)
        self.alpha_slider = ttk.Scale(self.control_bar, from_=0.3, to=1.0,
                                      orient="horizontal", command=self.update_alpha)
        self.alpha_slider.set(global_alpha)
        self.alpha_slider.pack(side="right", padx=10, fill="x", expand=True)

    # ================= FUNCTIONS =================
    def toggle_auto_alpha(self):
        global auto_alpha_enabled
        auto_alpha_enabled = not auto_alpha_enabled
        color = "#00FF7F" if auto_alpha_enabled else "#333"
        self.alpha_toggle_btn.config(text=f"Auto-Glass: {'ON' if auto_alpha_enabled else 'OFF'}", bg=color)

    def toggle_pin(self):
        global topmost
        topmost = not topmost
        self.root.attributes("-topmost", topmost)
        self.pin_btn.config(text="Unpin" if topmost else "Pin")

    def bind_events(self):
        self.title_bar.bind("<Button-1>", self.get_pos)
        self.title_bar.bind("<B1-Motion>", self.move_window)
        self.entry.bind("<Return>", self.calculate)
        self.root.bind("<Enter>", self.on_mouse_enter)
        self.root.bind("<Leave>", self.on_mouse_leave)

    def get_pos(self,event):
        self.xwin = event.x
        self.ywin = event.y

    def move_window(self,event):
        self.root.geometry(f'+{event.x_root - self.xwin}+{event.y_root - self.ywin}')

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

    # ================= CALCULATION =================
    def calculate(self,event=None):
        val = self.entry.get()
        if not val.isdigit() or len(val) > 2:
            messagebox.showerror("Error","Enter 1 or 2 digits only")
            return
        value = int(val)
        left, right = self.get_limits(value)
        self.left_var.set(left)
        self.right_var.set(right)
        mid = value if value in SPECIAL_MIDDLES else (left+right)//2
        self.mid_var.set(mid)
        self.update_colors(value,left,right,mid)
        self.add_history(value,left,right)

    def get_limits(self,value):
        if value <= limits[0]:
            return limits[0],limits[1]
        elif value >= limits[-1]:
            return limits[-2],limits[-1]
        for i in range(len(limits)-1):
            if value == limits[i]:
                return limits[i],limits[i+1]
            elif limits[i]<value<limits[i+1]:
                return limits[i],limits[i+1]

    def update_colors(self,value=None,left=None,right=None,mid=None):
        self.left_label.config(bg="green", fg="white")
        self.right_label.config(bg="red", fg="white")
        if mid in SPECIAL_MIDDLES:
            self.mid_label.config(bg="orange", fg="white")
        else:
            self.mid_label.config(bg="white", fg="black")

    # ================= HISTORY =================
    def add_history(self,value,left,right):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"#{len(self.history)+1} | Input:{value} | Left:{left} | Right:{right} | {timestamp}"
        self.history.append(entry)
        self.update_history()

    def update_history(self):
        self.history_text.config(state="normal")
        self.history_text.delete(1.0,tk.END)
        for line in self.history:
            self.history_text.insert(tk.END,line+"\n")
        self.history_text.config(state="disabled")

    def clear_history(self):
        self.history = []
        self.update_history()

    # ================= CLOSE =================
    def close_app(self):
        self.save_config()
        self.root.destroy()

    def save_config(self):
        cfg = {
            "global_alpha": global_alpha,
            "auto_alpha_enabled": auto_alpha_enabled,
            "topmost": topmost,
            "dark_mode": dark_mode,
            "current_font": current_font,
            "current_scale": current_scale
        }
        with open(CONFIG_FILE,"w") as f:
            json.dump(cfg,f)

# ================= RUN =================
if __name__=="__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Horizontal.TScale", background="#121212", foreground="#00FF7F")
    app = TradingWidget(root)
    root.mainloop()
