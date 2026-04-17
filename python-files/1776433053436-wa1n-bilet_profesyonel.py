
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import fitz
from docx import Document

def temizle_islem(dosya_yolu, silinecekler):
    try:
        cikti_yolu = "temizlenmis_" + os.path.basename(dosya_yolu)
        if not cikti_yolu.endswith('.pdf'):
            cikti_yolu = cikti_yolu.rsplit('.', 1)[0] + '.pdf'

        if dosya_yolu.endswith('.pdf'):
            doc = fitz.open(dosya_yolu)
            for page in doc:
                for kelime in silinecekler:
                    text_instances = page.search_for(kelime)
                    for inst in text_instances:
                        page.add_redact_annot(inst, fill=(1, 1, 1))
                page.apply_redactions()
            doc.save(cikti_yolu)
            doc.close()
        return cikti_yolu
    except Exception as e:
        return str(e)

def baslat_gui():
    root = tk.Tk()
    root.title("Bilet Temizleyici v1.0")
    root.geometry("400x300")
    tk.Label(root, text="Dosya Secin", pady=20).pack()
    def dosya_sec():
        yol = filedialog.askopenfilename(filetypes=[("Belgeler", "*.pdf *.docx")])
        if yol:
            liste = ["1500 TL", "Isim Soyisim"]
            sonuc = temizle_islem(yol, liste)
            messagebox.showinfo("Basarili", f"Dosya Hazir: {sonuc}")
    tk.Button(root, text="Dosya Sec ve Temizle", command=dosya_sec, bg="green", fg="white").pack()
    root.mainloop()

if __name__ == '__main__':
    baslat_gui()
