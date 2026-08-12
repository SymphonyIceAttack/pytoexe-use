import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation

MATERIAIS = {
    "NX": Decimal("0.18"),
    "XPS": Decimal("0.11"),
    "XPS + Protect": Decimal("0.14"),
}

CONSTRUCOES = ["Laminado", "Monocamada"]


def dec(text):
    text = str(text).strip().replace(".", ".")
    if not text:
        raise InvalidOperation
    return Decimal(text)


def brl(v):
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def filme(cores, altura, largura, material):
    # Reproduz as fórmulas da planilha "Calculo Filme".
    fator = MATERIAIS[material]

    if Decimal("0") <= largura <= Decimal("15.5"):
        pistas = 4
    elif Decimal("16") <= largura <= Decimal("24.5"):
        pistas = 3
    elif Decimal("25") <= largura <= Decimal("55"):
        pistas = 2
    elif Decimal("56") <= largura <= Decimal("99"):
        pistas = 1
    else:
        pistas = None

    if Decimal("0") <= altura <= Decimal("10"):
        imagens = 5
    elif Decimal("10.5") <= altura <= Decimal("13"):
        imagens = 4
    elif Decimal("13.5") <= altura <= Decimal("20"):
        imagens = 3
    elif Decimal("20.5") <= altura <= Decimal("40"):
        imagens = 2
    elif Decimal("40.5") <= altura <= Decimal("100"):
        imagens = 1
    else:
        imagens = None

    if pistas is None or imagens is None:
        return fator, pistas, imagens, None, None, None

    tamanho_pistas = Decimal(pistas) * largura
    tamanho_imagens = Decimal(imagens) * altura
    valor = cores * tamanho_pistas * tamanho_imagens * fator
    return fator, pistas, imagens, tamanho_pistas, tamanho_imagens, valor


def saco(cores, altura, largura, material):
    # Reproduz as fórmulas da planilha "Calculo Saco".
    fator = MATERIAIS[material]
    altura_x2 = altura * 2

    if Decimal("0") <= altura_x2 <= Decimal("40"):
        pistas = 2
    elif Decimal("40") <= altura_x2 <= Decimal("100"):
        pistas = 1
    else:
        pistas = None

    if Decimal("0") <= largura <= Decimal("20"):
        imagens = 3
    elif Decimal("21") <= largura <= Decimal("100"):
        imagens = 2
    else:
        imagens = None

    if pistas is None or imagens is None:
        return fator, pistas, imagens, altura_x2, None, None, None

    tamanho_pistas = Decimal(imagens) * largura
    tamanho_imagens = Decimal(imagens) * altura
    valor = cores * altura_x2 * tamanho_pistas * fator
    return fator, pistas, imagens, altura_x2, tamanho_pistas, tamanho_imagens, valor


def umacor(cores, altura, largura, material):
    # Reproduz a planilha "Calculo somente 01 cor (1x1)".
    # Nessa aba Pistas e Imagens são fixadas em 1.
    fator = MATERIAIS[material]
    pistas = 1
    imagens = 1
    altura_x2 = altura * 2
    tamanho_pistas = largura
    tamanho_imagens = altura
    valor = cores * altura_x2 * tamanho_pistas * fator
    return fator, pistas, imagens, altura_x2, tamanho_pistas, tamanho_imagens, valor


class CalculadoraTab(ttk.Frame):
    def __init__(self, master, tipo):
        super().__init__(master, padding=18)
        self.tipo = tipo

        self.material = tk.StringVar(value="XPS + Protect")
        self.construcao = tk.StringVar(value="Laminado" if tipo == "Filme" else "Monocamada")
        self.cores = tk.StringVar(value="3" if tipo == "Filme" else "8")
        self.altura = tk.StringVar(value="11" if tipo == "Filme" else "28")
        self.largura = tk.StringVar(value="16.1" if tipo == "Filme" else "20")

        self.vars = {k: tk.StringVar(value="-") for k in [
            "fator", "pistas", "imagens", "altura_x2",
            "tam_pistas", "tam_imagens", "valor"
        ]}

        self._build()

    def _build(self):
        title = "Orçamento Clichês — " + self.tipo
        ttk.Label(self, text=title, font=("Segoe UI", 17, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 18)
        )

        form = ttk.LabelFrame(self, text="Dados de entrada", padding=14)
        form.grid(row=1, column=0, columnspan=4, sticky="ew")
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        self._combo(form, "Material", self.material, list(MATERIAIS), 0, 0)
        self._combo(form, "Construção", self.construcao, CONSTRUCOES, 0, 2)

        self._entry(form, "Cores", self.cores, 1, 0)
        self._entry(form, "Altura (cm)", self.altura, 1, 2)
        self._entry(form, "Largura (cm)", self.largura, 2, 0)

        if self.tipo == "01 cor (1x1)":
            ttk.Label(
                form, text="Pistas e imagens: fixas em 1 (conforme a planilha)",
                foreground="#555"
            ).grid(row=2, column=2, columnspan=2, sticky="w", padx=8, pady=8)

        ttk.Button(form, text="CALCULAR", command=self.calculate).grid(
            row=3, column=0, columnspan=4, sticky="ew", padx=8, pady=(12, 4), ipady=6
        )

        result = ttk.LabelFrame(self, text="Resultado", padding=14)
        result.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(18, 0))
        result.columnconfigure(1, weight=1)
        result.columnconfigure(3, weight=1)

        labels = [
            ("Valor material / fator", "fator"),
            ("Pistas", "pistas"),
            ("Imagens", "imagens"),
            ("Altura x2", "altura_x2"),
            ("Tamanho pistas", "tam_pistas"),
            ("Tamanho imagens", "tam_imagens"),
        ]
        for i, (label, key) in enumerate(labels):
            r = i // 2
            c = (i % 2) * 2
            ttk.Label(result, text=label).grid(row=r, column=c, sticky="w", padx=8, pady=7)
            ttk.Label(result, textvariable=self.vars[key], font=("Segoe UI", 10, "bold")).grid(
                row=r, column=c+1, sticky="e", padx=8, pady=7
            )

        total = ttk.Frame(result)
        total.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(12, 4))
        total.columnconfigure(1, weight=1)
        ttk.Label(total, text="VALOR:", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(
            total, textvariable=self.vars["valor"],
            font=("Segoe UI", 18, "bold")
        ).grid(row=0, column=1, sticky="e")

        ttk.Label(
            result, text="Impostos não inclusos",
            font=("Segoe UI", 9, "italic")
        ).grid(row=4, column=0, columnspan=4, sticky="w", pady=(8, 0))

        self.bind_all("<Return>", lambda e: self.calculate())

    def _entry(self, parent, label, variable, row, col):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", padx=8, pady=8)
        ttk.Entry(parent, textvariable=variable, width=18).grid(
            row=row, column=col+1, sticky="ew", padx=8, pady=8
        )

    def _combo(self, parent, label, variable, values, row, col):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", padx=8, pady=8)
        ttk.Combobox(
            parent, textvariable=variable, values=values,
            state="readonly", width=16
        ).grid(row=row, column=col+1, sticky="ew", padx=8, pady=8)

    def calculate(self):
        try:
            cores = dec(self.cores.get())
            altura = dec(self.altura.get())
            largura = dec(self.largura.get())
            if cores < 0 or altura < 0 or largura < 0:
                raise InvalidOperation

            if self.tipo == "Filme":
                fator, pistas, imagens, tp, ti, valor = filme(
                    cores, altura, largura, self.material.get()
                )
                ax2 = None
            elif self.tipo == "Saco":
                fator, pistas, imagens, ax2, tp, ti, valor = saco(
                    cores, altura, largura, self.material.get()
                )
            else:
                fator, pistas, imagens, ax2, tp, ti, valor = umacor(
                    cores, altura, largura, self.material.get()
                )

            self.vars["fator"].set(str(fator).replace(".", ","))
            self.vars["pistas"].set("-" if pistas is None else str(pistas))
            self.vars["imagens"].set("-" if imagens is None else str(imagens))
            self.vars["altura_x2"].set("-" if ax2 is None else f"{ax2:g}".replace(".", ","))
            self.vars["tam_pistas"].set("-" if tp is None else f"{tp:g}".replace(".", ","))
            self.vars["tam_imagens"].set("-" if ti is None else f"{ti:g}".replace(".", ","))

            if valor is None:
                self.vars["valor"].set("FORA DA FAIXA DA PLANILHA")
            else:
                self.vars["valor"].set(brl(valor))

        except (InvalidOperation, KeyError, ValueError):
            messagebox.showerror(
                "Dados inválidos",
                "Preencha Cores, Altura e Largura com números válidos."
            )


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Orçamento de Clichês — Versão 1")
        self.geometry("760x610")
        self.minsize(700, 560)

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        nb.add(CalculadoraTab(nb, "Filme"), text="Cálculo Filme")
        nb.add(CalculadoraTab(nb, "Saco"), text="Cálculo Saco")
        nb.add(CalculadoraTab(nb, "01 cor (1x1)"), text="Somente 01 cor (1x1)")

        ttk.Label(
            self,
            text="Versão 1 — fórmulas reproduzidas da planilha Orçamento Cliche.ods",
            foreground="#666"
        ).pack(pady=(0, 8))


if __name__ == "__main__":
    App().mainloop()
