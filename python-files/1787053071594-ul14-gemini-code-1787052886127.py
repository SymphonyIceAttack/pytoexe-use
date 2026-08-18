import os
import glob
import pandas as pd

def konwertuj_csv_do_excel(katalog):
    # Utworzenie ścieżki wyszukiwania plików .csv w podanym katalogu
    sciezka_wyszukiwania = os.path.join(katalog, '*.csv')
    pliki_csv = glob.glob(sciezka_wyszukiwania)
    
    if not pliki_csv:
        print(f"Nie znaleziono żadnych plików .csv w katalogu: {katalog}")
        return

    print(f"Znaleziono {len(pliki_csv)} plików .csv. Rozpoczynam konwersję...\n")
    
    for plik_csv in pliki_csv:
        try:
            # Wczytanie pliku CSV do obiektu DataFrame (zakładamy standardowe kodowanie i separator)
            df = pd.read_csv(plik_csv)
            
            # Stworzenie nazwy dla nowego pliku Excel (.xlsx)
            nazwa_bazowa = os.path.splitext(plik_csv)[0]
            plik_excel = f"{nazwa_bazowa}.xlsx"
            
            # Zapis do formatu Excel bez kolumny indeksu
            df.to_excel(plik_excel, index=False, engine='openpyxl')
            
            print(f"Pomyślnie skonwertowano: {os.path.basename(plik_csv)} -> {os.path.basename(plik_excel)}")
            
        except Exception as e:
            print(f"Błąd podczas konwersji pliku {os.path.basename(plik_csv)}: {e}")

if __name__ == "__main__":
    # Domyślnie używa obecnego katalogu roboczego ('.')
    # Możesz podać tutaj inną ścieżkę, np. katalog = 'C:/moje_pliki'
    katalog_docelowy = '.' 
    
    konwertuj_csv_do_excel(katalog_docelowy)
    print("\nProces zakończony.")