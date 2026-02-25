import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import xml.etree.ElementTree as ET

class HelksaMindMap:
    def __init__(self, root):
        self.root = root
        self.root.title("هلکسا مایند مپ")
        self.root.geometry("700x500")
        self.root.resizable(True, True)

        # استایل و رنگ‌بندی سطوح
        style = ttk.Style()
        style.theme_use("clam")

        # درخت نمایش (فقط یک ستون برای عنوان)
        self.tree = ttk.Treeview(self.root, columns=(), selectmode="browse")
        self.tree.heading("#0", text="عنوان")
        self.tree.column("#0", width=650, minwidth=200)

        # اسکرول‌بار عمودی
        v_scroll = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # دکمه انتخاب فایل
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=5)

        self.select_btn = ttk.Button(
            btn_frame,
            text="انتخاب مایند‌مپ",
            command=self.load_file
        )
        self.select_btn.pack()

        # تعریف تگ‌های رنگی برای سطوح مختلف
        self.tree.tag_configure(
            "level0",
            background="#e3f0ff",
            foreground="#0b2d4b",
            font=('TkDefaultFont', 10, 'bold')
        )
        self.tree.tag_configure(
            "level1",
            background="#e5f7e5",
            foreground="#1c531c",
            font=('TkDefaultFont', 10)
        )
        self.tree.tag_configure(
            "level2",
            background="#fff0dc",
            foreground="#b45b0a",
            font=('TkDefaultFont', 10)
        )
        self.tree.tag_configure(
            "level3",
            background="#f3e5ff",
            foreground="#6a1b9a",
            font=('TkDefaultFont', 10)
        )
        self.tree.tag_configure(
            "level4",
            background="#d9f2f2",
            foreground="#0f6f6f",
            font=('TkDefaultFont', 10)
        )
        # سطوح بالاتر (≥5) با رنگ خاکستری یکسان
        self.tree.tag_configure(
            "level5",
            background="#f0f2f5",
            foreground="#4b5563",
            font=('TkDefaultFont', 10)
        )

        # کلیک روی هر آیتم باعث باز/بسته شدن زیرمجموعه‌های مستقیم آن می‌شود
        self.tree.bind("<ButtonRelease-1>", self.on_item_click)

    def load_file(self):
        """انتخاب فایل OPML و نمایش آن به صورت درخت"""
        file_path = filedialog.askopenfilename(
            title="انتخاب فایل مایندمپ (OPML)",
            filetypes=[("OPML files", "*.opml"), ("XML files", "*.xml"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            tree_xml = ET.parse(file_path)
            root_elem = tree_xml.getroot()

            # پیدا کردن تگ body
            body = root_elem.find('body')
            if body is None:
                messagebox.showerror("خطا", "ساختار OPML معتبر نیست: تگ <body> یافت نشد.")
                return

            # پاک کردن درخت قبلی
            for item in self.tree.get_children():
                self.tree.delete(item)

            # افزودن outline‌های سطح اول (زیر body)
            for outline in body.findall('outline'):
                self.add_outline(outline, parent_iid="", level=0)

        except Exception as e:
            messagebox.showerror("خطا", f"خطا در خواندن فایل:\n{e}")

    def add_outline(self, outline_elem, parent_iid, level):
        """افزودن یک گره outline و فرزندان آن به درخت"""
        # دریافت متن از attribute‌های 'text' یا 'title'
        text = outline_elem.get('text') or outline_elem.get('title') or 'بدون عنوان'

        # تعیین تگ بر اساس سطح (سطوح بیشتر از 4 به تگ level5 می‌روند)
        tag = f"level{min(level, 5)}"

        # درج آیتم در درخت
        iid = self.tree.insert(parent_iid, 'end', text=text, tags=(tag,))

        # پردازش فرزندان (outline‌های تو در تو)
        for child in outline_elem.findall('outline'):
            self.add_outline(child, parent_iid=iid, level=level + 1)

    def on_item_click(self, event):
        """باز/بسته کردن آیتم کلیک شده (اگر فرزند داشته باشد)"""
        item = self.tree.focus()
        if item:
            # تغییر وضعیت باز بودن آیتم
            current_state = self.tree.item(item, 'open')
            self.tree.item(item, open=not current_state)

if __name__ == "__main__":
    root = tk.Tk()
    app = HelksaMindMap(root)
    root.mainloop()