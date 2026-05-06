import math
import tkinter as tk
from tkinter import ttk, messagebox

# -------------------------
# MATH
# -------------------------
def deg2rad(deg):
    return deg * math.pi / 180


def calculate(lat1, lon1, lat2, lon2):

    φ1 = deg2rad(lat1)
    φ2 = deg2rad(lat2)
    λ1 = deg2rad(lon1)
    λ2 = deg2rad(lon2)

    dφ = φ2 - φ1
    dλ = λ2 - λ1

    # HAVERSINE
    a = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
    c = 2 * math.asin(math.sqrt(a))

    R = 6371
    km = R * c
    nm = km / 1.852

    # BEARING
    x = math.sin(dλ) * math.cos(φ2)
    y = math.cos(φ1)*math.sin(φ2) - math.sin(φ1)*math.cos(φ2)*math.cos(dλ)

    θ = math.atan2(x, y)
    bearing = (math.degrees(θ) + 360) % 360

    return km, nm, bearing


# -------------------------
# GUI
# -------------------------
def compute():
    try:
        a = entry_a.get().replace(",", ".")
        b = entry_b.get().replace(",", ".")

        lat1, lon1 = map(float, a.split())
        lat2, lon2 = map(float, b.split())

        km, nm, brg = calculate(lat1, lon1, lat2, lon2)

        result.set(
            f"Distanza: {km:.2f} km / {nm:.2f} NM\n"
            f"Bearing: {brg:.2f}°"
        )

    except Exception:
        messagebox.showerror("Errore", "Formato non valido!\nUsa: 46.7, -27.5 oppure 46.7 -27.5")


# finestra
root = tk.Tk()
root.title("GPS Distance & Bearing")
root.geometry("350x200")

# input
ttk.Label(root, text="Punto A (lat lon):").pack()
entry_a = ttk.Entry(root, width=30)
entry_a.pack()

ttk.Label(root, text="Punto B (lat lon):").pack()
entry_b = ttk.Entry(root, width=30)
entry_b.pack()

# bottone
ttk.Button(root, text="Calcola", command=compute).pack(pady=10)

# risultato
result = tk.StringVar()
ttk.Label(root, textvariable=result, justify="center").pack()

root.mainloop()