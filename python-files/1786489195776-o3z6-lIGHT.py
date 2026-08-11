import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Token

class ModernIDE(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Python LightIDE")
        self.geometry("1100x700")
        self.configure(bg="#1e1e1e")
        
        # Configure Style for ttk widgets
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", background="#252526", foreground="#d4d4d4", fieldbackground="#252526", borderwidth=0)
        self.style.configure("TNotebook", background="#1e1e1e", borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#2d2d2d", foreground="#858585", padding=[10, 5])
        self.style.map("TNotebook.Tab", background=[("selected", "#1e1e1e")], foreground=[("selected", "#ffffff")])

        # Main Layout (PanedWindow for Sidebar & Editor)
        self.main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar (File Explorer)
        self.sidebar_frame = tk.Frame(self.main_pane, bg="#252526")
        self.main_pane.add(self.sidebar_frame, weight=1)
        
        self.setup_sidebar()
        
        # Right Side (Editor + Output Console)
        self.right_pane = ttk.PanedWindow(self.main_pane, orient=tk.VERTICAL)
        self.main_pane.add(self.right_pane, weight=4)
        
        # Notebook for Tabs
        self.notebook = ttk.Notebook(self.right_pane)
        self.right_pane.add(self.notebook, weight=3)
        
        # Output Console
        self.setup_console()

        # Menu Bar
        self.setup_menu()

    def setup_sidebar(self):
        # Open Folder Button
        btn_open = tk.Button(self.sidebar_frame, text="Open Folder", bg="#333333", fg="#ffffff", bd=0, command=self.open_folder)
        btn_open.pack(fill=tk.X, padx=5, pady=5)
        
        # Treeview
        self.tree = ttk.Treeview(self.sidebar_frame)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree.bind("<Double-1>", self.on_file_double_click)

    def setup_console(self):
        console_frame = tk.Frame(self.right_pane, bg="#1e1e1e")
        self.right_pane.add(console_frame, weight=1)
        
        lbl_console = tk.Label(console_frame, text="Output Console", bg="#1e1e1e", fg="#858585", anchor="w")
        lbl_console.pack(fill=tk.X, padx=5)
        
        self.console = tk.Text(console_frame, bg="#1e1e1e", fg="#d4d4d4", insertbackground="white", bd=0, font=("Consolas", 10))
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.console.config(state=tk.DISABLED)

    def setup_menu(self):
        menubar = tk.Menu(self, bg="#2d2d2d", fg="#ffffff")
        
        file_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#ffffff")
        file_menu.add_command(label="New File", command=self.new_file)
        file_menu.add_command(label="Open File...", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        run_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#ffffff")
        run_menu.add_command(label="Run Script", command=self.run_code)
        menubar.add_cascade(label="Run", menu=run_menu)
        
        self.config(menu=menubar)

    def open_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.tree.delete(*self.tree.get_children())
            node = self.tree.insert("", "end", text=folder_selected, open=True)
            self.populate_tree(node, folder_selected)

    def populate_tree(self, parent, path):
        try:
            for p in os.listdir(path):
                full_path = os.path.join(path, p)
                if os.path.isdir(full_path):
                    node = self.tree.insert(parent, "end", text=p, open=False)
                    self.populate_tree(node, full_path)
                else:
                    self.tree.insert(parent, "end", text=p)
        except PermissionError:
            pass

    def get_selected_path(self):
        item = self.tree.selection()
        if not item:
            return None
        path_parts = []
        current = item[0]
        while current:
            path_parts.insert(0, self.tree.item(current, "text"))
            current = self.tree.parent(current)
        return os.path.join(*path_parts)

    def on_file_double_click(self, event):
        path = self.get_selected_path()
        if path and os.path.isfile(path):
            self.open_file_path(path)

    def new_file(self):
        editor_frame = self.create_editor_frame()
        self.notebook.add(editor_frame, text="Untitled")
        self.notebook.select(editor_frame)

    def open_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.open_file_path(file_path)

    def open_file_path(self, file_path):
        # Check if already open
        for tab_id in self.notebook.tabs():
            widget = self.notebook.nametowidget(tab_id)
            if hasattr(widget, "file_path") and widget.file_path == file_path:
                self.notebook.select(widget)
                return

        editor_frame = self.create_editor_frame(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        editor_frame.text_area.insert("1.0", content)
        self.notebook.add(editor_frame, text=os.path.basename(file_path))
        self.notebook.select(editor_frame)
        self.highlight_syntax(editor_frame.text_area)

    def create_editor_frame(self, file_path=None):
        frame = tk.Frame(self.notebook, bg="#1e1e1e")
        frame.file_path = file_path
        
        # Line numbers
        line_numbers = tk.Text(frame, width=4, bg="#1e1e1e", fg="#858585", bd=0, font=("Consolas", 11), state=tk.DISABLED)
        line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Text Area
        text_area = tk.Text(frame, bg="#1e1e1e", fg="#d4d4d4", insertbackground="white", bd=0, font=("Consolas", 11), undo=True)
        text_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        frame.text_area = text_area
        frame.line_numbers = line_numbers
        
        # Bindings for editing events
        text_area.bind("<KeyRelease>", lambda e: self.on_text_change(frame))
        
        return frame

    def on_text_change(self, frame):
        self.highlight_syntax(frame.text_area)
        self.update_line_numbers(frame)

    def update_line_numbers(self, frame):
        line_count = int(frame.text_area.index("end-1c").split(".")[0])
        line_strings = "\n".join(str(i) for i in range(1, line_count + 1))
        
        frame.line_numbers.config(state=tk.NORMAL)
        frame.line_numbers.delete("1.0", tk.END)
        frame.line_numbers.insert("1.0", line_strings)
        frame.line_numbers.config(state=tk.DISABLED)

    def highlight_syntax(self, text_area):
        # Clear previous tags
        for tag in ["Token.Keyword", "Token.String", "Token.Comment", "Token.Name.Function"]:
            text_area.tag_remove(tag, "1.0", tk.END)
            
        content = text_area.get("1.0", tk.END)
        
        # Configure Tag Colors
        text_area.tag_configure("Token.Keyword", foreground="#c586c0")
        text_area.tag_configure("Token.String", foreground="#ce9178")
        text_area.tag_configure("Token.Comment", foreground="#6a9955")
        text_area.tag_configure("Token.Name.Function", foreground="#dcdcaa")
        
        for tok_type, value in lex(content, PythonLexer()):
            tag_name = str(tok_type)
            # Find and tag matches
            start_idx = text_area.search(value, "1.0", tk.END)
            if start_idx:
                # Basic rough tagging for demonstration
                pass

    def save_file(self):
        current_tab_id = self.notebook.select()
        if not current_tab_id:
            return
        widget = self.notebook.nametowidget(current_tab_id)
        
        if not hasattr(widget, "file_path") or not widget.file_path:
            file_path = filedialog.asksaveasfilename(defaultextension=".py")
            if not file_path:
                return
            widget.file_path = file_path
            self.notebook.tab(current_tab_id, text=os.path.basename(file_path))
            
        with open(widget.file_path, "w", encoding="utf-8") as f:
            f.write(widget.text_area.get("1.0", "end-1c"))

    def run_code(self):
        current_tab_id = self.notebook.select()
        if not current_tab_id:
            return
        widget = self.notebook.nametowidget(current_tab_id)
        
        if not hasattr(widget, "file_path") or not widget.file_path:
            messagebox.showwarning("Warning", "Please save the file before running.")
            return
            
        # Save before running
        self.save_file()
        
        # Execute script via subprocess
        self.console.config(state=tk.NORMAL)
        self.console.delete("1.0", tk.END)
        self.console.insert(tk.END, f">>> Running {widget.file_path}...\n\n")
        
        try:
            result = subprocess.run(
                [sys.executable, widget.file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.console.insert(tk.END, result.stdout)
            if result.stderr:
                self.console.insert(tk.END, result.stderr)
        except subprocess.TimeoutExpired:
            self.console.insert(tk.END, "\n[Execution timed out]")
        except Exception as e:
            self.console.insert(tk.END, f"\n[Error: {str{e}}]")
            
        self.console.config(state=tk.DISABLED)

if __name__ == "__main__":
    app = ModernIDE()
    app.mainloop()