import tkinter as tk
from tkinter import filedialog

def kaydet():
    kod = metin.get("1.0", tk.END)
    dosya = filedialog.asksaveasfilename(
        defaultextension=".py",
        filetypes=[("Python Dosyası", "*.py")]
    )
    if dosya:
        with open(dosya, "w", encoding="utf-8") as f:
            f.write(kod)

# Pencere
pencere = tk.Tk()
pencere.title("HTML Görünümlü Python Kaydedici")
pencere.geometry("600x400")

# Sahte HTML etiketi hissi
etiket = tk.Label(pencere, text="<python>", font=("Consolas", 12))
etiket.pack(anchor="w", padx=10)

metin = tk.Text(pencere, font=("Consolas", 12))
metin.pack(expand=True, fill="both", padx=10)

etiket2 = tk.Label(pencere, text="</python>", font=("Consolas", 12))
etiket2.pack(anchor="w", padx=10)

buton = tk.Button(pencere, text="Python Olarak Kaydet", command=kaydet)
buton.pack(pady=10)

pencere.mainloop()
