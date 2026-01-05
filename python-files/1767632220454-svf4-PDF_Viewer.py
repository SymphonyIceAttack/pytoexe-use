import tkinter as tk
from tkinter import filedialog, ttk
import fitz  # من PyMuPDF
from fpdf import FPDF
import os

class PDFViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("عارض PDF رائع الشكل 🌟")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")

        # عنوان البرنامج
        title_label = tk.Label(root, text="عارض PDF احترافي", font=("Cairo", 24, "bold"), bg="#f0f0f0", fg="#2c3e50")
        title_label.pack(pady=10)

        # أزرار
        button_frame = tk.Frame(root, bg="#f0f0f0")
        button_frame.pack(pady=10)

        open_btn = tk.Button(button_frame, text="افتح ملف PDF", command=self.open_pdf, font=("Arial", 14), bg="#3498db", fg="white", padx=20, pady=10)
        open_btn.grid(row=0, column=0, padx=20)

        create_btn = tk.Button(button_frame, text="أنشئ PDF تجريبي جميل", command=self.create_sample_pdf, font=("Arial", 14), bg="#27ae60", fg="white", padx=20, pady=10)
        create_btn.grid(row=0, column=1, padx=20)

        # شريط الصفحات والزوم
        control_frame = tk.Frame(root, bg="#f0f0f0")
        control_frame.pack(pady=10)

        tk.Label(control_frame, text="الصفحة:", font=("Arial", 12), bg="#f0f0f0").pack(side="left", padx=10)
        self.page_entry = tk.Entry(control_frame, width=5, font=("Arial", 12))
        self.page_entry.pack(side="left")
        tk.Label(control_frame, text="/", font=("Arial", 12), bg="#f0f0f0").pack(side="left")
        self.total_pages_label = tk.Label(control_frame, text="0", font=("Arial", 12), bg="#f0f0f0")
        self.total_pages_label.pack(side="left", padx=5)

        go_btn = tk.Button(control_frame, text="انتقل", command=self.go_to_page, bg="#e74c3c", fg="white")
        go_btn.pack(side="left", padx=10)

        tk.Label(control_frame, text="زوم:", font=("Arial", 12), bg="#f0f0f0").pack(side="left", padx=20)
        self.zoom_var = tk.DoubleVar(value=1.0)
        zoom_scale = tk.Scale(control_frame, from_=0.5, to=3.0, resolution=0.1, orient="horizontal", variable=self.zoom_var, command=self.update_zoom, length=200)
        zoom_scale.pack(side="left")

        # منطقة عرض الـ PDF
        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(fill="both", expand=True, padx=20, pady=10)

        self.pdf_doc = None
        self.current_page = 0
        self.zoom = 1.0
        self.img = None

    def open_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            self.load_pdf(file_path)

    def create_sample_pdf(self):
        # إنشاء PDF تجريبي جميل
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 30)
        pdf.set_text_color(0, 102, 204)
        pdf.cell(0, 50, "ملف PDF رائع!", ln=True, align='C')

        pdf.set_font("Arial", size=20)
        pdf.set_text_color(0, 153, 0)
        pdf.cell(0, 30, "تم إنشاؤه داخل البرنامج!", ln=True, align='C')

        pdf.ln(20)
        pdf.set_font("Arial", size=16)
        pdf.set_text_color(102, 0, 102)
        pdf.multi_cell(0, 10, "هذا برنامج عارض PDF احترافي بـ Python\nشكله حلو وسهل الاستخدام 🌟\nجرب افتح أي PDF أو أنشئ واحد جديد!")

        filename = "PDF_تجريبي_رائع.pdf"
        pdf.output(filename)
        self.load_pdf(filename)
        tk.messagebox.showinfo("تم!", f"تم إنشاء الملف: {filename}\nوتم فتحه تلقائيًا!")

    def load_pdf(self, file_path):
        self.pdf_doc = fitz.open(file_path)
        self.current_page = 0
        self.total_pages_label.config(text=str(len(self.pdf_doc)))
        self.page_entry.delete(0, tk.END)
        self.page_entry.insert(0, "1")
        self.show_page()

    def show_page(self):
        if not self.pdf_doc:
            return
        page = self.pdf_doc[self.current_page]
        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom, self.zoom))
        img = fitz.Pixmap(pix, 0) if pix.alpha else pix
        img_data = img.tobytes("ppm")
        from PIL import Image, ImageTk
        image = Image.open(io.BytesIO(img_data))
        self.img = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.img)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def go_to_page(self):
        try:
            page_num = int(self.page_entry.get()) - 1
            if 0 <= page_num < len(self.pdf_doc):
                self.current_page = page_num
                self.show_page()
        except:
            pass

    def update_zoom(self, val):
        self.zoom = float(val)
        self.show_page()

import io
from tkinter import messagebox

root = tk.Tk()
app = PDFViewer(root)
root.mainloop()