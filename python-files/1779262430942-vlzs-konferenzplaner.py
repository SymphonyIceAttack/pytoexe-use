import csv
from itertools import combinations
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os

# =========================
# Einstellungen
# =========================

NICHT_RELEVANTE_FAECHER = {"AG", "AB", "FÖ", "VF", "DAZ"}

JAHRGANGS_LEHRER = {
    "Gth": range(5, 8),
    "Moj": range(8, 11),
}

# =========================
# GUI
# =========================

class LehrerGUI:

    def __init__(self, root):

        self.root = root
        self.root.title("Lehrkräfte Analyse (Kli / Tis XOR)")
        self.root.geometry("1000x700")

        self.datei = ""

        # =========================
        # Top Bar
        # =========================

        top = tk.Frame(root)
        top.pack(fill="x", padx=10, pady=10)

        self.label = tk.Label(top, text="Keine Datei ausgewählt")
        self.label.pack(side="left", fill="x", expand=True)

        tk.Button(top, text="CSV wählen", command=self.datei_waehlen).pack(side="left", padx=5)
        tk.Button(top, text="Start", bg="#4CAF50", fg="white", command=self.start).pack(side="left", padx=5)

        # =========================
        # XOR Auswahl (Radiobuttons)
        # =========================

        option_frame = tk.Frame(root)
        option_frame.pack(fill="x", padx=10)

        tk.Label(option_frame, text="11. Klassen Betreuung:").pack(side="left")

        self.betreuung = tk.StringVar(value="Kli")

        tk.Radiobutton(
            option_frame,
            text="Kli",
            variable=self.betreuung,
            value="Kli"
        ).pack(side="left", padx=5)

        tk.Radiobutton(
            option_frame,
            text="Tis",
            variable=self.betreuung,
            value="Tis"
        ).pack(side="left", padx=5)

        # =========================
        # Tabs
        # =========================

        self.nb = ttk.Notebook(root)
        self.nb.pack(fill="both", expand=True)

        self.tab1 = tk.Text(self.nb)
        self.tab2 = tk.Text(self.nb)

        self.nb.add(self.tab1, text="Klassen")
        self.nb.add(self.tab2, text="Konferenzen")

    # =========================
    # Datei wählen
    # =========================

    def datei_waehlen(self):

        file = filedialog.askopenfilename(
            filetypes=[("CSV Dateien", "*.csv")]
        )

        if file:
            self.datei = file
            self.label.config(text=os.path.basename(file))

    # =========================
    # Jahrgangslogik
    # =========================

    def jahrgang(self, klasse):

        try:
            nummer = int("".join([c for c in klasse if c.isdigit()]))
        except:
            return None

        if nummer == 11:
            return self.betreuung.get()

        for lehrer, bereich in JAHRGANGS_LEHRER.items():
            if nummer in bereich:
                return lehrer

        return None

    # =========================
    # CSV laden
    # =========================

    def lade_daten(self):

        daten = []

        with open(self.datei, newline="", encoding="cp1252") as f:

            sample = f.read(2048)
            f.seek(0)

            delimiter = ";" if sample.count(";") > sample.count(",") else ","

            reader = csv.DictReader(f, delimiter=delimiter)

            for row in reader:

                lehrer = row.get("Lehrer")
                fach = row.get("Fach")
                klassen = row.get("Klasse(n)")

                if not lehrer or not fach or not klassen:
                    continue

                lehrer = lehrer.strip()
                fach = fach.strip().upper()
                klassen = klassen.strip()

                if fach in NICHT_RELEVANTE_FAECHER:
                    continue

                klassen_liste = [
                    k.strip()
                    for k in klassen.split(",")
                    if k.strip()
                ]

                for k in klassen_liste:

                    if k.startswith(("12", "13")):
                        continue

                    daten.append((k, lehrer))

        return daten

    # =========================
    # Start
    # =========================

    def start(self):

        try:

            if not self.datei:
                messagebox.showerror("Fehler", "Keine Datei gewählt")
                return

            daten = self.lade_daten()

            if not daten:
                messagebox.showerror("Fehler", "Keine Daten gefunden")
                return

            ergebnis = {}

            for klasse, lehrer in daten:
                ergebnis.setdefault(klasse, set()).add(lehrer)

            for k in ergebnis:

                extra = self.jahrgang(k)

                if extra:
                    ergebnis[k].add(extra)

            # =========================
            # Ausgabe Klassen
            # =========================

            self.tab1.delete("1.0", tk.END)

            for k in sorted(ergebnis):

                self.tab1.insert(
                    tk.END,
                    f"{k}: {', '.join(sorted(ergebnis[k]))}\n\n"
                )

            # =========================
            # Konferenzen
            # =========================

            self.tab2.delete("1.0", tk.END)

            paare = []

            for (k1, l1), (k2, l2) in combinations(ergebnis.items(), 2):

                if l1.isdisjoint(l2):
                    paare.append((k1, k2))

            if paare:

                for a, b in paare:
                    self.tab2.insert(tk.END, f"{a} ↔ {b}\n")

            else:
                self.tab2.insert(tk.END, "Keine disjunkten Klassen.")

            messagebox.showinfo(
                "Fertig",
                f"Auswertung abgeschlossen!\nKlassen: {len(ergebnis)}"
            )

        except Exception as e:
            messagebox.showerror("Fehler", str(e))


# =========================
# Start
# =========================

if __name__ == "__main__":

    root = tk.Tk()
    app = LehrerGUI(root)
    root.mainloop()