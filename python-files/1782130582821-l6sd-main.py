"""
GTIC Maroc — Gestion des Demandes d'Achat
Application de bureau PySide6
"""

import sys
import os
import shutil
import sqlite3
import json
from datetime import date, datetime
from pathlib import Path

# ─── Chemins ────────────────────────────────────────────────────────────────

def get_app_data_dir():
    """Retourne le dossier de données utilisateur."""
    if sys.platform == 'win32':
        local_appdata = os.getenv('LOCALAPPDATA')
        if local_appdata is None:
            local_appdata = os.path.join(os.path.expanduser('~'), 'AppData', 'Local')
        app_data = Path(local_appdata) / 'GTIC'
    else:
        # Autres OS (Linux, Mac)
        app_data = Path(os.path.expanduser('~')) / '.gtic'
    app_data.mkdir(parents=True, exist_ok=True)
    return app_data

def resource_path(relative_path):
    """Retourne le chemin absolu pour un fichier dans l'EXE ou en développement."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # On est dans un EXE compilé par PyInstaller
        base_path = Path(sys._MEIPASS)
    else:
        # En développement, on utilise le répertoire du script
        base_path = Path(__file__).resolve().parent
    return base_path / relative_path

# Dossiers de données
DATA_DIR = get_app_data_dir()
DB_PATH = DATA_DIR / "gtic_demandes.db"
DOCS_DIR = DATA_DIR / "documents"
DOCS_DIR.mkdir(exist_ok=True)

# Logo (optionnel)
LOGO_PATH = resource_path("assets/logo.png")
if not LOGO_PATH.exists():
    LOGO_PATH = None   # Si le logo n'existe pas, on ne l'utilise pas

# ─── Palette ─────────────────────────────────────────────────────────────────
NAVY    = "#1a2e6c"
NAVY2   = "#243580"
RED     = "#cc1e2a"
BG      = "#f0f2f5"
WHITE   = "#ffffff"
BORDER  = "#dde2ef"
MUTED   = "#6b7a99"
TEXT    = "#0f1c3f"
SUCCESS = "#10b981"
WARNING = "#f59e0b"
DANGER  = "#ef4444"
INFO    = "#2e7dd4"

# ... (le reste de votre code inchangé)
# ... (le reste de votre code inchangé)

STATUT_COLORS = {
    "En attente":  ("#fffbeb", "#92400e", "#fde68a"),
    "En cours":    ("#eff6ff", "#1e40af", "#bfdbfe"),
    "Approuvé":    ("#ecfdf5", "#065f46", "#6ee7b7"),
    "Rejeté":      ("#fef2f2", "#991b1b", "#fca5a5"),
}
PRIORITE_COLORS = {
    "Normale":  ("#f8fafc", "#475569", "#cbd5e1"),
    "Urgente":  ("#fff7ed", "#9a3412", "#fdba74"),
    "Critique": ("#fef2f2", "#7f1d1d", "#fca5a5"),
}

# ─── Base de données ─────────────────────────────────────────────────────────

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS demandes (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        numero      TEXT NOT NULL UNIQUE,
        date_creation TEXT NOT NULL,
        date_limite   TEXT NOT NULL,
        demandeur     TEXT NOT NULL,
        departement   TEXT NOT NULL,
        projet        TEXT NOT NULL,
        objet         TEXT NOT NULL,
        statut        TEXT NOT NULL DEFAULT 'En attente',
        priorite      TEXT NOT NULL DEFAULT 'Normale',
        fournisseur   TEXT DEFAULT '',
        observations  TEXT DEFAULT '',
        montant_total REAL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS articles (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        demande_id  INTEGER NOT NULL,
        designation TEXT NOT NULL,
        quantite    REAL NOT NULL,
        unite       TEXT NOT NULL,
        prix_unitaire REAL NOT NULL,
        FOREIGN KEY (demande_id) REFERENCES demandes(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS documents (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        demande_id INTEGER NOT NULL,
        nom        TEXT NOT NULL,
        chemin     TEXT NOT NULL,
        taille     TEXT DEFAULT '',
        date_ajout TEXT DEFAULT '',
        FOREIGN KEY (demande_id) REFERENCES demandes(id) ON DELETE CASCADE
    );
    """)
    con.commit()

    # Données de démonstration
    if cur.execute("SELECT COUNT(*) FROM demandes").fetchone()[0] == 0:
        _seed_demo(cur)
    con.commit()
    con.close()

def _seed_demo(cur):
    demandes = [
        ("DA-2024-001", "2024-06-01", "2024-06-15", "Ahmed Benali",
         "Travaux Publics", "Route Nationale RN7 — Lot 3",
         "Achat de matériaux de construction", "Approuvé", "Urgente",
         "LAFARGE Maroc", "Livraison urgente requise.", 54100.0),
        ("DA-2024-002", "2024-06-05", "2024-06-20", "Fatima Zahra Moussaoui",
         "Bureau d'Études", "Pont Oued Tensift",
         "Équipements topographiques", "En cours", "Normale",
         "Topogéo Maroc", "Vérifier la garantie.", 87400.0),
        ("DA-2024-003", "2024-06-08", "2024-06-12", "Khalid Tazi",
         "Logistique", "Barrage Sidi Driss",
         "Carburant et lubrifiants pour engins", "En attente", "Critique",
         "AFRIQUIA SMDC", "Délai dépassé — traitement prioritaire.", 71500.0),
        ("DA-2024-004", "2024-06-10", "2024-07-01", "Nadia El Idrissi",
         "Qualité & Sécurité", "Tous chantiers",
         "Équipements de protection individuelle (EPI)", "Rejeté", "Normale",
         "PROSAFETY Maroc", "Rejeté — dépasse le budget.", 41500.0),
        ("DA-2024-005", "2024-06-12", "2024-06-30", "Youssef Benkirane",
         "Informatique", "Infrastructure SI",
         "Matériel informatique", "En attente", "Normale",
         "DELL Technologies Maroc", "", 80700.0),
    ]
    for d in demandes:
        cur.execute(
            "INSERT INTO demandes (numero,date_creation,date_limite,demandeur,"
            "departement,projet,objet,statut,priorite,fournisseur,observations,montant_total)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", d)
        did = cur.lastrowid
        if did == 1:
            cur.executemany(
                "INSERT INTO articles (demande_id,designation,quantite,unite,prix_unitaire) VALUES (?,?,?,?,?)",
                [(did,"Ciment Portland CEM I 52.5",500,"Sac",85),
                 (did,"Sable fin 0/2",20,"M³",180),
                 (did,"Gravier 8/15",30,"M³",210)])
        elif did == 2:
            cur.executemany(
                "INSERT INTO articles (demande_id,designation,quantite,unite,prix_unitaire) VALUES (?,?,?,?,?)",
                [(did,"Station totale Leica TS16",1,"Unité",85000),
                 (did,"Trépied aluminium",2,"Unité",1200)])

def get_con():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con

def fetch_all_demandes(search="", statut="Tous", priorite="Tous"):
    con = get_con()
    q = "SELECT * FROM demandes WHERE 1=1"
    params = []
    if search:
        q += " AND (numero LIKE ? OR objet LIKE ? OR demandeur LIKE ? OR projet LIKE ? OR departement LIKE ?)"
        s = f"%{search}%"
        params += [s, s, s, s, s]
    if statut != "Tous":
        q += " AND statut = ?"
        params.append(statut)
    if priorite != "Tous":
        q += " AND priorite = ?"
        params.append(priorite)
    q += " ORDER BY date_creation DESC"
    rows = con.execute(q, params).fetchall()
    con.close()
    return [dict(r) for r in rows]

def fetch_demande(did):
    con = get_con()
    d = dict(con.execute("SELECT * FROM demandes WHERE id=?", (did,)).fetchone())
    d["articles"] = [dict(r) for r in con.execute("SELECT * FROM articles WHERE demande_id=?", (did,)).fetchall()]
    d["documents"] = [dict(r) for r in con.execute("SELECT * FROM documents WHERE demande_id=?", (did,)).fetchall()]
    con.close()
    return d

def save_demande(data: dict, articles: list, doc_paths: list) -> int:
    con = get_con()
    cur = con.cursor()
    total = sum(a["quantite"] * a["prix_unitaire"] for a in articles)
    if data.get("id"):
        cur.execute(
            "UPDATE demandes SET numero=?,date_limite=?,demandeur=?,departement=?,projet=?,"
            "objet=?,statut=?,priorite=?,fournisseur=?,observations=?,montant_total=? WHERE id=?",
            (data["numero"], data["date_limite"], data["demandeur"], data["departement"],
             data["projet"], data["objet"], data["statut"], data["priorite"],
             data["fournisseur"], data["observations"], total, data["id"]))
        did = data["id"]
        cur.execute("DELETE FROM articles WHERE demande_id=?", (did,))
    else:
        cur.execute(
            "INSERT INTO demandes (numero,date_creation,date_limite,demandeur,departement,projet,"
            "objet,statut,priorite,fournisseur,observations,montant_total) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (data["numero"], data["date_creation"], data["date_limite"], data["demandeur"],
             data["departement"], data["projet"], data["objet"], data["statut"],
             data["priorite"], data["fournisseur"], data["observations"], total))
        did = cur.lastrowid

    for a in articles:
        cur.execute(
            "INSERT INTO articles (demande_id,designation,quantite,unite,prix_unitaire) VALUES (?,?,?,?,?)",
            (did, a["designation"], a["quantite"], a["unite"], a["prix_unitaire"]))

    for path in doc_paths:
        src = Path(path)
        dst = DOCS_DIR / f"{did}_{src.name}"
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
        taille = f"{dst.stat().st_size // 1024} KB" if dst.exists() else ""
        cur.execute(
            "INSERT INTO documents (demande_id,nom,chemin,taille,date_ajout) VALUES (?,?,?,?,?)",
            (did, src.name, str(dst), taille, date.today().isoformat()))

    con.commit()
    con.close()
    return did

def delete_demande(did):
    con = get_con()
    con.execute("DELETE FROM demandes WHERE id=?", (did,))
    con.commit()
    con.close()

def delete_document(doc_id, chemin):
    con = get_con()
    con.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    con.commit()
    con.close()
    try:
        Path(chemin).unlink(missing_ok=True)
    except Exception:
        pass

def next_numero():
    con = get_con()
    count = con.execute("SELECT COUNT(*) FROM demandes").fetchone()[0]
    con.close()
    year = date.today().year
    return f"DA-{year}-{count + 1:03d}"

def get_stats():
    con = get_con()
    stats = {}
    stats["total"] = con.execute("SELECT COUNT(*) FROM demandes").fetchone()[0]
    for s in ("En attente", "En cours", "Approuvé", "Rejeté"):
        stats[s] = con.execute("SELECT COUNT(*) FROM demandes WHERE statut=?", (s,)).fetchone()[0]
    stats["montant_total"] = con.execute("SELECT COALESCE(SUM(montant_total),0) FROM demandes").fetchone()[0]
    today = date.today().isoformat()
    stats["overdue"] = con.execute(
        "SELECT COUNT(*) FROM demandes WHERE statut IN ('En attente','En cours') AND date_limite < ?", (today,)
    ).fetchone()[0]
    stats["critique"] = con.execute(
        "SELECT COUNT(*) FROM demandes WHERE priorite='Critique' AND statut='En attente'"
    ).fetchone()[0]
    con.close()
    return stats

def get_alerts():
    con = get_con()
    today = date.today().isoformat()
    overdue = [dict(r) for r in con.execute(
        "SELECT * FROM demandes WHERE statut IN ('En attente','En cours') AND date_limite < ? ORDER BY date_limite",
        (today,)).fetchall()]
    critique = [dict(r) for r in con.execute(
        "SELECT * FROM demandes WHERE priorite='Critique' AND statut='En attente'"
    ).fetchall()]
    con.close()
    return overdue, critique

# ─── Styles helpers ──────────────────────────────────────────────────────────

def btn_style(bg, fg=WHITE, hover=None):
    h = hover or bg
    return f"""
    QPushButton {{
        background: {bg}; color: {fg};
        border: none; border-radius: 6px;
        padding: 7px 18px; font-weight: 600; font-size: 13px;
    }}
    QPushButton:hover {{ background: {h}; }}
    QPushButton:pressed {{ opacity: 0.85; }}
    """

def card_style():
    return f"""
    QFrame {{
        background: {WHITE}; border-radius: 10px;
        border: 1px solid {BORDER};
    }}
    """

def input_style():
    return f"""
    QLineEdit, QComboBox, QTextEdit, QDateEdit, QDoubleSpinBox, QSpinBox {{
        background: #f4f6fb; border: 1px solid {BORDER};
        border-radius: 6px; padding: 6px 10px;
        color: {TEXT}; font-size: 13px;
    }}
    QLineEdit:focus, QComboBox:focus, QTextEdit:focus,
    QDateEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
        border: 1.5px solid {NAVY}; background: {WHITE};
    }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox::down-arrow {{ width: 10px; }}
    """

# ─── Badge label ─────────────────────────────────────────────────────────────

class Badge(QLabel):
    def __init__(self, text, bg, fg, border):
        super().__init__(text)
        self.setStyleSheet(f"""
            QLabel {{
                background: {bg}; color: {fg};
                border: 1px solid {border};
                border-radius: 4px; padding: 2px 8px;
                font-size: 11px; font-weight: 700;
            }}
        """)
        self.setFixedHeight(22)

# ─── KPI Card ────────────────────────────────────────────────────────────────

class KpiCard(QFrame):
    def __init__(self, label, value, sub="", color=NAVY):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: {WHITE}; border-radius: 10px;
                border: 1px solid {BORDER};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)

        dot = QFrame()
        dot.setFixedSize(44, 44)
        dot.setStyleSheet(f"background: {color}; border-radius: 10px; border: none;")
        layout.addWidget(dot)

        right = QVBoxLayout()
        right.setSpacing(2)
        val_lbl = QLabel(str(value))
        val_lbl.setStyleSheet(f"color: {TEXT}; font-size: 20px; font-weight: 800; border: none; background: transparent;")
        lbl_lbl = QLabel(label)
        lbl_lbl.setStyleSheet(f"color: {MUTED}; font-size: 10px; font-weight: 700; text-transform: uppercase; border: none; background: transparent;")
        right.addWidget(val_lbl)
        right.addWidget(lbl_lbl)
        if sub:
            sub_lbl = QLabel(sub)
            sub_lbl.setStyleSheet(f"color: {MUTED}; font-size: 10px; border: none; background: transparent;")
            right.addWidget(sub_lbl)
        layout.addLayout(right)
        layout.addStretch()

# ─── Formulaire Demande ───────────────────────────────────────────────────────

DEPARTEMENTS = [
    "Travaux Publics", "Bureau d'Études", "Logistique",
    "Qualité & Sécurité", "Informatique", "Finances", "RH", "Direction Générale",
]
STATUTS   = ["En attente", "En cours", "Approuvé", "Rejeté"]
PRIORITES = ["Normale", "Urgente", "Critique"]

class ArticleRow(QWidget):
    removed = Signal(object)

    def __init__(self, data=None):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.desig = QLineEdit()
        self.desig.setPlaceholderText("Désignation")
        self.qty   = QDoubleSpinBox(); self.qty.setRange(0, 999999); self.qty.setValue(1)
        self.unite = QLineEdit(); self.unite.setText("Unité"); self.unite.setFixedWidth(70)
        self.pu    = QDoubleSpinBox(); self.pu.setRange(0, 9999999); self.pu.setDecimals(2)
        self.total_lbl = QLabel("0.00 MAD")
        self.total_lbl.setFixedWidth(100)
        self.total_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.total_lbl.setStyleSheet(f"color: {NAVY}; font-weight: 700; font-size: 12px;")

        self.qty.valueChanged.connect(self._update)
        self.pu.valueChanged.connect(self._update)

        for w in (self.desig, self.qty, self.unite, self.pu):
            w.setStyleSheet(input_style())

        rm = QPushButton("✕")
        rm.setFixedSize(26, 26)
        rm.setStyleSheet(f"QPushButton {{ background: #fee2e2; color: {RED}; border-radius: 5px; border: none; font-weight: 700; }}")
        rm.clicked.connect(lambda: self.removed.emit(self))

        layout.addWidget(self.desig, 3)
        layout.addWidget(self.qty, 1)
        layout.addWidget(self.unite)
        layout.addWidget(self.pu, 1)
        layout.addWidget(self.total_lbl)
        layout.addWidget(rm)

        if data:
            self.desig.setText(data.get("designation",""))
            self.qty.setValue(data.get("quantite",1))
            self.unite.setText(data.get("unite","Unité"))
            self.pu.setValue(data.get("prix_unitaire",0))
        self._update()

    def _update(self):
        t = self.qty.value() * self.pu.value()
        self.total_lbl.setText(f"{t:,.2f} MAD")

    def to_dict(self):
        return {
            "designation": self.desig.text(),
            "quantite": self.qty.value(),
            "unite": self.unite.text(),
            "prix_unitaire": self.pu.value(),
        }


class DemandeDialog(QDialog):
    def __init__(self, parent=None, demande_id=None):
        super().__init__(parent)
        self.demande_id = demande_id
        self.new_doc_paths = []
        self.article_rows = []
        self.existing_docs = []

        title = "Modifier la demande" if demande_id else "Nouvelle Demande d'Achat"
        self.setWindowTitle(title)
        self.setMinimumSize(820, 680)
        self.setStyleSheet(f"QDialog {{ background: {BG}; }}")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(52)
        header.setStyleSheet(f"background: {NAVY}; border-radius: 0px;")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(20, 0, 20, 0)
        lbl = QLabel(title)
        lbl.setStyleSheet("color: white; font-size: 14px; font-weight: 700;")
        h_lay.addWidget(lbl)
        root.addWidget(header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        content = QWidget()
        content.setStyleSheet(f"background: {BG};")
        self.form_layout = QVBoxLayout(content)
        self.form_layout.setContentsMargins(20, 16, 20, 16)
        self.form_layout.setSpacing(14)
        scroll.setWidget(content)
        root.addWidget(scroll)

        self._build_form()

        # Buttons
        btn_bar = QFrame()
        btn_bar.setStyleSheet(f"background: {WHITE}; border-top: 1px solid {BORDER};")
        btn_lay = QHBoxLayout(btn_bar)
        btn_lay.setContentsMargins(20, 10, 20, 10)
        btn_lay.addStretch()
        cancel = QPushButton("Annuler")
        cancel.setStyleSheet(btn_style("#e5e7eb", TEXT))
        cancel.clicked.connect(self.reject)
        save = QPushButton("💾  Enregistrer")
        save.setStyleSheet(btn_style(NAVY))
        save.clicked.connect(self._save)
        btn_lay.addWidget(cancel)
        btn_lay.addWidget(save)
        root.addWidget(btn_bar)

        if demande_id:
            self._load(demande_id)

    def _section(self, title):
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {NAVY}; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;")
        line = QFrame(); line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {BORDER};")
        self.form_layout.addWidget(lbl)
        self.form_layout.addWidget(line)

    def _row(self, *widgets):
        row = QHBoxLayout()
        row.setSpacing(12)
        for w in widgets:
            row.addWidget(w)
        self.form_layout.addLayout(row)

    def _field(self, label, widget):
        container = QVBoxLayout()
        container.setSpacing(4)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {MUTED}; font-size: 11px; font-weight: 700; text-transform: uppercase;")
        container.addWidget(lbl)
        container.addWidget(widget)
        w = QWidget(); w.setLayout(container)
        return w

    def _build_form(self):
        ist = input_style()

        self._section("Informations générales")

        self.f_demandeur = QLineEdit(); self.f_demandeur.setPlaceholderText("Nom complet"); self.f_demandeur.setStyleSheet(ist)
        self.f_dept = QComboBox(); self.f_dept.addItems(DEPARTEMENTS); self.f_dept.setStyleSheet(ist)
        self._row(self._field("Demandeur *", self.f_demandeur), self._field("Département *", self.f_dept))

        self.f_projet = QLineEdit(); self.f_projet.setPlaceholderText("Nom du projet ou chantier"); self.f_projet.setStyleSheet(ist)
        self._row(self._field("Projet / Chantier *", self.f_projet))

        self.f_objet = QLineEdit(); self.f_objet.setPlaceholderText("Description courte"); self.f_objet.setStyleSheet(ist)
        self._row(self._field("Objet de la demande *", self.f_objet))

        self.f_fournisseur = QLineEdit(); self.f_fournisseur.setPlaceholderText("Fournisseur suggéré"); self.f_fournisseur.setStyleSheet(ist)
        self.f_date_limite = QDateEdit(QDate.currentDate()); self.f_date_limite.setCalendarPopup(True); self.f_date_limite.setStyleSheet(ist)
        self._row(self._field("Fournisseur", self.f_fournisseur), self._field("Date limite *", self.f_date_limite))

        self.f_statut = QComboBox(); self.f_statut.addItems(STATUTS); self.f_statut.setStyleSheet(ist)
        self.f_priorite = QComboBox(); self.f_priorite.addItems(PRIORITES); self.f_priorite.setStyleSheet(ist)
        self._row(self._field("Statut", self.f_statut), self._field("Priorité", self.f_priorite))

        # Articles
        self._section("Articles / Fournitures")

        # Column headers
        hdr = QHBoxLayout(); hdr.setSpacing(6)
        for txt, stretch in [("Désignation",3),("Quantité",1),("Unité",None),("Prix unitaire (MAD)",1),("Total",None),("",None)]:
            l = QLabel(txt)
            l.setStyleSheet(f"color: {MUTED}; font-size: 10px; font-weight: 700; text-transform: uppercase;")
            if stretch:
                hdr.addWidget(l, stretch)
            elif txt == "Unité":
                l.setFixedWidth(70); hdr.addWidget(l)
            elif txt == "Total":
                l.setFixedWidth(100); hdr.addWidget(l)
            else:
                l.setFixedWidth(26); hdr.addWidget(l)
        self.form_layout.addLayout(hdr)

        self.articles_container = QVBoxLayout()
        self.articles_container.setSpacing(6)
        self.form_layout.addLayout(self.articles_container)

        add_art = QPushButton("＋  Ajouter un article")
        add_art.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {NAVY}; border: 1.5px dashed {NAVY};
            border-radius: 6px; padding: 7px; font-weight: 600; font-size: 12px; }}
            QPushButton:hover {{ background: #eff3fb; }}
        """)
        add_art.clicked.connect(self._add_article_row)
        self.form_layout.addWidget(add_art)

        # Documents
        self._section("Documents joints")

        self.docs_container = QVBoxLayout()
        self.docs_container.setSpacing(4)
        self.form_layout.addLayout(self.docs_container)

        add_doc = QPushButton("📎  Ajouter des documents (PDF, Word, Excel…)")
        add_doc.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {MUTED}; border: 1.5px dashed {BORDER};
            border-radius: 6px; padding: 10px; font-size: 12px; }}
            QPushButton:hover {{ border-color: {NAVY}; color: {NAVY}; background: #eff3fb; }}
        """)
        add_doc.clicked.connect(self._add_docs)
        self.form_layout.addWidget(add_doc)

        # Observations
        self._section("Observations")
        self.f_obs = QTextEdit(); self.f_obs.setPlaceholderText("Commentaires, instructions spéciales…")
        self.f_obs.setFixedHeight(80); self.f_obs.setStyleSheet(ist)
        self.form_layout.addWidget(self.f_obs)
        self.form_layout.addStretch()

    def _add_article_row(self, data=None):
        row = ArticleRow(data)
        row.removed.connect(self._remove_article_row)
        self.article_rows.append(row)
        self.articles_container.addWidget(row)

    def _remove_article_row(self, row):
        self.articles_container.removeWidget(row)
        self.article_rows.remove(row)
        row.deleteLater()

    def _add_docs(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Sélectionner des documents", "",
            "Documents (*.pdf *.docx *.doc *.xlsx *.xls *.png *.jpg *.jpeg *.txt)")
        for p in paths:
            self.new_doc_paths.append(p)
            self._add_doc_item(Path(p).name, p, new=True)

    def _add_doc_item(self, name, path_or_id, new=False, doc_id=None):
        row = QFrame()
        row.setStyleSheet(f"QFrame {{ background: #f8fafc; border-radius: 6px; border: 1px solid {BORDER}; }}")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(10, 6, 10, 6)
        lbl = QLabel(f"📄  {name}")
        lbl.setStyleSheet(f"color: {TEXT}; font-size: 12px; border: none; background: transparent;")
        lay.addWidget(lbl)
        lay.addStretch()
        if not new and doc_id:
            open_btn = QPushButton("Ouvrir")
            open_btn.setStyleSheet(btn_style(NAVY, WHITE))
            open_btn.setFixedHeight(26)
            open_btn.clicked.connect(lambda _, p=path_or_id: self._open_doc(p))
            lay.addWidget(open_btn)
        rm = QPushButton("✕")
        rm.setFixedSize(26, 26)
        rm.setStyleSheet(f"QPushButton {{ background: #fee2e2; color: {RED}; border-radius: 5px; border: none; font-weight: 700; }}")
        if new:
            rm.clicked.connect(lambda _, r=row, p=path_or_id: self._remove_new_doc(r, p))
        else:
            rm.clicked.connect(lambda _, r=row, did=doc_id, p=path_or_id: self._remove_existing_doc(r, did, p))
        lay.addWidget(rm)
        self.docs_container.addWidget(row)

    def _open_doc(self, path):
        import subprocess
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible d'ouvrir le fichier:\n{e}")

    def _remove_new_doc(self, row, path):
        if path in self.new_doc_paths:
            self.new_doc_paths.remove(path)
        self.docs_container.removeWidget(row)
        row.deleteLater()

    def _remove_existing_doc(self, row, doc_id, chemin):
        delete_document(doc_id, chemin)
        self.docs_container.removeWidget(row)
        row.deleteLater()

    def _load(self, did):
        d = fetch_demande(did)
        self.f_demandeur.setText(d["demandeur"])
        idx = self.f_dept.findText(d["departement"])
        if idx >= 0: self.f_dept.setCurrentIndex(idx)
        self.f_projet.setText(d["projet"])
        self.f_objet.setText(d["objet"])
        self.f_fournisseur.setText(d["fournisseur"] or "")
        self.f_date_limite.setDate(QDate.fromString(d["date_limite"], "yyyy-MM-dd"))
        idx2 = self.f_statut.findText(d["statut"])
        if idx2 >= 0: self.f_statut.setCurrentIndex(idx2)
        idx3 = self.f_priorite.findText(d["priorite"])
        if idx3 >= 0: self.f_priorite.setCurrentIndex(idx3)
        self.f_obs.setPlainText(d["observations"] or "")

        for a in d["articles"]:
            self._add_article_row(a)

        for doc in d["documents"]:
            self.existing_docs.append(doc)
            self._add_doc_item(doc["nom"], doc["chemin"], new=False, doc_id=doc["id"])

    def _save(self):
        if not self.f_demandeur.text().strip():
            QMessageBox.warning(self, "Champ requis", "Le nom du demandeur est obligatoire."); return
        if not self.f_objet.text().strip():
            QMessageBox.warning(self, "Champ requis", "L'objet de la demande est obligatoire."); return

        data = {
            "id": self.demande_id,
            "numero": next_numero() if not self.demande_id else self._get_numero(),
            "date_creation": date.today().isoformat(),
            "date_limite": self.f_date_limite.date().toString("yyyy-MM-dd"),
            "demandeur": self.f_demandeur.text().strip(),
            "departement": self.f_dept.currentText(),
            "projet": self.f_projet.text().strip(),
            "objet": self.f_objet.text().strip(),
            "statut": self.f_statut.currentText(),
            "priorite": self.f_priorite.currentText(),
            "fournisseur": self.f_fournisseur.text().strip(),
            "observations": self.f_obs.toPlainText().strip(),
        }
        articles = [r.to_dict() for r in self.article_rows if r.desig.text().strip()]
        save_demande(data, articles, self.new_doc_paths)
        self.accept()

    def _get_numero(self):
        con = get_con()
        row = con.execute("SELECT numero FROM demandes WHERE id=?", (self.demande_id,)).fetchone()
        con.close()
        return row["numero"] if row else next_numero()


# ─── Détail Dialog ────────────────────────────────────────────────────────────

class DetailDialog(QDialog):
    def __init__(self, parent, demande_id):
        super().__init__(parent)
        d = fetch_demande(demande_id)
        self.setWindowTitle(f"Détail — {d['numero']}")
        self.setMinimumSize(700, 580)
        self.setStyleSheet(f"QDialog {{ background: {BG}; }}")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        header = QFrame()
        header.setFixedHeight(52)
        header.setStyleSheet(f"background: {NAVY};")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(20, 0, 20, 0)
        lbl = QLabel(f"{d['numero']}  ·  {d['objet']}")
        lbl.setStyleSheet("color: white; font-size: 13px; font-weight: 700;")
        h_lay.addWidget(lbl)
        root.addWidget(header)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        content = QWidget(); content.setStyleSheet(f"background: {BG};")
        lay = QVBoxLayout(content); lay.setContentsMargins(20, 16, 20, 16); lay.setSpacing(14)
        scroll.setWidget(content)
        root.addWidget(scroll)

        # Overdue alert
        today = date.today().isoformat()
        if d["statut"] in ("En attente","En cours") and d["date_limite"] < today:
            alert = QFrame()
            alert.setStyleSheet("QFrame { background: #fef2f2; border: 1px solid #fca5a5; border-radius: 8px; }")
            al = QHBoxLayout(alert); al.setContentsMargins(12,8,12,8)
            al.addWidget(QLabel("⚠️  Délai dépassé — action requise immédiatement"))
            lay.addWidget(alert)

        # Info grid
        info_frame = QFrame()
        info_frame.setStyleSheet(card_style())
        info_lay = QGridLayout(info_frame); info_lay.setContentsMargins(16,14,16,14); info_lay.setSpacing(12)
        fields = [
            ("Demandeur", d["demandeur"]),
            ("Département", d["departement"]),
            ("Date création", d["date_creation"]),
            ("Date limite", d["date_limite"]),
            ("Fournisseur", d["fournisseur"] or "—"),
            ("Montant total", f"{d['montant_total']:,.2f} MAD"),
        ]
        for i, (k, v) in enumerate(fields):
            cell = QFrame(); cell.setStyleSheet(f"QFrame {{ background: #f4f6fb; border-radius: 8px; border: none; }}")
            cl = QVBoxLayout(cell); cl.setContentsMargins(10,8,10,8); cl.setSpacing(2)
            kl = QLabel(k); kl.setStyleSheet(f"color: {MUTED}; font-size: 10px; font-weight: 700; text-transform: uppercase;")
            vl = QLabel(v); vl.setStyleSheet(f"color: {TEXT}; font-size: 13px; font-weight: 600;")
            cl.addWidget(kl); cl.addWidget(vl)
            info_lay.addWidget(cell, i // 3, i % 3)
        lay.addWidget(info_frame)

        # Badges
        badge_row = QHBoxLayout()
        bg_s, fg_s, bd_s = STATUT_COLORS.get(d["statut"], ("#f8fafc","#475569","#cbd5e1"))
        bg_p, fg_p, bd_p = PRIORITE_COLORS.get(d["priorite"], ("#f8fafc","#475569","#cbd5e1"))
        badge_row.addWidget(Badge(d["statut"], bg_s, fg_s, bd_s))
        badge_row.addWidget(Badge(d["priorite"], bg_p, fg_p, bd_p))
        badge_row.addWidget(QLabel(d["projet"]))
        badge_row.addStretch()
        lay.addLayout(badge_row)

        # Articles table
        if d["articles"]:
            self._section(lay, "Articles / Fournitures")
            tbl = QTableWidget(len(d["articles"]), 5)
            tbl.setHorizontalHeaderLabels(["Désignation","Qté","Unité","Prix unitaire","Montant"])
            tbl.setStyleSheet(f"""
                QTableWidget {{ background: {WHITE}; gridline-color: {BORDER}; border: 1px solid {BORDER}; border-radius: 8px; font-size: 12px; }}
                QHeaderView::section {{ background: #f4f6fb; color: {MUTED}; font-size: 10px; font-weight: 700;
                    padding: 6px; border: none; border-bottom: 1px solid {BORDER}; text-transform: uppercase; }}
                QTableWidget::item {{ padding: 6px; }}
            """)
            tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            tbl.verticalHeader().setVisible(False)
            tbl.setSelectionMode(QTableWidget.NoSelection)
            tbl.setEditTriggers(QTableWidget.NoEditTriggers)
            for i, a in enumerate(d["articles"]):
                total = a["quantite"] * a["prix_unitaire"]
                tbl.setItem(i, 0, QTableWidgetItem(a["designation"]))
                tbl.setItem(i, 1, QTableWidgetItem(str(a["quantite"])))
                tbl.setItem(i, 2, QTableWidgetItem(a["unite"]))
                tbl.setItem(i, 3, QTableWidgetItem(f"{a['prix_unitaire']:,.2f} MAD"))
                tbl.setItem(i, 4, QTableWidgetItem(f"{total:,.2f} MAD"))
            tbl.setFixedHeight(min(len(d["articles"]) * 34 + 34, 220))
            lay.addWidget(tbl)

            total_lbl = QLabel(f"Total: {d['montant_total']:,.2f} MAD")
            total_lbl.setAlignment(Qt.AlignRight)
            total_lbl.setStyleSheet(f"color: {NAVY}; font-weight: 800; font-size: 14px;")
            lay.addWidget(total_lbl)

        # Documents
        if d["documents"]:
            self._section(lay, "Documents joints")
            for doc in d["documents"]:
                row = QFrame()
                row.setStyleSheet(f"QFrame {{ background: #f8fafc; border-radius: 6px; border: 1px solid {BORDER}; }}")
                rl = QHBoxLayout(row); rl.setContentsMargins(12,7,12,7)
                rl.addWidget(QLabel(f"📄  {doc['nom']}"))
                rl.addStretch()
                size_lbl = QLabel(doc["taille"]); size_lbl.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
                date_lbl = QLabel(doc["date_ajout"]); date_lbl.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
                open_btn = QPushButton("📂 Ouvrir")
                open_btn.setStyleSheet(btn_style(NAVY)); open_btn.setFixedHeight(28)
                open_btn.clicked.connect(lambda _, p=doc["chemin"]: self._open(p))
                rl.addWidget(size_lbl); rl.addWidget(date_lbl); rl.addWidget(open_btn)
                lay.addWidget(row)

        if d["observations"]:
            obs = QFrame()
            obs.setStyleSheet("QFrame { background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; }")
            ol = QHBoxLayout(obs); ol.setContentsMargins(12,10,12,10)
            ol.addWidget(QLabel(f"<b>Observations:</b> {d['observations']}"))
            lay.addWidget(obs)

        lay.addStretch()

        btn_bar = QFrame()
        btn_bar.setStyleSheet(f"background: {WHITE}; border-top: 1px solid {BORDER};")
        bl = QHBoxLayout(btn_bar); bl.setContentsMargins(20,10,20,10)
        bl.addStretch()
        close = QPushButton("Fermer"); close.setStyleSheet(btn_style(NAVY))
        close.clicked.connect(self.accept)
        bl.addWidget(close)
        root.addWidget(btn_bar)

    def _section(self, lay, title):
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {NAVY}; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;")
        lay.addWidget(lbl)

    def _open(self, path):
        import subprocess
        try:
            if sys.platform == "win32": os.startfile(path)
            elif sys.platform == "darwin": subprocess.run(["open", path])
            else: subprocess.run(["xdg-open", path])
        except Exception as e:
            QMessageBox.warning(self, "Erreur", str(e))


# ─── Page: Demandes ───────────────────────────────────────────────────────────

class DemandesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {WHITE}; border-radius: 10px; border: 1px solid {BORDER};")
        tb = QHBoxLayout(toolbar); tb.setContentsMargins(12,10,12,10); tb.setSpacing(10)

        self.search = QLineEdit(); self.search.setPlaceholderText("🔍  Rechercher par numéro, objet, demandeur…")
        self.search.setStyleSheet(input_style() + "QLineEdit { min-width: 280px; }")
        self.search.textChanged.connect(self.refresh)

        self.f_statut = QComboBox(); self.f_statut.addItems(["Tous statuts"] + STATUTS)
        self.f_statut.setStyleSheet(input_style()); self.f_statut.currentTextChanged.connect(self.refresh)

        self.f_priorite = QComboBox(); self.f_priorite.addItems(["Toutes priorités"] + PRIORITES)
        self.f_priorite.setStyleSheet(input_style()); self.f_priorite.currentTextChanged.connect(self.refresh)

        add_btn = QPushButton("＋  Nouvelle demande"); add_btn.setStyleSheet(btn_style(NAVY))
        add_btn.clicked.connect(self._add)

        tb.addWidget(self.search, 3)
        tb.addWidget(self.f_statut)
        tb.addWidget(self.f_priorite)
        tb.addStretch()
        tb.addWidget(add_btn)
        lay.addWidget(toolbar)

        # Table
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "N° DA", "Date créa.", "Date limite", "Demandeur",
            "Objet", "Statut", "Priorité", "Montant", "Actions"
        ])
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {WHITE}; gridline-color: {BORDER};
                border: 1px solid {BORDER}; border-radius: 10px;
                font-size: 12px; selection-background-color: #eff3fb;
            }}
            QHeaderView::section {{
                background: #f4f6fb; color: {MUTED};
                font-size: 10px; font-weight: 700; padding: 8px;
                border: none; border-bottom: 1px solid {BORDER};
                text-transform: uppercase;
            }}
            QTableWidget::item {{ padding: 6px; border-bottom: 1px solid {BORDER}; }}
        """)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setDefaultSectionSize(110)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.verticalHeader().setDefaultSectionSize(40)
        lay.addWidget(self.table)

        self.refresh()

    def refresh(self):
        search = self.search.text()
        statut = self.f_statut.currentText()
        priorite = self.f_priorite.currentText()
        if statut == "Tous statuts": statut = "Tous"
        if priorite == "Toutes priorités": priorite = "Tous"

        rows = fetch_all_demandes(search, statut, priorite)
        today = date.today().isoformat()
        self.table.setRowCount(len(rows))

        for i, d in enumerate(rows):
            overdue = d["statut"] in ("En attente","En cours") and d["date_limite"] < today

            num = QTableWidgetItem(d["numero"])
            num.setForeground(QColor(NAVY))
            num.setFont(QFont("Courier New", 11, QFont.Bold))
            self.table.setItem(i, 0, num)

            self.table.setItem(i, 1, QTableWidgetItem(d["date_creation"]))

            dl = QTableWidgetItem(d["date_limite"])
            if overdue:
                dl.setForeground(QColor(RED))
                dl.setFont(QFont("", -1, QFont.Bold))
            self.table.setItem(i, 2, dl)

            dem = QTableWidgetItem(d["demandeur"])
            self.table.setItem(i, 3, dem)
            self.table.setItem(i, 4, QTableWidgetItem(d["objet"]))

            # Statut badge in cell
            statut_item = QTableWidgetItem(d["statut"])
            bg_s, fg_s, _ = STATUT_COLORS.get(d["statut"], ("#f8fafc","#475569","#cbd5e1"))
            statut_item.setBackground(QColor(bg_s))
            statut_item.setForeground(QColor(fg_s))
            statut_item.setFont(QFont("", 11, QFont.Bold))
            self.table.setItem(i, 5, statut_item)

            prio_item = QTableWidgetItem(d["priorite"])
            bg_p, fg_p, _ = PRIORITE_COLORS.get(d["priorite"], ("#f8fafc","#475569","#cbd5e1"))
            prio_item.setBackground(QColor(bg_p))
            prio_item.setForeground(QColor(fg_p))
            prio_item.setFont(QFont("", 11, QFont.Bold))
            self.table.setItem(i, 6, prio_item)

            montant = QTableWidgetItem(f"{d['montant_total']:,.2f} MAD")
            montant.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            montant.setFont(QFont("", -1, QFont.Bold))
            self.table.setItem(i, 7, montant)

            if overdue:
                for col in range(8):
                    item = self.table.item(i, col)
                    if item:
                        item.setBackground(QColor("#fff1f2"))

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(4)

            eye = QPushButton("👁")
            eye.setToolTip("Voir détail")
            eye.setFixedSize(28, 28)
            eye.setStyleSheet(f"QPushButton {{ background: #eff3fb; border-radius: 5px; border: none; font-size: 13px; }} QPushButton:hover {{ background: {NAVY}; }}")
            eye.clicked.connect(lambda _, did=d["id"]: self._view(did))

            edit = QPushButton("✏️")
            edit.setToolTip("Modifier")
            edit.setFixedSize(28, 28)
            edit.setStyleSheet(f"QPushButton {{ background: #f0fdf4; border-radius: 5px; border: none; font-size: 13px; }} QPushButton:hover {{ background: #bbf7d0; }}")
            edit.clicked.connect(lambda _, did=d["id"]: self._edit(did))

            delete = QPushButton("🗑")
            delete.setToolTip("Supprimer")
            delete.setFixedSize(28, 28)
            delete.setStyleSheet(f"QPushButton {{ background: #fff1f2; border-radius: 5px; border: none; font-size: 13px; }} QPushButton:hover {{ background: #fca5a5; }}")
            delete.clicked.connect(lambda _, did=d["id"], num=d["numero"]: self._delete(did, num))

            action_layout.addWidget(eye)
            action_layout.addWidget(edit)
            action_layout.addWidget(delete)
            self.table.setCellWidget(i, 8, action_widget)

    def _add(self):
        dlg = DemandeDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh()

    def _edit(self, did):
        dlg = DemandeDialog(self, did)
        if dlg.exec() == QDialog.Accepted:
            self.refresh()

    def _view(self, did):
        dlg = DetailDialog(self, did)
        dlg.exec()

    def _delete(self, did, numero):
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer définitivement la demande <b>{numero}</b> ?<br>Cette action est irréversible.",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            delete_demande(did)
            self.refresh()


# ─── Page: Dashboard ──────────────────────────────────────────────────────────

class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        self.kpi_layout = QGridLayout()
        self.kpi_layout.setSpacing(12)
        lay.addLayout(self.kpi_layout)

        # Status bars
        status_frame = QFrame(); status_frame.setStyleSheet(card_style())
        sf_lay = QVBoxLayout(status_frame); sf_lay.setContentsMargins(16,14,16,14); sf_lay.setSpacing(10)
        title = QLabel("Répartition par statut")
        title.setStyleSheet(f"color: {NAVY}; font-size: 14px; font-weight: 700;")
        sf_lay.addWidget(title)
        self.status_bars_lay = QVBoxLayout(); self.status_bars_lay.setSpacing(8)
        sf_lay.addLayout(self.status_bars_lay)
        lay.addWidget(status_frame)

        # Recent table
        recent_frame = QFrame(); recent_frame.setStyleSheet(card_style())
        rf_lay = QVBoxLayout(recent_frame); rf_lay.setContentsMargins(16,14,16,14); rf_lay.setSpacing(10)
        rt = QLabel("Demandes récentes"); rt.setStyleSheet(f"color: {NAVY}; font-size: 14px; font-weight: 700;")
        rf_lay.addWidget(rt)
        self.recent_table = QTableWidget(0, 5)
        self.recent_table.setHorizontalHeaderLabels(["N°","Objet","Demandeur","Statut","Montant"])
        self.recent_table.setStyleSheet(f"""
            QTableWidget {{ background: {WHITE}; gridline-color: {BORDER}; border: none; font-size: 12px; }}
            QHeaderView::section {{ background: #f4f6fb; color: {MUTED}; font-size: 10px; font-weight: 700;
                padding: 6px; border: none; border-bottom: 1px solid {BORDER}; }}
            QTableWidget::item {{ padding: 6px; border-bottom: 1px solid {BORDER}; }}
        """)
        self.recent_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.recent_table.setSelectionMode(QTableWidget.NoSelection)
        self.recent_table.setFixedHeight(200)
        rf_lay.addWidget(self.recent_table)
        lay.addWidget(recent_frame)
        lay.addStretch()

        self.refresh()

    def refresh(self):
        stats = get_stats()

        # Clear KPI
        while self.kpi_layout.count():
            item = self.kpi_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        kpis = [
            ("Total demandes", stats["total"], "", NAVY),
            ("En attente", stats["En attente"], "À traiter", WARNING),
            ("Approuvées", stats["Approuvé"], "", SUCCESS),
            ("En retard", stats["overdue"], "Délai dépassé", DANGER),
            ("Critiques", stats["critique"], "", "#f97316"),
            ("Budget total", f"{stats['montant_total']:,.0f} MAD", "", INFO),
        ]
        for i, (label, val, sub, color) in enumerate(kpis):
            card = KpiCard(label, val, sub, color)
            self.kpi_layout.addWidget(card, 0, i)

        # Status bars
        while self.status_bars_lay.count():
            item = self.status_bars_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        total = stats["total"] or 1
        color_map = {"En attente": WARNING, "En cours": INFO, "Approuvé": SUCCESS, "Rejeté": DANGER}
        for s in ("En attente","En cours","Approuvé","Rejeté"):
            count = stats[s]
            pct = int(count / total * 100)
            row = QHBoxLayout(); row.setSpacing(10)
            lbl = QLabel(s); lbl.setFixedWidth(100)
            lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {TEXT};")
            bar = QProgressBar(); bar.setValue(pct); bar.setFixedHeight(10)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{ background: #e5e7eb; border-radius: 5px; border: none; }}
                QProgressBar::chunk {{ background: {color_map[s]}; border-radius: 5px; }}
            """)
            cnt = QLabel(f"{count}  ({pct}%)"); cnt.setFixedWidth(80)
            cnt.setStyleSheet(f"font-size: 11px; color: {MUTED};")
            row.addWidget(lbl); row.addWidget(bar, 1); row.addWidget(cnt)
            w = QWidget(); w.setLayout(row)
            self.status_bars_lay.addWidget(w)

        # Recent rows
        rows = fetch_all_demandes()[:6]
        self.recent_table.setRowCount(len(rows))
        for i, d in enumerate(rows):
            num = QTableWidgetItem(d["numero"])
            num.setForeground(QColor(NAVY)); num.setFont(QFont("Courier New", 11, QFont.Bold))
            self.recent_table.setItem(i, 0, num)
            self.recent_table.setItem(i, 1, QTableWidgetItem(d["objet"]))
            self.recent_table.setItem(i, 2, QTableWidgetItem(d["demandeur"]))
            si = QTableWidgetItem(d["statut"])
            bg_s, fg_s, _ = STATUT_COLORS.get(d["statut"], ("#f8fafc","#475569","#cbd5e1"))
            si.setBackground(QColor(bg_s)); si.setForeground(QColor(fg_s))
            si.setFont(QFont("", 11, QFont.Bold))
            self.recent_table.setItem(i, 3, si)
            m = QTableWidgetItem(f"{d['montant_total']:,.2f} MAD")
            m.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            m.setFont(QFont("", -1, QFont.Bold))
            self.recent_table.setItem(i, 4, m)


# ─── Page: Rapports ────────────────────────────────────────────────────────────

class RapportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        grid = QGridLayout(); grid.setSpacing(12)
        lay.addLayout(grid)

        # By departement
        self.dept_frame = QFrame(); self.dept_frame.setStyleSheet(card_style())
        df = QVBoxLayout(self.dept_frame); df.setContentsMargins(16,14,16,14); df.setSpacing(8)
        df.addWidget(self._title("Par département"))
        self.dept_lay = QVBoxLayout(); self.dept_lay.setSpacing(6)
        df.addLayout(self.dept_lay)
        grid.addWidget(self.dept_frame, 0, 0)

        # By statut
        self.stat_frame = QFrame(); self.stat_frame.setStyleSheet(card_style())
        sf = QVBoxLayout(self.stat_frame); sf.setContentsMargins(16,14,16,14); sf.setSpacing(8)
        sf.addWidget(self._title("Par statut"))
        self.stat_lay = QVBoxLayout(); self.stat_lay.setSpacing(6)
        sf.addLayout(self.stat_lay)
        grid.addWidget(self.stat_frame, 0, 1)

        # Top 5
        top_frame = QFrame(); top_frame.setStyleSheet(card_style())
        tf = QVBoxLayout(top_frame); tf.setContentsMargins(16,14,16,14); tf.setSpacing(8)
        tf.addWidget(self._title("Top 5 demandes par montant"))
        self.top_table = QTableWidget(0, 5)
        self.top_table.setHorizontalHeaderLabels(["N°","Objet","Demandeur","Statut","Montant"])
        self.top_table.setStyleSheet(f"""
            QTableWidget {{ background: {WHITE}; gridline-color: {BORDER}; border: none; font-size: 12px; }}
            QHeaderView::section {{ background: #f4f6fb; color: {MUTED}; font-size: 10px; font-weight: 700;
                padding: 6px; border: none; border-bottom: 1px solid {BORDER}; }}
            QTableWidget::item {{ padding: 6px; border-bottom: 1px solid {BORDER}; }}
        """)
        self.top_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.top_table.verticalHeader().setVisible(False)
        self.top_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.top_table.setSelectionMode(QTableWidget.NoSelection)
        tf.addWidget(self.top_table)
        grid.addWidget(top_frame, 1, 0, 1, 2)
        lay.addStretch()

        self.refresh()

    def _title(self, t):
        l = QLabel(t); l.setStyleSheet(f"color: {NAVY}; font-size: 13px; font-weight: 700;")
        return l

    def _bar_row(self, label, count, total, color, amount=None):
        pct = int(count / total * 100) if total else 0
        row = QHBoxLayout(); row.setSpacing(8)
        lbl = QLabel(label); lbl.setFixedWidth(160)
        lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {TEXT};")
        bar = QProgressBar(); bar.setValue(pct); bar.setFixedHeight(8); bar.setTextVisible(False)
        bar.setStyleSheet(f"QProgressBar {{ background: #e5e7eb; border-radius: 4px; border: none; }} QProgressBar::chunk {{ background: {color}; border-radius: 4px; }}")
        info = f"{count} ({pct}%)"
        if amount:
            info += f"  •  {amount:,.0f} MAD"
        cnt = QLabel(info); cnt.setStyleSheet(f"font-size: 10px; color: {MUTED};")
        row.addWidget(lbl); row.addWidget(bar, 1); row.addWidget(cnt)
        w = QWidget(); w.setLayout(row)
        return w

    def refresh(self):
        all_d = fetch_all_demandes()
        total = len(all_d) or 1

        # Dept bars
        while self.dept_lay.count():
            item = self.dept_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        dept_counts = {}
        for d in all_d:
            dept_counts.setdefault(d["departement"], {"count": 0, "amount": 0})
            dept_counts[d["departement"]]["count"] += 1
            dept_counts[d["departement"]]["amount"] += d["montant_total"]

        colors = [NAVY, INFO, SUCCESS, WARNING, DANGER, "#8b5cf6", "#ec4899", "#14b8a6"]
        for idx, (dept, data) in enumerate(sorted(dept_counts.items(), key=lambda x: -x[1]["count"])):
            self.dept_lay.addWidget(self._bar_row(dept, data["count"], total, colors[idx % len(colors)], data["amount"]))

        # Statut bars
        while self.stat_lay.count():
            item = self.stat_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        color_map = {"En attente": WARNING, "En cours": INFO, "Approuvé": SUCCESS, "Rejeté": DANGER}
        for s in STATUTS:
            cnt = sum(1 for d in all_d if d["statut"] == s)
            amt = sum(d["montant_total"] for d in all_d if d["statut"] == s)
            self.stat_lay.addWidget(self._bar_row(s, cnt, total, color_map[s], amt))

        # Top 5
        top5 = sorted(all_d, key=lambda x: x["montant_total"], reverse=True)[:5]
        self.top_table.setRowCount(len(top5))
        for i, d in enumerate(top5):
            num = QTableWidgetItem(d["numero"])
            num.setForeground(QColor(NAVY)); num.setFont(QFont("Courier New", 11, QFont.Bold))
            self.top_table.setItem(i, 0, num)
            self.top_table.setItem(i, 1, QTableWidgetItem(d["objet"]))
            self.top_table.setItem(i, 2, QTableWidgetItem(d["demandeur"]))
            si = QTableWidgetItem(d["statut"])
            bg_s, fg_s, _ = STATUT_COLORS.get(d["statut"], ("#f8fafc","#475569","#cbd5e1"))
            si.setBackground(QColor(bg_s)); si.setForeground(QColor(fg_s))
            si.setFont(QFont("", 11, QFont.Bold))
            self.top_table.setItem(i, 3, si)
            m = QTableWidgetItem(f"{d['montant_total']:,.2f} MAD")
            m.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            m.setFont(QFont("", -1, QFont.Bold))
            self.top_table.setItem(i, 4, m)
        self.top_table.setFixedHeight(len(top5) * 36 + 36)


# ─── Alert Dialog ─────────────────────────────────────────────────────────────

class AlertDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Alertes & Notifications")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(f"QDialog {{ background: {BG}; }}")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        header = QFrame(); header.setFixedHeight(48)
        header.setStyleSheet(f"background: {NAVY};")
        hl = QHBoxLayout(header); hl.setContentsMargins(16,0,16,0)
        hl.addWidget(QLabel("🔔  Alertes & Notifications").also(lambda l: l.setStyleSheet("color:white; font-size:13px; font-weight:700;")))
        root.addWidget(header)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        content = QWidget(); content.setStyleSheet(f"background: {BG};")
        cl = QVBoxLayout(content); cl.setContentsMargins(16,14,16,14); cl.setSpacing(8)
        scroll.setWidget(content)

        overdue, critique = get_alerts()

        if not overdue and not critique:
            none_lbl = QLabel("✅  Aucune alerte active"); none_lbl.setAlignment(Qt.AlignCenter)
            none_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 14px; font-weight: 600; padding: 30px;")
            cl.addWidget(none_lbl)
        else:
            for d in overdue:
                f = QFrame()
                f.setStyleSheet("QFrame { background: #fef2f2; border: 1px solid #fca5a5; border-radius: 8px; }")
                fl = QVBoxLayout(f); fl.setContentsMargins(12,10,12,10)
                fl.addWidget(QLabel(f"⚠️  <b>{d['numero']}</b> — Délai dépassé").also(lambda l: l.setStyleSheet(f"color: #991b1b; font-size: 12px;")))
                fl.addWidget(QLabel(d['objet']).also(lambda l: l.setStyleSheet(f"color: #b91c1c; font-size: 11px;")))
                fl.addWidget(QLabel(f"Limite: {d['date_limite']}").also(lambda l: l.setStyleSheet(f"color: #ef4444; font-size: 11px;")))
                cl.addWidget(f)
            for d in critique:
                f = QFrame()
                f.setStyleSheet("QFrame { background: #fff7ed; border: 1px solid #fdba74; border-radius: 8px; }")
                fl = QVBoxLayout(f); fl.setContentsMargins(12,10,12,10)
                fl.addWidget(QLabel(f"🚨  <b>{d['numero']}</b> — Priorité CRITIQUE").also(lambda l: l.setStyleSheet("color: #9a3412; font-size: 12px;")))
                fl.addWidget(QLabel(d['objet']).also(lambda l: l.setStyleSheet(f"color: #ea580c; font-size: 11px;")))
                cl.addWidget(f)

        cl.addStretch()
        root.addWidget(scroll)

        bb = QFrame(); bb.setStyleSheet(f"background: {WHITE}; border-top: 1px solid {BORDER};")
        bl = QHBoxLayout(bb); bl.setContentsMargins(16,10,16,10)
        bl.addStretch()
        ok = QPushButton("Fermer"); ok.setStyleSheet(btn_style(NAVY)); ok.clicked.connect(self.accept)
        bl.addWidget(ok)
        root.addWidget(bb)


# ─── Monkey-patch also helper ─────────────────────────────────────────────────

def _also(self, fn):
    fn(self)
    return self

QLabel.also = _also


# ─── Main Window ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GTIC Maroc — Gestion des Demandes d'Achat")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.setStyleSheet(f"QMainWindow {{ background: {BG}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet(f"QFrame {{ background: {NAVY}; border-right: none; }}")
        sb_lay = QVBoxLayout(self.sidebar)
        sb_lay.setContentsMargins(0, 0, 0, 0)
        sb_lay.setSpacing(0)

        # Logo area
        logo_frame = QFrame()
        logo_frame.setFixedHeight(70)
        logo_frame.setStyleSheet(f"background: {NAVY2}; border-bottom: 1px solid rgba(255,255,255,0.08);")
        lf = QHBoxLayout(logo_frame); lf.setContentsMargins(16,0,16,0); lf.setSpacing(12)
        if LOGO_PATH.exists():
            pix = QPixmap(str(LOGO_PATH)).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl = QLabel(); logo_lbl.setPixmap(pix)
            lf.addWidget(logo_lbl)
        title_v = QVBoxLayout(); title_v.setSpacing(0)
        t1 = QLabel("G.T.I.C"); t1.setStyleSheet("color: white; font-size: 15px; font-weight: 800; letter-spacing: 1px;")
        t2 = QLabel("Maroc"); t2.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 11px;")
        title_v.addWidget(t1); title_v.addWidget(t2)
        lf.addLayout(title_v); lf.addStretch()
        sb_lay.addWidget(logo_frame)

        # Nav buttons
        nav_container = QWidget(); nav_container.setStyleSheet("background: transparent;")
        nav_lay = QVBoxLayout(nav_container); nav_lay.setContentsMargins(8,12,8,0); nav_lay.setSpacing(2)

        self.nav_btns = {}
        nav_items = [
            ("dashboard",  "🏠",  "Tableau de bord"),
            ("demandes",   "📋",  "Demandes d'achat"),
            ("rapports",   "📊",  "Rapports"),
        ]
        for key, icon, label in nav_items:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setCheckable(True)
            btn.setFixedHeight(42)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: rgba(255,255,255,0.7);
                    border: none; border-radius: 8px;
                    text-align: left; padding-left: 12px;
                    font-size: 13px; font-weight: 500;
                }}
                QPushButton:checked {{
                    background: {RED}; color: white; font-weight: 700;
                }}
                QPushButton:hover:!checked {{
                    background: rgba(255,255,255,0.08); color: white;
                }}
            """)
            btn.clicked.connect(lambda _, k=key: self._switch(k))
            nav_lay.addWidget(btn)
            self.nav_btns[key] = btn

        nav_lay.addStretch()
        sb_lay.addWidget(nav_container, 1)

        # Bottom
        bottom = QFrame()
        bottom.setStyleSheet(f"background: transparent; border-top: 1px solid rgba(255,255,255,0.08);")
        bl = QVBoxLayout(bottom); bl.setContentsMargins(8,8,8,12); bl.setSpacing(2)
        self.alert_btn = QPushButton("  🔔  Alertes")
        self.alert_btn.setFixedHeight(38)
        self.alert_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: rgba(255,255,255,0.7);
                border: none; border-radius: 8px;
                text-align: left; padding-left: 12px; font-size: 12px;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.1); color: white; }}
        """)
        self.alert_btn.clicked.connect(self._show_alerts)
        bl.addWidget(self.alert_btn)
        quit_btn = QPushButton("  ✕  Quitter")
        quit_btn.setFixedHeight(36)
        quit_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: rgba(255,255,255,0.4);
                border: none; border-radius: 8px;
                text-align: left; padding-left: 12px; font-size: 11px;
            }}
            QPushButton:hover {{ background: rgba(204,30,42,0.3); color: white; }}
        """)
        quit_btn.clicked.connect(QApplication.quit)
        bl.addWidget(quit_btn)
        sb_lay.addWidget(bottom)

        root.addWidget(self.sidebar)

        # ── Content area ──
        content_area = QWidget()
        content_area.setStyleSheet(f"background: {BG};")
        ca_lay = QVBoxLayout(content_area)
        ca_lay.setContentsMargins(0, 0, 0, 0)
        ca_lay.setSpacing(0)

        # Top bar
        topbar = QFrame()
        topbar.setFixedHeight(56)
        topbar.setStyleSheet(f"background: {WHITE}; border-bottom: 1px solid {BORDER};")
        tb = QHBoxLayout(topbar); tb.setContentsMargins(20,0,20,0)
        self.page_title = QLabel("Tableau de bord")
        self.page_title.setStyleSheet(f"color: {TEXT}; font-size: 16px; font-weight: 700;")
        self.page_sub = QLabel("GTIC Maroc — Génie Civil & Travaux Publics")
        self.page_sub.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        ttv = QVBoxLayout(); ttv.setSpacing(0); ttv.addWidget(self.page_title); ttv.addWidget(self.page_sub)
        tb.addLayout(ttv)
        tb.addStretch()
        date_lbl = QLabel(datetime.now().strftime("%A %d %B %Y"))
        date_lbl.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        tb.addWidget(date_lbl)
        self.alert_badge = QLabel()
        self.alert_badge.setFixedSize(20, 20)
        self.alert_badge.setAlignment(Qt.AlignCenter)
        self.alert_badge.setStyleSheet(f"background: {RED}; color: white; border-radius: 10px; font-size: 10px; font-weight: 700;")
        tb.addWidget(self.alert_badge)
        av = QLabel("AD"); av.setFixedSize(34,34); av.setAlignment(Qt.AlignCenter)
        av.setStyleSheet(f"background: {NAVY}; color: white; border-radius: 17px; font-size: 12px; font-weight: 700;")
        tb.addWidget(av)
        ca_lay.addWidget(topbar)

        # Stack
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {BG};")

        scroll_wrap = lambda w: (lambda: (s := QScrollArea(), s.setWidget(w), s.setWidgetResizable(True), s.setStyleSheet("QScrollArea { border: none; background: transparent; }"), s)[-1])()

        self.page_dash = DashboardPage()
        self.page_dem  = DemandesPage()
        self.page_rap  = RapportsPage()

        for pg in (self.page_dash, self.page_dem, self.page_rap):
            sw = QScrollArea(); sw.setWidget(pg); sw.setWidgetResizable(True)
            sw.setStyleSheet("QScrollArea { border: none; background: transparent; }")
            # wrap each page in a padded container
            container = QWidget(); container.setStyleSheet(f"background: {BG};")
            cl = QVBoxLayout(container); cl.setContentsMargins(20,20,20,20); cl.setSpacing(0)
            cl.addWidget(pg)
            self.stack.addWidget(container)

        ca_lay.addWidget(self.stack, 1)
        root.addWidget(content_area, 1)

        # Init
        self._switch("dashboard")
        self._update_alert_badge()

        # Auto-refresh alerts every 60s
        timer = QTimer(self)
        timer.timeout.connect(self._update_alert_badge)
        timer.start(60000)

    def _switch(self, key):
        idx = {"dashboard": 0, "demandes": 1, "rapports": 2}[key]
        self.stack.setCurrentIndex(idx)
        titles = {"dashboard": "Tableau de bord", "demandes": "Demandes d'achat", "rapports": "Rapports & Statistiques"}
        self.page_title.setText(titles[key])
        for k, btn in self.nav_btns.items():
            btn.setChecked(k == key)

        # Refresh the active page
        if key == "dashboard": self.page_dash.refresh()
        elif key == "demandes": self.page_dem.refresh()
        elif key == "rapports": self.page_rap.refresh()

    def _show_alerts(self):
        dlg = AlertDialog(self)
        dlg.exec()

    def _update_alert_badge(self):
        overdue, critique = get_alerts()
        total = len(overdue) + len(critique)
        if total:
            self.alert_badge.setText(str(total))
            self.alert_badge.show()
            self.alert_btn.setText(f"  🔔  Alertes  ({total})")
            self.alert_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(204,30,42,0.15); color: #fca5a5;
                    border: none; border-radius: 8px;
                    text-align: left; padding-left: 12px; font-size: 12px; font-weight: 700;
                }}
                QPushButton:hover {{ background: rgba(204,30,42,0.3); color: white; }}
            """)
        else:
            self.alert_badge.hide()
            self.alert_btn.setText("  🔔  Alertes")
            self.alert_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: rgba(255,255,255,0.7);
                    border: none; border-radius: 8px;
                    text-align: left; padding-left: 12px; font-size: 12px;
                }}
                QPushButton:hover {{ background: rgba(255,255,255,0.1); color: white; }}
            """)


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("GTIC Demandes d'Achat")
    app.setOrganizationName("GTIC Maroc")

    # Smooth font rendering
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
