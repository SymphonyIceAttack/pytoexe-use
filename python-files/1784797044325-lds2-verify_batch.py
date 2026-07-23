import os
import csv
import sys
from datetime import datetime
from pathlib import Path
from collections import OrderedDict

# Importy z pyhanko
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko.sign.validation.errors import SignatureValidationError
from pyhanko.pdf_utils.reader import PdfFileReader

def extract_signature_info(pdf_path):
    """
    Weryfikuje pierwszy podpis w dokumencie i zwraca dane.
    Zabezpieczona przed błędami typu OrderedDict i nietypową strukturą certyfikatów.
    """
    result = {
        'status': 'ERROR',
        'signer': 'N/A',
        'signing_time': 'N/A',
        'cert_subject': 'N/A',
        'message': ''
    }

    try:
        with open(pdf_path, 'rb') as f:
            reader = PdfFileReader(f)
            
            # Pobierz wszystkie pola podpisu
            sig_fields = reader.embedded_signatures
            
            if not sig_fields:
                result['status'] = 'NO_SIGNATURE'
                result['message'] = 'Brak podpisu w pliku'
                return result

            # Weryfikujemy pierwszy podpis
            sig = sig_fields[0]
            
            # Walidacja podpisu
            try:
                val_report = validate_pdf_signature(sig)
                
                if val_report.intact and val_report.valid:
                    result['status'] = 'VALID'
                elif val_report.intact and not val_report.valid:
                    result['status'] = 'INVALID_SIGNATURE'
                else:
                    result['status'] = 'MODIFIED' # Dokument zmieniony po podpisie
                
                result['message'] = f"Integrity: {val_report.intact}, Valid: {val_report.valid}"
            except Exception as val_err:
                # Jeśli sama walidacja rzuci błąd, zapisujemy go, ale próbujemy dalej wyciągnąć metadane
                result['status'] = 'VALIDATION_ERROR'
                result['message'] = f"Błąd walidacji: {str(val_err)}"

            # Bezpieczne pobieranie danych certyfikatu
            try:
                cert = sig.signer_cert
                # Pobieramy surowe dane tematu (native)
                subject_native = cert.subject.native
                
                # --- Obsługa Common Name (CN) ---
                cn_attrs = subject_native.get('common_name', [])
                
                # Helper do wyciągania stringa z zagnieżdżeń
                def extract_first_string(val):
                    if isinstance(val, str):
                        return val
                    if isinstance(val, (list, tuple)):
                        return extract_first_string(val[0]) if val else None
                    if isinstance(val, (dict, OrderedDict)):
                        for v in val.values():
                            res = extract_first_string(v)
                            if res:
                                return res
                    return str(val) if val is not None else None

                raw_cn = extract_first_string(cn_attrs)
                result['signer'] = raw_cn if raw_cn else "Nieznany"
                
                # --- Obsługa pełnego tematu certyfikatu (cert_subject) ---
                try:
                    # Próba użycia wbudowanej, wygodnej metody
                    result['cert_subject'] = cert.subject.human_friendly
                except Exception:
                    # Fallback: ręczna konstrukcja stringa
                    if isinstance(subject_native, (dict, OrderedDict)):
                        parts = []
                        for key, val in subject_native.items():
                            if isinstance(val, list):
                                val_str = ", ".join(str(v) for v in val)
                            elif isinstance(val, (dict, OrderedDict)):
                                val_str = str(val)
                            else:
                                val_str = str(val)
                            parts.append(f"{key}={val_str}")
                        result['cert_subject'] = ", ".join(parts)
                    else:
                        result['cert_subject'] = str(subject_native)

            except Exception as cert_err:
                result['signer'] = 'Błąd odczytu CN'
                result['cert_subject'] = f'Błąd odczytu tematu: {str(cert_err)}'

            # --- Czas podpisu ---
            signing_time = sig.signing_time
            if signing_time:
                try:
                    result['signing_time'] = signing_time.isoformat()
                except Exception:
                    result['signing_time'] = str(signing_time)
            else:
                result['signing_time'] = 'Nieokreślony'

    except SignatureValidationError as e:
        result['status'] = 'VALIDATION_ERROR'
        result['message'] = str(e)
    except Exception as e:
        result['status'] = 'READ_ERROR'
        result['message'] = str(e)

    return result

def main():
    # Konfiguracja ścieżek
    print("=== Weryfikator Podpisów PDF (Bezpieczna Wersja) ===")
    
    # 1. Pobranie folderu źródłowego
    source_folder = input("Podaj ścieżkę do folderu z plikami PDF (np. T:\\Dokumenty): ").strip().strip('"')
    
    if not os.path.isdir(source_folder):
        print(f"Błąd: Folder '{source_folder}' nie istnieje.")
        input("Naciśnij Enter, aby wyjść...")
        return

    # 2. Pobranie nazwy pliku wynikowego (NOWOŚĆ)
    output_filename = input("Podaj nazwę pliku wynikowego (np. raport_kwietien.csv): ").strip().strip('"')
    
    if not output_filename:
        print("Błąd: Nie podano nazwy pliku.")
        input("Naciśnij Enter, aby wyjść...")
        return
        
    # Automatyczne dopisanie rozszerzenia .csv, jeśli użytkownik go pominął
    if not output_filename.lower().endswith('.csv'):
        output_filename += '.csv'
        
    output_file = output_filename
    
    # Sprawdzenie, czy plik już istnieje (opcjonalne ostrzeżenie)
    if os.path.exists(output_file):
        overwrite = input(f"Plik '{output_file}' już istnieje. Czy chcesz go nadpisać? (t/n): ").strip().lower()
        if overwrite != 't':
            print("Anulowano operację.")
            input("Naciśnij Enter, aby wyjść...")
            return

    print(f"Rozpoczynanie skanowania folderu: {source_folder}...")
    print(f"Wyniki zostaną zapisane w: {output_file}")
    print("To może potrwać chwilę przy dużej liczbie plików.")

    # Nagłówki CSV
    fieldnames = ['nazwa_pliku', 'status', 'podpisujacy', 'czas_podpisu', 'temat_certyfikatu', 'szczegoly']
    
    files_processed = 0
    errors_count = 0

    try:
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            # Przejście przez wszystkie pliki w folderze i podfolderach
            for root, dirs, files in os.walk(source_folder):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        full_path = os.path.join(root, file)
                        files_processed += 1
                        
                        print(f"[{files_processed}] Sprawdzanie: {file}...", end='\r')
                        
                        data = extract_signature_info(full_path)
                        
                        # Zapis do CSV
                        row = {
                            'nazwa_pliku': file,
                            'status': data['status'],
                            'podpisujacy': data['signer'],
                            'czas_podpisu': data['signing_time'],
                            'temat_certyfikatu': data['cert_subject'],
                            'szczegoly': data['message']
                        }
                        writer.writerow(row)
                        
                        if data['status'] not in ['VALID', 'NO_SIGNATURE']:
                            errors_count += 1

        print("\n" + "="*60)
        print(f"Zakończono pomyślnie!")
        print(f"Przetworzono plików PDF: {files_processed}")
        print(f"Znaleziono problemów/nieprawidłowych podpisów: {errors_count}")
        print(f"Wyniki zapisano w pliku: {os.path.abspath(output_file)}")
        print("="*60)
        
    except Exception as e:
        print(f"\nKrytyczny błąd podczas zapisu lub przetwarzania: {e}")
    
    input("Naciśnij Enter, aby zamknąć okno...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProces przerwany przez użytkownika.")
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd krytyczny: {e}")
        input("Naciśnij Enter, aby wyjść...")