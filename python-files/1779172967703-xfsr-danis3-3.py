import csv
import unicodedata
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


# =========================================================
# Felddefinitionen
# =========================================================

FIELDS = {
    "sid": "SchuelerIdentNummer",
    "nachname": "SchuelerNachname",
    "vornamen": "SchuelerVornamen",
    "rufname": "SchuelerRufname",
    "gebdat": "SchuelerGeburtsdatum",
    "gebort": "SchuelerGeburtsort",
    "strasse": "SchuelerStrasse",
    "plz": "SchuelerPlz",
    "ort": "SchuelerOrtsname",
    "klasse": "GruppeBezeichnung",
    "geschlecht": "SchuelerGeschlecht",
    "lehrer1": "Lehrernachname1",
    "lehrer2": "Lehrernachname2",
    "v1n": "Verantw1Nachname",
    "v1v": "Verantw1Vorname",
    "v2n": "Verantw2Nachname",
    "v2v": "Verantw2Vorname",
    "aufnahme": "SchuelerAufnahmedatum",
    "abgang": "SchuelerAbgangsdatum",
    "v1erz": "Verantw1Erziehungsberechtigt",
    "v2erz": "Verantw2Erziehungsberechtigt",
    "gebland": "SchuelerGeburtslandbezeichnungIso",
    "konfession": "SchuelerKonfession",
}


# =========================================================
# Hilfsfunktionen
# =========================================================

def val(d, key):
    return d.get(FIELDS[key], "").strip()


def klasse_umwandeln(klasse):

    klasse = klasse.strip()

    if len(klasse) > 1:

        if klasse[1] == "2":
            return "12"

        if klasse[1] == "3":
            return "13"

    return klasse


def normalize_text(text):

    ersetzungen = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "é": "e",
        "á": "a"
    }

    text = text.lower()

    for alt, neu in ersetzungen.items():
        text = text.replace(alt, neu)

    text = text.replace(" ", ".")

    text = unicodedata.normalize("NFKD", text)

    return text


def generate_username(rufname, nachname, verwendete_namen):

    rufname_norm = normalize_text(rufname)
    nachname_norm = normalize_text(nachname)

    # Standardname
    basis = f"{rufname_norm}.{nachname_norm}"

    if basis not in verwendete_namen:
        verwendete_namen.add(basis)
        return basis

    # Alternativen:
    # m.mustermann
    # ma.mustermann
    # max.mustermann2 usw.

    for i in range(1, len(rufname_norm) + 1):

        kandidat = (
            f"{rufname_norm[:i]}.{nachname_norm}"
        )

        if kandidat not in verwendete_namen:
            verwendete_namen.add(kandidat)
            return kandidat

    nummer = 2

    while True:

        kandidat = (
            f"{rufname_norm}.{nachname_norm}{nummer}"
        )

        if kandidat not in verwendete_namen:
            verwendete_namen.add(kandidat)
            return kandidat

        nummer += 1


def generate_email(username):

    return f"{username}@gym-sulingen.de"


def lese_csv(datei):

    with open(datei, encoding="utf-8-sig") as f:

        reader = csv.DictReader(f, delimiter=";")

        daten = []

        for row in reader:

            clean_row = {}

            for k, v in row.items():

                if k is None:
                    continue

                clean_row[k.strip()] = (v or "").strip()

            daten.append(clean_row)

        return daten


def schreibe_csv(datei, header, daten):

    with open(datei, "w", encoding="utf-8", newline="") as f:

        writer = csv.writer(f, delimiter=";")

        writer.writerow(header)

        writer.writerows(daten)


def dateiprefix():

    return datetime.now().strftime("%Y-%m-%d")


# =========================================================
# Filterfunktion für Abgänge
# =========================================================

def ist_abgaenger_in_vergangenheit(d):

    abgang = val(d, "abgang")

    # Kein Abgangsdatum -> Schüler bleibt erhalten
    if not abgang:
        return False

    try:

        # Erwartetes Format: TT.MM.JJJJ
        abgangsdatum = datetime.strptime(
            abgang,
            "%d.%m.%Y"
        ).date()

        # Nur ausschließen, wenn Datum in Vergangenheit liegt
        return abgangsdatum < datetime.today().date()

    except ValueError:

        # Ungültige Datumsformate behalten
        return False


# =========================================================
# Exportfunktionen
# =========================================================

def export_iserv_schueler(daten, zielordner, prefix):

    rows = []

    for d in daten:

        rows.append([
            val(d, "sid"),
            val(d, "nachname"),
            val(d, "rufname"),
            d["USERNAME"],
            klasse_umwandeln(val(d, "klasse"))
        ])

    schreibe_csv(
        zielordner / f"{prefix}_import_iserv_schueler.csv",
        [
            "SchuelerIdentNummer",
            "SchuelerNachname",
            "SchuelerRufname",
            "Benutzername",
            "GruppeBezeichnung"
        ],
        rows
    )


def export_iserv_eltern(daten, zielordner, prefix):

    rows = []

    for d in daten:

        if val(d, "v1v") and val(d, "v1n") and val(d, "v1erz"):

            rows.append([
                val(d, "sid"),
                val(d, "v1v"),
                val(d, "v1n")
            ])

        if val(d, "v2v") and val(d, "v2n") and val(d, "v2erz"):

            rows.append([
                val(d, "sid"),
                val(d, "v2v"),
                val(d, "v2n")
            ])

    schreibe_csv(
        zielordner / f"{prefix}_import_iserv_eltern.csv",
        [
            "SchuelerIdentNummer",
            "Verantw1Vorname",
            "Verantw1Nachname"
        ],
        rows
    )


def export_schulbuchausleihe(daten, zielordner, prefix):

    rows = []

    for d in daten:

        rows.append([
            val(d, "sid"),
            val(d, "nachname"),
            val(d, "rufname"),
            klasse_umwandeln(val(d, "klasse")),
            val(d, "gebdat")
        ])

    schreibe_csv(
        zielordner / f"{prefix}_import_iserv_schulbuchausleihe.csv",
        [
            "SchuelerIdentNummer",
            "SchuelerNachname",
            "SchuelerRufname",
            "GruppeBezeichnung",
            "SchuelerGeburtsdatum"
        ],
        rows
    )


def export_webuntis(daten, zielordner, prefix):

    rows = []

    for d in daten:

        email = generate_email(d["USERNAME"])

        rows.append([
            val(d, "sid"),
            val(d, "nachname"),
            val(d, "rufname"),
            d["USERNAME"],
            klasse_umwandeln(val(d, "klasse")),
            email,
            val(d, "aufnahme"),
            val(d, "abgang"),
            val(d, "gebdat"),
            val(d, "geschlecht")
        ])

    schreibe_csv(
        zielordner / f"{prefix}_import_webuntis.csv",
        [
            "SchuelerIdentNummer",
            "SchuelerNachname",
            "SchuelerRufname",
            "Benutzername",
            "GruppeBezeichnung",
            "SchuelerEMail",
            "Eintrittsdatum",
            "Austrittsdatum",
            "Geburtsdatum",
            "Geschlecht"
        ],
        rows
    )


def export_lebonline(daten, zielordner, prefix):

    rows = []

    for d in daten:

        gebort = val(d, "gebort")
        gebland = val(d, "gebland")

        if gebland and gebland != "Deutschland":
            gebort = f"{gebort} ({gebland})"

        getrennt = "NEIN"

        if val(d, "v2n") and val(d, "v2v"):

            adr1 = (
                d.get("Verantw1Strasse", ""),
                d.get("Verantw1Ortsname", ""),
                d.get("Verantw1PLZ", "")
            )

            adr2 = (
                d.get("Verantw2Strasse", ""),
                d.get("Verantw2Ortsname", ""),
                d.get("Verantw2PLZ", "")
            )

            if adr1 != adr2:
                getrennt = "JA"

        rows.append([
            val(d, "sid"),
            val(d, "nachname"),
            val(d, "vornamen"),
            val(d, "gebdat"),
            gebort,
            val(d, "strasse"),
            val(d, "plz"),
            val(d, "ort"),
            klasse_umwandeln(val(d, "klasse")),
            val(d, "geschlecht"),
            val(d, "lehrer1"),
            val(d, "lehrer2"),
            val(d, "v1n"),
            val(d, "v1v"),
            val(d, "v2n"),
            val(d, "v2v"),
            "",
            gebland,
            val(d, "konfession"),
            d.get("Verantw1Geschlecht", ""),
            d.get("Verantw1Namenszusatz", ""),
            d.get("Verantw1Strasse", ""),
            d.get("Verantw1Ortsname", ""),
            d.get("Verantw1PLZ", ""),
            d.get("Verantw1EMail", ""),
            d.get("Verantw1Telefon1", ""),
            d.get("Verantw2Geschlecht", ""),
            d.get("Verantw2Namenszusatz", ""),
            d.get("Verantw2Strasse", ""),
            d.get("Verantw2Ortsname", ""),
            d.get("Verantw2PLZ", ""),
            d.get("Verantw2EMail", ""),
            d.get("Verantw2Telefon1", ""),
            val(d, "v1erz"),
            val(d, "v2erz"),
            getrennt
        ])

    schreibe_csv(
        zielordner / f"{prefix}_import_lebonline.csv",
        [
            "Schüler-Nr.",
            "Nachname",
            "Vorname",
            "Geburtsdatum",
            "Geburtsort",
            "Straße",
            "PLZ",
            "Ort",
            "Klasse",
            "Geschlecht",
            "Klassenlehrer 1",
            "Klassenlehrer 2",
            "Verantw. 1 Nachname",
            "Verantw. 1 Vorname",
            "Verantw. 2 Nachname",
            "Verantw. 2 Vorname",
            "Förderbedarf",
            "Geburtsland",
            "Konfession",
            "Verantw. 1 Geschlecht",
            "Verantw. 1 Namenszusatz",
            "Verantw. 1 Straße",
            "Verantw. 1 Ort",
            "Verantw. 1 PLZ",
            "Verantw. 1 EMail",
            "Verantw. 1 Telefonnummer",
            "Verantw. 2 Geschlecht",
            "Verantw. 2 Namenszusatz",
            "Verantw. 2 Straße",
            "Verantw. 2 Ort",
            "Verantw. 2 PLZ",
            "Verantw. 2 EMail",
            "Verantw. 2 Telefonnummer",
            "Verantw. 1 Sorgeberechtigung",
            "Verantw. 2 Sorgeberechtigung",
            "Getrennt lebend"
        ],
        rows
    )


# =========================================================
# Hauptfunktion
# =========================================================

def konvertieren():

    datei = filedialog.askopenfilename(
        title="DaNiS-Export auswählen",
        filetypes=[("CSV-Dateien", "*.csv")]
    )

    if not datei:
        return

    try:

        daten = lese_csv(datei)

        # Schüler mit vergangenem Abgang entfernen
        daten = [
            d for d in daten
            if not ist_abgaenger_in_vergangenheit(d)
        ]

        # Benutzernamen erzeugen
        verwendete_namen = set()

        for d in daten:

            username = generate_username(
                val(d, "rufname"),
                val(d, "nachname"),
                verwendete_namen
            )

            d["USERNAME"] = username

        zielordner = Path(datei).parent

        prefix = dateiprefix()

        export_iserv_schueler(daten, zielordner, prefix)
        export_iserv_eltern(daten, zielordner, prefix)
        export_schulbuchausleihe(daten, zielordner, prefix)
        export_webuntis(daten, zielordner, prefix)
        export_lebonline(daten, zielordner, prefix)

        messagebox.showinfo(
            "Erfolg",
            "Alle Dateien wurden erfolgreich erstellt."
        )

    except Exception as e:

        messagebox.showerror(
            "Fehler",
            str(e)
        )


# =========================================================
# GUI
# =========================================================

root = tk.Tk()

root.title("DaNiS-Konvertierungstool")
root.geometry("600x350")
root.resizable(False, False)

title = tk.Label(
    root,
    text="DaNiS-Konvertierungstool",
    font=("Arial", 18, "bold")
)

title.pack(pady=20)

subtitle = tk.Label(
    root,
    text="Version 3.3",
    font=("Arial", 10)
)

subtitle.pack()

info = tk.Label(
    root,
    text=(
        "Konvertiert DaNiS-Exporte für:\n"
        "- IServ\n"
        "- WebUntis\n"
        "- Schulbuchausleihe\n"
        "- LEB online\n"
        "\n"
        "(C) Henning Moje, 2026\n"
    ),
    justify="center",
    font=("Arial", 11)
)

info.pack(pady=20)

button = ttk.Button(
    root,
    text="DaNiS-CSV auswählen und konvertieren",
    command=konvertieren
)

button.pack(pady=20)

exit_button = ttk.Button(
    root,
    text="Beenden",
    command=root.destroy
)

exit_button.pack(pady=10)

root.mainloop()