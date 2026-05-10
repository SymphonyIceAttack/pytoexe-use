import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont
import ctypes
from ctypes import wintypes
import glob
import time

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
    # Broadcast font change so tkinter can see it
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

# ==================================================
# Main Teleprompter Class (modified for better font loading)
# ==================================================
class UrduTeleprompter:
    def __init__(self, root):
        self.root = root
        self.root.title("Teleprompter [Developed By Malik Saleem 0300-9404560]")
        self.root.geometry("950x700")
        self.root.configure(bg='black')

        # Variables
        self.script_text = ""
        self.scroll_speed = 2.0
        self.scrolling = False
        self.mirror_mode = False
        self.current_y = 0
        self.scroll_id = None
        self.font_obj = None
        self.alignment = "right"     # Changed default to right (Urdu style)
        self.font_file = None

        # Load script
        self.load_script_from_file()

        # Load custom font from folder
        self.load_custom_font()

        # Create GUI
        self.create_menu()
        self.create_controls()
        self.create_canvas()

        # Initial display
        self.update_display()
        self.reset_scroll()

        # Keyboard shortcuts
        self.root.bind('<space>', lambda e: self.start_scroll() if not self.scrolling else self.pause_scroll())
        self.root.bind('<Escape>', lambda e: self.reset_scroll())
        self.root.bind('<Up>', lambda e: self.change_speed(self.scroll_speed + 0.5))
        self.root.bind('<Down>', lambda e: self.change_speed(self.scroll_speed - 0.5))

        # Cleanup
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

    # ========== FONT HANDLING (Improved) ==========
    def load_custom_font(self):
        self.font_file = find_font_in_folder()
        if not self.font_file:
            print("No custom font found, using default Arial")
            self.font_obj = tkfont.Font(family="Arial", size=40, weight="bold")
            return

        try:
            # Load font temporarily
            load_temp_font(self.font_file)
            # Wait a bit for the font to register
            self.root.update()
            time.sleep(0.2)
            # Get all font families after loading
            all_fonts = tkfont.families()
            font_name_guess = os.path.splitext(os.path.basename(self.font_file))[0]
            # Try multiple variations
            possible_names = [font_name_guess, 
                              font_name_guess.replace('_', ' ').replace('-', ' '),
                              font_name_guess.upper(), font_name_guess.lower()]
            found_family = None
            for name in possible_names:
                for f in all_fonts:
                    if name.lower() == f.lower() or name.lower() in f.lower() or f.lower() in name.lower():
                        found_family = f
                        break
                if found_family:
                    break
            if found_family:
                self.font_obj = tkfont.Font(family=found_family, size=40, weight="bold")
                print(f"Font loaded: {found_family}")
            else:
                # Last resort: try to use the filename as family directly
                try:
                    self.font_obj = tkfont.Font(family=font_name_guess, size=40, weight="bold")
                    self.root.tk.call("font", "measure", self.font_obj, "ب")
                    print(f"Font loaded (direct): {font_name_guess}")
                except:
                    raise Exception("Font name not recognized")
        except Exception as e:
            print(f"Font error: {e}, using Arial")
            self.font_obj = tkfont.Font(family="Arial", size=40, weight="bold")
            messagebox.showwarning("Font Warning", f"Could not load font '{os.path.basename(self.font_file)}'.\nUsing Arial.\nYou can use 'Select Font' button to try another font.")

    def select_manual_font(self):
        filepath = filedialog.askopenfilename(
            title="Select Urdu Font (.ttf or .otf)",
            filetypes=[("Font files", "*.ttf *.otf"), ("All files", "*.*")]
        )
        if filepath:
            try:
                # Unload previous font if any
                if self.font_file:
                    try:
                        unload_temp_font(self.font_file)
                    except:
                        pass
                # Load new font
                load_temp_font(filepath)
                self.root.update()
                time.sleep(0.2)
                font_name_guess = os.path.splitext(os.path.basename(filepath))[0]
                # Try to create font
                test_font = tkfont.Font(family=font_name_guess, size=40)
                test_font.measure("ب")
                self.font_obj = tkfont.Font(family=font_name_guess, size=self.font_size_var.get(), weight="bold")
                self.font_file = filepath
                self.update_display()
                self.reset_scroll()
                messagebox.showinfo("Success", f"Font loaded: {font_name_guess}")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot use this font: {e}")

    # ========== MENU BAR (unchanged) ==========
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=options_menu)

        self.mirror_var = tk.BooleanVar(value=self.mirror_mode)
        options_menu.add_checkbutton(label="Mirror Mode", variable=self.mirror_var,
                                     command=self.toggle_mirror)

        align_menu = tk.Menu(options_menu, tearoff=0)
        options_menu.add_cascade(label="Text Alignment", menu=align_menu)
        self.align_var = tk.StringVar(value=self.alignment)
        align_menu.add_radiobutton(label="Left", variable=self.align_var, value="left",
                                   command=self.change_alignment)
        align_menu.add_radiobutton(label="Center", variable=self.align_var, value="center",
                                   command=self.change_alignment)
        align_menu.add_radiobutton(label="Right", variable=self.align_var, value="right",
                                   command=self.change_alignment)

        options_menu.add_separator()
        options_menu.add_command(label="Reload Script (script.txt)", command=self.reload_script)

        self.top_var = tk.BooleanVar(value=False)
        options_menu.add_checkbutton(label="Always on Top", variable=self.top_var,
                                     command=self.toggle_top)

    def toggle_mirror(self):
        self.mirror_mode = self.mirror_var.get()
        self.update_display()

    def change_alignment(self):
        self.alignment = self.align_var.get()
        self.update_display()

    def toggle_top(self):
        self.root.attributes('-topmost', self.top_var.get())

    # ========== CONTROL BAR (added manual font button) ==========
    def create_controls(self):
        control_frame = tk.Frame(self.root, bg='gray20')
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(control_frame, text="Start", command=self.start_scroll,
                  bg='green', fg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="Pause", command=self.pause_scroll,
                  bg='orange', font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="Reset", command=self.reset_scroll,
                  bg='red', fg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=2)

        tk.Label(control_frame, text="Speed:", fg='white', bg='gray20',
                 font=('Arial', 9)).pack(side=tk.LEFT, padx=(10,2))
        self.speed_slider = tk.Scale(control_frame, from_=0.5, to=10, resolution=0.5,
                                     orient=tk.HORIZONTAL, bg='gray20', fg='white',
                                     length=150, command=self.change_speed)
        self.speed_slider.set(self.scroll_speed)
        self.speed_slider.pack(side=tk.LEFT, padx=5)

        tk.Label(control_frame, text="Font Size:", fg='white', bg='gray20',
                 font=('Arial', 9)).pack(side=tk.LEFT, padx=(10,2))
        self.font_size_var = tk.IntVar(value=40)
        font_spin = tk.Spinbox(control_frame, from_=12, to=100, textvariable=self.font_size_var,
                               width=5, command=self.change_font)
        font_spin.pack(side=tk.LEFT, padx=5)

        # Manual font select button (extra, but won't crash)
        tk.Button(control_frame, text="Select Font", command=self.select_manual_font,
                  bg='purple', fg='white', font=('Arial', 8)).pack(side=tk.LEFT, padx=10)

    def create_canvas(self):
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.text_id = None

    # ========== TEXT DISPLAY WITH MIRROR & IMPROVED ALIGNMENT ==========
    def mirror_text(self, text):
        if self.mirror_mode:
            lines = text.split('\n')
            mirrored = [line[::-1] for line in lines]
            return '\n'.join(mirrored)
        return text

    def update_display(self):
        try:
            self.canvas.delete("all")
            display_text = self.mirror_text(self.script_text)
            font_size = self.font_size_var.get()
            if self.font_obj:
                self.font_obj.configure(size=font_size)
            else:
                self.font_obj = tkfont.Font(family="Arial", size=font_size, weight="bold")

            canvas_width = self.canvas.winfo_width() if self.canvas.winfo_width() > 100 else 800
            margin = 30
            if self.alignment == "left":
                anchor = 'nw'
                x = margin
            elif self.alignment == "right":
                anchor = 'ne'
                x = canvas_width - margin
            else:  # center
                anchor = 'n'
                x = canvas_width // 2

            self.text_id = self.canvas.create_text(
                x, self.current_y,
                text=display_text,
                font=self.font_obj,
                fill='white',
                anchor=anchor,
                width=canvas_width - 2*margin
            )
            self.canvas.bind('<Configure>', lambda e: self.on_resize())
        except Exception as e:
            print("Update display error:", e)

    def on_resize(self, event=None):
        try:
            if self.text_id:
                canvas_width = self.canvas.winfo_width()
                margin = 30
                if self.alignment == "left":
                    x = margin
                    anchor = 'nw'
                elif self.alignment == "right":
                    x = canvas_width - margin
                    anchor = 'ne'
                else:
                    x = canvas_width // 2
                    anchor = 'n'
                self.canvas.coords(self.text_id, x, self.current_y)
                self.canvas.itemconfig(self.text_id, width=canvas_width - 2*margin, anchor=anchor)
        except:
            pass

    # ========== SCROLLING LOGIC (unchanged, but safe) ==========
    def start_scroll(self):
        if not self.scrolling:
            self.scrolling = True
            self._scroll_loop()

    def _scroll_loop(self):
        if self.scrolling:
            self.current_y -= self.scroll_speed
            if self.text_id:
                try:
                    canvas_width = self.canvas.winfo_width()
                    margin = 30
                    if self.alignment == "left":
                        x = margin
                        anchor = 'nw'
                    elif self.alignment == "right":
                        x = canvas_width - margin
                        anchor = 'ne'
                    else:
                        x = canvas_width // 2
                        anchor = 'n'
                    self.canvas.coords(self.text_id, x, self.current_y)
                    self.canvas.itemconfig(self.text_id, anchor=anchor)
                    bbox = self.canvas.bbox(self.text_id)
                    if bbox and bbox[3] < 0:
                        self.current_y = self.canvas.winfo_height()
                        self.canvas.coords(self.text_id, x, self.current_y)
                except:
                    pass
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