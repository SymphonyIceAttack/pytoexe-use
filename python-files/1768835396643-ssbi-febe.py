import tkinter as tk
from tkinter import ttk

# ===== FUNÇÕES DE CÁLCULO =====

def calcular_tolerancia_geral(medida):
    try:
        medida = float(medida)
    except ValueError:
        return 0

    if medida > 7996: return 3.0
    if medida > 3996: return 2.0
    if medida > 1996: return 1.2
    if medida > 996:  return 0.8
    if medida > 396:  return 0.5
    if medida > 116:  return 0.3
    if medida > 26:   return 0.1
    if medida > 5:    return 0.1
    return 0


def calcular_tolerancia_micra(valor):
    try:
        m = float(valor)
    except ValueError:
        return 0

    if m > 1996: return 0.100
    if m > 996:  return 0.050
    if m > 102:  return 0.025
    return 0.015


def atualizar_altura(*args):
    perfil = perfil_var.get()
    suporte = suporte_var.get()

    tabela = {
        ("V80", "Q15"): "3,5",

        ("V100", "Q15"): "3,6",
        ("V100", "Q20"): "4,3",
        ("V100", "Q25"): "5,1",
        ("V100", "Q30"): "5,8",

        ("V150", "Q15"): "4,1",
        ("V150", "Q20"): "4,8",
        ("V150", "Q25"): "5,6",
        ("V150", "Q30"): "6,1",
        ("V150", "Q40"): "7,5",

        ("V175", "Q20"): "5,2",
        ("V175", "Q25"): "6,0",
        ("V175", "Q30"): "7,1",
        ("V175", "Q40"): "8,0",

        ("V230", "Q25"): "6,3",
        ("V230", "Q30"): "7,1",
        ("V230", "Q40"): "8,4",
    }

    altura_var.set(tabela.get((perfil, suporte), ""))


def tratar_diametro(event):
    valor = diametro_var.get()
    valor = ''.join(c for c in valor if c.isdigit() or c == '.')
    if valor:
        tol = calcular_tolerancia_geral(valor)
        diametro_var.set(f"{valor} - tolerância {tol}")


def tratar_comprimento(event):
    valor = comprimento_var.get()
    valor = ''.join(c for c in valor if c.isdigit() or c == '.')
    if valor:
        tol = calcular_tolerancia_geral(valor)
        comprimento_var.set(f"{valor} - tolerância {tol}")


def tratar_micragem(event):
    valor = micragem_var.get()
    valor = ''.join(c for c in valor if c.isdigit() or c == '.')
    if valor:
        m = float(valor)
        tol = calcular_tolerancia_micra(m)
        divisao = f"{m / 1000:.3f}"
        micragem_var.set(f"{valor} micra - {divisao} tol: {tol:.3f}")


# ===== INTERFACE =====

root = tk.Tk()
root.title("FEBE - Sistema de Medição")
root.geometry("420x500")

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(fill="both", expand=True)

def label(text):
    tk.Label(frame, text=text, font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 0))

def entry(var, readonly=False):
    e = tk.Entry(frame, textvariable=var)
    if readonly:
        e.configure(state="readonly")
    e.pack(fill="x")
    return e


codigo_var = tk.StringVar()
diametro_var = tk.StringVar()
comprimento_var = tk.StringVar()
micragem_var = tk.StringVar()
perfil_var = tk.StringVar()
suporte_var = tk.StringVar()
altura_var = tk.StringVar()

label("Código")
entry(codigo_var)

label("Diâmetro")
e_diam = entry(diametro_var)
e_diam.bind("<FocusOut>", tratar_diametro)

label("Comprimento")
e_comp = entry(comprimento_var)
e_comp.bind("<FocusOut>", tratar_comprimento)

label("Micragem")
e_micra = entry(micragem_var)
e_micra.bind("<FocusOut>", tratar_micragem)

label("Perfil")
perfil = ttk.Combobox(frame, textvariable=perfil_var, values=[
    "V80 - 0,80 x 1,20", "V100 - 1,00 x 2,00", "V150 - 1,50 x 2,50", "V175 - 1,75 x 3,00", "V230 - 2,30 x 3,50"
])
perfil.pack(fill="x")
perfil.bind("<<ComboboxSelected>>", atualizar_altura)

label("Suporte")
suporte = ttk.Combobox(frame, textvariable=suporte_var, values=[
    "Q15 - 1,50 x 2,50 ", "Q20 - 2,00 x 3,20", "Q25 - 2,50 x 4,00 ", "Q30 - 3,00 x 5,00 ", "Q40 - 4,00 x 6,00"
])
suporte.pack(fill="x")
suporte.bind("<<ComboboxSelected>>", atualizar_altura)

label("Altura")
entry(altura_var, readonly=True)

root.mainloop()
