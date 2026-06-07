import tkinter as tk
import sys
import os

# === FUNKCJA ODNALEZIENIA PLIKOW (DZIALA W .EXE I .PY) ===
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# === LICZBA DO ODGADNIĘCIA ===
WYLOSOWANA = 67
proby = 0

# === OKNO ===
okno = tk.Tk()
okno.title("Zgadnij Liczbę")
okno.attributes("-fullscreen", True)
okno.configure(bg="red")
okno.protocol("WM_DELETE_WINDOW", lambda: None)

ramka_glowna = tk.Frame(okno, bg="red")
ramka_glowna.place(relx=0.5, rely=0.5, anchor="center")

tytul = tk.Label(ramka_glowna, text="🔢 ZGADNIJ LICZBĘ (1-100) 🔢",
                 font=("Arial", 48, "bold"), bg="red", fg="white")
tytul.pack(pady=30)

komunikat = tk.Label(ramka_glowna, text="Wpisz liczbę i naciśnij SPRAWDŹ",
                     font=("Arial", 28), bg="red", fg="white")
komunikat.pack(pady=20)

entry = tk.Entry(ramka_glowna, font=("Arial", 36), justify="center",
                 width=10, bg="white", fg="black")
entry.pack(pady=20)
entry.focus()

def sprawdz():
    global proby
    try:
        strzal = int(entry.get())
        proby += 1
        if strzal < WYLOSOWANA:
            komunikat.config(text=f"📉 ZA MAŁO! (Próba: {proby})", fg="yellow")
            entry.delete(0, tk.END)
            entry.focus()
        elif strzal > WYLOSOWANA:
            komunikat.config(text=f"📈 ZA DUŻO! (Próba: {proby})", fg="yellow")
            entry.delete(0, tk.END)
            entry.focus()
        else:
            ramka_glowna.config(bg="green")
            okno.configure(bg="green")
            tytul.config(text="🎉 GRATULACJE! 🎉", fg="white", bg="green")
            komunikat.config(text=f"Odgadłeś {WYLOSOWANA} za {proby} razów!",
                             fg="white", bg="green", font=("Arial", 40, "bold"))
            entry.config(state="disabled", bg="white")
            przycisk.config(state="disabled", bg="gray")
            przycisk_wyjscie.pack(pady=30)
    except ValueError:
        komunikat.config(text="⚠️ TO NIE JEST LICZBA! Wpisz liczbę!", fg="red")
        entry.delete(0, tk.END)
        entry.focus()

przycisk = tk.Button(ramka_glowna, text="✅ SPRAWDŹ ✅",
                     font=("Arial", 28, "bold"), bg="orange", fg="black",
                     command=sprawdz, width=12, height=1)
przycisk.pack(pady=20)

entry.bind("<Return>", lambda event: sprawdz())

def zamknij():
    okno.destroy()

przycisk_wyjscie = tk.Button(ramka_glowna, text="🚪 ZAKOŃCZ PROGRAM 🚪",
                              font=("Arial", 24, "bold"), bg="darkgreen", fg="white",
                              command=zamknij, width=15, height=1)

okno.mainloop()