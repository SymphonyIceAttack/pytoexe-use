import tkinter as tk
from tkinter import ttk, font, colorchooser, filedialog, messagebox

class SimpleWordProcessor:
    def __init__(self, root):
        self.root = root
        self.root.title("محرر نصوص بسيط - يشبه Microsoft Word")
        self.root.geometry("1000x600")

        self.current_font_family = "Arial"
        self.current_font_size = 12

        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(side="top", fill="x")

        font_families = font.families()
        self.font_box = ttk.Combobox(self.toolbar, values=font_families, width=20)
        self.font_box.current(font_families.index("Arial"))
        self.font_box.grid(row=0, column=0, padx=5, pady=5)
        self.font_box.bind("<<ComboboxSelected>>", self.change_font)

        sizes = list(range(8, 73, 4))
        self.size_box = ttk.Combobox(self.toolbar, values=sizes, width=10)
        self.size_box.current(sizes.index(12))
        self.size_box.grid(row=0, column=1, padx=5, pady=5)
        self.size_box.bind("<<ComboboxSelected>>", self.change_size)

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

        self.text_area = tk.Text(self.root, font=(self.current_font_family, self.current_font_size))
        self.text_area.pack(expand=True, fill="both")

        self.current_file = None

    # باقي الدوال زي ما هي (change_font, toggle_bold, إلخ)... 
    # (انسخ الكود كامل من الرسايل السابقة عشان ما يطولش هنا)

    if __name__ == "__main__":
        root = tk.Tk()
        app = SimpleWordProcessor(root)
        root.mainloop()