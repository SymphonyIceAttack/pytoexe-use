import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont
import ctypes
from ctypes import wintypes
import glob

# ==================================================
# Windows Font API - Temporary Font Loading
# ==================================================
FR_PRIVATE = 0x10
HWND_BROADCAST = 0xFFFF
WM_FONTCHANGE = 0x001D

gdi32 = ctypes.WinDLL('gdi32')
user32 = ctypes.windll.user32

gdi32.AddFontResourceExW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p]
gdi32.AddFontResourceExW.restype = ctypes.c_int
gdi32.RemoveFontResourceExW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p]
gdi32.RemoveFontResourceExW.restype = ctypes.c_int

def load_temp_font(font_path):
    result = gdi32.AddFontResourceExW(font_path, FR_PRIVATE, None)
    if result == 0:
        raise Exception(f"Font load failed: {font_path}")
    # Broadcast WM_FONTCHANGE so that tkinter can see the new font
    user32.SendMessageTimeoutW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0, 0, 0, 0)
    return result

def unload_temp_font(font_path):
    gdi32.RemoveFontResourceExW(font_path, FR_PRIVATE, None)
    user32.SendMessageTimeoutW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0, 0, 0, 0)

def find_font_in_folder():
    folder = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
    for ext in ['*.ttf', '*.otf']:
        files = glob.glob(os.path.join(folder, ext))
        if files:
            return files[0]
    return None

def get_font_family_after_load(font_path):
    """
    Try to guess the font family name.
    We'll list all tkinter font families and find one that matches
    the filename (without extension) or a common variation.
    """
    base = os.path.splitext(os.path.basename(font_path))[0]
    # Replace underscores/hyphens with spaces for better matching
    variations = [base, base.replace('_', ' ').replace('-', ' ')]
    all_fonts = tkfont.families()
    for var in variations:
        for f in all_fonts:
            if var.lower() == f.lower():
                return f
            if var.lower() in f.lower() or f.lower() in var.lower():
                return f
    return None

# ==================================================
# Main Application
# ==================================================
class UrduTeleprompter:
    def __init__(self, root):
        self.root = root
        self.root.title("Teleprompter [Developed By Malik Saleem 0300-9404560]")
        self.root.geometry("1000x700")
        self.root.configure(bg='black')

        # Variables
        self.script_text = ""
        self.scroll_speed = 2.0
        self.scrolling = False
        self.mirror_mode = False
        self.current_y = 0
        self.scroll_id = None
        self.font_obj = None
        self.alignment = "right"   # default: right alignment (like Urdu)
        self.font_file = None
        self.current_font_name = "Default (Arial)"

        # Load script
        self.load_script_from_file()

        # Create GUI controls first (so we can update font label later)
        self.create_controls()
        self.create_canvas()

        # Load font from folder (after controls exist)
        self.load_custom_font()

        # Initial display
        self.update_display()
        self.reset_scroll()

        # Keyboard shortcuts
        self.root.bind('<space>', lambda e: self.start_scroll() if not self.scrolling else self.pause_scroll())
        self.root.bind('<Escape>', lambda e: self.reset_scroll())
        self.root.bind('<Up>', lambda e: self.change_speed(self.scroll_speed + 0.5))
        self.root.bind('<Down>', lambda e: self.change_speed(self.scroll_speed - 0.5))

        # Cleanup on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ========== FILE HANDLING ==========
    def load_script_from_file(self):
        folder = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
        script_path = os.path.join(folder, "script.txt")
        if os.path.exists(script_path):
            with open(script_path, 'r', encoding='utf-8') as f:
                self.script_text = f.read()
        else:
            self.script_text = "script.txt not found.\nPlease create 'script.txt' in the same folder with Urdu text."

    def reload_script(self):
        self.load_script_from_file()
        self.update_display()
        self.reset_scroll()

    # ========== FONT HANDLING ==========
    def load_custom_font(self):
        self.font_file = find_font_in_folder()
        if not self.font_file:
            messagebox.showwarning("Font", "No .ttf or .otf font found in folder.\nUsing default Arial.")
            self.font_obj = tkfont.Font(family="Arial", size=40, weight="bold")
            self.current_font_name = "Arial (default)"
            self.update_font_label()
            return

        try:
            # Load temporarily
            load_temp_font(self.font_file)
            # Wait a bit for font registration
            self.root.update()
            # Try to find family name
            family = get_font_family_after_load(self.font_file)
            if family:
                self.font_obj = tkfont.Font(family=family, size=40, weight="bold")
                self.current_font_name = family
                print(f"Loaded font: {family} from {self.font_file}")
            else:
                # Fallback: create font with filename as family (sometimes works)
                base = os.path.splitext(os.path.basename(self.font_file))[0]
                self.font_obj = tkfont.Font(family=base, size=40, weight="bold")
                self.current_font_name = base
                print(f"Loaded font (direct): {base}")
            self.update_font_label()
        except Exception as e:
            messagebox.showerror("Font Error", f"Could not load font: {e}\nUsing Arial.")
            self.font_obj = tkfont.Font(family="Arial", size=40, weight="bold")
            self.current_font_name = "Arial (fallback)"
            self.update_font_label()

    def select_manual_font(self):
        filepath = filedialog.askopenfilename(
            title="Select Urdu Font",
            filetypes=[("Font files", "*.ttf *.otf"), ("All files", "*.*")]
        )
        if filepath:
            # Unload previous if any
            if self.font_file:
                try:
                    unload_temp_font(self.font_file)
                except:
                    pass
            self.font_file = filepath
            try:
                load_temp_font(self.font_file)
                self.root.update()
                family = get_font_family_after_load(self.font_file)
                if family:
                    self.font_obj = tkfont.Font(family=family, size=self.font_size_var.get(), weight="bold")
                    self.current_font_name = family
                else:
                    base = os.path.splitext(os.path.basename(self.font_file))[0]
                    self.font_obj = tkfont.Font(family=base, size=self.font_size_var.get(), weight="bold")
                    self.current_font_name = base
                self.update_font_label()
                self.update_display()
                self.reset_scroll()
                messagebox.showinfo("Success", f"Font loaded: {self.current_font_name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load font: {e}")

    def update_font_label(self):
        self.font_label.config(text=f"Font: {self.current_font_name}")

    # ========== CONTROL BAR (all options here) ==========
    def create_controls(self):
        control_frame = tk.Frame(self.root, bg='gray20')
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Row 1: Start, Pause, Reset, Speed, Font Size
        btn_start = tk.Button(control_frame, text="Start", command=self.start_scroll,
                              bg='green', fg='white', font=('Arial', 10, 'bold'))
        btn_start.pack(side=tk.LEFT, padx=2)

        btn_pause = tk.Button(control_frame, text="Pause", command=self.pause_scroll,
                              bg='orange', font=('Arial', 10, 'bold'))
        btn_pause.pack(side=tk.LEFT, padx=2)

        btn_reset = tk.Button(control_frame, text="Reset", command=self.reset_scroll,
                              bg='red', fg='white', font=('Arial', 10, 'bold'))
        btn_reset.pack(side=tk.LEFT, padx=2)

        # Speed
        tk.Label(control_frame, text="Speed:", fg='white', bg='gray20', font=('Arial', 9)).pack(side=tk.LEFT, padx=(10,2))
        self.speed_slider = tk.Scale(control_frame, from_=0.5, to=10, resolution=0.5,
                                     orient=tk.HORIZONTAL, bg='gray20', fg='white',
                                     length=120, command=self.change_speed)
        self.speed_slider.set(self.scroll_speed)
        self.speed_slider.pack(side=tk.LEFT, padx=5)

        # Font Size
        tk.Label(control_frame, text="Font Size:", fg='white', bg='gray20', font=('Arial', 9)).pack(side=tk.LEFT, padx=(10,2))
        self.font_size_var = tk.IntVar(value=40)
        font_spin = tk.Spinbox(control_frame, from_=12, to=100, textvariable=self.font_size_var,
                               width=5, command=self.change_font)
        font_spin.pack(side=tk.LEFT, padx=5)

        # Separator
        tk.Separator(control_frame, orient=tk.VERTICAL, bg='gray50').pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Mirror Mode (Checkbox)
        self.mirror_var = tk.BooleanVar(value=self.mirror_mode)
        chk_mirror = tk.Checkbutton(control_frame, text="Mirror Mode", variable=self.mirror_var,
                                    command=self.toggle_mirror, bg='gray20', fg='white',
                                    selectcolor='gray20', font=('Arial', 9))
        chk_mirror.pack(side=tk.LEFT, padx=5)

        # Alignment Radio Buttons
        tk.Label(control_frame, text="Alignment:", fg='white', bg='gray20', font=('Arial', 9)).pack(side=tk.LEFT, padx=(10,2))
        self.align_var = tk.StringVar(value=self.alignment)
        rb_left = tk.Radiobutton(control_frame, text="Left (English style)", variable=self.align_var,
                                 value="left", command=self.change_alignment, bg='gray20', fg='white',
                                 selectcolor='gray20', font=('Arial', 9))
        rb_left.pack(side=tk.LEFT, padx=2)
        rb_right = tk.Radiobutton(control_frame, text="Right (Urdu style)", variable=self.align_var,
                                  value="right", command=self.change_alignment, bg='gray20', fg='white',
                                  selectcolor='gray20', font=('Arial', 9))
        rb_right.pack(side=tk.LEFT, padx=2)

        # Reload Script Button
        btn_reload = tk.Button(control_frame, text="Reload Script", command=self.reload_script,
                               bg='blue', fg='white', font=('Arial', 9))
        btn_reload.pack(side=tk.LEFT, padx=10)

        # Always on Top Checkbox
        self.top_var = tk.BooleanVar(value=False)
        chk_top = tk.Checkbutton(control_frame, text="Always on Top", variable=self.top_var,
                                 command=self.toggle_top, bg='gray20', fg='white',
                                 selectcolor='gray20', font=('Arial', 9))
        chk_top.pack(side=tk.LEFT, padx=5)

        # Manual Font Select Button
        btn_font = tk.Button(control_frame, text="Select Font Manually", command=self.select_manual_font,
                             bg='purple', fg='white', font=('Arial', 9))
        btn_font.pack(side=tk.LEFT, padx=5)

        # Font Label (shows current font)
        self.font_label = tk.Label(control_frame, text="Font: loading...", fg='yellow', bg='gray20', font=('Arial', 8))
        self.font_label.pack(side=tk.LEFT, padx=10)

    def create_canvas(self):
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.text_id = None

    # ========== TEXT MIRROR & ALIGNMENT ==========
    def mirror_text(self, text):
        if self.mirror_mode:
            lines = text.split('\n')
            mirrored = [line[::-1] for line in lines]
            return '\n'.join(mirrored)
        return text

    def update_display(self):
        self.canvas.delete("all")
        display_text = self.mirror_text(self.script_text)
        font_size = self.font_size_var.get()
        if self.font_obj:
            self.font_obj.configure(size=font_size)
        else:
            self.font_obj = tkfont.Font(family="Arial", size=font_size, weight="bold")

        canvas_width = self.canvas.winfo_width() if self.canvas.winfo_width() > 100 else 800
        margin = 30

        # Set anchor and x based on alignment
        if self.alignment == "left":
            anchor = 'nw'
            x = margin
        else:  # right alignment (Urdu style)
            anchor = 'ne'
            x = canvas_width - margin

        self.text_id = self.canvas.create_text(
            x, self.current_y,
            text=display_text,
            font=self.font_obj,
            fill='white',
            anchor=anchor,
            width=canvas_width - 2*margin
        )
        self.canvas.bind('<Configure>', lambda e: self.on_resize())

    def on_resize(self):
        if self.text_id:
            canvas_width = self.canvas.winfo_width()
            margin = 30
            if self.alignment == "left":
                x = margin
                anchor = 'nw'
            else:
                x = canvas_width - margin
                anchor = 'ne'
            self.canvas.coords(self.text_id, x, self.current_y)
            self.canvas.itemconfig(self.text_id, width=canvas_width - 2*margin, anchor=anchor)

    def toggle_mirror(self):
        self.mirror_mode = self.mirror_var.get()
        self.update_display()

    def change_alignment(self):
        self.alignment = self.align_var.get()
        self.update_display()

    def toggle_top(self):
        self.root.attributes('-topmost', self.top_var.get())

    # ========== SCROLLING ==========
    def start_scroll(self):
        if not self.scrolling:
            self.scrolling = True
            self._scroll_loop()

    def _scroll_loop(self):
        if self.scrolling:
            self.current_y -= self.scroll_speed
            if self.text_id:
                canvas_width = self.canvas.winfo_width()
                margin = 30
                if self.alignment == "left":
                    x = margin
                    anchor = 'nw'
                else:
                    x = canvas_width - margin
                    anchor = 'ne'
                self.canvas.coords(self.text_id, x, self.current_y)
                self.canvas.itemconfig(self.text_id, anchor=anchor)
                bbox = self.canvas.bbox(self.text_id)
                if bbox and bbox[3] < 0:
                    self.current_y = self.canvas.winfo_height()
                    self.canvas.coords(self.text_id, x, self.current_y)
            self.scroll_id = self.root.after(30, self._scroll_loop)

    def pause_scroll(self):
        self.scrolling = False
        if self.scroll_id:
            self.root.after_cancel(self.scroll_id)
            self.scroll_id = None

    def reset_scroll(self):
        self.pause_scroll()
        self.current_y = self.canvas.winfo_height() if self.canvas.winfo_height() > 0 else 600
        self.update_display()

    def change_speed(self, val):
        self.scroll_speed = float(val)

    def change_font(self):
        self.update_display()

    # ========== CLEANUP ==========
    def on_closing(self):
        if self.font_file:
            try:
                unload_temp_font(self.font_file)
            except:
                pass
        self.root.destroy()

# ========== RUN ==========
if __name__ == "__main__":
    root = tk.Tk()
    app = UrduTeleprompter(root)
    root.mainloop()