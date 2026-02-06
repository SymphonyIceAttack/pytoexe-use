import tkinter as tk
from tkinter import filedialog, messagebox, font, colorchooser
from tkinter import ttk
import os

class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Text Editor")
        self.root.geometry("900x600")
        
        self.current_file = None
        self.default_font_family = "Arial"
        self.default_font_size = 12
        
        # Menüleiste erstellen
        self.create_menu()
        
        # Toolbar erstellen
        self.create_toolbar()
        
        # Textbereich mit Scrollbar
        self.create_text_area()
        
        # Statusleiste
        self.create_status_bar()
        
        # Tastenkombinationen
        self.setup_shortcuts()
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Datei-Menü
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Neu", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Öffnen", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Speichern", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Speichern unter...", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.quit_app)
        
        # Bearbeiten-Menü
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Bearbeiten", menu=edit_menu)
        edit_menu.add_command(label="Rückgängig", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Wiederholen", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Ausschneiden", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Kopieren", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Einfügen", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Alles auswählen", command=self.select_all, accelerator="Ctrl+A")
        
        # Format-Menü
        format_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Format", menu=format_menu)
        format_menu.add_command(label="Schriftart...", command=self.choose_font)
        format_menu.add_command(label="Schriftgröße...", command=self.choose_font_size)
        format_menu.add_command(label="Textfarbe...", command=self.choose_text_color)
        format_menu.add_command(label="Hintergrundfarbe...", command=self.choose_bg_color)
        
    def create_toolbar(self):
        toolbar = tk.Frame(self.root, bg="#f0f0f0", bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Schriftart-Dropdown
        tk.Label(toolbar, text="Schrift:", bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        
        available_fonts = sorted(font.families())
        self.font_var = tk.StringVar(value=self.default_font_family)
        font_dropdown = ttk.Combobox(toolbar, textvariable=self.font_var, 
                                     values=available_fonts, width=20, state="readonly")
        font_dropdown.pack(side=tk.LEFT, padx=5)
        font_dropdown.bind("<<ComboboxSelected>>", self.change_font)
        
        # Schriftgröße-Dropdown
        tk.Label(toolbar, text="Größe:", bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        
        font_sizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]
        self.size_var = tk.IntVar(value=self.default_font_size)
        size_dropdown = ttk.Combobox(toolbar, textvariable=self.size_var, 
                                     values=font_sizes, width=5, state="readonly")
        size_dropdown.pack(side=tk.LEFT, padx=5)
        size_dropdown.bind("<<ComboboxSelected>>", self.change_font_size)
        
        # Fett-Button
        self.bold_var = tk.BooleanVar()
        bold_btn = tk.Checkbutton(toolbar, text="B", font=("Arial", 10, "bold"),
                                  variable=self.bold_var, command=self.toggle_bold,
                                  bg="#f0f0f0", width=3)
        bold_btn.pack(side=tk.LEFT, padx=2)
        
        # Kursiv-Button
        self.italic_var = tk.BooleanVar()
        italic_btn = tk.Checkbutton(toolbar, text="I", font=("Arial", 10, "italic"),
                                    variable=self.italic_var, command=self.toggle_italic,
                                    bg="#f0f0f0", width=3)
        italic_btn.pack(side=tk.LEFT, padx=2)
        
        # Unterstrichen-Button
        self.underline_var = tk.BooleanVar()
        underline_btn = tk.Checkbutton(toolbar, text="U", font=("Arial", 10, "underline"),
                                       variable=self.underline_var, command=self.toggle_underline,
                                       bg="#f0f0f0", width=3)
        underline_btn.pack(side=tk.LEFT, padx=2)
        
    def create_text_area(self):
        # Frame für Text und Scrollbar
        text_frame = tk.Frame(self.root)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        v_scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Textbereich
        self.text_area = tk.Text(text_frame, 
                                 undo=True,
                                 wrap=tk.WORD,
                                 yscrollcommand=v_scrollbar.set,
                                 xscrollcommand=h_scrollbar.set,
                                 font=(self.default_font_family, self.default_font_size))
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        v_scrollbar.config(command=self.text_area.yview)
        h_scrollbar.config(command=self.text_area.xview)
        
        # Event-Binding für Statusaktualisierung
        self.text_area.bind("<KeyRelease>", self.update_status)
        self.text_area.bind("<ButtonRelease>", self.update_status)
        
    def create_status_bar(self):
        self.status_bar = tk.Label(self.root, text="Zeile: 1 | Spalte: 0 | Zeichen: 0",
                                   anchor=tk.W, relief=tk.SUNKEN, bd=1)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def setup_shortcuts(self):
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-a>", lambda e: self.select_all())
        
    # Datei-Operationen
    def new_file(self):
        if self.text_area.get(1.0, tk.END).strip():
            if messagebox.askyesno("Neues Dokument", "Möchten Sie die Änderungen speichern?"):
                self.save_file()
        self.text_area.delete(1.0, tk.END)
        self.current_file = None
        self.root.title("Python Text Editor - Neues Dokument")
        
    def open_file(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("Text-Dateien", "*.txt"), ("Alle Dateien", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.text_area.delete(1.0, tk.END)
                    self.text_area.insert(1.0, content)
                self.current_file = file_path
                self.root.title(f"Python Text Editor - {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Fehler", f"Datei konnte nicht geöffnet werden:\n{str(e)}")
                
    def save_file(self):
        if self.current_file:
            try:
                content = self.text_area.get(1.0, tk.END)
                with open(self.current_file, "w", encoding="utf-8") as file:
                    file.write(content)
                messagebox.showinfo("Gespeichert", "Datei wurde erfolgreich gespeichert!")
            except Exception as e:
                messagebox.showerror("Fehler", f"Datei konnte nicht gespeichert werden:\n{str(e)}")
        else:
            self.save_as_file()
            
    def save_as_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text-Dateien", "*.txt"), ("Alle Dateien", "*.*")]
        )
        if file_path:
            try:
                content = self.text_area.get(1.0, tk.END)
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(content)
                self.current_file = file_path
                self.root.title(f"Python Text Editor - {os.path.basename(file_path)}")
                messagebox.showinfo("Gespeichert", "Datei wurde erfolgreich gespeichert!")
            except Exception as e:
                messagebox.showerror("Fehler", f"Datei konnte nicht gespeichert werden:\n{str(e)}")
                
    def quit_app(self):
        if messagebox.askokcancel("Beenden", "Möchten Sie wirklich beenden?"):
            self.root.destroy()
            
    # Bearbeitungs-Funktionen
    def undo(self):
        try:
            self.text_area.edit_undo()
        except:
            pass
            
    def redo(self):
        try:
            self.text_area.edit_redo()
        except:
            pass
            
    def cut(self):
        self.text_area.event_generate("<<Cut>>")
        
    def copy(self):
        self.text_area.event_generate("<<Copy>>")
        
    def paste(self):
        self.text_area.event_generate("<<Paste>>")
        
    def select_all(self):
        self.text_area.tag_add(tk.SEL, "1.0", tk.END)
        self.text_area.mark_set(tk.INSERT, "1.0")
        self.text_area.see(tk.INSERT)
        return 'break'
        
    # Format-Funktionen
    def change_font(self, event=None):
        current_font = font.Font(font=self.text_area['font'])
        self.text_area.config(font=(self.font_var.get(), 
                                   current_font.actual()['size'],
                                   self.get_font_style()))
        
    def change_font_size(self, event=None):
        current_font = font.Font(font=self.text_area['font'])
        self.text_area.config(font=(current_font.actual()['family'], 
                                   self.size_var.get(),
                                   self.get_font_style()))
        
    def get_font_style(self):
        style = []
        if self.bold_var.get():
            style.append("bold")
        if self.italic_var.get():
            style.append("italic")
        if self.underline_var.get():
            style.append("underline")
        return " ".join(style) if style else "normal"
        
    def toggle_bold(self):
        self.update_font_style()
        
    def toggle_italic(self):
        self.update_font_style()
        
    def toggle_underline(self):
        self.update_font_style()
        
    def update_font_style(self):
        current_font = font.Font(font=self.text_area['font'])
        self.text_area.config(font=(current_font.actual()['family'], 
                                   current_font.actual()['size'],
                                   self.get_font_style()))
        
    def choose_font(self):
        current_font = font.Font(font=self.text_area['font'])
        font_window = tk.Toplevel(self.root)
        font_window.title("Schriftart auswählen")
        font_window.geometry("400x500")
        
        tk.Label(font_window, text="Schriftart:").pack(pady=5)
        
        listbox = tk.Listbox(font_window, height=15)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        available_fonts = sorted(font.families())
        for f in available_fonts:
            listbox.insert(tk.END, f)
            
        def apply_font():
            selection = listbox.curselection()
            if selection:
                selected_font = listbox.get(selection[0])
                self.font_var.set(selected_font)
                self.change_font()
                font_window.destroy()
                
        tk.Button(font_window, text="OK", command=apply_font).pack(pady=10)
        
    def choose_font_size(self):
        size_window = tk.Toplevel(self.root)
        size_window.title("Schriftgröße auswählen")
        size_window.geometry("200x150")
        
        tk.Label(size_window, text="Größe auswählen:").pack(pady=10)
        
        size_scale = tk.Scale(size_window, from_=8, to=72, orient=tk.HORIZONTAL)
        current_font = font.Font(font=self.text_area['font'])
        size_scale.set(current_font.actual()['size'])
        size_scale.pack(pady=10)
        
        def apply_size():
            self.size_var.set(size_scale.get())
            self.change_font_size()
            size_window.destroy()
            
        tk.Button(size_window, text="OK", command=apply_size).pack(pady=10)
        
    def choose_text_color(self):
        color = colorchooser.askcolor(title="Textfarbe auswählen")
        if color[1]:
            self.text_area.config(fg=color[1])
            
    def choose_bg_color(self):
        color = colorchooser.askcolor(title="Hintergrundfarbe auswählen")
        if color[1]:
            self.text_area.config(bg=color[1])
            
    # Statusleiste
    def update_status(self, event=None):
        line, column = self.text_area.index(tk.INSERT).split('.')
        char_count = len(self.text_area.get(1.0, tk.END)) - 1
        self.status_bar.config(text=f"Zeile: {line} | Spalte: {column} | Zeichen: {char_count}")


if __name__ == "__main__":
    root = tk.Tk()
    editor = TextEditor(root)
    root.mainloop()