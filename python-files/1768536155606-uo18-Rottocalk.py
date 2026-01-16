import os
import re
from datetime import datetime
from collections import defaultdict
from tkinter import Tk, Button, Label, Text, END, Frame, StringVar, Checkbutton, filedialog
from PyPDF2 import PdfReader
from fpdf import FPDF

# ================= CONFIGURACIÓN =================

PLUS_POR_HORA = {
    2023: 0.67,
    2024: 0.70,
    2025: 0.72,
    2026: 0.75,
}

ADVERTENCIA_LEGAL = (
    "⚠️ Esta herramienta es un apoyo para el cálculo; se recomienda\n"
    "siempre la comprobación manual de los datos."
)

COLOR_FONDO = "#FFFFFF"
COLOR_TEXTO = "#005A2B"
COLOR_BOTON = "#007A3D"
COLOR_BOTON_TEXTO = "#FFFFFF"

# ================= FUNCIONES =================

def extraer_horas(texto):
    patron = re.compile(
        r'(\d{2}/\d{2}/\d{4}).*?(Control 1|Refuerzo Control 1).*?(\d+(?:[.,]\d+)?)\s*horas?',
        re.IGNORECASE
    )
    resultados = []
    for fecha, servicio, horas in patron.findall(texto):
        try:
            fecha_dt = datetime.strptime(fecha, "%d/%m/%Y")
            horas = float(horas.replace(",", "."))
            resultados.append((fecha_dt, servicio, horas))
        except:
            pass
    return resultados

def leer_pdfs(carpeta):
    datos = []
    for f in os.listdir(carpeta):
        if f.lower().endswith(".pdf"):
            try:
                lector = PdfReader(os.path.join(carpeta, f))
                texto = ""
                for p in lector.pages:
                    texto += p.extract_text() or ""
                datos.extend(extraer_horas(texto))
            except:
                pass
    return datos

def calcular(datos, años):
    horas_por_año = defaultdict(float)
    detalle = defaultdict(list)
    for fecha, servicio, horas in datos:
        if fecha.year in años:
            horas_por_año[fecha.year] += horas
            detalle[fecha.year].append(
                (fecha.strftime("%d/%m/%Y"), servicio, horas)
            )
    return horas_por_año, detalle

def generar_pdf(ruta, horas_por_año, detalle):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    pdf.multi_cell(0, 8, ADVERTENCIA_LEGAL)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Resumen Plus de Rotación", ln=True, align="C")
    pdf.ln(5)

    total = 0
    for año in sorted(horas_por_año):
        horas = horas_por_año[año]
        importe = horas * PLUS_POR_HORA.get(año, 0)
        total += importe
        pdf.cell(
            0, 8,
            f"Año {año}: {horas:.2f} h x {PLUS_POR_HORA.get(año,0):.2f} €/h = {importe:.2f} €",
            ln=True
        )

    pdf.ln(6)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, f"TOTAL ESTIMADO: {total:.2f} €", ln=True)
    pdf.ln(6)
    pdf.cell(0, 8, "Detalle de días trabajados:", ln=True)

    for año in sorted(detalle):
        pdf.cell(0, 7, f"Año {año}:", ln=True)
        for f, s, h in detalle[año]:
            pdf.cell(0, 6, f"  {f} - {s} - {h} horas", ln=True)

    pdf.output(ruta)

# ================= INTERFAZ =================

def main():
    root = Tk()
    root.title("Calculadora Plus Rotación")
    root.configure(bg=COLOR_FONDO)
    root.geometry("800x650")

    # Mostrar advertencia legal arriba
    Label(
        root,
        text=ADVERTENCIA_LEGAL,
        font=("Arial", 10, "italic"),
        fg="#FF0000",
        bg=COLOR_FONDO,
        justify="left"
    ).pack(pady=5)

    Label(
        root,
        text="Calculadora Plus de Rotación",
        font=("Arial", 14, "bold"),
        fg=COLOR_TEXTO,
        bg=COLOR_FONDO
    ).pack()

    Label(
        root,
        text="1️⃣ Selecciona la carpeta con tus PDFs",
        fg=COLOR_TEXTO,
        bg=COLOR_FONDO
    ).pack(pady=5)

    resultado = Text(root, height=20, width=90)
    resultado.pack(pady=10)

    Label(
        root,
        text="2️⃣ Selecciona los años a calcular",
        fg=COLOR_TEXTO,
        bg=COLOR_FONDO
    ).pack(pady=5)

    frame_años = Frame(root, bg=COLOR_FONDO)
    frame_años.pack()

    vars_años = {}
    for año in sorted(PLUS_POR_HORA):
        var = StringVar(value="1")
        cb = Checkbutton(
            frame_años, text=str(año),
            variable=var, onvalue="1", offvalue="0",
            fg=COLOR_TEXTO, bg=COLOR_FONDO
        )
        cb.pack(side="left", padx=10)
        vars_años[año] = var

    def ejecutar():
        # Forzar diálogo encima de todo
        root.lift()
        root.attributes('-topmost', True)
        root.after_idle(root.attributes,'-topmost',False)

        carpeta = filedialog.askdirectory()
        if not carpeta:
            return

        resultado.delete("1.0", END)
        resultado.insert(END, f"Carpeta seleccionada: {carpeta}\n\n")

        años = [a for a, v in vars_años.items() if v.get() == "1"]
        if not años:
            resultado.insert(END, "❌ No has seleccionado ningún año.\n")
            return

        datos = leer_pdfs(carpeta)
        if not datos:
            resultado.insert(END, "❌ No se han encontrado servicios de Control 1.\n")
            return

        horas, detalle = calcular(datos, años)

        total = 0
        for año in sorted(horas):
            importe = horas[año] * PLUS_POR_HORA.get(año, 0)
            total += importe
            resultado.insert(
                END,
                f"Año {año}: {horas[año]:.2f} h → {importe:.2f} €\n"
            )

        resultado.insert(END, f"\nTOTAL ESTIMADO: {total:.2f} €\n")

        pdf_path = os.path.join(carpeta, "Resumen_Plus_Rotacion.pdf")
        generar_pdf(pdf_path, horas, detalle)
        resultado.insert(END, f"\n📄 PDF generado en:\n{pdf_path}\n")

    Button(
        root,
        text="▶️ CALCULAR",
        font=("Arial", 13),
        fg=COLOR_BOTON_TEXTO,
        bg=COLOR_BOTON,
        command=ejecutar
    ).pack(pady=15)

    root.mainloop()

if __name__ == "__main__":
    main()