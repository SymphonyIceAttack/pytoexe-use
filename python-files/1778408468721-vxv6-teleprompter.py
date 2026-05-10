import os
import sys
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import ctypes
from ctypes import wintypes
import glob

# =========================================================
# WINDOWS TEMP FONT LOADER
# =========================================================

FR_PRIVATE = 0x10
FR_NOT_ENUM = 0x20

gdi32 = ctypes.WinDLL("gdi32")
user32 = ctypes.WinDLL("user32")

AddFontResourceEx = gdi32.AddFontResourceExW
AddFontResourceEx.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.PVOID]
AddFontResourceEx.restype = wintypes.INT

RemoveFontResourceEx = gdi32.RemoveFontResourceExW
RemoveFontResourceEx.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.PVOID]
RemoveFontResourceEx.restype = wintypes.BOOL

WM_FONTCHANGE = 0x001D
HWND_BROADCAST = 0xFFFF

# =========================================================
# FIND APP DIRECTORY
# =========================================================

def app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)

# =========================================================
# LOAD TEMP FONT
# =========================================================

def load_font(font_path):
    AddFontResourceEx(font_path, FR_PRIVATE, 0)

    # refresh font cache
    user32.SendMessageW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0)

# =========================================================
# FIND FIRST FONT
# =========================================================

def find_font():
    folder = app_dir()

    for ext in ["*.ttf", "*.otf"]:
        files = glob.glob(os.path.join(folder, ext))
        if files:
            return files[0]

    return None

# =========================================================
# TELEPROMPTER
# =========================================================

class Teleprompter:

    def __init__(self, root):

        self.root = root
        self.root.title("Urdu Teleprompter")
        self.root.geometry("1200x750")
        self.root.configure(bg="black")

        self.scroll_speed = 2
        self.scrolling = False
        self.text_y = 700

        self.mirror_mode = False
        self.alignment = "right"

        self.font_size = 42

        # =================================================
        # LOAD SCRIPT
        # =================================================

        script_file = os.path.join(app_dir(), "script.txt")

        if os.path.exists(script_file):
            with open(script_file, "r", encoding="utf-8") as f:
                self.script = f.read()
        else:
            self.script = "script.txt not found"

        # =================================================
        # LOAD FONT
        # =================================================

        font_file = find_font()

        self.font_family = "Arial"

        if font_file:

            try:
                load_font(font_file)

                # try to detect font family
                all_fonts = list(tkfont.families())

                base = os.path.splitext(os.path.basename(font_file))[0].lower()

                found = None

                for f in all_fonts:

                    ff = f.lower()

                    if base in ff or ff in base:
                        found = f
                        break

                if found:
                    self.font_family = found

            except Exception as e:
                print(e)

        # =================================================
        # FONT OBJECT
        # =================================================

        self.text_font = tkfont.Font(
            family=self.font_family,
            size=self.font_size,
            weight="bold"
        )

        # =================================================
        # TOP CONTROL BAR
        # =================================================

        top = tk.Frame(root, bg="#202020")
        top.pack(fill="x")

        # START
        tk.Button(
            top,
            text="Start",
            command=self.start_scroll,
            bg="green",
            fg="white",
            width=8
        ).pack(side="left", padx=3, pady=4)

        # PAUSE
        tk.Button(
            top,
            text="Pause",
            command=self.pause_scroll,
            bg="orange",
            width=8
        ).pack(side="left", padx=3)

        # RESET
        tk.Button(
            top,
            text="Reset",
            command=self.reset_scroll,
            bg="red",
            fg="white",
            width=8
        ).pack(side="left", padx=3)

        # SPEED
        tk.Label(top, text="Speed", bg="#202020", fg="white").pack(side="left", padx=(15,3))

        self.speed_slider = tk.Scale(
            top,
            from_=1,
            to=10,
            orient="horizontal",
            bg="#202020",
            fg="white",
            command=self.change_speed,
            length=120
        )

        self.speed_slider.set(2)
        self.speed_slider.pack(side="left")

        # FONT SIZE
        tk.Label(top, text="Font", bg="#202020", fg="white").pack(side="left", padx=(15,3))

        self.font_slider = tk.Scale(
            top,
            from_=20,
            to=100,
            orient="horizontal",
            bg="#202020",
            fg="white",
            command=self.change_font_size,
            length=120
        )

        self.font_slider.set(42)
        self.font_slider.pack(side="left")

        # MIRROR MODE
        self.mirror_var = tk.BooleanVar()

        tk.Checkbutton(
            top,
            text="Mirror",
            variable=self.mirror_var,
            command=self.toggle_mirror,
            bg="#202020",
            fg="white",
            selectcolor="#202020"
        ).pack(side="left", padx=15)

        # ALIGNMENT
        tk.Label(top, text="Align", bg="#202020", fg="white").pack(side="left", padx=(10,3))

        self.align_var = tk.StringVar(value="right")

        tk.Radiobutton(
            top,
            text="Left",
            variable=self.align_var,
            value="left",
            command=self.change_alignment,
            bg="#202020",
            fg="white",
            selectcolor="#202020"
        ).pack(side="left")

        tk.Radiobutton(
            top,
            text="Center",
            variable=self.align_var,
            value="center",
            command=self.change_alignment,
            bg="#202020",
            fg="white",
            selectcolor="#202020"
        ).pack(side="left")

        tk.Radiobutton(
            top,
            text="Right",
            variable=self.align_var,
            value="right",
            command=self.change_alignment,
            bg="#202020",
            fg="white",
            selectcolor="#202020"
        ).pack(side="left")

        # RELOAD
        tk.Button(
            top,
            text="Reload Script",
            command=self.reload_script,
            bg="#444",
            fg="white"
        ).pack(side="left", padx=15)

        # TOPMOST
        self.top_var = tk.BooleanVar()

        tk.Checkbutton(
            top,
            text="Always On Top",
            variable=self.top_var,
            command=self.toggle_top,
            bg="#202020",
            fg="white",
            selectcolor="#202020"
        ).pack(side="left", padx=10)

        # =================================================
        # CANVAS
        # =================================================

        self.canvas = tk.Canvas(
            root,
            bg="black",
            highlightthickness=0
        )

        self.canvas.pack(fill="both", expand=True)

        self.text_id = None

        self.draw_text()

    # =====================================================
    # DRAW TEXT
    # =====================================================

    def draw_text(self):

        self.canvas.delete("all")

        txt = self.script

        # MIRROR
        if self.mirror_mode:

            lines = txt.split("\n")
            lines = [line[::-1] for line in lines]
            txt = "\n".join(lines)

        width = self.canvas.winfo_width()

        if width < 100:
            width = 1200

        # =================================================
        # ALIGNMENT
        # =================================================

        if self.alignment == "left":

            x = 40
            anchor = "nw"
            justify = "left"

        elif self.alignment == "center":

            x = width // 2
            anchor = "n"
            justify = "center"

        else:

            x = width - 40
            anchor = "ne"
            justify = "right"

        self.text_id = self.canvas.create_text(
            x,
            self.text_y,
            text=txt,
            font=self.text_font,
            fill="white",
            anchor=anchor,
            justify=justify,
            width=width - 80
        )

    # =====================================================
    # SCROLL LOOP
    # =====================================================

    def scroll_loop(self):

        if self.scrolling:

            self.text_y -= self.scroll_speed

            self.draw_text()

            self.root.after(30, self.scroll_loop)

    # =====================================================
    # CONTROLS
    # =====================================================

    def start_scroll(self):

        if not self.scrolling:
            self.scrolling = True
            self.scroll_loop()

    def pause_scroll(self):
        self.scrolling = False

    def reset_scroll(self):

        self.scrolling = False
        self.text_y = self.canvas.winfo_height()

        self.draw_text()

    def change_speed(self, val):
        self.scroll_speed = float(val)

    def change_font_size(self, val):

        self.font_size = int(val)

        self.text_font.configure(size=self.font_size)

        self.draw_text()

    def toggle_mirror(self):

        self.mirror_mode = self.mirror_var.get()

        self.draw_text()

    def change_alignment(self):

        self.alignment = self.align_var.get()

        self.draw_text()

    def reload_script(self):

        script_file = os.path.join(app_dir(), "script.txt")

        if os.path.exists(script_file):

            with open(script_file, "r", encoding="utf-8") as f:
                self.script = f.read()

        self.draw_text()

    def toggle_top(self):

        self.root.attributes("-topmost", self.top_var.get())

# =========================================================
# RUN
# =========================================================

root = tk.Tk()

app = Teleprompter(root)

root.mainloop()