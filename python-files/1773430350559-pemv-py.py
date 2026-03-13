#!/usr/bin/env python3
"""
Расписание звонков — минималистичное приложение для образовательного учреждения.
"""

import tkinter as tk
from tkinter import simpledialog, scrolledtext
import subprocess
import webbrowser
import sys
import os
from datetime import datetime

# ============================================================
# РАСПИСАНИЕ ЗВОНКОВ
# ============================================================

MONDAY_SCHEDULE = [
    ("1 пара",    "08:00", "08:30"),
    ("2 пара",    "08:40", "10:10"),
    ("3 пара",    "10:20", "11:50"),
    ("4 пара",    "12:10", "13:40"),
    ("Совещание", "13:50", "14:50"),
    ("5 пара",    "15:00", "16:30"),
    ("6 пара",    "16:50", "18:20"),
    ("7 пара",    "18:30", "20:00"),
]

REGULAR_SCHEDULE = [
    ("1 пара", "08:00", "09:30"),
    ("2 пара", "09:40", "11:10"),
    ("3 пара", "11:40", "13:10"),
    ("4 пара", "13:20", "14:50"),
    ("5 пара", "15:00", "16:30"),
    ("6 пара", "16:50", "18:20"),
    ("7 пара", "18:30", "20:00"),
]

DAYS_RU = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

# ============================================================
# ТЕМЫ ОФОРМЛЕНИЯ
# ============================================================

THEMES = {
    "Обычная": {
        "BG": "#EEEEEE", "FG": "#333333", "ACCENT": "#1A5276",
        "GREEN": "#27AE60", "YELLOW": "#E67E22", "RED": "#C0392B",
        "SUB": "#888888", "TITLE_BG": "#EEEEEE", "CLOSE_BG": "#E74C3C",
        "STATUS_ON": "#AFAFAF", "STATUS_BRK": "#27AE60", "STATUS_OFF": "#B3B3B3",
        "STATUS_BEF": "#3498DB", "DIVIDER": "#FFFFFF", "MENU_BG": "#F5F5F5",
        "MENU_HOVER": "#E0E0E0", "BTN_FG": "#000000", "CLOSE_FG": "white",
        "STATUS_FG": "white",
    },
    "🌙 Тёмная ночь": {
        "BG": "#1E1E2E", "FG": "#CDD6F4", "ACCENT": "#89B4FA",
        "GREEN": "#A6E3A1", "YELLOW": "#F9E2AF", "RED": "#F38BA8",
        "SUB": "#6C7086", "TITLE_BG": "#181825", "CLOSE_BG": "#F38BA8",
        "STATUS_ON": "#45475A", "STATUS_BRK": "#A6E3A1", "STATUS_OFF": "#313244",
        "STATUS_BEF": "#89B4FA", "DIVIDER": "#313244", "MENU_BG": "#1E1E2E",
        "MENU_HOVER": "#313244", "BTN_FG": "#CDD6F4", "CLOSE_FG": "#1E1E2E",
        "STATUS_FG": "#FFFFFF",
    },
    "🌊 Океан": {
        "BG": "#0A1628", "FG": "#E0F7FA", "ACCENT": "#00BCD4",
        "GREEN": "#00E676", "YELLOW": "#FFAB40", "RED": "#FF5252",
        "SUB": "#4DB6AC", "TITLE_BG": "#0D1F3C", "CLOSE_BG": "#FF5252",
        "STATUS_ON": "#1A237E", "STATUS_BRK": "#00897B", "STATUS_OFF": "#0D1F3C",
        "STATUS_BEF": "#0288D1", "DIVIDER": "#1A237E", "MENU_BG": "#0D1F3C",
        "MENU_HOVER": "#1A237E", "BTN_FG": "#80DEEA", "CLOSE_FG": "white",
        "STATUS_FG": "white",
    },
    "🌸 Сакура": {
        "BG": "#FFF0F5", "FG": "#4A0E2E", "ACCENT": "#C2185B",
        "GREEN": "#E91E90", "YELLOW": "#FF6F91", "RED": "#D50000",
        "SUB": "#AD1457", "TITLE_BG": "#FCE4EC", "CLOSE_BG": "#E91E63",
        "STATUS_ON": "#F48FB1", "STATUS_BRK": "#EC407A", "STATUS_OFF": "#F8BBD0",
        "STATUS_BEF": "#CE93D8", "DIVIDER": "#F8BBD0", "MENU_BG": "#FFF0F5",
        "MENU_HOVER": "#FCE4EC", "BTN_FG": "#880E4F", "CLOSE_FG": "white",
        "STATUS_FG": "white",
    },
    "🔥 Вулкан": {
        "BG": "#1A0A00", "FG": "#FFCCBC", "ACCENT": "#FF6D00",
        "GREEN": "#FFAB00", "YELLOW": "#FF9100", "RED": "#DD2C00",
        "SUB": "#BF360C", "TITLE_BG": "#2A1000", "CLOSE_BG": "#DD2C00",
        "STATUS_ON": "#BF360C", "STATUS_BRK": "#FF6D00", "STATUS_OFF": "#3E2723",
        "STATUS_BEF": "#E65100", "DIVIDER": "#4E342E", "MENU_BG": "#2A1000",
        "MENU_HOVER": "#4E342E", "BTN_FG": "#FFAB91", "CLOSE_FG": "white",
        "STATUS_FG": "white",
    },
    "🌿 Лесная": {
        "BG": "#E8F5E9", "FG": "#1B5E20", "ACCENT": "#2E7D32",
        "GREEN": "#43A047", "YELLOW": "#F9A825", "RED": "#C62828",
        "SUB": "#558B2F", "TITLE_BG": "#C8E6C9", "CLOSE_BG": "#C62828",
        "STATUS_ON": "#66BB6A", "STATUS_BRK": "#2E7D32", "STATUS_OFF": "#A5D6A7",
        "STATUS_BEF": "#00897B", "DIVIDER": "#A5D6A7", "MENU_BG": "#E8F5E9",
        "MENU_HOVER": "#C8E6C9", "BTN_FG": "#1B5E20", "CLOSE_FG": "white",
        "STATUS_FG": "white",
    },
    "💜 Фиолет": {
        "BG": "#2D1B4E", "FG": "#E1BEE7", "ACCENT": "#CE93D8",
        "GREEN": "#AB47BC", "YELLOW": "#FFB74D", "RED": "#EF5350",
        "SUB": "#9575CD", "TITLE_BG": "#1A0A2E", "CLOSE_BG": "#EF5350",
        "STATUS_ON": "#7B1FA2", "STATUS_BRK": "#AB47BC", "STATUS_OFF": "#4A148C",
        "STATUS_BEF": "#7E57C2", "DIVIDER": "#4A148C", "MENU_BG": "#2D1B4E",
        "MENU_HOVER": "#4A148C", "BTN_FG": "#CE93D8", "CLOSE_FG": "white",
        "STATUS_FG": "white",
    },
    "🏖️ Закат": {
        "BG": "#FFF3E0", "FG": "#3E2723", "ACCENT": "#E65100",
        "GREEN": "#FF8F00", "YELLOW": "#F57C00", "RED": "#D84315",
        "SUB": "#8D6E63", "TITLE_BG": "#FFE0B2", "CLOSE_BG": "#D84315",
        "STATUS_ON": "#FF8A65", "STATUS_BRK": "#FFA726", "STATUS_OFF": "#FFCC80",
        "STATUS_BEF": "#FB8C00", "DIVIDER": "#FFCC80", "MENU_BG": "#FFF3E0",
        "MENU_HOVER": "#FFE0B2", "BTN_FG": "#4E342E", "CLOSE_FG": "white",
        "STATUS_FG": "white",
    },
    "❄️ Арктика": {
        "BG": "#E3F2FD", "FG": "#0D47A1", "ACCENT": "#1565C0",
        "GREEN": "#42A5F5", "YELLOW": "#29B6F6", "RED": "#C62828",
        "SUB": "#5C6BC0", "TITLE_BG": "#BBDEFB", "CLOSE_BG": "#C62828",
        "STATUS_ON": "#64B5F6", "STATUS_BRK": "#42A5F5", "STATUS_OFF": "#90CAF9",
        "STATUS_BEF": "#1E88E5", "DIVIDER": "#90CAF9", "MENU_BG": "#E3F2FD",
        "MENU_HOVER": "#BBDEFB", "BTN_FG": "#0D47A1", "CLOSE_FG": "white",
        "STATUS_FG": "white",
    },
    "🖤 Хакер": {
        "BG": "#0A0A0A", "FG": "#00FF41", "ACCENT": "#00FF41",
        "GREEN": "#00FF41", "YELLOW": "#39FF14", "RED": "#FF0040",
        "SUB": "#00CC33", "TITLE_BG": "#050505", "CLOSE_BG": "#FF0040",
        "STATUS_ON": "#003300", "STATUS_BRK": "#00FF41", "STATUS_OFF": "#0D0D0D",
        "STATUS_BEF": "#00CC33", "DIVIDER": "#003300", "MENU_BG": "#0A0A0A",
        "MENU_HOVER": "#003300", "BTN_FG": "#00FF41", "CLOSE_FG": "white",
        "STATUS_FG": "#FFFFFF",
    },
    "🍬 Конфетная": {
        "BG": "#FFFDE7", "FG": "#4A148C", "ACCENT": "#AA00FF",
        "GREEN": "#F700FF", "YELLOW": "#FFEA00", "RED": "#FF1744",
        "SUB": "#D500F9", "TITLE_BG": "#F3E5F5", "CLOSE_BG": "#FF1744",
        "STATUS_ON": "#E040FB", "STATUS_BRK": "#00E5FF", "STATUS_OFF": "#CE93D8",
        "STATUS_BEF": "#651FFF", "DIVIDER": "#E1BEE7", "MENU_BG": "#FFFDE7",
        "MENU_HOVER": "#F3E5F5", "BTN_FG": "#6A1B9A", "CLOSE_FG": "white",
        "STATUS_FG": "white",
    },
}


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def time_to_min(t: str) -> int:
    h, m = map(int, t.split(":"))
    return h * 60 + m


def fmt_dur(minutes: int) -> str:
    if minutes < 0:
        return "—"
    h, m = divmod(minutes, 60)
    return f"{h}ч {m:02d}мин" if h > 0 else f"{m} мин"


def fmt_seconds(total_seconds: int) -> str:
    if total_seconds < 0:
        return "00:00:00"
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def get_schedule(wd: int):
    if wd == 0:
        return MONDAY_SCHEDULE
    elif 1 <= wd <= 5:
        return REGULAR_SCHEDULE
    return []


def analyze_time(now: datetime):
    wd = now.weekday()
    schedule = get_schedule(wd)
    r = {
        "day": DAYS_RU[wd], "pair": None, "to_break": None,
        "to_next": None, "next_name": None, "status": "day_off",
        "is_last": False
    }
    if not schedule:
        return r

    nm = now.hour * 60 + now.minute
    parsed = [(n, time_to_min(s), time_to_min(e)) for n, s, e in schedule]

    for i, (name, s, e) in enumerate(parsed):
        if s <= nm < e:
            r.update(status="on_pair", pair=name, to_break=e - nm)
            if i + 1 < len(parsed):
                r["next_name"], ns = parsed[i + 1][0], parsed[i + 1][1]
                r["to_next"] = ns - nm
            else:
                r["is_last"] = True
            return r

    for i in range(len(parsed) - 1):
        if parsed[i][2] <= nm < parsed[i + 1][1]:
            r.update(status="on_break", next_name=parsed[i + 1][0],
                     to_next=parsed[i + 1][1] - nm)
            return r

    if nm < parsed[0][1]:
        r.update(status="before", next_name=parsed[0][0], to_next=parsed[0][1] - nm)
        return r

    if nm >= parsed[-1][2]:
        r["status"] = "after"
    return r


def open_calculator():
    try:
        if sys.platform == "win32":
            subprocess.Popen("calc.exe")
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-a", "Calculator"])
        else:
            for calc in ["gnome-calculator", "kcalc", "galculator", "xcalc"]:
                try:
                    subprocess.Popen([calc])
                    return
                except FileNotFoundError:
                    continue
    except Exception:
        pass


def open_journal():
    webbrowser.open("https://rmk.stavedu.ru:8010")


# ============================================================
# ГРАФИЧЕСКИЙ ИНТЕРФЕЙС
# ============================================================

class ScheduleApp:
    BASE_WIDTH = 260
    TIMER_EXTRA_WIDTH = 160
    MIN_HEIGHT = 120
    MIN_HEIGHT_WITH_TIMER = 190

    # Минимальные размеры окна заметок
    NOTES_MIN_W = 200
    NOTES_MIN_H = 150

    def __init__(self):
        self.pinned = True
        self._drag_x = 0
        self._drag_y = 0
        self._menu_window = None
        self._theme_window = None
        self._notes_window = None
        self.current_theme_name = "Обычная"

        # Таймер
        self.timer_active = False
        self.timer_visible = False
        self.timer_remaining = 0
        self.timer_after_id = None

        # Заметки
        self.notes_text_content = ""

        # Resize для заметок
        self._notes_resize_dragging = False
        self._notes_resize_edge = None  # какой край тянем

        self._load_theme_colors("Обычная")

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.configure(bg=self.BG)
        self.root.resizable(False, False)
        self.root.attributes("-topmost", self.pinned)
        self.root.config(highlightthickness=0)

        screen_w = self.root.winfo_screenwidth()
        x = screen_w - self.BASE_WIDTH - 8
        y = 8
        self.root.geometry(f"{self.BASE_WIDTH}x{self.MIN_HEIGHT}+{x}+{y}")

        self._build()
        self._tick()
        self.root.mainloop()

    def _load_theme_colors(self, theme_name):
        theme = THEMES.get(theme_name, THEMES["Обычная"])
        self.BG = theme["BG"]
        self.FG = theme["FG"]
        self.ACCENT = theme["ACCENT"]
        self.GREEN = theme["GREEN"]
        self.YELLOW = theme["YELLOW"]
        self.RED = theme["RED"]
        self.SUB = theme["SUB"]
        self.TITLE_BG = theme["TITLE_BG"]
        self.CLOSE_BG = theme["CLOSE_BG"]
        self.STATUS_ON = theme["STATUS_ON"]
        self.STATUS_BRK = theme["STATUS_BRK"]
        self.STATUS_OFF = theme["STATUS_OFF"]
        self.STATUS_BEF = theme["STATUS_BEF"]
        self.DIVIDER = theme["DIVIDER"]
        self.MENU_BG = theme["MENU_BG"]
        self.MENU_HOVER = theme["MENU_HOVER"]
        self.BTN_FG = theme["BTN_FG"]
        self.CLOSE_FG = theme["CLOSE_FG"]
        self.STATUS_FG = theme["STATUS_FG"]
        self.current_theme_name = theme_name

    def _apply_theme(self, theme_name):
        self._close_menu()
        self._close_theme_window()
        self._load_theme_colors(theme_name)

        self.root.configure(bg=self.BG)

        self.title_bar.config(bg=self.TITLE_BG)
        self.btn_pin.config(bg=self.TITLE_BG, fg=self.BTN_FG)
        self.btn_other.config(bg=self.TITLE_BG, fg=self.BTN_FG)
        self.btn_close.config(bg=self.CLOSE_BG, fg=self.CLOSE_FG)
        self.lbl_title.config(bg=self.TITLE_BG, fg=self.BTN_FG)

        self.main_frame.config(bg=self.BG)
        self.time_row.config(bg=self.BG)
        self.lbl_time.config(bg=self.BG, fg=self.ACCENT)
        self.date_frame.config(bg=self.BG)
        self.lbl_dayname.config(bg=self.BG, fg=self.SUB)
        self.lbl_date.config(bg=self.BG, fg=self.SUB)
        self.divider.config(bg=self.DIVIDER)
        self.info_frame.config(bg=self.BG)

        self.row1.config(bg=self.BG)
        self.lbl_cur_label.config(bg=self.BG, fg=self.SUB)
        self.lbl_cur.config(bg=self.BG)

        self.row2.config(bg=self.BG)
        self.lbl_brk_label.config(bg=self.BG, fg=self.SUB)
        self.lbl_brk.config(bg=self.BG)

        self.row3.config(bg=self.BG)
        self.lbl_nxt_label.config(bg=self.BG, fg=self.SUB)
        self.lbl_nxt.config(bg=self.BG)

        if self.timer_visible:
            was_active = self.timer_active
            remaining = self.timer_remaining

            if hasattr(self, 'timer_panel') and self.timer_panel.winfo_exists():
                self.timer_panel.destroy()

            self._create_timer_panel_widgets()

            if was_active and hasattr(self, 'lbl_timer_value'):
                self.lbl_timer_value.config(text=fmt_seconds(remaining))
                if remaining <= 10:
                    self.lbl_timer_value.config(fg=self.RED)
                elif remaining <= 60:
                    self.lbl_timer_value.config(fg=self.YELLOW)
            elif not was_active and hasattr(self, 'lbl_timer_value'):
                self.lbl_timer_value.config(text="00:00:00", fg=self.RED)
                self.lbl_timer_label.config(text="Время вышло!")

        self._apply_theme_to_notes()
        self._tick_once()

    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_drag(self, event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _close(self):
        self._close_menu()
        self._close_theme_window()
        self._close_notes_window()
        if self.timer_after_id:
            self.root.after_cancel(self.timer_after_id)
        self.root.destroy()

    def _toggle_pin(self):
        self.pinned = not self.pinned
        self.root.attributes("-topmost", self.pinned)
        icon = "📌" if self.pinned else "📍"
        self.btn_pin.config(text=icon)

    def _close_menu(self):
        if self._menu_window and self._menu_window.winfo_exists():
            self._menu_window.destroy()
        self._menu_window = None

    def _close_theme_window(self):
        if self._theme_window and self._theme_window.winfo_exists():
            self._theme_window.destroy()
        self._theme_window = None

    def _close_notes_window(self):
        if self._notes_window and self._notes_window.winfo_exists():
            if hasattr(self, '_notes_text_widget') and self._notes_text_widget.winfo_exists():
                self.notes_text_content = self._notes_text_widget.get("1.0", "end-1c")
            self._notes_window.destroy()
        self._notes_window = None

    def _toggle_menu(self):
        if self._menu_window and self._menu_window.winfo_exists():
            self._close_menu()
            return

        btn = self.btn_other
        x = btn.winfo_rootx()
        y = btn.winfo_rooty() + btn.winfo_height()

        menu = tk.Toplevel(self.root)
        menu.overrideredirect(True)
        menu.configure(bg="#D0D0D0")
        menu.attributes("-topmost", True)
        menu.config(highlightthickness=0)

        inner = tk.Frame(menu, bg=self.MENU_BG)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        menu_items = [
            ("🧮  Калькулятор", lambda: self._menu_action(open_calculator)),
            ("📖  Эл.журнал", lambda: self._menu_action(open_journal)),
            ("🎨  Темы", lambda: self._menu_action(self._open_theme_picker)),
            ("⏱️  Таймер", lambda: self._menu_action(self._open_timer_dialog)),
            ("📝  Заметки", lambda: self._menu_action(self._open_notes_window)),
        ]

        for i, (text, command) in enumerate(menu_items):
            if i > 0:
                tk.Frame(inner, height=1, bg=self.DIVIDER).pack(fill="x", padx=5)

            btn_item = tk.Button(
                inner, text=text, command=command,
                font=("Segoe UI", 9), bg=self.MENU_BG, fg=self.FG,
                bd=0, relief="flat", cursor="hand2", anchor="w",
                padx=10, pady=5
            )
            btn_item.pack(fill="x")
            btn_item.bind("<Enter>", lambda e, b=btn_item: b.config(bg=self.MENU_HOVER))
            btn_item.bind("<Leave>", lambda e, b=btn_item: b.config(bg=self.MENU_BG))

        menu.update_idletasks()
        menu_w = menu.winfo_reqwidth()
        menu_h = menu.winfo_reqheight()

        screen_w = self.root.winfo_screenwidth()
        if x + menu_w > screen_w:
            x = screen_w - menu_w - 4

        menu.geometry(f"{menu_w}x{menu_h}+{x}+{y}")
        self._menu_window = menu

        def _on_focus_out(event):
            self.root.after(100, self._close_menu)

        menu.bind("<FocusOut>", _on_focus_out)
        menu.focus_set()

    def _menu_action(self, action):
        self._close_menu()
        action()

    def _open_theme_picker(self):
        if self._theme_window and self._theme_window.winfo_exists():
            self._theme_window.lift()
            return

        tw = tk.Toplevel(self.root)
        tw.title("Выбор темы")
        tw.overrideredirect(True)
        tw.attributes("-topmost", True)
        tw.config(highlightthickness=0)

        rx = self.root.winfo_x()
        ry = self.root.winfo_y()
        tw.geometry(f"+{rx - 210}+{ry}")

        outer = tk.Frame(tw, bg="#888888")
        outer.pack(fill="both", expand=True)

        container = tk.Frame(outer, bg=self.MENU_BG)
        container.pack(fill="both", expand=True, padx=1, pady=1)

        header = tk.Frame(container, bg=self.TITLE_BG, height=30)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="🎨 Выбор темы", font=("Segoe UI", 10, "bold"),
            bg=self.TITLE_BG, fg=self.BTN_FG
        ).pack(side="left", padx=8)

        btn_close_theme = tk.Button(
            header, text="✕", command=self._close_theme_window,
            font=("Segoe UI", 9, "bold"), bg=self.CLOSE_BG, fg=self.CLOSE_FG,
            bd=0, relief="flat", cursor="hand2", width=3
        )
        btn_close_theme.pack(side="right")

        canvas = tk.Canvas(container, bg=self.MENU_BG, highlightthickness=0, width=190)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.MENU_BG)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        for theme_name in THEMES:
            theme_data = THEMES[theme_name]
            is_current = (theme_name == self.current_theme_name)

            preview_frame = tk.Frame(scroll_frame, bg=self.MENU_BG)
            preview_frame.pack(fill="x", padx=4, pady=2)

            color_bar = tk.Frame(preview_frame, bg=theme_data["ACCENT"], width=6)
            color_bar.pack(side="left", fill="y", padx=(0, 6))

            label_text = f"{'✓ ' if is_current else '   '}{theme_name}"

            btn = tk.Button(
                preview_frame, text=label_text,
                command=lambda tn=theme_name: self._apply_theme(tn),
                font=("Segoe UI", 9, "bold" if is_current else "normal"),
                bg=theme_data["BG"], fg=theme_data["FG"],
                bd=0, relief="flat", cursor="hand2", anchor="w",
                padx=8, pady=4, width=18
            )
            btn.pack(side="left", fill="x", expand=True)

            hover_bg = theme_data.get("MENU_HOVER", theme_data["BG"])
            normal_bg = theme_data["BG"]
            btn.bind("<Enter>", lambda e, b=btn, hbg=hover_bg: b.config(bg=hbg))
            btn.bind("<Leave>", lambda e, b=btn, nbg=normal_bg: b.config(bg=nbg))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tw.update_idletasks()
        tw_h = min(400, scroll_frame.winfo_reqheight() + 35)
        tw.geometry(f"210x{tw_h}+{rx - 220}+{ry}")

        self._theme_window = tw

        header.bind("<Button-1>", lambda e: setattr(self, '_tw_drag', (e.x, e.y)))
        header.bind("<B1-Motion>", lambda e: tw.geometry(
            f"+{tw.winfo_x() + e.x - self._tw_drag[0]}+{tw.winfo_y() + e.y - self._tw_drag[1]}"
        ))

    # ============================================================
    # ЗАМЕТКИ (с изменяемым размером)
    # ============================================================

    def _open_notes_window(self):
        if self._notes_window and self._notes_window.winfo_exists():
            self._notes_window.lift()
            return

        nw = tk.Toplevel(self.root)
        nw.overrideredirect(True)
        nw.attributes("-topmost", True)
        nw.config(highlightthickness=0)

        rx = self.root.winfo_x()
        ry = self.root.winfo_y()
        rh = self.root.winfo_height()
        nw_w = 280
        nw_h = 300
        nx = rx
        ny = ry + rh + 5

        screen_h = self.root.winfo_screenheight()
        if ny + nw_h > screen_h:
            ny = ry - nw_h - 5

        nw.geometry(f"{nw_w}x{nw_h}+{nx}+{ny}")

        # Рамка-бордюр (она же служит зоной ресайза)
        outer = tk.Frame(nw, bg="#888888")
        outer.pack(fill="both", expand=True)

        container = tk.Frame(outer, bg=self.BG)
        container.pack(fill="both", expand=True, padx=1, pady=1)

        # --- Заголовок ---
        header = tk.Frame(container, bg=self.TITLE_BG, height=30)
        header.pack(fill="x")
        header.pack_propagate(False)

        self._notes_header = header

        self._notes_title_lbl = tk.Label(
            header, text="📝 Заметки", font=("Segoe UI", 10, "bold"),
            bg=self.TITLE_BG, fg=self.BTN_FG
        )
        self._notes_title_lbl.pack(side="left", padx=8)

        self._notes_close_btn = tk.Button(
            header, text="✕", command=self._close_notes_window,
            font=("Segoe UI", 9, "bold"), bg=self.CLOSE_BG, fg=self.CLOSE_FG,
            bd=0, relief="flat", cursor="hand2", width=3
        )
        self._notes_close_btn.pack(side="right")

        # Перетаскивание за заголовок
        header.bind("<Button-1>", lambda e: setattr(self, '_nw_drag', (e.x, e.y)))
        header.bind("<B1-Motion>", lambda e: nw.geometry(
            f"+{nw.winfo_x() + e.x - self._nw_drag[0]}+{nw.winfo_y() + e.y - self._nw_drag[1]}"
        ))

        # --- Подсказка ---
        self._notes_hint_lbl = tk.Label(
            container, text="Заметки не сохраняются после закрытия приложения",
            font=("Segoe UI", 7), bg=self.BG, fg=self.SUB, anchor="w"
        )
        self._notes_hint_lbl.pack(fill="x", padx=8, pady=(4, 0))

        self._notes_container = container

        # --- Текстовое поле ---
        text_frame = tk.Frame(container, bg=self.BG)
        text_frame.pack(fill="both", expand=True, padx=8, pady=(4, 4))

        self._notes_text_widget = tk.Text(
            text_frame,
            font=("Segoe UI", 10),
            bg=self.MENU_BG,
            fg=self.FG,
            insertbackground=self.FG,
            selectbackground=self.ACCENT,
            selectforeground="white",
            bd=1,
            relief="solid",
            highlightthickness=0,
            wrap="word",
            padx=6,
            pady=6
        )
        self._notes_text_widget.pack(fill="both", expand=True)

        if self.notes_text_content:
            self._notes_text_widget.insert("1.0", self.notes_text_content)

        # --- Нижняя панель: счётчик + ручка ресайза ---
        bottom_bar = tk.Frame(container, bg=self.BG, height=20)
        bottom_bar.pack(fill="x", padx=8, pady=(0, 2))
        bottom_bar.pack_propagate(False)

        self._notes_counter_lbl = tk.Label(
            bottom_bar, text="0 символов", font=("Segoe UI", 8),
            bg=self.BG, fg=self.SUB, anchor="w"
        )
        self._notes_counter_lbl.pack(side="left", fill="x", expand=True)

        # Ручка ресайза (grip) — в правом нижнем углу
        self._notes_grip = tk.Label(
            bottom_bar, text="⋱", font=("Segoe UI", 10, "bold"),
            bg=self.BG, fg=self.SUB, cursor="bottom_right_corner"
        )
        self._notes_grip.pack(side="right")

        # --- Привязки для ресайза через grip ---
        self._notes_grip.bind("<Button-1>", self._notes_grip_start)
        self._notes_grip.bind("<B1-Motion>", self._notes_grip_drag)

        # --- Привязки для ресайза через края окна (outer frame) ---
        # Используем bind на nw (Toplevel) для определения позиции мыши у краёв
        nw.bind("<Motion>", self._notes_edge_cursor)
        nw.bind("<Button-1>", self._notes_edge_start)
        nw.bind("<B1-Motion>", self._notes_edge_drag)
        nw.bind("<ButtonRelease-1>", self._notes_edge_release)

        def _update_counter(event=None):
            content = self._notes_text_widget.get("1.0", "end-1c")
            count = len(content)
            self._notes_counter_lbl.config(text=f"{count} символов")

        self._notes_text_widget.bind("<KeyRelease>", _update_counter)
        _update_counter()

        self._notes_window = nw
        self._notes_outer = outer

    # --- Grip resize (правый нижний угол) ---

    def _notes_grip_start(self, event):
        """Начало ресайза через grip."""
        nw = self._notes_window
        if not nw or not nw.winfo_exists():
            return
        self._notes_grip_data = {
            'start_x': event.x_root,
            'start_y': event.y_root,
            'start_w': nw.winfo_width(),
            'start_h': nw.winfo_height(),
        }

    def _notes_grip_drag(self, event):
        """Перетаскивание grip для ресайза."""
        nw = self._notes_window
        if not nw or not nw.winfo_exists():
            return
        if not hasattr(self, '_notes_grip_data'):
            return

        d = self._notes_grip_data
        dx = event.x_root - d['start_x']
        dy = event.y_root - d['start_y']

        new_w = max(self.NOTES_MIN_W, d['start_w'] + dx)
        new_h = max(self.NOTES_MIN_H, d['start_h'] + dy)

        nw.geometry(f"{new_w}x{new_h}")

    # --- Edge resize (все 4 стороны и 4 угла) ---

    def _notes_detect_edge(self, event):
        """Определить, у какого края/угла находится курсор. Возвращает строку вроде 'right', 'bottom', 'bottom_right' и т.д., или None."""
        nw = self._notes_window
        if not nw or not nw.winfo_exists():
            return None

        w = nw.winfo_width()
        h = nw.winfo_height()
        x = event.x
        y = event.y
        margin = 6  # зона захвата в пикселях

        on_left = x < margin
        on_right = x > w - margin
        on_top = y < margin
        on_bottom = y > h - margin

        if on_top and on_left:
            return "top_left"
        if on_top and on_right:
            return "top_right"
        if on_bottom and on_left:
            return "bottom_left"
        if on_bottom and on_right:
            return "bottom_right"
        if on_left:
            return "left"
        if on_right:
            return "right"
        if on_top:
            return "top"
        if on_bottom:
            return "bottom"
        return None

    def _notes_edge_cursor(self, event):
        """Менять курсор при наведении на край окна заметок."""
        nw = self._notes_window
        if not nw or not nw.winfo_exists():
            return

        # Не менять курсор если уже идёт ресайз
        if self._notes_resize_dragging:
            return

        edge = self._notes_detect_edge(event)
        cursor_map = {
            "left": "left_side",
            "right": "right_side",
            "top": "top_side",
            "bottom": "bottom_side",
            "top_left": "top_left_corner",
            "top_right": "top_right_corner",
            "bottom_left": "bottom_left_corner",
            "bottom_right": "bottom_right_corner",
        }

        if edge and edge in cursor_map:
            nw.config(cursor=cursor_map[edge])
        else:
            nw.config(cursor="")

    def _notes_edge_start(self, event):
        """Начало ресайза через край окна."""
        nw = self._notes_window
        if not nw or not nw.winfo_exists():
            return

        edge = self._notes_detect_edge(event)
        if not edge:
            return  # клик не на краю — ничего не делаем (перетаскивание обрабатывается header)

        self._notes_resize_dragging = True
        self._notes_resize_edge = edge
        self._notes_resize_data = {
            'start_x': event.x_root,
            'start_y': event.y_root,
            'start_w': nw.winfo_width(),
            'start_h': nw.winfo_height(),
            'start_wx': nw.winfo_x(),
            'start_wy': nw.winfo_y(),
        }

    def _notes_edge_drag(self, event):
        """Перетаскивание края окна для ресайза."""
        if not self._notes_resize_dragging:
            return

        nw = self._notes_window
        if not nw or not nw.winfo_exists():
            return

        d = self._notes_resize_data
        edge = self._notes_resize_edge

        dx = event.x_root - d['start_x']
        dy = event.y_root - d['start_y']

        new_x = d['start_wx']
        new_y = d['start_wy']
        new_w = d['start_w']
        new_h = d['start_h']

        # Правый край
        if edge in ("right", "top_right", "bottom_right"):
            new_w = max(self.NOTES_MIN_W, d['start_w'] + dx)

        # Левый край
        if edge in ("left", "top_left", "bottom_left"):
            proposed_w = d['start_w'] - dx
            if proposed_w >= self.NOTES_MIN_W:
                new_w = proposed_w
                new_x = d['start_wx'] + dx
            else:
                new_w = self.NOTES_MIN_W
                new_x = d['start_wx'] + d['start_w'] - self.NOTES_MIN_W

        # Нижний край
        if edge in ("bottom", "bottom_left", "bottom_right"):
            new_h = max(self.NOTES_MIN_H, d['start_h'] + dy)

        # Верхний край
        if edge in ("top", "top_left", "top_right"):
            proposed_h = d['start_h'] - dy
            if proposed_h >= self.NOTES_MIN_H:
                new_h = proposed_h
                new_y = d['start_wy'] + dy
            else:
                new_h = self.NOTES_MIN_H
                new_y = d['start_wy'] + d['start_h'] - self.NOTES_MIN_H

        nw.geometry(f"{new_w}x{new_h}+{new_x}+{new_y}")

    def _notes_edge_release(self, event):
        """Конец ресайза."""
        self._notes_resize_dragging = False
        self._notes_resize_edge = None

    def _apply_theme_to_notes(self):
        if not self._notes_window or not self._notes_window.winfo_exists():
            return

        try:
            self._notes_header.config(bg=self.TITLE_BG)
            self._notes_title_lbl.config(bg=self.TITLE_BG, fg=self.BTN_FG)
            self._notes_close_btn.config(bg=self.CLOSE_BG, fg=self.CLOSE_FG)
            self._notes_container.config(bg=self.BG)
            self._notes_hint_lbl.config(bg=self.BG, fg=self.SUB)
            self._notes_counter_lbl.config(bg=self.BG, fg=self.SUB)
            self._notes_grip.config(bg=self.BG, fg=self.SUB)
            self._notes_text_widget.config(
                bg=self.MENU_BG,
                fg=self.FG,
                insertbackground=self.FG,
                selectbackground=self.ACCENT,
            )
        except (tk.TclError, AttributeError):
            pass

    # ============================================================
    # ТАЙМЕР
    # ============================================================

    def _open_timer_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Установить таймер")
        dialog.overrideredirect(True)
        dialog.attributes("-topmost", True)
        dialog.config(highlightthickness=0)

        rx = self.root.winfo_x()
        ry = self.root.winfo_y()
        rw = self.root.winfo_width()
        dialog_w = 250
        dialog_h = 200
        dx = rx + (rw - dialog_w) // 2
        dy = ry + 50
        dialog.geometry(f"{dialog_w}x{dialog_h}+{dx}+{dy}")

        outer = tk.Frame(dialog, bg="#888888")
        outer.pack(fill="both", expand=True)

        container = tk.Frame(outer, bg=self.BG)
        container.pack(fill="both", expand=True, padx=1, pady=1)

        header = tk.Frame(container, bg=self.TITLE_BG, height=30)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="⏱️ Таймер", font=("Segoe UI", 10, "bold"),
            bg=self.TITLE_BG, fg=self.BTN_FG
        ).pack(side="left", padx=8)

        btn_close_dlg = tk.Button(
            header, text="✕", command=dialog.destroy,
            font=("Segoe UI", 9, "bold"), bg=self.CLOSE_BG, fg=self.CLOSE_FG,
            bd=0, relief="flat", cursor="hand2", width=3
        )
        btn_close_dlg.pack(side="right")

        header.bind("<Button-1>", lambda e: setattr(self, '_dlg_drag', (e.x, e.y)))
        header.bind("<B1-Motion>", lambda e: dialog.geometry(
            f"+{dialog.winfo_x() + e.x - self._dlg_drag[0]}+{dialog.winfo_y() + e.y - self._dlg_drag[1]}"
        ))

        body = tk.Frame(container, bg=self.BG)
        body.pack(fill="both", expand=True, padx=15, pady=10)

        row_h = tk.Frame(body, bg=self.BG)
        row_h.pack(fill="x", pady=3)
        tk.Label(row_h, text="Часы:", font=("Segoe UI", 10), bg=self.BG, fg=self.FG, width=10, anchor="w").pack(side="left")
        spin_h = tk.Spinbox(row_h, from_=0, to=23, width=5, font=("Segoe UI", 11),
                            bg=self.MENU_BG, fg=self.FG, buttonbackground=self.MENU_HOVER,
                            highlightthickness=0, bd=1, relief="solid")
        spin_h.pack(side="left", padx=(5, 0))
        spin_h.delete(0, "end")
        spin_h.insert(0, "0")

        row_m = tk.Frame(body, bg=self.BG)
        row_m.pack(fill="x", pady=3)
        tk.Label(row_m, text="Минуты:", font=("Segoe UI", 10), bg=self.BG, fg=self.FG, width=10, anchor="w").pack(side="left")
        spin_m = tk.Spinbox(row_m, from_=0, to=59, width=5, font=("Segoe UI", 11),
                            bg=self.MENU_BG, fg=self.FG, buttonbackground=self.MENU_HOVER,
                            highlightthickness=0, bd=1, relief="solid")
        spin_m.pack(side="left", padx=(5, 0))
        spin_m.delete(0, "end")
        spin_m.insert(0, "5")

        row_s = tk.Frame(body, bg=self.BG)
        row_s.pack(fill="x", pady=3)
        tk.Label(row_s, text="Секунды:", font=("Segoe UI", 10), bg=self.BG, fg=self.FG, width=10, anchor="w").pack(side="left")
        spin_s = tk.Spinbox(row_s, from_=0, to=59, width=5, font=("Segoe UI", 11),
                            bg=self.MENU_BG, fg=self.FG, buttonbackground=self.MENU_HOVER,
                            highlightthickness=0, bd=1, relief="solid")
        spin_s.pack(side="left", padx=(5, 0))
        spin_s.delete(0, "end")
        spin_s.insert(0, "0")

        def _start_timer():
            try:
                h = int(spin_h.get())
                m = int(spin_m.get())
                s = int(spin_s.get())
            except ValueError:
                return
            total = h * 3600 + m * 60 + s
            if total <= 0:
                return
            dialog.destroy()
            self._start_timer(total)

        btn_start = tk.Button(
            body, text="▶  Запустить", command=_start_timer,
            font=("Segoe UI", 10, "bold"), bg=self.GREEN, fg="white",
            bd=0, relief="flat", cursor="hand2", pady=5
        )
        btn_start.pack(fill="x", pady=(10, 0))

    def _start_timer(self, total_seconds):
        if self.timer_after_id:
            self.root.after_cancel(self.timer_after_id)
            self.timer_after_id = None

        self.timer_remaining = total_seconds
        self.timer_active = True

        if not self.timer_visible:
            self._show_timer_panel()
        else:
            if hasattr(self, 'lbl_timer_label'):
                self.lbl_timer_label.config(text="Таймер:")
            if hasattr(self, 'lbl_timer_value'):
                self.lbl_timer_value.config(text=fmt_seconds(total_seconds), fg=self.ACCENT)

        self._timer_tick()

    def _show_timer_panel(self):
        self.timer_visible = True
        self._auto_resize_height()
        self._create_timer_panel_widgets()

    def _create_timer_panel_widgets(self):
        self.root.update_idletasks()
        cur_h = self.root.winfo_height()

        title_h = 28
        status_h = 24
        available_h = cur_h - title_h - status_h

        self.timer_panel = tk.Frame(self.root, bg=self.BG, width=self.TIMER_EXTRA_WIDTH)
        self.timer_panel.place(
            x=self.BASE_WIDTH,
            y=title_h,
            width=self.TIMER_EXTRA_WIDTH,
            height=available_h
        )

        self.timer_divider = tk.Frame(self.timer_panel, width=2, bg=self.DIVIDER)
        self.timer_divider.pack(side="left", fill="y", padx=(0, 5), pady=5)

        timer_content = tk.Frame(self.timer_panel, bg=self.BG)
        timer_content.pack(fill="both", expand=True, padx=5, pady=5)

        self.lbl_timer_icon = tk.Label(
            timer_content, text="⏱️", font=("Segoe UI", 18),
            bg=self.BG, fg=self.ACCENT
        )
        self.lbl_timer_icon.pack(pady=(2, 1))

        self.lbl_timer_label = tk.Label(
            timer_content, text="Таймер:", font=("Segoe UI", 9),
            bg=self.BG, fg=self.SUB
        )
        self.lbl_timer_label.pack()

        self.lbl_timer_value = tk.Label(
            timer_content, text=fmt_seconds(self.timer_remaining),
            font=("Segoe UI", 14, "bold"),
            bg=self.BG, fg=self.ACCENT
        )
        self.lbl_timer_value.pack(pady=(1, 3))

        self.btn_timer_stop = tk.Button(
            timer_content, text="⏹ Стоп", command=self._stop_timer,
            font=("Segoe UI", 8, "bold"), bg=self.RED, fg="white",
            bd=0, relief="flat", cursor="hand2", pady=2
        )
        self.btn_timer_stop.pack(fill="x", padx=8)

    def _hide_timer_panel(self):
        self.timer_visible = False

        if hasattr(self, 'timer_panel') and self.timer_panel.winfo_exists():
            self.timer_panel.destroy()

        self._auto_resize_height()

    def _stop_timer(self):
        self.timer_active = False
        if self.timer_after_id:
            self.root.after_cancel(self.timer_after_id)
            self.timer_after_id = None
        self._hide_timer_panel()

    def _timer_tick(self):
        if not self.timer_active:
            return

        if self.timer_remaining <= 0:
            self.timer_active = False
            if self.timer_visible and hasattr(self, 'lbl_timer_value'):
                self.lbl_timer_value.config(text="00:00:00", fg=self.RED)
                self.lbl_timer_label.config(text="Время вышло!")
            self._timer_blink(0)
            return

        if self.timer_visible and hasattr(self, 'lbl_timer_value'):
            self.lbl_timer_value.config(text=fmt_seconds(self.timer_remaining))

            if self.timer_remaining <= 10:
                self.lbl_timer_value.config(fg=self.RED)
            elif self.timer_remaining <= 60:
                self.lbl_timer_value.config(fg=self.YELLOW)
            else:
                self.lbl_timer_value.config(fg=self.ACCENT)

        self.timer_remaining -= 1
        self.timer_after_id = self.root.after(1000, self._timer_tick)

    def _timer_blink(self, count):
        if count >= 10:
            self.root.after(2000, self._stop_timer)
            return
        if self.timer_visible and hasattr(self, 'lbl_timer_value'):
            current_fg = self.lbl_timer_value.cget("fg")
            new_fg = self.BG if current_fg != self.BG else self.RED
            self.lbl_timer_value.config(fg=new_fg)
        self.root.after(300, lambda: self._timer_blink(count + 1))

    def _build(self):
        # ─── Заголовочная полоса ───
        self.title_bar = tk.Frame(self.root, bg=self.TITLE_BG, height=28)
        self.title_bar.pack(fill="x")
        self.title_bar.pack_propagate(False)

        self.title_bar.bind("<Button-1>", self._start_drag)
        self.title_bar.bind("<B1-Motion>", self._do_drag)

        self.btn_pin = tk.Button(
            self.title_bar, text="📌", command=self._toggle_pin,
            font=("Segoe UI", 8), bg=self.TITLE_BG, fg=self.BTN_FG,
            bd=0, relief="flat", cursor="hand2",
        )
        self.btn_pin.pack(side="left", padx=(4, 0))

        self.btn_other = tk.Button(
            self.title_bar, text="Другое ▾", command=self._toggle_menu,
            font=("Segoe UI", 8), bg=self.TITLE_BG, fg=self.BTN_FG,
            bd=0, relief="flat", cursor="hand2",
        )
        self.btn_other.pack(side="left", padx=(6, 0))

        self.btn_close = tk.Button(
            self.title_bar, text="✕", command=self._close,
            font=("Segoe UI", 9, "bold"), bg=self.CLOSE_BG, fg=self.CLOSE_FG,
            bd=0, relief="flat", cursor="hand2", width=3,
            padx=0, pady=0
        )
        self.btn_close.pack(side="right", padx=0, pady=0, ipadx=0, ipady=0)

        self.lbl_title = tk.Label(
            self.title_bar, text="СРМК", font=("Segoe UI", 12),
            bg=self.TITLE_BG, fg=self.BTN_FG
        )
        self.lbl_title.pack(side="right", padx=(0, 6))
        self.lbl_title.bind("<Button-1>", self._start_drag)
        self.lbl_title.bind("<B1-Motion>", self._do_drag)

        # ─── Основная область ───
        self.main_frame = tk.Frame(self.root, bg=self.BG)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(4, 0))

        self.time_row = tk.Frame(self.main_frame, bg=self.BG)
        self.time_row.pack(fill="x")

        self.lbl_time = tk.Label(
            self.time_row, text="", font=("Segoe UI", 28, "bold"),
            bg=self.BG, fg=self.ACCENT
        )
        self.lbl_time.pack(side="left")

        self.date_frame = tk.Frame(self.time_row, bg=self.BG)
        self.date_frame.pack(side="right", anchor="e", padx=(0, 2))

        self.lbl_dayname = tk.Label(
            self.date_frame, text="", font=("Segoe UI", 10),
            bg=self.BG, fg=self.SUB, anchor="e"
        )
        self.lbl_dayname.pack(anchor="e")

        self.lbl_date = tk.Label(
            self.date_frame, text="", font=("Segoe UI", 10),
            bg=self.BG, fg=self.SUB, anchor="e"
        )
        self.lbl_date.pack(anchor="e")

        self.divider = tk.Frame(self.main_frame, height=2, bg=self.DIVIDER)
        self.divider.pack(fill="x", pady=(3, 5))

        # ─── Строки информации ───
        self.info_frame = tk.Frame(self.main_frame, bg=self.BG)
        self.info_frame.pack(fill="x")

        self.row1 = tk.Frame(self.info_frame, bg=self.BG)
        self.row1.pack(fill="x", pady=1)
        self.lbl_cur_label = tk.Label(
            self.row1, text="Текущая:", font=("Segoe UI", 10),
            bg=self.BG, fg=self.SUB, anchor="w"
        )
        self.lbl_cur_label.pack(side="left")
        self.lbl_cur = tk.Label(
            self.row1, text="—", font=("Segoe UI", 12, "bold"),
            bg=self.BG, fg=self.FG, anchor="w"
        )
        self.lbl_cur.pack(side="left", padx=(12, 0))

        self.row2 = tk.Frame(self.info_frame, bg=self.BG)
        self.row2.pack(fill="x", pady=1)
        self.lbl_brk_label = tk.Label(
            self.row2, text="До перемены:", font=("Segoe UI", 10),
            bg=self.BG, fg=self.SUB, anchor="w"
        )
        self.lbl_brk_label.pack(side="left")
        self.lbl_brk = tk.Label(
            self.row2, text="—", font=("Segoe UI", 12, "bold"),
            bg=self.BG, fg=self.YELLOW, anchor="w"
        )
        self.lbl_brk.pack(side="left", padx=(12, 0))

        self.row3 = tk.Frame(self.info_frame, bg=self.BG)
        self.row3.pack(fill="x", pady=1)
        self.lbl_nxt_label = tk.Label(
            self.row3, text="Следующая:", font=("Segoe UI", 10),
            bg=self.BG, fg=self.SUB, anchor="w"
        )
        self.lbl_nxt_label.pack(side="left")
        self.lbl_nxt = tk.Label(
            self.row3, text="—", font=("Segoe UI", 12, "bold"),
            bg=self.BG, fg=self.GREEN, anchor="w"
        )
        self.lbl_nxt.pack(side="left", padx=(12, 0))

        # ─── Статус-бар внизу ───
        self.status_bar = tk.Frame(self.root, bg=self.STATUS_ON, height=24)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)

        self.lbl_st = tk.Label(
            self.status_bar, text="", font=("Segoe UI", 9, "bold"),
            bg=self.STATUS_ON, fg=self.STATUS_FG, anchor="center"
        )
        self.lbl_st.pack(expand=True, fill="both")

    def _set_status(self, text, bg_color):
        self.status_bar.config(bg=bg_color)
        self.lbl_st.config(text=text, bg=bg_color, fg=self.STATUS_FG)

    def _show_row(self, row, show):
        if show:
            row.pack(fill="x", pady=1)
        else:
            row.pack_forget()

    def _auto_resize_height(self):
        self.root.update_idletasks()

        title_h = self.title_bar.winfo_reqheight()
        main_h = self.main_frame.winfo_reqheight()
        status_h = 24
        padding = 8

        content_h = title_h + main_h + status_h + padding

        if self.timer_visible:
            min_h = self.MIN_HEIGHT_WITH_TIMER
        else:
            min_h = self.MIN_HEIGHT

        new_h = max(content_h, min_h)

        cur_geo = self.root.geometry()
        parts = cur_geo.split("+")
        cur_x = int(parts[1])
        cur_y = int(parts[2])
        size_parts = parts[0].split("x")
        cur_w = int(size_parts[0])
        cur_h = int(size_parts[1])

        if self.timer_visible:
            expected_w = self.BASE_WIDTH + self.TIMER_EXTRA_WIDTH
        else:
            expected_w = self.BASE_WIDTH

        if cur_w != expected_w:
            if expected_w > cur_w:
                cur_x = max(0, cur_x - (expected_w - cur_w))
            else:
                cur_x = cur_x + (cur_w - expected_w)

        if cur_w != expected_w or cur_h != new_h:
            self.root.geometry(f"{expected_w}x{new_h}+{cur_x}+{cur_y}")

            if self.timer_visible and hasattr(self, 'timer_panel') and self.timer_panel.winfo_exists():
                available_h = new_h - title_h - status_h
                self.timer_panel.place_configure(height=available_h)

    def _tick_once(self):
        now = datetime.now()
        info = analyze_time(now)

        self.lbl_time.config(text=now.strftime("%H:%M:%S"))
        self.lbl_dayname.config(text=f"{info['day']},")
        self.lbl_date.config(text=now.strftime("%d.%m.%Y"))

        s = info["status"]

        if s == "day_off":
            self._show_row(self.row1, False)
            self._show_row(self.row2, False)
            self._show_row(self.row3, True)
            self.lbl_nxt_label.config(text="Следующая:")
            self.lbl_nxt.config(text="Выходной 🎉", fg=self.GREEN)
            self._set_status("Сегодня занятий нет", self.STATUS_OFF)

        elif s == "on_pair":
            self._show_row(self.row1, True)
            self._show_row(self.row2, True)
            self.lbl_cur_label.config(text="Текущая:")
            self.lbl_cur.config(text=info["pair"], fg=self.ACCENT)
            tb = info["to_break"]

            if info["is_last"]:
                self.lbl_brk_label.config(text="До конца пары:")
                self.lbl_brk.config(
                    text=fmt_dur(tb),
                    fg=self.RED if tb <= 5 else self.YELLOW
                )
                self._show_row(self.row3, False)
            else:
                self.lbl_brk_label.config(text="До перемены:")
                self.lbl_brk.config(
                    text=fmt_dur(tb),
                    fg=self.RED if tb <= 5 else self.YELLOW
                )
                self._show_row(self.row3, True)
                self.lbl_nxt_label.config(text="Следующая:")
                self.lbl_nxt.config(
                    text=f'{fmt_dur(info["to_next"])} → {info["next_name"]}',
                    fg=self.GREEN
                )
            self._set_status("Идёт занятие", self.STATUS_ON)

        elif s == "on_break":
            self._show_row(self.row1, False)
            self._show_row(self.row2, False)
            self._show_row(self.row3, True)
            self.lbl_nxt_label.config(text="Следующая:")
            self.lbl_nxt.config(
                text=f'{fmt_dur(info["to_next"])} → {info["next_name"]}',
                fg=self.GREEN
            )
            self._set_status("Перемена", self.STATUS_BRK)

        elif s == "before":
            self._show_row(self.row1, False)
            self._show_row(self.row2, False)
            self._show_row(self.row3, True)
            self.lbl_nxt_label.config(text="Следующая:")
            self.lbl_nxt.config(
                text=f'{fmt_dur(info["to_next"])} → {info["next_name"]}',
                fg=self.GREEN
            )
            self._set_status("До начала занятий", self.STATUS_BEF)

        elif s == "after":
            self._show_row(self.row1, False)
            self._show_row(self.row2, False)
            self._show_row(self.row3, True)
            self.lbl_nxt_label.config(text="Статус:")
            self.lbl_nxt.config(text="Занятия окончены ✓", fg=self.GREEN)
            self._set_status("Учебный день завершён ✓", self.STATUS_OFF)

        self._auto_resize_height()

    def _tick(self):
        self._tick_once()
        self.root.after(1000, self._tick)


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":
    ScheduleApp()