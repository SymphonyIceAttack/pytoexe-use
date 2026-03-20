import tkinter as tk
from tkinter import messagebox

class CariHesapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cari Hesap Takip")

        self.bakiye = 0

        tk.Label(root, text="Açıklama").grid(row=0, column=0)
        tk.Label(root, text="Tutar").grid(row=1, column=0)

        self.aciklama = tk.Entry(root)
        self.aciklama.grid(row=0, column=1)

        self.tutar = tk.Entry(root)
        self.tutar.grid(row=1, column=1)

        tk.Button(root, text="Gelir Ekle", command=self.gelir_ekle).grid(row=2, column=0)
        tk.Button(root, text="Gider Ekle", command=self.gider_ekle).grid(row=2, column=1)

        self.liste = tk.Listbox(root, width=50)
        self.liste.grid(row=3, column=0, columnspan=2)

        self.bakiye_label = tk.Label(root, text="Bakiye: 0 TL")
        self.bakiye_label.grid(row=4, column=0, columnspan=2)

    def gelir_ekle(self):
        try:
            tutar = float(self.tutar.get())
            self.bakiye += tutar
            self.liste.insert(tk.END, f"+ {tutar} TL - {self.aciklama.get()}")
            self.guncelle()
        except:
            messagebox.showerror("Hata", "Geçerli tutar gir")

    def gider_ekle(self):
        try:
            tutar = float(self.tutar.get())
            self.bakiye -= tutar
            self.liste.insert(tk.END, f"- {tutar} TL - {self.aciklama.get()}")
            self.guncelle()
        except:
            messagebox.showerror("Hata", "Geçerli tutar gir")

    def guncelle(self):
        self.bakiye_label.config(text=f"Bakiye: {self.bakiye} TL")
        self.aciklama.delete(0, tk.END)
        self.tutar.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = CariHesapApp(root)
    root.mainloop()
