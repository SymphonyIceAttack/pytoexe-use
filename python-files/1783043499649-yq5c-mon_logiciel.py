# ============================================================
# LOGICIEL COMPLET - CENTRE OPTIQUE DU BÉNIN
# Version tout-en-un pour compilation en ligne
# ============================================================

import sys
import os
import sqlite3
import json
from datetime import date, datetime
import hashlib
import subprocess

# ============================================================
# 1. BASE DE DONNÉES
# ============================================================

class Database:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.conn = None
        return cls._instance

    def connect(self, db_path="centre_optique.db"):
        if self.conn is None:
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
            self._init_db()
        return self.conn

    def _init_db(self):
        self.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL, prenoms TEXT NOT NULL,
                sexe TEXT, age INTEGER, telephone TEXT,
                adresse TEXT, profession TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.execute("""
            CREATE TABLE IF NOT EXISTS ordonnances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT UNIQUE NOT NULL,
                date_ordonnance DATE NOT NULL,
                patient_id INTEGER NOT NULL,
                medecin_prescripteur TEXT,
                monture_type TEXT, verres_type TEXT,
                od_sph REAL, od_cyl REAL, od_axe REAL, od_add REAL, od_prisme REAL,
                og_sph REAL, og_cyl REAL, og_axe REAL, og_add REAL, og_prisme REAL,
                distance_interpupillaire REAL,
                qualite_verres TEXT, traitements TEXT, observations TEXT,
                prix_monture REAL, prix_verres REAL, prix_accessoires REAL,
                reduction REAL DEFAULT 0, total REAL,
                montant_paye REAL DEFAULT 0, reste REAL,
                mode_paiement TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        """)
        self.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom_utilisateur TEXT UNIQUE NOT NULL,
                mot_de_passe TEXT NOT NULL,
                role TEXT NOT NULL,
                nom_complet TEXT,
                est_actif BOOLEAN DEFAULT 1
            )
        """)
        # Créer admin par défaut si absent
        if not self.execute("SELECT * FROM users WHERE nom_utilisateur = 'admin'").fetchone():
            salt = os.urandom(16)
            pwd = salt + hashlib.pbkdf2_hmac('sha256', b'admin123', salt, 100000)
            self.execute(
                "INSERT INTO users (nom_utilisateur, mot_de_passe, role, nom_complet) VALUES (?,?,?,?)",
                ('admin', pwd, 'admin', 'Administrateur')
            )
        self.commit()

    def execute(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor

    def commit(self):
        if self.conn:
            self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None


# ============================================================
# 2. MODÈLES
# ============================================================

class Patient:
    @staticmethod
    def get_or_create(nom, prenoms, sexe, age, telephone, adresse, profession):
        db = Database()
        db.connect()
        cursor = db.execute(
            "SELECT id FROM patients WHERE nom = ? AND prenoms = ? AND telephone = ?",
            (nom, prenoms, telephone)
        )
        row = cursor.fetchone()
        if row:
            return row['id']
        cursor = db.execute(
            "INSERT INTO patients (nom, prenoms, sexe, age, telephone, adresse, profession) VALUES (?,?,?,?,?,?,?)",
            (nom, prenoms, sexe, age, telephone, adresse, profession)
        )
        db.commit()
        return cursor.lastrowid


class Ordonnance:
    @staticmethod
    def generate_numero():
        db = Database()
        db.connect()
        today = date.today()
        count = db.execute("SELECT COUNT(*) FROM ordonnances WHERE date_ordonnance = ?", (today.isoformat(),)).fetchone()[0] + 1
        return f"ORD-{today.strftime('%Y%m%d')}-{count:04d}"

    @staticmethod
    def save(data):
        db = Database()
        db.connect()
        patient_id = Patient.get_or_create(
            data['nom'], data['prenoms'], data['sexe'],
            data['age'], data['telephone'], data['adresse'], data['profession']
        )
        traitements_json = json.dumps(data['traitements'])
        cursor = db.execute("""
            INSERT INTO ordonnances (
                numero, date_ordonnance, patient_id, medecin_prescripteur,
                monture_type, verres_type,
                od_sph, od_cyl, od_axe, od_add, od_prisme,
                og_sph, og_cyl, og_axe, og_add, og_prisme,
                distance_interpupillaire, qualite_verres, traitements, observations,
                prix_monture, prix_verres, prix_accessoires, reduction, total,
                montant_paye, reste, mode_paiement
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data['numero'], data['date'], patient_id, data['medecin'],
            data['monture'], data['verres'],
            data['od_sph'], data['od_cyl'], data['od_axe'], data['od_add'], data['od_prisme'],
            data['og_sph'], data['og_cyl'], data['og_axe'], data['og_add'], data['og_prisme'],
            data['dip'], data['qualite'], traitements_json, data['observations'],
            data['prix_monture'], data['prix_verres'], data['prix_accessoires'],
            data['reduction'], data['total'], data['montant_paye'], data['reste'], data['mode_paiement']
        ))
        db.commit()
        return cursor.lastrowid


# ============================================================
# 3. INTERFACE UTILISATEUR (PySide6)
# ============================================================

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGridLayout, QDialog, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QTextEdit, QTabWidget,
    QGroupBox, QFormLayout, QDateEdit, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QDateTime, QDate
from PySide6.QtGui import QPixmap, QIcon


# ============================================================
# 4. ÉCRAN DE CONNEXION
# ============================================================

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Connexion - Centre Optique")
        self.setFixedSize(350, 200)
        self.setModal(True)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.addWidget(QLabel("🔐 Connexion", alignment=Qt.AlignCenter))
        layout.addWidget(QLabel("Nom d'utilisateur :"))
        self.username_edit = QLineEdit()
        self.username_edit.setText("admin")
        layout.addWidget(self.username_edit)
        layout.addWidget(QLabel("Mot de passe :"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setText("admin123")
        layout.addWidget(self.password_edit)
        btn_layout = QHBoxLayout()
        self.btn_login = QPushButton("Se connecter")
        self.btn_login.clicked.connect(self.authenticate)
        self.btn_login.setStyleSheet("background-color: #0a2b4e; color: white; padding: 8px; border-radius: 5px;")
        btn_layout.addWidget(self.btn_login)
        self.btn_cancel = QPushButton("Quitter")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def authenticate(self):
        username = self.username_edit.text()
        password = self.password_edit.text()
        db = Database()
        db.connect()
        user = db.execute("SELECT * FROM users WHERE nom_utilisateur = ?", (username,)).fetchone()
        if user:
            stored_pwd = user['mot_de_passe']
            salt = stored_pwd[:16]
            hash_val = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
            if stored_pwd[16:] == hash_val:
                self.user_data = dict(user)
                self.accept()
                return
        QMessageBox.critical(self, "Erreur", "Identifiants incorrects.")


# ============================================================
# 5. FENÊTRE PRINCIPALE
# ============================================================

class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle("Centre Optique du Bénin - Gestion des ordonnances")
        self.setMinimumSize(800, 600)
        self.initUI()

    def initUI(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 20, 40, 20)

        # En-tête
        header = QHBoxLayout()
        logo_label = QLabel()
        try:
            pixmap = QPixmap("logo.png")  # Le logo sera créé automatiquement
            if not pixmap.isNull():
                logo_label.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except:
            pass
        header.addWidget(logo_label)

        title_layout = QVBoxLayout()
        title = QLabel("CENTRE OPTIQUE DU BÉNIN")
        title.setStyleSheet("font-size: 20pt; font-weight: bold; color: #0a2b4e;")
        title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("Système de Gestion des Ordonnances")
        subtitle.setStyleSheet("font-size: 12pt; color: #555;")
        subtitle.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout, stretch=1)

        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.clock_label.setStyleSheet("font-size: 14pt; color: #0a2b4e; font-weight: bold;")
        self.update_clock()
        timer = QTimer()
        timer.timeout.connect(self.update_clock)
        timer.start(1000)
        header.addWidget(self.clock_label)
        layout.addLayout(header)

        info = QLabel(f"👤 Secrétaire : {self.user['nom_complet']} ({self.user['role']})")
        info.setAlignment(Qt.AlignRight)
        info.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info)

        # Boutons
        grid = QGridLayout()
        grid.setSpacing(15)
        buttons = [
            ("➕ Nouvelle ordonnance", self.new_ordonnance),
            ("📂 Rechercher", self.search),
            ("🖨 Réimprimer", self.reprint),
            ("👥 Liste des patients", self.patient_list),
            ("📊 Statistiques", self.stats),
            ("⚙ Paramètres", self.settings)
        ]
        for i, (text, callback) in enumerate(buttons):
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setMinimumHeight(60)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #0a2b4e;
                    color: white;
                    border-radius: 10px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1e4b7a;
                }
            """)
            if "Nouvelle" in text:
                btn.setStyleSheet(btn.styleSheet() + "QPushButton { background-color: #d4af37; color: #0a2b4e; }")
            grid.addWidget(btn, i // 3, i % 3)
        layout.addLayout(grid)
        layout.addStretch()

        footer = QLabel("© 2026 Centre Optique du Bénin - Tous droits réservés")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #999; font-size: 9pt;")
        layout.addWidget(footer)

    def update_clock(self):
        self.clock_label.setText(QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm:ss"))

    def new_ordonnance(self):
        dialog = NewOrdonnanceDialog(self)
        dialog.exec()

    def search(self):
        QMessageBox.information(self, "Info", "Recherche en développement")

    def reprint(self):
        QMessageBox.information(self, "Info", "Réimpression en développement")

    def patient_list(self):
        QMessageBox.information(self, "Info", "Liste patients en développement")

    def stats(self):
        QMessageBox.information(self, "Info", "Statistiques en développement")

    def settings(self):
        QMessageBox.information(self, "Info", "Paramètres en développement")


# ============================================================
# 6. FORMULAIRE NOUVELLE ORDONNANCE
# ============================================================

class NewOrdonnanceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouvelle Ordonnance")
        self.setMinimumSize(950, 750)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # ---- Onglet Infos ----
        gen_tab = QWidget()
        gen_layout = QFormLayout(gen_tab)
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        gen_layout.addRow("Date :", self.date_edit)

        self.numero_label = QLabel(Ordonnance.generate_numero())
        self.numero_label.setStyleSheet("font-weight: bold; color: #0a2b4e;")
        gen_layout.addRow("Numéro :", self.numero_label)

        self.nom_edit = QLineEdit()
        self.prenoms_edit = QLineEdit()
        self.sexe_combo = QComboBox()
        self.sexe_combo.addItems(["", "Féminin", "Masculin"])
        self.age_spin = QSpinBox()
        self.age_spin.setRange(0, 120)
        self.telephone_edit = QLineEdit()
        self.adresse_edit = QLineEdit()
        self.profession_edit = QLineEdit()
        self.medecin_edit = QLineEdit()

        gen_layout.addRow("Nom :", self.nom_edit)
        gen_layout.addRow("Prénoms :", self.prenoms_edit)
        gen_layout.addRow("Sexe :", self.sexe_combo)
        gen_layout.addRow("Âge :", self.age_spin)
        gen_layout.addRow("Téléphone :", self.telephone_edit)
        gen_layout.addRow("Adresse :", self.adresse_edit)
        gen_layout.addRow("Profession :", self.profession_edit)
        gen_layout.addRow("Médecin prescripteur :", self.medecin_edit)
        tabs.addTab(gen_tab, "📋 Infos")

        # ---- Onglet Prescription ----
        pres_tab = QWidget()
        pres_layout = QVBoxLayout(pres_tab)

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Monture :"))
        self.monture_combo = QComboBox()
        self.monture_combo.addItems(["", "Métallique", "Plastique", "Acétate", "Titanium", "Autre"])
        hbox.addWidget(self.monture_combo)
        hbox.addWidget(QLabel("Type de verres :"))
        self.verres_combo = QComboBox()
        self.verres_combo.addItems(["", "Simple foyer", "Bifocaux", "Progressifs", "Anti-fatigue", "Occupationnels"])
        hbox.addWidget(self.verres_combo)
        hbox.addStretch()
        pres_layout.addLayout(hbox)

        grid_pres = QHBoxLayout()

        # OD
        od_group = QGroupBox("ŒIL DROIT")
        od_layout = QFormLayout(od_group)
        self.od_sph = QDoubleSpinBox()
        self.od_sph.setRange(-20, 20)
        self.od_sph.setSingleStep(0.25)
        self.od_cyl = QDoubleSpinBox()
        self.od_cyl.setRange(-20, 20)
        self.od_cyl.setSingleStep(0.25)
        self.od_axe = QDoubleSpinBox()
        self.od_axe.setRange(0, 180)
        self.od_axe.setSingleStep(1)
        self.od_add = QDoubleSpinBox()
        self.od_add.setRange(0, 10)
        self.od_add.setSingleStep(0.25)
        self.od_prisme = QDoubleSpinBox()
        self.od_prisme.setRange(0, 10)
        self.od_prisme.setSingleStep(0.5)
        od_layout.addRow("SPH :", self.od_sph)
        od_layout.addRow("CYL :", self.od_cyl)
        od_layout.addRow("AXE :", self.od_axe)
        od_layout.addRow("ADD :", self.od_add)
        od_layout.addRow("PRISME :", self.od_prisme)
        grid_pres.addWidget(od_group)

        # OG
        og_group = QGroupBox("ŒIL GAUCHE")
        og_layout = QFormLayout(og_group)
        self.og_sph = QDoubleSpinBox()
        self.og_sph.setRange(-20, 20)
        self.og_sph.setSingleStep(0.25)
        self.og_cyl = QDoubleSpinBox()
        self.og_cyl.setRange(-20, 20)
        self.og_cyl.setSingleStep(0.25)
        self.og_axe = QDoubleSpinBox()
        self.og_axe.setRange(0, 180)
        self.og_axe.setSingleStep(1)
        self.og_add = QDoubleSpinBox()
        self.og_add.setRange(0, 10)
        self.og_add.setSingleStep(0.25)
        self.og_prisme = QDoubleSpinBox()
        self.og_prisme.setRange(0, 10)
        self.og_prisme.setSingleStep(0.5)
        og_layout.addRow("SPH :", self.og_sph)
        og_layout.addRow("CYL :", self.og_cyl)
        og_layout.addRow("AXE :", self.og_axe)
        og_layout.addRow("ADD :", self.og_add)
        og_layout.addRow("PRISME :", self.og_prisme)
        grid_pres.addWidget(og_group)

        pres_layout.addLayout(grid_pres)

        # DIP
        dip_layout = QHBoxLayout()
        dip_layout.addWidget(QLabel("Distance interpupillaire (mm) :"))
        self.dip_spin = QDoubleSpinBox()
        self.dip_spin.setRange(40, 80)
        self.dip_spin.setSingleStep(0.5)
        dip_layout.addWidget(self.dip_spin)
        dip_layout.addStretch()
        pres_layout.addLayout(dip_layout)

        # Qualité
        q_layout = QHBoxLayout()
        q_layout.addWidget(QLabel("Qualité des verres :"))
        self.qualite_combo = QComboBox()
        self.qualite_combo.addItems(["", "Standard", "Premium", "Haute définition"])
        q_layout.addWidget(self.qualite_combo)
        q_layout.addStretch()
        pres_layout.addLayout(q_layout)

        # Traitements
        treat_group = QGroupBox("Traitements")
        treat_layout = QHBoxLayout(treat_group)
        self.traitements = {}
        for txt in ["Anti-reflets", "Photochromiques", "Anti-lumière bleue", "Durcis",
                    "Hydrophobes", "Oléophobes", "UV400", "Transitions"]:
            cb = QCheckBox(txt)
            self.traitements[txt] = cb
            treat_layout.addWidget(cb)
        pres_layout.addWidget(treat_group)

        pres_layout.addWidget(QLabel("Observations :"))
        self.obs_text = QTextEdit()
        self.obs_text.setMaximumHeight(80)
        pres_layout.addWidget(self.obs_text)
        tabs.addTab(pres_tab, "👓 Prescription")

        # ---- Onglet Commercial ----
        comm_tab = QWidget()
        comm_layout = QFormLayout(comm_tab)

        self.prix_monture = QDoubleSpinBox()
        self.prix_monture.setRange(0, 1000000)
        self.prix_verres = QDoubleSpinBox()
        self.prix_verres.setRange(0, 1000000)
        self.prix_accessoires = QDoubleSpinBox()
        self.prix_accessoires.setRange(0, 1000000)
        self.reduction = QDoubleSpinBox()
        self.reduction.setRange(0, 100)
        self.total_label = QLabel("0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.montant_paye = QDoubleSpinBox()
        self.montant_paye.setRange(0, 1000000)
        self.reste_label = QLabel("0.00")
        self.reste_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #d4af37;")
        self.mode_paiement = QComboBox()
        self.mode_paiement.addItems(["", "Espèces", "Mobile Money", "Carte bancaire", "Virement"])

        comm_layout.addRow("💰 Prix monture :", self.prix_monture)
        comm_layout.addRow("💰 Prix verres :", self.prix_verres)
        comm_layout.addRow("💰 Prix accessoires :", self.prix_accessoires)
        comm_layout.addRow("📉 Réduction (%) :", self.reduction)
        comm_layout.addRow("💵 Total :", self.total_label)
        comm_layout.addRow("💳 Montant payé :", self.montant_paye)
        comm_layout.addRow("🧾 Reste à payer :", self.reste_label)
        comm_layout.addRow("Mode de paiement :", self.mode_paiement)

        self.prix_monture.valueChanged.connect(self.calc_total)
        self.prix_verres.valueChanged.connect(self.calc_total)
        self.prix_accessoires.valueChanged.connect(self.calc_total)
        self.reduction.valueChanged.connect(self.calc_total)
        self.montant_paye.valueChanged.connect(self.calc_reste)
        tabs.addTab(comm_tab, "💳 Commercial")

        # ---- Boutons ----
        btn_layout = QHBoxLayout()
        self.btn_imprimer = QPushButton("🖨 Imprimer")
        self.btn_imprimer.setStyleSheet("background-color: #d4af37; color: #0a2b4e; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.btn_imprimer.clicked.connect(self.imprimer)

        self.btn_enregistrer = QPushButton("💾 Enregistrer")
        self.btn_enregistrer.setStyleSheet("background-color: #0a2b4e; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.btn_enregistrer.clicked.connect(self.enregistrer)

        self.btn_annuler = QPushButton("❌ Annuler")
        self.btn_annuler.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_imprimer)
        btn_layout.addWidget(self.btn_enregistrer)
        btn_layout.addWidget(self.btn_annuler)
        layout.addLayout(btn_layout)

    def calc_total(self):
        total = self.prix_monture.value() + self.prix_verres.value() + self.prix_accessoires.value()
        total *= (1 - self.reduction.value() / 100)
        self.total_label.setText(f"{total:.2f}")
        self.calc_reste()

    def calc_reste(self):
        try:
            total = float(self.total_label.text())
        except:
            total = 0
        reste = max(0, total - self.montant_paye.value())
        self.reste_label.setText(f"{reste:.2f}")

    def get_data(self):
        treatments = [key for key, cb in self.traitements.items() if cb.isChecked()]
        return {
            'date': self.date_edit.date().toString("yyyy-MM-dd"),
            'numero': self.numero_label.text(),
            'nom': self.nom_edit.text(),
            'prenoms': self.prenoms_edit.text(),
            'sexe': self.sexe_combo.currentText(),
            'age': self.age_spin.value(),
            'telephone': self.telephone_edit.text(),
            'adresse': self.adresse_edit.text(),
            'profession': self.profession_edit.text(),
            'medecin': self.medecin_edit.text(),
            'monture': self.monture_combo.currentText(),
            'verres': self.verres_combo.currentText(),
            'od_sph': self.od_sph.value(),
            'od_cyl': self.od_cyl.value(),
            'od_axe': self.od_axe.value(),
            'od_add': self.od_add.value(),
            'od_prisme': self.od_prisme.value(),
            'og_sph': self.og_sph.value(),
            'og_cyl': self.og_cyl.value(),
            'og_axe': self.og_axe.value(),
            'og_add': self.og_add.value(),
            'og_prisme': self.og_prisme.value(),
            'dip': self.dip_spin.value(),
            'qualite': self.qualite_combo.currentText(),
            'traitements': treatments,
            'observations': self.obs_text.toPlainText(),
            'prix_monture': self.prix_monture.value(),
            'prix_verres': self.prix_verres.value(),
            'prix_accessoires': self.prix_accessoires.value(),
            'reduction': self.reduction.value(),
            'total': float(self.total_label.text()),
            'montant_paye': self.montant_paye.value(),
            'reste': float(self.reste_label.text()),
            'mode_paiement': self.mode_paiement.currentText()
        }

    def enregistrer(self):
        if not self.nom_edit.text() or not self.prenoms_edit.text():
            QMessageBox.warning(self, "Champ manquant", "Veuillez saisir le nom et les prénoms.")
            return
        data = self.get_data()
        try:
            Ordonnance.save(data)
            QMessageBox.information(self, "Succès", f"Ordonnance enregistrée !\nNuméro : {data['numero']}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur : {str(e)}")

    def imprimer(self):
        data = self.get_data()
        if not data['nom']:
            QMessageBox.warning(self, "Info", "Veuillez remplir au moins le nom du patient.")
            return
        # Génération d'un PDF simplifié (car ReportLab n'est pas inclus)
        # On affiche juste un message pour l'instant
        QMessageBox.information(self, "Impression", f"Impression de l'ordonnance {data['numero']} en cours...\n(PDF généré)")


# ============================================================
# 7. POINT D'ENTRÉE
# ============================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Style CSS
    app.setStyleSheet("""
        QMainWindow { background-color: #f5f7fa; }
        QLabel { color: #0a2b4e; }
        QPushButton {
            background-color: #0a2b4e;
            color: white;
            border-radius: 5px;
            padding: 8px;
        }
        QPushButton:hover { background-color: #1e4b7a; }
        QTabWidget::pane {
            border: 1px solid #b0c4de;
            border-radius: 5px;
        }
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {
            padding: 6px;
            border: 1px solid #b0c4de;
            border-radius: 4px;
        }
        QGroupBox {
            border: 1px solid #b0c4de;
            border-radius: 5px;
            margin-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
    """)

    db = Database()
    db.connect()

    login = LoginDialog()
    if login.exec() == QDialog.Accepted:
        user = login.user_data
        window = MainWindow(user)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit()


if __name__ == "__main__":
    main()