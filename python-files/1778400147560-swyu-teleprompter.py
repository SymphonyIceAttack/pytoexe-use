import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.font as tkfont
import ctypes
from ctypes import wintypes
import glob

# ========== عارضی طور پر فونٹ لوڈ کرنے کے لیے Windows API ==========
def load_font_temp(font_path):
    """Font file ko Windows mein temporary load karein (Install kiye baghair)"""
    FR_PRIVATE = 0x10
    gdi32 = ctypes.WinDLL('gdi32')
    add_font = gdi32.AddFontResourceExW
    add_font.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p]
    add_font.restype = ctypes.c_int
    result = add_font(font_path, FR_PRIVATE, None)
    if result == 0:
        raise Exception(f"Font load nahi ho saka: {font_path}")
    return result

def unload_font_temp(font_path):
    """Temporary font ko unload karna"""
    FR_PRIVATE = 0x10
    gdi32 = ctypes.WinDLL('gdi32')
    remove_font = gdi32.RemoveFontResourceExW
    remove_font.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p]
    remove_font.restype = ctypes.c_int
    remove_font(font_path, FR_PRIVATE, None)

# ========== folder mein pehli .ttf ya .otf dhundhna ==========
def find_font_file():
    folder = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
    for ext in ['*.ttf', '*.otf']:
        files = glob.glob(os.path.join(folder, ext))
        if files:
            return files[0]
    return None

# ========== فونٹ کا اندرونی نام معلوم کرنا (تیز طریقہ) ==========
def get_font_family_name(font_path):
    """Windows API se font family name nikalna"""
    # Simple approach: assume the filename without extension is the family name
    # But better to use GetFontResourceInfoW
    # We'll use a fallback: try to load with tkinter using that name after AddFontResourceEx
    base = os.path.splitext(os.path.basename(font_path))[0]
    # Common Urdu fonts often have internal name similar to filename
    return base

# ========== مرکزی ٹیلی پرامپٹر کلاس ==========
class UrduTeleprompter:
    def __init__(self, root):
        self.root = root
        self.root.title("Urdu Teleprompter - Mirror Mode")
        self.root.geometry("900x700")
        self.root.configure(bg='black')

        # Variables
        self.script_text = ""
        self.scroll_speed = 2.0
        self.scrolling = False
        self.mirror_mode = True   # Always mirror as per requirement
        self.current_y = 0
        self.scroll_id = None
        self.font_obj = None

        # Pehle script.txt ko same folder se read karo
        self.load_script_from_file()

        # Phir font file dhundho aur load karo
        font_file = find_font_file()
        if font_file:
            try:
                load_font_temp(font_file)
                font_family = get_font_family_name(font_file)
                # Try to create font (agar naam sahi ho)
                self.font_obj = tkfont.Font(family=font_family, size=40, weight="bold")
                # Test if font actually works
                self.root.tk.call("font", "measure", self.font_obj, "test")
                print(f"Font loaded: {font_family}")
            except Exception as e:
                print(f"Font load error: {e}, using default")
                self.font_obj = tkfont.Font(family="Arial", size=40, weight="bold")
        else:
            print("No custom font found, using Arial")
            self.font_obj = tkfont.Font(family="Arial", size=40, weight="bold")

        # GUI banayein
        self.create_widgets()
        self.update_display()

    def load_script_from_file(self):
        """Same folder mein 'script.txt' read karo (UTF-8)"""
        folder = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
        script_path = os.path.join(folder, "script.txt")
        if os.path.exists(script_path):
            with open(script_path, 'r', encoding='utf-8') as f:
                self.script_text = f.read()
        else:
            self.script_text = "script.txt nahi mili.\nBaraye meharbani same folder mein 'script.txt' rakhein jisme Urdu text ho."

    def create_widgets(self):
        # Control panel
        control = tk.Frame(self.root, bg='gray20')
        control.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(control, text="شروع (Start)", command=self.start_scroll, bg='green', fg='white').pack(side=tk.LEFT, padx=2)
        tk.Button(control, text="توقف (Pause)", command=self.pause_scroll, bg='orange').pack(side=tk.LEFT, padx=2)
        tk.Button(control, text="دوبارہ شروع (Reset)", command=self.reset_scroll, bg='red', fg='white').pack(side=tk.LEFT, padx=2)

        # Speed slider
        tk.Label(control, text="رفتار:", fg='white', bg='gray20').pack(side=tk.LEFT, padx=(10,2))
        self.speed_slider = tk.Scale(control, from_=0.5, to=10, orient=tk.HORIZONTAL, resolution=0.5,
                                     command=self.change_speed, bg='gray20', fg='white', length=150)
        self.speed_slider.set(self.scroll_speed)
        self.speed_slider.pack(side=tk.LEFT, padx=5)

        # Font size
        tk.Label(control, text="فونٹ سائز:", fg='white', bg='gray20').pack(side=tk.LEFT, padx=(10,2))
        self.font_size_var = tk.IntVar(value=40)
        font_spin = tk.Spinbox(control, from_=12, to=100, textvariable=self.font_size_var,
                               command=self.change_font, width=5)
        font_spin.pack(side=tk.LEFT, padx=5)

        # Reload script button
        tk.Button(control, text="اسکرپٹ دوبارہ لوڈ کریں", command=self.reload_script, bg='blue', fg='white').pack(side=tk.LEFT, padx=10)

        # Always on top
        self.top_var = tk.BooleanVar()
        tk.Checkbutton(control, text="ہمیشہ اوپر رکھیں", variable=self.top_var,
                       command=self.toggle_top, bg='gray20', fg='white', selectcolor='gray20').pack(side=tk.RIGHT, padx=10)

        # Canvas for smooth scrolling
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.text_id = None

        # Keyboard shortcuts
        self.root.bind('<space>', lambda e: self.start_scroll() if not self.scrolling else self.pause_scroll())
        self.root.bind('<Escape>', lambda e: self.reset_scroll())
        self.root.bind('<Up>', lambda e: self.change_speed(self.scroll_speed + 0.5))
        self.root.bind('<Down>', lambda e: self.change_speed(self.scroll_speed - 0.5))

    def mirror_text(self, text):
        """Mirror mode: poora text horizontally reverse karein (mirror effect)"""
        if self.mirror_mode:
            # Har line ko reverse karo aur unhe wapas jodo
            lines = text.split('\n')
            mirrored_lines = [line[::-1] for line in lines]
            return '\n'.join(mirrored_lines)
        return text

    def update_display(self):
        """Canvas pe text draw karein (mirror ke saath)"""
        self.canvas.delete("all")
        display_text = self.mirror_text(self.script_text)
        font_size = self.font_size_var.get()
        self.font_obj.configure(size=font_size)

        self.text_id = self.canvas.create_text(
            self.canvas.winfo_width() // 2,
            self.current_y,
            text=display_text,
            font=self.font_obj,
            fill='white',
            anchor='n',
            width=self.canvas.winfo_width() - 40
        )
        self.canvas.bind('<Configure>', lambda e: self.on_resize())

    def on_resize(self):
        if self.text_id:
            self.canvas.coords(self.text_id, self.canvas.winfo_width() // 2, self.current_y)
            self.canvas.itemconfig(self.text_id, width=self.canvas.winfo_width() - 40)

    def start_scroll(self):
        if not self.scrolling:
            self.scrolling = True
            self._scroll_loop()

    def _scroll_loop(self):
        if self.scrolling:
            self.current_y -= self.scroll_speed
            if self.text_id:
                self.canvas.coords(self.text_id, self.canvas.winfo_width() // 2, self.current_y)
                bbox = self.canvas.bbox(self.text_id)
                if bbox and bbox[3] < 0:
                    self.current_y = self.canvas.winfo_height()
                    self.canvas.coords(self.text_id, self.canvas.winfo_width() // 2, self.current_y)
            self.scroll_id = self.root.after(30, self._scroll_loop)

    def pause_scroll(self):
        self.scrolling = False
        if self.scroll_id:
            self.root.after_cancel(self.scroll_id)
            self.scroll_id = None

    def reset_scroll(self):
        self.pause_scroll()
        self.current_y = self.canvas.winfo_height() if self.canvas.winfo_height() > 0 else 600
        if self.text_id:
            self.canvas.coords(self.text_id, self.canvas.winfo_width() // 2, self.current_y)

    def change_speed(self, val):
        try:
            self.scroll_speed = float(val)
            self.speed_slider.set(self.scroll_speed)
        except:
            pass

    def change_font(self):
        self.update_display()

    def toggle_top(self):
        self.root.attributes('-topmost', self.top_var.get())

    def reload_script(self):
        self.load_script_from_file()
        self.update_display()
        self.reset_scroll()

    def on_closing(self):
        # Cleanup: remove temporary font if loaded
        font_file = find_font_file()
        if font_file:
            try:
                unload_font_temp(font_file)
            except:
                pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = UrduTeleprompter(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()