import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog, colorchooser, font
import webbrowser
import os
import re

class ToolTip:
    """Podpowiedź dla przycisków"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind('<Enter>', self.show_tip)
        widget.bind('<Leave>', self.hide_tip)

    def show_tip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("Arial", 10))
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class IconButton(tk.Button):
    """Przycisk z ikoną, zaokrąglony, z efektem hover"""
    def __init__(self, parent, icon, command, tooltip, bg_normal, bg_hover="#555555", fg="#ffffff", **kwargs):
        super().__init__(parent, text=icon, command=command,
                         font=("Segoe UI Emoji", 14),
                         relief=tk.FLAT, bd=0, padx=10, pady=5,
                         bg=bg_normal, fg=fg, activebackground=bg_hover,
                         activeforeground=fg, cursor="hand2")
        self.normal_bg = bg_normal
        self.hover_bg = bg_hover
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        ToolTip(self, tooltip)

    def on_enter(self, e):
        self.configure(bg=self.hover_bg)

    def on_leave(self, e):
        self.configure(bg=self.normal_bg)

class WebMasterIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("WebMaster IDE Pro v5.0 - Nowoczesny i intuicyjny")
        self.root.geometry("1300x900")

        # --- USTAWIENIA DOMYŚLNE ---
        self.editor_font_family = "Arial"
        self.editor_font_size = 12
        self.file_path = None

        self.themes = {
            "Ciemny":      ("#2c3e50", "#ffffff", "#1e1e1e", "#d4d4d4"),
            "Jasny":       ("#dcdde1", "#2f3640", "#ffffff", "#2f3640"),
            "Miętowy":     ("#26de81", "#ffffff", "#f1f2f6", "#2d3436"),
            "Lawendowy":   ("#a55eea", "#ffffff", "#f5f0ff", "#4b2c20"),
            "Błękitny":    ("#45aaf2", "#ffffff", "#ebf7ff", "#002b36"),
            "Pomarańczowy":("#fa8231", "#ffffff", "#fff5eb", "#4b2c20"),
            "Szary":       ("#778ca3", "#ffffff", "#f1f2f6", "#2f3640"),
            "Złoty":       ("#f39c12", "#2c3e50", "#fef9e7", "#2c3e50")
        }

        self.current_theme = "Ciemny"
        colors = self.themes[self.current_theme]
        self.tool_bg, self.tool_fg, self.editor_bg, self.editor_fg = colors

        self.containers = ["div", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6", "a", "ul", "li", "section"]
        self.all_keywords = sorted(self.containers + ["br", "hr", "img"])

        self.setup_ui()
        self.setup_tags()
        self.setup_shortcuts()
        self.load_template()

    # ----------------------------------------------------------------------
    # UI - jeden pasek, same ikony
    # ----------------------------------------------------------------------
    def setup_ui(self):
        self.toolbar = tk.Frame(self.root, bg=self.tool_bg, pady=5)
        self.toolbar.pack(side="top", fill="x")

        self.btn_open = IconButton(self.toolbar, "📂", self.open_file, "Otwórz plik (Ctrl+O)",
                                   self.tool_bg, "#27ae60")
        self.btn_open.pack(side="left", padx=2)

        self.btn_save = IconButton(self.toolbar, "💾", self.save_file, "Zapisz plik (Ctrl+S)",
                                   self.tool_bg, "#27ae60")
        self.btn_save.pack(side="left", padx=2)

        self.btn_settings = IconButton(self.toolbar, "⚙️", self.open_settings_window, "Ustawienia",
                                       self.tool_bg, "#34495e")
        self.btn_settings.pack(side="left", padx=2)

        tk.Frame(self.toolbar, width=2, bg="#95a5a6").pack(side="left", padx=5, fill="y", pady=2)

        self.btn_bold = IconButton(self.toolbar, "🅱", lambda: self.wrap_text("b"), "Pogrubienie (Ctrl+B)",
                                   self.tool_bg, "#3498db")
        self.btn_bold.pack(side="left", padx=2)

        self.btn_italic = IconButton(self.toolbar, "𝐼", lambda: self.wrap_text("i"), "Kursywa (Ctrl+I)",
                                     self.tool_bg, "#3498db")
        self.btn_italic.pack(side="left", padx=2)

        self.btn_underline = IconButton(self.toolbar, "𝑈", lambda: self.wrap_text("u"), "Podkreślenie (Ctrl+U)",
                                        self.tool_bg, "#3498db")
        self.btn_underline.pack(side="left", padx=2)

        self.btn_color = IconButton(self.toolbar, "🎨", self.insert_color_tag, "Kolor tekstu",
                                    self.tool_bg, "#9b59b6")
        self.btn_color.pack(side="left", padx=2)

        tk.Frame(self.toolbar, width=2, bg="#95a5a6").pack(side="left", padx=5, fill="y", pady=2)

        self.btn_link = IconButton(self.toolbar, "🔗", self.insert_link, "Wstaw link",
                                   self.tool_bg, "#e67e22")
        self.btn_link.pack(side="left", padx=2)

        self.btn_image = IconButton(self.toolbar, "🖼️", self.insert_image, "Wstaw obraz",
                                    self.tool_bg, "#e67e22")
        self.btn_image.pack(side="left", padx=2)

        tk.Frame(self.toolbar, width=2, bg="#95a5a6").pack(side="left", padx=5, fill="y", pady=2)

        self.btn_header = IconButton(self.toolbar, "H", self.show_header_menu, "Nagłówek H1-H6",
                                     self.tool_bg, "#16a085")
        self.btn_header.pack(side="left", padx=2)

        self.btn_fontsize = IconButton(self.toolbar, "A+", self.insert_font_size_dialog, "Rozmiar czcionki",
                                       self.tool_bg, "#2980b9")
        self.btn_fontsize.pack(side="left", padx=2)

        self.btn_center = IconButton(self.toolbar, "⏺️", lambda: self.wrap_text("p", ' style="text-align: center;"'),
                                     "Wyśrodkuj tekst", self.tool_bg, "#1abc9c")
        self.btn_center.pack(side="left", padx=2)

        self.btn_right = IconButton(self.toolbar, "➡️", lambda: self.wrap_text("p", ' style="text-align: right;"'),
                                    "Wyrównaj do prawej", self.tool_bg, "#1abc9c")
        self.btn_right.pack(side="left", padx=2)

        tk.Frame(self.toolbar, width=2, bg="#95a5a6").pack(side="left", padx=5, fill="y", pady=2)

        self.btn_preview = IconButton(self.toolbar, "▶️", self.show_preview, "Podgląd w przeglądarce (Ctrl+P)",
                                      self.tool_bg, "#e67e22")
        self.btn_preview.configure(bg="#e67e22", activebackground="#d35400")
        self.btn_preview.normal_bg = "#e67e22"
        self.btn_preview.pack(side="left", padx=2)

        self.text_area = tk.Text(self.root, undo=True, wrap="none",
                                 font=(self.editor_font_family, self.editor_font_size),
                                 bg=self.editor_bg, fg=self.editor_fg,
                                 insertbackground=self.editor_fg, padx=15, pady=15)
        self.text_area.pack(expand=True, fill="both")
        self.text_area.bind("<KeyRelease>", self.on_key_event)

    def show_header_menu(self):
        menu = tk.Menu(self.root, tearoff=0)
        for i in range(1, 7):
            menu.add_command(label=f"H{i}", command=lambda h=i: self.wrap_text(f"h{h}"))
        x = self.btn_header.winfo_rootx()
        y = self.btn_header.winfo_rooty() + self.btn_header.winfo_height()
        menu.post(x, y)

    # ----------------------------------------------------------------------
    # OKNO USTAWIEN Z LISTĄ ROZMIARÓW CZCIONKI (8,10,11,12,...36)
    # ----------------------------------------------------------------------
    def open_settings_window(self):
        win = tk.Toplevel(self.root)
        win.title("Ustawienia IDE")
        win.geometry("380x550")
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="🎨 MOTYW (SKÓRKA):", font=("Arial", 10, "bold")).pack(pady=8)
        th_c = ttk.Combobox(win, values=list(self.themes.keys()), state="readonly", width=20)
        th_c.set(self.current_theme)
        th_c.pack()

        tk.Label(win, text="✍️ CZCIONKA KODU:", font=("Arial", 10, "bold")).pack(pady=8)
        f_c = ttk.Combobox(win, values=sorted(list(font.families())), width=25)
        f_c.set(self.editor_font_family)
        f_c.pack()

        tk.Label(win, text="🔢 ROZMIAR CZCIONKI:", font=("Arial", 10, "bold")).pack(pady=8)
        # Lista rozmiarów według żądania
        size_values = ["8", "10", "11", "12", "14", "16", "18", "20", "22", "24", "26", "28", "30", "32", "34", "36"]
        size_combo = ttk.Combobox(win, values=size_values, state="readonly", width=10)
        size_combo.set(str(self.editor_font_size))
        size_combo.pack()

        tk.Frame(win, height=2, bd=1, relief="sunken").pack(fill="x", pady=10, padx=20)

        tk.Label(win, text="🎨 DODATKOWE KOLORY (opcjonalnie):", font=("Arial", 9, "bold")).pack(pady=5)
        
        def set_custom_bg():
            res = colorchooser.askcolor(title="Wybierz tło edytora")[1]
            if res:
                self.editor_bg = res

        def set_custom_fg():
            res = colorchooser.askcolor(title="Wybierz kolor tekstu")[1]
            if res:
                self.editor_fg = res

        tk.Button(win, text="🖌️ TŁO EDYTORA", command=set_custom_bg, width=25, bg="#95a5a6", fg="white").pack(pady=3)
        tk.Button(win, text="✒️ KOLOR FONTU", command=set_custom_fg, width=25, bg="#95a5a6", fg="white").pack(pady=3)

        def save_settings():
            self.editor_font_family = f_c.get()
            try:
                self.editor_font_size = int(size_combo.get())
            except:
                pass
            new_theme = th_c.get()
            if new_theme != self.current_theme:
                self.current_theme = new_theme
                colors = self.themes[self.current_theme]
                self.tool_bg, self.tool_fg, self.editor_bg, self.editor_fg = colors
            self.apply_visuals()
            win.destroy()

        btn_save = tk.Button(win, text="✅ ZASTOSUJ I ZAMKNIJ", command=save_settings,
                             bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
                             height=2, width=25)
        btn_save.pack(pady=20)

    def apply_visuals(self):
        self.toolbar.configure(bg=self.tool_bg)
        for child in self.toolbar.winfo_children():
            if isinstance(child, IconButton):
                if child == self.btn_preview:
                    child.configure(bg="#e67e22", activebackground="#d35400")
                    child.normal_bg = "#e67e22"
                else:
                    child.configure(bg=self.tool_bg)
                    child.normal_bg = self.tool_bg
        self.text_area.configure(font=(self.editor_font_family, self.editor_font_size),
                                 bg=self.editor_bg, fg=self.editor_fg,
                                 insertbackground=self.editor_fg)
        self.colorize()

    # ----------------------------------------------------------------------
    # WSTAWIANIE LINKA – pytamy o tekst i URL
    # ----------------------------------------------------------------------
    def insert_link(self):
        try:
            sel_start = self.text_area.index("sel.first")
            sel_end = self.text_area.index("sel.last")
            selected_text = self.text_area.get(sel_start, sel_end)
        except:
            selected_text = ""

        dialog = tk.Toplevel(self.root)
        dialog.title("Wstaw link")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.grab_set()

        tk.Label(dialog, text="Tekst linku:", font=("Arial", 10)).pack(pady=5)
        text_entry = tk.Entry(dialog, width=50, font=("Arial", 10))
        text_entry.pack(pady=5)
        if selected_text:
            text_entry.insert(0, selected_text)

        tk.Label(dialog, text="Adres URL:", font=("Arial", 10)).pack(pady=5)
        url_entry = tk.Entry(dialog, width=50, font=("Arial", 10))
        url_entry.insert(0, "https://")
        url_entry.pack(pady=5)

        def insert():
            link_text = text_entry.get().strip()
            url = url_entry.get().strip()
            if not link_text:
                messagebox.showerror("Błąd", "Tekst linku nie może być pusty!")
                return
            if not url:
                messagebox.showerror("Błąd", "Adres URL nie może być pusty!")
                return
            try:
                if selected_text:
                    self.text_area.delete(sel_start, sel_end)
                    self.text_area.insert(sel_start, f'<a href="{url}">{link_text}</a>')
                else:
                    self.text_area.insert(tk.INSERT, f'<a href="{url}">{link_text}</a>')
                self.colorize()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się wstawić linku: {e}")

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="Wstaw", command=insert, bg="#27ae60", fg="white", padx=20).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Anuluj", command=dialog.destroy, bg="#e74c3c", fg="white", padx=20).pack(side="left")

    # ----------------------------------------------------------------------
    # POZOSTAŁE FUNKCJE (formatowanie, obrazki itp.)
    # ----------------------------------------------------------------------
    def setup_shortcuts(self):
        self.root.bind_all("<Control-o>", lambda e: self.open_file())
        self.root.bind_all("<Control-s>", lambda e: self.save_file())
        self.root.bind_all("<Control-p>", lambda e: self.show_preview())
        self.root.bind_all("<Control-b>", lambda e: self.wrap_text("b"))
        self.root.bind_all("<Control-i>", lambda e: self.wrap_text("i"))
        self.root.bind_all("<Control-u>", lambda e: self.wrap_text("u"))

    def insert_font_size_dialog(self):
        size = simpledialog.askstring("Wielkość tekstu", "Podaj rozmiar (np. 24px, 200%, 3em):")
        if size:
            self.wrap_text("span", f' style="font-size: {size};"')

    def wrap_text(self, tag, extra=""):
        try:
            s, e = self.text_area.index("sel.first"), self.text_area.index("sel.last")
            txt = self.text_area.get(s, e)
            self.text_area.replace(s, e, f"<{tag}{extra}>{txt}</{tag}>")
        except:
            self.text_area.insert(tk.INSERT, f"<{tag}{extra}></{tag}>")
            if not extra:
                self.text_area.mark_set(tk.INSERT, f"{tk.INSERT} - {len(tag)+3}c")
        self.colorize()

    def insert_color_tag(self):
        c = colorchooser.askcolor(title="Kolor zaznaczonego tekstu")[1]
        if c:
            self.wrap_text("span", f' style="color: {c};"')

    def insert_image(self):
        p = filedialog.askopenfilename()
        if p:
            self.text_area.insert(tk.INSERT, f'<img src="file:///{p}" alt="img" style="max-width:100%;">')
            self.colorize()

    def setup_tags(self):
        self.text_area.tag_configure("tag", foreground="#569cd6")
        self.text_area.tag_configure("attr", foreground="#9cdcfe")
        self.text_area.tag_configure("string", foreground="#ce9178")
        self.text_area.tag_configure("bracket", foreground="#808080")

    def on_key_event(self, event):
        self.colorize()
        if event.char == "<":
            self.show_autocomplete()

    def colorize(self):
        content = self.text_area.get("1.0", "end-1c")
        for t in ["tag", "attr", "string", "bracket"]:
            self.text_area.tag_remove(t, "1.0", "end")
        for m in re.finditer(r'[<>]', content):
            self.text_area.tag_add("bracket", f"1.0 + {m.start()}c", f"1.0 + {m.end()}c")
        for m in re.finditer(r'(?<=<)/?[a-zA-Z1-6]+', content):
            self.text_area.tag_add("tag", f"1.0 + {m.start()}c", f"1.0 + {m.end()}c")
        for m in re.finditer(r'\s[a-zA-Z\-]+(?==)', content):
            self.text_area.tag_add("attr", f"1.0 + {m.start()}c", f"1.0 + {m.end()}c")
        for m in re.finditer(r'"[^"]*"', content):
            self.text_area.tag_add("string", f"1.0 + {m.start()}c", f"1.0 + {m.end()}c")

    def show_autocomplete(self):
        menu = tk.Menu(self.root, tearoff=0)
        for tag in self.all_keywords:
            menu.add_command(label=f"<{tag}>", command=lambda t=tag: self.insert_smart_tag(t))
        try:
            x, y, _, _ = self.text_area.bbox(tk.INSERT)
            menu.post(self.text_area.winfo_rootx() + x, self.text_area.winfo_rooty() + y)
        except:
            pass

    def insert_smart_tag(self, tag):
        if tag in self.containers:
            self.text_area.insert(tk.INSERT, f"{tag}></{tag}>")
            self.text_area.mark_set(tk.INSERT, f"{tk.INSERT} - {len(tag) + 3}c")
        else:
            self.text_area.insert(tk.INSERT, f"{tag}>")
        self.colorize()

    def show_preview(self):
        p = os.path.abspath("preview.html")
        with open(p, "w", encoding="utf-8") as f:
            f.write(self.text_area.get("1.0", "end-1c"))
        webbrowser.open(f"file://{p}")

    def save_file(self):
        p = filedialog.asksaveasfilename(defaultextension=".html")
        if p:
            self.file_path = p
            with open(p, "w", encoding="utf-8") as f:
                f.write(self.text_area.get("1.0", "end-1c"))
            messagebox.showinfo("Info", "Zapisano plik!")

    def open_file(self):
        p = filedialog.askopenfilename(filetypes=[("HTML", "*.html"), ("Wszystkie", "*.*")])
        if p:
            self.text_area.delete("1.0", "end")
            with open(p, "r", encoding="utf-8") as f:
                self.text_area.insert("1.0", f.read())
            self.colorize()
            self.file_path = p

    def load_template(self):
        self.text_area.insert("1.0", "<!DOCTYPE html>\n<html>\n<head>\n<meta charset='UTF-8'>\n<title>Nowa strona</title>\n</head>\n<body>\n\n</body>\n</html>")
        self.colorize()

if __name__ == "__main__":
    root = tk.Tk()
    app = WebMasterIDE(root)
    root.mainloop()