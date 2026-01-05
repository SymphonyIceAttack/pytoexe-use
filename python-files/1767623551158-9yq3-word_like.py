import tkinter as tk
from tkinter import ttk, font, colorchooser, filedialog, messagebox

class SimpleWordProcessor:
    def __init__(self, root):
        self.root = root
        self.root.title("محرر نصوص بسيط - يشبه Microsoft Word")
        self.root.geometry("1000x600")

        # إعداد الخطوط الافتراضية
        self.current_font_family = "Arial"
        self.current_font_size = 12

        # إنشاء شريط الأدوات
        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(side="top", fill="x")

        # قائمة الخطوط
        font_families = font.families()
        self.font_box = ttk.Combobox(self.toolbar, values=font_families, width=20)
        self.font_box.current(font_families.index("Arial"))
        self.font_box.grid(row=0, column=0, padx=5, pady=5)
        self.font_box.bind("<<ComboboxSelected>>", self.change_font)

        # قائمة حجم الخط
        sizes = list(range(8, 73, 4))
        self.size_box = ttk.Combobox(self.toolbar, values=sizes, width=10)
        self.size_box.current(sizes.index(12))
        self.size_box.grid(row=0, column=1, padx=5, pady=5)
        self.size_box.bind("<<ComboboxSelected>>", self.change_size)

        # أزرار التنسيق
        self.bold_btn = ttk.Button(self.toolbar, text="جريء", command=self.toggle_bold)
        self.bold_btn.grid(row=0, column=2, padx=5)

        self.italic_btn = ttk.Button(self.toolbar, text="مائل", command=self.toggle_italic)
        self.italic_btn.grid(row=0, column=3, padx=5)

        self.underline_btn = ttk.Button(self.toolbar, text="تحت خط", command=self.toggle_underline)
        self.underline_btn.grid(row=0, column=4, padx=5)

        self.color_btn = ttk.Button(self.toolbar, text="لون النص", command=self.change_text_color)
        self.color_btn.grid(row=0, column=5, padx=5)

        self.bg_color_btn = ttk.Button(self.toolbar, text="لون الخلفية", command=self.change_bg_color)
        self.bg_color_btn.grid(row=0, column=6, padx=5)

        # قائمة الملفات
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ملف", menu=file_menu)
        file_menu.add_command(label="جديد", command=self.new_file)
        file_menu.add_command(label="فتح", command=self.open_file)
        file_menu.add_command(label="حفظ", command=self.save_file)
        file_menu.add_command(label="حفظ باسم", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="خروج", command=self.root.quit)

        # منطقة الكتابة
        self.text_area = tk.Text(self.root, font=(self.current_font_family, self.current_font_size))
        self.text_area.pack(expand=True, fill="both")

        # تتبع الملف الحالي
        self.current_file = None

    def change_font(self, event=None):
        self.current_font_family = self.font_box.get()
        self.apply_font()

    def change_size(self, event=None):
        self.current_font_size = int(self.size_box.get())
        self.apply_font()

    def apply_font(self):
        current_tags = self.text_area.tag_names("sel.first")
        self.text_area.tag_config("font", font=(self.current_font_family, self.current_font_size))
        if "sel" in current_tags:
            self.text_area.tag_add("font", "sel.first", "sel.last")
        else:
            self.text_area.tag_add("font", "insert")

    def toggle_bold(self):
        current_tags = self.text_area.tag_names("sel.first" if self.text_area.tag_ranges("sel") else "insert")
        if "bold" in current_tags:
            self.text_area.tag_remove("bold", "sel.first", "sel.last")
        else:
            bold_font = font.Font(self.text_area, self.text_area.cget("font"))
            bold_font.configure(weight="bold")
            self.text_area.tag_config("bold", font=bold_font)
            self.text_area.tag_add("bold", "sel.first" if self.text_area.tag_ranges("sel") else "insert",
                                  "sel.last" if self.text_area.tag_ranges("sel") else "insert+1c")

    def toggle_italic(self):
        current_tags = self.text_area.tag_names("sel.first" if self.text_area.tag_ranges("sel") else "insert")
        if "italic" in current_tags:
            self.text_area.tag_remove("italic", "sel.first", "sel.last")
        else:
            italic_font = font.Font(self.text_area, self.text_area.cget("font"))
            italic_font.configure(slant="italic")
            self.text_area.tag_config("italic", font=italic_font)
            self.text_area.tag_add("italic", "sel.first" if self.text_area.tag_ranges("sel") else "insert",
                                  "sel.last" if self.text_area.tag_ranges("sel") else "insert+1c")

    def toggle_underline(self):
        current_tags = self.text_area.tag_names("sel.first" if self.text_area.tag_ranges("sel") else "insert")
        if "underline" in current_tags:
            self.text_area.tag_remove("underline", "sel.first", "sel.last")
        else:
            self.text_area.tag_config("underline", underline=True)
            self.text_area.tag_add("underline", "sel.first" if self.text_area.tag_ranges("sel") else "insert",
                                  "sel.last" if self.text_area.tag_ranges("sel") else "insert+1c")

    def change_text_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.text_area.tag_config("colored", foreground=color)
            self.text_area.tag_add("colored", "sel.first" if self.text_area.tag_ranges("sel") else "insert",
                                  "sel.last" if self.text_area.tag_ranges("sel") else "insert+1c")

    def change_bg_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.text_area.tag_config("bg_colored", background=color)
            self.text_area.tag_add("bg_colored", "sel.first" if self.text_area.tag_ranges("sel") else "insert",
                                  "sel.last" if self.text_area.tag_ranges("sel") else "insert+1c")

    def new_file(self):
        self.text_area.delete(1.0, tk.END)
        self.current_file = None
        self.root.title("محرر نصوص بسيط - يشبه Microsoft Word")

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(1.0, f.read())
            self.current_file = file_path
            self.root.title(f"{file_path} - محرر نصوص بسيط")

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
            self.root.title(f"{file_path} - محرر نصوص بسيط")

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleWordProcessor(root)
    root.mainloop()