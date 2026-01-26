import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta, date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ===== DATABASE =====
conn = sqlite3.connect("yacine_sat.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT,
    telephone TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS abonnements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    type TEXT,
    prix REAL,
    date_debut TEXT,
    date_fin TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS ventes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client TEXT,
    montant REAL,
    date TEXT
)
""")

conn.commit()

# ===== APP =====
app = tk.Tk()
app.title("YACINE SAT")
app.geometry("650x500")
app.configure(bg="#1e1e2f")

# ??? ???? ??????
# app.iconbitmap("icon.ico")

tk.Label(app, text="YACINE SAT", fg="white", bg="#1e1e2f",
         font=("Segoe UI", 20, "bold")).pack(pady=10)
tk.Label(app, text="Gestion des ventes & abonnements",
         fg="lightgray", bg="#1e1e2f").pack()

# ===== FUNCTIONS =====
def window_clients():
    w = tk.Toplevel(app)
    w.title("Clients")
    w.geometry("350x300")

    tk.Label(w, text="Nom").pack()
    nom = tk.Entry(w)
    nom.pack()

    tk.Label(w, text="T�l�phone").pack()
    tel = tk.Entry(w)
    tel.pack()

    def save():
        cur.execute("INSERT INTO clients VALUES (NULL,?,?)",
                    (nom.get(), tel.get()))
        conn.commit()
        w.destroy()

    tk.Button(w, text="Enregistrer", command=save).pack(pady=10)

def window_abonnements():
    w = tk.Toplevel(app)
    w.title("Abonnements")
    w.geometry("350x350")

    tk.Label(w, text="ID Client").pack()
    cid = tk.Entry(w)
    cid.pack()

    tk.Label(w, text="Type").pack()
    type_ab = ttk.Combobox(w, values=["Mensuel", "Trimestriel", "Annuel"])
    type_ab.pack()

    tk.Label(w, text="Prix").pack()
    prix = tk.Entry(w)
    prix.pack()

    def save():
        days = 30 if type_ab.get() == "Mensuel" else 90 if type_ab.get() == "Trimestriel" else 365
        debut = datetime.now()
        fin = debut + timedelta(days=days)

        cur.execute("""
        INSERT INTO abonnements VALUES (NULL,?,?,?,?,?)
        """, (
            cid.get(),
            type_ab.get(),
            prix.get(),
            debut.strftime("%Y-%m-%d"),
            fin.strftime("%Y-%m-%d")
        ))
        conn.commit()
        w.destroy()

    tk.Button(w, text="Enregistrer", command=save).pack(pady=10)

def window_ventes():
    w = tk.Toplevel(app)
    w.title("Ventes")
    w.geometry("350x300")

    tk.Label(w, text="Client").pack()
    client = tk.Entry(w)
    client.pack()

    tk.Label(w, text="Montant").pack()
    montant = tk.Entry(w)
    montant.pack()

    def save():
        cur.execute("INSERT INTO ventes VALUES (NULL,?,?,?)",
                    (client.get(), montant.get(),
                     datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        facture_pdf(client.get(), montant.get())
        w.destroy()

    tk.Button(w, text="Enregistrer", command=save).pack(pady=10)

# ===== PDF =====
def rapport_ventes_pdf():
    c = canvas.Canvas("rapport_ventes.pdf", pagesize=A4)
    c.setFont("Helvetica", 12)
    c.drawString(50, 800, "Rapport des ventes - YACINE SAT")

    y = 760
    cur.execute("SELECT client, montant, date FROM ventes")
    for v in cur.fetchall():
        c.drawString(50, y, f"{v[2]} | {v[0]} | {v[1]} DA")
        y -= 20

    c.save()
    messagebox.showinfo("PDF", "Rapport g�n�r� : rapport_ventes.pdf")

def facture_pdf(client, montant):
    c = canvas.Canvas(f"facture_{client}.pdf", pagesize=A4)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 800, "FACTURE - YACINE SAT")

    c.setFont("Helvetica", 12)
    c.drawString(50, 760, f"Client : {client}")
    c.drawString(50, 730, f"Montant : {montant} DA")
    c.drawString(50, 700, f"Date : {date.today()}")

    c.save()

# ===== ALERT =====
def check_abonnements():
    today = date.today().strftime("%Y-%m-%d")
    cur.execute("SELECT COUNT(*) FROM abonnements WHERE date_fin < ?", (today,))
    expired = cur.fetchone()[0]

    if expired > 0:
        messagebox.showwarning("Alerte",
            f"{expired} abonnements expir�s !")

check_abonnements()

# ===== BUTTONS =====
style = ttk.Style()
style.configure("TButton", font=("Segoe UI", 10), padding=6)

ttk.Button(app, text="Clients", width=30, command=window_clients).pack(pady=5)
ttk.Button(app, text="Abonnements", width=30, command=window_abonnements).pack(pady=5)
ttk.Button(app, text="Ventes", width=30, command=window_ventes).pack(pady=5)
ttk.Button(app, text="Rapport PDF", width=30, command=rapport_ventes_pdf).pack(pady=5)
ttk.Button(app, text="Quitter", width=30, command=app.destroy).pack(pady=10)

app.mainloop()
