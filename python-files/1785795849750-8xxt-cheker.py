import subprocess
import json
import os
import sys
import threading
import time
import math
import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# ==================== СЕРВЕРА ====================
SERVERS = [
    {"name": "Downtown",  "emoji": "🌆", "host": "downtown.gta5rp.com",  "port": "22005"},
    {"name": "Strawberry","emoji": "🍓", "host": "strawberry.gta5rp.com","port": "22005"},
    {"name": "Vinewood",  "emoji": "🏰", "host": "vinewood.gta5rp.com",  "port": "22005"},
    {"name": "Blackberry","emoji": "🍇", "host": "blackberry.gta5rp.com","port": "22005"},
    {"name": "Insquad",   "emoji": "🎭", "host": "insquad.gta5rp.com",   "port": "22005"},
    {"name": "Sunrise",   "emoji": "🌅", "host": "sunrise.gta5rp.com",   "port": "22005"},
    {"name": "Rainbow",   "emoji": "🌈", "host": "rainbow.gta5rp.com",   "port": "22005"},
    {"name": "Richman",   "emoji": "🤵", "host": "richman.gta5rp.com",   "port": "22005"},
    {"name": "Eclipse",   "emoji": "🌘", "host": "eclipse.gta5rp.com",   "port": "22005"},
    {"name": "La Mesa",   "emoji": "🌵", "host": "lamesa.gta5rp.com",    "port": "22005"},
    {"name": "Burton",    "emoji": "🏛", "host": "burton.gta5rp.com",    "port": "22005"},
    {"name": "Rockford",  "emoji": "💎", "host": "rockford.gta5rp.com",  "port": "22005"},
    {"name": "Alta",      "emoji": "🍀", "host": "alta.gta5rp.com",      "port": "22005"},
    {"name": "Del Perro", "emoji": "🎡", "host": "delperro.gta5rp.com",  "port": "22005"},
    {"name": "Davis",     "emoji": "🏀", "host": "davis.gta5rp.com",     "port": "22005"},
    {"name": "Harmony",   "emoji": "🌸", "host": "harmony.gta5rp.com",   "port": "22005"},
    {"name": "Redwood",   "emoji": "🌲", "host": "redwood.gta5rp.com",   "port": "22005"},
    {"name": "Hawick",    "emoji": "💵", "host": "hawick.gta5rp.com",    "port": "22005"},
    {"name": "Grapeseed", "emoji": "🌱", "host": "grapeseed.gta5rp.com", "port": "22005"},
    {"name": "Murrieta",  "emoji": "🌹", "host": "murrieta.gta5rp.com",  "port": "22005"},
    {"name": "Vespucci",  "emoji": "🛶", "host": "vespucci.gta5rp.com",  "port": "22005"},
    {"name": "Milton",    "emoji": "🍸", "host": "milton.gta5rp.com",    "port": "22005"},
    {"name": "La Puerta", "emoji": "🪇", "host": "lapuerta.gta5rp.com",  "port": "22005"},
    {"name": "Senora",    "emoji": "🦂", "host": "senora.gta5rp.com",    "port": "22005"},
]

CHECK_INTERVAL = 0.3  # сек между циклами опроса ВСЕХ серверов (минимум, ограничен сетью)
MAX_WORKERS = 8

# ==================== ЧЁРНАЯ КОММЕРЧЕСКАЯ ПАЛИТРА ====================
COLOR_BG            = "#05070C"
COLOR_SIDEBAR       = "#080B12"
COLOR_SIDEBAR_HOVER = "#0F1420"
COLOR_SIDEBAR_SEL   = "#151C2B"

COLOR_GLASS         = "#0C101A"
COLOR_GLASS_LIGHT   = "#121826"
COLOR_GLASS_BORDER  = "#1E2738"
COLOR_GLASS_GLOW    = "#162033"

COLOR_ACCENT        = "#6366F1"
COLOR_ACCENT_GLOW   = "#2E2A75"
COLOR_GREEN         = "#10B981"
COLOR_GREEN_GLOW    = "#053F2E"
COLOR_RED           = "#F43F5E"
COLOR_RED_GLOW      = "#7A1229"
COLOR_AMBER         = "#F59E0B"
COLOR_AMBER_GLOW    = "#6B3A08"
COLOR_CYAN          = "#22D3EE"

COLOR_TEXT          = "#F1F5F9"
COLOR_TEXT_SEC      = "#94A3B8"
COLOR_TEXT_MUTED    = "#64748B"
COLOR_TEXT_DIM      = "#3F4A5C"

COLOR_CLOSE         = "#EF4444"
COLOR_CLOSE_HOVER   = "#DC2626"
COLOR_MIN           = "#64748B"
COLOR_MIN_HOVER     = "#94A3B8"


def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*(max(0, min(255, int(c))) for c in rgb))

def blend(c1, c2, t):
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    return rgb_to_hex(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


# ==================== СТЕКЛЯННАЯ КАРТОЧКА ====================
class GlassCard(tk.Canvas):
    def __init__(self, parent, bg=COLOR_GLASS, border=COLOR_GLASS_BORDER, radius=18, glow=True, **kw):
        super().__init__(parent, bg=parent["bg"], highlightthickness=0, **kw)
        self.bg_c = bg
        self.border_c = border
        self.radius = radius
        self.glow = glow
        self.bind("<Configure>", self._draw)

    def _draw(self, _=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        r = self.radius
        if w < 2 * r or h < 2 * r:
            return

        for i, a in enumerate([0.45, 0.28, 0.15]):
            off = i + 2
            shadow = blend("#000000", COLOR_BG, 1 - a)
            self._rounded(off, off, w - off, h - off, r, shadow)

        if self.glow:
            self._rounded(0, 0, w, h, r, COLOR_GLASS_GLOW)

        self._rounded(1, 1, w - 1, h - 1, r - 1, self.border_c)
        self._rounded(2, 2, w - 2, h - 2, r - 2, self.bg_c)

        hi = blend(self.bg_c, "#FFFFFF", 0.05)
        self.create_rectangle(r, 3, w - r, 5, fill=hi, outline="")

    def _rounded(self, x1, y1, x2, y2, r, color):
        self.create_arc(x1, y1, x1 + 2*r, y1 + 2*r, start=90, extent=90, fill=color, outline="")
        self.create_arc(x2 - 2*r, y1, x2, y1 + 2*r, start=0, extent=90, fill=color, outline="")
        self.create_arc(x1, y2 - 2*r, x1 + 2*r, y2, start=180, extent=90, fill=color, outline="")
        self.create_arc(x2 - 2*r, y2 - 2*r, x2, y2, start=270, extent=90, fill=color, outline="")
        self.create_rectangle(x1 + r, y1, x2 - r, y2, fill=color, outline="")
        self.create_rectangle(x1, y1 + r, x2, y2 - r, fill=color, outline="")


# ==================== ПРЕМИУМ КНОПКА ====================
class PremiumButton(tk.Canvas):
    def __init__(self, parent, text, bg, fg, hover, command=None, height=52, font=None, radius=14):
        super().__init__(parent, bg=parent["bg"], highlightthickness=0, height=height, cursor="hand2")
        self.cmd = command
        self.curr = bg
        self.target = bg
        self.default = bg
        self.hover = hover
        self.fg = fg
        self.txt = text
        self.font = font
        self.radius = radius

        self.bind("<Configure>", self._draw)
        self.bind("<Enter>", lambda e: self._go(self.hover))
        self.bind("<Leave>", lambda e: self._go(self.default))
        self.bind("<Button-1>", lambda e: self.cmd() if self.cmd else None)

    def _draw(self, _=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        r = self.radius
        if w < 2 * r or h < 2 * r:
            return

        self.create_arc(2, 3, 2+2*r, 3+2*r, start=90, extent=90, fill="#03050A", outline="")
        self.create_arc(w-2-2*r, 3, w-2, 3+2*r, start=0, extent=90, fill="#03050A", outline="")
        self.create_arc(2, h-1-2*r, 2+2*r, h-1, start=180, extent=90, fill="#03050A", outline="")
        self.create_arc(w-2-2*r, h-1-2*r, w-2, h-1, start=270, extent=90, fill="#03050A", outline="")
        self.create_rectangle(2+r, 3, w-2-r, h-1, fill="#03050A", outline="")
        self.create_rectangle(2, 3+r, w-2, h-1-r, fill="#03050A", outline="")

        self.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=self.curr, outline="")
        self.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=self.curr, outline="")
        self.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=self.curr, outline="")
        self.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=self.curr, outline="")
        self.create_rectangle(r, 0, w-r, h, fill=self.curr, outline="")
        self.create_rectangle(0, r, w, h-r, fill=self.curr, outline="")

        hi = blend(self.curr, "#FFFFFF", 0.11)
        self.create_rectangle(r, 1, w-r, 4, fill=hi, outline="")

        self.create_text(w/2, h/2, text=self.txt, fill=self.fg, font=self.font)

    def _go(self, color):
        self.target = color
        self._step()

    def _step(self):
        if self.curr != self.target:
            self.curr = blend(self.curr, self.target, 0.30)
            self._draw()
            self.after(13, self._step)

    def set_config(self, text, bg, fg, hover):
        self.txt = text
        self.default = bg
        self.curr = bg
        self.target = bg
        self.fg = fg
        self.hover = hover
        self._draw()


# ==================== NEON BAR ====================
class NeonBar(tk.Canvas):
    def __init__(self, parent, height=10, **kw):
        super().__init__(parent, bg=parent["bg"], highlightthickness=0, height=height, **kw)
        self.progress = 0.0
        self.color = COLOR_GREEN
        self.bind("<Configure>", self._draw)

    def set(self, ratio, color):
        self.progress = max(0.0, min(1.0, ratio))
        self.color = color
        self._draw()

    def _draw(self, _=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        r = h // 2
        if w <= 0:
            return

        self.create_arc(0, 0, 2*r, h, start=90, extent=180, fill="#0A0E16", outline="")
        self.create_arc(w-2*r, 0, w, h, start=270, extent=180, fill="#0A0E16", outline="")
        self.create_rectangle(r, 0, w-r, h, fill="#0A0E16", outline="")

        if self.progress <= 0:
            return

        pw = max(2*r, int(w * self.progress))

        glow = blend(self.color, "#000000", 0.6)
        self.create_arc(0, 1, 2*r, h+1, start=90, extent=180, fill=glow, outline="")
        if pw >= 2*r:
            self.create_arc(pw-2*r, 1, pw, h+1, start=270, extent=180, fill=glow, outline="")
            self.create_rectangle(r, 1, pw-r, h+1, fill=glow, outline="")

        self.create_arc(0, 0, 2*r, h, start=90, extent=180, fill=self.color, outline="")
        if pw >= 2*r:
            self.create_arc(pw-2*r, 0, pw, h, start=270, extent=180, fill=self.color, outline="")
            self.create_rectangle(r, 0, pw-r, h, fill=self.color, outline="")

        hi = blend(self.color, "#FFFFFF", 0.22)
        self.create_rectangle(r, 1, max(r+1, pw-r), 3, fill=hi, outline="")


# ==================== SERVER ROW ====================
class ServerRow(tk.Canvas):
    def __init__(self, parent, server, on_click, fonts):
        super().__init__(parent, bg=COLOR_SIDEBAR, highlightthickness=0, height=56, cursor="hand2")
        self.server = server
        self.on_click = on_click
        self.fonts = fonts
        self.selected = False
        self.status = "pending"
        self.players = None
        self.maxplayers = None
        self.bg_curr = COLOR_SIDEBAR
        self.bg_target = COLOR_SIDEBAR

        self.bind("<Configure>", self._draw)
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Button-1>", lambda e: self.on_click(self.server))

    def _enter(self, _):
        if not self.selected:
            self._anim(COLOR_SIDEBAR_HOVER)

    def _leave(self, _):
        if not self.selected:
            self._anim(COLOR_SIDEBAR)

    def _anim(self, target):
        self.bg_target = target
        self._step()

    def _step(self):
        if self.bg_curr != self.bg_target:
            self.bg_curr = blend(self.bg_curr, self.bg_target, 0.34)
            self._draw()
            self.after(13, self._step)

    def set_selected(self, sel):
        self.selected = sel
        self.bg_target = COLOR_SIDEBAR_SEL if sel else COLOR_SIDEBAR
        self.bg_curr = self.bg_target
        self._draw()

    def update_status(self, online, players, maxplayers):
        self.status = "online" if online else "offline"
        self.players = players
        self.maxplayers = maxplayers
        self._draw()

    def _draw(self, _=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        r = 11

        self.create_arc(5, 2, 5+2*r, 2+2*r, start=90, extent=90, fill=self.bg_curr, outline="")
        self.create_arc(w-5-2*r, 2, w-5, 2+2*r, start=0, extent=90, fill=self.bg_curr, outline="")
        self.create_arc(5, h-2-2*r, 5+2*r, h-2, start=180, extent=90, fill=self.bg_curr, outline="")
        self.create_arc(w-5-2*r, h-2-2*r, w-5, h-2, start=270, extent=90, fill=self.bg_curr, outline="")
        self.create_rectangle(5+r, 2, w-5-r, h-2, fill=self.bg_curr, outline="")
        self.create_rectangle(5, 2+r, w-5, h-2-r, fill=self.bg_curr, outline="")

        if self.selected:
            self.create_rectangle(5, 9, 9, h-9, fill=COLOR_ACCENT, outline="")
            self.create_rectangle(9, 11, 11, h-11, fill=COLOR_ACCENT_GLOW, outline="")

        cx, cy = 27, h // 2
        if self.status == "online":
            self.create_oval(cx-8, cy-8, cx+8, cy+8, fill=COLOR_GREEN_GLOW, outline="")
            self.create_oval(cx-4, cy-4, cx+4, cy+4, fill=COLOR_GREEN, outline="")
        elif self.status == "offline":
            self.create_oval(cx-8, cy-8, cx+8, cy+8, fill=COLOR_RED_GLOW, outline="")
            self.create_oval(cx-4, cy-4, cx+4, cy+4, fill=COLOR_RED, outline="")
        else:
            self.create_oval(cx-8, cy-8, cx+8, cy+8, fill=COLOR_AMBER_GLOW, outline="")
            self.create_oval(cx-4, cy-4, cx+4, cy+4, fill=COLOR_AMBER, outline="")

        name = f"{self.server['emoji']}  {self.server['name']}"
        self.create_text(44, h//2 - 8, text=name, fill=COLOR_TEXT, font=self.fonts["row_name"], anchor="w")

        if self.status == "online" and self.players is not None:
            sub = f"{self.players} / {self.maxplayers}" if self.maxplayers else str(self.players)
            col = COLOR_TEXT_SEC
        elif self.status == "offline":
            sub = "Офлайн"
            col = COLOR_RED
        else:
            sub = "Подключение…"
            col = COLOR_TEXT_MUTED

        self.create_text(44, h//2 + 10, text=sub, fill=col, font=self.fonts["row_sub"], anchor="w")


# ==================== TITLEBAR BUTTON ====================
class TitleBtn(tk.Canvas):
    def __init__(self, parent, symbol, color, hover, command, size=36):
        super().__init__(parent, width=size, height=size, bg=parent["bg"],
                         highlightthickness=0, cursor="hand2")
        self.symbol = symbol
        self.color = color
        self.hover = hover
        self.cmd = command
        self.curr = color
        self.size = size

        self.bind("<Enter>", lambda e: self._set(self.hover))
        self.bind("<Leave>", lambda e: self._set(self.color))
        self.bind("<Button-1>", lambda e: self.cmd())
        self._draw()

    def _set(self, c):
        self.curr = c
        self._draw()

    def _draw(self):
        self.delete("all")
        s = self.size
        self.create_text(s/2, s/2, text=self.symbol, fill=self.curr,
                         font=("Segoe UI", 14 if self.symbol == "×" else 12))


# ==================== MAIN APP ====================
class MultiServerMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("GTA5RP Ultra")
        self.root.geometry("1100x700")
        self.root.configure(bg=COLOR_BG)
        self.root.minsize(960, 600)

        # Полностью убираем системную рамку Windows
        self.root.overrideredirect(True)

        # Прозрачность
        try:
            self.root.attributes("-alpha", 0.94)
        except Exception:
            pass

        # Скругление окна (Windows 11+)
        try:
            from ctypes import windll, byref, sizeof, c_int
            hwnd = windll.user32.GetParent(self.root.winfo_id())
            windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, byref(c_int(2)), sizeof(c_int))
        except Exception:
            pass

        self.running = False
        self.selected_server = SERVERS[0]
        self.rows = {}
        self.anim_curr = 0
        self.anim_target = 0
        self._drag_data = {"x": 0, "y": 0}

        def base_dir():
            # Работает и при обычном запуске .py, и из собранного PyInstaller .exe:
            # в обоих случаях папка с ресурсами (node/, check_all_persistent.js)
            # лежит рядом с самим исполняемым файлом.
            if getattr(sys, "frozen", False):
                return os.path.dirname(sys.executable)
            return os.path.dirname(os.path.abspath(__file__))

        script_dir = base_dir()
        self.js_path = os.path.join(script_dir, "check_all_persistent.js")

        # Сначала ищем "свой" портативный node.exe рядом с приложением
        # (папка node/, которую кладёт установщик). Если его нет —
        # используем системный node из PATH (для запуска как обычного .py).
        bundled_node = os.path.join(script_dir, "node", "node.exe")
        self.node_exe = bundled_node if os.path.isfile(bundled_node) else "node"

        self.proc = None  # постоянный процесс Node.js

        self._fonts()
        self._ui()
        self._select(SERVERS[0], scroll_only=True)

        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - 1100) // 2
        y = (sh - 700) // 2
        self.root.geometry(f"1100x700+{x}+{y}")

    def _fonts(self):
        family = "Segoe UI" if sys.platform == "win32" else "Helvetica Neue"
        self.fonts = {
            "brand":     tkfont.Font(family=family, size=20, weight="bold"),
            "brand_sub": tkfont.Font(family=family, size=8, weight="bold"),
            "title":     tkfont.Font(family=family, size=22, weight="bold"),
            "mono":      tkfont.Font(family="Consolas", size=10),
            "row_name":  tkfont.Font(family=family, size=11, weight="bold"),
            "row_sub":   tkfont.Font(family=family, size=9),
            "big_status":tkfont.Font(family=family, size=18, weight="bold"),
            "big_count": tkfont.Font(family=family, size=52, weight="bold"),
            "btn":       tkfont.Font(family=family, size=11, weight="bold"),
            "label":     tkfont.Font(family=family, size=9, weight="bold"),
            "small":     tkfont.Font(family=family, size=9),
            "titlebar":  tkfont.Font(family=family, size=10),
        }

    def _ui(self):
        # ───────── CUSTOM TITLEBAR ─────────
        titlebar = tk.Frame(self.root, bg=COLOR_BG, height=42)
        titlebar.pack(fill="x")
        titlebar.pack_propagate(False)

        drag = tk.Frame(titlebar, bg=COLOR_BG)
        drag.pack(side="left", fill="both", expand=True)

        tk.Label(drag, text="  GTA5RP  Ultra Commercial", font=self.fonts["titlebar"],
                 bg=COLOR_BG, fg=COLOR_TEXT_MUTED).pack(side="left", padx=(12, 0), pady=10)

        for w in (titlebar, drag):
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._do_drag)

        controls = tk.Frame(titlebar, bg=COLOR_BG)
        controls.pack(side="right", padx=8)

        TitleBtn(controls, "─", COLOR_MIN, COLOR_MIN_HOVER, self._minimize, size=34).pack(side="left", padx=2)
        TitleBtn(controls, "×", COLOR_CLOSE, COLOR_CLOSE_HOVER, self._close, size=34).pack(side="left", padx=2)

        # ───────── BODY ─────────
        body = tk.Frame(self.root, bg=COLOR_BG)
        body.pack(fill="both", expand=True)

        # SIDEBAR
        side = tk.Frame(body, bg=COLOR_SIDEBAR, width=290)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        brand = tk.Frame(side, bg=COLOR_SIDEBAR)
        brand.pack(fill="x", padx=22, pady=(18, 14))

        tk.Label(brand, text="GTA5RP", font=self.fonts["brand"],
                 bg=COLOR_SIDEBAR, fg=COLOR_TEXT).pack(anchor="w")
        tk.Label(brand, text="ULTRA  •  v4.1 COMMERCIAL", font=self.fonts["brand_sub"],
                 bg=COLOR_SIDEBAR, fg=COLOR_ACCENT).pack(anchor="w", pady=(2, 0))

        tk.Frame(side, bg=COLOR_GLASS_BORDER, height=1).pack(fill="x", padx=18, pady=(0, 12))

        canvas = tk.Canvas(side, bg=COLOR_SIDEBAR, highlightthickness=0)
        self.list_frame = tk.Frame(canvas, bg=COLOR_SIDEBAR)

        self.list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.list_frame, anchor="nw", width=274)
        canvas.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 12))

        def _wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _wheel)

        for s in SERVERS:
            row = ServerRow(self.list_frame, s, self._select, self.fonts)
            row.pack(fill="x", pady=2, padx=3)
            self.rows[s["host"]] = row

        # MAIN CONTENT
        main = tk.Frame(body, bg=COLOR_BG)
        main.pack(side="left", fill="both", expand=True, padx=32, pady=(8, 24))

        head = tk.Frame(main, bg=COLOR_BG)
        head.pack(fill="x", pady=(4, 16))

        self.hdr_title = tk.Label(head, text="", font=self.fonts["title"],
                                  bg=COLOR_BG, fg=COLOR_TEXT)
        self.hdr_title.pack(anchor="w")

        self.hdr_sub = tk.Label(head, text="", font=self.fonts["mono"],
                                bg=COLOR_BG, fg=COLOR_TEXT_MUTED)
        self.hdr_sub.pack(anchor="w", pady=(3, 0))

        self.card = GlassCard(main, height=190, radius=18)
        self.card.pack(fill="x", pady=(0, 16))

        inner = tk.Frame(self.card, bg=COLOR_GLASS)
        inner.place(relx=0.04, rely=0.13, relwidth=0.92, relheight=0.74)

        left = tk.Frame(inner, bg=COLOR_GLASS)
        left.pack(side="left", fill="y")

        status_row = tk.Frame(left, bg=COLOR_GLASS)
        status_row.pack(anchor="w", pady=(4, 0))

        self.dot = tk.Canvas(status_row, width=24, height=24, bg=COLOR_GLASS, highlightthickness=0)
        self.dot.pack(side="left", padx=(0, 12))

        self.status_lbl = tk.Label(status_row, text="ОЖИДАНИЕ", font=self.fonts["big_status"],
                                   bg=COLOR_GLASS, fg=COLOR_TEXT_SEC)
        self.status_lbl.pack(side="left")

        self.last_lbl = tk.Label(left, text="Обновление не запрашивалось",
                                 font=self.fonts["small"], bg=COLOR_GLASS, fg=COLOR_TEXT_MUTED)
        self.last_lbl.pack(anchor="w", pady=(14, 0))

        right = tk.Frame(inner, bg=COLOR_GLASS)
        right.pack(side="right", fill="y")

        self.count_lbl = tk.Label(right, text="0", font=self.fonts["big_count"],
                                  bg=COLOR_GLASS, fg=COLOR_ACCENT)
        self.count_lbl.pack(anchor="e")

        self.max_lbl = tk.Label(right, text="ОЖИДАНИЕ ДАННЫХ", font=self.fonts["label"],
                                bg=COLOR_GLASS, fg=COLOR_TEXT_MUTED)
        self.max_lbl.pack(anchor="e")

        bar_wrap = tk.Frame(main, bg=COLOR_BG)
        bar_wrap.pack(fill="x", pady=(0, 20))
        self.bar = NeonBar(bar_wrap, height=10)
        self.bar.pack(fill="x")

        # ───── КНОПКИ — коммерческое расположение ─────
        btn_area = tk.Frame(main, bg=COLOR_BG)
        btn_area.pack(fill="x", pady=(0, 14))

        self.toggle_btn = PremiumButton(
            btn_area, text="▶    ЗАПУСТИТЬ МОНИТОРИНГ",
            bg=COLOR_GREEN, fg="#022C22", hover="#34D399",
            command=self.toggle, font=self.fonts["btn"], height=52, radius=13
        )
        self.toggle_btn.pack(fill="x")

        btn_sec = tk.Frame(main, bg=COLOR_BG)
        btn_sec.pack(fill="x", pady=(10, 12))

        self.log_btn = PremiumButton(
            btn_sec, text="📋    КОНСОЛЬ СОБЫТИЙ",
            bg=COLOR_GLASS_LIGHT, fg=COLOR_TEXT, hover=COLOR_GLASS_BORDER,
            command=self.toggle_log, font=self.fonts["btn"], height=46, radius=12
        )
        self.log_btn.pack(fill="x")

        self.log_box = tk.Frame(main, bg=COLOR_BG)
        self.log_visible = False

        tk.Label(self.log_box, text="КОНСОЛЬ", font=self.fonts["label"],
                 bg=COLOR_BG, fg=COLOR_TEXT_MUTED).pack(anchor="w", pady=(0, 6))

        log_card = GlassCard(self.log_box, bg="#06090F", border=COLOR_GLASS_BORDER, radius=14, glow=False)
        log_card.pack(fill="both", expand=True)

        log_inner = tk.Frame(log_card, bg="#06090F")
        log_inner.place(relx=0.015, rely=0.04, relwidth=0.97, relheight=0.92)

        scroll = tk.Scrollbar(log_inner, width=6)
        scroll.pack(side="right", fill="y")

        self.log = tk.Text(
            log_inner, bg="#06090F", fg=COLOR_TEXT_SEC, font=self.fonts["mono"],
            bd=0, wrap="word", yscrollcommand=scroll.set,
            insertbackground=COLOR_TEXT, padx=10, pady=8
        )
        self.log.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.log.yview)

        self.log.tag_config("online", foreground=COLOR_GREEN)
        self.log.tag_config("offline", foreground=COLOR_RED)
        self.log.tag_config("info", foreground=COLOR_CYAN)
        self.log.config(state="disabled")

    def _start_drag(self, e):
        self._drag_data["x"] = e.x
        self._drag_data["y"] = e.y

    def _do_drag(self, e):
        x = self.root.winfo_x() + e.x - self._drag_data["x"]
        y = self.root.winfo_y() + e.y - self._drag_data["y"]
        self.root.geometry(f"+{x}+{y}")

    def _close(self):
        self.running = False
        self._stop_process()
        self.root.destroy()

    def _minimize(self):
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.after(10, lambda: self.root.overrideredirect(True))

    def _select(self, server, scroll_only=False):
        if not scroll_only:
            self.rows[self.selected_server["host"]].set_selected(False)
        self.selected_server = server
        self.rows[server["host"]].set_selected(True)

        self.hdr_title.config(text=f"{server['emoji']}   {server['name']}")
        self.hdr_sub.config(text=f"{server['host']}:{server['port']}")

        self._render(self.rows[server["host"]])
        self._clear_log()

    def _render(self, row):
        self.dot.delete("all")
        if row.status == "online":
            self.dot.create_oval(0, 0, 24, 24, fill=COLOR_GREEN_GLOW, outline="")
            self.dot.create_oval(5, 5, 19, 19, fill=COLOR_GREEN, outline="")
            self.status_lbl.config(text="ОНЛАЙН", fg=COLOR_GREEN)
            self._counter(row.players if row.players is not None else 0)
            if row.maxplayers:
                self.max_lbl.config(text=f"ИЗ {row.maxplayers} СЛОТОВ")
                ratio = (row.players or 0) / row.maxplayers
                c = COLOR_GREEN if ratio < 0.82 else (COLOR_AMBER if ratio < 0.95 else COLOR_RED)
                self.bar.set(ratio, c)
            else:
                self.max_lbl.config(text="")
                self.bar.set(0, COLOR_GLASS_BORDER)
        elif row.status == "offline":
            self.dot.create_oval(0, 0, 24, 24, fill=COLOR_RED_GLOW, outline="")
            self.dot.create_oval(5, 5, 19, 19, fill=COLOR_RED, outline="")
            self.status_lbl.config(text="ОФЛАЙН", fg=COLOR_RED)
            self._counter(0)
            self.max_lbl.config(text="СЕРВЕР НЕДОСТУПЕН")
            self.bar.set(0, COLOR_RED)
        else:
            self.dot.create_oval(0, 0, 24, 24, fill=COLOR_AMBER_GLOW, outline="")
            self.dot.create_oval(5, 5, 19, 19, fill=COLOR_AMBER, outline="")
            self.status_lbl.config(text="ОЖИДАНИЕ", fg=COLOR_TEXT_SEC)
            self._counter(0)
            self.max_lbl.config(text="ПОДКЛЮЧЕНИЕ…")
            self.bar.set(0, COLOR_GLASS_BORDER)

    def _counter(self, target):
        self.anim_target = target
        self._step_counter()

    def _step_counter(self):
        diff = self.anim_target - self.anim_curr
        if abs(diff) > 0:
            step = max(1, abs(diff) // 5)
            self.anim_curr += step if diff > 0 else -step
            self.count_lbl.config(text=str(self.anim_curr))
            self.root.after(20, self._step_counter)
        else:
            self.anim_curr = self.anim_target
            self.count_lbl.config(text=str(self.anim_curr))

    def toggle_log(self):
        if self.log_visible:
            self.log_box.pack_forget()
            self.log_btn.set_config("📋    КОНСОЛЬ СОБЫТИЙ", COLOR_GLASS_LIGHT, COLOR_TEXT, COLOR_GLASS_BORDER)
            self.log_visible = False
            self.root.geometry("1100x620")
        else:
            self.log_box.pack(fill="both", expand=True)
            self.log_btn.set_config("📋    СКРЫТЬ КОНСОЛЬ", COLOR_GLASS_LIGHT, COLOR_TEXT, COLOR_GLASS_BORDER)
            self.log_visible = True
            self.root.geometry("1100x780")

    def _clear_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")

    def _log(self, msg, tag="info"):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n", tag)
        self.log.see("end")
        if int(self.log.index("end-1c").split(".")[0]) > 450:
            self.log.delete("1.0", "2.0")
        self.log.config(state="disabled")

    def toggle(self):
        if self.running:
            self.running = False
            self.toggle_btn.set_config("▶    ЗАПУСТИТЬ МОНИТОРИНГ", COLOR_GREEN, "#022C22", "#34D399")
            self._stop_process()
        else:
            self.running = True
            self.toggle_btn.set_config("⏸    ОСТАНОВИТЬ МОНИТОРИНГ", COLOR_RED, "#450A0A", "#FB7185")
            self._start_process()

    def _start_process(self):
        servers_json = json.dumps(
            [{"host": s["host"], "port": s["port"]} for s in SERVERS]
        )
        # CHECK_INTERVAL задаётся в секундах выше по файлу для совместимости;
        # здесь переводим в миллисекунды для цикла внутри Node.js
        cycle_delay_ms = str(int(CHECK_INTERVAL * 1000))

        popen_kwargs = dict(
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # построчная буферизация — читаем результаты сразу по готовности
        )
        # На Windows скрываем мелькающее консольное окно Node.js
        if sys.platform == "win32":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            popen_kwargs["startupinfo"] = si
            popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        self.proc = subprocess.Popen(
            [self.node_exe, self.js_path, servers_json, cycle_delay_ms],
            **popen_kwargs,
        )
        threading.Thread(target=self._read_loop, daemon=True).start()

    def _stop_process(self):
        if self.proc is not None:
            try:
                self.proc.terminate()
            except Exception:
                pass
            self.proc = None

    def _read_loop(self):
        proc = self.proc
        if proc is None:
            return
        for line in proc.stdout:
            if not self.running:
                break
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            host = data.get("host")
            server = next((s for s in SERVERS if s["host"] == host), None)
            if server is None:
                continue

            online = bool(data.get("online"))
            players = maxp = None
            detail = ""
            if online:
                d = data.get("data") or {}
                if isinstance(d, dict):
                    players = d.get("players")
                    maxp = d.get("maxplayers")
                detail = str(d)
            else:
                detail = str(data.get("error"))

            self.root.after(0, self._apply, server, online, players, maxp, detail)

    def _apply(self, server, online, players, maxp, detail):
        row = self.rows[server["host"]]
        row.update_status(online, players, maxp)
        if server["host"] == self.selected_server["host"]:
            self._render(row)
            now = datetime.now().strftime("%H:%M:%S")
            self.last_lbl.config(text=f"ПОСЛЕДНЕЕ ОБНОВЛЕНИЕ  •  {now}")
            if online:
                self._log(f"[{now}]  ОНЛАЙН  —  {players}/{maxp} игроков", "online")
            else:
                self._log(f"[{now}]  ОФЛАЙН  —  {detail}", "offline")


def main():
    root = tk.Tk()
    MultiServerMonitor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
