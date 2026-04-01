import tkinter as tk

# ================= FUNKCJE =================

def dodaj(znak):
    pole.insert(tk.END, znak)

def wyczysc():
    pole.delete(0, tk.END)

def usun_znak():
    tekst = pole.get()
    pole.delete(0, tk.END)
    pole.insert(0, tekst[:-1])

def oblicz():
    try:
        wyrazenie = pole.get()

        if wyrazenie.strip() == "":
            raise ValueError("Najpierw wpisz działanie")

        wynik = eval(wyrazenie)

        pole.delete(0, tk.END)
        pole.insert(0, str(wynik))

    except ZeroDivisionError:
        pole.delete(0, tk.END)
        pole.insert(0, "Nie można dzielić przez zero")

    except SyntaxError:
        pole.delete(0, tk.END)
        pole.insert(0, "Błędne działanie")

    except ValueError as e:
        pole.delete(0, tk.END)
        pole.insert(0, str(e))

    except Exception:
        pole.delete(0, tk.END)
        pole.insert(0, "Nieznany błąd")

# ================= KLAWIATURA =================

def klawiatura(event):
    znak = event.char

    if znak in "0123456789+-*/.":
        dodaj(znak)
    elif event.keysym == "Return":
        oblicz()
    elif event.keysym == "BackSpace":
        wyczysc()
    # ESC celowo NIC nie robi

# ================= OKNO =================

okno = tk.Tk()
okno.title("Kalkulator")
okno.geometry("320x450")
okno.resizable(True, True)

# ================= WYŚWIETLACZ =================

pole = tk.Entry(
    okno,
    font=("Segoe UI", 26),
    justify="right",
    bd=10
)
pole.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)

# ================= RAMKA =================

ramka = tk.Frame(okno)
ramka.grid(row=1, column=0, columnspan=4, sticky="nsew")

okno.rowconfigure(0, weight=1)
okno.rowconfigure(1, weight=5)
okno.columnconfigure(0, weight=1)

# ================= PRZYCISKI =================

def przycisk(txt, r, c, cmd, colspan=1, rowspan=1):
    btn = tk.Button(
        ramka,
        text=txt,
        font=("Segoe UI", 16),
        command=cmd
    )
    btn.grid(row=r, column=c, columnspan=colspan, rowspan=rowspan,
             sticky="nsew", padx=2, pady=2)

for i in range(5):
    ramka.rowconfigure(i, weight=1)
for i in range(4):
    ramka.columnconfigure(i, weight=1)

# Rząd 1
przycisk("C", 0, 0, wyczysc)
przycisk("←", 0, 1, usun_znak)
przycisk("/", 0, 2, lambda: dodaj("/"))
przycisk("*", 0, 3, lambda: dodaj("*"))

# Rząd 2
przycisk("7", 1, 0, lambda: dodaj("7"))
przycisk("8", 1, 1, lambda: dodaj("8"))
przycisk("9", 1, 2, lambda: dodaj("9"))
przycisk("-", 1, 3, lambda: dodaj("-"))

# Rząd 3
przycisk("4", 2, 0, lambda: dodaj("4"))
przycisk("5", 2, 1, lambda: dodaj("5"))
przycisk("6", 2, 2, lambda: dodaj("6"))
przycisk("+", 2, 3, lambda: dodaj("+"))

# Rząd 4
przycisk("1", 3, 0, lambda: dodaj("1"))
przycisk("2", 3, 1, lambda: dodaj("2"))
przycisk("3", 3, 2, lambda: dodaj("3"))
przycisk("=", 3, 3, oblicz, rowspan=2)

# Rząd 5
przycisk("0", 4, 0, lambda: dodaj("0"), colspan=2)
przycisk(".", 4, 2, lambda: dodaj("."))

# ================= KLAWIATURA =================

okno.bind("<Key>", klawiatura)

# ================= START =================

okno.mainloop()