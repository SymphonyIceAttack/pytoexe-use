import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json, os, hashlib, sys, subprocess, platform
from datetime import datetime, date
import threading, time

# ─────────────────────────────────────────────────────────────────────────────
#  OPTIONAL IMPORTS  (graceful fallback if not installed)
# ─────────────────────────────────────────────────────────────────────────────
try:
    from plyer import notification as plyer_notif
    HAS_PLYER = True
except ImportError:
    HAS_PLYER = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as rl_colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
DATA_FILE = os.path.join(os.path.expanduser("~"), "car_licenses.json")
DEFAULT_PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()
APP_NAME  = "CarLicenseTracker"
SCRIPT_PATH = os.path.abspath(__file__)

WARN_DAYS_1 = 90   # amber
WARN_DAYS_2 = 30   # red

# ── Themes ────────────────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "BG_DARK":      "#0F1117",
        "BG_CARD":      "#1A1D27",
        "BG_INPUT":     "#252836",
        "ACCENT_BLUE":  "#4F8EF7",
        "ACCENT_GREEN": "#2ECC71",
        "ACCENT_AMBER": "#F39C12",
        "ACCENT_RED":   "#E74C3C",
        "TEXT_PRIMARY": "#EAEAEA",
        "TEXT_MUTED":   "#7A7F99",
        "BORDER_COLOR": "#2E3248",
        "HOVER_COLOR":  "#2A2D3E",
    },
    "light": {
        "BG_DARK":      "#F0F2F8",
        "BG_CARD":      "#FFFFFF",
        "BG_INPUT":     "#EEF0F7",
        "ACCENT_BLUE":  "#2563EB",
        "ACCENT_GREEN": "#16A34A",
        "ACCENT_AMBER": "#D97706",
        "ACCENT_RED":   "#DC2626",
        "TEXT_PRIMARY": "#111827",
        "TEXT_MUTED":   "#6B7280",
        "BORDER_COLOR": "#D1D5DB",
        "HOVER_COLOR":  "#E5E7EB",
    }
}

T = THEMES["dark"].copy()   # active theme dict (mutable global)

FONT_TITLE   = ("Segoe UI", 22, "bold")
FONT_HEADING = ("Segoe UI", 13, "bold")
FONT_BODY    = ("Segoe UI", 11)
FONT_SMALL   = ("Segoe UI", 9)

# ─────────────────────────────────────────────────────────────────────────────
#  DATA HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"password": DEFAULT_PASSWORD_HASH, "cars": [],
                "theme": "dark", "startup": False,
                "remind_days": 30, "remind_enabled": True}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
    # back-compat defaults
    d.setdefault("theme", "dark")
    d.setdefault("startup", False)
    d.setdefault("remind_days", 30)
    d.setdefault("remind_enabled", True)
    return d

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def days_left(date_str):
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (d - date.today()).days
    except:
        return None

def status_color(days):
    if days is None:           return T["TEXT_MUTED"]
    if days < 0:               return T["ACCENT_RED"]
    if days <= WARN_DAYS_2:    return T["ACCENT_RED"]
    if days <= WARN_DAYS_1:    return T["ACCENT_AMBER"]
    return T["ACCENT_GREEN"]

def status_label(days):
    if days is None: return "Unknown"
    if days < 0:     return f"Expired {abs(days)}d ago"
    if days == 0:    return "Expires TODAY!"
    return f"{days} days left"

# ─────────────────────────────────────────────────────────────────────────────
#  STARTUP REGISTRATION  (Windows only)
# ─────────────────────────────────────────────────────────────────────────────
def set_startup(enable: bool):
    if platform.system() != "Windows":
        return False
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        if enable:
            cmd = f'pythonw "{SCRIPT_PATH}"'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try: winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError: pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print("Startup reg error:", e)
        return False

def get_startup_state():
    if platform.system() != "Windows":
        return False
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except:
        return False

# ─────────────────────────────────────────────────────────────────────────────
#  STARTUP POPUP REMINDER  (shown before login if urgent cars found)
# ─────────────────────────────────────────────────────────────────────────────
def check_and_show_startup_reminder(data):
    if not data.get("remind_enabled", True):
        return
    remind_days = data.get("remind_days", 30)
    urgent = []
    for car in data.get("cars", []):
        for field, label in [("end_date","Expiry"), ("update_date","Renewal")]:
            d = days_left(car.get(field, ""))
            if d is not None and d <= remind_days:
                urgent.append((car.get("plate","?"), label, d))

    if not urgent:
        return

    # Try native OS notification first
    if HAS_PLYER:
        lines = []
        for plate, label, d in urgent[:5]:
            if d < 0:
                lines.append(f"{plate} {label} EXPIRED {abs(d)}d ago!")
            else:
                lines.append(f"{plate} {label} in {d} day(s)")
        msg = "\n".join(lines)
        try:
            plyer_notif.notify(
                title="🚗 Car License Reminder",
                message=msg,
                app_name="Car License Tracker",
                timeout=10
            )
        except:
            pass

    # Always show in-app popup too
    _show_reminder_popup(urgent)

def _show_reminder_popup(urgent):
    popup = tk.Tk()
    popup.title("⚠ License Reminder")
    popup.configure(bg=T["BG_DARK"])
    popup.resizable(False, False)
    popup.attributes("-topmost", True)

    w, h = 440, min(80 + len(urgent)*56 + 70, 520)
    popup.geometry(f"{w}x{h}")
    popup.update_idletasks()
    px = (popup.winfo_screenwidth()  - w) // 2
    py = (popup.winfo_screenheight() - h) // 2
    popup.geometry(f"{w}x{h}+{px}+{py}")

    tk.Label(popup, text="⚠  License Alert", font=("Segoe UI",16,"bold"),
             bg=T["BG_DARK"], fg=T["ACCENT_RED"]).pack(pady=(20,4))
    tk.Label(popup, text="The following licenses need your attention:",
             font=FONT_SMALL, bg=T["BG_DARK"], fg=T["TEXT_MUTED"]).pack(pady=(0,12))

    for plate, label, d in urgent:
        row = tk.Frame(popup, bg=T["BG_CARD"],
                       highlightthickness=1, highlightbackground=T["BORDER_COLOR"])
        row.pack(fill="x", padx=20, pady=3)
        col = status_color(d)
        tk.Label(row, text=f"🚗  {plate}", font=("Segoe UI",11,"bold"),
                 bg=T["BG_CARD"], fg=T["TEXT_PRIMARY"]).pack(side="left", padx=12, pady=10)
        lbl_txt = f"{label}: " + (f"EXPIRED {abs(d)}d ago" if d<0 else f"{d} day(s) left")
        tk.Label(row, text=lbl_txt, font=("Segoe UI",10,"bold"),
                 bg=T["BG_CARD"], fg=col).pack(side="right", padx=12)

    tk.Button(popup, text="OK — Open App", font=("Segoe UI",11,"bold"),
              bg=T["ACCENT_BLUE"], fg="white", relief="flat", bd=0,
              cursor="hand2", command=popup.destroy).pack(fill="x", padx=20, pady=18, ipady=9)
    popup.mainloop()

# ─────────────────────────────────────────────────────────────────────────────
#  PDF EXPORT
# ─────────────────────────────────────────────────────────────────────────────
def export_pdf(cars, path):
    if not HAS_PDF:
        return False
    doc = SimpleDocTemplate(path, pagesize=A4,
                            rightMargin=40, leftMargin=40,
                            topMargin=60, bottomMargin=40)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("🚗 Car License Report", styles["Title"]))
    elements.append(Paragraph(f"Generated: {date.today()}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    headers = ["Plate", "Model", "Start Date", "Update Date", "Expiry Date", "Days Left", "Status"]
    rows = [headers]
    for car in cars:
        d = days_left(car.get("end_date",""))
        stat = status_label(d)
        rows.append([
            car.get("plate",""),
            car.get("model",""),
            car.get("start_date",""),
            car.get("update_date",""),
            car.get("end_date",""),
            str(d) if d is not None else "?",
            stat,
        ])

    tbl = Table(rows, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,0), rl_colors.HexColor("#2563EB")),
        ("TEXTCOLOR",  (0,0),(-1,0), rl_colors.white),
        ("FONTNAME",   (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0),(-1,0), 10),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[rl_colors.white, rl_colors.HexColor("#F3F4F6")]),
        ("GRID",       (0,0),(-1,-1), 0.5, rl_colors.HexColor("#D1D5DB")),
        ("FONTSIZE",   (0,1),(-1,-1), 9),
        ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
        ("PADDING",    (0,0),(-1,-1), 6),
    ]))
    elements.append(tbl)
    doc.build(elements)
    return True

# ═════════════════════════════════════════════════════════════════════════════
#  LOGIN WINDOW
# ═════════════════════════════════════════════════════════════════════════════
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Car License Tracker — Login")
        self.configure(bg=T["BG_DARK"])
        self.resizable(False, False)
        self.geometry("420x500")
        self._center()
        self._build()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 420) // 2
        y = (self.winfo_screenheight() - 500) // 2
        self.geometry(f"420x500+{x}+{y}")

    def _build(self):
        tk.Label(self, text="🚗", font=("Segoe UI", 52),
                 bg=T["BG_DARK"], fg=T["ACCENT_BLUE"]).pack(pady=(44, 4))
        tk.Label(self, text="Car License Tracker", font=FONT_TITLE,
                 bg=T["BG_DARK"], fg=T["TEXT_PRIMARY"]).pack()
        tk.Label(self, text="Sign in to manage your fleet", font=FONT_SMALL,
                 bg=T["BG_DARK"], fg=T["TEXT_MUTED"]).pack(pady=(4, 28))

        frame = tk.Frame(self, bg=T["BG_CARD"], bd=0, highlightthickness=1,
                         highlightbackground=T["BORDER_COLOR"])
        frame.pack(padx=36, fill="x")
        inner = tk.Frame(frame, bg=T["BG_CARD"])
        inner.pack(padx=24, pady=24, fill="x")

        tk.Label(inner, text="PASSWORD", font=("Segoe UI", 9, "bold"),
                 bg=T["BG_CARD"], fg=T["TEXT_MUTED"]).pack(anchor="w")
        self.pw_var = tk.StringVar()
        pw_entry = tk.Entry(inner, textvariable=self.pw_var, show="●",
                            font=FONT_BODY, bg=T["BG_INPUT"], fg=T["TEXT_PRIMARY"],
                            insertbackground=T["TEXT_PRIMARY"], relief="flat",
                            bd=0, highlightthickness=1,
                            highlightbackground=T["BORDER_COLOR"],
                            highlightcolor=T["ACCENT_BLUE"])
        pw_entry.pack(fill="x", ipady=10, pady=(4, 0))
        pw_entry.bind("<Return>", lambda e: self._login())
        pw_entry.focus()

       
        tk.Button(inner, text="Sign In", font=("Segoe UI", 11, "bold"),
                  bg=T["ACCENT_BLUE"], fg="white", relief="flat", bd=0,
                  activebackground="#3A7AE0", activeforeground="white",
                  cursor="hand2", command=self._login).pack(fill="x", ipady=10,pady=(20, 50))

        self.err_lbl = tk.Label(self, text="", font=FONT_SMALL,
                                bg=T["BG_DARK"], fg=T["ACCENT_RED"])
        self.err_lbl.pack(pady=(12, 0))

    def _login(self):
        data = load_data()
        if hash_pw(self.pw_var.get()) == data["password"]:
            self.destroy()
            MainApp(data).mainloop()
        else:
            self.err_lbl.config(text="❌  Incorrect password. Try again.")
            self.pw_var.set("")

# ═════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ═════════════════════════════════════════════════════════════════════════════
class MainApp(tk.Tk):
    def __init__(self, data):
        super().__init__()
        self.data   = data
        self._apply_theme(data.get("theme","dark"), rebuild=False)
        self.title("Car License Tracker")
        self.configure(bg=T["BG_DARK"])
        self.geometry("1080x700")
        self.minsize(900, 600)
        self._center()
        self._build()
        self._refresh_list()
        # start background reminder ticker (every 60 min)
        self._schedule_bg_check()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 1080) // 2
        y = (self.winfo_screenheight() - 700)  // 2
        self.geometry(f"1080x700+{x}+{y}")

    # ── Theme ─────────────────────────────────────────────────────────────────
    def _apply_theme(self, name, rebuild=True):
        T.update(THEMES.get(name, THEMES["dark"]))
        self.data["theme"] = name
        if rebuild:
            save_data(self.data)
            self._rebuild_ui()

    def _toggle_theme(self):
        cur = self.data.get("theme","dark")
        self._apply_theme("light" if cur=="dark" else "dark")

    def _rebuild_ui(self):
        for w in self.winfo_children():
            w.destroy()
        self.configure(bg=T["BG_DARK"])
        self._build()
        self._refresh_list()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self):
        # ── Top bar
        topbar = tk.Frame(self, bg=T["BG_CARD"], height=62)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="🚗  Car License Tracker",
                 font=("Segoe UI", 15, "bold"),
                 bg=T["BG_CARD"], fg=T["TEXT_PRIMARY"]).pack(side="left", padx=20)

        # right-side buttons
        def tb_btn(text, cmd, bg=None, fg=None):
            b = tk.Button(topbar, text=text, font=FONT_SMALL,
                          bg=bg or T["BG_INPUT"], fg=fg or T["TEXT_MUTED"],
                          relief="flat", bd=0, cursor="hand2",
                          activebackground=T["HOVER_COLOR"],
                          command=cmd)
            b.pack(side="right", padx=4, pady=14, ipadx=10, ipady=4)
            return b

        tb_btn("📤 Export PDF",    self._export_pdf)
        tb_btn("⚙  Settings",     self._open_settings)
        tb_btn("🔒 Change Pwd",   self._change_password)
        theme_icon = "☀" if self.data.get("theme")=="dark" else "🌙"
        tb_btn(f"{theme_icon} Theme", self._toggle_theme)
        tk.Button(topbar, text="＋  Add Car",
                  font=("Segoe UI", 10, "bold"),
                  bg=T["ACCENT_BLUE"], fg="white", relief="flat", bd=0,
                  activebackground="#3A7AE0", cursor="hand2",
                  command=self._open_add_dialog).pack(
                  side="right", padx=(0,4), pady=14, ipadx=12, ipady=4)

        # ── Body
        body = tk.Frame(self, bg=T["BG_DARK"])
        body.pack(fill="both", expand=True, padx=16, pady=16)

        # Sidebar
        left = tk.Frame(body, bg=T["BG_CARD"], width=270,
                        highlightthickness=1, highlightbackground=T["BORDER_COLOR"])
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="MY CARS", font=("Segoe UI", 9, "bold"),
                 bg=T["BG_CARD"], fg=T["TEXT_MUTED"]).pack(anchor="w", padx=16, pady=(16,8))

        # Scrollable list
        canvas_side = tk.Canvas(left, bg=T["BG_CARD"], highlightthickness=0)
        scrollbar   = tk.Scrollbar(left, orient="vertical", command=canvas_side.yview)
        self.list_frame = tk.Frame(canvas_side, bg=T["BG_CARD"])
        self.list_frame.bind("<Configure>",
            lambda e: canvas_side.configure(scrollregion=canvas_side.bbox("all")))
        canvas_side.create_window((0,0), window=self.list_frame, anchor="nw")
        canvas_side.configure(yscrollcommand=scrollbar.set)
        canvas_side.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Detail
        self.detail_frame = tk.Frame(body, bg=T["BG_DARK"])
        self.detail_frame.pack(side="left", fill="both", expand=True, padx=(16,0))

        self._show_welcome()

    # ── Sidebar list ──────────────────────────────────────────────────────────
    def _refresh_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        if not self.data["cars"]:
            tk.Label(self.list_frame,
                     text="No cars yet.\nClick ＋ Add Car.",
                     font=FONT_SMALL, bg=T["BG_CARD"], fg=T["TEXT_MUTED"],
                     justify="center").pack(pady=40)
            return
        for i, car in enumerate(self.data["cars"]):
            d = days_left(car.get("end_date",""))
            self._make_car_btn(i, car, status_color(d))

    def _make_car_btn(self, i, car, col):
        frame = tk.Frame(self.list_frame, bg=T["BG_CARD"], cursor="hand2")
        frame.pack(fill="x", pady=3, padx=4)
        bar = tk.Frame(frame, bg=col, width=4)
        bar.pack(side="left", fill="y")
        inner = tk.Frame(frame, bg=T["BG_CARD"])
        inner.pack(side="left", fill="x", expand=True, padx=8, pady=8)
        tk.Label(inner, text=car.get("plate",""), font=("Segoe UI",11,"bold"),
                 bg=T["BG_CARD"], fg=T["TEXT_PRIMARY"], anchor="w").pack(fill="x")
        tk.Label(inner, text=car.get("model",""), font=FONT_SMALL,
                 bg=T["BG_CARD"], fg=T["TEXT_MUTED"], anchor="w").pack(fill="x")
        d = days_left(car.get("end_date",""))
        tk.Label(inner, text=status_label(d), font=("Segoe UI",8,"bold"),
                 bg=T["BG_CARD"], fg=col, anchor="w").pack(fill="x")
        for w in [frame, bar, inner] + list(inner.winfo_children()):
            w.bind("<Button-1>", lambda e, idx=i: self._show_car(idx))
            w.bind("<Enter>",    lambda e, f=inner: f.config(bg=T["HOVER_COLOR"]))
            w.bind("<Leave>",    lambda e, f=inner: f.config(bg=T["BG_CARD"]))

    # ── Welcome ───────────────────────────────────────────────────────────────
    def _show_welcome(self):
        for w in self.detail_frame.winfo_children():
            w.destroy()
        tk.Label(self.detail_frame, text="🚗", font=("Segoe UI",64),
                 bg=T["BG_DARK"], fg=T["BORDER_COLOR"]).pack(pady=(80,8))
        tk.Label(self.detail_frame, text="Select a car to see details",
                 font=FONT_HEADING, bg=T["BG_DARK"], fg=T["TEXT_MUTED"]).pack()
        tk.Label(self.detail_frame, text="or click  ＋ Add Car  to get started.",
                 font=FONT_SMALL, bg=T["BG_DARK"], fg=T["TEXT_MUTED"]).pack(pady=4)

    # ── Detail panel ──────────────────────────────────────────────────────────
    def _show_car(self, idx):
        car = self.data["cars"][idx]
        for w in self.detail_frame.winfo_children():
            w.destroy()

        # Header card
        hdr = tk.Frame(self.detail_frame, bg=T["BG_CARD"],
                       highlightthickness=1, highlightbackground=T["BORDER_COLOR"])
        hdr.pack(fill="x", pady=(0,12))
        hi = tk.Frame(hdr, bg=T["BG_CARD"])
        hi.pack(padx=24, pady=20, fill="x")
        lh = tk.Frame(hi, bg=T["BG_CARD"])
        lh.pack(side="left", fill="x", expand=True)
        tk.Label(lh, text=car.get("plate",""), font=("Segoe UI",26,"bold"),
                 bg=T["BG_CARD"], fg=T["TEXT_PRIMARY"]).pack(anchor="w")
        tk.Label(lh, text=car.get("model",""), font=("Segoe UI",13),
                 bg=T["BG_CARD"], fg=T["TEXT_MUTED"]).pack(anchor="w")
        rh = tk.Frame(hi, bg=T["BG_CARD"])
        rh.pack(side="right")
        for txt, cmd, bg, fg in [
            ("✏  Edit", lambda: self._open_edit_dialog(idx), T["BG_INPUT"], T["TEXT_PRIMARY"]),
            ("🗑  Delete", lambda: self._delete_car(idx), "#3D1A1A", T["ACCENT_RED"]),
        ]:
            tk.Button(rh, text=txt, font=FONT_SMALL, bg=bg, fg=fg,
                      relief="flat", bd=0, cursor="hand2",
                      activebackground=T["HOVER_COLOR"],
                      command=cmd).pack(side="left", padx=4, ipady=6, ipadx=10)

        # Stat cards row
        stats = tk.Frame(self.detail_frame, bg=T["BG_DARK"])
        stats.pack(fill="x", pady=(0,12))
        for lbl, val, d in [
            ("📅 Start Date",  car.get("start_date","—"), None),
            ("🔄 Update Date", car.get("update_date","—"), days_left(car.get("update_date",""))),
            ("⚠️ End Date",    car.get("end_date","—"),   days_left(car.get("end_date",""))),
        ]:
            self._stat_card(stats, lbl, val, d)

        # Timeline
        self._build_timeline(car)

        # Reminder banner
        d_end    = days_left(car.get("end_date",""))
        d_update = days_left(car.get("update_date",""))
        remind   = self.data.get("remind_days", 30)
        for d_val, kind in [(d_end,"Expiry"), (d_update,"Renewal")]:
            if d_val is not None and d_val <= remind:
                self._reminder_banner(kind, d_val)

        # Notes
        if car.get("notes","").strip():
            nf = tk.Frame(self.detail_frame, bg=T["BG_CARD"],
                          highlightthickness=1, highlightbackground=T["BORDER_COLOR"])
            nf.pack(fill="x", pady=(0,12))
            ni = tk.Frame(nf, bg=T["BG_CARD"])
            ni.pack(padx=20, pady=16, fill="x")
            tk.Label(ni, text="📝 Notes", font=("Segoe UI",10,"bold"),
                     bg=T["BG_CARD"], fg=T["TEXT_MUTED"]).pack(anchor="w")
            tk.Label(ni, text=car["notes"], font=FONT_BODY,
                     bg=T["BG_CARD"], fg=T["TEXT_PRIMARY"],
                     wraplength=560, justify="left").pack(anchor="w", pady=(6,0))

    def _reminder_banner(self, kind, d):
        col = T["ACCENT_RED"] if d <= WARN_DAYS_2 else T["ACCENT_AMBER"]
        bg  = "#3D1A1A" if d <= WARN_DAYS_2 else "#3D2E0A"
        if self.data.get("theme") == "light":
            bg = "#FEE2E2" if d <= WARN_DAYS_2 else "#FEF3C7"
        banner = tk.Frame(self.detail_frame, bg=bg,
                          highlightthickness=1, highlightbackground=col)
        banner.pack(fill="x", pady=(0,8))
        msg = f"{'🚨' if d<=WARN_DAYS_2 else '⚠️'}  {kind} "
        msg += f"EXPIRED {abs(d)} day(s) ago!" if d < 0 else (
               f"TODAY!" if d==0 else f"in {d} day(s) — action required!")
        tk.Label(banner, text=msg, font=("Segoe UI",10,"bold"),
                 bg=bg, fg=col).pack(padx=16, pady=10, anchor="w")

    def _stat_card(self, parent, label, val, days_val):
        card = tk.Frame(parent, bg=T["BG_CARD"],
                        highlightthickness=1, highlightbackground=T["BORDER_COLOR"])
        card.pack(side="left", fill="both", expand=True, padx=(0,8))
        inner = tk.Frame(card, bg=T["BG_CARD"])
        inner.pack(padx=16, pady=14)
        tk.Label(inner, text=label, font=("Segoe UI",9,"bold"),
                 bg=T["BG_CARD"], fg=T["TEXT_MUTED"]).pack(anchor="w")
        tk.Label(inner, text=val, font=("Segoe UI",15,"bold"),
                 bg=T["BG_CARD"], fg=T["TEXT_PRIMARY"]).pack(anchor="w", pady=(4,2))
        if days_val is not None:
            col = status_color(days_val)
            tk.Label(inner, text=status_label(days_val), font=("Segoe UI",9,"bold"),
                     bg=T["BG_CARD"], fg=col).pack(anchor="w")

    def _build_timeline(self, car):
        tf = tk.Frame(self.detail_frame, bg=T["BG_CARD"],
                      highlightthickness=1, highlightbackground=T["BORDER_COLOR"])
        tf.pack(fill="x", pady=(0,12))
        inner = tk.Frame(tf, bg=T["BG_CARD"])
        inner.pack(padx=20, pady=16, fill="x")
        tk.Label(inner, text="LICENSE TIMELINE", font=("Segoe UI",9,"bold"),
                 bg=T["BG_CARD"], fg=T["TEXT_MUTED"]).pack(anchor="w", pady=(0,10))
        try:
            s     = datetime.strptime(car.get("start_date",""), "%Y-%m-%d").date()
            e     = datetime.strptime(car.get("end_date",""),   "%Y-%m-%d").date()
            today = date.today()
            total   = max(1, (e - s).days)
            elapsed = max(0, min(total, (today - s).days))
            pct     = elapsed / total
        except:
            pct, s, e, today = 0, date.today(), date.today(), date.today()
            total = 1

        bar_w, bar_h = 560, 28
        canv = tk.Canvas(inner, width=bar_w, height=bar_h,
                         bg=T["BG_CARD"], highlightthickness=0)
        canv.pack(fill="x")
        canv.create_rectangle(0, 4, bar_w, bar_h-4, fill=T["BG_INPUT"], outline="")
        fill_w = int(bar_w * pct)
        col    = status_color(days_left(car.get("end_date","")))
        if fill_w > 0:
            canv.create_rectangle(0, 4, fill_w, bar_h-4, fill=col, outline="")
        dot_x = max(10, min(bar_w-10, fill_w))
        canv.create_oval(dot_x-6, 4, dot_x+6, bar_h-4, fill=col,
                         outline=T["BG_CARD"], width=2)

        lf = tk.Frame(inner, bg=T["BG_CARD"])
        lf.pack(fill="x", pady=(6,0))
        tk.Label(lf, text=str(s), font=FONT_SMALL, bg=T["BG_CARD"], fg=T["TEXT_MUTED"]).pack(side="left")
        tk.Label(lf, text=f"{int(pct*100)}% elapsed", font=("Segoe UI",9,"bold"),
                 bg=T["BG_CARD"], fg=col).pack(side="left", expand=True)
        tk.Label(lf, text=str(e), font=FONT_SMALL, bg=T["BG_CARD"], fg=T["TEXT_MUTED"]).pack(side="right")

    # ── Add / Edit dialog ─────────────────────────────────────────────────────
    def _open_add_dialog(self):  self._car_dialog(None)
    def _open_edit_dialog(self, idx): self._car_dialog(idx)

    def _car_dialog(self, idx):
        is_edit = idx is not None
        car = self.data["cars"][idx] if is_edit else {}
        dlg = tk.Toplevel(self)
        dlg.title("Edit Car" if is_edit else "Add New Car")
        dlg.configure(bg=T["BG_DARK"])
        dlg.geometry("480x570")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - 480) // 2
        y = self.winfo_y() + (self.winfo_height() - 570) // 2
        dlg.geometry(f"480x570+{x}+{y}")

        tk.Label(dlg, text="✏  Edit Car" if is_edit else "＋  Add New Car",
                 font=FONT_HEADING, bg=T["BG_DARK"], fg=T["TEXT_PRIMARY"]).pack(
                 pady=(24,4), padx=32, anchor="w")
        tk.Label(dlg, text="Dates must be in YYYY-MM-DD format",
                 font=FONT_SMALL, bg=T["BG_DARK"], fg=T["TEXT_MUTED"]).pack(
                 padx=32, anchor="w", pady=(0,16))

        fields = {}
        for key, lbl in [
            ("plate",       "License Plate  (e.g. ABC-1234)"),
            ("model",       "Car Model  (e.g. Toyota Camry 2020)"),
            ("start_date",  "Start Date  (YYYY-MM-DD)"),
            ("update_date", "Update / Renewal Date  (YYYY-MM-DD)"),
            ("end_date",    "Expiry Date  (YYYY-MM-DD)"),
            ("notes",       "Notes  (optional)"),
        ]:
            tk.Label(dlg, text=lbl, font=("Segoe UI",9,"bold"),
                     bg=T["BG_DARK"], fg=T["TEXT_MUTED"]).pack(anchor="w", padx=32, pady=(4,0))
            var = tk.StringVar(value=car.get(key,""))
            e   = tk.Entry(dlg, textvariable=var, font=FONT_BODY,
                           bg=T["BG_INPUT"], fg=T["TEXT_PRIMARY"],
                           insertbackground=T["TEXT_PRIMARY"],
                           relief="flat", bd=0, highlightthickness=1,
                           highlightbackground=T["BORDER_COLOR"],
                           highlightcolor=T["ACCENT_BLUE"])
            e.pack(fill="x", padx=32, ipady=9, pady=(3,0))
            fields[key] = var

        btn_row = tk.Frame(dlg, bg=T["BG_DARK"])
        btn_row.pack(fill="x", padx=32, pady=20, side="bottom")

        def save():
            plate = fields["plate"].get().strip()
            if not plate:
                messagebox.showerror("Error","License plate is required.", parent=dlg); return
            for lbl2, val in [("Start Date", fields["start_date"].get()),
                               ("Expiry Date", fields["end_date"].get())]:
                if val.strip():
                    try: datetime.strptime(val.strip(), "%Y-%m-%d")
                    except: messagebox.showerror("Error", f"{lbl2} must be YYYY-MM-DD.", parent=dlg); return
            new_car = {k: v.get().strip() for k,v in fields.items()}
            if is_edit: self.data["cars"][idx] = new_car
            else:       self.data["cars"].append(new_car)
            save_data(self.data)
            self._refresh_list()
            if is_edit: self._show_car(idx)
            dlg.destroy()

        tk.Button(btn_row, text="Cancel", font=FONT_BODY,
                  bg=T["BG_INPUT"], fg=T["TEXT_MUTED"], relief="flat", bd=0,
                  cursor="hand2", activebackground=T["HOVER_COLOR"],
                  command=dlg.destroy).pack(side="left", ipady=8, ipadx=16)
        tk.Button(btn_row, text="Save Car", font=("Segoe UI",11,"bold"),
                  bg=T["ACCENT_BLUE"], fg="white", relief="flat", bd=0,
                  cursor="hand2", activebackground="#3A7AE0",
                  command=save).pack(side="right", ipady=8, ipadx=20)

    # ── Delete ────────────────────────────────────────────────────────────────
    def _delete_car(self, idx):
        plate = self.data["cars"][idx].get("plate","this car")
        if messagebox.askyesno("Delete Car", f"Remove {plate}?", icon="warning", parent=self):
            self.data["cars"].pop(idx)
            save_data(self.data)
            self._refresh_list()
            self._show_welcome()

    # ── Change password ───────────────────────────────────────────────────────
    def _change_password(self):
        dlg = tk.Toplevel(self)
        dlg.title("Change Password")
        dlg.configure(bg=T["BG_DARK"])
        dlg.geometry("380x320")
        dlg.resizable(False,False)
        dlg.grab_set()
        dlg.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() -380)//2
        y = self.winfo_y() + (self.winfo_height()-320)//2
        dlg.geometry(f"380x320+{x}+{y}")

        tk.Label(dlg, text="🔒  Change Password", font=FONT_HEADING,
                 bg=T["BG_DARK"], fg=T["TEXT_PRIMARY"]).pack(pady=(24,16), padx=24, anchor="w")
        vars_ = {}
        for lbl, key in [("Current Password","current"),("New Password","new"),("Confirm New","confirm")]:
            tk.Label(dlg, text=lbl, font=("Segoe UI",9,"bold"),
                     bg=T["BG_DARK"], fg=T["TEXT_MUTED"]).pack(anchor="w", padx=24, pady=(6,0))
            v = tk.StringVar()
            tk.Entry(dlg, textvariable=v, show="●", font=FONT_BODY,
                     bg=T["BG_INPUT"], fg=T["TEXT_PRIMARY"],
                     insertbackground=T["TEXT_PRIMARY"],
                     relief="flat", bd=0, highlightthickness=1,
                     highlightbackground=T["BORDER_COLOR"],
                     highlightcolor=T["ACCENT_BLUE"]).pack(fill="x", padx=24, ipady=9, pady=(3,0))
            vars_[key] = v
        err = tk.Label(dlg, text="", font=FONT_SMALL, bg=T["BG_DARK"], fg=T["ACCENT_RED"])
        err.pack(pady=(8,0))
        def save():
            if hash_pw(vars_["current"].get()) != self.data["password"]:
                err.config(text="Current password is incorrect."); return
            if vars_["new"].get() != vars_["confirm"].get():
                err.config(text="New passwords do not match."); return
            if len(vars_["new"].get()) < 4:
                err.config(text="Password must be at least 4 characters."); return
            self.data["password"] = hash_pw(vars_["new"].get())
            save_data(self.data)
            dlg.destroy()
            messagebox.showinfo("Success","Password updated!")
        tk.Button(dlg, text="Update Password", font=("Segoe UI",11,"bold"),
                  bg=T["ACCENT_BLUE"], fg="white", relief="flat", bd=0,
                  cursor="hand2", command=save).pack(fill="x", padx=24, pady=16, ipady=9)

    # ── Settings dialog ───────────────────────────────────────────────────────
    def _open_settings(self):
        dlg = tk.Toplevel(self)
        dlg.title("Settings")
        dlg.configure(bg=T["BG_DARK"])
        dlg.geometry("440x420")
        dlg.resizable(False,False)
        dlg.grab_set()
        dlg.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() -440)//2
        y = self.winfo_y() + (self.winfo_height()-420)//2
        dlg.geometry(f"440x420+{x}+{y}")

        tk.Label(dlg, text="⚙  Settings", font=FONT_HEADING,
                 bg=T["BG_DARK"], fg=T["TEXT_PRIMARY"]).pack(pady=(24,20), padx=28, anchor="w")

        # ── Startup toggle
        section(dlg, "🚀  Run on PC Startup  (Windows only)")
        startup_var = tk.BooleanVar(value=get_startup_state())
        row = tk.Frame(dlg, bg=T["BG_DARK"])
        row.pack(fill="x", padx=28, pady=(4,16))
        tk.Label(row, text="Launch automatically when Windows starts",
                 font=FONT_SMALL, bg=T["BG_DARK"], fg=T["TEXT_MUTED"]).pack(side="left")
        def toggle_startup():
            ok = set_startup(startup_var.get())
            if not ok:
                messagebox.showinfo("Note","Startup registration only works on Windows.",parent=dlg)
                startup_var.set(False)
            else:
                self.data["startup"] = startup_var.get()
                save_data(self.data)
        tk.Checkbutton(row, variable=startup_var, bg=T["BG_DARK"],
                       activebackground=T["BG_DARK"],
                       fg=T["ACCENT_BLUE"], selectcolor=T["BG_INPUT"],
                       command=toggle_startup).pack(side="right")

        # ── Reminder toggle
        section(dlg, "🔔  Popup Reminders")
        remind_var = tk.BooleanVar(value=self.data.get("remind_enabled", True))
        row2 = tk.Frame(dlg, bg=T["BG_DARK"])
        row2.pack(fill="x", padx=28, pady=(4,0))
        tk.Label(row2, text="Show reminder popups for upcoming expiries",
                 font=FONT_SMALL, bg=T["BG_DARK"], fg=T["TEXT_MUTED"]).pack(side="left")
        tk.Checkbutton(row2, variable=remind_var, bg=T["BG_DARK"],
                       activebackground=T["BG_DARK"],
                       fg=T["ACCENT_BLUE"], selectcolor=T["BG_INPUT"]).pack(side="right")

        # ── Days threshold
        section(dlg, "📅  Remind me when fewer than X days remain")
        days_var = tk.IntVar(value=self.data.get("remind_days",30))
        row3 = tk.Frame(dlg, bg=T["BG_DARK"])
        row3.pack(fill="x", padx=28, pady=(4,16))
        tk.Scale(row3, variable=days_var, from_=7, to=180, orient="horizontal",
                 bg=T["BG_DARK"], fg=T["TEXT_PRIMARY"], troughcolor=T["BG_INPUT"],
                 highlightthickness=0, length=300).pack(side="left")
        tk.Label(row3, textvariable=days_var, font=("Segoe UI",12,"bold"),
                 bg=T["BG_DARK"], fg=T["ACCENT_BLUE"]).pack(side="left", padx=8)
        tk.Label(row3, text="days", font=FONT_SMALL,
                 bg=T["BG_DARK"], fg=T["TEXT_MUTED"]).pack(side="left")

        def save_settings():
            self.data["remind_enabled"] = remind_var.get()
            self.data["remind_days"]    = days_var.get()
            save_data(self.data)
            dlg.destroy()
            messagebox.showinfo("Saved","Settings saved!")

        tk.Button(dlg, text="Save Settings", font=("Segoe UI",11,"bold"),
                  bg=T["ACCENT_BLUE"], fg="white", relief="flat", bd=0,
                  cursor="hand2", command=save_settings).pack(
                  fill="x", padx=28, pady=20, ipady=9, side="bottom")

    # ── PDF Export ────────────────────────────────────────────────────────────
    def _export_pdf(self):
        if not HAS_PDF:
            messagebox.showinfo("Install Required",
                "To export PDF, install reportlab:\n\npip install reportlab", parent=self)
            return
        if not self.data["cars"]:
            messagebox.showinfo("No Cars","Add some cars first!", parent=self); return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files","*.pdf")],
            initialfile=f"car_licenses_{date.today()}.pdf",
            parent=self)
        if not path: return
        ok = export_pdf(self.data["cars"], path)
        if ok:
            messagebox.showinfo("Exported", f"PDF saved to:\n{path}", parent=self)
            if platform.system() == "Windows":
                os.startfile(path)
        else:
            messagebox.showerror("Error","PDF export failed.", parent=self)

    # ── Background reminder check ─────────────────────────────────────────────
    def _schedule_bg_check(self):
        self._bg_check()
        # Check every 60 minutes
        self.after(60 * 60 * 1000, self._schedule_bg_check)

    def _bg_check(self):
        if not self.data.get("remind_enabled", True): return
        remind = self.data.get("remind_days", 30)
        urgent = []
        for car in self.data.get("cars", []):
            for field, label in [("end_date","Expiry"), ("update_date","Renewal")]:
                d = days_left(car.get(field,""))
                if d is not None and d <= remind:
                    urgent.append((car.get("plate","?"), label, d))
        if urgent and HAS_PLYER:
            lines = [f"{p} {l}: " + (f"EXPIRED" if d<0 else f"{d}d left")
                     for p, l, d in urgent[:4]]
            try:
                plyer_notif.notify(
                    title="🚗 Car License Reminder",
                    message="\n".join(lines),
                    app_name="Car License Tracker",
                    timeout=8)
            except: pass

# ── Helper ────────────────────────────────────────────────────────────────────
def section(parent, text):
    tk.Label(parent, text=text, font=("Segoe UI",10,"bold"),
             bg=T["BG_DARK"], fg=T["TEXT_PRIMARY"]).pack(anchor="w", padx=28, pady=(12,0))
    tk.Frame(parent, bg=T["BORDER_COLOR"], height=1).pack(fill="x", padx=28, pady=(4,0))

# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    data = load_data()
    # Apply saved theme before any window opens
    T.update(THEMES.get(data.get("theme","dark"), THEMES["dark"]))
    # Show startup reminder popup (if needed)
    check_and_show_startup_reminder(data)
    # Open login
    LoginWindow().mainloop()
