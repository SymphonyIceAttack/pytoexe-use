# ===============================
# KASA SKLEPOWA – Python 3 + Tkinter + SQLite3
# Logowanie pracownika, sprzedaz, paragony, bony z waznoscia
# ===============================

import tkinter as tk
from tkinter import messagebox
import sqlite3
import datetime
import random
import string

# ---------- BAZA DANYCH ----------
conn = sqlite3.connect("kasa.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS pracownicy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT UNIQUE,
    pin TEXT,
    karta TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS produkty (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kod TEXT UNIQUE,
    nazwa TEXT,
    cena REAL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS sprzedaz (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nr_paragonu INTEGER,
    nazwa TEXT,
    cena REAL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS licznik (
    id INTEGER PRIMARY KEY CHECK(id=1),
    numer INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS bony (
    kod TEXT PRIMARY KEY,
    kwota REAL,
    waznosc DATE,
    wykorzystany INTEGER
)
""")

c.execute("INSERT OR IGNORE INTO licznik (id, numer) VALUES (1,1)")
c.execute("INSERT OR IGNORE INTO pracownicy (login,pin,karta) VALUES ('admin','1234','0000')")
conn.commit()

# ---------- ZMIENNE ----------
zalogowany = None
suma = 0.0
nazwa_sklepu = "SKLEP XYZ"
adres_sklepu = "ul. Przykladowa 1"

# ---------- FUNKCJE ----------
def losowy_kod(n=8):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))

# ---------- LOGOWANIE ----------
def zaloguj():
    global zalogowany
    l = e_login.get()
    h = e_haslo.get()

    r = c.execute("SELECT login FROM pracownicy WHERE login=? AND (pin=? OR karta=?)", (l,h,h)).fetchone()

    if r:
        zalogowany = r[0]
        messagebox.showinfo(
            "Informacja",
            "UWAGA: To nie jest darmowy program.
"
            "Po 22 dniach program staje sie platny.

"
            "Cennik:
"
            "- 22 PLN / miesiac
"
            "- 222 PLN / rok

"
            "Platnosc BLIK na numer:
+48 573 244 366"
        )
        okno_login.destroy()
        start_kasa()
    else:
        messagebox.showerror("Blad", "Bledne dane logowania")

# ---------- KASA ----------
def dodaj_produkt():
    try:
        c.execute("INSERT INTO produkty (kod,nazwa,cena) VALUES (?,?,?)",
                  (e_pkod.get(), e_pnazwa.get(), float(e_pcena.get())))
        conn.commit()
        messagebox.showinfo("OK", "Produkt dodany")
    except:
        messagebox.showerror("Blad", "Kod juz istnieje")


def sprzedaj():
    global suma
    kod = e_skan.get()
    r = c.execute("SELECT nazwa,cena FROM produkty WHERE kod=?", (kod,)).fetchone()
    if not r:
        messagebox.showerror("Blad", "Nieznany kod produktu")
        return

    nr = c.execute("SELECT numer FROM licznik WHERE id=1").fetchone()[0]
    c.execute("INSERT INTO sprzedaz (nr_paragonu,nazwa,cena) VALUES (?,?,?)", (nr,r[0],r[1]))
    conn.commit()

    lista.insert(tk.END, f"{r[0]} - {r[1]} zl")
    suma += r[1]
    lbl_suma.config(text=f"Suma: {round(suma,2)} zl")


def uzyj_bon():
    global suma
    kod = e_bon.get()
    today = datetime.date.today()
    r = c.execute("SELECT kwota,waznosc,wykorzystany FROM bony WHERE kod=?", (kod,)).fetchone()

    if not r:
        messagebox.showerror("Blad", "Bon nie istnieje")
        return

    kw, waznosc, wykorzystany = r
    if wykorzystany == 1:
        messagebox.showerror("Blad", "Bon juz wykorzystany")
        return

    if datetime.datetime.strptime(waznosc, '%Y-%m-%d').date() < today:
        messagebox.showerror("Blad", "Bon wygasl")
        return

    suma -= kw
    if suma < 0:
        suma = 0

    c.execute("UPDATE bony SET wykorzystany=1 WHERE kod=?", (kod,))
    conn.commit()
    lbl_suma.config(text=f"Suma: {round(suma,2)} zl")


def paragon():
    global suma
    nr = c.execute("SELECT numer FROM licznik WHERE id=1").fetchone()[0]
    rows = c.execute("SELECT nazwa,cena FROM sprzedaz WHERE nr_paragonu=?", (nr,)).fetchall()

    if not rows:
        messagebox.showwarning("Brak", "Nie mozna wystawic pustego paragonu")
        return

    tekst = f"""{nazwa_sklepu}\n{adres_sklepu}\n\nPARAGON NR {nr}\nData: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\nKasjer: {zalogowany}\n--------------------------------\n"""

    for n, c1 in rows:
        tekst += f"{n} - {c1} zl\n"

    tekst += f"--------------------------------\nSUMA: {round(suma,2)} zl\nDziekujemy za zakupy!\n"

    with open(f"paragon_{nr}.txt", "w", encoding="utf-8") as f:
        f.write(tekst)

    c.execute("UPDATE licznik SET numer=numer+1 WHERE id=1")
    c.execute("DELETE FROM sprzedaz WHERE nr_paragonu=?", (nr,))
    conn.commit()

    lista.delete(0, tk.END)
    suma = 0
    lbl_suma.config(text="Suma: 0 zl")
    messagebox.showinfo("OK", "Paragon zapisany")

# ---------- TWORZENIE BONU ----------
def nowy_bon():
    kod = losowy_kod()
    try:
        kw = float(e_kwota.get())
        waznosc_input = e_waznosc.get()
        datetime.datetime.strptime(waznosc_input, '%Y-%m-%d')  # sprawdzenie formatu daty
    except:
        messagebox.showerror("Blad", "Nieprawidlowe dane: kwota musi byc liczba, waznosc YYYY-MM-DD")
        return

    c.execute("INSERT INTO bony (kod,kwota,waznosc,wykorzystany) VALUES (?,?,?,0)", (kod, kw, waznosc_input))
    conn.commit()
    messagebox.showinfo("Bon utworzony", f"Kod: {kod}\nKwota: {kw} zl\nWaznosc: {waznosc_input}")

# ---------- GUI KASY ----------
def start_kasa():
    global e_pkod,e_pnazwa,e_pcena,e_skan,lista,lbl_suma,e_bon,e_kwota,e_waznosc

    okno = tk.Tk()
    okno.title("Kasa sklepowa")

    tk.Label(okno, text=f"Kasjer: {zalogowany}").grid(row=0, column=0, columnspan=3)

    e_pkod = tk.Entry(okno); e_pkod.grid(row=1,column=0)
    e_pnazwa = tk.Entry(okno); e_pnazwa.grid(row=1,column=1)
    e_pcena = tk.Entry(okno); e_pcena.grid(row=1,column=2)
    tk.Button(okno, text="Dodaj produkt", command=dodaj_produkt).grid(row=1,column=3)

    e_skan = tk.Entry(okno); e_skan.grid(row=2,column=0)
    tk.Button(okno, text="Sprzedaj", command=sprzedaj).grid(row=2,column=1)

    lista = tk.Listbox(okno, width=40)
    lista.grid(row=3,column=0,columnspan=4)

    lbl_suma = tk.Label(okno, text="Suma: 0 zl")
    lbl_suma.grid(row=4,column=0)

    e_bon = tk.Entry(okno); e_bon.grid(row=5,column=0)
    tk.Button(okno, text="Uzyj bon", command=uzyj_bon).grid(row=5,column=1)

    tk.Button(okno, text="Paragon", command=paragon).grid(row=6,column=0)

    e_kwota = tk.Entry(okno); e_kwota.grid(row=7,column=0)
    e_waznosc = tk.Entry(okno); e_waznosc.grid(row=7,column=1)
    tk.Button(okno, text="Nowy bon", command=nowy_bon).grid(row=7,column=2)

    okno.mainloop()

# ---------- OKNO LOGOWANIA ----------
okno_login = tk.Tk()
okno_login.title("Logowanie pracownika")

tk.Label(okno_login, text="Login").grid(row=0,column=0)
e_login = tk.Entry(okno_login)
e_login.grid(row=0,column=1)

tk.Label(okno_login, text="PIN lub karta").grid(row=1,column=0)
e_haslo = tk.Entry(okno_login, show="*")
e_haslo.grid(row=1,column=1)

tk.Button(okno_login, text="Zaloguj", command=zaloguj).grid(row=2,column=0,columnspan=2)

okno_login.mainloop()
