#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Suivi Élèves – École V9 STABLE (Mac + PC)
Base : PySide6 + SQLite locale

Objectifs V9 :
- Appli "complète" et surtout PERSISTANTE (tout est sauvegardé en base)
- Identité élève
- Diagnostics (cases + autre détails) -> sauvegardés
- Suivis médicaux -> sauvegardés
- Réunions REE / ESS -> sauvegardées
- Dispositifs (PAP/PAI/PPS/AESH/GEVASCO) -> sauvegardés
- Observations / notes -> sauvegardées
- Historique enseignants (par année) -> sauvegardé
- Import / Export CSV (auto-détection séparateur ; dates DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD)
- Export PDF : fiche élève + liste classe
- Tableau de bord + stats par classe + stats dispositifs/diagnostics

Données : fichier SQLite local (ecole_v9.db) dans le même dossier que ce script.
"""

import sys, sqlite3, uuid, csv, os
import shutil
import hashlib
import secrets
from datetime import date, datetime

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtPrintSupport import QPrinter

APP_TITLE = "Suivi Élèves – École V10 PRO"
VERSION = "13.2"
ADMIN_RESET_CODE_DEFAULT = "ADMIN-ECOLE-2026"

COPYRIGHT_NOTICE = "© 2026 Isabelle Genty. Tous droits réservés."
LICENSE_TEXT = """Suivi Élèves – Licence d'utilisation

© 2026 Isabelle Genty. Tous droits réservés.

Ce logiciel, son code source, son interface, sa base de données, ses exports,
ses documents associés et sa structure fonctionnelle sont protégés par le droit d'auteur.

Sauf autorisation écrite préalable de l'autrice :
- la reproduction, la duplication, la diffusion ou la redistribution sont interdites,
- la revente, la location ou la mise à disposition payante sont interdites,
- l'adaptation, la modification ou l'intégration dans un autre logiciel sont interdites.

L'usage du logiciel peut être autorisé école par école, selon les conditions définies par l'autrice.
"""

def ensure_license_file():
    try:
        path = os.path.join(BASE_DIR, "LICENCE.txt")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(LICENSE_TEXT)
    except Exception:
        pass


STYLE_QSS = """
/* ---- SuiviEleves V10 PRO – Thème clair + accent rose ---- */
QWidget {
    font-size: 13px;
}
QMainWindow {
    background: #FAFAFA;
}
QTabWidget::pane {
    border: 1px solid #E5E5E5;
    top: -1px;
    background: white;
    border-radius: 10px;
}
QTabBar::tab {
    background: #F3F3F3;
    border: 1px solid #E5E5E5;
    padding: 8px 12px;
    margin-right: 6px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}
QTabBar::tab:selected {
    background: white;
    border-bottom: 1px solid white;
}
QGroupBox {
    border: 1px solid #E5E5E5;
    border-radius: 12px;
    margin-top: 10px;
    padding: 10px;
    background: white;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #333;
    font-weight: 600;
}
QLineEdit, QComboBox, QDateEdit, QTextEdit, QPlainTextEdit, QSpinBox {
    border: 1px solid #D9D9D9;
    border-radius: 10px;
    padding: 6px 8px;
    background: white;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus {
    border: 2px solid #E91E63; /* rose */
}
QPushButton {
    border: 1px solid #E91E63;
    background: #E91E63;
    color: white;
    border-radius: 12px;
    padding: 8px 12px;
    font-weight: 600;
}
QPushButton:hover {
    background: #D81B60;
    border-color: #D81B60;
}
QPushButton:pressed {
    background: #C2185B;
    border-color: #C2185B;
}
QPushButton:disabled {
    background: #F0B6C9;
    border-color: #F0B6C9;
    color: white;
}
QToolBar {
    background: white;
    border-bottom: 1px solid #E5E5E5;
    spacing: 8px;
}
QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 6px;
}
QToolButton:hover {
    border: 1px solid #F2B1C9;
    background: #FFF0F6;
}
QToolButton:pressed {
    background: #FFE3EE;
}
QTableWidget {
    border: 1px solid #E5E5E5;
    border-radius: 12px;
    background: white;
}
QHeaderView::section {
    background: #F7F7F7;
    border: none;
    border-bottom: 1px solid #E5E5E5;
    padding: 6px;
    font-weight: 600;
}
QMenuBar {
    background: white;
    border-bottom: 1px solid #E5E5E5;
}
QMenuBar::item:selected {
    background: #FFF0F6;
}
QMenu {
    background: white;
    border: 1px solid #E5E5E5;
}
QMenu::item:selected {
    background: #FFF0F6;
}
"""

# --- Mode "portable" : base et dossiers à côté de l'appli (Mac/Windows) ---
# En mode PyInstaller, sys.executable pointe vers l'exécutable ; sinon __file__
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB = os.path.join(BASE_DIR, "ecole.db")

# Dossiers utiles (créés automatiquement)
BACKUP_DIR = os.path.join(BASE_DIR, "sauvegardes")
EXPORT_DIR = os.path.join(BASE_DIR, "exports_pdf")
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

NIVEAUX = ["","PS","MS","GS","CP","CE1","CE2","CM1","CM2"]
SUIVIS = ["","CMPP","CMP","Orthophoniste","Psychomotricien","Psychologue","Neurologue","Suivi hôpital","Autre"]
DIAGNOSTICS = ["TDA","TDAH","TSA","Dyslexie","Dysorthographie","Dyscalculie","Dyspraxie","Dysphasie","Dysgraphie"]
DISPOSITIFS = ["","PAP","PAI","PPS","GEVASCO","AESH"]

# ------------------------- OUTILS DATE / CSV -------------------------

def parse_date_any(s: str) -> str:
    """
    Retourne une date ISO YYYY-MM-DD ou "" si impossible.
    Accepte :
    - DD/MM/YYYY
    - DD-MM-YYYY
    - YYYY-MM-DD
    - YYYY/MM/DD
    """
    if not s:
        return ""
    s = str(s).strip()
    if not s:
        return ""
    s = s.replace(".", "/").replace("\\", "/").replace("-", "/")
    parts = [p for p in s.split("/") if p]
    try:
        if len(parts) != 3:
            return ""
        # si commence par 4 chiffres => YYYY/MM/DD
        if len(parts[0]) == 4:
            y, m, d = map(int, parts)
        else:
            d, m, y = map(int, parts)
        dt = date(y, m, d)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return ""


def parse_libelle_classe(val: str) -> tuple[str, str]:
    """
    Extrait classe + enseignant depuis la colonne ONDE "Libellé classe".
    Ex: "CE2 B - Mme Angélie COUGOUL" -> ("CE2 B", "Mme Angélie COUGOUL")
    """
    if val is None:
        return "", ""
    s = str(val).strip().strip('"').strip()
    if " - " in s:
        a, b = s.split(" - ", 1)
        return a.strip(), b.strip()
    m = re.match(r"^(.*?)\s*[-–—]\s*(.*)$", s)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return s, ""

def calc_age(iso: str) -> str:
    if not iso:
        return ""
    try:
        y, m, d = map(int, iso.split("-"))
        dob = date(y, m, d)
        today = date.today()
        return str(today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day)))
    except Exception:
        return ""

def detect_delimiter(sample: str) -> str:
    # Essai simple ; on peut compléter au besoin
    if sample.count(";") >= sample.count(","):
        return ";"
    return ","

# ------------------------- BASE SQLITE -------------------------

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS settings(
        k TEXT PRIMARY KEY,
        v TEXT
    )""")


    conn.execute("""
    CREATE TABLE IF NOT EXISTS eleves(
        id TEXT PRIMARY KEY,
        nom TEXT,
        prenom TEXT,
        sexe TEXT,
        naissance TEXT,
        niveau TEXT,
        classe TEXT,
        enseignant TEXT,
        actif INTEGER DEFAULT 1
    )""")

    # Infos ONDE (optionnel) : permet d'importer davantage de données sans toucher à la table eleves
    conn.execute("""
    CREATE TABLE IF NOT EXISTS onde_infos(
        eleve_id TEXT PRIMARY KEY,
        ine TEXT,
        adresse1 TEXT,
        cp1 TEXT,
        commune1 TEXT,
        autorisation_photo TEXT,
        dispositif TEXT,
        regroupement TEXT,
        cycle TEXT,
        identifiant_classe TEXT,
        FOREIGN KEY(eleve_id) REFERENCES eleves(id) ON DELETE CASCADE
    )""")

    # Diagnostics (N-N) + "autre"
    conn.execute("""
    CREATE TABLE IF NOT EXISTS eleve_diagnostics(
        eleve_id TEXT NOT NULL,
        diag TEXT NOT NULL,
        PRIMARY KEY(eleve_id, diag),
        FOREIGN KEY(eleve_id) REFERENCES eleves(id) ON DELETE CASCADE
    )""")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS eleve_diag_autre(
        eleve_id TEXT PRIMARY KEY,
        details TEXT,
        FOREIGN KEY(eleve_id) REFERENCES eleves(id) ON DELETE CASCADE
    )""")

    # Suivis médicaux
    conn.execute("""
    CREATE TABLE IF NOT EXISTS suivis(
        id TEXT PRIMARY KEY,
        eleve_id TEXT NOT NULL,
        type TEXT,
        debut TEXT,
        fin TEXT,
        professionnel TEXT,
        notes TEXT,
        FOREIGN KEY(eleve_id) REFERENCES eleves(id) ON DELETE CASCADE
    )""")

    # Réunions REE / ESS
    conn.execute("""
    CREATE TABLE IF NOT EXISTS reunions(
        id TEXT PRIMARY KEY,
        eleve_id TEXT NOT NULL,
        type TEXT,
        d TEXT,
        notes TEXT,
        FOREIGN KEY(eleve_id) REFERENCES eleves(id) ON DELETE CASCADE
    )""")

    # Historique enseignants par année
    conn.execute("""
    CREATE TABLE IF NOT EXISTS enseignants(
        id TEXT PRIMARY KEY,
        eleve_id TEXT NOT NULL,
        annee TEXT,
        enseignant TEXT,
        niveau TEXT,
        classe TEXT,
        FOREIGN KEY(eleve_id) REFERENCES eleves(id) ON DELETE CASCADE
    )""")

    # Dispositifs (PAP / PAI / PPS / AESH / etc.)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS dispositifs(
        id TEXT PRIMARY KEY,
        eleve_id TEXT NOT NULL,
        type TEXT,
        debut TEXT,
        fin TEXT,
        aesh INTEGER DEFAULT 0,
        heures_aesh TEXT,
        amenagements TEXT,
        notes TEXT,
        FOREIGN KEY(eleve_id) REFERENCES eleves(id) ON DELETE CASCADE
    )""")


    # Dispositifs "scolaires" (1 ligne par élève) – V9.3
    # (On garde la table 'dispositifs' pour compatibilité/historique, mais l'UI utilise celle-ci.)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS dispositifs_eleve(
        eleve_id TEXT PRIMARY KEY,

        -- Notification MDPH
        mdph_notif INTEGER DEFAULT 0,
        mdph_type TEXT,                -- "Individuel" / "Mutualisé"
        mdph_date_notif TEXT,          -- date notification
        mdph_date_fin_validite TEXT,   -- fin de validité
        aesh_heures TEXT,              -- heures AESH

        -- PAI (3 types)
        pai_type TEXT,                 -- "Alimentaire" / "Anxiété scolaire" / "Asthme"
        pai_debut TEXT,

        -- PAP
        pap INTEGER DEFAULT 0,
        pap_debut TEXT,

        -- PPRE
        ppre INTEGER DEFAULT 0,
        ppre_debut TEXT,
        ppre_fin TEXT,

        -- Textes libres
        amenagements TEXT,
        notes TEXT,

        FOREIGN KEY(eleve_id) REFERENCES eleves(id) ON DELETE CASCADE
    )""")

    # Migration douce : ajoute les colonnes manquantes si une ancienne base existe
    def _add_col(coldef: str):
        try:
            conn.execute(f"ALTER TABLE dispositifs_eleve ADD COLUMN {coldef}")
        except Exception:
            pass

    _add_col("mdph_notif INTEGER DEFAULT 0")
    _add_col("mdph_type TEXT")
    _add_col("mdph_date_notif TEXT")
    _add_col("mdph_date_fin_validite TEXT")
    _add_col("aesh_heures TEXT")
    _add_col("pai_type TEXT")
    _add_col("pai_debut TEXT")
    _add_col("pap INTEGER DEFAULT 0")
    _add_col("pap_debut TEXT")
    _add_col("ppre INTEGER DEFAULT 0")
    _add_col("ppre_debut TEXT")
    _add_col("ppre_fin TEXT")
    _add_col("amenagements TEXT")
    _add_col("notes TEXT")

    # Observations (notes datées)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS notes(
        id TEXT PRIMARY KEY,
        eleve_id TEXT NOT NULL,
        d TEXT,
        categorie TEXT,
        contenu TEXT,
        FOREIGN KEY(eleve_id) REFERENCES eleves(id) ON DELETE CASCADE
    )""")

    conn.commit()
    return conn



def setting_get(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    row = conn.execute("SELECT v FROM settings WHERE k=?", (key,)).fetchone()
    return row[0] if row and row[0] is not None else default

def setting_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT OR REPLACE INTO settings(k,v) VALUES(?,?)", (key, value))
    conn.commit()

def _pbkdf2_hash(password: str, salt_hex: str, iterations: int = 200_000) -> str:
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return dk.hex()

def ensure_password_gate(parent, conn: sqlite3.Connection) -> bool:
    """
    Sécurisation "direction d'école" (contrôle d'accès) :
    - 1ère ouverture : création d'un mot de passe
    - ensuite : demande du mot de passe à chaque lancement
    Note : ceci ne chiffre pas le fichier SQLite (pas de SQLCipher), c'est un verrou d'accès applicatif.
    """
    salt = setting_get(conn, "pw_salt", "")
    pw_hash = setting_get(conn, "pw_hash", "")
    if not salt or not pw_hash:
        # créer un mot de passe
        pw, ok = QInputDialog.getText(parent, "Sécurité", "Créer un mot de passe (direction) :", QLineEdit.Password)
        if not ok:
            return False
        pw2, ok2 = QInputDialog.getText(parent, "Sécurité", "Confirmer le mot de passe :", QLineEdit.Password)
        if not ok2:
            return False
        if pw != pw2 or len(pw.strip()) < 4:
            QMessageBox.warning(parent, "Sécurité", "Mot de passe invalide (min 4 caractères) ou non identique.")
            return False
        salt = secrets.token_hex(16)
        pw_hash = _pbkdf2_hash(pw, salt)
        setting_set(conn, "pw_salt", salt)
        setting_set(conn, "pw_hash", pw_hash)
        return True

    # demander le mot de passe
    pw, ok = QInputDialog.getText(parent, "Sécurité", "Mot de passe :", QLineEdit.Password)
    if not ok:
        return False
    if _pbkdf2_hash(pw, salt) != pw_hash:
        QMessageBox.critical(parent, "Sécurité", "Mot de passe incorrect.")
        return False
    return True

def sauvegarde_auto(reason: str = "") -> str:
    """
    Sauvegarde automatique "intelligente" :
    - Copie la base SQLite dans 'sauvegardes'
    - Garde les 30 dernières sauvegardes
    - Garde aussi 1 sauvegarde "quotidienne" par jour (suffixe _daily) sur 60 jours
    Retourne le chemin du fichier créé (ou "" si échec).
    """
    try:
        if not os.path.exists(DB):
            return ""

        os.makedirs(BACKUP_DIR, exist_ok=True)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = "ecole"
        name = f"{base_name}_{stamp}.db" if not reason else f"{base_name}_{stamp}_{reason}.db"
        dst = os.path.join(BACKUP_DIR, name)
        shutil.copy(DB, dst)

        # Daily (1 par jour)
        day = datetime.now().strftime("%Y%m%d")
        daily = os.path.join(BACKUP_DIR, f"{base_name}_{day}_daily.db")
        if not os.path.exists(daily):
            shutil.copy(DB, daily)

        # Rotation: garder 30 dernières + daily sur 60 jours
        files = []
        for fn in os.listdir(BACKUP_DIR):
            if fn.endswith(".db") and fn.startswith(base_name + "_"):
                p = os.path.join(BACKUP_DIR, fn)
                try:
                    files.append((os.path.getmtime(p), p))
                except Exception:
                    pass
        files.sort(reverse=True)

        # garder 30 plus récentes (hors daily) + tous les daily
        nondaily = [p for _, p in files if "_daily.db" not in p]
        daily_files = [p for _, p in files if "_daily.db" in p]

        for p in nondaily[30:]:
            try: os.remove(p)
            except Exception: pass

        # daily > 60 jours
        cutoff = datetime.now().timestamp() - (60 * 24 * 3600)
        for p in daily_files:
            try:
                if os.path.getmtime(p) < cutoff:
                    os.remove(p)
            except Exception:
                pass

        return dst
    except Exception:
        return ""
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"ecole_{stamp}.db" if not reason else f"ecole_{stamp}_{reason}.db"
        dst = os.path.join(BACKUP_DIR, name)
        shutil.copy(DB, dst)
        return dst
    except Exception:
        return ""

# ------------------------- UI -------------------------

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.conn = db()
        self.current = None  # eleve_id
        self.show_archived = False  # afficher les élèves archivés (actif=0)

        self.setWindowTitle(APP_TITLE)
        # Icône fenêtre (si un fichier est disponible à côté de l'app)
        try:
            ico_path = os.path.join(BASE_DIR, 'icone_suivi_eleves.png')
            if os.path.exists(ico_path):
                self.setWindowIcon(QIcon(ico_path))
        except Exception:
            pass
        self.resize(1500, 900)

        self.build_ui()
        self.create_menu()
        self.create_toolbar()
        self.apply_theme()
        ensure_license_file()
        self.refresh()

        # Sauvegarde automatique : au démarrage + toutes les 10 minutes
        sauvegarde_auto('startup')
        self._autosave_timer = QTimer(self)
        self._autosave_timer.timeout.connect(lambda: sauvegarde_auto('auto'))
        self._autosave_timer.start(10 * 60 * 1000)


    def build_ui(self):
        root = QHBoxLayout()
        main = QWidget()
        main.setLayout(root)
        self.setCentralWidget(main)

        # ---- Gauche : liste + actions direction ----
        left = QVBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher élève")
        self.search.textChanged.connect(self.refresh)

        # Filtres (direction)
        self.filter_classe = QComboBox()
        self.filter_classe.addItems(["Toutes les classes"])
        self.filter_classe.currentIndexChanged.connect(self.refresh)

        self.filter_dispositif = QComboBox()
        self.filter_dispositif.addItems([
            "Tous dispositifs",
            "MDPH",
            "AESH Individuel",
            "AESH Mutualisé",
            "PAI Alimentaire",
            "PAI Anxiété scolaire",
            "PAI Asthme",
            "PAP",
            "PPRE"
        ])
        self.filter_dispositif.currentIndexChanged.connect(self.refresh)

        self.list = QListWidget()
        self.list.itemClicked.connect(self.load)

        btn_new = QPushButton("Nouvel élève")
        btn_new.clicked.connect(self.new)

        btn_import = QPushButton("Importer élèves CSV")
        btn_import.clicked.connect(self.import_csv)

        btn_export = QPushButton("Exporter CSV école")
        btn_export.clicked.connect(self.export_csv)

        btn_dashboard = QPushButton("Tableau de bord direction")
        btn_dashboard.clicked.connect(self.dashboard)

        btn_classes = QPushButton("Statistiques par classe")
        btn_stats = QPushButton("Statistiques école (avancé)")
        btn_stats.clicked.connect(self.stats_ecole)

        btn_classes.clicked.connect(self.stats_classes)

        left.addWidget(self.search)
        left.addWidget(QLabel('Filtre classe'))
        left.addWidget(self.filter_classe)
        left.addWidget(QLabel('Filtre dispositif'))
        left.addWidget(self.filter_dispositif)
        left.addWidget(self.list)
        left.addWidget(btn_new)
        left.addWidget(btn_import)
        left.addWidget(btn_export)
        left.addWidget(btn_dashboard)
        left.addWidget(btn_classes)
        left.addWidget(btn_stats)

        # ---- Droite : onglets ----
        right = QVBoxLayout()
        self.tabs = QTabWidget()
        right.addWidget(self.tabs)

        self.tab_identite()
        self.tab_synthese()
        self.tab_diagnostics()
        self.tab_suivis()
        self.tab_dispositifs()
        self.tab_reunions()
        self.tab_notes()
        self.tab_historique_enseignants()

        # ---- Bas : actions ----
        actions = QHBoxLayout()
        btn_save = QPushButton("Enregistrer tout")
        btn_save.clicked.connect(self.save_all)

        btn_pdf_fiche = QPushButton("Exporter fiche élève (PDF)")
        btn_pdf_fiche.clicked.connect(self.export_pdf_fiche)

        btn_pdf_classe = QPushButton("Exporter liste classe (PDF)")
        btn_pdf_classe.clicked.connect(self.export_pdf_classe)

        actions.addWidget(btn_save)
        actions.addWidget(btn_pdf_fiche)
        actions.addWidget(btn_pdf_classe)

        self.status = QLabel("")
        self.status.setWordWrap(True)

        right.addLayout(actions)
        right.addWidget(self.status)

        root.addLayout(left, 1)
        root.addLayout(right, 3)


    def create_menu(self):
        menubar = self.menuBar()

        m_file = menubar.addMenu("Fichier")

        act_save = QAction("Enregistrer tout", self)
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self.save_all)
        m_file.addAction(act_save)

        act_backup = QAction("Sauvegarde maintenant", self)
        act_backup.triggered.connect(self.menu_backup_now)
        m_file.addAction(act_backup)

        m_file.addSeparator()

        act_open_backup = QAction("Ouvrir dossier sauvegardes", self)
        act_open_backup.triggered.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(BACKUP_DIR)))
        m_file.addAction(act_open_backup)

        act_open_exports = QAction("Ouvrir dossier exports PDF", self)
        act_open_exports.triggered.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(EXPORT_DIR)))
        m_file.addAction(act_open_exports)

        m_file.addSeparator()

        act_quit = QAction("Quitter", self)
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self.close)
        m_file.addAction(act_quit)

        act_change_pw = QAction("Changer le mot de passe", self)
        act_change_pw.triggered.connect(self.change_password)
        m_file.addAction(act_change_pw)

        act_reset_pw = QAction("Réinitialiser le mot de passe (code admin)", self)
        act_reset_pw.triggered.connect(self.reset_password_with_admin_code)
        m_file.addAction(act_reset_pw)

        m_file.addSeparator()

        act_import = QAction("Importer ONDE / CSV", self)
        act_import.triggered.connect(self.import_csv)
        m_file.addAction(act_import)

        act_sync = QAction("Synchroniser avec ONDE", self)
        act_sync.triggered.connect(self.synchroniser_onde)
        m_file.addAction(act_sync)

        m_file.addSeparator()

        act_restore = QAction("Restaurer une sauvegarde…", self)
        act_restore.triggered.connect(self.restore_backup)
        m_file.addAction(act_restore)

        # Élèves / archives
        m_eleves = menubar.addMenu("Élèves")
        act_archives = QAction("Afficher les élèves archivés", self)
        act_archives.setCheckable(True)
        act_archives.triggered.connect(self.set_show_archives)
        m_eleves.addAction(act_archives)
        m_eleves.addSeparator()
        act_archiver = QAction("Archiver l'élève sélectionné", self)
        act_archiver.triggered.connect(self.archive_current)
        m_eleves.addAction(act_archiver)
        act_reactiver = QAction("Réactiver l'élève sélectionné", self)
        act_reactiver.triggered.connect(self.reactivate_current)
        m_eleves.addAction(act_reactiver)
        m_eleves.addSeparator()
        act_dossier = QAction("Exporter dossier élève (PDF)", self)
        act_dossier.triggered.connect(self.export_pdf_dossier)
        m_eleves.addAction(act_dossier)
        # Année scolaire
        m_annee = menubar.addMenu("Année scolaire")
        act_rentree = QAction("Préparer la rentrée (archiver CM2)", self)
        act_rentree.triggered.connect(self.preparer_rentree)
        m_annee.addAction(act_rentree)



        m_help = menubar.addMenu("Aide")
        act_about = QAction("À propos", self)
        act_about.triggered.connect(self.about)
        m_help.addAction(act_about)


    def apply_theme(self):
        # Thème clair + accent rose (sans modifier la logique métier)
        try:
            QApplication.instance().setStyleSheet(STYLE_QSS)
        except Exception:
            # Ne jamais bloquer l'app si le style échoue
            pass

    def create_toolbar(self):
        # Barre d'outils "direction" avec icônes (style rempli via icônes système Qt)
        tb = QToolBar("Actions")
        tb.setMovable(False)
        tb.setIconSize(QSize(22, 22))
        self.addToolBar(Qt.TopToolBarArea, tb)

        st = self.style()

        act_new = QAction(st.standardIcon(QStyle.SP_FileDialogNewFolder), "Nouveau", self)
        act_new.setToolTip("Nouvel élève")
        act_new.triggered.connect(self.new)
        tb.addAction(act_new)

        act_save = QAction(st.standardIcon(QStyle.SP_DialogSaveButton), "Enregistrer", self)
        act_save.setToolTip("Enregistrer tout (Ctrl+S)")
        act_save.triggered.connect(self.save_all)
        tb.addAction(act_save)

        tb.addSeparator()

        act_pdf = QAction(st.standardIcon(QStyle.SP_FileIcon), "PDF élève", self)
        act_pdf.setToolTip("Exporter la fiche élève en PDF")
        act_pdf.triggered.connect(self.export_pdf_fiche)
        tb.addAction(act_pdf)

        act_pdf_list = QAction(st.standardIcon(QStyle.SP_FileDialogDetailedView), "PDF liste", self)
        act_pdf_list.setToolTip("Exporter la liste (classe/filtre) en PDF")
        act_pdf_list.triggered.connect(self.export_pdf_classe)
        tb.addAction(act_pdf_list)

        tb.addSeparator()

        act_backup = QAction(st.standardIcon(QStyle.SP_BrowserReload), "Sauvegarde", self)
        act_backup.setToolTip("Sauvegarde maintenant")
        act_backup.triggered.connect(self.menu_backup_now)
        tb.addAction(act_backup)

        act_stats = QAction(st.standardIcon(QStyle.SP_ComputerIcon), "Stats", self)
        act_stats.setToolTip("Tableau de bord / statistiques")
        act_stats.triggered.connect(self.dashboard)
        tb.addAction(act_stats)

        act_sync = QAction(st.standardIcon(QStyle.SP_BrowserReload), "Sync ONDE", self)
        act_sync.setToolTip("Synchroniser avec ONDE")
        act_sync.triggered.connect(self.synchroniser_onde)
        tb.addAction(act_sync)

        act_restore = QAction(st.standardIcon(QStyle.SP_DialogOpenButton), "Restaurer", self)
        act_restore.setToolTip("Restaurer une sauvegarde")
        act_restore.triggered.connect(self.restore_backup)
        tb.addAction(act_restore)

        tb.addSeparator()
        act_rentree = QAction(st.standardIcon(QStyle.SP_DirIcon), "Rentrée", self)
        act_rentree.setToolTip("Préparer la rentrée : archiver les CM2")
        act_rentree.triggered.connect(self.preparer_rentree)
        tb.addAction(act_rentree)

    def menu_backup_now(self):
        path = sauvegarde_auto("manual")
        if path:
            QMessageBox.information(self, "Sauvegarde", f"Sauvegarde créée :\n{path}")
        else:
            QMessageBox.warning(self, "Sauvegarde", "Impossible de créer la sauvegarde.")


    def preparer_rentree(self):
        """
        Année scolaire (option B) :
        - Archive les élèves de CM2 (actif=0) sans supprimer les données
        - Sauvegarde automatique avant action (si dispo)
        - L'import ONDE de rentrée remettra à jour les élèves + classes/enseignants
        """
        rep = QMessageBox.question(
            self,
            "Préparer la rentrée",
            "Les élèves de CM2 vont être archivés.\n\n"
            "Ils resteront dans l'historique mais ne seront plus actifs.\n\n"
            "Continuer ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if rep != QMessageBox.Yes:
            return

        # Sauvegarde automatique (si disponible)
        try:
            self.menu_backup_now()
        except Exception:
            pass

        try:
            cur = self.conn.execute("SELECT COUNT(*) AS n FROM eleves WHERE niveau='CM2' AND actif=1")
            n = cur.fetchone()["n"]
            self.conn.execute("UPDATE eleves SET actif=0 WHERE niveau='CM2' AND actif=1")
            self.conn.commit()
            QMessageBox.information(
                self,
                "Rentrée préparée",
                f"CM2 archivés : {n}\n\nVous pouvez maintenant importer le nouveau fichier ONDE."
            )
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Préparer la rentrée", f"Erreur :\n{e}")

    def change_password(self):
        salt = setting_get(self.conn, "pw_salt", "")
        pw_hash = setting_get(self.conn, "pw_hash", "")
        if not salt or not pw_hash:
            QMessageBox.information(self, "Sécurité", "Aucun mot de passe n'est défini.")
            return

        old, ok = QInputDialog.getText(self, "Sécurité", "Ancien mot de passe :", QLineEdit.Password)
        if not ok:
            return
        if _pbkdf2_hash(old, salt) != pw_hash:
            QMessageBox.critical(self, "Sécurité", "Ancien mot de passe incorrect.")
            return

        new1, ok1 = QInputDialog.getText(self, "Sécurité", "Nouveau mot de passe :", QLineEdit.Password)
        if not ok1:
            return
        new2, ok2 = QInputDialog.getText(self, "Sécurité", "Confirmer le nouveau mot de passe :", QLineEdit.Password)
        if not ok2:
            return
        if new1 != new2 or len(new1.strip()) < 4:
            QMessageBox.warning(self, "Sécurité", "Mot de passe invalide (min 4 caractères) ou non identique.")
            return

        new_salt = secrets.token_hex(16)
        new_hash = _pbkdf2_hash(new1, new_salt)
        setting_set(self.conn, "pw_salt", new_salt)
        setting_set(self.conn, "pw_hash", new_hash)
        QMessageBox.information(self, "Sécurité", "Mot de passe changé ✅")



    def reset_password_with_admin_code(self):
        """
        Réinitialisation du mot de passe avec le code administratrice.
        Code par défaut si non défini dans la base : ADMIN-ECOLE-2026
        """
        code_ref = setting_get(self.conn, "admin_reset_code", ADMIN_RESET_CODE_DEFAULT)

        code, ok = QInputDialog.getText(
            self,
            "Réinitialisation mot de passe",
            "Entrez le code administratrice de réinitialisation :",
            QLineEdit.Password
        )
        if not ok:
            return

        if (code or "").strip() != (code_ref or "").strip():
            QMessageBox.critical(self, "Sécurité", "Code administratrice incorrect.")
            return

        new1, ok1 = QInputDialog.getText(self, "Sécurité", "Nouveau mot de passe :", QLineEdit.Password)
        if not ok1:
            return
        new2, ok2 = QInputDialog.getText(self, "Sécurité", "Confirmer le nouveau mot de passe :", QLineEdit.Password)
        if not ok2:
            return
        if new1 != new2 or len(new1.strip()) < 4:
            QMessageBox.warning(self, "Sécurité", "Mot de passe invalide (min 4 caractères) ou non identique.")
            return

        new_salt = secrets.token_hex(16)
        new_hash = _pbkdf2_hash(new1, new_salt)
        setting_set(self.conn, "pw_salt", new_salt)
        setting_set(self.conn, "pw_hash", new_hash)
        QMessageBox.information(
            self,
            "Sécurité",
            "Mot de passe réinitialisé ✅\n\n"
            f"Code administratrice attendu : {code_ref}"
        )


    def restore_backup(self):
        """
        Restaurer une sauvegarde SQLite (.db).
        """
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Restaurer une sauvegarde",
            BACKUP_DIR,
            "Base SQLite (*.db)"
        )
        if not path:
            return

        rep = QMessageBox.question(
            self,
            "Restaurer une sauvegarde",
            "La base actuelle va être remplacée par la sauvegarde sélectionnée.\n\n"
            "Une sauvegarde de sécurité de la base actuelle sera créée avant restauration.\n\n"
            "Continuer ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if rep != QMessageBox.Yes:
            return

        try:
            sauvegarde_auto("before_restore")
        except Exception:
            pass

        try:
            try:
                self.conn.close()
            except Exception:
                pass

            shutil.copy(path, DB)
            self.conn = db()
            self.current = None
            try:
                self.new()
            except Exception:
                pass
            self.refresh()
            QMessageBox.information(self, "Restauration", "Sauvegarde restaurée ✅")
        except Exception as e:
            QMessageBox.critical(self, "Restauration", f"Erreur lors de la restauration :\n{e}")

    def add_student_from_transfer_pdf(self):
        QMessageBox.information(
            self,
            "Transfert PDF",
            "L'ajout d'un élève depuis une synthèse PDF a été retiré de cette version."
        )

    # ----------------- ARCHIVES / TRANSFERT -----------------

    def set_show_archives(self, show: bool):
        self.show_archived = bool(show)
        # Nettoyer la sélection actuelle pour éviter de modifier un élève sans le vouloir
        self.current = None
        try:
            self.new()
        except Exception:
            pass
        self.refresh()

    def archive_current(self):
        if not self.current:
            QMessageBox.information(self, "Archives", "Sélectionnez un élève.")
            return
        rep = QMessageBox.question(
            self,
            "Archiver l'élève",
            "Archiver cet élève ?\n\nIl restera dans l'historique, mais ne sera plus actif.",
            QMessageBox.Yes | QMessageBox.No
        )
        if rep != QMessageBox.Yes:
            return
        try:
            self.conn.execute("UPDATE eleves SET actif=0 WHERE id=?", (self.current,))
            self.conn.commit()
            QMessageBox.information(self, "Archives", "Élève archivé ✅")
            self.current = None
            try:
                self.new()
            except Exception:
                pass
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Archives", f"Erreur :\n{e}")

    def reactivate_current(self):
        if not self.current:
            QMessageBox.information(self, "Archives", "Sélectionnez un élève.")
            return
        rep = QMessageBox.question(
            self,
            "Réactiver l'élève",
            "Réactiver cet élève ?\n\nIl réapparaîtra dans la liste active.",
            QMessageBox.Yes | QMessageBox.No
        )
        if rep != QMessageBox.Yes:
            return
        try:
            self.conn.execute("UPDATE eleves SET actif=1 WHERE id=?", (self.current,))
            self.conn.commit()
            QMessageBox.information(self, "Archives", "Élève réactivé ✅")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Archives", f"Erreur :\n{e}")

    def export_pdf_dossier(self):
        # Pour l'instant, le "dossier" reprend la fiche élève complète déjà en place (très riche).
        # Nom de fichier différent pour distinguer.
        if not self.current:
            QMessageBox.information(self, "PDF", "Sélectionnez un élève.")
            return

        try:
            name = f"{self.nom.text()}_{self.prenom.text()}".strip().replace(" ", "_") or "eleve"
            default_path = os.path.join(EXPORT_DIR, f"{name}_dossier.pdf")

            path, _ = QFileDialog.getSaveFileName(
                self,
                "Enregistrer le dossier élève (PDF)",
                default_path,
                "PDF (*.pdf)"
            )
            if not path:
                return
            if not path.lower().endswith(".pdf"):
                path += ".pdf"

            # On réutilise la logique HTML existante de l'export fiche (mêmes sections)
            # en copiant le contenu de export_pdf_fiche mais en écrivant dans 'path'.
            diags = [d for d, cb in self.diag.items() if cb.isChecked()]
            autre = self.diag_autre.toPlainText().strip()
            if autre:
                diags.append(f"Autre : {autre}")

            def safe_html_list(*method_names, empty_li="<li>—</li>"):
                for mn in method_names:
                    fn = getattr(self, mn, None)
                    if callable(fn):
                        try:
                            out = fn()
                            return out if (out and out.strip()) else empty_li
                        except Exception:
                            return empty_li
                return empty_li

            html = f"""
            <h1>Dossier élève</h1>
            <h2>{self._html_escape(self.nom.text())} {self._html_escape(self.prenom.text())}</h2>
            <p>
                <b>Classe</b> : {self._html_escape(self.classe.text())}
                &nbsp;&nbsp; <b>Niveau</b> : {self._html_escape(self.niveau.currentText())}
                &nbsp;&nbsp; <b>Enseignant</b> : {self._html_escape(self.enseignant.text())}
            </p>
            <p>
                <b>Date naissance</b> : {self.naissance.date().toString("yyyy-MM-dd")}
                &nbsp;&nbsp; <b>Âge</b> : {self._html_escape(self.age_label.text())}
            </p>

            <h2>Diagnostics / troubles</h2>
            <p>{("<br>".join([self._html_escape(x) for x in diags])) if diags else "—"}</p>

            <h2>Suivis médicaux</h2>
            <ul>{safe_html_list("_html_list_from_table_suivis")}</ul>

            <h2>Dispositifs</h2>
            <ul>{safe_html_list("_html_list_from_table_dispositifs")}</ul>

            <h2>Réunions</h2>
            <ul>{safe_html_list("_html_list_from_table_reunions")}</ul>

            <h2>Notes</h2>
            <ul>{safe_html_list("_html_list_from_table_notes")}</ul>

            <h2>Historique enseignants</h2>
            <ul>{safe_html_list("_html_list_from_table_historique", "_html_list_from_table_hist")}</ul>
            """

            doc = QTextDocument()
            doc.setHtml(html)

            printer = QPrinter()
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            doc.print_(printer)

            QMessageBox.information(self, "PDF", f"Dossier élève exporté ✅\n\nEmplacement :\n{path}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

        except Exception as e:
            QMessageBox.critical(self, "PDF", f"Erreur lors de l'export PDF :\n{e}")


    def mail_dossier_current(self):
        QMessageBox.information(
            self,
            "Mail",
            "La fonction d'envoi par mail a été retirée de cette version."
        )

    def about(self):
        QMessageBox.information(
            self,
            "À propos",
            "Suivi Élèves – École\n"
            "Version V13.1 PRO\n\n"
            f"{COPYRIGHT_NOTICE}\n"
            "Reproduction, adaptation, diffusion, duplication ou revente\n"
            "interdites sans autorisation écrite.\n\n"
            "Données : ecole.db (dans le dossier de l'application)\n"
            "Sauvegardes : dossier 'sauvegardes'\n"
            "Exports PDF : dossier 'exports_pdf'\n"
            "Code admin reset par défaut : ADMIN-ECOLE-2026\n"
            "Une copie de la licence est créée dans LICENCE.txt"
        )

    # ----------------- ONGLET IDENTITE -----------------

    def tab_identite(self):
        w = QWidget()
        form = QFormLayout()

        self.nom = QLineEdit()
        self.prenom = QLineEdit()

        self.sexe = QComboBox()
        self.sexe.addItems(["", "F", "M"])

        self.naissance = QDateEdit()
        self.naissance.setCalendarPopup(True)
        self.naissance.dateChanged.connect(self.update_age)

        self.age_label = QLabel("")

        self.classe = QLineEdit()

        self.niveau = QComboBox()
        self.niveau.addItems(NIVEAUX)

        self.enseignant = QLineEdit()

        form.addRow("Nom", self.nom)
        form.addRow("Prénom", self.prenom)
        form.addRow("Sexe", self.sexe)
        form.addRow("Date naissance", self.naissance)
        form.addRow("Âge", self.age_label)
        form.addRow("Classe", self.classe)
        form.addRow("Niveau", self.niveau)
        form.addRow("Enseignant (actuel)", self.enseignant)

        w.setLayout(form)
        self.tabs.addTab(w, "Identité")

    def update_age(self):
        d = self.naissance.date().toString("yyyy-MM-dd")
        self.age_label.setText(calc_age(d))


    # ----------------- ONGLET SYNTHESE / RECAP -----------------

    def tab_synthese(self):
        w = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Récapitulatif élève (mise à jour au chargement et à l'enregistrement)"))
        self.synth = QTextBrowser()
        self.synth.setOpenExternalLinks(True)
        self.synth.setMinimumHeight(400)

        btn_refresh = QPushButton("Rafraîchir la synthèse")
        btn_refresh.clicked.connect(self.refresh_synthese)

        layout.addWidget(self.synth)
        layout.addWidget(btn_refresh)
        w.setLayout(layout)
        self.tabs.addTab(w, "Synthèse")

    def refresh_synthese(self):
        if not self.current:
            self.synth.setHtml("<p>—</p>")
            return
        self.synth.setHtml(self.build_synthese_html())

    def build_synthese_html(self) -> str:
        # Identité
        nom = self._html_escape(self.nom.text().strip())
        prenom = self._html_escape(self.prenom.text().strip())
        sexe = self._html_escape(self.sexe.currentText())
        naissance = self._html_escape(self.naissance.date().toString("yyyy-MM-dd"))
        age = self._html_escape(self.age_label.text())
        classe = self._html_escape(self.classe.text().strip())
        niveau = self._html_escape(self.niveau.currentText())
        ens = self._html_escape(self.enseignant.text().strip())

        # Diagnostics
        diags = [self._html_escape(d) for d, cb in self.diag.items() if cb.isChecked()]
        autre = self._html_escape(self.diag_autre.toPlainText().strip())
        if autre:
            diags.append(f"Autre : {autre}")

        html = f"""
        <h1 style="margin-bottom:0;">{nom} {prenom}</h1>
        <p style="margin-top:4px;">
            <b>Sexe</b> : {sexe} &nbsp;|&nbsp;
            <b>Naissance</b> : {naissance} &nbsp;|&nbsp;
            <b>Âge</b> : {age}
        </p>
        <p>
            <b>Classe</b> : {classe} &nbsp;|&nbsp;
            <b>Niveau</b> : {niveau} &nbsp;|&nbsp;
            <b>Enseignant</b> : {ens}
        </p>

        <h2>Diagnostics / troubles</h2>
        <p>{("<br>".join(diags) if diags else "—")}</p>

        <h2>Suivis médicaux</h2>
        <ul>{self._html_list_from_table_suivis()}</ul>

        <h2>Dispositifs</h2>
        <ul>{self._html_list_from_table_dispositifs()}</ul>

        <h2>Réunions (REE / ESS)</h2>
        <ul>{self._html_list_from_table_reunions()}</ul>

        <h2>Observations</h2>
        <ul>{self._html_list_from_table_notes()}</ul>

        <h2>Historique enseignants</h2>
        <ul>{self._html_list_from_table_hist()}</ul>
        """
        return html

    def _html_list_from_table_hist(self) -> str:
        items = []
        for r in range(self.hist_table.rowCount()):
            annee = self.hist_table.item(r, 0).text() if self.hist_table.item(r, 0) else ""
            ens = self.hist_table.item(r, 1).text() if self.hist_table.item(r, 1) else ""
            niv = self.hist_table.item(r, 2).text() if self.hist_table.item(r, 2) else ""
            cla = self.hist_table.item(r, 3).text() if self.hist_table.item(r, 3) else ""
            txt = f"<li><b>{self._html_escape(annee)}</b> — {self._html_escape(ens)} — {self._html_escape(niv)} — {self._html_escape(cla)}</li>"
            if annee or ens or niv or cla:
                items.append(txt)
        return "\n".join(items) if items else "<li>—</li>"


    # ----------------- ONGLET DIAGNOSTICS -----------------

    def tab_diagnostics(self):
        w = QWidget()
        layout = QVBoxLayout()

        self.diag = {}
        for d in DIAGNOSTICS:
            cb = QCheckBox(d)
            self.diag[d] = cb
            layout.addWidget(cb)

        layout.addSpacing(8)
        layout.addWidget(QLabel("Autre (détails)"))
        self.diag_autre = QTextEdit()
        layout.addWidget(self.diag_autre)

        layout.addStretch(1)
        w.setLayout(layout)
        self.tabs.addTab(w, "Diagnostics")

    # ----------------- ONGLET SUIVIS -----------------

    def tab_suivis(self):
        w = QWidget()
        layout = QVBoxLayout()

        self.suivi_table = QTableWidget(0, 5)
        self.suivi_table.setHorizontalHeaderLabels(["Type", "Début", "Fin", "Professionnel", "Notes"])
        self.suivi_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.suivi_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.suivi_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed | QAbstractItemView.AnyKeyPressed)

        bar = QHBoxLayout()
        btn_add = QPushButton("Ajouter suivi")
        btn_add.clicked.connect(self.add_suivi_row)
        btn_del = QPushButton("Supprimer suivi")
        btn_del.clicked.connect(self.del_selected_rows_suivi)
        bar.addWidget(btn_add)
        bar.addWidget(btn_del)
        bar.addStretch(1)

        layout.addWidget(self.suivi_table)
        layout.addLayout(bar)
        w.setLayout(layout)
        self.tabs.addTab(w, "Suivis médicaux")

    def add_suivi_row(self):
        r = self.suivi_table.rowCount()
        self.suivi_table.insertRow(r)

        combo = QComboBox()
        combo.addItems(SUIVIS)
        self.suivi_table.setCellWidget(r, 0, combo)

        # items
        for c in range(1, 5):
            it = QTableWidgetItem("")
            self.suivi_table.setItem(r, c, it)

        # id caché dans UserRole d'un item (col 1)
        self.suivi_table.item(r, 1).setData(Qt.UserRole, str(uuid.uuid4()))

    def del_selected_rows_suivi(self):
        rows = sorted({i.row() for i in self.suivi_table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.suivi_table.removeRow(r)

    # ----------------- ONGLET DISPOSITIFS -----------------

    def tab_dispositifs(self):
        """
        Dispositifs (selon votre demande) :
        - Notification MDPH : Oui/Non
          - si Oui : AESH Individuel ou Mutualisé
          - Date de notification + Date de fin de validité
        - PAI : 3 choix (Alimentaire / Anxiété scolaire / Asthme) + Date début
        - PAP : coche + Date début
        - PPRE : coche + Date début + Date fin
        - + Aménagements + Notes (texte libre)
        """
        w = QWidget()
        form = QFormLayout()

        # ---- MDPH ----
        self.mdph_notif = QCheckBox("Notification MDPH (Oui)")
        self.mdph_type = QComboBox()
        self.mdph_type.addItems(["", "Individuel", "Mutualisé"])

        mdph_line = QHBoxLayout()
        mdph_line.addWidget(self.mdph_notif)
        mdph_line.addWidget(QLabel("AESH"))
        mdph_line.addWidget(self.mdph_type)
        mdph_w = QWidget(); mdph_w.setLayout(mdph_line)
        form.addRow("MDPH", mdph_w)

        self.mdph_date_notif = QLineEdit()
        self.mdph_date_notif.setPlaceholderText("Date notification (YYYY-MM-DD ou DD/MM/YYYY)")
        form.addRow("MDPH – Date notification", self.mdph_date_notif)

        self.mdph_date_fin_validite = QLineEdit()
        self.mdph_date_fin_validite.setPlaceholderText("Date fin de validité (YYYY-MM-DD ou DD/MM/YYYY)")
        form.addRow("MDPH – Fin validité", self.mdph_date_fin_validite)

        self.aesh_heures = QLineEdit()
        self.aesh_heures.setPlaceholderText("Heures AESH (ex: 12h)")
        form.addRow("AESH – Heures", self.aesh_heures)

        def _toggle_mdph():
            enabled = self.mdph_notif.isChecked()
            self.mdph_type.setEnabled(enabled)
            self.mdph_date_notif.setEnabled(enabled)
            self.mdph_date_fin_validite.setEnabled(enabled)
            self.aesh_heures.setEnabled(enabled)
        self.mdph_notif.stateChanged.connect(_toggle_mdph)
        _toggle_mdph()

        # ---- PAI ----
        self.pai_type = QComboBox()
        self.pai_type.addItems(["", "Alimentaire", "Anxiété scolaire", "Asthme"])

        self.pai_debut = QLineEdit()
        self.pai_debut.setPlaceholderText("Date début (YYYY-MM-DD ou DD/MM/YYYY)")

        pai_line = QHBoxLayout()
        pai_line.addWidget(QLabel("Type"))
        pai_line.addWidget(self.pai_type)
        pai_line.addWidget(QLabel("Début"))
        pai_line.addWidget(self.pai_debut)
        pai_w = QWidget(); pai_w.setLayout(pai_line)
        form.addRow("PAI", pai_w)

        # ---- PAP ----
        self.pap = QCheckBox("PAP")
        self.pap_debut = QLineEdit()
        self.pap_debut.setPlaceholderText("Date début (YYYY-MM-DD ou DD/MM/YYYY)")

        pap_line = QHBoxLayout()
        pap_line.addWidget(self.pap)
        pap_line.addWidget(QLabel("Début"))
        pap_line.addWidget(self.pap_debut)
        pap_w = QWidget(); pap_w.setLayout(pap_line)
        form.addRow("PAP", pap_w)

        # ---- PPRE ----
        self.ppre = QCheckBox("PPRE")
        self.ppre_debut = QLineEdit(); self.ppre_debut.setPlaceholderText("Date début (YYYY-MM-DD ou DD/MM/YYYY)")
        self.ppre_fin = QLineEdit(); self.ppre_fin.setPlaceholderText("Date fin (YYYY-MM-DD ou DD/MM/YYYY)")

        ppre_line = QHBoxLayout()
        ppre_line.addWidget(self.ppre)
        ppre_line.addWidget(QLabel("Début"))
        ppre_line.addWidget(self.ppre_debut)
        ppre_line.addWidget(QLabel("Fin"))
        ppre_line.addWidget(self.ppre_fin)
        ppre_w = QWidget(); ppre_w.setLayout(ppre_line)
        form.addRow("PPRE", ppre_w)

        # ---- Textes libres ----
        self.amenagements = QTextEdit()
        self.amenagements.setPlaceholderText("Aménagements pédagogiques (liste, consignes, évaluations, matériel...)")
        form.addRow("Aménagements", self.amenagements)

        self.disp_notes = QTextEdit()
        self.disp_notes.setPlaceholderText("Notes (documents, dates clés, infos utiles...)")
        form.addRow("Notes", self.disp_notes)

        w.setLayout(form)
        self.tabs.addTab(w, "Dispositifs")

    # ----------------- ONGLET REUNIONS -----------------


    def tab_reunions(self):
        w = QWidget()
        layout = QVBoxLayout()

        self.reunion_table = QTableWidget(0, 4)
        self.reunion_table.setHorizontalHeaderLabels(["Type", "Date", "Notes", "ID"])
        self.reunion_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.reunion_table.setColumnHidden(3, True)
        self.reunion_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        bar = QHBoxLayout()
        btn_add = QPushButton("Ajouter REE / ESS")
        btn_add.clicked.connect(self.add_reunion_row)
        btn_del = QPushButton("Supprimer réunion")
        btn_del.clicked.connect(self.del_selected_rows_reunions)
        bar.addWidget(btn_add)
        bar.addWidget(btn_del)
        bar.addStretch(1)

        layout.addWidget(self.reunion_table)
        layout.addLayout(bar)

        w.setLayout(layout)
        self.tabs.addTab(w, "REE / ESS")

    def add_reunion_row(self):
        r = self.reunion_table.rowCount()
        self.reunion_table.insertRow(r)

        combo = QComboBox()
        combo.addItems(["REE", "ESS"])
        self.reunion_table.setCellWidget(r, 0, combo)

        self.reunion_table.setItem(r, 1, QTableWidgetItem(""))
        self.reunion_table.setItem(r, 2, QTableWidgetItem(""))
        self.reunion_table.setItem(r, 3, QTableWidgetItem(str(uuid.uuid4())))

    def del_selected_rows_reunions(self):
        rows = sorted({i.row() for i in self.reunion_table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.reunion_table.removeRow(r)

    # ----------------- ONGLET NOTES -----------------

    def tab_notes(self):
        w = QWidget()
        layout = QVBoxLayout()

        self.notes_table = QTableWidget(0, 4)
        self.notes_table.setHorizontalHeaderLabels(["Date", "Catégorie", "Contenu", "ID"])
        self.notes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.notes_table.setColumnHidden(3, True)
        self.notes_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        bar = QHBoxLayout()
        btn_add = QPushButton("Ajouter note")
        btn_add.clicked.connect(self.add_note_row)
        btn_del = QPushButton("Supprimer note")
        btn_del.clicked.connect(self.del_selected_rows_notes)
        bar.addWidget(btn_add)
        bar.addWidget(btn_del)
        bar.addStretch(1)

        layout.addWidget(self.notes_table)
        layout.addLayout(bar)

        w.setLayout(layout)
        self.tabs.addTab(w, "Observations")

    def add_note_row(self):
        r = self.notes_table.rowCount()
        self.notes_table.insertRow(r)
        self.notes_table.setItem(r, 0, QTableWidgetItem(date.today().strftime("%Y-%m-%d")))
        self.notes_table.setItem(r, 1, QTableWidgetItem(""))
        self.notes_table.setItem(r, 2, QTableWidgetItem(""))
        self.notes_table.setItem(r, 3, QTableWidgetItem(str(uuid.uuid4())))

    def del_selected_rows_notes(self):
        rows = sorted({i.row() for i in self.notes_table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.notes_table.removeRow(r)

    # ----------------- ONGLET HISTORIQUE ENSEIGNANTS -----------------

    def tab_historique_enseignants(self):
        w = QWidget()
        layout = QVBoxLayout()

        self.hist_table = QTableWidget(0, 6)
        self.hist_table.setHorizontalHeaderLabels(["Année", "Enseignant", "Niveau", "Classe", "ID", ""])
        self.hist_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.hist_table.setColumnHidden(4, True)
        self.hist_table.setColumnHidden(5, True)
        self.hist_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        bar = QHBoxLayout()
        btn_add = QPushButton("Ajouter année")
        btn_add.clicked.connect(self.add_hist_row)
        btn_del = QPushButton("Supprimer")
        btn_del.clicked.connect(self.del_selected_rows_hist)
        bar.addWidget(btn_add)
        bar.addWidget(btn_del)
        bar.addStretch(1)

        layout.addWidget(self.hist_table)
        layout.addLayout(bar)

        w.setLayout(layout)
        self.tabs.addTab(w, "Historique enseignants")

    def add_hist_row(self):
        r = self.hist_table.rowCount()
        self.hist_table.insertRow(r)
        self.hist_table.setItem(r, 0, QTableWidgetItem(f"{date.today().year}-{date.today().year+1}"))
        self.hist_table.setItem(r, 1, QTableWidgetItem(""))
        self.hist_table.setItem(r, 2, QTableWidgetItem(""))
        self.hist_table.setItem(r, 3, QTableWidgetItem(""))
        self.hist_table.setItem(r, 4, QTableWidgetItem(str(uuid.uuid4())))
        self.hist_table.setItem(r, 5, QTableWidgetItem(""))

    def del_selected_rows_hist(self):
        rows = sorted({i.row() for i in self.hist_table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.hist_table.removeRow(r)

    # ----------------- LISTE / CRUD ELEVES -----------------

    def refresh(self):
        q = (self.search.text() or "").lower().strip()

        actif_val = 0 if getattr(self, 'show_archived', False) else 1

        # rafraîchir la liste des classes
        classes = [r[0] for r in self.conn.execute(
            f"SELECT DISTINCT classe FROM eleves WHERE actif={actif_val} AND classe IS NOT NULL AND TRIM(classe)<>'' ORDER BY classe"
        ).fetchall()]
        cur = self.filter_classe.currentText() if hasattr(self, "filter_classe") else "Toutes les classes"
        self.filter_classe.blockSignals(True)
        self.filter_classe.clear()
        self.filter_classe.addItem("Toutes les classes")
        for c in classes:
            self.filter_classe.addItem(c)
        # restaurer selection si possible
        idx = self.filter_classe.findText(cur)
        self.filter_classe.setCurrentIndex(idx if idx >= 0 else 0)
        self.filter_classe.blockSignals(False)

        sel_classe = self.filter_classe.currentText()
        sel_disp = self.filter_dispositif.currentText()

        # base query
        params = []
        where = [f"actif={actif_val}"]

        if sel_classe and sel_classe != "Toutes les classes":
            where.append("classe=?")
            params.append(sel_classe)

        # dispositif filter (via join dispositifs_eleve)
        join = ""
        if sel_disp and sel_disp != "Tous dispositifs":
            join = "LEFT JOIN dispositifs_eleve de ON de.eleve_id = e.id"
            if sel_disp == "MDPH":
                where.append("COALESCE(de.mdph_notif,0)=1")
            elif sel_disp == "AESH Individuel":
                where.append("COALESCE(de.mdph_notif,0)=1 AND COALESCE(de.mdph_type,'')='Individuel'")
            elif sel_disp == "AESH Mutualisé":
                where.append("COALESCE(de.mdph_notif,0)=1 AND COALESCE(de.mdph_type,'')='Mutualisé'")
            elif sel_disp == "PAI Alimentaire":
                where.append("COALESCE(de.pai_type,'')='Alimentaire'")
            elif sel_disp == "PAI Anxiété scolaire":
                where.append("COALESCE(de.pai_type,'')='Anxiété scolaire'")
            elif sel_disp == "PAI Asthme":
                where.append("COALESCE(de.pai_type,'')='Asthme'")
            elif sel_disp == "PAP":
                where.append("COALESCE(de.pap,0)=1")
            elif sel_disp == "PPRE":
                where.append("COALESCE(de.ppre,0)=1")

        sql = f"SELECT e.* FROM eleves e {join} WHERE " + " AND ".join(where) + " ORDER BY e.nom, e.prenom"
        rows = self.conn.execute(sql, tuple(params)).fetchall()

        self.list.clear()
        for r in rows:
            name = f"{r['nom'] or ''} {r['prenom'] or ''}".strip()
            if not q or q in name.lower():
                item = QListWidgetItem(name if name else "(Sans nom)")
                item.setData(Qt.UserRole, r["id"])
                self.list.addItem(item)

    def new(self):
        eid = str(uuid.uuid4())
        self.conn.execute("INSERT INTO eleves(id,nom,prenom) VALUES(?,?,?)", (eid, "NOM", "Prénom"))
        self.conn.commit()
        self.refresh()
        self.status.setText("Élève créé. Cliquez dessus pour le renseigner.")

    def clear_child_tabs(self):
        # diagnostics
        for cb in self.diag.values():
            cb.setChecked(False)
        self.diag_autre.setPlainText("")

        # tables
        for tbl in (self.suivi_table, self.reunion_table, self.notes_table, self.hist_table):
            tbl.setRowCount(0)

        # dispositifs (fiche)
        if hasattr(self, 'mdph_notif'):
            self.mdph_notif.setChecked(False)
            self.mdph_type.setCurrentText('')
            self.mdph_date_notif.setText('')
            self.mdph_date_fin_validite.setText('')
            self.aesh_heures.setText('')
            self.pai_type.setCurrentText('')
            self.pai_debut.setText('')
            self.pap.setChecked(False)
            self.pap_debut.setText('')
            self.ppre.setChecked(False)
            self.ppre_debut.setText('')
            self.ppre_fin.setText('')
            self.amenagements.setPlainText('')
            self.disp_notes.setPlainText('')

    def load(self, item: QListWidgetItem):
        eid = item.data(Qt.UserRole)
        self.current = eid

        r = self.conn.execute("SELECT * FROM eleves WHERE id=?", (eid,)).fetchone()
        if not r:
            return

        self.nom.setText(r["nom"] or "")
        self.prenom.setText(r["prenom"] or "")
        self.sexe.setCurrentText(r["sexe"] or "")
        self.classe.setText(r["classe"] or "")
        self.niveau.setCurrentText(r["niveau"] or "")
        self.enseignant.setText(r["enseignant"] or "")

        if r["naissance"]:
            try:
                y, m, d = map(int, r["naissance"].split("-"))
                self.naissance.setDate(QDate(y, m, d))
            except Exception:
                self.naissance.setDate(QDate.currentDate())
        else:
            self.naissance.setDate(QDate.currentDate())
        self.update_age()

        self.clear_child_tabs()

        # --- diagnostics ---
        checked = set(x["diag"] for x in self.conn.execute(
            "SELECT diag FROM eleve_diagnostics WHERE eleve_id=?", (eid,)
        ).fetchall())
        for d, cb in self.diag.items():
            cb.setChecked(d in checked)

        autre = self.conn.execute(
            "SELECT details FROM eleve_diag_autre WHERE eleve_id=?", (eid,)
        ).fetchone()
        self.diag_autre.setPlainText(autre["details"] if autre and autre["details"] else "")

        # --- suivis ---
        suivis = self.conn.execute("""
            SELECT * FROM suivis WHERE eleve_id=? ORDER BY debut, type
        """, (eid,)).fetchall()
        self.suivi_table.setRowCount(0)
        for s in suivis:
            r = self.suivi_table.rowCount()
            self.suivi_table.insertRow(r)
            combo = QComboBox()
            combo.addItems(SUIVIS)
            combo.setCurrentText(s["type"] or "")
            self.suivi_table.setCellWidget(r, 0, combo)

            it_debut = QTableWidgetItem(s["debut"] or "")
            it_debut.setData(Qt.UserRole, s["id"])  # id caché
            self.suivi_table.setItem(r, 1, it_debut)
            self.suivi_table.setItem(r, 2, QTableWidgetItem(s["fin"] or ""))
            self.suivi_table.setItem(r, 3, QTableWidgetItem(s["professionnel"] or ""))
            self.suivi_table.setItem(r, 4, QTableWidgetItem(s["notes"] or ""))

        # --- dispositifs (fiche) ---
        de = self.conn.execute("""
            SELECT * FROM dispositifs_eleve WHERE eleve_id=?
        """, (eid,)).fetchone()

        if de:
            self.mdph_notif.setChecked((de["mdph_notif"] or 0) == 1)
            self.mdph_type.setCurrentText(de["mdph_type"] or "")
            self.mdph_date_notif.setText(de["mdph_date_notif"] or "")
            self.mdph_date_fin_validite.setText(de["mdph_date_fin_validite"] or "")
            self.aesh_heures.setText(de["aesh_heures"] or "")

            self.pai_type.setCurrentText(de["pai_type"] or "")
            self.pai_debut.setText(de["pai_debut"] or "")

            self.pap.setChecked((de["pap"] or 0) == 1)
            self.pap_debut.setText(de["pap_debut"] or "")

            self.ppre.setChecked((de["ppre"] or 0) == 1)
            self.ppre_debut.setText(de["ppre_debut"] or "")
            self.ppre_fin.setText(de["ppre_fin"] or "")

            self.amenagements.setPlainText(de["amenagements"] or "")
            self.disp_notes.setPlainText(de["notes"] or "")

        # --- réunions ---
        reus = self.conn.execute("""
            SELECT * FROM reunions WHERE eleve_id=? ORDER BY d DESC
        """, (eid,)).fetchall()
        self.reunion_table.setRowCount(0)
        for rr in reus:
            r = self.reunion_table.rowCount()
            self.reunion_table.insertRow(r)
            combo = QComboBox()
            combo.addItems(["REE", "ESS"])
            combo.setCurrentText(rr["type"] or "REE")
            self.reunion_table.setCellWidget(r, 0, combo)
            self.reunion_table.setItem(r, 1, QTableWidgetItem(rr["d"] or ""))
            self.reunion_table.setItem(r, 2, QTableWidgetItem(rr["notes"] or ""))
            self.reunion_table.setItem(r, 3, QTableWidgetItem(rr["id"]))

        # --- notes ---
        notes = self.conn.execute("""
            SELECT * FROM notes WHERE eleve_id=? ORDER BY d DESC
        """, (eid,)).fetchall()
        self.notes_table.setRowCount(0)
        for n in notes:
            r = self.notes_table.rowCount()
            self.notes_table.insertRow(r)
            self.notes_table.setItem(r, 0, QTableWidgetItem(n["d"] or ""))
            self.notes_table.setItem(r, 1, QTableWidgetItem(n["categorie"] or ""))
            self.notes_table.setItem(r, 2, QTableWidgetItem(n["contenu"] or ""))
            self.notes_table.setItem(r, 3, QTableWidgetItem(n["id"]))

        # --- historique enseignants ---
        hs = self.conn.execute("""
            SELECT * FROM enseignants WHERE eleve_id=? ORDER BY annee DESC
        """, (eid,)).fetchall()
        self.hist_table.setRowCount(0)
        for h in hs:
            r = self.hist_table.rowCount()
            self.hist_table.insertRow(r)
            self.hist_table.setItem(r, 0, QTableWidgetItem(h["annee"] or ""))
            self.hist_table.setItem(r, 1, QTableWidgetItem(h["enseignant"] or ""))
            self.hist_table.setItem(r, 2, QTableWidgetItem(h["niveau"] or ""))
            self.hist_table.setItem(r, 3, QTableWidgetItem(h["classe"] or ""))
            self.hist_table.setItem(r, 4, QTableWidgetItem(h["id"]))
            self.hist_table.setItem(r, 5, QTableWidgetItem(""))

        self.status.setText("Élève chargé ✅")
        self.refresh_synthese()

    # ----------------- SAUVEGARDE -----------------

    def save_all(self):
        if not self.current:
            QMessageBox.information(self, "Info", "Sélectionnez un élève.")
            return

        eid = self.current

        # Identité
        dob = self.naissance.date().toString("yyyy-MM-dd")
        self.conn.execute("""
            UPDATE eleves SET
            nom=?, prenom=?, sexe=?, naissance=?,
            niveau=?, classe=?, enseignant=?
            WHERE id=?
        """, (
            self.nom.text().strip(),
            self.prenom.text().strip(),
            self.sexe.currentText(),
            dob,
            self.niveau.currentText(),
            self.classe.text().strip(),
            self.enseignant.text().strip(),
            eid
        ))

        # Diagnostics (replace)
        self.conn.execute("DELETE FROM eleve_diagnostics WHERE eleve_id=?", (eid,))
        for d, cb in self.diag.items():
            if cb.isChecked():
                self.conn.execute("INSERT OR REPLACE INTO eleve_diagnostics(eleve_id, diag) VALUES(?,?)", (eid, d))

        self.conn.execute("DELETE FROM eleve_diag_autre WHERE eleve_id=?", (eid,))
        details = self.diag_autre.toPlainText().strip()
        if details:
            self.conn.execute("INSERT OR REPLACE INTO eleve_diag_autre(eleve_id, details) VALUES(?,?)", (eid, details))

        # Suivis (replace)
        self.conn.execute("DELETE FROM suivis WHERE eleve_id=?", (eid,))
        for r in range(self.suivi_table.rowCount()):
            combo = self.suivi_table.cellWidget(r, 0)
            typ = combo.currentText() if combo else ""
            debut = (self.suivi_table.item(r, 1).text() if self.suivi_table.item(r, 1) else "").strip()
            fin = (self.suivi_table.item(r, 2).text() if self.suivi_table.item(r, 2) else "").strip()
            pro = (self.suivi_table.item(r, 3).text() if self.suivi_table.item(r, 3) else "").strip()
            notes = (self.suivi_table.item(r, 4).text() if self.suivi_table.item(r, 4) else "").strip()

            sid = None
            it = self.suivi_table.item(r, 1)
            if it is not None:
                sid = it.data(Qt.UserRole)
            if not sid:
                sid = str(uuid.uuid4())

            # normaliser dates si possible
            debut_iso = parse_date_any(debut) or debut
            fin_iso = parse_date_any(fin) or fin

            if typ or debut_iso or fin_iso or pro or notes:
                self.conn.execute("""
                    INSERT INTO suivis(id, eleve_id, type, debut, fin, professionnel, notes)
                    VALUES(?,?,?,?,?,?,?)
                """, (sid, eid, typ, debut_iso, fin_iso, pro, notes))

        # Réunions (replace)
        self.conn.execute("DELETE FROM reunions WHERE eleve_id=?", (eid,))
        for r in range(self.reunion_table.rowCount()):
            combo = self.reunion_table.cellWidget(r, 0)
            typ = combo.currentText() if combo else "REE"
            d = (self.reunion_table.item(r, 1).text() if self.reunion_table.item(r, 1) else "").strip()
            notes = (self.reunion_table.item(r, 2).text() if self.reunion_table.item(r, 2) else "").strip()
            rid = (self.reunion_table.item(r, 3).text() if self.reunion_table.item(r, 3) else "").strip() or str(uuid.uuid4())

            d_iso = parse_date_any(d) or d

            if typ or d_iso or notes:
                self.conn.execute("""
                    INSERT INTO reunions(id, eleve_id, type, d, notes)
                    VALUES(?,?,?,?,?)
                """, (rid, eid, typ, d_iso, notes))


        # Dispositifs (fiche) : 1 ligne/élève
        self.conn.execute("DELETE FROM dispositifs_eleve WHERE eleve_id=?", (eid,))

        mdph_notif = 1 if self.mdph_notif.isChecked() else 0
        mdph_type = self.mdph_type.currentText().strip() if mdph_notif else ""
        mdph_date_notif = parse_date_any(self.mdph_date_notif.text().strip()) or self.mdph_date_notif.text().strip()
        mdph_date_fin = parse_date_any(self.mdph_date_fin_validite.text().strip()) or self.mdph_date_fin_validite.text().strip()
        aesh_heures = self.aesh_heures.text().strip() if mdph_notif else ""

        pai_type = self.pai_type.currentText().strip()
        pai_debut = parse_date_any(self.pai_debut.text().strip()) or self.pai_debut.text().strip()

        pap = 1 if self.pap.isChecked() else 0
        pap_debut = parse_date_any(self.pap_debut.text().strip()) or self.pap_debut.text().strip()

        ppre = 1 if self.ppre.isChecked() else 0
        ppre_debut = parse_date_any(self.ppre_debut.text().strip()) or self.ppre_debut.text().strip()
        ppre_fin = parse_date_any(self.ppre_fin.text().strip()) or self.ppre_fin.text().strip()

        amen = self.amenagements.toPlainText().strip()
        notes_disp = self.disp_notes.toPlainText().strip()

        if (mdph_notif or mdph_type or mdph_date_notif or mdph_date_fin or aesh_heures or
            pai_type or pai_debut or
            pap or pap_debut or
            ppre or ppre_debut or ppre_fin or
            amen or notes_disp):
            self.conn.execute("""
                INSERT INTO dispositifs_eleve(
                    eleve_id,
                    mdph_notif, mdph_type, mdph_date_notif, mdph_date_fin_validite, aesh_heures,
                    pai_type, pai_debut,
                    pap, pap_debut,
                    ppre, ppre_debut, ppre_fin,
                    amenagements, notes
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                eid,
                mdph_notif, mdph_type, mdph_date_notif, mdph_date_fin, aesh_heures,
                pai_type, pai_debut,
                pap, pap_debut,
                ppre, ppre_debut, ppre_fin,
                amen, notes_disp
            ))

        # Notes (replace)

        self.conn.execute("DELETE FROM notes WHERE eleve_id=?", (eid,))
        for r in range(self.notes_table.rowCount()):
            d = (self.notes_table.item(r, 0).text() if self.notes_table.item(r, 0) else "").strip()
            cat = (self.notes_table.item(r, 1).text() if self.notes_table.item(r, 1) else "").strip()
            contenu = (self.notes_table.item(r, 2).text() if self.notes_table.item(r, 2) else "").strip()
            nid = (self.notes_table.item(r, 3).text() if self.notes_table.item(r, 3) else "").strip() or str(uuid.uuid4())

            d_iso = parse_date_any(d) or d

            if d_iso or cat or contenu:
                self.conn.execute("""
                    INSERT INTO notes(id, eleve_id, d, categorie, contenu)
                    VALUES(?,?,?,?,?)
                """, (nid, eid, d_iso, cat, contenu))

        # Historique enseignants (replace)
        self.conn.execute("DELETE FROM enseignants WHERE eleve_id=?", (eid,))
        for r in range(self.hist_table.rowCount()):
            annee = (self.hist_table.item(r, 0).text() if self.hist_table.item(r, 0) else "").strip()
            ens = (self.hist_table.item(r, 1).text() if self.hist_table.item(r, 1) else "").strip()
            niv = (self.hist_table.item(r, 2).text() if self.hist_table.item(r, 2) else "").strip()
            cla = (self.hist_table.item(r, 3).text() if self.hist_table.item(r, 3) else "").strip()
            hid = (self.hist_table.item(r, 4).text() if self.hist_table.item(r, 4) else "").strip() or str(uuid.uuid4())

            if annee or ens or niv or cla:
                self.conn.execute("""
                    INSERT INTO enseignants(id, eleve_id, annee, enseignant, niveau, classe)
                    VALUES(?,?,?,?,?,?)
                """, (hid, eid, annee, ens, niv, cla))

        self.conn.commit()
        self.refresh()
        self.status.setText("Enregistré ✅ (toutes les sections)")

        # Sauvegarde automatique après enregistrement
        sauvegarde_auto("save")
        self.refresh_synthese()

    # ----------------- IMPORT / EXPORT CSV -----------------


    def _import_csv_core(self, sync_mode: bool = False):
        """
        Import CSV / ONDE :
        - met à jour les élèves existants
        - ajoute les nouveaux
        - si sync_mode=True et format ONDE : archive les élèves absents du fichier
        """
        title = "Synchroniser avec ONDE" if sync_mode else "Importer ONDE / CSV"
        path, _ = QFileDialog.getOpenFileName(self, title, "", "CSV (*.csv)")
        if not path:
            return

        with open(path, "r", encoding="utf8", newline="") as f:
            sample = f.read(4096)
            delim = detect_delimiter(sample)
            f.seek(0)
            reader = csv.DictReader(f, delimiter=delim)

            if not reader.fieldnames:
                QMessageBox.critical(self, "Import", "Fichier CSV vide ou illisible.")
                return

            is_onde = ("Libellé classe" in reader.fieldnames) or ("Identifiant classe" in reader.fieldnames) or ("INE" in reader.fieldnames)

            required_common = ["Nom élève", "Prénom élève", "Sexe", "Niveau", "Date naissance"]
            for h in required_common:
                if h not in reader.fieldnames:
                    QMessageBox.critical(self, "Import", "En-têtes CSV incorrects.\nChamps requis :\n" + "\n".join(required_common))
                    return

            if is_onde:
                if "Libellé classe" not in reader.fieldnames:
                    QMessageBox.critical(self, "Import", "CSV ONDE détecté mais colonne manquante : Libellé classe")
                    return
            else:
                if "Classe" not in reader.fieldnames:
                    QMessageBox.critical(
                        self,
                        "Import",
                        "CSV détecté (format interne) mais colonne manquante : Classe\n"
                        "Soit exportez depuis ONDE, soit utilisez les en-têtes internes."
                    )
                    return

            if sync_mode and not is_onde:
                QMessageBox.warning(self, "Synchronisation", "La synchronisation est réservée au format ONDE.")
                return

            n_new = 0
            n_upd = 0
            n_arch = 0
            imported_keys = set()

            for row in reader:
                nom = (row.get("Nom élève") or "").strip()
                prenom = (row.get("Prénom élève") or "").strip()
                sexe = (row.get("Sexe") or "").strip()
                niveau = (row.get("Niveau") or "").strip()
                naissance = parse_date_any(row.get("Date naissance") or "")

                if not (nom or prenom):
                    continue

                key = ((nom or "").lower(), (prenom or "").lower(), naissance or "")
                imported_keys.add(key)

                if is_onde:
                    lib = (row.get("Libellé classe") or "").strip()
                    classe, enseignant = parse_libelle_classe(lib)
                else:
                    classe = (row.get("Classe") or "").strip()
                    enseignant = (row.get("Enseignant") or "").strip() if "Enseignant" in reader.fieldnames else ""

                existing = self.conn.execute(
                    "SELECT id FROM eleves WHERE lower(nom)=lower(?) AND lower(prenom)=lower(?) AND naissance=? LIMIT 1",
                    (nom, prenom, naissance)
                ).fetchone()

                if existing:
                    eleve_id = existing["id"]
                    self.conn.execute("""
                        UPDATE eleves
                        SET sexe=?, niveau=?, classe=?, enseignant=?, actif=1
                        WHERE id=?
                    """, (sexe, niveau, classe, enseignant, eleve_id))
                    n_upd += 1
                else:
                    eleve_id = str(uuid.uuid4())
                    self.conn.execute("""
                        INSERT INTO eleves(id, nom, prenom, sexe, naissance, niveau, classe, enseignant, actif)
                        VALUES(?,?,?,?,?,?,?,?,1)
                    """, (eleve_id, nom, prenom, sexe, naissance, niveau, classe, enseignant))
                    n_new += 1

                if is_onde:
                    ine = (row.get("INE") or "").strip()
                    adresse1 = (row.get("Adresse1") or "").strip()
                    cp1 = (row.get("Cp1") or "").strip()
                    commune1 = (row.get("Commune1") or "").strip()
                    autor_photo = (row.get("Autorisation photo") or "").strip()
                    dispositif = (row.get("Dispositif(s)") or "").strip()
                    regroup = (row.get("Regroupement(s)") or "").strip()
                    cycle = (row.get(" Cycle") or row.get("Cycle") or "").strip()
                    ident_classe = (row.get("Identifiant classe") or "").strip()

                    self.conn.execute("""
                        INSERT INTO onde_infos(eleve_id, ine, adresse1, cp1, commune1, autorisation_photo, dispositif, regroupement, cycle, identifiant_classe)
                        VALUES(?,?,?,?,?,?,?,?,?,?)
                        ON CONFLICT(eleve_id) DO UPDATE SET
                            ine=excluded.ine,
                            adresse1=excluded.adresse1,
                            cp1=excluded.cp1,
                            commune1=excluded.commune1,
                            autorisation_photo=excluded.autorisation_photo,
                            dispositif=excluded.dispositif,
                            regroupement=excluded.regroupement,
                            cycle=excluded.cycle,
                            identifiant_classe=excluded.identifiant_classe
                    """, (eleve_id, ine, adresse1, cp1, commune1, autor_photo, dispositif, regroup, cycle, ident_classe))

            if sync_mode and is_onde:
                rows = self.conn.execute("SELECT id, nom, prenom, naissance FROM eleves WHERE actif=1").fetchall()
                to_archive = []
                for r in rows:
                    key = ((r["nom"] or "").lower(), (r["prenom"] or "").lower(), (r["naissance"] or ""))
                    if key not in imported_keys:
                        to_archive.append(r["id"])
                for eid in to_archive:
                    self.conn.execute("UPDATE eleves SET actif=0 WHERE id=?", (eid,))
                n_arch = len(to_archive)

            self.conn.commit()

        self.refresh()
        if sync_mode and is_onde:
            QMessageBox.information(
                self,
                "Synchronisation ONDE",
                f"Synchronisation terminée ✅\n\nNouveaux élèves : {n_new}\nMis à jour : {n_upd}\nArchivés (absents du fichier ONDE) : {n_arch}"
            )
        else:
            QMessageBox.information(
                self,
                "Import",
                f"Import terminé ✅\n\nNouveaux élèves : {n_new}\nMis à jour : {n_upd}\n\nFormat : {'ONDE' if is_onde else 'CSV interne'}"
            )

    def import_csv(self):
        self._import_csv_core(sync_mode=False)

    def synchroniser_onde(self):
        rep = QMessageBox.question(
            self,
            "Synchroniser avec ONDE",
            "La synchronisation va :\n"
            "- mettre à jour les élèves présents dans le fichier ONDE\n"
            "- ajouter les nouveaux élèves\n"
            "- archiver les élèves absents du fichier ONDE\n\n"
            "Aucune donnée ne sera supprimée.\n\nContinuer ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if rep != QMessageBox.Yes:
            return
        self._import_csv_core(sync_mode=True)

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exporter CSV école", os.path.expanduser("~/Desktop/ecole_export.csv"), "CSV (*.csv)")
        if not path:
            return

        rows = self.conn.execute("SELECT * FROM eleves WHERE actif=1 ORDER BY classe, nom, prenom").fetchall()

        with open(path, "w", newline="", encoding="utf8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Nom", "Prénom", "Sexe", "Date naissance", "Niveau", "Classe", "Enseignant"])
            for r in rows:
                writer.writerow([r["nom"], r["prenom"], r["sexe"], r["naissance"], r["niveau"], r["classe"], r["enseignant"]])

        QMessageBox.information(self, "Export", "Export CSV réalisé ✅")

    # ----------------- PDF -----------------

    def export_pdf_fiche(self):
        """Export PDF fiable (V10 PRO + correctif PDF)."""
        if not self.current:
            QMessageBox.information(self, "PDF", "Sélectionnez un élève.")
            return

        try:
            def safe_html_list(*method_names, empty_li="<li>—</li>"):
                for mn in method_names:
                    fn = getattr(self, mn, None)
                    if callable(fn):
                        try:
                            out = fn()
                            return out if (out and out.strip()) else empty_li
                        except Exception:
                            return empty_li
                return empty_li

            name = f"{self.nom.text()}_{self.prenom.text()}".strip().replace(" ", "_") or "eleve"
            default_path = os.path.join(EXPORT_DIR, f"{name}_fiche.pdf")

            path, _ = QFileDialog.getSaveFileName(
                self,
                "Enregistrer la fiche élève (PDF)",
                default_path,
                "PDF (*.pdf)"
            )
            if not path:
                return
            if not path.lower().endswith(".pdf"):
                path += ".pdf"

            diags = [d for d, cb in self.diag.items() if cb.isChecked()]
            autre = self.diag_autre.toPlainText().strip()
            if autre:
                diags.append(f"Autre : {autre}")

            html = f"""
            <h1>{self._html_escape(self.nom.text())} {self._html_escape(self.prenom.text())}</h1>
            <p>
                <b>Classe</b> : {self._html_escape(self.classe.text())}
                &nbsp;&nbsp; <b>Niveau</b> : {self._html_escape(self.niveau.currentText())}
                &nbsp;&nbsp; <b>Enseignant</b> : {self._html_escape(self.enseignant.text())}
            </p>
            <p>
                <b>Date naissance</b> : {self.naissance.date().toString("yyyy-MM-dd")}
                &nbsp;&nbsp; <b>Âge</b> : {self._html_escape(self.age_label.text())}
            </p>

            <h2>Diagnostics / troubles</h2>
            <p>{("<br>".join([self._html_escape(x) for x in diags])) if diags else "—"}</p>

            <h2>Suivis médicaux</h2>
            <ul>{safe_html_list("_html_list_from_table_suivis")}</ul>

            <h2>Dispositifs</h2>
            <ul>{safe_html_list("_html_list_from_table_dispositifs")}</ul>

            <h2>Réunions</h2>
            <ul>{safe_html_list("_html_list_from_table_reunions")}</ul>

            <h2>Notes</h2>
            <ul>{safe_html_list("_html_list_from_table_notes")}</ul>

            <h2>Historique enseignants</h2>
            <ul>{safe_html_list("_html_list_from_table_historique", "_html_list_from_table_hist")}</ul>
            """

            doc = QTextDocument()
            doc.setHtml(html)

            printer = QPrinter()
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            doc.print_(printer)

            QMessageBox.information(self, "PDF (V10 PRO FIX)", f"Fiche élève exportée ✅\n\nEmplacement :\n{path}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

        except Exception as e:
            QMessageBox.critical(self, "PDF (V10 PRO FIX)", f"Erreur lors de l'export PDF :\n{e}")


    def _html_escape(self, s: str) -> str:
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _html_list_from_table_suivis(self) -> str:
        items = []
        for r in range(self.suivi_table.rowCount()):
            combo = self.suivi_table.cellWidget(r, 0)
            typ = combo.currentText() if combo else ""
            debut = self.suivi_table.item(r, 1).text() if self.suivi_table.item(r, 1) else ""
            fin = self.suivi_table.item(r, 2).text() if self.suivi_table.item(r, 2) else ""
            pro = self.suivi_table.item(r, 3).text() if self.suivi_table.item(r, 3) else ""
            notes = self.suivi_table.item(r, 4).text() if self.suivi_table.item(r, 4) else ""
            txt = f"<li><b>{self._html_escape(typ)}</b> {self._html_escape(debut)} → {self._html_escape(fin)} — {self._html_escape(pro)}<br>{self._html_escape(notes)}</li>"
            if (typ or debut or fin or pro or notes):
                items.append(txt)
        return "\n".join(items) if items else "<li>—</li>"

    def _html_list_from_table_dispositifs(self) -> str:
        items = []

        if self.mdph_notif.isChecked():
            items.append(
                "<li><b>Notification MDPH</b> — AESH : "
                f"{self._html_escape(self.mdph_type.currentText())}<br>"
                f"Date notification : {self._html_escape(self.mdph_date_notif.text())}<br>"
                f"Fin validité : {self._html_escape(self.mdph_date_fin_validite.text())}<br>"
                f"Heures AESH : {self._html_escape(self.aesh_heures.text())}</li>"
            )

        if self.pai_type.currentText().strip() or self.pai_debut.text().strip():
            items.append(
                f"<li><b>PAI</b> — {self._html_escape(self.pai_type.currentText())}"
                f" — Début : {self._html_escape(self.pai_debut.text())}</li>"
            )

        if self.pap.isChecked() or self.pap_debut.text().strip():
            items.append(f"<li><b>PAP</b> — Début : {self._html_escape(self.pap_debut.text())}</li>")

        if self.ppre.isChecked() or self.ppre_debut.text().strip() or self.ppre_fin.text().strip():
            items.append(
                f"<li><b>PPRE</b> — {self._html_escape(self.ppre_debut.text())} → {self._html_escape(self.ppre_fin.text())}</li>"
            )

        amen = self.amenagements.toPlainText().strip()
        if amen:
            items.append(f"<li><b>Aménagements</b><br>{self._html_escape(amen)}</li>")

        notes = self.disp_notes.toPlainText().strip()
        if notes:
            items.append(f"<li><b>Notes</b><br>{self._html_escape(notes)}</li>")

        return "\n".join(items) if items else "<li>—</li>"

    def _html_list_from_table_reunions(self) -> str:
        items = []
        for r in range(self.reunion_table.rowCount()):
            combo = self.reunion_table.cellWidget(r, 0)
            typ = combo.currentText() if combo else ""
            d = self.reunion_table.item(r, 1).text() if self.reunion_table.item(r, 1) else ""
            notes = self.reunion_table.item(r, 2).text() if self.reunion_table.item(r, 2) else ""
            txt = f"<li><b>{self._html_escape(typ)}</b> — {self._html_escape(d)}<br>{self._html_escape(notes)}</li>"
            if (typ or d or notes):
                items.append(txt)
        return "\n".join(items) if items else "<li>—</li>"

    def _html_list_from_table_notes(self) -> str:
        items = []
        for r in range(self.notes_table.rowCount()):
            d = self.notes_table.item(r, 0).text() if self.notes_table.item(r, 0) else ""
            cat = self.notes_table.item(r, 1).text() if self.notes_table.item(r, 1) else ""
            contenu = self.notes_table.item(r, 2).text() if self.notes_table.item(r, 2) else ""
            txt = f"<li><b>{self._html_escape(d)}</b> [{self._html_escape(cat)}] — {self._html_escape(contenu)}</li>"
            if (d or cat or contenu):
                items.append(txt)
        return "\n".join(items) if items else "<li>—</li>"

    def export_pdf_classe(self):
        """Export PDF liste élèves (V10 PRO + correctif PDF)."""
        try:
            sel_classe = self.filter_classe.currentText() if hasattr(self, "filter_classe") else "Toutes les classes"
            sel_disp = self.filter_dispositif.currentText() if hasattr(self, "filter_dispositif") else "Tous dispositifs"

            title = "Liste élèves"
            if sel_classe and sel_classe != "Toutes les classes":
                title += f" — {sel_classe}"
            if sel_disp and sel_disp != "Tous dispositifs":
                title += f" — {sel_disp}"

            default_path = os.path.join(EXPORT_DIR, "liste_eleves.pdf")
            path, _ = QFileDialog.getSaveFileName(self, "Enregistrer la liste (PDF)", default_path, "PDF (*.pdf)")
            if not path:
                return
            if not path.lower().endswith(".pdf"):
                path += ".pdf"

            params = []
            where = ["e.actif=1"]
            join = ""

            if sel_classe and sel_classe != "Toutes les classes":
                where.append("e.classe=?")
                params.append(sel_classe)

            if sel_disp and sel_disp != "Tous dispositifs":
                join = "LEFT JOIN dispositifs_eleve de ON de.eleve_id = e.id"
                if sel_disp == "MDPH":
                    where.append("COALESCE(de.mdph_notif,0)=1")
                elif sel_disp == "AESH Individuel":
                    where.append("COALESCE(de.mdph_notif,0)=1 AND COALESCE(de.mdph_type,'')='Individuel'")
                elif sel_disp == "AESH Mutualisé":
                    where.append("COALESCE(de.mdph_notif,0)=1 AND COALESCE(de.mdph_type,'')='Mutualisé'")
                elif sel_disp == "PAI Alimentaire":
                    where.append("COALESCE(de.pai_type,'')='Alimentaire'")
                elif sel_disp == "PAI Anxiété scolaire":
                    where.append("COALESCE(de.pai_type,'')='Anxiété scolaire'")
                elif sel_disp == "PAI Asthme":
                    where.append("COALESCE(de.pai_type,'')='Asthme'")
                elif sel_disp == "PAP":
                    where.append("COALESCE(de.pap,0)=1")
                elif sel_disp == "PPRE":
                    where.append("COALESCE(de.ppre,0)=1")

            sql = f"SELECT e.nom, e.prenom, e.classe, e.niveau FROM eleves e {join} WHERE " + " AND ".join(where) + " ORDER BY e.nom, e.prenom"
            rows = self.conn.execute(sql, tuple(params)).fetchall()

            lines = []
            for r in rows:
                nom = self._html_escape(r["nom"] or "")
                prenom = self._html_escape(r["prenom"] or "")
                classe = self._html_escape(r["classe"] or "")
                niveau = self._html_escape(r["niveau"] or "")
                lines.append(f"<tr><td>{nom}</td><td>{prenom}</td><td>{classe}</td><td>{niveau}</td></tr>")

            html = f"""
            <h1>{self._html_escape(title)}</h1>
            <p>Date : {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <table border='1' cellspacing='0' cellpadding='4'>
                <tr><th>Nom</th><th>Prénom</th><th>Classe</th><th>Niveau</th></tr>
                {''.join(lines) if lines else '<tr><td colspan="4">—</td></tr>'}
            </table>
            """

            doc = QTextDocument()
            doc.setHtml(html)

            printer = QPrinter()
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            doc.print_(printer)

            QMessageBox.information(self, "PDF (V10 PRO FIX)", f"Liste exportée ✅\n\nEmplacement :\n{path}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

        except Exception as e:
            QMessageBox.critical(self, "PDF (V10 PRO FIX)", f"Erreur lors de l'export PDF :\n{e}")


    # ----------------- DASHBOARD / STATS -----------------

    def dashboard(self):
        total = self.conn.execute("SELECT COUNT(*) FROM eleves WHERE actif=1").fetchone()[0]
        total_suivis = self.conn.execute("SELECT COUNT(*) FROM suivis").fetchone()[0]
        total_reu = self.conn.execute("SELECT COUNT(*) FROM reunions").fetchone()[0]
        total_disp = self.conn.execute("SELECT COUNT(*) FROM dispositifs_eleve").fetchone()[0]

        # top diagnostics
        top = self.conn.execute("""
            SELECT diag, COUNT(*) c
            FROM eleve_diagnostics
            GROUP BY diag
            ORDER BY c DESC
            LIMIT 10
        """).fetchall()

        txt = f"Tableau de bord\n\n"
        txt += f"Élèves actifs : {total}\n"
        txt += f"Suivis enregistrés : {total_suivis}\n"
        txt += f"Réunions enregistrées : {total_reu}\n"
        txt += f"Dispositifs enregistrés : {total_disp}\n\n"
        txt += "Top diagnostics :\n"
        if top:
            for r in top:
                txt += f"- {r['diag']} : {r['c']}\n"
        else:
            txt += "—\n"

        QMessageBox.information(self, "Tableau de bord", txt)


    def stats_ecole(self):
        # Élèves par classe
        classes = self.conn.execute("""
            SELECT COALESCE(classe,'(sans classe)') classe, COUNT(*) c
            FROM eleves
            WHERE actif=1
            GROUP BY classe
            ORDER BY classe
        """).fetchall()

        # Diagnostics (top)
        diags = self.conn.execute("""
            SELECT diag, COUNT(*) c
            FROM eleve_diagnostics
            GROUP BY diag
            ORDER BY c DESC
        """).fetchall()

        # Dispositifs (dispositifs_eleve)
        disp = self.conn.execute("""
            SELECT
              SUM(COALESCE(mdph_notif,0)) AS mdph,
              SUM(CASE WHEN COALESCE(mdph_type,'')='Individuel' THEN 1 ELSE 0 END) AS aesh_ind,
              SUM(CASE WHEN COALESCE(mdph_type,'')='Mutualisé' THEN 1 ELSE 0 END) AS aesh_mut,
              SUM(CASE WHEN COALESCE(pai_type,'')='Alimentaire' THEN 1 ELSE 0 END) AS pai_alim,
              SUM(CASE WHEN COALESCE(pai_type,'')='Anxiété scolaire' THEN 1 ELSE 0 END) AS pai_anx,
              SUM(CASE WHEN COALESCE(pai_type,'')='Asthme' THEN 1 ELSE 0 END) AS pai_ast,
              SUM(COALESCE(pap,0)) AS pap,
              SUM(COALESCE(ppre,0)) AS ppre
            FROM dispositifs_eleve
        """).fetchone()

        total = self.conn.execute("SELECT COUNT(*) FROM eleves WHERE actif=1").fetchone()[0]

        txt = []
        txt.append("Statistiques école (V10 PRO)\n")
        txt.append(f"Élèves actifs : {total}\n")

        txt.append("Élèves par classe :")
        for r in classes:
            txt.append(f" - {r['classe']} : {r['c']}")
        txt.append("")

        txt.append("Dispositifs :")
        if disp:
            txt.append(f" - MDPH : {disp['mdph'] or 0}")
            txt.append(f"   • AESH individuel : {disp['aesh_ind'] or 0}")
            txt.append(f"   • AESH mutualisé : {disp['aesh_mut'] or 0}")
            txt.append(f" - PAI alimentaire : {disp['pai_alim'] or 0}")
            txt.append(f" - PAI anxiété scolaire : {disp['pai_anx'] or 0}")
            txt.append(f" - PAI asthme : {disp['pai_ast'] or 0}")
            txt.append(f" - PAP : {disp['pap'] or 0}")
            txt.append(f" - PPRE : {disp['ppre'] or 0}")
        else:
            txt.append(" - —")
        txt.append("")

        txt.append("Diagnostics :")
        if diags:
            for r in diags:
                txt.append(f" - {r['diag']} : {r['c']}")
        else:
            txt.append(" - —")

        QMessageBox.information(self, "Statistiques école", "\n".join(txt))

    def stats_classes(self):
        rows = self.conn.execute("""
            SELECT classe, COUNT(*) c
            FROM eleves
            WHERE actif=1
            GROUP BY classe
            ORDER BY classe
        """).fetchall()

        txt = "Statistiques par classe\n\n"
        for r in rows:
            txt += f"{r['classe'] or '(sans classe)'} : {r['c']} élèves\n"
        QMessageBox.information(self, "Classes", txt)

# ------------------------- MAIN -------------------------

def main():
    app = QApplication(sys.argv)
    w = App()
    # Sécurité : mot de passe (direction)
    if not ensure_password_gate(w, w.conn):
        return
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
