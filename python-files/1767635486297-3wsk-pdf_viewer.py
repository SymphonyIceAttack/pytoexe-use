import tkinter as tk
from tkinter import filedialog
import fitz  # PyMuPDF
from PIL import Image, ImageTk

class PDFViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("برنامج PDF")
        self.root.geometry("800x600")

        self.doc = None
        self.page_number = 0
        self.zoom = 1.0

        toolbar = tk.Frame(root)
        toolbar.pack(fill="x")

        tk.Button(toolbar, text="فتح ملف PDF", command=self.open_pdf).pack(side="left")
        tk.Button(toolbar, text="◀ السابق", command=self.prev_page).pack(side="left")
        tk.Button(toolbar, text="التالي ▶", command=self.next_page).pack(side="left")
        tk.Button(toolbar, text="تكبير +", command=self.zoom_in).pack(side="left")
        tk.Button(toolbar, text="تصغير -", command=self.zoom_out).pack(side="left")

        self.canvas = tk.Canvas(root, bg="gray")
        self.canvas.pack(fill="both", expand=True)

    def open_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not path:
            return
        self.doc = fitz.open(path)
        self.page_number = 0
        self.zoom = 1.0
        self.show_page()

    def show_page(self):
        if not self.doc:
            return

        page = self.doc.load_page(self.page_number)
        mat = fitz.Matrix(self.zoom, self.zoom)
        pix = page.get_pixmap(matrix=mat)

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.img_tk = ImageTk.PhotoImage(img)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.img_tk)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        self.root.title(f"PDF - صفحة {self.page_number + 1} / {self.doc.page_count}")

    def next_page(self):
        if self.doc and self.page_number < self.doc.page_count - 1:
            self.page_number += 1
            self.show_page()

    def prev_page(self):
        if self.doc and self.page_number > 0:
            self.page_number -= 1
            self.show_page()

    def zoom_in(self):
        if self.doc:
            self.zoom += 0.2
            self.show_page()

    def zoom_out(self):
        if self.doc and self.zoom > 0.4:
            self.zoom -= 0.2
            self.show_page()

root = tk.Tk()
PDFViewer(root)
root.mainloop()
