import tkinter as tk
from tkinter import ttk, messagebox

# ============================================================
# CILINDROS E FECHAMENTOS - PROTÓTIPO V1
# Baseado na planilha "Cilindros e Fechamentos.xlsx.ods"
# ============================================================

def numero(valor):
    """Aceita números no padrão brasileiro (ex.: 480, 480,5)."""
    valor = str(valor).strip().replace(".", "").replace(",", ".")
    return float(valor)

def fmt(valor, casas=2):
    return f"{valor:.{casas}f}".replace(".", ",")

def calcular_cilindro():
    try:
        cilindro = numero(ent_cilindro.get())
        imagens = numero(ent_imagens.get())

        if imagens <= 0:
            raise ValueError("O número de imagens deve ser maior que zero.")

        # Regra da planilha:
        # Fechamento = Cilindro - 5
        fechamento = cilindro - 5
        fechamento_unitario = fechamento / imagens

        # A planilha trabalha com passo/layout arredondado para mm inteiro
        # para o valor de referência do layout.
        passo_layout = round(fechamento_unitario)

        # Tolerância indicada na planilha.
        tolerancia = "± 1 mm"

        var_fechamento.set(f"{fmt(fechamento, 0)} mm")
        var_unitario.set(f"{fmt(fechamento_unitario)} mm")
        var_passo.set(f"{fmt(passo_layout, 0)} mm")
        var_tolerancia.set(tolerancia)

    except Exception as e:
        messagebox.showerror("Erro", str(e))

def calcular_rapido():
    try:
        passo = numero(ent_passo.get())
        imagens = numero(ent_imagens_rapido.get())

        if imagens <= 0:
            raise ValueError("O número de imagens deve ser maior que zero.")

        resultado = passo * imagens
        var_resultado_rapido.set(f"{fmt(resultado, 0)} mm")

    except Exception as e:
        messagebox.showerror("Erro", str(e))

def limpar():
    ent_cilindro.delete(0, tk.END)
    ent_imagens.delete(0, tk.END)
    ent_cilindro.insert(0, "480")
    ent_imagens.insert(0, "3")

    ent_passo.delete(0, tk.END)
    ent_imagens_rapido.delete(0, tk.END)
    ent_passo.insert(0, "160")
    ent_imagens_rapido.insert(0, "3")

    var_fechamento.set("-")
    var_unitario.set("-")
    var_passo.set("-")
    var_tolerancia.set("-")
    var_resultado_rapido.set("-")

root = tk.Tk()
root.title("Cilindros e Fechamentos - Protótipo V1")
root.geometry("760x650")
root.resizable(False, False)

style = ttk.Style()
try:
    style.theme_use("clam")
except:
    pass

titulo = ttk.Label(
    root,
    text="CÁLCULO DE CILINDRO E FECHAMENTO",
    font=("Segoe UI", 18, "bold")
)
titulo.pack(pady=(20, 5))

subtitulo = ttk.Label(
    root,
    text="Protótipo V1 — baseado na planilha fornecida",
    font=("Segoe UI", 10)
)
subtitulo.pack(pady=(0, 15))

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=25, pady=10)

# ------------------------------------------------------------
# Aba 1
# ------------------------------------------------------------
aba1 = ttk.Frame(notebook, padding=25)
notebook.add(aba1, text="  Cilindro e Fechamento  ")

ttk.Label(aba1, text="Cilindro (mm):", font=("Segoe UI", 11)).grid(
    row=0, column=0, sticky="w", pady=8
)
ent_cilindro = ttk.Entry(aba1, width=25, font=("Segoe UI", 12))
ent_cilindro.grid(row=0, column=1, pady=8, padx=15)
ent_cilindro.insert(0, "480")

ttk.Label(aba1, text="Impressora:", font=("Segoe UI", 11)).grid(
    row=1, column=0, sticky="w", pady=8
)
combo_impressora = ttk.Combobox(
    aba1,
    width=22,
    state="readonly",
    values=[
        "Bielloni 28",
        "Flexopower 29",
        "Flexopower 30",
        "Flexopower 31",
    ],
)
combo_impressora.grid(row=1, column=1, pady=8, padx=15)
combo_impressora.current(0)

ttk.Label(aba1, text="Nº de imagens:", font=("Segoe UI", 11)).grid(
    row=2, column=0, sticky="w", pady=8
)
ent_imagens = ttk.Entry(aba1, width=25, font=("Segoe UI", 12))
ent_imagens.grid(row=2, column=1, pady=8, padx=15)
ent_imagens.insert(0, "3")

ttk.Label(aba1, text="Substrato:", font=("Segoe UI", 11)).grid(
    row=3, column=0, sticky="w", pady=8
)
combo_substrato = ttk.Combobox(
    aba1,
    width=22,
    state="readonly",
    values=["BOPP", "PET", "PP", "PEBD", "CPP"],
)
combo_substrato.grid(row=3, column=1, pady=8, padx=15)
combo_substrato.current(1)

ttk.Button(aba1, text="CALCULAR", command=calcular_cilindro).grid(
    row=4, column=0, columnspan=2, pady=20, ipadx=40, ipady=6
)

frame_resultado = ttk.LabelFrame(aba1, text=" Resultado ", padding=15)
frame_resultado.grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)

var_fechamento = tk.StringVar(value="-")
var_unitario = tk.StringVar(value="-")
var_passo = tk.StringVar(value="-")
var_tolerancia = tk.StringVar(value="-")

linhas = [
    ("Fechamento:", var_fechamento),
    ("Fechamento unitário:", var_unitario),
    ("Passo / Layout:", var_passo),
    ("Tolerância:", var_tolerancia),
]

for i, (texto, variavel) in enumerate(linhas):
    ttk.Label(frame_resultado, text=texto, font=("Segoe UI", 11)).grid(
        row=i, column=0, sticky="w", padx=10, pady=7
    )
    ttk.Label(
        frame_resultado,
        textvariable=variavel,
        font=("Segoe UI", 12, "bold")
    ).grid(row=i, column=1, sticky="e", padx=10, pady=7)

# ------------------------------------------------------------
# Aba 2
# ------------------------------------------------------------
aba2 = ttk.Frame(notebook, padding=25)
notebook.add(aba2, text="  Cálculo Rápido  ")

ttk.Label(
    aba2,
    text="CÁLCULO RÁPIDO DE CILINDRO",
    font=("Segoe UI", 15, "bold")
).grid(row=0, column=0, columnspan=2, pady=(5, 25))

ttk.Label(aba2, text="Passo / Layout (mm):", font=("Segoe UI", 11)).grid(
    row=1, column=0, sticky="w", pady=10
)
ent_passo = ttk.Entry(aba2, width=25, font=("Segoe UI", 12))
ent_passo.grid(row=1, column=1, padx=15, pady=10)
ent_passo.insert(0, "160")

ttk.Label(aba2, text="Nº de imagens:", font=("Segoe UI", 11)).grid(
    row=2, column=0, sticky="w", pady=10
)
ent_imagens_rapido = ttk.Entry(aba2, width=25, font=("Segoe UI", 12))
ent_imagens_rapido.grid(row=2, column=1, padx=15, pady=10)
ent_imagens_rapido.insert(0, "3")

ttk.Button(aba2, text="CALCULAR", command=calcular_rapido).grid(
    row=3, column=0, columnspan=2, pady=25, ipadx=40, ipady=6
)

frame_rapido = ttk.LabelFrame(aba2, text=" Resultado ", padding=20)
frame_rapido.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)

var_resultado_rapido = tk.StringVar(value="-")
ttk.Label(
    frame_rapido,
    text="Cilindro:",
    font=("Segoe UI", 12)
).grid(row=0, column=0, padx=15, pady=15)

ttk.Label(
    frame_rapido,
    textvariable=var_resultado_rapido,
    font=("Segoe UI", 16, "bold")
).grid(row=0, column=1, padx=15, pady=15)

ttk.Button(root, text="LIMPAR / RESTAURAR EXEMPLOS", command=limpar).pack(
    pady=(0, 20)
)

root.mainloop()
