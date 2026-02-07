import tkinter as tk
import time
import threading
import random
import os
import socket
import platform

def odliczanie():
    for liczba in range(10, 0, -1):
        etykieta_liczba.config(text=str(liczba))
        time.sleep(1)
    etykieta_liczba.config(text="Koniec!")
    canvas.delete("smile")
    canvas.create_arc(80, 110, 120, 140, start=0, extent=180, style=tk.ARC, outline="black", width=2, tags="smile")

def zapisz_info_na_pulpit():
    sciezka = os.path.join(os.path.expanduser("~"), "Desktop", "ip_komputera.txt")
    ip_komputera = socket.gethostbyname(socket.gethostname())
    nazwa_komputera = platform.node()
    system_operacyjny = platform.system()
    wersja_systemu = platform.version()
    with open(sciezka, "w") as plik:
        plik.write("IP komputera: " + ip_komputera + "\n")
        plik.write("Nazwa komputera: " + nazwa_komputera + "\n")
        plik.write("System operacyjny: " + system_operacyjny + "\n")
        plik.write("Wersja systemu: " + wersja_systemu + "\n")

zapisz_info_na_pulpit()

okno = tk.Tk()
okno.title("Odliczanie z czaszką")
okno.attributes("-fullscreen", True)
okno.resizable(False, False)

canvas = tk.Canvas(okno, width=200, height=200, bg="white")
canvas.pack(pady=100)

canvas.create_oval(50, 50, 150, 150, fill="white", outline="black", width=3)
canvas.create_rectangle(90, 150, 110, 170, fill="black")
canvas.create_oval(70, 80, 90, 100, fill="black")
canvas.create_oval(110, 80, 130, 100, fill="black")
canvas.create_arc(80, 110, 120, 140, start=0, extent=-180, style=tk.ARC, outline="black", width=2, tags="smile")

etykieta_liczba = tk.Label(okno, text="10", font=("Arial", 24), fg="red")
etykieta_liczba.pack(pady=10)

watek = threading.Thread(target=odliczanie)
watek.start()

okno.mainloop()