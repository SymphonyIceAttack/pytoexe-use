import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.font as tkfont
import glob

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
        self.alignment = "right"   # default: Urdu style (right aligned)
        self.font_path = None
        self.current_font_name = "Default"

        # Load script
        self.load_script_from_file()

        # Create GUI
        self.create_controls()
        self.create_canvas()

        # Load font from folder (simple method)
        self.load_font_simple()

        # Initial display
        self.update_display()
        self.root.after(100, self.reset_scroll)  # wait for canvas size

        # Keyboard shortcuts
        self.root.bind('<space>', lambda e: self.start_scroll() if not self.scrolling else self.pause_scroll())
        self.root.bind('<Escape>', lambda e: self.reset_scroll())
        self.root.bind('<Up>', lambda e: self.change_speed(self.scroll_speed + 0.5))
        self.root.bind('<Down>', lambda e: self.change_speed(self.scroll_speed - 0.5))

    # ---------- File ----------
    def load_script_from_file(self):
        folder = self.get_base_folder()
        script_path = os.path.join(folder, "script.txt")
        try:
            if os.path.exists(script_path):
                with open(script_path, 'r', encoding='utf-8') as f:
                    self.script_text = f.read()
            else:
                self.script_text = "script.txt not found.\nPlease create 'script.txt' in the same folder with Urdu text."
        except Exception as e:
            self.script_text = f"Error reading script.txt: {e}"

    def get_base_folder(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def reload_script(self):
        self.load_script_from_file()
        self.update_display()
        self.reset_scroll()

    # ---------- Font (Simplified, no complex API) ----------
    def load_font_simple(self):
        folder = self.get_base_folder()
        font_files = glob.glob(os.path.join(folder, "*.ttf")) + glob.glob(os.path.join(folder, "*.otf"))
        if not font_files:
            self.font_obj = tkfont.Font(family="Arial", size=40, weight="bold")
            self.current_font_name = "Arial (no custom font)"
            self.update_font_label()
            return

        self.font_path = font_files[0]
        # Try to use the font by its filename (without extension) as family name
        font_name_guess = os.path.splitext(os.path.basename(self.font_path))[0]
        try:
            # Test if tkinter can use this font family directly
            test_font = tkfont.Font(family=font_name_guess, size=40)
            # Measure a test string to check if it works
            test_font.measure("ب")
            self.font_obj = tkfont.Font(family=font_name_guess, size=40, weight="bold")
            self.current_font_name = font_name_guess
            print(f"Font loaded: {font_name_guess}")
        except:
            # Fallback to Arial
            self.font_obj = tkfont.Font(family="Arial", size=40, weight="bold")
            self.current_font_name = f"{font_name_guess} (not recognized, using Arial)"
            messagebox.showwarning("Font Warning", f"Font '{font_name_guess}' could not be used.\nUsing Arial instead.\nYou can manually select font.")
        self.update_font_label()

    def select_manual_font(self):
        filepath = filedialog.askopenfilename(
            title="Select Urdu Font (.ttf or .otf)",
            filetypes=[("Font files", "*.ttf *.otf"), ("All files", "*.*")]
        )
        if filepath:
            font_name_guess = os.path.splitext(os.path.basename(filepath))[0]
            try:
                test_font = tkfont.Font(family=font_name_guess, size=40)
                test_font.measure("ب")
                self.font_obj = tkfont.Font(family=font_name_guess, size=self.font_size_var.get(), weight="bold")
                self.current_font_name = font_name_guess
                self.font_path = filepath
                self.update_font_label()
                self.update_display()
                self.reset_scroll()
                messagebox.showinfo("Success", f"Font changed to: {font_name_guess}")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot use this font: {e}")

    def update_font_label(self):
        if hasattr(self, 'font_label'):
            self.font_label.config(text=f"Font: {self.current_font_name}")

    # ---------- GUI Controls (all in one bar) ----------
    def create_controls(self):
        control_frame = tk.Frame(self.root, bg='gray20')
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Row of buttons
        tk.Button(control_frame, text="Start", command=self.start_scroll,
                  bg='green', fg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="Pause", command=self.pause_scroll,
                  bg='orange', font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="Reset", command=self.reset_scroll,
                  bg='red', fg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=2)

        # Speed
        tk.Label(control_frame, text="Speed:", fg='white', bg='gray20').pack(side=tk.LEFT, padx=(10,2))
        self.speed_slider = tk.Scale(control_frame, from_=0.5, to=10, resolution=0.5,
                                     orient=tk.HORIZONTAL, bg='gray20', fg='white',
                                     length=120, command=self.change_speed)
        self.speed_slider.set(self.scroll_speed)
        self.speed_slider.pack(side=tk.LEFT, padx=5)

        # Font Size
        tk.Label(control_frame, text="Font Size:", fg='white', bg='gray20').pack(side=tk.LEFT, padx=(10,2))
        self.font_size_var = tk.IntVar(value=40)
        font_spin = tk.Spinbox(control_frame, from_=12, to=100, textvariable=self.font_size_var,
                               width=5, command=self.change_font)
        font_spin.pack(side=tk.LEFT, padx=5)

        # Separator
        tk.Separator(control_frame, orient=tk.VERTICAL, bg='gray50').pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Mirror Mode
        self.mirror_var = tk.BooleanVar(value=self.mirror_mode)
        tk.Checkbutton(control_frame, text="Mirror Mode", variable=self.mirror_var,
                       command=self.toggle_mirror, bg='gray20', fg='white',
                       selectcolor='gray20').pack(side=tk.LEFT, padx=5)

        # Alignment Radio
        tk.Label(control_frame, text="Alignment:", fg='white', bg='gray20').pack(side=tk.LEFT, padx=(10,2))
        self.align_var = tk.StringVar(value=self.alignment)
        tk.Radiobutton(control_frame, text="Left (English)", variable=self.align_var,
                       value="left", command=self.change_alignment, bg='gray20', fg='white',
                       selectcolor='gray20').pack(side=tk.LEFT, padx=2)
        tk.Radiobutton(control_frame, text="Right (Urdu)", variable=self.align_var,
                       value="right", command=self.change_alignment, bg='gray20', fg='white',
                       selectcolor='gray20').pack(side=tk.LEFT, padx=2)

        # Reload Script
        tk.Button(control_frame, text="Reload Script", command=self.reload_script,
                  bg='blue', fg='white').pack(side=tk.LEFT, padx=10)

        # Always on Top
        self.top_var = tk.BooleanVar(value=False)
        tk.Checkbutton(control_frame, text="Always on Top", variable=self.top_var,
                       command=self.toggle_top, bg='gray20', fg='white',
                       selectcolor='gray20').pack(side=tk.LEFT, padx=5)

        # Manual Font Button
        tk.Button(control_frame, text="Select Font", command=self.select_manual_font,
                  bg='purple', fg='white').pack(side=tk.LEFT, padx=5)

        # Font name label
        self.font_label = tk.Label(control_frame, text="Font: loading...", fg='yellow', bg='gray20')
        self.font_label.pack(side=tk.LEFT, padx=10)

    def create_canvas(self):
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.text_id = None

    # ---------- Text Mirror & Alignment ----------
    def mirror_text(self, text):
        if self.mirror_mode:
            lines = text.split('\n')
            return '\n'.join(line[::-1] for line in lines)
        return text

    def update_display(self):
        if not self.canvas.winfo_exists():
            return
        self.canvas.delete("all")
        display_text = self.mirror_text(self.script_text)
        font_size = self.font_size_var.get()
        if self.font_obj:
            self.font_obj.configure(size=font_size)
        else:
            self.font_obj = tkfont.Font(family="Arial", size=font_size, weight="bold")

        canvas_width = max(100, self.canvas.winfo_width())
        margin = 30
        if self.alignment == "left":
            anchor = 'nw'
            x = margin
        else:  # right alignment (Urdu)
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

    def on_resize(self, event=None):
        if self.text_id and self.canvas.winfo_exists():
            canvas_width = max(100, self.canvas.winfo_width())
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
        self.on_resize()

    def toggle_top(self):
        self.root.attributes('-topmost', self.top_var.get())

    # ---------- Scrolling ----------
    def start_scroll(self):
        if not self.scrolling:
            self.scrolling = True
            self._scroll_loop()

    def _scroll_loop(self):
        if self.scrolling and self.canvas.winfo_exists():
            self.current_y -= self.scroll_speed
            if self.text_id:
                canvas_width = max(100, self.canvas.winfo_width())
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

# ---------- Run ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = UrduTeleprompter(root)
    root.mainloop()