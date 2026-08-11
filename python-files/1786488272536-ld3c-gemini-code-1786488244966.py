import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import sys

class OfficeSuite(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python Mini Office Suite")
        self.geometry("900x600")
        
        # Configure overall styling
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        
        # Create Navigation / Sidebar
        self.nav_frame = ttk.Frame(self, padding=5)
        self.nav_frame.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(self.nav_frame, text="📄 Word Processor", command=lambda: self.show_frame(self.writer_frame)).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.nav_frame, text="📊 Spreadsheet", command=lambda: self.show_frame(self.calc_frame)).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.nav_frame, text="📈 Presentation", command=lambda: self.show_frame(self.impress_frame)).pack(side=tk.LEFT, padx=5)
        
        # Container for different apps
        self.container = ttk.Frame(self)
        self.container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        # Initialize Apps
        self.writer_frame = self.create_writer_app()
        self.calc_frame = self.create_calc_app()
        self.impress_frame = self.create_impress_app()
        
        # Show Word Processor by default
        self.show_frame(self.writer_frame)

    def show_frame(self, frame):
        frame.tkraise()

    # --- App 1: Word Processor (Writer) ---
    def create_writer_app(self):
        frame = ttk.Frame(self.container)
        frame.grid(row=0, column=0, sticky="nsew")
        
        # Toolbar
        toolbar = ttk.Frame(frame, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(toolbar, text="Save File", command=self.save_writer_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Open File", command=self.open_writer_file).pack(side=tk.LEFT, padx=2)
        
        # Text Editor Area
        self.text_editor = tk.Text(frame, wrap=tk.WORD, font=("Arial", 11), padx=10, pady=10)
        self.text_editor.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.text_editor.insert("1.0", "Welcome to Python Writer!\nStart typing your document here...")
        
        return frame

    def save_writer_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Documents", "*.txt"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, "w") as f:
                f.write(self.text_editor.get("1.0", tk.END))
            messagebox.showinfo("Success", "File saved successfully!")

    def open_writer_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Documents", "*.txt"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, "r") as f:
                content = f.read()
            self.text_editor.delete("1.0", tk.END)
            self.text_editor.insert("1.0", content)

    # --- App 2: Spreadsheet (Calc) ---
    def create_calc_app(self):
        frame = ttk.Frame(self.container)
        frame.grid(row=0, column=0, sticky="nsew")
        
        # Toolbar
        toolbar = ttk.Frame(frame, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(toolbar, text="Clear Grid", command=self.clear_calc_grid).pack(side=tk.LEFT, padx=2)
        
        # Grid Setup (5 rows x 5 columns)
        self.calc_cells = {}
        grid_frame = ttk.Frame(frame, padding=10)
        grid_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Column Headers
        for c in range(1, 6):
            lbl = ttk.Label(grid_frame, text=f"Col {c}", font=("Arial", 9, "bold"), anchor="center")
            lbl.grid(row=0, column=c, padx=2, pady=2, sticky="nsew")
            
        # Rows and Entries
        for r in range(1, 6):
            lbl = ttk.Label(grid_frame, text=f"Row {r}", font=("Arial", 9, "bold"))
            lbl.grid(row=r, column=0, padx=2, pady=2, sticky="e")
            for c in range(1, 6):
                entry = ttk.Entry(grid_frame, width=15)
                entry.grid(row=r, column=c, padx=2, pady=2)
                self.calc_cells[(r, c)] = entry
                
        return frame

    def clear_calc_grid(self):
        for entry in self.calc_cells.values():
            entry.delete(0, tk.END)

    # --- App 3: Presentation (Impress) ---
    def create_impress_app(self):
        frame = ttk.Frame(self.container)
        frame.grid(row=0, column=0, sticky="nsew")
        
        self.slides_data = [
            {"title": "Slide 1: Introduction", "content": "Welcome to Python Impress.\nEasily manage simple slide notes and titles."},
            {"title": "Slide 2: Features", "content": "- Lightweight Python UI\n- Built using Tkinter\n- Fully functional standard library tools"},
            {"title": "Slide 3: Conclusion", "content": "Thank you for using the Python Office Suite!"}
        ]
        self.current_slide_idx = 0
        
        # Slide Display Card Container
        slide_card = ttk.Frame(frame, padding=30, relief="solid")
        slide_card.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        self.slide_title_lbl = ttk.Label(slide_card, text="", font=("Arial", 18, "bold"))
        self.slide_title_lbl.pack(pady=(0, 20))
        
        self.slide_content_lbl = ttk.Label(slide_card, text="", font=("Arial", 12), justify="center")
        self.slide_content_lbl.pack(fill=tk.BOTH, expand=True)
        
        # Controls Toolbar
        controls = ttk.Frame(frame, padding=10)
        controls.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(controls, text="◀ Previous", command=self.prev_slide).pack(side=tk.LEFT, padx=20)
        self.slide_counter_lbl = ttk.Label(controls, text="", font=("Arial", 10, "bold"))
        self.slide_counter_lbl.pack(side=tk.LEFT, expand=True)
        ttk.Button(controls, text="Next ▶", command=self.next_slide).pack(side=tk.RIGHT, padx=20)
        
        self.update_slide_view()
        return frame

    def update_slide_view(self):
        current = self.slides_data[self.current_slide_idx]
        self.slide_title_lbl.config(text=current["title"])
        self.slide_content_lbl.config(text=current["content"])
        self.slide_counter_lbl.config(text=f"Slide {self.current_slide_idx + 1} of {len(self.slides_data)}")

    fn_next = lambda self: (setattr(self, 'current_slide_idx', min(self.current_slide_idx + 1, len(self.slides_data) - 1)), self.update_slide_view())
    fn_prev = lambda self: (setattr(self, 'current_slide_idx', max(self.current_slide_idx - 1, 0)), self.update_slide_view())
    
    def next_slide(self):
        if self.current_slide_idx < len(self.slides_data) - 1:
            self.current_slide_idx += 1
            self.update_slide_view()

    def prev_slide(self):
        if self.current_slide_idx > 0:
            self.current_slide_idx -= 1
            self.update_slide_view()

if __name__ == "__main__":
    app = OfficeSuite()
    app.mainloop()