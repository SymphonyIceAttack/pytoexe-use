import sys
import re
import os
from tkinter import Tk, filedialog, messagebox

def process_file(input_file):
    # Ruta i nom de sortida
    base, ext = os.path.splitext(input_file)
    output_file = base + ".convertit" + ext

    spot_map = {}

    # Llegir fitxer
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Crear mapping SPOT_n → Pantone
    for line in lines:
        m = re.search(r'SPOT_ID\s+"(\d+)\s+(PANTONE[^"]+)"', line)
        if m:
            num = m.group(1)
            name = m.group(2).strip()
            spot_map[f"SPOT_{num}"] = name

    # Substituir tots els SPOT_n per Pantone
    output_lines = []
    for line in lines:
        for spot, name in spot_map.items():
            line = re.sub(rf"\b{spot}\b", name, line)
        output_lines.append(line)

    # Escriure fitxer de sortida
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(output_lines)

    # Missatge final (popup si es drag & drop)
    messagebox.showinfo("Finalitzat", f"Fitxer generat:\n{output_file}")

if __name__ == "__main__":
    # Si s'arrossega un fitxer, sys.argv[1] existirà
    if len(sys.argv) > 1:
        process_file(sys.argv[1])
    else:
        # Si no, obrir diàleg per seleccionar fitxer
        root = Tk()
        root.withdraw()
        input_file = filedialog.askopenfilename(
            title="Selecciona un fitxer CGATS",
            filetypes=[("Text files", "*.txt;*.cgats")]
        )
        if input_file:
            process_file(input_file)
