import tkinter as tk
from tkinter import filedialog, colorchooser
import io
import contextlib
import os
import webbrowser
import tempfile
import json
import random
import string
import time
import re

# ========================= THEMES =========================

THEMES = {
    "Modern Blue": {
        "bg": "#1e1f22",
        "panel_bg": "#2b2d31",
        "editor_bg": "#2b2d31",
        "editor_fg": "#e6e6e6",
        "output_bg": "#1f2124",
        "output_fg": "#cfcfcf",
        "accent": "#4ea3ff",
        "menu_bg": "#2b2d31",
        "menu_fg": "#e6e6e6",
        "status_bg": "#1f2124",
        "status_fg": "#9bb7d9",
        "sidebar_bg": "#1e1f22",
        "sidebar_fg": "#c7d4e6",
    },
    "Modern Dark": {
        "bg": "#0f0f0f",
        "panel_bg": "#1a1a1a",
        "editor_bg": "#1a1a1a",
        "editor_fg": "#f2f2f2",
        "output_bg": "#111111",
        "output_fg": "#dcdcdc",
        "accent": "#00adee",
        "menu_bg": "#1a1a1a",
        "menu_fg": "#ffffff",
        "status_bg": "#111111",
        "status_fg": "#cccccc",
        "sidebar_bg": "#0f0f0f",
        "sidebar_fg": "#e0e0e0",
    },
    "Modern Light": {
        "bg": "#f4f4f4",
        "panel_bg": "#ffffff",
        "editor_bg": "#ffffff",
        "editor_fg": "#000000",
        "output_bg": "#f0f0f0",
        "output_fg": "#111111",
        "accent": "#0078d7",
        "menu_bg": "#e8e8e8",
        "menu_fg": "#000000",
        "status_bg": "#e8e8e8",
        "status_fg": "#333333",
        "sidebar_bg": "#e8e8e8",
        "sidebar_fg": "#000000",
    },
    "Neon Green": {
        "bg": "#020402",
        "panel_bg": "#050b05",
        "editor_bg": "#050b05",
        "editor_fg": "#b6ffb6",
        "output_bg": "#020802",
        "output_fg": "#8cff8c",
        "accent": "#00ff5a",
        "menu_bg": "#050b05",
        "menu_fg": "#b6ffb6",
        "status_bg": "#050b05",
        "status_fg": "#6cff6c",
        "sidebar_bg": "#020402",
        "sidebar_fg": "#b6ffb6",
    },
    "Neon Purple": {
        "bg": "#0b0014",
        "panel_bg": "#150026",
        "editor_bg": "#150026",
        "editor_fg": "#f2d9ff",
        "output_bg": "#0d001a",
        "output_fg": "#e6b3ff",
        "accent": "#b300ff",
        "menu_bg": "#150026",
        "menu_fg": "#f2d9ff",
        "status_bg": "#150026",
        "status_fg": "#d999ff",
        "sidebar_bg": "#0b0014",
        "sidebar_fg": "#f2d9ff",
    },
    "Neon Red": {
        "bg": "#1a0000",
        "panel_bg": "#260000",
        "editor_bg": "#260000",
        "editor_fg": "#ffcccc",
        "output_bg": "#1a0000",
        "output_fg": "#ff9999",
        "accent": "#ff2e2e",
        "menu_bg": "#260000",
        "menu_fg": "#ffcccc",
        "status_bg": "#260000",
        "status_fg": "#ffaaaa",
        "sidebar_bg": "#1a0000",
        "sidebar_fg": "#ffcccc",
    },
    "Ocean Blue": {
        "bg": "#021018",
        "panel_bg": "#031b26",
        "editor_bg": "#031b26",
        "editor_fg": "#d6f7ff",
        "output_bg": "#02141e",
        "output_fg": "#bdefff",
        "accent": "#00c0ff",
        "menu_bg": "#031b26",
        "menu_fg": "#d6f7ff",
        "status_bg": "#031b26",
        "status_fg": "#8fdfff",
        "sidebar_bg": "#021018",
        "sidebar_fg": "#d6f7ff",
    },
    "Midnight Gray": {
        "bg": "#121212",
        "panel_bg": "#1e1e1e",
        "editor_bg": "#1e1e1e",
        "editor_fg": "#e0e0e0",
        "output_bg": "#161616",
        "output_fg": "#cfcfcf",
        "accent": "#8888ff",
        "menu_bg": "#1e1e1e",
        "menu_fg": "#ffffff",
        "status_bg": "#161616",
        "status_fg": "#bbbbbb",
        "sidebar_bg": "#121212",
        "sidebar_fg": "#e0e0e0",
    }
}

LANGUAGES = ["Python", "HTML", "Batch", "JavaScript"]
DEFAULT_THEME = "Modern Blue"

# ========================= MAIN APP =========================

class DistourStudioX:
    def __init__(self, root):
        self.root = root
        self.root.title("Distour Studio X")
        self.root.geometry("1400x820")

        self.current_theme_name = DEFAULT_THEME
        self.theme = THEMES[self.current_theme_name]

        self.filename = None
        self.current_language = "Python"

        self.main_menu_frame = None
        self.editor_frame = None
        self.tools_frame = None

        self.error_message = "OK"

        # font system defaults
        self.editor_font_name = "Consolas"
        self.editor_font_size = 13
        self.output_font_size = 12

        self.build_main_menu()

    # ---------------- ERROR SYSTEM ----------------
    def set_error(self, msg):
        self.error_message = msg
        if hasattr(self, "error_bar"):
            self.error_bar.config(
                text=f"Status: {msg}",
                fg=self.theme["accent"] if msg == "OK" else "#ff4444"
            )

    # ---------------- THEME ----------------
    def apply_theme(self):
        self.root.configure(bg=self.theme["bg"])

    def set_theme(self, name):
        if name in THEMES:
            self.current_theme_name = name
            self.theme = THEMES[name]
            self.build_main_menu(refresh=True)

    # ---------------- MAIN MENU ----------------
    def build_main_menu(self, refresh=False):
        if refresh and self.main_menu_frame:
            self.main_menu_frame.destroy()
        if self.editor_frame:
            self.editor_frame.destroy()
        if self.tools_frame:
            self.tools_frame.destroy()

        self.apply_theme()

        self.main_menu_frame = tk.Frame(self.root, bg=self.theme["bg"])
        self.main_menu_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            self.main_menu_frame,
            text="DISTOUR STUDIO X",
            font=("Segoe UI", 38, "bold"),
            fg=self.theme["accent"],
            bg=self.theme["bg"]
        ).pack(pady=40)

        tk.Label(
            self.main_menu_frame,
            text="Coding studio for beginners",
            font=("Segoe UI", 16),
            fg=self.theme["editor_fg"],
            bg=self.theme["bg"]
        ).pack(pady=5)

        btn_frame = tk.Frame(self.main_menu_frame, bg=self.theme["bg"])
        btn_frame.pack(pady=40)

        self.big_button(btn_frame, "Start Coding", self.open_editor).pack(pady=10)
        self.big_button(btn_frame, "Tools", self.open_tools).pack(pady=10)
        self.big_button(btn_frame, "Themes", self.open_settings).pack(pady=10)
        self.big_button(btn_frame, "About", self.open_about).pack(pady=10)
        self.big_button(btn_frame, "Exit", self.root.quit).pack(pady=10)

        self.error_bar = tk.Label(
            self.main_menu_frame,
            text=f"Status: {self.error_message}",
            bg=self.theme["status_bg"],
            fg=self.theme["accent"],
            font=("Segoe UI", 10),
            anchor="w"
        )
        self.error_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def big_button(self, parent, text, cmd):
        return tk.Button(
            parent,
            text=text,
            command=cmd,
            bg=self.theme["accent"],
            fg=self.theme["bg"],
            relief="flat",
            padx=60,
            pady=14,
            font=("Segoe UI", 13, "bold")
        )

    # ---------------- ABOUT ----------------
    def open_about(self):
        win = tk.Toplevel(self.root)
        win.title("About Distour Studio X")
        win.geometry("560x460")
        win.configure(bg=self.theme["bg"])

        tk.Label(
            win,
            text="Distour Studio X",
            font=("Segoe UI", 20, "bold"),
            fg=self.theme["accent"],
            bg=self.theme["bg"]
        ).pack(pady=15)

        text = (
            "A modern, multi-language coding studio.\n\n"
            "Features:\n"
            "• Modern UI\n"
            "• Sidebar navigation\n"
            "• Tools panel\n"
            "• Multiple themes\n"
            "• Python / HTML / Batch / JS\n"
            "• Real CMD batch runner\n"
            "• Editor + Output console\n"
            "• Syntax highlighting\n"
            "• Font options\n"
            "• Error system\n"
            "• About + Settings\n\n"
            "Created by: Distour\n"
            "Add finchyss_ on discord if you have questions\n"
            "Version: 2.1.0"
        )

        tk.Label(
            win,
            text=text,
            font=("Segoe UI", 11),
            fg=self.theme["editor_fg"],
            bg=self.theme["bg"],
            justify="left"
        ).pack(padx=20, pady=10)

        tk.Button(
            win,
            text="Close",
            command=win.destroy,
            bg=self.theme["accent"],
            fg=self.theme["bg"],
            relief="flat",
            padx=20,
            pady=5,
            font=("Segoe UI", 10, "bold")
        ).pack(pady=15)

    # ---------------- SETTINGS ----------------
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Themes")
        win.geometry("420x400")
        win.configure(bg=self.theme["bg"])

        tk.Label(
            win,
            text="Select Theme",
            font=("Segoe UI", 16, "bold"),
            fg=self.theme["accent"],
            bg=self.theme["bg"]
        ).pack(pady=15)

        for name in THEMES:
            tk.Button(
                win,
                text=name,
                command=lambda n=name: self.set_theme(n),
                bg=self.theme["panel_bg"],
                fg=self.theme["editor_fg"],
                relief="flat",
                padx=20,
                pady=6,
                font=("Segoe UI", 10, "bold")
            ).pack(pady=4, fill=tk.X, padx=40)

    # ---------------- TOOLS PANEL ----------------
    def open_tools(self):
        if self.main_menu_frame:
            self.main_menu_frame.destroy()
        if self.editor_frame:
            self.editor_frame.destroy()

        self.apply_theme()

        self.tools_frame = tk.Frame(self.root, bg=self.theme["bg"])
        self.tools_frame.pack(fill=tk.BOTH, expand=True)

        sidebar = tk.Frame(self.tools_frame, width=200, bg=self.theme["sidebar_bg"])
        sidebar.pack(side=tk.LEFT, fill=tk.Y)

        main = tk.Frame(self.tools_frame, bg=self.theme["panel_bg"])
        main.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.sidebar_button(sidebar, "← Home", self.back_to_menu).pack(fill=tk.X, pady=4)
        self.sidebar_button(sidebar, "Editor", self.open_editor).pack(fill=tk.X, pady=4)
        self.sidebar_button(sidebar, "Color Picker", lambda: self.tool_color_picker(main)).pack(fill=tk.X, pady=4)
        self.sidebar_button(sidebar, "Text Tools", lambda: self.tool_text_tools(main)).pack(fill=tk.X, pady=4)
        self.sidebar_button(sidebar, "JSON Formatter", lambda: self.tool_json_formatter(main)).pack(fill=tk.X, pady=4)
        self.sidebar_button(sidebar, "Random Generator", lambda: self.tool_random(main)).pack(fill=tk.X, pady=4)
        self.sidebar_button(sidebar, "Timestamp", lambda: self.tool_timestamp(main)).pack(fill=tk.X, pady=4)

        tk.Label(
            main,
            text="Tools Panel",
            font=("Segoe UI", 20, "bold"),
            fg=self.theme["accent"],
            bg=self.theme["panel_bg"]
        ).pack(pady=40)

        self.error_bar = tk.Label(
            self.tools_frame,
            text=f"Status: {self.error_message}",
            bg=self.theme["status_bg"],
            fg=self.theme["accent"],
            font=("Segoe UI", 10),
            anchor="w"
        )
        self.error_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def sidebar_button(self, parent, text, cmd):
        return tk.Button(
            parent,
            text=text,
            command=cmd,
            bg=self.theme["sidebar_bg"],
            fg=self.theme["sidebar_fg"],
            relief="flat",
            padx=10,
            pady=8,
            font=("Segoe UI", 10, "bold")
        )

    # ---------------- TOOL FUNCTIONS ----------------
    def tool_color_picker(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

        tk.Label(
            frame,
            text="Color Picker",
            font=("Segoe UI", 18, "bold"),
            fg=self.theme["accent"],
            bg=self.theme["panel_bg"]
        ).pack(pady=20)

        def pick():
            color = colorchooser.askcolor()[1]
            if color:
                output.config(text=f"Selected Color: {color}")
                self.set_error("OK")
            else:
                self.set_error("Color picker canceled")

        tk.Button(
            frame,
            text="Pick Color",
            command=pick,
            bg=self.theme["accent"],
            fg=self.theme["bg"],
            relief="flat",
            padx=20,
            pady=8,
            font=("Segoe UI", 11, "bold")
        ).pack(pady=10)

        output = tk.Label(
            frame,
            text="Selected Color: None",
            font=("Segoe UI", 12),
            fg=self.theme["editor_fg"],
            bg=self.theme["panel_bg"]
        )
        output.pack(pady=10)

    def tool_text_tools(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

        tk.Label(
            frame,
            text="Text Tools",
            font=("Segoe UI", 18, "bold"),
            fg=self.theme["accent"],
            bg=self.theme["panel_bg"]
        ).pack(pady=20)

        text_box = tk.Text(
            frame,
            height=10,
            bg=self.theme["editor_bg"],
            fg=self.theme["editor_fg"],
            insertbackground=self.theme["editor_fg"],
            font=(self.editor_font_name, 12),
            border=0
        )
        text_box.pack(fill=tk.X, padx=20)

        def to_upper():
            content = text_box.get("1.0", tk.END)
            text_box.delete("1.0", tk.END)
            text_box.insert("1.0", content.upper())
            self.set_error("OK")

        def to_lower():
            content = text_box.get("1.0", tk.END)
            text_box.delete("1.0", tk.END)
            text_box.insert("1.0", content.lower())
            self.set_error("OK")

        def word_count():
            content = text_box.get("1.0", tk.END)
            count = len(content.split())
            result.config(text=f"Word Count: {count}")
            self.set_error("OK")

        tk.Button(
            frame,
            text="UPPERCASE",
            command=to_upper,
            bg=self.theme["accent"],
            fg=self.theme["bg"],
            relief="flat",
            padx=16,
            pady=4,
            font=("Segoe UI", 10, "bold")
        ).pack(pady=4)

        tk.Button(
            frame,
            text="lowercase",
            command=to_lower,
            bg=self.theme["accent"],
            fg=self.theme["bg"],
            relief="flat",
            padx=16,
            pady=4,
            font=("Segoe UI", 10, "bold")
        ).pack(pady=4)

        tk.Button(
            frame,
            text="Word Count",
            command=word_count,
            bg=self.theme["accent"],
            fg=self.theme["bg"],
            relief="flat",
            padx=16,
            pady=4,
            font=("Segoe UI", 10, "bold")
        ).pack(pady=4)

        result = tk.Label(
            frame,
            text="",
            bg=self.theme["panel_bg"],
            fg=self.theme["editor_fg"],
            font=("Segoe UI", 11)
        )
        result.pack(pady=10)

    def tool_json_formatter(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

        tk.Label(
            frame,
            text="JSON Formatter",
            font=("Segoe UI", 18, "bold"),
            fg=self.theme["accent"],
            bg=self.theme["panel_bg"]
        ).pack(pady=20)

        text_box = tk.Text(
            frame,
            height=12,
            bg=self.theme["editor_bg"],
            fg=self.theme["editor_fg"],
            insertbackground=self.theme["editor_fg"],
            font=(self.editor_font_name, 12),
            border=0
        )
        text_box.pack(fill=tk.X, padx=20)

        def format_json():
            content = text_box.get("1.0", tk.END).strip()
            if (content.startswith("{") and content.endswith("}")) or \
               (content.startswith("[") and content.endswith("]")):
                parsed = json.loads(content)
                formatted = json.dumps(parsed, indent=4)
                text_box.delete("1.0", tk.END)
                text_box.insert("1.0", formatted)
                self.set_error("OK")
            else:
                text_box.delete("1.0", tk.END)
                text_box.insert("1.0", "Invalid JSON (must start with { or [)")
                self.set_error("Invalid JSON")

        tk.Button(
            frame,
            text="Format JSON",
            command=format_json,
            bg=self.theme["accent"],
            fg=self.theme["bg"],
            relief="flat",
            padx=20,
            pady=6,
            font=("Segoe UI", 10, "bold")
        ).pack(pady=10)

    def tool_random(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

        tk.Label(
            frame,
            text="Random String Generator",
            font=("Segoe UI", 18, "bold"),
            fg=self.theme["accent"],
            bg=self.theme["panel_bg"]
        ).pack(pady=20)

        length_label = tk.Label(
            frame,
            text="Length:",
            font=("Segoe UI", 11),
            fg=self.theme["editor_fg"],
            bg=self.theme["panel_bg"]
        )
        length_label.pack(pady=4)

        length_entry = tk.Entry(
            frame,
            bg=self.theme["editor_bg"],
            fg=self.theme["editor_fg"],
            insertbackground=self.theme["editor_fg"],
            font=("Segoe UI", 11),
            border=0
        )
        length_entry.insert(0, "16")
        length_entry.pack(pady=4)

        output = tk.Text(
            frame,
            height=4,
            bg=self.theme["editor_bg"],
            fg=self.theme["editor_fg"],
            insertbackground=self.theme["editor_fg"],
            font=(self.editor_font_name, 12),
            border=0
        )
        output.pack(fill=tk.X, padx=20, pady=10)

        def generate():
            val = length_entry.get().strip()
            if not val.isdigit():
                output.delete("1.0", tk.END)
                output.insert("1.0", "Length must be a number.")
                self.set_error("Invalid length")
                return

            n = int(val)
            chars = string.ascii_letters + string.digits
            s = "".join(random.choice(chars) for _ in range(n))
            output.delete("1.0", tk.END)
            output.insert("1.0", s)
            self.set_error("OK")

        tk.Button(
            frame,
            text="Generate",
            command=generate,
            bg=self.theme["accent"],
            fg=self.theme["bg"],
            relief="flat",
            padx=20,
            pady=6,
            font=("Segoe UI", 10, "bold")
        ).pack(pady=4)

    def tool_timestamp(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

        tk.Label(
            frame,
            text="Timestamp Tool",
            font=("Segoe UI", 18, "bold"),
            fg=self.theme["accent"],
            bg=self.theme["panel_bg"]
        ).pack(pady=20)

        output = tk.Text(
            frame,
            height=6,
            bg=self.theme["editor_bg"],
            fg=self.theme["editor_fg"],
            insertbackground=self.theme["editor_fg"],
            font=(self.editor_font_name, 12),
            border=0
        )
        output.pack(fill=tk.X, padx=20, pady=10)

        def show_now():
            now = time.time()
            local = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
            output.delete("1.0", tk.END)
            output.insert("1.0", f"Unix: {int(now)}\nLocal: {local}")
            self.set_error("OK")

        tk.Button(
            frame,
            text="Now",
            command=show_now,
            bg=self.theme["accent"],
            fg=self.theme["bg"],
            relief="flat",
            padx=20,
            pady=6,
            font=("Segoe UI", 10, "bold")
        ).pack(pady=4)

    # ---------------- SYNTAX HIGHLIGHTING ----------------
    def highlight_syntax(self, event=None):
        if not hasattr(self, "code_text"):
            return

        text = self.code_text.get("1.0", tk.END)

        for tag in self.code_text.tag_names():
            self.code_text.tag_remove(tag, "1.0", tk.END)

        keyword_color = "#4ea3ff"
        string_color = "#ffcc66"
        comment_color = "#6a9955"
        number_color = "#d19a66"
        func_color = "#c678dd"

        keywords = [
            "def","class","return","if","elif","else","for","while","import","from",
            "as","with","try","except","finally","pass","break","continue","lambda",
            "True","False","None","in","is","not","and","or","global","nonlocal"
        ]

        functions = ["print","len","range","open","input","str","int","float","list","dict","set"]

        for word in keywords:
            start = "1.0"
            pattern = r"\b" + re.escape(word) + r"\b"
            while True:
                pos = self.code_text.search(pattern, start, tk.END, regexp=True)
                if not pos:
                    break
                end = f"{pos}+{len(word)}c"
                self.code_text.tag_add("keyword", pos, end)
                start = end

        for word in functions:
            start = "1.0"
            pattern = r"\b" + re.escape(word) + r"\b"
            while True:
                pos = self.code_text.search(pattern, start, tk.END, regexp=True)
                if not pos:
                    break
                end = f"{pos}+{len(word)}c"
                self.code_text.tag_add("func", pos, end)
                start = end

        start = "1.0"
        while True:
            pos = self.code_text.search(r"(['\"])", start, tk.END, regexp=True)
            if not pos:
                break
            quote = self.code_text.get(pos, f"{pos}+1c")
            end = self.code_text.search(quote, f"{pos}+1c", tk.END)
            if not end:
                break
            end = f"{end}+1c"
            self.code_text.tag_add("string", pos, end)
            start = end

        start = "1.0"
        while True:
            pos = self.code_text.search("#", start, tk.END)
            if not pos:
                break
            line = pos.split(".")[0]
            line_end = line + ".end"
            self.code_text.tag_add("comment", pos, line_end)
            start = line_end

        start = "1.0"
        while True:
            pos = self.code_text.search(r"\b[0-9]+\b", start, tk.END, regexp=True)
            if not pos:
                break
            end = f"{pos}+{len(self.code_text.get(pos, pos + ' wordend'))}c"
            self.code_text.tag_add("number", pos, end)
            start = end

        self.code_text.tag_config("keyword", foreground=keyword_color)
        self.code_text.tag_config("string", foreground=string_color)
        self.code_text.tag_config("comment", foreground=comment_color)
        self.code_text.tag_config("number", foreground=number_color)
        self.code_text.tag_config("func", foreground=func_color)

    # ---------------- FONT SYSTEM ----------------
    def set_editor_font(self, font_name):
        self.editor_font_name = font_name
        if hasattr(self, "code_text"):
            self.code_text.config(font=(font_name, self.editor_font_size))
        if hasattr(self, "output_text"):
            self.output_text.config(font=(font_name, self.output_font_size))
        self.set_error("OK")
        self.highlight_syntax()

    def adjust_font_size(self, change):
        self.editor_font_size += change
        self.output_font_size += change

        if self.editor_font_size < 6:
            self.editor_font_size = 6
        if self.output_font_size < 6:
            self.output_font_size = 6

        if hasattr(self, "code_text"):
            self.code_text.config(font=(self.editor_font_name, self.editor_font_size))
        if hasattr(self, "output_text"):
            self.output_text.config(font=(self.editor_font_name, self.output_font_size))
        self.set_error("OK")
        self.highlight_syntax()

    # ---------------- EDITOR SCREEN ----------------
    def open_editor(self):
        if self.main_menu_frame:
            self.main_menu_frame.destroy()
        if self.tools_frame:
            self.tools_frame.destroy()
        self.build_editor()

    def build_editor(self, refresh=False):
        if refresh and self.editor_frame:
            self.editor_frame.destroy()

        self.apply_theme()

        self.editor_frame = tk.Frame(self.root, bg=self.theme["bg"])
        self.editor_frame.pack(fill=tk.BOTH, expand=True)

        menubar = tk.Menu(self.root, bg=self.theme["menu_bg"], fg=self.theme["menu_fg"])

        filemenu = tk.Menu(menubar, tearoff=0, bg=self.theme["menu_bg"], fg=self.theme["menu_fg"])
        filemenu.add_command(label="New", command=self.new_file)
        filemenu.add_command(label="Open", command=self.open_file)
        filemenu.add_command(label="Save", command=self.save_file)
        filemenu.add_command(label="Save As", command=self.save_file_as)
        filemenu.add_separator()
        filemenu.add_command(label="Home", command=self.back_to_menu)
        filemenu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        langmenu = tk.Menu(menubar, tearoff=0, bg=self.theme["menu_bg"], fg=self.theme["menu_fg"])
        for lang in LANGUAGES:
            langmenu.add_command(label=lang, command=lambda l=lang: self.set_language(l))
        menubar.add_cascade(label="Language", menu=langmenu)

        runmenu = tk.Menu(menubar, tearoff=0, bg=self.theme["menu_bg"], fg=self.theme["menu_fg"])
        runmenu.add_command(label="Run", command=self.run_code)
        runmenu.add_command(label="Clear Output", command=self.clear_output)
        menubar.add_cascade(label="Run", menu=runmenu)

        fontmenu = tk.Menu(menubar, tearoff=0, bg=self.theme["menu_bg"], fg=self.theme["menu_fg"])
        fontmenu.add_command(label="Editor Font: Consolas", command=lambda: self.set_editor_font("Consolas"))
        fontmenu.add_command(label="Editor Font: JetBrains Mono", command=lambda: self.set_editor_font("JetBrains Mono"))
        fontmenu.add_command(label="Editor Font: Fira Code", command=lambda: self.set_editor_font("Fira Code"))
        fontmenu.add_command(label="Editor Font: Cascadia Code", command=lambda: self.set_editor_font("Cascadia Code"))
        fontmenu.add_separator()
        fontmenu.add_command(label="Increase Font Size", command=lambda: self.adjust_font_size(1))
        fontmenu.add_command(label="Decrease Font Size", command=lambda: self.adjust_font_size(-1))
        menubar.add_cascade(label="Fonts", menu=fontmenu)

        toolmenu = tk.Menu(menubar, tearoff=0, bg=self.theme["menu_bg"], fg=self.theme["menu_fg"])
        toolmenu.add_command(label="Open Tools Panel", command=self.open_tools)
        menubar.add_cascade(label="Tools", menu=toolmenu)

        helpmenu = tk.Menu(menubar, tearoff=0, bg=self.theme["menu_bg"], fg=self.theme["menu_fg"])
        helpmenu.add_command(label="About", command=self.open_about)
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.root.config(menu=menubar)

        toolbar = tk.Frame(self.editor_frame, bg=self.theme["bg"])
        toolbar.pack(fill=tk.X, pady=4)

        self.toolbar_button(toolbar, "New", self.new_file).pack(side=tk.LEFT, padx=4)
        self.toolbar_button(toolbar, "Open", self.open_file).pack(side=tk.LEFT, padx=4)
        self.toolbar_button(toolbar, "Save", self.save_file).pack(side=tk.LEFT, padx=4)
        self.toolbar_button(toolbar, "Run", self.run_code).pack(side=tk.LEFT, padx=4)
        self.toolbar_button(toolbar, "Clear", self.clear_output).pack(side=tk.LEFT, padx=4)
        self.toolbar_button(toolbar, "Tools", self.open_tools).pack(side=tk.LEFT, padx=4)

        self.lang_label = tk.Label(
            toolbar,
            text=f"Language: {self.current_language}",
            bg=self.theme["bg"],
            fg=self.theme["editor_fg"],
            font=("Segoe UI", 10)
        )
        self.lang_label.pack(side=tk.RIGHT, padx=10)

        main_split = tk.PanedWindow(self.editor_frame, orient=tk.VERTICAL, bg=self.theme["bg"])
        main_split.pack(fill=tk.BOTH, expand=True)

        editor_frame = tk.Frame(main_split, bg=self.theme["bg"])
        main_split.add(editor_frame)

        self.code_text = tk.Text(
            editor_frame,
            wrap="none",
            font=(self.editor_font_name, self.editor_font_size),
            bg=self.theme["editor_bg"],
            fg=self.theme["editor_fg"],
            insertbackground=self.theme["editor_fg"],
            border=0
        )
        self.code_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scroll = tk.Scrollbar(editor_frame, command=self.code_text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.code_text.config(yscrollcommand=scroll.set)

        self.code_text.bind("<KeyRelease>", self.highlight_syntax)
        self.highlight_syntax()

        output_frame = tk.Frame(main_split, bg=self.theme["bg"])
        main_split.add(output_frame)

        tk.Label(
            output_frame,
            text="Output",
            bg=self.theme["bg"],
            fg=self.theme["accent"],
            font=("Segoe UI", 11, "bold")
        ).pack(fill=tk.X)

        self.output_text = tk.Text(
            output_frame,
            height=10,
            wrap="none",
            bg=self.theme["output_bg"],
            fg=self.theme["output_fg"],
            insertbackground=self.theme["output_fg"],
            font=(self.editor_font_name, self.output_font_size),
            border=0
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        out_scroll = tk.Scrollbar(output_frame, command=self.output_text.yview)
        out_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.config(yscrollcommand=out_scroll.set)

        self.error_bar = tk.Label(
            self.editor_frame,
            text=f"Status: {self.error_message}",
            bg=self.theme["status_bg"],
            fg=self.theme["accent"],
            font=("Segoe UI", 10),
            anchor="w"
        )
        self.error_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def toolbar_button(self, parent, text, cmd):
        return tk.Button(
            parent,
            text=text,
            command=cmd,
            bg=self.theme["accent"],
            fg=self.theme["bg"],
            relief="flat",
            padx=12,
            pady=4,
            font=("Segoe UI", 9, "bold")
        )

    # ---------------- FILE OPS ----------------
    def new_file(self):
        self.filename = None
        self.code_text.delete("1.0", tk.END)
        self.set_error("OK")
        self.highlight_syntax()

    def open_file(self):
        path = filedialog.askopenfilename()
        if path:
            f = open(path, "r", encoding="utf-8")
            content = f.read()
            f.close()
            self.code_text.delete("1.0", tk.END)
            self.code_text.insert("1.0", content)
            self.filename = path
            self.set_error("OK")
            self.highlight_syntax()
        else:
            self.set_error("Open canceled")

    def save_file(self):
        if self.filename:
            f = open(self.filename, "w", encoding="utf-8")
            f.write(self.code_text.get("1.0", tk.END))
            f.close()
            self.set_error("OK")
        else:
            self.save_file_as()

    def save_file_as(self):
        path = filedialog.asksaveasfilename()
        if path:
            f = open(path, "w", encoding="utf-8")
            f.write(self.code_text.get("1.0", tk.END))
            f.close()
            self.filename = path
            self.set_error("OK")
        else:
            self.set_error("Save canceled")

    # ---------------- LANGUAGE ----------------
    def set_language(self, lang):
        self.current_language = lang
        if hasattr(self, "lang_label"):
            self.lang_label.config(text=f"Language: {self.current_language}")
        self.set_error("OK")
        self.highlight_syntax()

    # ---------------- RUN ----------------
    def clear_output(self):
        self.output_text.delete("1.0", tk.END)
        self.set_error("OK")

    def run_code(self):
        code = self.code_text.get("1.0", tk.END)

        if self.current_language == "Python":
            self.run_python(code)
        elif self.current_language == "HTML":
            self.run_html(code)
        elif self.current_language == "Batch":
            self.run_batch(code)
        elif self.current_language == "JavaScript":
            self.run_js(code)

    def run_python(self, code):
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            with contextlib.redirect_stderr(stderr):
                exec(code, {})

        out = stdout.getvalue()
        err = stderr.getvalue()

        self.output_text.insert(tk.END, out)
        self.output_text.insert(tk.END, err)

        if err.strip():
            self.set_error("Python Error")
        else:
            self.set_error("OK")

    def run_html(self, code):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8")
        tmp.write(code)
        tmp.close()
        webbrowser.open_new_tab(tmp.name)
        self.output_text.insert(tk.END, "Opened HTML in browser.\n")
        self.set_error("OK")

    def run_batch(self, code):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bat", mode="w", encoding="utf-8")
        tmp.write(code)
        tmp.close()
        os.system(f'start cmd /k "{tmp.name}"')
        self.output_text.insert(tk.END, "Opened CMD window running batch script.\n")
        self.set_error("OK")

    def run_js(self, code):
        html = f"""
        <html><body><script>{code}</script>
        <pre style='color:#0f0;background:#000'>Open console (F12) to see JS output.</pre>
        </body></html>
        """
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8")
        tmp.write(html)
        tmp.close()
        webbrowser.open_new_tab(tmp.name)
        self.output_text.insert(tk.END, "Opened JavaScript runner in browser.\n")
        self.set_error("OK")

    # ---------------- NAV ----------------
    def back_to_menu(self):
        if self.editor_frame:
            self.editor_frame.destroy()
            self.editor_frame = None
        if self.tools_frame:
            self.tools_frame.destroy()
            self.tools_frame = None
        self.build_main_menu()


def main():
    root = tk.Tk()
    DistourStudioX(root)
    root.mainloop()


if __name__ == "__main__":
    main()
