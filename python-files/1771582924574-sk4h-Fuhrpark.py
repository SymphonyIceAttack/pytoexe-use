#!/usr/bin/env python3
"""
Text to Python Conversion
Generated: 2026-02-20T10:21:14.107Z
Total Lines: 188
"""

def process_text():
    """
    Process and analyze text data
    Returns: dictionary with text data and metadata
    """
    text_lines = [
    "import tkinter as tk",
    "from tkinter import messagebox",
    "import sqlite3",
    "from datetime import datetime",
    "DB_NAME = \"fuhrpark.db\"",
    "# -----------------------------",
    "# Datenbank erstellen",
    "# -----------------------------",
    "def init_db():",
    "    conn = sqlite3.connect(DB_NAME)",
    "    c = conn.cursor()",
    "    c.execute(\"\"\"",
    "    CREATE TABLE IF NOT EXISTS lkw (",
    "        lkw_id INTEGER PRIMARY KEY,",
    "        kennzeichen TEXT UNIQUE,",
    "        fahrzeugtyp TEXT,",
    "        hersteller TEXT,",
    "        modell TEXT,",
    "        baujahr INTEGER,",
    "        erstzulassung TEXT,",
    "        fahrgestellnummer TEXT,",
    "        aktueller_km INTEGER,",
    "        tuev_datum TEXT,",
    "        sp_datum TEXT",
    "    )",
    "    \"\"\")",
    "    c.execute(\"\"\"",
    "    CREATE TABLE IF NOT EXISTS reparaturen (",
    "        reparatur_id INTEGER PRIMARY KEY,",
    "        lkw_id INTEGER,",
    "        datum TEXT,",
    "        kilometerstand INTEGER,",
    "        beschreibung TEXT,",
    "        kosten REAL,",
    "        FOREIGN KEY(lkw_id) REFERENCES lkw(lkw_id)",
    "    )",
    "    \"\"\")",
    "    conn.commit()",
    "    conn.close()",
    "# -----------------------------",
    "# Status prüfen",
    "# -----------------------------",
    "def pruef_status(datum_string):",
    "    try:",
    "        pruefdatum = datetime.strptime(datum_string, \"%Y-%m-%d\")",
    "        heute = datetime.today()",
    "        diff = (pruefdatum - heute).days",
    "        if diff < 0:",
    "            return \"rot\"",
    "        elif diff <= 30:",
    "            return \"gelb\"",
    "        else:",
    "            return \"gruen\"",
    "    except:",
    "        return \"unbekannt\"",
    "# -----------------------------",
    "# Warnsystem (Gelb + Rot getrennt)",
    "# -----------------------------",
    "def pruefe_warnungen():",
    "    conn = sqlite3.connect(DB_NAME)",
    "    c = conn.cursor()",
    "    c.execute(\"SELECT kennzeichen, tuev_datum, sp_datum FROM lkw\")",
    "    daten = c.fetchall()",
    "    conn.close()",
    "    rot_liste = []",
    "    gelb_liste = []",
    "    for lkw in daten:",
    "        tuev_status = pruef_status(lkw[1])",
    "        sp_status = pruef_status(lkw[2])",
    "        if tuev_status == \"rot\":",
    "            rot_liste.append(f\"{lkw[0]} - TÜV\")",
    "        elif tuev_status == \"gelb\":",
    "            gelb_liste.append(f\"{lkw[0]} - TÜV\")",
    "        if sp_status == \"rot\":",
    "            rot_liste.append(f\"{lkw[0]} - SP\")",
    "        elif sp_status == \"gelb\":",
    "            gelb_liste.append(f\"{lkw[0]} - SP\")",
    "    meldung = \"\"",
    "    if rot_liste:",
    "        meldung += \"🔴 ÜBERFÄLLIG:\\n\"",
    "        meldung += \"\\n\".join(rot_liste)",
    "        meldung += \"\\n\\n\"",
    "    if gelb_liste:",
    "        meldung += \"🟡 BALD FÄLLIG (30 Tage):\\n\"",
    "        meldung += \"\\n\".join(gelb_liste)",
    "    if meldung:",
    "        messagebox.showwarning(\"Prüfungswarnung\", meldung)",
    "# -----------------------------",
    "# LKW hinzufügen",
    "# -----------------------------",
    "def neues_lkw():",
    "    fenster = tk.Toplevel(root)",
    "    fenster.title(\"Neuen LKW anlegen\")",
    "    felder = [",
    "        \"Kennzeichen\",",
    "        \"Fahrzeugtyp\",",
    "        \"Hersteller\",",
    "        \"Modell\",",
    "        \"Baujahr\",",
    "        \"Erstzulassung (YYYY-MM-DD)\",",
    "        \"Fahrgestellnummer\",",
    "        \"Aktueller KM\",",
    "        \"TÜV Datum (YYYY-MM-DD)\",",
    "        \"SP Datum (YYYY-MM-DD)\"",
    "    ]",
    "    entries = []",
    "    for feld in felder:",
    "        tk.Label(fenster, text=feld).pack()",
    "        e = tk.Entry(fenster)",
    "        e.pack()",
    "        entries.append(e)",
    "    def speichern():",
    "        conn = sqlite3.connect(DB_NAME)",
    "        c = conn.cursor()",
    "        c.execute(\"\"\"",
    "        INSERT INTO lkw (",
    "            kennzeichen, fahrzeugtyp, hersteller, modell,",
    "            baujahr, erstzulassung, fahrgestellnummer,",
    "            aktueller_km, tuev_datum, sp_datum",
    "        )",
    "        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    "        \"\"\", tuple(entry.get() for entry in entries))",
    "        conn.commit()",
    "        conn.close()",
    "        messagebox.showinfo(\"Erfolg\", \"LKW gespeichert!\")",
    "        fenster.destroy()",
    "        lade_lkw()",
    "    tk.Button(fenster, text=\"Speichern\", command=speichern).pack(pady=10)",
    "# -----------------------------",
    "# LKW laden mit Ampelanzeige",
    "# -----------------------------",
    "def lade_lkw():",
    "    for widget in frame_lkw.winfo_children():",
    "        widget.destroy()",
    "    conn = sqlite3.connect(DB_NAME)",
    "    c = conn.cursor()",
    "    c.execute(\"SELECT lkw_id, kennzeichen, tuev_datum, sp_datum FROM lkw\")",
    "    daten = c.fetchall()",
    "    conn.close()",
    "    for lkw in daten:",
    "        tuev_status = pruef_status(lkw[2])",
    "        sp_status = pruef_status(lkw[3])",
    "        symbol_tuev = \"🔴\" if tuev_status == \"rot\" else \"🟡\" if tuev_status == \"gelb\" else \"🟢\"",
    "        symbol_sp = \"🔴\" if sp_status == \"rot\" else \"🟡\" if sp_status == \"gelb\" else \"🟢\"",
    "        text = f\"{lkw[1]}   TÜV:{symbol_tuev}  SP:{symbol_sp}\"",
    "        tk.Button(frame_lkw,",
    "                  text=text,",
    "                  width=45,",
    "                  command=lambda lkw_id=lkw[0]: lkw_detail(lkw_id)",
    "                  ).pack(pady=2)",
    "# -----------------------------",
    "# Detailfenster",
    "# -----------------------------",
    "def lkw_detail(lkw_id):",
    "    fenster = tk.Toplevel(root)",
    "    fenster.title(\"LKW Detail\")",
    "    conn = sqlite3.connect(DB_NAME)",
    "    c = conn.cursor()",
    "    c.execute(\"SELECT * FROM lkw WHERE lkw_id=?\", (lkw_id,))",
    "    data = c.fetchone()",
    "    conn.close()",
    "    labels = [",
    "        f\"Kennzeichen: {data[1]}\",",
    "        f\"Fahrzeugtyp: {data[2]}\",",
    "        f\"Hersteller: {data[3]}\",",
    "        f\"Modell: {data[4]}\",",
    "        f\"Baujahr: {data[5]}\",",
    "        f\"Erstzulassung: {data[6]}\",",
    "        f\"Fahrgestellnummer: {data[7]}\",",
    "        f\"KM: {data[8]}\",",
    "        f\"TÜV: {data[9]}\",",
    "        f\"SP: {data[10]}\"",
    "    ]",
    "    for text in labels:",
    "        tk.Label(fenster, text=text).pack()",
    "# -----------------------------",
    "# Hauptfenster",
    "# -----------------------------",
    "root = tk.Tk()",
    "root.title(\"Fuhrpark Verwaltung\")",
    "root.geometry(\"700x550\")",
    "tk.Button(root, text=\"Neuen LKW anlegen\", command=neues_lkw).pack(pady=10)",
    "frame_lkw = tk.Frame(root)",
    "frame_lkw.pack()",
    "init_db()",
    "lade_lkw()",
    "pruefe_warnungen()",
    "root.mainloop()"
    ]
    
    # Calculate metadata
    metadata = {
        'total_lines': 188,
        'total_characters': 5743,
        'total_words': 510,
        'created_at': '2026-02-20T10:21:14.107Z',
        'version': '1.0'
    }
    
    # Calculate statistics
    line_lengths = [len(line) for line in text_lines]
    statistics = {
        'average_line_length': sum(line_lengths) // len(line_lengths) if line_lengths else 0,
        'longest_line': max(line_lengths) if line_lengths else 0,
        'shortest_line': min(line_lengths) if line_lengths else 0,
        'empty_lines': 42
    }
    
    return {
        'lines': text_lines,
        'metadata': metadata,
        'statistics': statistics
    }

def display_text(data):
    """Display text data with metadata"""
    print("Metadata:")
    for key, value in data['metadata'].items():
        print(f"  {key}: {value}")
    
    print("\nStatistics:")
    for key, value in data['statistics'].items():
        print(f"  {key}: {value}")
    
    print("\nText Lines:")
    for i, line in enumerate(data['lines'], 1):
        print(f"Line {i}: {line}")

if __name__ == "__main__":
    data = process_text()
    display_text(data)