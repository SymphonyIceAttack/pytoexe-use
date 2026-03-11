#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
SNEP CRM PROFESSIONNEL - Édition PyQt5
Société Nationale d'Électrolyse et de Pétrochimie
Version 9.0 - Design moderne
===============================================================================
"""

import sys
import sqlite3
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
DB_NAME = "snep_crm_pro.db"

# Couleurs SNEP
COLOR_PRIMARY = "#5B2C83"      # Violet SNEP
COLOR_SECONDARY = "#F4F6FA"     # Gris clair
COLOR_SUCCESS = "#18B663"       # Vert
COLOR_WARNING = "#FF8A00"       # Orange
COLOR_DANGER = "#E53E3E"        # Rouge
COLOR_INFO = "#2F6FED"          # Bleu

# -----------------------------------------------------------------------------
# LISTES DE CHOIX (identiques à la version Tkinter)
# -----------------------------------------------------------------------------
LISTE_CLIENTS = [
    "ONEE", "LYDEC", "AMENDIS", "REDAL", "RADEEMA", "RADEEF", "RAK", "RADEEC",
    "OCP GROUP", "COSUMAR", "LESIEUR CRISTAL", "MAGHREB STEEL", "DIMATIT", "AQUAPLAST",
    "PLASTUMAR", "MAROC PVC", "BATIGLOB", "NEXANS MAROC", "TGCC", "JET CONTRACTORS",
    "SGTM", "SONASID", "MANAGEM", "SNEP", "SNRT", "ONCF", "BMCE", "BANQUE POPULAIRE",
    "ATTIJARIWAFA BANK", "CIH", "CDG", "MUTUELLE", "CNSS", "TOTAL MAROC", "SHELL MAROC",
    "AFRIQUIA", "ALUMINIUM DU MAROC", "BRASSERIES DU MAROC", "CIMENTS DU MAROC",
    "HOLCIM", "LAFARGE", "LYONNAISE", "PLASTIFER", "SEAF", "SNTL", "SOMACA", "YAZAKI"
]

LISTE_COMMERCIAUX = [
    "OUSSAMA RAMZI",
    "COMMERCIAL",
    "RESPONSABLE COMMERCIAL",
    "DIRECTEUR COMMERCIAL",
    "ATTACHE COMMERCIAL",
    "TECHNICO-COMMERCIAL",
    "INGENIEUR COMMERCIAL"
]

LISTE_CIVILITES = ["Mr", "Mme", "Mle", "Societe", "Dr", "Pr", "Ing", "Master"]

LISTE_FONCTIONS = [
    "Directeur Achat", "Chef Service Achat", "Responsable Achat", "Acheteur Senior",
    "Acheteur Junior", "Directeur Logistique", "Responsable Logistique", "Directeur d'Usine",
    "Chef Production", "Chef d'Atelier", "Chef Magasin", "Magasinier", "Gestionnaire Stock",
    "Responsable Qualite", "Responsable Maintenance"
]

LISTE_PRODUITS = [
    "CHLORE GAZEUX 99.5%", "CHLORE LIQUIDE 99.8%", "CHLORE LIQUIDE 99.9%",
    "SOUDE CAUSTIQUE LIQ 30%", "SOUDE CAUSTIQUE LIQ 33%", "SOUDE CAUSTIQUE LIQ 48%",
    "SOUDE CAUSTIQUE LIQ 50%", "SOUDE CAUSTIQUE ECAILLES 98%", "SOUDE CAUSTIQUE ECAILLES 99%",
    "ACIDE CHLORHYDRIQUE 31%", "ACIDE CHLORHYDRIQUE 32%", "ACIDE CHLORHYDRIQUE 33%",
    "ACIDE CHLORHYDRIQUE 35%", "ACIDE SULFURIQUE 96%", "ACIDE SULFURIQUE 98%",
    "ACIDE NITRIQUE 53%", "ACIDE NITRIQUE 56%",
    "EAU DE JAVEL 12°", "EAU DE JAVEL 15°", "EAU DE JAVEL 24°", "EAU DE JAVEL 36°", "EAU DE JAVEL 48°",
    "PVC SUSPENSION S60", "PVC SUSPENSION S65", "PVC SUSPENSION S67", "PVC EMULSION", "PVC COMPOUND"
]

LISTE_UNITES = ["TONNES", "KG", "M3", "LITRES", "PALETTES", "BARILS", "FUTS", "CONTENEURS", "CITERNES"]

LISTE_PAIEMENTS = [
    "Especes", "Cheque", "Cheque certifie", "Virement bancaire", "Virement international",
    "Effet de commerce", "Lettre de change", "LCR", "Billet à ordre", "Traite",
    "Prelevement", "Carte bancaire", "PayPal", "Western Union", "Mandat"
]

LISTE_ECHEANCES = [
    "Comptant", "15 jours", "30 jours", "45 jours", "60 jours", "90 jours",
    "120 jours", "180 jours", "A reception", "Fin de mois"
]

LISTE_TYPES_TEL = [
    "Mobile Pro", "Mobile Perso", "Fixe Pro", "Fixe Perso",
    "WhatsApp", "Telegram", "Teams", "Zoom", "Standard"
]

LISTE_FLUX = [
    "Appel entrant", "Appel sortant", "Visite terrain", "RDV client", "RDV fournisseur",
    "Email", "Devis envoye", "Commande recue", "Facture envoyee", "Relance",
    "Reclamation", "Prospection", "Signature contrat"
]

LISTE_STATUTS = [
    "En cours", "Valide", "Annule", "Reporte", "En attente", "Termine", "Livre",
    "Facture", "Paye", "Impaye", "En litige", "Prospect", "Client actif",
    "Client inactif", "Client perdu", "Cheque envoye", "Cheque en cours",
    "Cheque encaisse", "Cheque refuse"
]

LISTE_REMARQUES = [
    "Client interesse", "Client tres interesse", "Client en reflexion",
    "Client compare les prix", "Client fidele", "Nouveau prospect",
    "Prospect qualifie", "Client potentiel", "Client inactif",
    "Client perdu", "Client strategique", "Client VIP",
    "Projet en cours", "Nouveau projet", "Projet prevu",
    "Projet reporte", "Projet annule", "Opportunite importante",
    "Demande de devis", "Offre envoyee", "Offre acceptee",
    "Offre refusee", "Negociation en cours", "Appel d'offres",
    "Relance prevue", "Relance effectuee", "Visite programmee",
    "Visite effectuee", "RDV confirme", "RDV reporte",
    "RDV annule", "Attente reponse", "Attente decision",
    "Demande de remise", "Negociation prix", "Accord en cours",
    "Accord confirme", "Accord de principe", "Remise accordee",
    "Prix bloque", "Verifier disponibilite", "Rupture stock",
    "Livraison urgente", "Livraison programmee", "Livraison en attente",
    "Probleme livraison", "Retard livraison", "Paiement en attente",
    "Paiement confirme", "Paiement recu", "Paiement partiel",
    "Paiement en retard", "Client solvable", "Verifier situation",
    "Bonne relation", "Client satisfait", "Client insatisfait",
    "Reclamation client", "Reclamation resolue", "Forte concurrence",
    "Prix concurrent inferieur", "Opportunite de recuperation",
    "Envoyer devis", "Envoyer catalogue", "Preparer offre",
    "Programmer visite", "Contacter decideur", "Suivre projet",
    "Rappeler client", "Relancer urgemment"
]

LISTE_ETAPES_PIPELINE = [
    "1. PROSPECTION", "2. CONTACT INITIAL", "3. RDV DECOUVERTE",
    "4. ENVOI DEVIS", "5. NEGOCIATION", "6. ACCORD PRINCIPE",
    "7. CONTRAT", "8. COMMANDE", "9. FACTURATION",
    "10. PAIEMENT", "11. CLIENT ACTIF", "12. PERDU"
]

# -----------------------------------------------------------------------------
# BASE DE DONNÉES (identique à la version Tkinter)
# -----------------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        secteur TEXT,
        email TEXT,
        telephone TEXT,
        ville TEXT,
        date_creation TEXT,
        est_prospect INTEGER DEFAULT 1
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        categorie TEXT,
        unite TEXT,
        prix REAL
    )''')
    c.execute("SELECT COUNT(*) FROM produits")
    if c.fetchone()[0] == 0:
        for prod in LISTE_PRODUITS:
            c.execute("INSERT INTO produits (nom, categorie, unite, prix) VALUES (?, ?, ?, ?)",
                      (prod, "Divers", "TONNES", 0.0))
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        client_id INTEGER,
        produit_id INTEGER,
        quantite REAL,
        prix_unitaire REAL,
        total REAL,
        paiement TEXT,
        echeance TEXT,
        commercial TEXT,
        type_tel TEXT,
        telephone TEXT,
        flux TEXT,
        statut TEXT,
        remarque TEXT,
        alerte TEXT,
        date_relance TEXT,
        etape_pipeline TEXT,
        FOREIGN KEY(client_id) REFERENCES clients(id),
        FOREIGN KEY(produit_id) REFERENCES produits(id)
    )''')
    conn.commit()
    conn.close()

# -----------------------------------------------------------------------------
# MODÈLES (identiques)
# -----------------------------------------------------------------------------
class Client:
    def __init__(self, id=None, nom="", secteur="", email="", telephone="", ville="", date_creation=None, est_prospect=1):
        self.id = id
        self.nom = nom
        self.secteur = secteur
        self.email = email
        self.telephone = telephone
        self.ville = ville
        self.date_creation = date_creation or datetime.now().strftime("%Y-%m-%d")
        self.est_prospect = est_prospect

    def save(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        if self.id is None:
            c.execute('''INSERT INTO clients (nom, secteur, email, telephone, ville, date_creation, est_prospect)
                         VALUES (?,?,?,?,?,?,?)''',
                      (self.nom, self.secteur, self.email, self.telephone, self.ville, self.date_creation, self.est_prospect))
            self.id = c.lastrowid
        else:
            c.execute('''UPDATE clients SET nom=?, secteur=?, email=?, telephone=?, ville=?, est_prospect=?
                         WHERE id=?''',
                      (self.nom, self.secteur, self.email, self.telephone, self.ville, self.est_prospect, self.id))
        conn.commit()
        conn.close()

    def delete(self):
        if self.id:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DELETE FROM clients WHERE id=?", (self.id,))
            conn.commit()
            conn.close()

    @staticmethod
    def get_all():
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, nom, secteur, email, telephone, ville, date_creation, est_prospect FROM clients ORDER BY nom")
        rows = c.fetchall()
        conn.close()
        return [Client(*row) for row in rows]

    @staticmethod
    def get_by_id(id):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, nom, secteur, email, telephone, ville, date_creation, est_prospect FROM clients WHERE id=?", (id,))
        row = c.fetchone()
        conn.close()
        return Client(*row) if row else None

class Produit:
    def __init__(self, id=None, nom="", categorie="", unite="", prix=0.0):
        self.id = id
        self.nom = nom
        self.categorie = categorie
        self.unite = unite
        self.prix = prix

    def save(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        if self.id is None:
            c.execute('''INSERT INTO produits (nom, categorie, unite, prix)
                         VALUES (?,?,?,?)''',
                      (self.nom, self.categorie, self.unite, self.prix))
            self.id = c.lastrowid
        else:
            c.execute('''UPDATE produits SET nom=?, categorie=?, unite=?, prix=?
                         WHERE id=?''',
                      (self.nom, self.categorie, self.unite, self.prix, self.id))
        conn.commit()
        conn.close()

    @staticmethod
    def get_all():
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, nom, categorie, unite, prix FROM produits ORDER BY nom")
        rows = c.fetchall()
        conn.close()
        return [Produit(*row) for row in rows]

    @staticmethod
    def get_by_id(id):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, nom, categorie, unite, prix FROM produits WHERE id=?", (id,))
        row = c.fetchone()
        conn.close()
        return Produit(*row) if row else None

class Transaction:
    def __init__(self, id=None, date=None, client_id=None, produit_id=None, quantite=0.0,
                 prix_unitaire=0.0, total=0.0, paiement="", echeance="", commercial="",
                 type_tel="", telephone="", flux="", statut="", remarque="",
                 alerte="", date_relance="", etape_pipeline=""):
        self.id = id
        self.date = date or datetime.now().strftime("%Y-%m-%d")
        self.client_id = client_id
        self.produit_id = produit_id
        self.quantite = quantite
        self.prix_unitaire = prix_unitaire
        self.total = total
        self.paiement = paiement
        self.echeance = echeance
        self.commercial = commercial
        self.type_tel = type_tel
        self.telephone = telephone
        self.flux = flux
        self.statut = statut
        self.remarque = remarque
        self.alerte = alerte
        self.date_relance = date_relance
        self.etape_pipeline = etape_pipeline

    def save(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        if self.id is None:
            c.execute('''INSERT INTO transactions
                         (date, client_id, produit_id, quantite, prix_unitaire, total,
                          paiement, echeance, commercial, type_tel, telephone, flux,
                          statut, remarque, alerte, date_relance, etape_pipeline)
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                      (self.date, self.client_id, self.produit_id, self.quantite, self.prix_unitaire,
                       self.total, self.paiement, self.echeance, self.commercial,
                       self.type_tel, self.telephone, self.flux, self.statut,
                       self.remarque, self.alerte, self.date_relance, self.etape_pipeline))
            self.id = c.lastrowid
        else:
            c.execute('''UPDATE transactions SET
                         date=?, client_id=?, produit_id=?, quantite=?, prix_unitaire=?, total=?,
                         paiement=?, echeance=?, commercial=?, type_tel=?, telephone=?, flux=?,
                         statut=?, remarque=?, alerte=?, date_relance=?, etape_pipeline=?
                         WHERE id=?''',
                      (self.date, self.client_id, self.produit_id, self.quantite, self.prix_unitaire,
                       self.total, self.paiement, self.echeance, self.commercial,
                       self.type_tel, self.telephone, self.flux, self.statut,
                       self.remarque, self.alerte, self.date_relance, self.etape_pipeline, self.id))
        conn.commit()
        conn.close()

    @staticmethod
    def get_all():
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''SELECT t.id, t.date, c.nom, p.nom, t.quantite, t.prix_unitaire, t.total,
                            t.paiement, t.echeance, t.commercial, t.type_tel, t.telephone,
                            t.flux, t.statut, t.remarque, t.alerte, t.date_relance, t.etape_pipeline
                     FROM transactions t
                     LEFT JOIN clients c ON t.client_id = c.id
                     LEFT JOIN produits p ON t.produit_id = p.id
                     ORDER BY t.date DESC''')
        rows = c.fetchall()
        conn.close()
        return rows

# -----------------------------------------------------------------------------
# CARTE STATISTIQUE (comme dans le design)
# -----------------------------------------------------------------------------
class StatCard(QFrame):
    def __init__(self, title, value, color):
        super().__init__()
        self.setStyleSheet(f"""
            background-color: {color};
            color: white;
            border-radius: 8px;
            padding: 10px;
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: normal;")
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet("font-size: 26px; font-weight: bold;")
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        self.setLayout(layout)

# -----------------------------------------------------------------------------
# FENÊTRE PRINCIPALE
# -----------------------------------------------------------------------------
class CRM_MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SNEP CRM Professionnel")
        self.setGeometry(100, 100, 1400, 800)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal horizontal
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # ----- MENU LATÉRAL GAUCHE (violet) -----
        self.menu_widget = QWidget()
        self.menu_widget.setStyleSheet("""
            background-color: #5B2C83;
            color: white;
        """)
        self.menu_widget.setFixedWidth(250)
        menu_layout = QVBoxLayout()
        self.menu_widget.setLayout(menu_layout)

        # Titre CRM
        title = QLabel("SNEP CRM")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("padding: 15px; color: white;")
        menu_layout.addWidget(title)

        # Boutons de navigation
        self.nav_buttons = []
        nav_items = [
            ("🏠 Tableau de bord", self.show_dashboard),
            ("👥 Clients", self.show_clients),
            ("📦 Produits", self.show_produits),
            ("💰 Transactions", self.show_transactions),
            ("📈 Pipeline", self.show_pipeline),
            ("⚠️ Alertes", self.show_alertes),
            ("📋 Rapports", self.show_rapports),
        ]
        for text, callback in nav_items:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #5B2C83;
                    color: white;
                    border: none;
                    text-align: left;
                    padding: 12px 15px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #6F3CA5;
                }
            """)
            btn.clicked.connect(callback)
            menu_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        menu_layout.addStretch()

        # ----- ZONE PRINCIPALE DROITE -----
        self.right_widget = QWidget()
        self.right_widget.setStyleSheet("background-color: #F4F6FA;")
        right_layout = QVBoxLayout()
        self.right_widget.setLayout(right_layout)

        # En-tête avec nom SNEP à droite
        header = QWidget()
        header_layout = QHBoxLayout()
        header.setLayout(header_layout)

        # Titre de la page (sera mis à jour)
        self.page_title = QLabel("Tableau de bord")
        self.page_title.setFont(QFont("Arial", 20, QFont.Bold))
        header_layout.addWidget(self.page_title)

        header_layout.addStretch()

        # Nom de la société à droite
        company = QLabel("SOCIÉTÉ NATIONALE D'ÉLECTROLYSE ET DE PÉTROCHIMIE")
        company.setFont(QFont("Arial", 10))
        company.setStyleSheet("color: #5B2C83; font-weight: bold;")
        header_layout.addWidget(company)

        right_layout.addWidget(header)

        # Zone de contenu avec QStackedWidget pour changer de page
        self.stacked_widget = QStackedWidget()
        right_layout.addWidget(self.stacked_widget)

        # Création des pages
        self.dashboard_page = self.create_dashboard_page()
        self.clients_page = self.create_clients_page()
        self.produits_page = self.create_produits_page()
        self.transactions_page = self.create_transactions_page()
        self.pipeline_page = self.create_pipeline_page()
        self.alertes_page = self.create_alertes_page()
        self.rapports_page = self.create_rapports_page()

        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.addWidget(self.clients_page)
        self.stacked_widget.addWidget(self.produits_page)
        self.stacked_widget.addWidget(self.transactions_page)
        self.stacked_widget.addWidget(self.pipeline_page)
        self.stacked_widget.addWidget(self.alertes_page)
        self.stacked_widget.addWidget(self.rapports_page)

        # Ajout des widgets au layout principal
        main_layout.addWidget(self.menu_widget)
        main_layout.addWidget(self.right_widget, 1)

        # Chargement initial des données
        self.refresh_dashboard()
        self.refresh_clients_table()
        self.refresh_produits_table()
        self.refresh_transactions_table()
        self.refresh_pipeline()
        self.refresh_alertes()

    # -------------------------------------------------------------------------
    # CRÉATION DES PAGES
    # -------------------------------------------------------------------------
    def create_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)

        # Cartes de statistiques
        cards_layout = QHBoxLayout()
        self.kpi_ca = StatCard("CA Total", "0 DHS", COLOR_INFO)
        self.kpi_trans = StatCard("Transactions", "0", COLOR_INFO)
        self.kpi_clients = StatCard("Clients", "0", COLOR_WARNING)
        self.kpi_alertes = StatCard("Alertes", "0", COLOR_DANGER)

        cards_layout.addWidget(self.kpi_ca)
        cards_layout.addWidget(self.kpi_trans)
        cards_layout.addWidget(self.kpi_clients)
        cards_layout.addWidget(self.kpi_alertes)
        layout.addLayout(cards_layout)

        # Tableau des dernières transactions
        layout.addWidget(QLabel("Dernières transactions"))
        self.dashboard_table = QTableWidget()
        self.dashboard_table.setColumnCount(4)
        self.dashboard_table.setHorizontalHeaderLabels(["Date", "Client", "Montant", "Alerte"])
        self.dashboard_table.horizontalHeader().setStretchLastSection(True)
        self.dashboard_table.setAlternatingRowColors(True)
        layout.addWidget(self.dashboard_table)

        return page

    def create_clients_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)

        # Boutons
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Nouveau client")
        btn_add.clicked.connect(self.ajouter_client)
        btn_modify = QPushButton("✏️ Modifier")
        btn_modify.clicked.connect(self.modifier_client)
        btn_delete = QPushButton("🗑️ Supprimer")
        btn_delete.clicked.connect(self.supprimer_client)
        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.clicked.connect(self.refresh_clients_table)

        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_modify)
        btn_layout.addWidget(btn_delete)
        btn_layout.addWidget(btn_refresh)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Tableau des clients
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(8)
        self.clients_table.setHorizontalHeaderLabels(["ID", "Société", "Secteur", "Email", "Téléphone", "Ville", "Création", "Prospect"])
        self.clients_table.horizontalHeader().setStretchLastSection(True)
        self.clients_table.setAlternatingRowColors(True)
        self.clients_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.clients_table)

        return page

    def create_produits_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)

        # Boutons
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Nouveau produit")
        btn_add.clicked.connect(self.ajouter_produit)
        btn_modify = QPushButton("✏️ Modifier")
        btn_modify.clicked.connect(self.modifier_produit)
        btn_delete = QPushButton("🗑️ Supprimer")
        btn_delete.clicked.connect(self.supprimer_produit)
        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.clicked.connect(self.refresh_produits_table)

        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_modify)
        btn_layout.addWidget(btn_delete)
        btn_layout.addWidget(btn_refresh)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Tableau des produits
        self.produits_table = QTableWidget()
        self.produits_table.setColumnCount(5)
        self.produits_table.setHorizontalHeaderLabels(["ID", "Nom", "Catégorie", "Unité", "Prix (DHS)"])
        self.produits_table.horizontalHeader().setStretchLastSection(True)
        self.produits_table.setAlternatingRowColors(True)
        self.produits_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.produits_table)

        return page

    def create_transactions_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)

        # Formulaire de transaction (simplifié, on pourrait faire un onglet à part)
        form_group = QGroupBox("Nouvelle transaction")
        form_layout = QGridLayout()
        form_group.setLayout(form_layout)

        # Champs
        row = 0
        form_layout.addWidget(QLabel("Client:"), row, 0)
        self.trans_client = QComboBox()
        self.trans_client.addItems(LISTE_CLIENTS)
        self.trans_client.setEditable(True)
        form_layout.addWidget(self.trans_client, row, 1)

        form_layout.addWidget(QLabel("Commercial:"), row, 2)
        self.trans_commercial = QComboBox()
        self.trans_commercial.addItems(LISTE_COMMERCIAUX)
        self.trans_commercial.setEditable(True)
        self.trans_commercial.setCurrentText("OUSSAMA RAMZI")
        form_layout.addWidget(self.trans_commercial, row, 3)

        row += 1
        form_layout.addWidget(QLabel("Produit:"), row, 0)
        self.trans_produit = QComboBox()
        self.trans_produit.addItems(LISTE_PRODUITS)
        self.trans_produit.setEditable(True)
        form_layout.addWidget(self.trans_produit, row, 1)

        form_layout.addWidget(QLabel("Quantité:"), row, 2)
        self.trans_quantite = QLineEdit("1")
        form_layout.addWidget(self.trans_quantite, row, 3)

        row += 1
        form_layout.addWidget(QLabel("Unité:"), row, 0)
        self.trans_unite = QComboBox()
        self.trans_unite.addItems(LISTE_UNITES)
        self.trans_unite.setCurrentText("TONNES")
        form_layout.addWidget(self.trans_unite, row, 1)

        form_layout.addWidget(QLabel("Prix unitaire:"), row, 2)
        self.trans_prix = QLineEdit("0")
        form_layout.addWidget(self.trans_prix, row, 3)

        row += 1
        form_layout.addWidget(QLabel("Paiement:"), row, 0)
        self.trans_paiement = QComboBox()
        self.trans_paiement.addItems(LISTE_PAIEMENTS)
        form_layout.addWidget(self.trans_paiement, row, 1)

        form_layout.addWidget(QLabel("Échéance:"), row, 2)
        self.trans_echeance = QComboBox()
        self.trans_echeance.addItems(LISTE_ECHEANCES)
        form_layout.addWidget(self.trans_echeance, row, 3)

        row += 1
        form_layout.addWidget(QLabel("Type téléphone:"), row, 0)
        self.trans_type_tel = QComboBox()
        self.trans_type_tel.addItems(LISTE_TYPES_TEL)
        form_layout.addWidget(self.trans_type_tel, row, 1)

        form_layout.addWidget(QLabel("Numéro:"), row, 2)
        self.trans_telephone = QLineEdit("06 00 00 00 00")
        form_layout.addWidget(self.trans_telephone, row, 3)

        row += 1
        form_layout.addWidget(QLabel("Flux:"), row, 0)
        self.trans_flux = QComboBox()
        self.trans_flux.addItems(LISTE_FLUX)
        form_layout.addWidget(self.trans_flux, row, 1)

        form_layout.addWidget(QLabel("Statut:"), row, 2)
        self.trans_statut = QComboBox()
        self.trans_statut.addItems(LISTE_STATUTS)
        form_layout.addWidget(self.trans_statut, row, 3)

        row += 1
        form_layout.addWidget(QLabel("Remarque:"), row, 0)
        self.trans_remarque = QComboBox()
        self.trans_remarque.addItems(LISTE_REMARQUES)
        self.trans_remarque.setEditable(True)
        form_layout.addWidget(self.trans_remarque, row, 1, 1, 3)

        row += 1
        form_layout.addWidget(QLabel("Étape pipeline:"), row, 0)
        self.trans_etape = QComboBox()
        self.trans_etape.addItems(LISTE_ETAPES_PIPELINE)
        form_layout.addWidget(self.trans_etape, row, 1, 1, 3)

        row += 1
        btn_save = QPushButton("📥 Enregistrer transaction")
        btn_save.clicked.connect(self.ajouter_transaction)
        btn_save.setStyleSheet(f"background-color: {COLOR_SUCCESS}; color: white; padding: 8px;")
        form_layout.addWidget(btn_save, row, 0, 1, 4)

        layout.addWidget(form_group)

        # Tableau des transactions
        layout.addWidget(QLabel("Historique des transactions"))
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(8)
        self.transactions_table.setHorizontalHeaderLabels(["Date", "Client", "Produit", "Qté", "Total", "Paiement", "Statut", "Alerte"])
        self.transactions_table.horizontalHeader().setStretchLastSection(True)
        self.transactions_table.setAlternatingRowColors(True)
        layout.addWidget(self.transactions_table)

        return page

    def create_pipeline_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)

        # Titre
        layout.addWidget(QLabel("Pipeline commercial"))

        # Zone de scroll pour les colonnes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QHBoxLayout()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        self.pipeline_frames = {}
        for etape in LISTE_ETAPES_PIPELINE:
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            frame.setStyleSheet("background-color: white; border: 1px solid #ddd; border-radius: 5px;")
            vbox = QVBoxLayout()
            vbox.addWidget(QLabel(etape))
            scroll_layout.addWidget(frame)
            self.pipeline_frames[etape] = vbox
            frame.setLayout(vbox)

        return page

    def create_alertes_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)

        # Chèques en cours
        layout.addWidget(QLabel("🟡 Chèques en cours"))
        self.cheques_table = QTableWidget()
        self.cheques_table.setColumnCount(5)
        self.cheques_table.setHorizontalHeaderLabels(["Date", "Client", "Montant", "Échéance", "Relance"])
        layout.addWidget(self.cheques_table)

        # Alertes urgentes
        layout.addWidget(QLabel("🔴 Alertes urgentes"))
        self.urgent_table = QTableWidget()
        self.urgent_table.setColumnCount(4)
        self.urgent_table.setHorizontalHeaderLabels(["Date", "Client", "Montant", "Alerte"])
        layout.addWidget(self.urgent_table)

        # Bouton actualiser
        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.clicked.connect(self.refresh_alertes)
        layout.addWidget(btn_refresh)

        return page

    def create_rapports_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)

        # Choix du type de rapport
        form_layout = QFormLayout()
        self.rapport_type = QComboBox()
        self.rapport_type.addItems(["Journalier", "Mensuel", "Pipeline", "Performance"])
        form_layout.addRow("Type de rapport:", self.rapport_type)

        btn_generate = QPushButton("📄 Générer")
        btn_generate.clicked.connect(self.generer_rapport)
        form_layout.addRow(btn_generate)

        layout.addLayout(form_layout)

        # Zone de texte pour le rapport
        self.rapport_text = QTextEdit()
        self.rapport_text.setReadOnly(True)
        self.rapport_text.setFont(QFont("Courier", 10))
        layout.addWidget(self.rapport_text)

        # Boutons d'export
        btn_export_pdf = QPushButton("📥 Exporter PDF")
        btn_export_pdf.clicked.connect(self.export_pdf)
        layout.addWidget(btn_export_pdf)

        return page

    # -------------------------------------------------------------------------
    # MÉTHODES DE NAVIGATION
    # -------------------------------------------------------------------------
    def show_dashboard(self):
        self.stacked_widget.setCurrentWidget(self.dashboard_page)
        self.page_title.setText("Tableau de bord")
        self.refresh_dashboard()

    def show_clients(self):
        self.stacked_widget.setCurrentWidget(self.clients_page)
        self.page_title.setText("Clients")
        self.refresh_clients_table()

    def show_produits(self):
        self.stacked_widget.setCurrentWidget(self.produits_page)
        self.page_title.setText("Produits")
        self.refresh_produits_table()

    def show_transactions(self):
        self.stacked_widget.setCurrentWidget(self.transactions_page)
        self.page_title.setText("Transactions")
        self.refresh_transactions_table()

    def show_pipeline(self):
        self.stacked_widget.setCurrentWidget(self.pipeline_page)
        self.page_title.setText("Pipeline")
        self.refresh_pipeline()

    def show_alertes(self):
        self.stacked_widget.setCurrentWidget(self.alertes_page)
        self.page_title.setText("Alertes")
        self.refresh_alertes()

    def show_rapports(self):
        self.stacked_widget.setCurrentWidget(self.rapports_page)
        self.page_title.setText("Rapports")

    # -------------------------------------------------------------------------
    # MÉTHODES DE RAFRAÎCHISSEMENT
    # -------------------------------------------------------------------------
    def refresh_dashboard(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT SUM(total) FROM transactions")
        ca = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM transactions")
        nb_trans = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM clients")
        nb_clients = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM transactions WHERE alerte='URGENT'")
        nb_alertes = c.fetchone()[0]
        conn.close()

        self.kpi_ca.value_label.setText(f"{ca:,.0f} DHS")
        self.kpi_trans.value_label.setText(str(nb_trans))
        self.kpi_clients.value_label.setText(str(nb_clients))
        self.kpi_alertes.value_label.setText(str(nb_alertes))

        # Dernières transactions
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''SELECT t.date, c.nom, t.total, t.alerte
                     FROM transactions t
                     LEFT JOIN clients c ON t.client_id = c.id
                     ORDER BY t.date DESC LIMIT 10''')
        rows = c.fetchall()
        conn.close()

        self.dashboard_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                if j == 3 and val == "URGENT":
                    item.setForeground(QBrush(QColor(COLOR_DANGER)))
                self.dashboard_table.setItem(i, j, item)

    def refresh_clients_table(self):
        clients = Client.get_all()
        self.clients_table.setRowCount(len(clients))
        for i, c in enumerate(clients):
            self.clients_table.setItem(i, 0, QTableWidgetItem(str(c.id)))
            self.clients_table.setItem(i, 1, QTableWidgetItem(c.nom))
            self.clients_table.setItem(i, 2, QTableWidgetItem(c.secteur))
            self.clients_table.setItem(i, 3, QTableWidgetItem(c.email))
            self.clients_table.setItem(i, 4, QTableWidgetItem(c.telephone))
            self.clients_table.setItem(i, 5, QTableWidgetItem(c.ville))
            self.clients_table.setItem(i, 6, QTableWidgetItem(c.date_creation))
            self.clients_table.setItem(i, 7, QTableWidgetItem("Oui" if c.est_prospect else "Non"))

    def refresh_produits_table(self):
        produits = Produit.get_all()
        self.produits_table.setRowCount(len(produits))
        for i, p in enumerate(produits):
            self.produits_table.setItem(i, 0, QTableWidgetItem(str(p.id)))
            self.produits_table.setItem(i, 1, QTableWidgetItem(p.nom))
            self.produits_table.setItem(i, 2, QTableWidgetItem(p.categorie))
            self.produits_table.setItem(i, 3, QTableWidgetItem(p.unite))
            self.produits_table.setItem(i, 4, QTableWidgetItem(f"{p.prix:.2f}"))

    def refresh_transactions_table(self):
        rows = Transaction.get_all()
        self.transactions_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            # r = (id, date, client, produit, quantite, prix, total, paiement, echeance, commercial, ...)
            self.transactions_table.setItem(i, 0, QTableWidgetItem(r[1]))
            self.transactions_table.setItem(i, 1, QTableWidgetItem(r[2]))
            self.transactions_table.setItem(i, 2, QTableWidgetItem(r[3]))
            self.transactions_table.setItem(i, 3, QTableWidgetItem(str(r[4])))
            self.transactions_table.setItem(i, 4, QTableWidgetItem(f"{r[6]:,.0f}"))
            self.transactions_table.setItem(i, 5, QTableWidgetItem(r[7]))
            self.transactions_table.setItem(i, 6, QTableWidgetItem(r[13]))
            self.transactions_table.setItem(i, 7, QTableWidgetItem(r[15]))

    def refresh_pipeline(self):
        # Nettoyer les colonnes
        for etape, vbox in self.pipeline_frames.items():
            # Enlever les cartes existantes (sauf le titre)
            for i in reversed(range(vbox.count())):
                widget = vbox.itemAt(i).widget()
                if widget and widget != vbox.itemAt(0).widget():  # garder le titre
                    widget.deleteLater()

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        for etape in LISTE_ETAPES_PIPELINE:
            c.execute('''SELECT c.nom, t.total FROM transactions t
                         JOIN clients c ON t.client_id = c.id
                         WHERE t.etape_pipeline=? ORDER BY t.date DESC''', (etape,))
            rows = c.fetchall()
            for nom, montant in rows:
                card = QFrame()
                card.setFrameShape(QFrame.Box)
                card.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; margin: 2px;")
                layout = QVBoxLayout()
                layout.addWidget(QLabel(nom))
                layout.addWidget(QLabel(f"{montant:,.0f} DHS"))
                card.setLayout(layout)
                self.pipeline_frames[etape].addWidget(card)
        conn.close()

    def refresh_alertes(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''SELECT t.date, c.nom, t.total, t.echeance, t.date_relance
                     FROM transactions t
                     LEFT JOIN clients c ON t.client_id = c.id
                     WHERE t.paiement LIKE '%CHEQUE%' OR t.paiement LIKE '%Chèque%'
                     ORDER BY t.date DESC''')
        cheques = c.fetchall()
        c.execute('''SELECT t.date, c.nom, t.total, t.alerte
                     FROM transactions t
                     LEFT JOIN clients c ON t.client_id = c.id
                     WHERE t.alerte = 'URGENT'
                     ORDER BY t.date DESC''')
        urgents = c.fetchall()
        conn.close()

        self.cheques_table.setRowCount(len(cheques))
        for i, r in enumerate(cheques):
            for j, val in enumerate(r):
                self.cheques_table.setItem(i, j, QTableWidgetItem(str(val) if val else ""))

        self.urgent_table.setRowCount(len(urgents))
        for i, r in enumerate(urgents):
            for j, val in enumerate(r):
                self.urgent_table.setItem(i, j, QTableWidgetItem(str(val)))

    # -------------------------------------------------------------------------
    # ACTIONS CLIENTS
    # -------------------------------------------------------------------------
    def ajouter_client(self):
        self._client_form()

    def modifier_client(self):
        selected = self.clients_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Attention", "Sélectionnez un client.")
            return
        client_id = int(self.clients_table.item(selected, 0).text())
        client = Client.get_by_id(client_id)
        if client:
            self._client_form(client)

    def supprimer_client(self):
        selected = self.clients_table.currentRow()
        if selected < 0:
            return
        reply = QMessageBox.question(self, "Confirmation", "Supprimer ce client ?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            client_id = int(self.clients_table.item(selected, 0).text())
            client = Client.get_by_id(client_id)
            if client:
                client.delete()
                self.refresh_clients_table()
                self.refresh_dashboard()

    def _client_form(self, client=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Client" if client else "Nouveau client")
        dialog.setModal(True)
        layout = QFormLayout()

        fields = {}
        for label in ('Nom', 'Secteur', 'Email', 'Téléphone', 'Ville'):
            edit = QLineEdit()
            if client:
                edit.setText(getattr(client, label.lower()))
            layout.addRow(label + ":", edit)
            fields[label.lower()] = edit

        prospect_cb = QCheckBox("Est un prospect")
        if client:
            prospect_cb.setChecked(client.est_prospect == 1)
        else:
            prospect_cb.setChecked(True)
        layout.addRow(prospect_cb)

        def save():
            if not fields['nom'].text():
                QMessageBox.critical(dialog, "Erreur", "Le nom est obligatoire")
                return
            if client is None:
                c = Client(
                    nom=fields['nom'].text(),
                    secteur=fields['secteur'].text(),
                    email=fields['email'].text(),
                    telephone=fields['telephone'].text(),
                    ville=fields['ville'].text(),
                    est_prospect=1 if prospect_cb.isChecked() else 0
                )
            else:
                client.nom = fields['nom'].text()
                client.secteur = fields['secteur'].text()
                client.email = fields['email'].text()
                client.telephone = fields['telephone'].text()
                client.ville = fields['ville'].text()
                client.est_prospect = 1 if prospect_cb.isChecked() else 0
                c = client
            c.save()
            self.refresh_clients_table()
            self.refresh_dashboard()
            dialog.accept()

        btn_save = QPushButton("Enregistrer")
        btn_save.clicked.connect(save)
        layout.addRow(btn_save)

        dialog.setLayout(layout)
        dialog.exec_()

    # -------------------------------------------------------------------------
    # ACTIONS PRODUITS
    # -------------------------------------------------------------------------
    def ajouter_produit(self):
        self._produit_form()

    def modifier_produit(self):
        selected = self.produits_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Attention", "Sélectionnez un produit.")
            return
        prod_id = int(self.produits_table.item(selected, 0).text())
        produit = Produit.get_by_id(prod_id)
        if produit:
            self._produit_form(produit)

    def supprimer_produit(self):
        selected = self.produits_table.currentRow()
        if selected < 0:
            return
        reply = QMessageBox.question(self, "Confirmation", "Supprimer ce produit ?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            prod_id = int(self.produits_table.item(selected, 0).text())
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DELETE FROM produits WHERE id=?", (prod_id,))
            conn.commit()
            conn.close()
            self.refresh_produits_table()

    def _produit_form(self, produit=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Produit" if produit else "Nouveau produit")
        layout = QFormLayout()

        nom = QLineEdit()
        categorie = QLineEdit()
        unite = QLineEdit()
        prix = QLineEdit()

        if produit:
            nom.setText(produit.nom)
            categorie.setText(produit.categorie)
            unite.setText(produit.unite)
            prix.setText(str(produit.prix))

        layout.addRow("Nom:", nom)
        layout.addRow("Catégorie:", categorie)
        layout.addRow("Unité:", unite)
        layout.addRow("Prix:", prix)

        def save():
            if not nom.text():
                QMessageBox.critical(dialog, "Erreur", "Le nom est obligatoire")
                return
            try:
                p = float(prix.text() or 0)
            except:
                QMessageBox.critical(dialog, "Erreur", "Prix invalide")
                return
            if produit is None:
                p = Produit(nom=nom.text(), categorie=categorie.text(), unite=unite.text(), prix=p)
            else:
                produit.nom = nom.text()
                produit.categorie = categorie.text()
                produit.unite = unite.text()
                produit.prix = p
                p = produit
            p.save()
            self.refresh_produits_table()
            dialog.accept()

        btn_save = QPushButton("Enregistrer")
        btn_save.clicked.connect(save)
        layout.addRow(btn_save)

        dialog.setLayout(layout)
        dialog.exec_()

    # -------------------------------------------------------------------------
    # ACTIONS TRANSACTIONS
    # -------------------------------------------------------------------------
    def ajouter_transaction(self):
        client_nom = self.trans_client.currentText()
        if not client_nom:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un client.")
            return
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM clients WHERE nom=?", (client_nom,))
        row = c.fetchone()
        if not row:
            client = Client(nom=client_nom)
            client.save()
            client_id = client.id
        else:
            client_id = row[0]

        produit_nom = self.trans_produit.currentText()
        if not produit_nom:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un produit.")
            return
        c.execute("SELECT id, prix FROM produits WHERE nom=?", (produit_nom,))
        row = c.fetchone()
        if not row:
            prod = Produit(nom=produit_nom, categorie="Divers", unite=self.trans_unite.currentText(), prix=0.0)
            prod.save()
            produit_id = prod.id
            prix_produit = 0.0
        else:
            produit_id = row[0]
            prix_produit = row[1]
        conn.close()

        try:
            quantite = float(self.trans_quantite.text())
            prix_saisi = float(self.trans_prix.text())
        except:
            QMessageBox.critical(self, "Erreur", "Quantité ou prix invalide")
            return

        if prix_saisi == 0 and prix_produit != 0:
            prix_saisi = prix_produit
        total = quantite * prix_saisi

        paiement = self.trans_paiement.currentText()
        echeance = self.trans_echeance.currentText()
        commercial = self.trans_commercial.currentText()
        type_tel = self.trans_type_tel.currentText()
        telephone = self.trans_telephone.text()
        flux = self.trans_flux.currentText()
        statut = self.trans_statut.currentText()
        remarque = self.trans_remarque.currentText()
        etape = self.trans_etape.currentText()

        # Détermination alerte
        alerte = "SUIVI NORMAL"
        if "RETARD" in paiement.upper() or "URGENT" in remarque.upper():
            alerte = "URGENT"
        elif "CHEQUE" in paiement.upper():
            alerte = "A SURVEILLER"
        elif "COMPTANT" in paiement.upper():
            alerte = "OK"

        date_relance = ""
        if "CHEQUE" in paiement.upper():
            date_relance = (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d")

        trans = Transaction(
            date=datetime.now().strftime("%Y-%m-%d"),
            client_id=client_id,
            produit_id=produit_id,
            quantite=quantite,
            prix_unitaire=prix_saisi,
            total=total,
            paiement=paiement,
            echeance=echeance,
            commercial=commercial,
            type_tel=type_tel,
            telephone=telephone,
            flux=flux,
            statut=statut,
            remarque=remarque,
            alerte=alerte,
            date_relance=date_relance,
            etape_pipeline=etape
        )
        trans.save()
        self.refresh_transactions_table()
        self.refresh_dashboard()
        self.refresh_alertes()
        QMessageBox.information(self, "Succès", f"Transaction enregistrée, total: {total:,.0f} DHS")

    # -------------------------------------------------------------------------
    # RAPPORTS
    # -------------------------------------------------------------------------
    def generer_rapport(self):
        type_r = self.rapport_type.currentText()
        if type_r == "Journalier":
            self.rapport_journalier()
        elif type_r == "Mensuel":
            self.rapport_mensuel()
        elif type_r == "Pipeline":
            self.rapport_pipeline()
        elif type_r == "Performance":
            self.rapport_performance()

    def rapport_journalier(self):
        today = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''SELECT COUNT(*), SUM(total) FROM transactions WHERE date=?''', (today,))
        nb, ca = c.fetchone()
        nb = nb or 0
        ca = ca or 0
        c.execute('''SELECT c.nom, t.total FROM transactions t
                     JOIN clients c ON t.client_id = c.id
                     WHERE t.date=? ORDER BY t.total DESC''', (today,))
        details = c.fetchall()
        conn.close()

        rapport = f"RAPPORT JOURNALIER - {today}\n"
        rapport += "="*40 + "\n"
        rapport += f"Transactions : {nb}\n"
        rapport += f"CA total : {ca:,.0f} DHS\n"
        if nb > 0:
            rapport += f"CA moyen : {ca/nb:,.0f} DHS\n\n"
            rapport += "Détail :\n"
            for nom, montant in details:
                rapport += f"  • {nom} : {montant:,.0f} DHS\n"
        self.rapport_text.setText(rapport)

    def rapport_mensuel(self):
        mois = datetime.now().strftime("%Y-%m")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''SELECT COUNT(*), SUM(total) FROM transactions WHERE strftime('%Y-%m', date)=?''', (mois,))
        nb, ca = c.fetchone()
        nb = nb or 0
        ca = ca or 0
        c.execute('''SELECT c.nom, SUM(t.total) FROM transactions t
                     JOIN clients c ON t.client_id = c.id
                     WHERE strftime('%Y-%m', t.date)=?
                     GROUP BY c.nom ORDER BY SUM(t.total) DESC''', (mois,))
        tops = c.fetchall()
        conn.close()

        rapport = f"RAPPORT MENSUEL - {mois}\n"
        rapport += "="*40 + "\n"
        rapport += f"Transactions : {nb}\n"
        rapport += f"CA total : {ca:,.0f} DHS\n"
        if nb > 0:
            rapport += f"CA moyen : {ca/nb:,.0f} DHS\n\n"
            rapport += "Top clients :\n"
            for nom, montant in tops[:5]:
                rapport += f"  • {nom} : {montant:,.0f} DHS\n"
        self.rapport_text.setText(rapport)

    def rapport_pipeline(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        rapport = "PIPELINE COMMERCIAL\n" + "="*40 + "\n"
        total_opportunites = 0
        for etape in LISTE_ETAPES_PIPELINE[:5]:
            c.execute('''SELECT COUNT(*), SUM(total) FROM transactions WHERE etape_pipeline=?''', (etape,))
            nb, montant = c.fetchone()
            nb = nb or 0
            montant = montant or 0
            rapport += f"{etape} : {nb} opportunités, {montant:,.0f} DHS\n"
            total_opportunites += montant
        rapport += f"\nTotal pipeline : {total_opportunites:,.0f} DHS\n"
        conn.close()
        self.rapport_text.setText(rapport)

    def rapport_performance(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''SELECT commercial, COUNT(*), SUM(total) FROM transactions GROUP BY commercial''')
        perf = c.fetchall()
        rapport = "PERFORMANCE COMMERCIALE\n" + "="*40 + "\n"
        for comm, nb, ca in perf:
            rapport += f"{comm} : {nb} ventes, {ca:,.0f} DHS\n"
        conn.close()
        self.rapport_text.setText(rapport)

    def export_pdf(self):
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import cm
        except ImportError:
            QMessageBox.critical(self, "Erreur", "ReportLab n'est pas installé. Exécutez : pip install reportlab")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Exporter PDF", "", "PDF files (*.pdf)")
        if not filename:
            return
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        c.setFont("Helvetica-Bold", 16)
        c.drawString(2*cm, height-2*cm, "SNEP CRM - Rapport")
        c.setFont("Helvetica", 10)
        y = height - 4*cm
        for line in self.rapport_text.toPlainText().split('\n'):
            if y < 2*cm:
                c.showPage()
                y = height - 2*cm
                c.setFont("Helvetica", 10)
            c.drawString(2*cm, y, line[:80])
            y -= 0.5*cm
        c.save()
        QMessageBox.information(self, "Export", "Rapport PDF généré.")

# -----------------------------------------------------------------------------
# LANCEMENT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    window = CRM_MainWindow()
    window.show()
    sys.exit(app.exec_())