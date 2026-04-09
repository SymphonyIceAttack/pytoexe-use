import re

# Verbessertes Pattern – erkennt auch leicht abweichende Formate
mac_pattern = re.compile(r'(?i)00[:\-]?1A[:\-]?79[:\-]?[0-9A-F]{2}[:\-]?[0-9A-F]{2}[:\-]?[0-9A-F]{2}')

def extract_macs(input_file: str, output_file: str):
    try:
        # Versucht verschiedene Encodings
        content = None
        for encoding in ['utf-8', 'utf-8-sig', 'windows-1252', 'latin1']:
            try:
                with open(input_file, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"✅ Datei mit Encoding '{encoding}' erfolgreich gelesen.")
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            print("❌ Konnte die Datei mit keinem Encoding lesen.")
            return

        # Alle passenden MAC-Adressen finden
        matches = mac_pattern.findall(content)

        # Normalisieren auf einheitliches Format mit Doppelpunkten und Großbuchstaben
        macs = []
        for m in matches:
            # Entferne alle Trennzeichen und formatiere neu
            clean = re.sub(r'[^0-9A-Fa-f]', '', m)
            if len(clean) == 12:
                formatted = ':'.join(clean[i:i+2] for i in range(0, 12, 2)).upper()
                macs.append(formatted)

        # Duplikate entfernen und sortieren
        macs = sorted(list(set(macs)))

        if not macs:
            print("⚠️  Keine MAC-Adressen mit Prefix 00:1A:79 gefunden.")
            print("   Tipp: Schicke mir bitte 5-10 Zeilen aus deiner Textdatei, damit ich das Pattern anpassen kann.")
            return

        # In Datei schreiben
        with open(output_file, 'w', encoding='utf-8') as f:
            for mac in macs:
                f.write(mac + '\n')

        print(f"✅ Erfolg! {len(macs)} eindeutige MAC-Adressen wurden gefunden und gespeichert.")
        print(f"   Ausgabedatei: {output_file}")

    except FileNotFoundError:
        print(f"❌ Datei nicht gefunden: {input_file}")
        print("   Bitte überprüfe den Dateipfad und den Dateinamen.")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")


# ====================== Hauptprogramm ======================
if __name__ == "__main__":
    print("=== MAC-Adressen Extraktor (00:1A:79) ===\n")

    input_file = input("Pfad zur Eingabedatei (z.B. liste.txt): ").strip()
    output_file = input("Pfad zur Ausgabedatei (z.B. macs.txt): ").strip()

    if not input_file or not output_file:
        print("❌ Bitte beide Dateinamen angeben.")
    else:
        extract_macs(input_file, output_file)

    input("\nDrücke Enter zum Beenden...")