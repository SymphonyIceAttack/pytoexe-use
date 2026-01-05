import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from PIL import Image, ImageTk
import shutil

class PDFToolsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("أدوات PDF - يشبه SmallPDF")
        self.root.geometry("1400x800")
        self.root.configure(bg="#f8f9fa")

        # شريط القوائم العلوي
        self.create_top_menu()

        # الـ Ribbon الرئيسي (زي SmallPDF)
        self.create_ribbon()

        # منطقة السحب والإفلات
        self.create_drop_zone()

    def create_top_menu(self):
        # Header زي SmallPDF
        header = tk.Frame(self.root, bg="#2c3e50", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        # Logo
        logo_label = tk.Label(header, text="🅿️🅳🅵 TOOLS", font=("Segoe UI", 18, "bold"), 
                             bg="#2c3e50", fg="white")
        logo_label.pack(side="left", padx=20, pady=15)

        # Navigation
        nav_frame = tk.Frame(header, bg="#2c3e50")
        nav_frame.pack(side="right", padx=20, pady=15)

        nav_items = ["الرئيسية", "أدوات", "المستندات", "بحث"]
        for item in nav_items:
            btn = tk.Button(nav_frame, text=item, bg="#2c3e50", fg="white", 
                          font=("Segoe UI", 12), relief="flat", padx=20)
            btn.pack(side="right", padx=10)

    def create_ribbon(self):
        # Notebook للتبويبات
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="x", padx=20, pady=10)

        # تبويب All Tools (الرئيسي زي الصورة)
        all_tools_tab = tk.Frame(notebook, bg="white")
        notebook.add(all_tools_tab, text="جميع الأدوات")

        # إنشاء الأزرار زي SmallPDF بالضبط
        self.create_main_tools(all_tools_tab)

    def create_main_tools(self, parent):
        # التصميم grid 3x4 زي الصورة
        tools_data = [
            {"icon": "🔴", "text": "ضغط PDF", "color": "#e74c3c"},
            {"icon": "📄", "text": "PDF Converter", "color": "#3498db"},
            {"icon": "📊", "text": "PPT إلى PDF", "color": "#f39c12"},
            
            {"icon": "📄", "text": "PDF إلى PPT", "color": "#f39c12"},
            {"icon": "🖼️", "text": "JPG إلى PDF", "color": "#f1c40f"},
            {"icon": "🖼️", "text": "PDF إلى JPG", "color": "#f1c40f"},
            
            {"icon": "📊", "text": "Excel إلى PDF", "color": "#27ae60"},
            {"icon": "📊", "text": "PDF إلى Excel", "color": "#27ae60"},
            {"icon": "✏️", "text": "تعديل PDF", "color": "#2ecc71"},
            
            {"icon": "📖", "text": "PDF Reader", "color": "#9b59b6"},
            {"icon": "🔢", "text": "ترقيم الصفحات", "color": "#1abc9c"},
            {"icon": "🗑️", "text": "حذف صفحات PDF", "color": "#e67e22"},
            
            {"icon": "🔄", "text": "تدوير PDF", "color": "#00b894"},
            {"icon": "📝", "text": "Word إلى PDF", "color": "#3498db"},
            {"icon": "📝", "text": "PDF إلى Word", "color": "#3498db"},
            
            {"icon": "🔗", "text": "دمج PDF", "color": "#9b59b6"},
            {"icon": "✂️", "text": "تقسيم PDF", "color": "#e91e63"},
            {"icon": "✍️", "text": "توقيع PDF", "color": "#ff6b9d"},
            
            {"icon": "🔓", "text": "فك قفل PDF", "color": "#e17055"},
            {"icon": "🔒", "text": "حماية PDF", "color": "#d63031"},
        ]

        row, col = 0, 0
        for tool in tools_data:
            btn = tk.Button(parent, text=f"{tool['icon']}\n{tool['text']}", 
                          font=("Segoe UI", 10, "bold"), bg=tool['color'], 
                          fg="white", relief="flat", width=14, height=4,
                          command=lambda t=tool['text']: self.tool_clicked(t))
            btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            col += 1
            if col > 5:
                col = 0
                row += 1

        # جعل الـ grid يتمدد
        for i in range(4):
            parent.grid_rowconfigure(i, weight=1)
        for i in range(6):
            parent.grid_columnconfigure(i, weight=1)

    def create_drop_zone(self):
        drop_frame = tk.Frame(self.root, bg="#ecf0f1", height=300, relief="dashed", bd=2)
        drop_frame.pack(fill="both", expand=True, padx=20, pady=20)
        drop_frame.pack_propagate(False)

        drop_label = tk.Label(drop_frame, text="📁\nاسحب ملفات PDF هنا أو\nاضغط لاختيار ملف", 
                            font=("Segoe UI", 24), bg="#ecf0f1", fg="#7f8c8d")
        drop_label.pack(expand=True)

        drop_label.bind("<Button-1>", self.select_files)

    def tool_clicked(self, tool_name):
        messagebox.showinfo("تم", f"تم الضغط على: {tool_name}\n(الميزة قيد التطوير)")
        print(f"Tool clicked: {tool_name}")

    def select_files(self, event=None):
        files = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")])
        if files:
            messagebox.showinfo("تم", f"تم اختيار {len(files)} ملف")

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFToolsApp(root)
    root.mainloop()