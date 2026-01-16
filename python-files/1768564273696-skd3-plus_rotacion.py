import os
import re
import pdfplumber
import tkinter as tk
from tkinter import filedialog, messagebox

PLUS_ROTACION = {
    2023: 0.67,
    2024: 0.70,
    2025: 0.72,
    2026: 0.74
}

PALABRAS_CLAVE = ["CONTROL 1", "REFUERZO CONTROL 1"]

def extraer_horas_pdf(ruta_pdf):
    horas = 0.0
    with pdfplumber.open(ruta_pdf) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if not texto:
                continue
            for linea in texto.splitlines():
                if not any(p in linea.upper() for p in PALABRAS_CLAVE):
                    continue
                match = re.search(r"\b\d{1,2}[.,]\d{2}\b", linea)
                if match:
                    horas += float(match.group().replace(",", "."))
    return horas

def calcular_total(carpeta):
    total = 0.0
    for archivo in os.listdir(carpeta):
        if archivo.lower().endswith(".pdf"):
            total += extraer_horas_pdf(os.path.join(carpeta, archivo))
    return total

def calcular():
    anios = [a for a, v in vars_anios.items() if v.get()]
    if len(anios) != 1:
        messagebox.showerror("Error", "Marca un solo año.")
        return
    anio = anios[0]
    carpeta = filedialog.askdirectory()
    if not carpeta:
        return
    horas = calcular_total(carpeta)
    euros = horas * PLUS_ROTACION[anio]
    resultado.delete("1.0", tk.END)
    resultado.insert(tk.END, f"AÑO {anio}\n\nIMPORTE TOTAL A COBRAR:\n{euros:.2f} €")

root = tk.Tk()
root.title("Plus de Rotación")
root.geometry("350x260")

frame = tk.Frame(root)
frame.pack(pady=10)

vars_anios = {}
for a in [2023, 2024, 2025, 2026]:
    v = tk.BooleanVar()
    tk.Checkbutton(frame, text=str(a), variable=v).pack(side=tk.LEFT, padx=5)
    vars_anios[a] = v

tk.Button(root, text="Seleccionar carpeta y calcular", command=calcular).pack(pady=10)

resultado = tk.Text(root, height=5)
resultado.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

root.mainloop()