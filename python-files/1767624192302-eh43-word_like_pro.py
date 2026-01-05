import tkinter as tk
from tkinter import ttk, font, colorchooser, filedialog
from tkinter import Menu

class WordLikeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("محرر نصوص متقدم - يشبه Microsoft Word")
        self.root.geometry("1200x800")

        # متغيرات التنسيق الحالية
        self.current_font = "Arial"
        self.current_size = 12
        self.current_bold = False
        self.current_italic = False
        self.current_underline = False

        # إنشاء الـ Notebook للتبويبات (Ribbon Style)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(side="top", fill="x")

        # تبويب Home
        self.home_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.home_tab, text="الرئيسية (Home)")

        # تبويب Insert
        self.insert_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.insert_tab, text="إدراج (Insert)")

        # تبويب View
        self.view_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.view_tab, text="عرض (View)")

        # شريط أدوات Home
        self.create_home_toolbar()

        # شريط أدوات Insert (بسيط)
        self.create_insert_toolbar()

        # منطقة الكتابة
        self.text_area = tk.Text(self.root, font=(self.current_font, self.current_size), undo=True, wrap="word")
        self.text_area.pack(expand=True, fill="both", padx=10, pady=10)

        # قائمة الملف العلوية
        self.create_menu()

        # حالة الملف
        self.current_file = None

    def create_menu(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ملف", menu=file_menu)
        file_menu.add_command(label="جديد", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="فتح...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="حفظ", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="حفظ باسم...", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="خروج", command=self.root.quit)

        # اختصارات كيبورد
        self.root.bind_all("<Control-n>", lambda e: self.new_file())
        self.root.bind_all("<Control-o>", lambda e: self.open_file())
        self.root.bind_all("<Control-s>", lambda e: self.save_file())

    def create_home_toolbar(self):
        toolbar = ttk.Frame(self.home_tab)
        toolbar.pack(fill="x", padx=5, pady=5)

        # قائمة الخطوط
        fonts = list(font.families())
        self.font_combo = ttk.Combobox(toolbar, values=fonts, width=25, state="readonly")
        self.font_combo.set("Arial")
        self.font_combo.grid(row=0, column=0, padx=5)
        self.font_combo.bind("<<ComboboxSelected>>", self.change_font)

        # قائمة الحجم
        sizes = [8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 72]
        self.size_combo = ttk.Combobox(toolbar, values=sizes, width=10, state="readonly")
        self.size_combo.set(12)
        self.size_combo.grid(row=0, column=1, padx=5)
        self.size_combo.bind("<<ComboboxSelected>>", self.change_size)

        # أزرار التنسيق
        self.bold_btn = ttk.Button(toolbar, text="جريء (B)", command=self.toggle_bold)
        self.bold_btn.grid(row=0, column=2, padx=5)

        self.italic_btn = ttk.Button(toolbar, text="مائل (I)", command=self.toggle_italic)
        self.italic_btn.grid(row=0, column=3, padx=5)

        self.underline_btn = ttk.Button(toolbar, text="تحت خط (U)", command=self.toggle_underline)
        self.underline_btn.grid(row=0, column=4, padx=5)

        self.color_btn = ttk.Button(toolbar, text="لون النص", command=self.change_text_color)
        self.color_btn.grid(row=0, column=5, padx=5)

        self.highlight_btn = ttk.Button(toolbar, text="لون الخلفية", command=self.change_highlight)
        self.highlight_btn.grid(row=0, column=6, padx=5)

    def create_insert_toolbar(self):
        toolbar = ttk.Frame(self.insert_tab)
        toolbar.pack(fill="x", padx=5, pady=5)

        label = ttk.Label(toolbar, text="تبويب إدراج: هنا ممكن تضيف صور أو جداول في نسخ متقدمة")
        label.pack(side="left", padx=10)

    def change_font(self, event=None):
        self.current_font = self.font_combo.get()
        self.apply_style()

    def change_size(self, event=None):
        self.current_size = int(self.size_combo.get())
        self.apply_style()

    def toggle_bold(self):
        self.current_bold = not self.current_bold
        self.apply_style()

    def toggle_italic(self):
        self.current_italic = not self.current_italic
        self.apply_style()

    def toggle_underline(self):
        self.current_underline = not self.current_underline
        self.apply_style()

    def apply_style(self):
        try:
            current_tags = self.text_area.tag_names("sel.first")
        except:
            current_tags = []

        # إزالة التنسيق القديم
        self.text_area.tag_remove("bold", "1.0", "end")
        self.text_area.tag_remove("italic", "1.0", "end")
        self.text_area.tag_remove("underline", "1.0", "end")
        self.text_area.tag_remove("font_size", "1.0", "end")
        self.text_area.tag_remove("font_family", "1.0", "end")

        # تطبيق التنسيق على النص المحدد أو عند المؤشر
        start = "sel.first" if "sel" in current_tags else "insert"
        end = "sel.last" if "sel" in current_tags else "insert"

        weight = "bold" if self.current_bold else "normal"
        slant = "italic" if self.current_italic else "roman"
        underline = 1 if self.current_underline else 0

        new_font = font.Font(family=self.current_font, size=self.current_size, weight=weight, slant=slant, underline=underline)
        self.text_area.tag_config("styled", font=new_font)
        self.text_area.tag_add("styled", start, end)

    def change_text_color(self):
        color = colorchooser.askcolor(title="اختر لون النص")[1]
        if color:
            self.text_area.tag_config("textcolor", foreground=color)
            if self.text_area.tag_ranges("sel"):
                self.text_area.tag_add("textcolor", "sel.first", "sel.last")
            else:
                self.text_area.tag_add("textcolor", "insert", "insert+1c")

    def change_highlight(self):
        color = colorchooser.askcolor(title="اختر لون الخلفية")[1]
        if color:
            self.text_area.tag_config("highlight", background=color)
            if self.text_area.tag_ranges("sel"):
                self.text_area.tag_add("highlight", "sel.first", "sel.last")
            else:
                self.text_area.tag_add("highlight", "insert", "insert+1c")

    def new_file(self):
        self.text_area.delete(1.0, tk.END)
        self.current_file = None
        self.root.title("محرر نصوص متقدم - يشبه Microsoft Word")

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(1.0, f.read())
            self.current_file = file_path
            self.root.title(f"{file_path} - محرر نصوص متقدم")

    def save_file(self):
        if self.current_file:
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(self.text_area.get(1.0, tk.END))
        else:
            self.save_as_file()

    def save_as_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.text_area.get(1.0, tk.END))
            self.current_file = file_path
            self.root.title(f"{file_path} - محرر نصوص متقدم")

if __name__ == "__main__":
    root = tk.Tk()
    app = WordLikeApp(root)
    root.mainloop()