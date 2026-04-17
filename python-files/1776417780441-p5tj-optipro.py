import json
import logging
import copy
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import zipfile
import shutil
import tempfile
import os
import csv
import threading
import hashlib
import sqlite3
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager

# Für Diagramme
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ------------------------------------------------------------
#  Konfiguration & Hilfsfunktionen
# ------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

FONT_NAME = 'Helvetica'
try:
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
    FONT_NAME = 'Arial'
except Exception:
    try:
        pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        FONT_NAME = 'DejaVu'
    except Exception:
        pass

# Farben (heller Modus – Standard)
LIGHT_COLORS = {
    'bg':           '#F7F9FC',
    'sidebar':      '#1E2A3A',
    'accent':       '#2563EB',
    'accent_hover': '#1D4ED8',
    'success':      '#16A34A',
    'danger':       '#DC2626',
    'warning':      '#D97706',
    'text_main':    '#111827',
    'text_muted':   '#6B7280',
    'border':       '#E5E7EB',
    'card':         '#FFFFFF',
    'header_bg':    '#1E2A3A',
    'row_alt':      '#F1F5F9',
    'btn_pdf':      '#16A34A',
}

DARK_COLORS = {
    'bg':           '#1E1E2E',
    'sidebar':      '#0F0F1A',
    'accent':       '#3B82F6',
    'accent_hover': '#2563EB',
    'success':      '#22C55E',
    'danger':       '#EF4444',
    'warning':      '#F59E0B',
    'text_main':    '#F3F4F6',
    'text_muted':   '#9CA3AF',
    'border':       '#374151',
    'card':         '#2D2D3A',
    'header_bg':    '#0F0F1A',
    'row_alt':      '#262633',
    'btn_pdf':      '#22C55E',
}

COLORS = LIGHT_COLORS.copy()

def toggle_dark_mode():
    global COLORS
    if COLORS is LIGHT_COLORS:
        COLORS.update(DARK_COLORS)
    else:
        COLORS.update(LIGHT_COLORS)

def format_currency(value: float) -> str:
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------------------------------------------------
#  MySQL-Konfiguration – HIER DEINE ZUGANGSDATEN EINTRAGEN
# ------------------------------------------------------------
MYSQL_CONFIG = {
    'host': '72.60.86.50',        # z.B. 'mysql.hostinger.com' oder '217.91.31.252'
    'port': 3306,
    'user': 'u187396654_Jonas',        # Dein Benutzername (z.B. 'u187396654_Jonas')
    'password': 'Manupuff!12',    # Dein Passwort
    'database': 'u187396654_Daten'     # Deine Datenbank (z.B. 'u187396654_meinedb')
}
# Wenn alle Felder leer sind, wird automatisch SQLite verwendet.

# ------------------------------------------------------------
#  Datenbank-Pfade
# ------------------------------------------------------------
def get_data_dir() -> Path:
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir

DB_CONFIG_PATH = get_data_dir() / "db_config.json"
LOCAL_SQLITE_PATH = get_data_dir() / "enterprise_local.db"

# ------------------------------------------------------------
#  Datenbank-Konfiguration (lokal)
# ------------------------------------------------------------
class DatabaseConfig:
    def __init__(self):
        self.config = {}
        self._load()

    def _load(self):
        # Zuerst prüfen, ob vordefinierte MySQL-Daten vorhanden sind
        if MYSQL_CONFIG['host'] and MYSQL_CONFIG['user'] and MYSQL_CONFIG['database']:
            self.config = MYSQL_CONFIG.copy()
            return
        # Ansonsten aus JSON-Datei laden
        if DB_CONFIG_PATH.exists():
            try:
                with open(DB_CONFIG_PATH, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = {}
        else:
            self.config = {}

    def save(self):
        # Nur speichern, wenn nicht vordefiniert (um die JSON nicht zu überschreiben)
        if not (MYSQL_CONFIG['host'] and MYSQL_CONFIG['user'] and MYSQL_CONFIG['database']):
            with open(DB_CONFIG_PATH, 'w') as f:
                json.dump(self.config, f, indent=4)

    def is_mysql_configured(self):
        return bool(self.config.get('host') and self.config.get('user') and self.config.get('database'))

    def get_mysql_config(self):
        return self.config

    def set_mysql_config(self, host, port, user, password, database):
        self.config = {'host': host, 'port': port, 'user': user, 'password': password, 'database': database}
        self.save()

    def clear_mysql_config(self):
        self.config = {}
        self.save()

# ------------------------------------------------------------
#  Datenbank-Manager (unterstützt SQLite und MySQL)
# ------------------------------------------------------------
class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.db_config = DatabaseConfig()
        self.use_mysql = self.db_config.is_mysql_configured()
        self.connection = None
        self._connect()
        if self.use_mysql and self.connection:
            self._init_mysql_tables()
        elif self.connection:
            self._init_sqlite_tables()
        # Fallback, falls keine Verbindung (z.B. MySQL fehlgeschlagen)
        if not self.connection:
            self.use_mysql = False
            self._connect_sqlite()
            self._init_sqlite_tables()

    def _connect(self):
        if self.use_mysql:
            try:
                cfg = self.db_config.get_mysql_config()
                self.connection = mysql.connector.connect(
                    host=cfg['host'],
                    port=cfg.get('port', 3306),
                    user=cfg['user'],
                    password=cfg['password'],
                    database=cfg['database'],
                    autocommit=False
                )
            except Error as e:
                logging.error(f"MySQL-Verbindung fehlgeschlagen: {e}. Fallback zu SQLite.")
                self.use_mysql = False
                self._connect_sqlite()
        else:
            self._connect_sqlite()

    def _connect_sqlite(self):
        self.connection = sqlite3.connect(str(LOCAL_SQLITE_PATH), check_same_thread=False)
        self.connection.row_factory = sqlite3.Row

    def _init_mysql_tables(self):
        cursor = self.connection.cursor()
        # Benutzer
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                created VARCHAR(255) NOT NULL
            )
        ''')
        # Kunden
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name TEXT,
                address TEXT,
                contact TEXT,
                phone TEXT,
                email TEXT,
                customer_type VARCHAR(50)
            )
        ''')
        # Produkte
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                description TEXT NOT NULL,
                unit_price DOUBLE NOT NULL
            )
        ''')
        # Firmeneinstellungen
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company (
                id INT PRIMARY KEY CHECK (id = 1),
                name TEXT,
                address_line1 TEXT,
                address_line2 TEXT,
                phone TEXT,
                email TEXT,
                website TEXT,
                ceo TEXT,
                smtp_server TEXT,
                smtp_port INT,
                smtp_user TEXT,
                smtp_password TEXT,
                offer_number_prefix VARCHAR(50),
                offer_number_counter INT
            )
        ''')
        # Textvorlagen
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                text TEXT NOT NULL
            )
        ''')
        # Angebote
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                offer_number VARCHAR(255) UNIQUE NOT NULL,
                date VARCHAR(50),
                valid_until VARCHAR(50),
                customer_ref VARCHAR(255),
                customer_type VARCHAR(50),
                customer_name TEXT,
                customer_address TEXT,
                customer_contact TEXT,
                customer_phone TEXT,
                customer_email TEXT,
                items TEXT,
                tax_rate INT,
                discount DOUBLE,
                shipping DOUBLE,
                personal_message TEXT,
                terms TEXT,
                status VARCHAR(50),
                owner VARCHAR(255)
            )
        ''')
        self.connection.commit()
        self._init_default_data_mysql()

    def _init_default_data_mysql(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (username, password_hash, role, created) VALUES (%s, %s, %s, %s)",
                           ("admin", hash_password("admin"), "admin", datetime.now().isoformat()))
        cursor.execute("SELECT COUNT(*) FROM company")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO company (id, name, address_line1, address_line2, phone, email, website, ceo,
                                     smtp_server, smtp_port, smtp_user, smtp_password,
                                     offer_number_prefix, offer_number_counter)
                VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', ("Meine Firma GmbH", "Musterstraße 1", "12345 Musterstadt",
                  "+49 123 4567890", "info@ihrefirma.de", "www.ihrefirma.de", "Max Mustermann",
                  "", 587, "", "", "A", 1))
        cursor.execute("SELECT COUNT(*) FROM templates")
        if cursor.fetchone()[0] == 0:
            templates = [
                ("Standard (Gewerbe)", "Lieferung erfolgt innerhalb von 10 Werktagen nach Zahlungseingang.\nZahlbar innerhalb 30 Tagen netto.\nEs gelten unsere AGB."),
                ("Privatkunde", "Lieferung nach Zahlungseingang. Kein Widerrufsrecht bei individualisierten Produkten.\nEs gelten die gesetzlichen Bestimmungen."),
                ("Eilauftrag", "Expresslieferung innerhalb von 2 Werktagen.\nZuschlag für Eilauftrag: 15% auf den Nettobetrag.\nZahlung sofort nach Rechnungserhalt.")
            ]
            cursor.executemany("INSERT INTO templates (name, text) VALUES (%s, %s)", templates)
        self.connection.commit()

    def _init_sqlite_tables(self):
        cursor = self.connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                address TEXT,
                contact TEXT,
                phone TEXT,
                email TEXT,
                customer_type TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                unit_price REAL NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT,
                address_line1 TEXT,
                address_line2 TEXT,
                phone TEXT,
                email TEXT,
                website TEXT,
                ceo TEXT,
                smtp_server TEXT,
                smtp_port INTEGER,
                smtp_user TEXT,
                smtp_password TEXT,
                offer_number_prefix TEXT,
                offer_number_counter INTEGER
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                text TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                offer_number TEXT UNIQUE NOT NULL,
                date TEXT,
                valid_until TEXT,
                customer_ref TEXT,
                customer_type TEXT,
                customer_name TEXT,
                customer_address TEXT,
                customer_contact TEXT,
                customer_phone TEXT,
                customer_email TEXT,
                items TEXT,
                tax_rate INTEGER,
                discount REAL,
                shipping REAL,
                personal_message TEXT,
                terms TEXT,
                status TEXT,
                owner TEXT
            )
        ''')
        self.connection.commit()
        self._init_default_data_sqlite()

    def _init_default_data_sqlite(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (username, password_hash, role, created) VALUES (?, ?, ?, ?)",
                           ("admin", hash_password("admin"), "admin", datetime.now().isoformat()))
        cursor.execute("SELECT COUNT(*) FROM company")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO company (id, name, address_line1, address_line2, phone, email, website, ceo,
                                     smtp_server, smtp_port, smtp_user, smtp_password,
                                     offer_number_prefix, offer_number_counter)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ("Meine Firma GmbH", "Musterstraße 1", "12345 Musterstadt",
                  "+49 123 4567890", "info@ihrefirma.de", "www.ihrefirma.de", "Max Mustermann",
                  "", 587, "", "", "A", 1))
        cursor.execute("SELECT COUNT(*) FROM templates")
        if cursor.fetchone()[0] == 0:
            templates = [
                ("Standard (Gewerbe)", "Lieferung erfolgt innerhalb von 10 Werktagen nach Zahlungseingang.\nZahlbar innerhalb 30 Tagen netto.\nEs gelten unsere AGB."),
                ("Privatkunde", "Lieferung nach Zahlungseingang. Kein Widerrufsrecht bei individualisierten Produkten.\nEs gelten die gesetzlichen Bestimmungen."),
                ("Eilauftrag", "Expresslieferung innerhalb von 2 Werktagen.\nZuschlag für Eilauftrag: 15% auf den Nettobetrag.\nZahlung sofort nach Rechnungserhalt.")
            ]
            cursor.executemany("INSERT INTO templates (name, text) VALUES (?, ?)", templates)
        self.connection.commit()

    def execute(self, sql, params=()):
        if not self.connection:
            raise Exception("Keine Datenbankverbindung")
        if self.use_mysql:
            cursor = self.connection.cursor(dictionary=True)
        else:
            cursor = self.connection.cursor()
        cursor.execute(sql, params)
        return cursor

    def fetch_one(self, sql, params=()):
        cursor = self.execute(sql, params)
        row = cursor.fetchone()
        cursor.close()
        return row

    def fetch_all(self, sql, params=()):
        cursor = self.execute(sql, params)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def execute_many(self, sql, params_list):
        if not self.connection:
            raise Exception("Keine Datenbankverbindung")
        cursor = self.connection.cursor()
        cursor.executemany(sql, params_list)
        self.connection.commit()
        cursor.close()

    def commit(self):
        if self.connection:
            self.connection.commit()

    def rollback(self):
        if self.connection:
            self.connection.rollback()

    def close(self):
        if self.connection:
            self.connection.close()
class UserDatabase:
    def __init__(self):
        self.db = DatabaseManager()

    def verify_user(self, username: str, password: str) -> Optional[Dict]:
        row = self.db.fetch_one(
            "SELECT username, role FROM users WHERE username = %s AND password_hash = %s" if self.db.use_mysql
            else "SELECT username, role FROM users WHERE username = ? AND password_hash = ?",
            (username, hash_password(password))
        )
        return row if row else None

    def get_all_users(self) -> List[Dict]:
        rows = self.db.fetch_all("SELECT username, role, created FROM users")
        return rows

    def add_user(self, username: str, password: str, role: str = "user"):
        try:
            self.db.execute(
                "INSERT INTO users (username, password_hash, role, created) VALUES (%s, %s, %s, %s)" if self.db.use_mysql
                else "INSERT INTO users (username, password_hash, role, created) VALUES (?, ?, ?, ?)",
                (username, hash_password(password), role, datetime.now().isoformat())
            )
            self.db.commit()
            return True
        except Exception:
            return False

    def change_password(self, username: str, new_password: str):
        self.db.execute(
            "UPDATE users SET password_hash = %s WHERE username = %s" if self.db.use_mysql
            else "UPDATE users SET password_hash = ? WHERE username = ?",
            (hash_password(new_password), username)
        )
        self.db.commit()
        return True

    def delete_user(self, username: str):
        self.db.execute(
            "DELETE FROM users WHERE username = %s" if self.db.use_mysql else "DELETE FROM users WHERE username = ?",
            (username,)
        )
        self.db.commit()

class CustomerDatabase:
    def __init__(self):
        self.db = DatabaseManager()

    def get_all(self) -> List[Dict]:
        return self.db.fetch_all("SELECT id, name, address, contact, phone, email, customer_type FROM customers")

    def add(self, customer: Dict):
        sql = ("INSERT INTO customers (name, address, contact, phone, email, customer_type) VALUES (%s, %s, %s, %s, %s, %s)"
               if self.db.use_mysql else
               "INSERT INTO customers (name, address, contact, phone, email, customer_type) VALUES (?, ?, ?, ?, ?, ?)")
        self.db.execute(sql, (customer.get("name", ""), customer.get("address", ""), customer.get("contact", ""),
                              customer.get("phone", ""), customer.get("email", ""), customer.get("customer_type", "gewerblich")))
        self.db.commit()

    def update(self, cust_id: int, customer: Dict):
        sql = ("UPDATE customers SET name=%s, address=%s, contact=%s, phone=%s, email=%s, customer_type=%s WHERE id=%s"
               if self.db.use_mysql else
               "UPDATE customers SET name=?, address=?, contact=?, phone=?, email=?, customer_type=? WHERE id=?")
        self.db.execute(sql, (customer.get("name", ""), customer.get("address", ""), customer.get("contact", ""),
                              customer.get("phone", ""), customer.get("email", ""), customer.get("customer_type", "gewerblich"), cust_id))
        self.db.commit()

    def delete(self, cust_id: int):
        self.db.execute("DELETE FROM customers WHERE id=%s" if self.db.use_mysql else "DELETE FROM customers WHERE id=?", (cust_id,))
        self.db.commit()

class ProductDatabase:
    def __init__(self):
        self.db = DatabaseManager()

    def get_all(self) -> List[Dict]:
        return self.db.fetch_all("SELECT id, description, unit_price FROM products")

    def add(self, product: Dict):
        sql = "INSERT INTO products (description, unit_price) VALUES (%s, %s)" if self.db.use_mysql else "INSERT INTO products (description, unit_price) VALUES (?, ?)"
        self.db.execute(sql, (product["description"], product["unit_price"]))
        self.db.commit()

    def update(self, prod_id: int, product: Dict):
        sql = "UPDATE products SET description=%s, unit_price=%s WHERE id=%s" if self.db.use_mysql else "UPDATE products SET description=?, unit_price=? WHERE id=?"
        self.db.execute(sql, (product["description"], product["unit_price"], prod_id))
        self.db.commit()

    def delete(self, prod_id: int):
        self.db.execute("DELETE FROM products WHERE id=%s" if self.db.use_mysql else "DELETE FROM products WHERE id=?", (prod_id,))
        self.db.commit()

class CompanyDatabase:
    def __init__(self):
        self.db = DatabaseManager()

    def get_company(self) -> Dict:
        row = self.db.fetch_one("SELECT * FROM company WHERE id=1")
        return row if row else {}

    def update_company(self, data: Dict):
        sql = '''
            UPDATE company SET
                name=%s, address_line1=%s, address_line2=%s, phone=%s, email=%s, website=%s, ceo=%s,
                smtp_server=%s, smtp_port=%s, smtp_user=%s, smtp_password=%s,
                offer_number_prefix=%s, offer_number_counter=%s
            WHERE id=1
        ''' if self.db.use_mysql else '''
            UPDATE company SET
                name=?, address_line1=?, address_line2=?, phone=?, email=?, website=?, ceo=?,
                smtp_server=?, smtp_port=?, smtp_user=?, smtp_password=?,
                offer_number_prefix=?, offer_number_counter=?
            WHERE id=1
        '''
        self.db.execute(sql, (data.get("name", ""), data.get("address_line1", ""), data.get("address_line2", ""),
                              data.get("phone", ""), data.get("email", ""), data.get("website", ""), data.get("ceo", ""),
                              data.get("smtp_server", ""), data.get("smtp_port", 587), data.get("smtp_user", ""),
                              data.get("smtp_password", ""), data.get("offer_number_prefix", "A"), data.get("offer_number_counter", 1)))
        self.db.commit()

class TemplateDatabase:
    def __init__(self):
        self.db = DatabaseManager()

    def get_all(self) -> List[Dict]:
        return self.db.fetch_all("SELECT name, text FROM templates")

    def get_template(self, name: str) -> str:
        row = self.db.fetch_one("SELECT text FROM templates WHERE name=%s" if self.db.use_mysql else "SELECT text FROM templates WHERE name=?", (name,))
        return row["text"] if row else ""

class OfferDatabase:
    def __init__(self):
        self.db = DatabaseManager()
        self.versions_dir = get_data_dir() / "versions"
        self.versions_dir.mkdir(exist_ok=True)

    def _save_version(self, offer: Dict):
        if not offer.get("offer_number"):
            return
        version_file = self.versions_dir / f"{offer['offer_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(offer, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Fehler beim Speichern der Version: {e}")

    def get_offer_by_number(self, number: str) -> Optional[Dict]:
        row = self.db.fetch_one("SELECT * FROM offers WHERE offer_number=%s" if self.db.use_mysql else "SELECT * FROM offers WHERE offer_number=?", (number,))
        if row:
            offer = dict(row)
            offer["items"] = json.loads(offer["items"]) if offer["items"] else []
            offer["customer"] = {
                "name": offer.pop("customer_name", ""),
                "address": offer.pop("customer_address", ""),
                "contact": offer.pop("customer_contact", ""),
                "phone": offer.pop("customer_phone", ""),
                "email": offer.pop("customer_email", "")
            }
            return offer
        return None

    def get_all(self, username: str = None, is_admin: bool = False) -> List[Dict]:
        if is_admin:
            rows = self.db.fetch_all("SELECT * FROM offers")
        else:
            rows = self.db.fetch_all("SELECT * FROM offers WHERE owner=%s" if self.db.use_mysql else "SELECT * FROM offers WHERE owner=?", (username,))
        offers = []
        for row in rows:
            offer = dict(row)
            offer["items"] = json.loads(offer["items"]) if offer["items"] else []
            offer["customer"] = {
                "name": offer.pop("customer_name", ""),
                "address": offer.pop("customer_address", ""),
                "contact": offer.pop("customer_contact", ""),
                "phone": offer.pop("customer_phone", ""),
                "email": offer.pop("customer_email", "")
            }
            offers.append(offer)
        return offers

    def add_or_update(self, offer: Dict, username: str):
        existing = self.get_offer_by_number(offer.get("offer_number"))
        items_json = json.dumps(offer.get("items", []), ensure_ascii=False)
        cust = offer.get("customer", {})
        if existing:
            sql = '''
                UPDATE offers SET
                    date=%s, valid_until=%s, customer_ref=%s, customer_type=%s,
                    customer_name=%s, customer_address=%s, customer_contact=%s, customer_phone=%s, customer_email=%s,
                    items=%s, tax_rate=%s, discount=%s, shipping=%s, personal_message=%s, terms=%s, status=%s, owner=%s
                WHERE offer_number=%s
            ''' if self.db.use_mysql else '''
                UPDATE offers SET
                    date=?, valid_until=?, customer_ref=?, customer_type=?,
                    customer_name=?, customer_address=?, customer_contact=?, customer_phone=?, customer_email=?,
                    items=?, tax_rate=?, discount=?, shipping=?, personal_message=?, terms=?, status=?, owner=?
                WHERE offer_number=?
            '''
            self.db.execute(sql, (offer.get("date", ""), offer.get("valid_until", ""), offer.get("customer_ref", ""),
                                  offer.get("customer_type", ""),
                                  cust.get("name", ""), cust.get("address", ""), cust.get("contact", ""),
                                  cust.get("phone", ""), cust.get("email", ""),
                                  items_json, offer.get("tax_rate", 19), offer.get("discount", 0.0), offer.get("shipping", 0.0),
                                  offer.get("personal_message", ""), offer.get("terms", ""), offer.get("status", "Entwurf"), username,
                                  offer.get("offer_number")))
        else:
            sql = '''
                INSERT INTO offers (
                    offer_number, date, valid_until, customer_ref, customer_type,
                    customer_name, customer_address, customer_contact, customer_phone, customer_email,
                    items, tax_rate, discount, shipping, personal_message, terms, status, owner
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ''' if self.db.use_mysql else '''
                INSERT INTO offers (
                    offer_number, date, valid_until, customer_ref, customer_type,
                    customer_name, customer_address, customer_contact, customer_phone, customer_email,
                    items, tax_rate, discount, shipping, personal_message, terms, status, owner
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            '''
            self.db.execute(sql, (offer.get("offer_number"), offer.get("date", ""), offer.get("valid_until", ""),
                                  offer.get("customer_ref", ""), offer.get("customer_type", ""),
                                  cust.get("name", ""), cust.get("address", ""), cust.get("contact", ""),
                                  cust.get("phone", ""), cust.get("email", ""),
                                  items_json, offer.get("tax_rate", 19), offer.get("discount", 0.0), offer.get("shipping", 0.0),
                                  offer.get("personal_message", ""), offer.get("terms", ""), offer.get("status", "Entwurf"), username))
        self.db.commit()
        if existing:
            self._save_version(existing)

    def delete(self, offer_number: str, username: str, is_admin: bool = False):
        if is_admin:
            self.db.execute("DELETE FROM offers WHERE offer_number=%s" if self.db.use_mysql else "DELETE FROM offers WHERE offer_number=?", (offer_number,))
        else:
            self.db.execute("DELETE FROM offers WHERE offer_number=%s AND owner=%s" if self.db.use_mysql else "DELETE FROM offers WHERE offer_number=? AND owner=?", (offer_number, username))
        self.db.commit()

    def get_versions(self, offer_number: str) -> List[Path]:
        pattern = f"{offer_number}_*.json"
        versions = list(self.versions_dir.glob(pattern))
        versions.sort(key=lambda p: p.stat().st_mtime)
        return versions

    def restore_version(self, version_path: Path) -> Dict:
        with open(version_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_statistics(self, username: str = None, is_admin: bool = False) -> Dict:
        offers = self.get_all(username, is_admin)
        total_offers = len(offers)
        total_net = 0.0
        total_gross = 0.0
        status_count = {"Entwurf": 0, "Gesendet": 0, "Angenommen": 0, "Abgelehnt": 0}
        monthly_revenue = {}
        for offer in offers:
            net = sum(item["quantity"] * item["unit_price"] for item in offer.get("items", []))
            disc = offer.get("discount", 0.0)
            ship = offer.get("shipping", 0.0)
            net_after = net * (1 - disc/100) + ship
            tax = net_after * offer.get("tax_rate", 19) / 100
            gross = net_after + tax
            total_net += net_after
            total_gross += gross
            status = offer.get("status", "Entwurf")
            status_count[status] = status_count.get(status, 0) + 1
            date_str = offer.get("date", "")
            try:
                if date_str:
                    date_obj = datetime.strptime(date_str, "%d.%m.%Y")
                    month_key = date_obj.strftime("%Y-%m")
                    monthly_revenue[month_key] = monthly_revenue.get(month_key, 0) + gross
            except:
                pass
        now = datetime.now()
        for i in range(12):
            month_key = (now - timedelta(days=30*i)).strftime("%Y-%m")
            if month_key not in monthly_revenue:
                monthly_revenue[month_key] = 0
        sorted_months = sorted(monthly_revenue.keys())
        return {
            "total_offers": total_offers,
            "total_net": total_net,
            "total_gross": total_gross,
            "status_count": status_count,
            "monthly_revenue": [(m, monthly_revenue[m]) for m in sorted_months[-12:]]
        }

# ------------------------------------------------------------
#  PDF-Generator (unverändert)
# ------------------------------------------------------------
class EnterprisePDFGenerator:
    def __init__(self, offer_data: Dict[str, Any], company_data: Dict[str, Any], filename: str):
        self.offer = offer_data
        self.company = company_data
        self.filename = filename
        self.doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm,
                                     leftMargin=25*mm, rightMargin=25*mm)
        self.story = []
        self.styles = self._setup_styles()

    def _setup_styles(self):
        styles = getSampleStyleSheet()
        styles['Title'].fontName = FONT_NAME
        styles['Title'].fontSize = 16
        styles['Title'].textColor = colors.HexColor('#003366')
        styles['Title'].alignment = TA_CENTER
        styles['Title'].spaceAfter = 15
        styles.add(ParagraphStyle(name='CompanyName', parent=styles['Normal'], fontName=FONT_NAME, fontSize=12, textColor=colors.HexColor('#003366'), spaceAfter=2))
        styles.add(ParagraphStyle(name='CompanyAddress', parent=styles['Normal'], fontName=FONT_NAME, fontSize=9, textColor=colors.grey))
        styles.add(ParagraphStyle(name='SectionHead', parent=styles['Heading2'], fontName=FONT_NAME, fontSize=11, textColor=colors.HexColor('#003366'), spaceAfter=6))
        styles.add(ParagraphStyle(name='NormalRight', parent=styles['Normal'], alignment=TA_RIGHT, fontName=FONT_NAME))
        styles.add(ParagraphStyle(name='NormalBold', parent=styles['Normal'], fontName=FONT_NAME, bold=True))
        return styles

    def _header_footer(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#003366'))
        canvas.setLineWidth(0.8)
        canvas.line(25*mm, doc.height + 28*mm, doc.width + 25*mm, doc.height + 28*mm)
        canvas.setFont(FONT_NAME, 8)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(doc.width + 20*mm, 15*mm, f"Seite {canvas.getPageNumber()}")
        canvas.restoreState()

    def _add_logo_and_header(self):
        logo_path = Path(__file__).parent / "logo.png"
        if logo_path.exists():
            img = Image(str(logo_path), width=35*mm, height=20*mm)
            img.hAlign = 'LEFT'
            self.story.append(img)
            self.story.append(Spacer(1, 2*mm))
        company_lines = [f"<b>{self.company.get('name', '')}</b>",
                         self.company.get('address_line1', ''),
                         self.company.get('address_line2', ''),
                         f"Tel: {self.company.get('phone', '')}  |  Email: {self.company.get('email', '')}",
                         f"Web: {self.company.get('website', '')}"]
        valid_until = self.offer.get('valid_until') or (datetime.now() + timedelta(days=30)).strftime('%d.%m.%Y')
        offer_lines = [f"<b>Angebot Nr.:</b> {self.offer.get('offer_number', 'Entwurf')}",
                       f"<b>Datum:</b> {self.offer.get('date', '')}",
                       f"<b>Gültig bis:</b> {valid_until}"]
        if self.offer.get('customer_ref', '').strip():
            offer_lines.insert(2, f"<b>Ihr Zeichen:</b> {self.offer['customer_ref']}")
        header_table = Table([[Paragraph('<br/>'.join(company_lines), self.styles['CompanyAddress']),
                               Paragraph('<br/>'.join(offer_lines), self.styles['NormalRight'])]],
                             colWidths=[self.doc.width/2, self.doc.width/2])
        header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (0,0), 0), ('RIGHTPADDING', (1,0), (1,0), 0)]))
        self.story.append(header_table)
        self.story.append(Spacer(1, 6*mm))

    def _add_customer_block(self):
        cust = self.offer.get('customer', {})
        headline = "Kundendaten (Privat)" if self.offer.get('customer_type') == 'privat' else "Firmendaten"
        addr_parts = [f"<b>{cust.get('name', '')}</b>"]
        if cust.get('address', '').strip():
            addr_parts.append(cust['address'].replace('\n', '<br/>'))
        if cust.get('contact', '').strip():
            addr_parts.append(cust['contact'])
        contact_parts = [c for c in [cust.get('phone', ''), cust.get('email', '')] if c.strip()]
        if contact_parts:
            addr_parts.append('  |  '.join(contact_parts))
        self.story.append(Paragraph(headline, self.styles['SectionHead']))
        self.story.append(Paragraph('<br/>'.join(addr_parts), self.styles['Normal']))
        self.story.append(Spacer(1, 5*mm))

    def _add_title(self):
        self.story.append(Paragraph("Angebot / Leistungsübersicht", self.styles['Title']))
        self.story.append(Spacer(1, 3*mm))

    def _add_items_table(self):
        data = [["Pos.", "Beschreibung", "Menge", "Einzelpreis", "Gesamt"]]
        total_net = 0.0
        for idx, item in enumerate(self.offer.get('items', []), 1):
            qty, price = item['quantity'], item['unit_price']
            total = qty * price
            total_net += total
            qty_str = f"{qty:g}" if qty != int(qty) else str(int(qty))
            data.append([str(idx), Paragraph(item['description'], self.styles['Normal']),
                         qty_str, format_currency(price), format_currency(total)])
        data.append(["", "", "", "Zwischensumme", format_currency(total_net)])
        discount = self.offer.get('discount', 0.0)
        discount_amount = total_net * discount / 100
        if discount > 0:
            data.append(["", "", "", f"Rabatt ({discount}%)", f"- {format_currency(discount_amount)}"])
        total_net_after_discount = total_net - discount_amount
        shipping = self.offer.get('shipping', 0.0)
        if shipping > 0:
            data.append(["", "", "", "Versandkosten", format_currency(shipping)])
        total_net_after_shipping = total_net_after_discount + shipping
        tax_rate = self.offer.get('tax_rate', 19)
        tax_amount = total_net_after_shipping * tax_rate / 100
        total_gross = total_net_after_shipping + tax_amount
        data.extend([
            ["", "", "", "Nettosumme", format_currency(total_net_after_shipping)],
            ["", "", "", f"MwSt. {tax_rate}%", format_currency(tax_amount)],
            ["", "", "", "Gesamtbetrag (brutto)", format_currency(total_gross)]
        ])
        col_widths = [12*mm, 80*mm, 18*mm, 35*mm, 35*mm]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), FONT_NAME),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1, -5), 0.5, colors.lightgrey),
            ('LINEBELOW', (0, -5), (-1, -5), 1, colors.black),
            ('ALIGN', (2,1), (2,-5), 'CENTER'),
            ('ALIGN', (3,1), (4,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1, -5), [colors.white, colors.HexColor('#f5f5f5')]),
            ('BACKGROUND', (0,-5), (-1,-1), colors.HexColor('#e6f0fa')),
            ('FONTNAME', (0,-5), (-1,-1), FONT_NAME),
            ('FONTSIZE', (0,-5), (-1,-1), 9),
        ])
        if discount > 0:
            row_idx = -7 if shipping > 0 else -6
            style.add('TEXTCOLOR', (0, row_idx), (-1, row_idx), colors.red)
        table.setStyle(style)
        self.story.append(table)
        self.story.append(Spacer(1, 6*mm))

    def _add_personal_message(self):
        msg = self.offer.get('personal_message', '').strip()
        if msg:
            self.story.append(Paragraph("Ihre Nachricht an uns", self.styles['SectionHead']))
            self.story.append(Paragraph(msg.replace('\n', '<br/>'), self.styles['Normal']))
            self.story.append(Spacer(1, 5*mm))

    def _add_terms(self):
        terms = self.offer.get('terms', '').strip()
        if terms:
            self.story.append(Paragraph("Liefer- und Zahlungsbedingungen", self.styles['SectionHead']))
            for line in terms.split('\n'):
                if line.strip():
                    self.story.append(Paragraph(f"• {line}", self.styles['Normal']))
            self.story.append(Spacer(1, 5*mm))

    def _add_signature_stamp(self):
        sig_data = [["Ort, Datum: _________________", "Unterschrift: _________________"],
                    ["", "Stempel / rechtsverbindlich"]]
        sig_table = Table(sig_data, colWidths=[self.doc.width/2, self.doc.width/2])
        sig_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
            ('TOPPADDING', (0,0), (-1,-1), 10),
        ]))
        self.story.append(sig_table)

    def build(self):
        self._add_logo_and_header()
        self._add_customer_block()
        self._add_title()
        self._add_items_table()
        self._add_personal_message()
        self._add_terms()
        self._add_signature_stamp()
        self.doc.build(self.story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)

# ------------------------------------------------------------
#  E-Mail Sender und Rechner
# ------------------------------------------------------------
class EmailSender:
    @staticmethod
    def send_email(smtp_server, smtp_port, smtp_user, smtp_password,
                   to_addr, subject, body, attachment_path=None):
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_addr
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        if attachment_path and Path(attachment_path).exists():
            with open(attachment_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{Path(attachment_path).name}"')
                msg.attach(part)
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            return True, "E-Mail erfolgreich gesendet."
        except Exception as e:
            return False, f"Fehler: {str(e)}"

class GrossNetCalculatorDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Brutto-Netto-Rechner")
        self.geometry("400x250")
        self.resizable(False, False)
        self.configure(bg=COLORS['bg'])
        self.create_widgets()
        self.bind('<Return>', self.calc)
        self.bind('<Escape>', lambda e: self.destroy())
    def create_widgets(self):
        main = ttk.Frame(self, padding=15)
        main.pack(fill='both', expand=True)
        ttk.Label(main, text="Betrag (Netto):").grid(row=0, column=0, sticky='w', pady=5)
        self.net_entry = ttk.Entry(main, width=15)
        self.net_entry.grid(row=0, column=1, padx=10, pady=5)
        ttk.Label(main, text="MwSt.-Satz (%):").grid(row=1, column=0, sticky='w', pady=5)
        self.tax_var = tk.IntVar(value=19)
        ttk.Spinbox(main, from_=0, to=25, textvariable=self.tax_var, width=13).grid(row=1, column=1, padx=10, pady=5)
        ttk.Button(main, text="Berechnen", command=self.calc).grid(row=2, column=0, columnspan=2, pady=10)
        self.result_label = ttk.Label(main, text="", font=('Segoe UI', 10, 'bold'))
        self.result_label.grid(row=3, column=0, columnspan=2, pady=5)
        ttk.Label(main, text="Betrag (Brutto):").grid(row=4, column=0, sticky='w', pady=5)
        self.gross_entry = ttk.Entry(main, width=15)
        self.gross_entry.grid(row=4, column=1, padx=10, pady=5)
        ttk.Button(main, text="Berechnen (Brutto→Netto)", command=self.calc_reverse).grid(row=5, column=0, columnspan=2, pady=5)
    def calc(self, event=None):
        try:
            net = float(self.net_entry.get().replace(',', '.'))
            tax = self.tax_var.get()
            gross = net * (1 + tax/100)
            self.result_label.config(text=f"Brutto: {format_currency(gross)}")
        except:
            messagebox.showerror("Fehler", "Bitte gültigen Nettobetrag eingeben.")
    def calc_reverse(self, event=None):
        try:
            gross = float(self.gross_entry.get().replace(',', '.'))
            tax = self.tax_var.get()
            net = gross / (1 + tax/100)
            self.result_label.config(text=f"Netto: {format_currency(net)}")
        except:
            messagebox.showerror("Fehler", "Bitte gültigen Bruttobetrag eingeben.")

# ------------------------------------------------------------
#  Benutzerverwaltungs-Dialog (nur für Admin)
# ------------------------------------------------------------
class UserManagementDialog(tk.Toplevel):
    def __init__(self, parent, user_db):
        super().__init__(parent)
        self.user_db = user_db
        self.title("Benutzerverwaltung")
        self.geometry("600x400")
        self.configure(bg=COLORS['bg'])
        self.create_widgets()
        self.refresh_list()
        self.grab_set()
        self.transient(parent)
        self.bind('<Escape>', lambda e: self.destroy())

    def create_widgets(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill='both', expand=True)
        toolbar = ttk.Frame(main)
        toolbar.pack(fill='x', pady=5)
        ttk.Button(toolbar, text="Neuer Benutzer", command=self.add_user).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Passwort ändern", command=self.change_password).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Benutzer löschen", command=self.delete_user).pack(side='left', padx=2)
        self.tree = ttk.Treeview(main, columns=("username", "role", "created"), show='headings')
        self.tree.heading("username", text="Benutzername")
        self.tree.heading("role", text="Rolle")
        self.tree.heading("created", text="Erstellt am")
        self.tree.pack(fill='both', expand=True)

    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for u in self.user_db.get_all_users():
            self.tree.insert("", "end", values=(u["username"], u["role"], u["created"]))

    def add_user(self):
        win = tk.Toplevel(self)
        win.title("Neuer Benutzer")
        win.geometry("350x250")
        win.transient(self)
        win.grab_set()
        ttk.Label(win, text="Benutzername:").pack(pady=5)
        user_var = tk.StringVar()
        ttk.Entry(win, textvariable=user_var).pack()
        ttk.Label(win, text="Passwort:").pack(pady=5)
        pass_var = tk.StringVar()
        ttk.Entry(win, textvariable=pass_var, show="*").pack()
        ttk.Label(win, text="Rolle:").pack(pady=5)
        role_var = tk.StringVar(value="user")
        ttk.Combobox(win, textvariable=role_var, values=["user", "admin"], state="readonly").pack()
        def save():
            username = user_var.get().strip()
            password = pass_var.get()
            role = role_var.get()
            if not username or not password:
                messagebox.showerror("Fehler", "Benutzername und Passwort erforderlich.")
                return
            if self.user_db.add_user(username, password, role):
                self.refresh_list()
                win.destroy()
            else:
                messagebox.showerror("Fehler", "Benutzername existiert bereits.")
        ttk.Button(win, text="Speichern", command=save).pack(pady=15)
        win.bind('<Return>', lambda e: save())
        win.bind('<Escape>', lambda e: win.destroy())

    def change_password(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Bitte Benutzer auswählen.")
            return
        username = self.tree.item(sel[0], "values")[0]
        new_pass = simpledialog.askstring("Passwort ändern", f"Neues Passwort für {username}:", show="*")
        if new_pass:
            self.user_db.change_password(username, new_pass)
            messagebox.showinfo("Erfolg", "Passwort geändert.")

    def delete_user(self):
        sel = self.tree.selection()
        if not sel:
            return
        username = self.tree.item(sel[0], "values")[0]
        if username == "admin":
            messagebox.showerror("Fehler", "Admin kann nicht gelöscht werden.")
            return
        if messagebox.askyesno("Löschen", f"Benutzer '{username}' wirklich löschen?"):
            self.user_db.delete_user(username)
            self.refresh_list()

# ------------------------------------------------------------
#  Fortschrittsdialog
# ------------------------------------------------------------
class ProgressDialog(tk.Toplevel):
    def __init__(self, parent, title="Bitte warten..."):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x100")
        self.resizable(False, False)
        self.configure(bg=COLORS['bg'])
        self.transient(parent)
        self.grab_set()
        ttk.Label(self, text=title, font=('Segoe UI', 10)).pack(pady=20)
        self.progress = ttk.Progressbar(self, mode='indeterminate')
        self.progress.pack(fill='x', padx=20, pady=10)
        self.progress.start(10)
        self.bind('<Escape>', lambda e: None)

    def close(self):
        self.progress.stop()
        self.destroy()

# ------------------------------------------------------------
#  Tooltip-Klasse
# ------------------------------------------------------------
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0,0,0,0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tip, text=self.text, background="#1E2A3A",
                         foreground="white", font=('Segoe UI', 9),
                         padx=8, pady=4, relief='flat')
        label.pack()

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

# ------------------------------------------------------------
#  Datenbank-Konfigurationsdialog (für MySQL)
# ------------------------------------------------------------
class DatabaseConfigDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("MySQL-Datenbank einrichten")
        self.geometry("500x350")
        self.configure(bg=COLORS['bg'])
        self.transient(parent)
        self.grab_set()
        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        main = ttk.Frame(self, padding=20)
        main.pack(fill='both', expand=True)
        ttk.Label(main, text="MySQL-Verbindungsdaten", font=('Segoe UI', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        fields = [("Host:", "host"), ("Port:", "port"), ("Benutzername:", "user"), ("Passwort:", "password"), ("Datenbankname:", "database")]
        self.entries = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(main, text=label).grid(row=i+1, column=0, sticky='w', pady=5)
            entry = ttk.Entry(main, width=30, show="*" if key == "password" else "")
            entry.grid(row=i+1, column=1, padx=10, pady=5)
            self.entries[key] = entry
        ttk.Label(main, text="Hinweis: Die Tabelle wird automatisch erstellt.").grid(row=6, column=0, columnspan=2, pady=10)
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Testverbindung", command=self.test_connection).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Speichern", command=self.save_config, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Abbrechen", command=self.destroy).pack(side='left', padx=5)

    def load_config(self):
        cfg = DatabaseConfig()
        config = cfg.get_mysql_config()
        if config:
            self.entries["host"].insert(0, config.get("host", ""))
            self.entries["port"].insert(0, str(config.get("port", "3306")))
            self.entries["user"].insert(0, config.get("user", ""))
            self.entries["password"].insert(0, config.get("password", ""))
            self.entries["database"].insert(0, config.get("database", ""))

    def test_connection(self):
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=self.entries["host"].get(),
                port=int(self.entries["port"].get()) if self.entries["port"].get() else 3306,
                user=self.entries["user"].get(),
                password=self.entries["password"].get(),
                database=self.entries["database"].get()
            )
            conn.close()
            messagebox.showinfo("Erfolg", "Verbindung erfolgreich!")
        except Exception as e:
            messagebox.showerror("Fehler", f"Verbindung fehlgeschlagen:\n{e}")

    def save_config(self):
        host = self.entries["host"].get().strip()
        port = int(self.entries["port"].get()) if self.entries["port"].get() else 3306
        user = self.entries["user"].get().strip()
        password = self.entries["password"].get()
        database = self.entries["database"].get().strip()
        if not all([host, user, database]):
            messagebox.showerror("Fehler", "Bitte Host, Benutzername und Datenbankname angeben.")
            return
        cfg = DatabaseConfig()
        cfg.set_mysql_config(host, port, user, password, database)
        # Neuen DatabaseManager initialisieren
        DatabaseManager._instance = None
        try:
            db = DatabaseManager()
            if not db.use_mysql:
                messagebox.showerror("Fehler", "MySQL-Verbindung konnte nicht hergestellt werden. Bitte prüfen Sie die Daten.")
                cfg.clear_mysql_config()
                return
            messagebox.showinfo("Erfolg", "MySQL-Konfiguration gespeichert und verbunden. Starten Sie das Programm neu, um die Datenbank zu verwenden.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler bei der Verbindung: {e}")
            cfg.clear_mysql_config()

# ------------------------------------------------------------
#  Haupt-GUI (mit integriertem Login-Frame)
# ------------------------------------------------------------
class EnterpriseAngebotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📋 Angebotsmanager PRO")
        self.root.geometry("1400x900")
        self.root.minsize(1100, 700)
        self.root.configure(bg=COLORS['bg'])
        
        self.current_user = None
        self.is_admin = False
        
        # Datenbanken initialisieren (SQLite oder MySQL)
        self.user_db = UserDatabase()
        self.company_db = CompanyDatabase()
        self.template_db = TemplateDatabase()
        
        self._setup_styles()
        self._show_login_frame()
        
        # Undo/Redo Manager (wird nach Login initialisiert)
        self.undo_redo = None
        self._save_state_for_undo = self._dummy_save
        
        # Automatisches tägliches Backup
        self._check_auto_backup()
    
    def _dummy_save(self):
        pass

    def _real_save_state_for_undo(self):
        if hasattr(self, 'current_offer') and self.undo_redo:
            self.undo_redo.push(copy.deepcopy(self.current_offer))

    def undo_action(self, event=None):
        if not self.undo_redo or not self.undo_redo.can_undo():
            self._set_status("Keine weiteren Undo-Schritte möglich")
            return
        prev_state = self.undo_redo.undo()
        if prev_state:
            self.current_offer = copy.deepcopy(prev_state)
            self.sync_data_to_ui()
            self._set_status("Rückgängig gemacht")

    def redo_action(self, event=None):
        self._set_status("Redo derzeit nicht implementiert")

    # --------------------------------------------------------
    #  Tastaturbedienung für Positionen und Angebote
    # --------------------------------------------------------
    def _bind_treeview_keys(self):
        self.tree.bind('<Delete>', lambda e: self.delete_item())
        self.tree.bind('<Insert>', lambda e: self.add_item())
        self.tree.bind('<Return>', lambda e: self.edit_item())
    
    def _bind_offers_tree_keys(self):
        self.offer_tree.bind('<Delete>', lambda e: self.delete_selected_offer())
        self.offer_tree.bind('<Return>', lambda e: self.load_selected_offer())
    
    # --------------------------------------------------------
    #  UI-Styles
    # --------------------------------------------------------
    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use('clam')
        s.configure('.', background=COLORS['bg'], font=('Segoe UI', 10))
        s.configure('TNotebook', background=COLORS['bg'], borderwidth=0)
        s.configure('TNotebook.Tab', font=('Segoe UI', 10, 'bold'), padding=[24, 10])
        s.map('TNotebook.Tab',
              background=[('selected', COLORS['card']), ('active', COLORS['row_alt'])],
              foreground=[('selected', COLORS['accent']), ('active', COLORS['text_main'])])
        s.configure('TLabelframe', background=COLORS['card'], bordercolor=COLORS['border'],
                    relief='solid', borderwidth=1, padding=12)
        s.configure('TLabelframe.Label', font=('Segoe UI', 10, 'bold'),
                    foreground=COLORS['accent'], background=COLORS['card'])
        s.configure('TButton', font=('Segoe UI', 10), padding=8, relief='flat')
        s.map('TButton',
              background=[('active', COLORS['accent_hover'])],
              foreground=[('active', 'white')])
        s.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'), padding=8,
                    relief='flat', background=COLORS['accent'], foreground='white')
        s.map('Accent.TButton',
              background=[('active', COLORS['accent_hover'])])
        s.configure('Neutral.TButton', font=('Segoe UI', 9, 'bold'), padding=6,
                    relief='flat', background='#374151', foreground='white')
        s.map('Neutral.TButton',
              background=[('active', '#4B5563')])
        s.configure('Treeview', font=('Segoe UI', 10), rowheight=32,
                    background='white', fieldbackground='white')
        s.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'),
                    background=COLORS['header_bg'], foreground='white', relief='flat')
        s.map('Treeview.Heading', background=[('active', COLORS['accent'])])
        s.configure('TEntry', font=('Segoe UI', 10), padding=6, fieldbackground='white')
        s.configure('TCombobox', font=('Segoe UI', 10), padding=6)
        s.configure('TSeparator', background=COLORS['border'])
    
    def _check_auto_backup(self):
        backup_dir = get_data_dir() / "backups"
        backup_dir.mkdir(exist_ok=True)
        last_backup_file = backup_dir / ".last_backup.txt"
        today = datetime.now().strftime("%Y%m%d")
        if last_backup_file.exists():
            last = last_backup_file.read_text().strip()
            if last == today:
                return
        def do_backup():
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = backup_dir / f"auto_backup_{timestamp}.zip"
                with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    if LOCAL_SQLITE_PATH.exists():
                        zipf.write(LOCAL_SQLITE_PATH, arcname="enterprise_local.db")
                    if DB_CONFIG_PATH.exists():
                        zipf.write(DB_CONFIG_PATH, arcname="db_config.json")
                    versions_dir = get_data_dir() / "versions"
                    if versions_dir.exists():
                        for vf in versions_dir.glob("*.json"):
                            zipf.write(vf, arcname=f"versions/{vf.name}")
                with open(last_backup_file, 'w') as f:
                    f.write(today)
            except Exception as e:
                logging.error(f"Auto-Backup fehlgeschlagen: {e}")
        threading.Thread(target=do_backup, daemon=True).start()
    
    def _show_login_frame(self):
        self.login_frame = ttk.Frame(self.root, padding=40)
        self.login_frame.pack(fill='both', expand=True)
        ttk.Label(self.login_frame, text="Angebotsmanager PRO", font=('Segoe UI', 18, 'bold')).pack(pady=(0,30))
        ttk.Label(self.login_frame, text="Benutzername:").pack(anchor='w', pady=(10,0))
        self.username_entry = ttk.Entry(self.login_frame, width=30, font=('Segoe UI', 11))
        self.username_entry.pack(fill='x', pady=5)
        ttk.Label(self.login_frame, text="Passwort:").pack(anchor='w', pady=(10,0))
        self.password_entry = ttk.Entry(self.login_frame, width=30, show="*", font=('Segoe UI', 11))
        self.password_entry.pack(fill='x', pady=5)
        self.login_button = ttk.Button(self.login_frame, text="Anmelden", command=self._do_login, style='Accent.TButton')
        self.login_button.pack(pady=20)
        self.login_error = ttk.Label(self.login_frame, text="", foreground=COLORS['danger'])
        self.login_error.pack()
        self.username_entry.focus()
        self.root.bind('<Return>', lambda e: self._do_login())
    
    def _do_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        user = self.user_db.verify_user(username, password)
        if user:
            self.current_user = user["username"]
            self.is_admin = (user["role"] == "admin")
            self.login_frame.destroy()
            self.root.unbind('<Return>')
            self.product_db = ProductDatabase()
            self.customer_db = CustomerDatabase()
            self.offer_db = OfferDatabase()
            self.current_offer = self._get_empty_offer()
            self.drag_start_index = None
            self.current_customers = []
            self.current_products = []
            # Undo/Redo initialisieren
            from collections import deque
            class SimpleUndoRedo:
                def __init__(self, max_stack=50):
                    self.undo_stack = []
                    self.max_stack = max_stack
                def push(self, state):
                    self.undo_stack.append(copy.deepcopy(state))
                    if len(self.undo_stack) > self.max_stack:
                        self.undo_stack.pop(0)
                def undo(self):
                    if not self.undo_stack:
                        return None
                    return self.undo_stack.pop()
                def can_undo(self):
                    return len(self.undo_stack) > 0
            self.undo_redo = SimpleUndoRedo()
            self._save_state_for_undo = self._real_save_state_for_undo
            self._build_ui()
            self.sync_data_to_ui()
            self.update_items_table()
            self.refresh_dashboard()
            self.refresh_offer_list()
            self.refresh_customer_list()
            self.refresh_product_list()
            self._bind_shortcuts()
            self._save_state_for_undo()
            self.root.title(f"📋 Angebotsmanager PRO - Angemeldet als {self.current_user} ({'Admin' if self.is_admin else 'User'})")
        else:
            self.login_error.config(text="Ungültiger Benutzername oder Passwort")
    
    # --------------------------------------------------------
    #  Basismethoden
    # --------------------------------------------------------
    def _get_empty_offer(self):
        company = self.company_db.get_company()
        return {
            "offer_number": self._generate_offer_number(),
            "date": datetime.now().strftime("%d.%m.%Y"),
            "valid_until": (datetime.now() + timedelta(days=30)).strftime("%d.%m.%Y"),
            "customer_ref": "",
            "customer_type": "gewerblich",
            "customer": {"name": "", "address": "", "contact": "", "phone": "", "email": ""},
            "items": [],
            "tax_rate": 19,
            "discount": 0.0,
            "shipping": 0.0,
            "personal_message": "",
            "terms": self.template_db.get_template("Standard (Gewerbe)"),
            "status": "Entwurf"
        }

    def _generate_offer_number(self) -> str:
        company = self.company_db.get_company()
        prefix = company.get("offer_number_prefix", "A")
        counter = company.get("offer_number_counter", 1)
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        new_number = f"{prefix}-{year}-{month}-{counter:04d}"
        company["offer_number_counter"] = counter + 1
        self.company_db.update_company(company)
        return new_number

    # --------------------------------------------------------
    #  UI Aufbau (nach Login)
    # --------------------------------------------------------
    def _build_ui(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Extras", menu=tools_menu)
        tools_menu.add_command(label="Dunkelmodus umschalten", command=self._toggle_theme)
        tools_menu.add_separator()
        tools_menu.add_command(label="Angebote als CSV exportieren", command=self.export_offers_to_csv)
        tools_menu.add_command(label="Aktuelles Angebot drucken", command=self.print_offer)
        if self.is_admin:
            tools_menu.add_separator()
            tools_menu.add_command(label="MySQL-Datenbank einrichten", command=self.open_db_config)
        
        header = tk.Frame(self.root, bg=COLORS['header_bg'], height=56)
        header.pack(fill='x', side='top')
        tk.Label(header, text="📋  Angebotsmanager PRO", font=('Segoe UI', 14, 'bold'), bg=COLORS['header_bg'], fg='white').pack(side='left', padx=20, pady=12)
        btn_container = tk.Frame(header, bg=COLORS['header_bg'])
        btn_container.pack(side='right', padx=12, pady=8)
        admin_buttons = []
        if self.is_admin:
            admin_buttons = [("👥 Benutzer", self.open_user_management, "#374151")]
        for txt, cmd, bg_color in [("🆕  Neu", self._new_offer, "#374151"),
                                    ("📂  Laden", self.load_offer, "#374151"),
                                    ("💾  Speichern", self.save_offer, COLORS['accent']),
                                    ("📄  PDF erstellen", self.generate_pdf, COLORS['btn_pdf']),
                                    ("✉️  PDF per Mail", self.send_email_dialog, "#D97706"),
                                    ("🧮  Rechner", self.open_calculator, "#374151"),
                                    ("💾 Backup", self.backup_database, "#374151"),
                                    ("🔄 Wiederherstellen", self.restore_database, "#374151")] + admin_buttons:
            if bg_color == COLORS['accent']:
                style = 'Accent.TButton'
            elif bg_color == '#374151':
                style = 'Neutral.TButton'
            else:
                style = 'TButton'
            btn = ttk.Button(btn_container, text=txt, command=cmd, style=style)
            btn.pack(side='left', padx=3)
            if txt == "💾 Backup":
                Tooltip(btn, "Erstellt ein ZIP-Backup aller Datenbanken")
            elif txt == "🔄 Wiederherstellen":
                Tooltip(btn, "Stellt ein Backup wieder her")
            elif txt == "✉️  PDF per Mail":
                Tooltip(btn, "Sendet das aktuelle Angebot als PDF an den Kunden")
            elif txt == "📄  PDF erstellen":
                Tooltip(btn, "Erzeugt ein professionelles PDF-Angebot")
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        tab1 = ttk.Frame(self.notebook)
        self.notebook.add(tab1, text="   📄  Angebot & Kunde   ")
        self._build_tab_offer(tab1)
        
        tab2 = ttk.Frame(self.notebook)
        self.notebook.add(tab2, text="   📦  Positionen & Bibliothek   ")
        self._build_tab_items(tab2)
        
        tab3 = ttk.Frame(self.notebook)
        self.notebook.add(tab3, text="   👥  Kunden-Datenbank   ")
        self._build_tab_customers(tab3)
        
        tab4 = ttk.Frame(self.notebook)
        self.notebook.add(tab4, text="   📊  Angebote & Status   ")
        self._build_tab_offers(tab4)
        
        tab5 = ttk.Frame(self.notebook)
        self.notebook.add(tab5, text="   📈  Dashboard   ")
        self._build_tab_dashboard(tab5)
        
        tab6 = ttk.Frame(self.notebook)
        self.notebook.add(tab6, text="   🏢  Meine Firma   ")
        self._build_tab_company(tab6)
        
        self.status_var = tk.StringVar(value="Bereit.")
        self.total_label_var = tk.StringVar()
        status_bar = tk.Frame(self.root, bg=COLORS['header_bg'], height=32)
        status_bar.pack(fill='x', side='bottom')
        ttk.Separator(status_bar, orient='horizontal').pack(fill='x')
        inner = tk.Frame(status_bar, bg=COLORS['header_bg'])
        inner.pack(fill='both', expand=True, padx=14, pady=4)
        tk.Label(inner, textvariable=self.status_var, font=('Segoe UI', 9),
                 bg=COLORS['header_bg'], fg='#94A3B8').pack(side='left')
        tk.Label(inner, textvariable=self.total_label_var, font=('Segoe UI', 9, 'bold'),
                 bg=COLORS['header_bg'], fg='#86EFAC').pack(side='right')
    
    def open_db_config(self):
        DatabaseConfigDialog(self.root)
    
    def _toggle_theme(self):
        global COLORS
        if COLORS is LIGHT_COLORS:
            COLORS.update(DARK_COLORS)
        else:
            COLORS.update(LIGHT_COLORS)
        self._setup_styles()
        for widget in self.root.winfo_children():
            if widget not in (self.notebook, self.root.winfo_children()[0]):
                widget.destroy()
        self._build_ui()
        self.refresh_offer_list()
        self.refresh_customer_list()
        self.refresh_product_list()
        self.refresh_dashboard()
        self.sync_data_to_ui()
    
    def _bind_shortcuts(self):
        self.root.bind('<Control-n>', lambda e: self._new_offer())
        self.root.bind('<Control-s>', lambda e: self.save_offer())
        self.root.bind('<Control-e>', lambda e: self.generate_pdf())
        self.root.bind('<Control-Shift-M>', lambda e: self.send_email_dialog())
        self.root.bind('<Control-b>', lambda e: self.backup_database())
        self.root.bind('<Control-r>', lambda e: self.restore_database())
        self.root.bind('<Control-z>', self.undo_action)
        self.root.bind('<Control-y>', self.redo_action)
        self.root.bind('<Control-Shift-Z>', self.redo_action)
    
    def open_user_management(self):
        UserManagementDialog(self.root, self.user_db)
    
    def export_offers_to_csv(self):
        if not hasattr(self, 'offer_tree'):
            messagebox.showinfo("Info", "Bitte warten, bis die Angebotsliste geladen ist.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Angebots-Nr.", "Datum", "Kunde", "Netto", "Status", "Besitzer"])
                    for child in self.offer_tree.get_children():
                        values = self.offer_tree.item(child, "values")
                        writer.writerow(values)
                messagebox.showinfo("Export", f"CSV erfolgreich exportiert nach {path}")
            except Exception as e:
                messagebox.showerror("Fehler", f"Export fehlgeschlagen: {e}")
    
    def print_offer(self):
        if not self.current_offer['items']:
            messagebox.showwarning("Fehler", "Keine Positionen zum Drucken vorhanden.")
            return
        fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        company = self.company_db.get_company()
        gen = EnterprisePDFGenerator(self.current_offer, company, pdf_path)
        gen.build()
        try:
            os.startfile(pdf_path, "print")
        except:
            os.startfile(pdf_path)
        finally:
            self.root.after(30000, lambda: Path(pdf_path).unlink(missing_ok=True))
    
    # --------------------------------------------------------
    #  Tab: Angebot & Kunde (wie gehabt, aber mit Undo)
    # --------------------------------------------------------
    def _build_tab_offer(self, parent):
        canvas = tk.Canvas(parent, bg=COLORS['bg'], highlightthickness=0)
        vsb = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor='nw')
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        
        fg = ttk.LabelFrame(scrollable, text="  📋  Angebotsdaten  ", padding=12)
        fg.pack(fill='x', padx=20, pady=15)
        self.offer_number_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.valid_var = tk.StringVar()
        self.customer_ref_var = tk.StringVar()
        self.customer_type_var = tk.StringVar(value="gewerblich")
        self._field(fg, "Angebots-Nr.:", 0, 0, 20, self.offer_number_var)
        self._field(fg, "Datum:", 0, 1, 14, self.date_var)
        self._field(fg, "Gültig bis:", 0, 2, 14, self.valid_var)
        self._field(fg, "Ihr Zeichen:", 1, 0, 20, self.customer_ref_var)
        ttk.Label(fg, text="Kundentyp:").grid(row=1, column=2, sticky='w', pady=4)
        type_cb = ttk.Combobox(fg, textvariable=self.customer_type_var, values=["gewerblich", "privat"], state="readonly", width=16)
        type_cb.grid(row=1, column=3, sticky='w', padx=(0,16))
        type_cb.bind("<<ComboboxSelected>>", self.on_customer_type_changed)
        
        ttk.Separator(scrollable, orient='horizontal').pack(fill='x', padx=20, pady=10)
        
        fc = ttk.LabelFrame(scrollable, text="  👤  Kundendaten  ", padding=12)
        fc.pack(fill='x', padx=20, pady=15)
        self.cust_name = tk.StringVar()
        self.cust_addr = tk.StringVar()
        self.cust_contact = tk.StringVar()
        self.cust_phone = tk.StringVar()
        self.cust_email = tk.StringVar()
        self.kunden_label = ttk.Label(fc, text="Firma / Person:")
        self.kunden_label.grid(row=0, column=0, sticky='w', pady=4)
        ttk.Entry(fc, textvariable=self.cust_name, width=38).grid(row=0, column=1, columnspan=3, sticky='ew')
        btn = ttk.Button(fc, text="📖 Kunde aus DB", command=self.select_customer_from_db)
        btn.grid(row=0, column=4, padx=5)
        Tooltip(btn, "Kunden aus der Datenbank auswählen")
        ttk.Label(fc, text="Adresse:").grid(row=1, column=0, sticky='w', pady=4)
        ttk.Entry(fc, textvariable=self.cust_addr, width=50).grid(row=1, column=1, columnspan=3, sticky='ew')
        self.contact_label = ttk.Label(fc, text="Kontaktperson:")
        self.contact_label.grid(row=2, column=0, sticky='w', pady=4)
        ttk.Entry(fc, textvariable=self.cust_contact, width=25).grid(row=2, column=1, sticky='ew')
        ttk.Label(fc, text="Telefon:").grid(row=2, column=2, sticky='w', padx=(16,6))
        ttk.Entry(fc, textvariable=self.cust_phone, width=20).grid(row=2, column=3, sticky='ew')
        ttk.Label(fc, text="E-Mail:").grid(row=3, column=0, sticky='w', pady=4)
        ttk.Entry(fc, textvariable=self.cust_email, width=38).grid(row=3, column=1, columnspan=3, sticky='ew')
        
        for var in [self.cust_name, self.cust_addr, self.cust_contact, self.cust_phone, self.cust_email]:
            var.trace('w', lambda *a: self._on_customer_data_changed())
        
        ttk.Separator(scrollable, orient='horizontal').pack(fill='x', padx=20, pady=10)
        
        ffi = ttk.LabelFrame(scrollable, text="  💰  Finanzen & Bedingungen  ", padding=12)
        ffi.pack(fill='x', padx=20, pady=15)
        self.tax_var = tk.IntVar(value=19)
        self.discount_var = tk.DoubleVar(value=0.0)
        self.shipping_var = tk.DoubleVar(value=0.0)
        ttk.Label(ffi, text="MwSt %:").grid(row=0, column=0)
        tax_spin = ttk.Spinbox(ffi, from_=0, to=25, textvariable=self.tax_var, width=6)
        tax_spin.grid(row=0, column=1, padx=10)
        ttk.Label(ffi, text="Rabatt %:").grid(row=0, column=2)
        disc_spin = ttk.Spinbox(ffi, from_=0, to=100, textvariable=self.discount_var, width=6)
        disc_spin.grid(row=0, column=3, padx=10)
        ttk.Label(ffi, text="Versand €:").grid(row=0, column=4)
        ship_entry = ttk.Entry(ffi, textvariable=self.shipping_var, width=10)
        ship_entry.grid(row=0, column=5, padx=10)
        
        self.tax_var.trace('w', lambda *a: self._on_finance_changed())
        self.discount_var.trace('w', lambda *a: self._on_finance_changed())
        self.shipping_var.trace('w', lambda *a: self._on_finance_changed())
        
        self.personal_msg = tk.Text(ffi, height=3, width=80, font=('Segoe UI', 10), bd=1, relief='solid')
        self.personal_msg.grid(row=1, column=0, columnspan=6, pady=10)
        self.personal_msg.bind('<KeyRelease>', lambda e: self._on_text_changed())
        
        self.terms_text = tk.Text(ffi, height=5, width=80, font=('Segoe UI', 10), bd=1, relief='solid')
        self.terms_text.grid(row=2, column=0, columnspan=6, pady=5)
        self.terms_text.bind('<KeyRelease>', lambda e: self._on_text_changed())
        
        self.template_var = tk.StringVar()
        tmpl_cb = ttk.Combobox(ffi, textvariable=self.template_var, values=[t["name"] for t in self.template_db.get_all()], state="readonly")
        tmpl_cb.grid(row=3, column=1, columnspan=2, sticky='w')
        tmpl_cb.bind("<<ComboboxSelected>>", self.load_text_template)
    
    def _field(self, parent, label, row, col, width, var):
        ttk.Label(parent, text=label).grid(row=row, column=col*2, sticky='w', padx=(0,6), pady=4)
        e = ttk.Entry(parent, textvariable=var, width=width)
        e.grid(row=row, column=col*2+1, sticky='w', padx=(0,16))
        return e
    
    def _on_customer_data_changed(self):
        self._save_state_for_undo()
        self.sync_ui_to_data()
        self.update_items_table()
    
    def _on_finance_changed(self):
        self._save_state_for_undo()
        self.sync_ui_to_data()
        self.update_items_table()
    
    def _on_text_changed(self):
        self._save_state_for_undo()
        self.sync_ui_to_data()
        self.update_items_table()
    
    def select_customer_from_db(self):
        customers = self.customer_db.get_all()
        if not customers:
            messagebox.showinfo("Info", "Keine Kunden in der Datenbank.")
            return
        win = tk.Toplevel(self.root)
        win.title("Kunde auswählen")
        win.geometry("500x400")
        win.transient(self.root)
        win.grab_set()
        tree = ttk.Treeview(win, columns=("name", "address", "contact"), show="headings")
        tree.heading("name", text="Name/Firma")
        tree.heading("address", text="Adresse")
        tree.heading("contact", text="Kontakt")
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        for cust in customers:
            tree.insert("", "end", iid=str(cust["id"]), values=(cust.get("name"), cust.get("address"), cust.get("contact")))
        def on_select():
            sel = tree.selection()
            if sel:
                cust_id = int(sel[0])
                for cust in customers:
                    if cust["id"] == cust_id:
                        self._save_state_for_undo()
                        self.cust_name.set(cust.get("name", ""))
                        self.cust_addr.set(cust.get("address", ""))
                        self.cust_contact.set(cust.get("contact", ""))
                        self.cust_phone.set(cust.get("phone", ""))
                        self.cust_email.set(cust.get("email", ""))
                        self.customer_type_var.set(cust.get("customer_type", "gewerblich"))
                        win.destroy()
                        break
        ttk.Button(win, text="Übernehmen", command=on_select).pack(pady=5)
        win.bind('<Return>', lambda e: on_select())
        win.bind('<Escape>', lambda e: win.destroy())
    
    def on_customer_type_changed(self, e=None):
        if self.customer_type_var.get() == "privat":
            self.kunden_label.config(text="Name des Kunden:")
            self.contact_label.config(text="Vorname / Zusatz:")
        else:
            self.kunden_label.config(text="Firmenname:")
            self.contact_label.config(text="Kontaktperson:")
        self._on_customer_data_changed()
    
    def load_text_template(self, e=None):
        name = self.template_var.get()
        text = self.template_db.get_template(name)
        self._save_state_for_undo()
        self.terms_text.delete("1.0", tk.END)
        self.terms_text.insert("1.0", text)
    
    # --------------------------------------------------------
    #  Tab: Positionen & Bibliothek (wie gehabt)
    # --------------------------------------------------------
    def _build_tab_items(self, parent):
        pw = tk.PanedWindow(parent, orient='horizontal', bg=COLORS['border'], sashwidth=4)
        pw.pack(fill='both', expand=True, padx=10, pady=10)
        lib_side = ttk.Frame(pw, padding=10)
        pw.add(lib_side, width=400)
        ttk.Label(lib_side, text="📦 Artikel-Bibliothek (Vorlagen)", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        search_frame = ttk.Frame(lib_side)
        search_frame.pack(fill='x', pady=5)
        ttk.Label(search_frame, text="Suche:").pack(side='left')
        self.lib_search_var = tk.StringVar()
        self.lib_search_var.trace('w', lambda *a: self.refresh_product_list())
        ttk.Entry(search_frame, textvariable=self.lib_search_var).pack(side='left', fill='x', expand=True, padx=5)
        self.lib_tree = ttk.Treeview(lib_side, columns=("Preis"), show='tree headings')
        self.lib_tree.heading("#0", text="Artikelbezeichnung")
        self.lib_tree.heading("Preis", text="Einzelpreis")
        self.lib_tree.column("Preis", width=90, anchor='e')
        self.lib_tree.pack(fill='both', expand=True, pady=5)
        lib_btn_f = ttk.Frame(lib_side)
        lib_btn_f.pack(fill='x')
        btn1 = ttk.Button(lib_btn_f, text="In Angebot übernehmen", command=self.add_from_library)
        btn1.pack(fill='x', pady=2)
        Tooltip(btn1, "Den ausgewählten Artikel in die Positionsliste übernehmen")
        btn2 = ttk.Button(lib_btn_f, text="➕ Neuer Artikel", command=self.add_product)
        btn2.pack(fill='x', pady=2)
        Tooltip(btn2, "Einen neuen Artikel zur Bibliothek hinzufügen")
        btn3 = ttk.Button(lib_btn_f, text="✏️ Artikel bearbeiten", command=self.edit_selected_product)
        btn3.pack(fill='x', pady=2)
        Tooltip(btn3, "Den ausgewählten Artikel bearbeiten")
        btn4 = ttk.Button(lib_btn_f, text="📂 Preise aus CSV importieren", command=self.update_prices_from_csv)
        btn4.pack(fill='x', pady=2)
        Tooltip(btn4, "Preise aus einer CSV-Datei aktualisieren")
        self.lib_tree.bind("<Double-1>", lambda e: self.add_from_library())
        self.lib_menu = tk.Menu(self.root, tearoff=0)
        self.lib_menu.add_command(label="Bearbeiten", command=self.edit_selected_product)
        self.lib_menu.add_command(label="Löschen", command=self.delete_selected_product)
        self.lib_tree.bind("<Button-3>", lambda e: self.lib_menu.post(e.x_root, e.y_root))
        
        right_side = ttk.Frame(pw, padding=10)
        pw.add(right_side)
        entry_frame = ttk.LabelFrame(right_side, text="  ➕  Neue Position hinzufügen  ", padding=12)
        entry_frame.pack(fill='x', pady=(0, 10))
        self.desc_entry = ttk.Entry(entry_frame, width=45)
        self.desc_entry.grid(row=0, column=0, padx=5, sticky='ew')
        self.qty_entry = ttk.Entry(entry_frame, width=8)
        self.qty_entry.insert(0, "1")
        self.qty_entry.grid(row=0, column=1, padx=5)
        self.price_entry = ttk.Entry(entry_frame, width=12)
        self.price_entry.grid(row=0, column=2, padx=5)
        ttk.Button(entry_frame, text="Hinzufügen", command=self.add_item, style='Accent.TButton').grid(row=0, column=3, padx=5)
        entry_frame.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(right_side, columns=("Beschreibung", "Menge", "Einzelpreis", "Gesamt"), show='headings')
        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
        self.tree.column("Beschreibung", width=300)
        self.tree.column("Menge", width=70, anchor='center')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind("<ButtonPress-1>", self.on_drag_start)
        self.tree.bind("<B1-Motion>", self.on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self.on_drag_drop)
        self._bind_treeview_keys()
        btn_row = tk.Frame(right_side, bg=COLORS['bg'])
        btn_row.pack(fill='x', pady=8)
        for txt, cmd in [("✏️ Bearbeiten", self.edit_item), ("📋 Kopieren", self.copy_item),
                         ("⬆ Hoch", self.move_up), ("⬇ Runter", self.move_down), ("🗑 Löschen", self.delete_item)]:
            ttk.Button(btn_row, text=txt, command=cmd).pack(side='left', padx=2)
        self.refresh_product_list()
    
    def refresh_product_list(self):
        for row in self.lib_tree.get_children():
            self.lib_tree.delete(row)
        self.current_products = self.product_db.get_all()
        search_term = self.lib_search_var.get().strip().lower()
        for prod in self.current_products:
            if search_term and search_term not in prod['description'].lower():
                continue
            self.lib_tree.insert('', 'end', text=prod['description'], values=(format_currency(prod['unit_price'])))
    
    def add_from_library(self):
        sel = self.lib_tree.selection()
        if not sel: return
        item_desc = self.lib_tree.item(sel[0], "text")
        for prod in self.current_products:
            if prod['description'] == item_desc:
                self.desc_entry.delete(0, tk.END)
                self.desc_entry.insert(0, prod['description'])
                self.price_entry.delete(0, tk.END)
                self.price_entry.insert(0, str(prod['unit_price']).replace('.', ','))
                self.qty_entry.focus()
                break
    
    def add_product(self):
        win = tk.Toplevel(self.root)
        win.title("Neuer Artikel")
        win.geometry("400x250")
        win.transient(self.root)
        win.grab_set()
        ttk.Label(win, text="Bezeichnung:").pack(anchor='w', padx=10, pady=5)
        desc_var = tk.StringVar()
        ttk.Entry(win, textvariable=desc_var, width=50).pack(fill='x', padx=10)
        ttk.Label(win, text="Preis (€):").pack(anchor='w', padx=10, pady=5)
        price_var = tk.StringVar()
        ttk.Entry(win, textvariable=price_var, width=20).pack(anchor='w', padx=10)
        def save():
            desc = desc_var.get().strip()
            try:
                price = float(price_var.get().replace(',', '.'))
            except:
                messagebox.showerror("Fehler", "Ungültiger Preis.")
                return
            if not desc:
                messagebox.showerror("Fehler", "Bezeichnung darf nicht leer sein.")
                return
            self.product_db.add({"description": desc, "unit_price": price})
            self.refresh_product_list()
            win.destroy()
        ttk.Button(win, text="Hinzufügen", command=save).pack(pady=20)
        win.bind('<Return>', lambda e: save())
        win.bind('<Escape>', lambda e: win.destroy())
    
    def edit_selected_product(self):
        sel = self.lib_tree.selection()
        if not sel: return
        item_text = self.lib_tree.item(sel[0], "text")
        for prod in self.current_products:
            if prod['description'] == item_text:
                win = tk.Toplevel(self.root)
                win.title("Artikel bearbeiten")
                win.geometry("400x250")
                win.transient(self.root)
                win.grab_set()
                ttk.Label(win, text="Bezeichnung:").pack(anchor='w', padx=10, pady=5)
                desc_var = tk.StringVar(value=prod['description'])
                ttk.Entry(win, textvariable=desc_var, width=50).pack(fill='x', padx=10)
                ttk.Label(win, text="Preis (€):").pack(anchor='w', padx=10, pady=5)
                price_var = tk.StringVar(value=str(prod['unit_price']).replace('.', ','))
                ttk.Entry(win, textvariable=price_var, width=20).pack(anchor='w', padx=10)
                def save():
                    new_desc = desc_var.get().strip()
                    try:
                        new_price = float(price_var.get().replace(',', '.'))
                    except:
                        messagebox.showerror("Fehler", "Ungültiger Preis.")
                        return
                    if not new_desc:
                        messagebox.showerror("Fehler", "Bezeichnung darf nicht leer sein.")
                        return
                    prod['description'] = new_desc
                    prod['unit_price'] = new_price
                    self.product_db.update(prod['id'], prod)
                    self.refresh_product_list()
                    win.destroy()
                ttk.Button(win, text="Speichern", command=save).pack(pady=20)
                win.bind('<Return>', lambda e: save())
                win.bind('<Escape>', lambda e: win.destroy())
                break
    
    def delete_selected_product(self):
        sel = self.lib_tree.selection()
        if not sel: return
        item_text = self.lib_tree.item(sel[0], "text")
        for prod in self.current_products:
            if prod['description'] == item_text:
                if messagebox.askyesno("Löschen", f"Artikel '{item_text}' wirklich löschen?"):
                    self.product_db.delete(prod['id'])
                    self.refresh_product_list()
                break
    
    def update_prices_from_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not filepath: return
        progress = ProgressDialog(self.root, "Importiere Preise...")
        def do_import():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    updates = {row['Artikelname'].strip(): float(row['Preis'].replace(',', '.')) for row in reader}
                updated = 0
                for prod in self.current_products:
                    if prod['description'] in updates:
                        prod['unit_price'] = updates[prod['description']]
                        self.product_db.update(prod['id'], prod)
                        updated += 1
                self.root.after(0, lambda: self.refresh_product_list())
                self.root.after(0, lambda: messagebox.showinfo("Preisupdate", f"{updated} Preise aktualisiert."))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Fehler", f"CSV konnte nicht gelesen werden: {e}"))
            finally:
                self.root.after(0, progress.close)
        threading.Thread(target=do_import, daemon=True).start()
    
    # --------------------------------------------------------
    #  Drag & Drop für Positionen
    # --------------------------------------------------------
    def on_drag_start(self, event):
        self.drag_start_index = self.tree.identify_row(event.y)
        if self.drag_start_index:
            self.tree.selection_set(self.drag_start_index)
    def on_drag_motion(self, event):
        pass
    def on_drag_drop(self, event):
        if not self.drag_start_index: return
        target = self.tree.identify_row(event.y)
        if not target or target == self.drag_start_index:
            self.drag_start_index = None
            return
        items = self.tree.get_children()
        start_idx = items.index(self.drag_start_index)
        target_idx = items.index(target)
        items_list = self.current_offer['items']
        self._save_state_for_undo()
        item_moved = items_list.pop(start_idx)
        items_list.insert(target_idx, item_moved)
        self.update_items_table()
        new_items = self.tree.get_children()
        self.tree.selection_set(new_items[target_idx])
        self.drag_start_index = None
    
    # --------------------------------------------------------
    #  Positionen bearbeiten (mit Undo)
    # --------------------------------------------------------
    def add_item(self):
        try:
            desc = self.desc_entry.get().strip()
            qty = float(self.qty_entry.get().replace(',', '.'))
            price = float(self.price_entry.get().replace(',', '.'))
            if not desc: raise ValueError
            self._save_state_for_undo()
            self.current_offer['items'].append({"description": desc, "quantity": qty, "unit_price": price})
            self.update_items_table()
            self.desc_entry.delete(0, tk.END)
            self.price_entry.delete(0, tk.END)
            self.desc_entry.focus()
        except:
            messagebox.showerror("Eingabe", "Bitte gültige Beschreibung, Menge und Preis eingeben.")
    
    def update_items_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        total_net = 0
        for item in self.current_offer['items']:
            total = item['quantity'] * item['unit_price']
            total_net += total
            self.tree.insert('', 'end', values=(item['description'], f"{item['quantity']:g}", format_currency(item['unit_price']), format_currency(total)))
        self._update_totals(total_net)
        self.sync_ui_to_data()
    
    def _update_totals(self, net):
        tax = self.tax_var.get()
        disc = self.discount_var.get()
        ship = self.shipping_var.get()
        final_net = net * (1 - disc/100) + ship
        gross = final_net * (1 + tax/100)
        self.total_label_var.set(f"Gesamt (brutto): {format_currency(gross)}")
    
    def edit_item(self):
        sel = self.tree.selection()
        if not sel: return
        idx = self.tree.index(sel[0])
        self._save_state_for_undo()
        item = self.current_offer['items'].pop(idx)
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(0, item['description'])
        self.qty_entry.delete(0, tk.END)
        self.qty_entry.insert(0, str(item['quantity']))
        self.price_entry.delete(0, tk.END)
        self.price_entry.insert(0, str(item['unit_price']))
        self.update_items_table()
        self.desc_entry.focus()
    
    def copy_item(self):
        sel = self.tree.selection()
        if not sel: return
        idx = self.tree.index(sel[0])
        self._save_state_for_undo()
        item = copy.deepcopy(self.current_offer['items'][idx])
        self.current_offer['items'].insert(idx+1, item)
        self.update_items_table()
    
    def delete_item(self):
        sel = self.tree.selection()
        if not sel: return
        idx = self.tree.index(sel[0])
        self._save_state_for_undo()
        del self.current_offer['items'][idx]
        self.update_items_table()
    
    def move_up(self):
        sel = self.tree.selection()
        if not sel: return
        idx = self.tree.index(sel[0])
        if idx > 0:
            self._save_state_for_undo()
            it = self.current_offer['items']
            it[idx], it[idx-1] = it[idx-1], it[idx]
            self.update_items_table()
            self.tree.selection_set(self.tree.get_children()[idx-1])
    
    def move_down(self):
        sel = self.tree.selection()
        if not sel: return
        idx = self.tree.index(sel[0])
        it = self.current_offer['items']
        if idx < len(it)-1:
            self._save_state_for_undo()
            it[idx], it[idx+1] = it[idx+1], it[idx]
            self.update_items_table()
            self.tree.selection_set(self.tree.get_children()[idx+1])
    
    # --------------------------------------------------------
    #  Tab: Kunden-Datenbank (wie gehabt)
    # --------------------------------------------------------
    def _build_tab_customers(self, parent):
        frame = ttk.Frame(parent, padding=10)
        frame.pack(fill='both', expand=True)
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill='x', pady=5)
        ttk.Button(toolbar, text="Neuer Kunde", command=self.add_customer).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Bearbeiten", command=self.edit_customer).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Löschen", command=self.delete_customer).pack(side='left', padx=2)
        cols = ("id", "name", "address", "contact", "phone", "email", "type")
        self.cust_tree = ttk.Treeview(frame, columns=cols, show='headings')
        self.cust_tree.heading("id", text="ID")
        self.cust_tree.heading("name", text="Name/Firma")
        self.cust_tree.heading("address", text="Adresse")
        self.cust_tree.heading("contact", text="Kontakt")
        self.cust_tree.heading("phone", text="Telefon")
        self.cust_tree.heading("email", text="E-Mail")
        self.cust_tree.heading("type", text="Typ")
        self.cust_tree.column("id", width=50)
        self.cust_tree.pack(fill='both', expand=True)
        self.refresh_customer_list()
    
    def refresh_customer_list(self):
        for row in self.cust_tree.get_children():
            self.cust_tree.delete(row)
        self.current_customers = self.customer_db.get_all()
        for cust in self.current_customers:
            self.cust_tree.insert("", "end", values=(
                cust["id"], cust.get("name", ""), cust.get("address", ""), cust.get("contact", ""),
                cust.get("phone", ""), cust.get("email", ""), cust.get("customer_type", "")
            ))
    
    def add_customer(self):
        self._edit_customer_dialog()
    def edit_customer(self):
        sel = self.cust_tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Bitte Kunden auswählen.")
            return
        cust_id = int(self.cust_tree.item(sel[0], "values")[0])
        for cust in self.current_customers:
            if cust["id"] == cust_id:
                self._edit_customer_dialog(cust, cust_id)
                break
    def _edit_customer_dialog(self, cust=None, cust_id=None):
        win = tk.Toplevel(self.root)
        win.title("Kunde bearbeiten" if cust else "Neuer Kunde")
        win.geometry("500x450")
        win.transient(self.root)
        win.grab_set()
        fields = {}
        labels = [("Name/Firma", "name"), ("Adresse", "address"), ("Kontaktperson", "contact"),
                  ("Telefon", "phone"), ("E-Mail", "email")]
        for i, (label, key) in enumerate(labels):
            ttk.Label(win, text=label).grid(row=i, column=0, sticky='w', padx=10, pady=5)
            var = tk.StringVar(value=cust.get(key, "") if cust else "")
            fields[key] = var
            ttk.Entry(win, textvariable=var, width=40).grid(row=i, column=1, padx=10, pady=5)
        ttk.Label(win, text="Kundentyp:").grid(row=len(labels), column=0, sticky='w', padx=10, pady=5)
        type_var = tk.StringVar(value=cust.get("customer_type", "gewerblich") if cust else "gewerblich")
        ttk.Combobox(win, textvariable=type_var, values=["gewerblich", "privat"], state="readonly").grid(row=len(labels), column=1, padx=10, pady=5)
        def save():
            new_cust = {k: v.get() for k, v in fields.items()}
            new_cust["customer_type"] = type_var.get()
            if cust and cust_id:
                self.customer_db.update(cust_id, new_cust)
            else:
                self.customer_db.add(new_cust)
            self.refresh_customer_list()
            win.destroy()
        ttk.Button(win, text="Speichern", command=save).grid(row=len(labels)+1, column=0, columnspan=2, pady=20)
        win.bind('<Return>', lambda e: save())
        win.bind('<Escape>', lambda e: win.destroy())
    def delete_customer(self):
        sel = self.cust_tree.selection()
        if not sel: return
        cust_id = int(self.cust_tree.item(sel[0], "values")[0])
        if messagebox.askyesno("Löschen", "Kunden wirklich löschen?"):
            self.customer_db.delete(cust_id)
            self.refresh_customer_list()
    
    # --------------------------------------------------------
    #  Tab: Angebote & Status (mit Suchfilter)
    # --------------------------------------------------------
    def _build_tab_offers(self, parent):
        frame = ttk.Frame(parent, padding=10)
        frame.pack(fill='both', expand=True)
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill='x', pady=5)
        ttk.Label(toolbar, text="Filter:").pack(side='left', padx=5)
        self.filter_var = tk.StringVar()
        self.filter_var.trace('w', lambda *a: self.refresh_offer_list())
        ttk.Entry(toolbar, textvariable=self.filter_var, width=30).pack(side='left', padx=5)
        Tooltip(toolbar.winfo_children()[-1], "Suche nach Angebotsnummer, Kunde oder Status")
        ttk.Button(toolbar, text="Angebot laden", command=self.load_selected_offer).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Status ändern", command=self.change_status).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Versionen", command=self.show_versions).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Löschen", command=self.delete_selected_offer).pack(side='left', padx=2)
        if self.is_admin:
            self.show_all_offers_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(toolbar, text="Alle Angebote anzeigen", variable=self.show_all_offers_var, command=self.refresh_offer_list).pack(side='left', padx=10)
        cols = ("nummer", "datum", "kunde", "netto", "status", "besitzer")
        self.offer_tree = ttk.Treeview(frame, columns=cols, show='headings')
        self.offer_tree.heading("nummer", text="Angebots-Nr.")
        self.offer_tree.heading("datum", text="Datum")
        self.offer_tree.heading("kunde", text="Kunde")
        self.offer_tree.heading("netto", text="Netto")
        self.offer_tree.heading("status", text="Status")
        self.offer_tree.heading("besitzer", text="Besitzer")
        self.offer_tree.pack(fill='both', expand=True)
        self.offer_tree.bind("<Double-1>", lambda e: self.load_selected_offer())
        self._bind_offers_tree_keys()
        self.refresh_offer_list()
    
    def refresh_offer_list(self):
        for row in self.offer_tree.get_children():
            self.offer_tree.delete(row)
        if self.is_admin and hasattr(self, 'show_all_offers_var') and self.show_all_offers_var.get():
            offers = self.offer_db.get_all(is_admin=True)
        else:
            offers = self.offer_db.get_all(username=self.current_user)
        filter_text = self.filter_var.get().strip().lower()
        for offer in offers:
            net = sum(item["quantity"] * item["unit_price"] for item in offer.get("items", []))
            disc = offer.get("discount", 0.0)
            ship = offer.get("shipping", 0.0)
            net_after = net * (1 - disc/100) + ship
            nummer = offer.get("offer_number", "")
            kunde = offer.get("customer", {}).get("name", "")
            status = offer.get("status", "Entwurf")
            if filter_text:
                if filter_text not in nummer.lower() and filter_text not in kunde.lower() and filter_text not in status.lower():
                    continue
            self.offer_tree.insert("", "end", values=(
                nummer, offer.get("date", ""), kunde, format_currency(net_after),
                status, offer.get("owner", "")
            ), tags=(offer,))
    
    def load_selected_offer(self):
        sel = self.offer_tree.selection()
        if not sel: return
        offer = self.offer_tree.item(sel[0], "tags")[0]
        if not self.is_admin and offer.get("owner") != self.current_user:
            messagebox.showerror("Fehler", "Keine Berechtigung für dieses Angebot.")
            return
        self._save_state_for_undo()
        self.current_offer = copy.deepcopy(offer)
        self.sync_data_to_ui()
        self.notebook.select(0)
        self._set_status(f"Angebot {offer.get('offer_number')} geladen.")
    
    def change_status(self):
        sel = self.offer_tree.selection()
        if not sel: return
        offer = self.offer_tree.item(sel[0], "tags")[0]
        if not self.is_admin and offer.get("owner") != self.current_user:
            messagebox.showerror("Fehler", "Keine Berechtigung.")
            return
        new_status = simpledialog.askstring("Status ändern", "Neuer Status (Entwurf, Gesendet, Angenommen, Abgelehnt):", initialvalue=offer.get("status", "Entwurf"))
        if new_status and new_status in ["Entwurf", "Gesendet", "Angenommen", "Abgelehnt"]:
            self._save_state_for_undo()
            offer["status"] = new_status
            self.offer_db.add_or_update(offer, self.current_user)
            self.refresh_offer_list()
            self.refresh_dashboard()
            self._set_status(f"Status geändert zu {new_status}")
    
    def show_versions(self):
        sel = self.offer_tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Bitte Angebot auswählen.")
            return
        offer = self.offer_tree.item(sel[0], "tags")[0]
        if not self.is_admin and offer.get("owner") != self.current_user:
            messagebox.showerror("Fehler", "Keine Berechtigung.")
            return
        versions = self.offer_db.get_versions(offer.get("offer_number"))
        if not versions:
            messagebox.showinfo("Info", "Keine älteren Versionen.")
            return
        win = tk.Toplevel(self.root)
        win.title(f"Versionen von {offer.get('offer_number')}")
        win.geometry("600x400")
        win.transient(self.root)
        win.grab_set()
        listbox = tk.Listbox(win, font=('Segoe UI', 10))
        listbox.pack(fill='both', expand=True, padx=10, pady=10)
        for v in versions:
            listbox.insert(tk.END, v.name)
        def restore():
            sel_idx = listbox.curselection()
            if sel_idx:
                version_path = versions[sel_idx[0]]
                restored = self.offer_db.restore_version(version_path)
                self._save_state_for_undo()
                self.current_offer = copy.deepcopy(restored)
                self.sync_data_to_ui()
                self.notebook.select(0)
                self._set_status(f"Version {version_path.name} wiederhergestellt.")
                win.destroy()
        ttk.Button(win, text="Wiederherstellen", command=restore).pack(pady=5)
        win.bind('<Return>', lambda e: restore())
        win.bind('<Escape>', lambda e: win.destroy())
    
    def delete_selected_offer(self):
        sel = self.offer_tree.selection()
        if not sel: return
        offer = self.offer_tree.item(sel[0], "tags")[0]
        if not self.is_admin and offer.get("owner") != self.current_user:
            messagebox.showerror("Fehler", "Keine Berechtigung.")
            return
        if messagebox.askyesno("Löschen", f"Angebot {offer.get('offer_number')} löschen?"):
            self.offer_db.delete(offer.get("offer_number"), self.current_user, self.is_admin)
            self.refresh_offer_list()
            self.refresh_dashboard()
    
    # --------------------------------------------------------
    #  Tab: Dashboard
    # --------------------------------------------------------
    def _build_tab_dashboard(self, parent):
        notebook = ttk.Notebook(parent)
        notebook.pack(fill='both', expand=True)
        text_frame = ttk.Frame(notebook)
        notebook.add(text_frame, text="📊 Zahlen")
        self.dashboard_text = tk.Text(text_frame, font=('Segoe UI', 11), bg=COLORS['bg'], fg=COLORS['text_main'], wrap='word')
        self.dashboard_text.pack(fill='both', expand=True)
        status_frame = ttk.Frame(notebook)
        notebook.add(status_frame, text="📈 Statusverteilung")
        self.status_fig = Figure(figsize=(5,4), dpi=100)
        self.status_ax = self.status_fig.add_subplot(111)
        self.status_canvas = FigureCanvasTkAgg(self.status_fig, master=status_frame)
        self.status_canvas.get_tk_widget().pack(fill='both', expand=True)
        revenue_frame = ttk.Frame(notebook)
        notebook.add(revenue_frame, text="💰 Umsatzentwicklung")
        self.revenue_fig = Figure(figsize=(5,4), dpi=100)
        self.revenue_ax = self.revenue_fig.add_subplot(111)
        self.revenue_canvas = FigureCanvasTkAgg(self.revenue_fig, master=revenue_frame)
        self.revenue_canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def refresh_dashboard(self):
        if self.is_admin and hasattr(self, 'show_all_offers_var') and self.show_all_offers_var.get():
            stats = self.offer_db.get_statistics(is_admin=True)
        else:
            stats = self.offer_db.get_statistics(username=self.current_user)
        text = f"""
📊 DASHBOARD STATISTIKEN (Benutzer: {self.current_user})

📄 Anzahl Angebote insgesamt: {stats['total_offers']}

💰 Umsatz (Netto): {format_currency(stats['total_net'])}
💰 Umsatz (Brutto): {format_currency(stats['total_gross'])}

📌 Status-Verteilung:
   • Entwurf:     {stats['status_count'].get('Entwurf', 0)}
   • Gesendet:    {stats['status_count'].get('Gesendet', 0)}
   • Angenommen:  {stats['status_count'].get('Angenommen', 0)}
   • Abgelehnt:   {stats['status_count'].get('Abgelehnt', 0)}
        """
        self.dashboard_text.delete(1.0, tk.END)
        self.dashboard_text.insert(tk.END, text)
        self.status_ax.clear()
        statuses = list(stats['status_count'].keys())
        counts = list(stats['status_count'].values())
        colors_bar = [COLORS['success'] if s == 'Angenommen' else COLORS['danger'] if s == 'Abgelehnt' else COLORS['warning'] for s in statuses]
        self.status_ax.bar(statuses, counts, color=colors_bar)
        self.status_ax.set_title('Angebote nach Status')
        self.status_ax.set_ylabel('Anzahl')
        self.status_canvas.draw()
        self.revenue_ax.clear()
        months_str = [m[0] for m in stats['monthly_revenue']]
        revenues = [m[1] for m in stats['monthly_revenue']]
        if months_str:
            months_dt = [datetime.strptime(ms, "%Y-%m") for ms in months_str]
            self.revenue_ax.plot(months_dt, revenues, marker='o', color=COLORS['accent'])
            self.revenue_ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            self.revenue_fig.autofmt_xdate()
        self.revenue_ax.set_title('Bruttoumsatz pro Monat')
        self.revenue_ax.set_ylabel('Umsatz (€)')
        self.revenue_canvas.draw()
    
    # --------------------------------------------------------
    #  Tab: Meine Firma
    # --------------------------------------------------------
    def _build_tab_company(self, parent):
        f = ttk.Frame(parent, padding=20)
        f.pack(fill='both')
        self.comp_vars = {}
        company = self.company_db.get_company()
        fields = [
            ("Firmenname", "name"), ("Straße", "address_line1"), ("Stadt", "address_line2"),
            ("Telefon", "phone"), ("Email", "email"), ("Website", "website"),
            ("IBAN", "iban"), ("Geschäftsführer", "ceo"),
            ("SMTP-Server", "smtp_server"), ("SMTP-Port", "smtp_port"),
            ("SMTP-Benutzer", "smtp_user"), ("SMTP-Passwort", "smtp_password"),
            ("Angebots-Präfix (z.B. A)", "offer_number_prefix")
        ]
        for i, (label, key) in enumerate(fields):
            ttk.Label(f, text=label).grid(row=i, column=0, sticky='w', pady=5)
            var = tk.StringVar(value=company.get(key, ""))
            self.comp_vars[key] = var
            if key == "smtp_password":
                e = ttk.Entry(f, textvariable=var, width=40, show="*")
            else:
                e = ttk.Entry(f, textvariable=var, width=40)
            e.grid(row=i, column=1, padx=10, sticky='ew')
        ttk.Button(f, text="Firmendaten speichern", command=self._save_company_from_ui, style='Accent.TButton').grid(row=len(fields), column=1, pady=20, sticky='e')
    
    def _save_company_from_ui(self):
        new_company = {}
        for k, v in self.comp_vars.items():
            if k == "smtp_port":
                try:
                    new_company[k] = int(v.get())
                except:
                    new_company[k] = 587
            elif k == "offer_number_prefix":
                new_company[k] = v.get().strip() or "A"
            else:
                new_company[k] = v.get()
        self.company_db.update_company(new_company)
        messagebox.showinfo("Erfolg", "Firmendaten gespeichert.")
    
    # --------------------------------------------------------
    #  Backup & Restore (mit Fortschrittsdialog)
    # --------------------------------------------------------
    def backup_database(self):
        progress = ProgressDialog(self.root, "Erstelle Backup...")
        def do_backup():
            try:
                backup_dir = get_data_dir() / "backups"
                backup_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = backup_dir / f"backup_{timestamp}.zip"
                with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    if LOCAL_SQLITE_PATH.exists():
                        zipf.write(LOCAL_SQLITE_PATH, arcname="enterprise_local.db")
                    if DB_CONFIG_PATH.exists():
                        zipf.write(DB_CONFIG_PATH, arcname="db_config.json")
                    versions_dir = get_data_dir() / "versions"
                    if versions_dir.exists():
                        for vf in versions_dir.glob("*.json"):
                            zipf.write(vf, arcname=f"versions/{vf.name}")
                self.root.after(0, lambda: messagebox.showinfo("Backup", f"Backup erstellt unter:\n{backup_file}"))
                self.root.after(0, lambda: self._set_status("Backup erstellt."))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Fehler", f"Backup fehlgeschlagen: {e}"))
            finally:
                self.root.after(0, progress.close)
        threading.Thread(target=do_backup, daemon=True).start()
    
    def restore_database(self):
        backup_dir = get_data_dir() / "backups"
        backup_file = filedialog.askopenfilename(filetypes=[("ZIP", "*.zip")], initialdir=backup_dir)
        if not backup_file: return
        progress = ProgressDialog(self.root, "Stelle Backup wieder her...")
        def do_restore():
            try:
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        zipf.extractall(tmpdir)
                        src_local_db = Path(tmpdir) / "enterprise_local.db"
                        if src_local_db.exists():
                            shutil.copy2(src_local_db, LOCAL_SQLITE_PATH)
                        src_config = Path(tmpdir) / "db_config.json"
                        if src_config.exists():
                            shutil.copy2(src_config, DB_CONFIG_PATH)
                        src_versions = Path(tmpdir) / "versions"
                        if src_versions.exists():
                            versions_dir = get_data_dir() / "versions"
                            versions_dir.mkdir(exist_ok=True)
                            for vf in src_versions.glob("*.json"):
                                shutil.copy2(vf, versions_dir / vf.name)
                # Datenbankverbindungen neu initialisieren
                DatabaseManager._instance = None
                self.user_db = UserDatabase()
                self.company_db = CompanyDatabase()
                self.template_db = TemplateDatabase()
                self.product_db = ProductDatabase()
                self.customer_db = CustomerDatabase()
                self.offer_db = OfferDatabase()
                self.root.after(0, lambda: self.refresh_customer_list())
                self.root.after(0, lambda: self.refresh_offer_list())
                self.root.after(0, lambda: self.refresh_product_list())
                self.root.after(0, lambda: self.refresh_dashboard())
                self.current_offer = self._get_empty_offer()
                self.root.after(0, lambda: self.sync_data_to_ui())
                self.root.after(0, lambda: messagebox.showinfo("Wiederherstellung", "Datenbank wiederhergestellt."))
                self.root.after(0, lambda: self._set_status("Backup wiederhergestellt."))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Fehler", f"Wiederherstellung fehlgeschlagen: {e}"))
            finally:
                self.root.after(0, progress.close)
        threading.Thread(target=do_restore, daemon=True).start()
    
    # --------------------------------------------------------
    #  Sync & Dateioperationen
    # --------------------------------------------------------
    def sync_ui_to_data(self):
        self.current_offer.update({
            "offer_number": self.offer_number_var.get(),
            "date": self.date_var.get(),
            "valid_until": self.valid_var.get(),
            "customer_ref": self.customer_ref_var.get(),
            "customer_type": self.customer_type_var.get(),
            "tax_rate": self.tax_var.get(),
            "discount": self.discount_var.get(),
            "shipping": self.shipping_var.get(),
            "personal_message": self.personal_msg.get("1.0", tk.END).strip(),
            "terms": self.terms_text.get("1.0", tk.END).strip()
        })
        self.current_offer['customer'].update({
            "name": self.cust_name.get(),
            "address": self.cust_addr.get(),
            "contact": self.cust_contact.get(),
            "phone": self.cust_phone.get(),
            "email": self.cust_email.get()
        })
    
    def sync_data_to_ui(self):
        self.offer_number_var.set(self.current_offer.get('offer_number', ''))
        self.date_var.set(self.current_offer.get('date', ''))
        self.valid_var.set(self.current_offer.get('valid_until', ''))
        self.customer_ref_var.set(self.current_offer.get('customer_ref', ''))
        self.customer_type_var.set(self.current_offer.get('customer_type', 'gewerblich'))
        self.tax_var.set(self.current_offer.get('tax_rate', 19))
        self.discount_var.set(self.current_offer.get('discount', 0.0))
        self.shipping_var.set(self.current_offer.get('shipping', 0.0))
        self.personal_msg.delete("1.0", tk.END)
        self.personal_msg.insert("1.0", self.current_offer.get('personal_message', ''))
        self.terms_text.delete("1.0", tk.END)
        self.terms_text.insert("1.0", self.current_offer.get('terms', ''))
        cust = self.current_offer.get('customer', {})
        self.cust_name.set(cust.get('name', ''))
        self.cust_addr.set(cust.get('address', ''))
        self.cust_contact.set(cust.get('contact', ''))
        self.cust_phone.set(cust.get('phone', ''))
        self.cust_email.set(cust.get('email', ''))
        self.update_items_table()
    
    def _new_offer(self):
        if messagebox.askyesno("Neu", "Neues Angebot erstellen?"):
            self._save_state_for_undo()
            self.current_offer = self._get_empty_offer()
            self.sync_data_to_ui()
    
    def save_offer(self):
        self.sync_ui_to_data()
        if "status" not in self.current_offer:
            self.current_offer["status"] = "Entwurf"
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_offer, f, indent=4)
                self.offer_db.add_or_update(self.current_offer, self.current_user)
                self.refresh_offer_list()
                self.refresh_dashboard()
                self._set_status("✅ Angebot gespeichert und in Datenbank aktualisiert.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {e}")
    
    def load_offer(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self._save_state_for_undo()
                    self.current_offer = json.load(f)
                self.sync_data_to_ui()
                self._set_status("📂 Angebot geladen.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Laden fehlgeschlagen: {e}")
    
    def generate_pdf(self):
        self.sync_ui_to_data()
        if not self.current_offer['items']:
            messagebox.showwarning("Fehler", "Keine Positionen vorhanden.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if path:
            try:
                company = self.company_db.get_company()
                gen = EnterprisePDFGenerator(self.current_offer, company, path)
                gen.build()
                messagebox.showinfo("PDF", f"PDF erstellt unter:\n{path}")
            except Exception as e:
                messagebox.showerror("Fehler", f"PDF-Erstellung fehlgeschlagen: {e}")
    
    def send_email_dialog(self):
        self.sync_ui_to_data()
        if not self.current_offer['items']:
            messagebox.showwarning("Fehler", "Keine Positionen vorhanden.")
            return
        fd, temp_pdf = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        company = self.company_db.get_company()
        gen = EnterprisePDFGenerator(self.current_offer, company, temp_pdf)
        gen.build()
        win = tk.Toplevel(self.root)
        win.title("E-Mail versenden")
        win.geometry("500x400")
        win.transient(self.root)
        win.grab_set()
        ttk.Label(win, text="Empfänger:").pack(anchor='w', padx=10, pady=5)
        to_entry = ttk.Entry(win, width=60)
        to_entry.pack(fill='x', padx=10)
        to_entry.insert(0, self.current_offer.get('customer', {}).get('email', ''))
        ttk.Label(win, text="Betreff:").pack(anchor='w', padx=10, pady=5)
        subj_entry = ttk.Entry(win, width=60)
        subj_entry.pack(fill='x', padx=10)
        subj_entry.insert(0, f"Angebot {self.current_offer.get('offer_number', '')}")
        ttk.Label(win, text="Nachricht:").pack(anchor='w', padx=10, pady=5)
        msg_text = tk.Text(win, height=8)
        msg_text.pack(fill='both', expand=True, padx=10, pady=5)
        msg_text.insert("1.0", "Sehr geehrte Damen und Herren,\n\nanbei erhalten Sie unser Angebot.\n\nMit freundlichen Grüßen\nIhr Team")
        def do_send():
            to_addr = to_entry.get().strip()
            if not to_addr:
                messagebox.showerror("Fehler", "Bitte Empfänger-E-Mail angeben.")
                return
            smtp_server = company.get("smtp_server", "")
            smtp_port = company.get("smtp_port", 587)
            smtp_user = company.get("smtp_user", "")
            smtp_pass = company.get("smtp_password", "")
            if not smtp_server or not smtp_user:
                messagebox.showerror("Fehler", "SMTP-Einstellungen in 'Meine Firma' fehlen.")
                return
            success, msg = EmailSender.send_email(
                smtp_server, smtp_port, smtp_user, smtp_pass,
                to_addr, subj_entry.get(), msg_text.get("1.0", tk.END).strip(),
                temp_pdf
            )
            if success:
                messagebox.showinfo("Erfolg", msg)
                self.current_offer["status"] = "Gesendet"
                self.offer_db.add_or_update(self.current_offer, self.current_user)
                self.refresh_offer_list()
                self.refresh_dashboard()
                win.destroy()
            else:
                messagebox.showerror("Fehler", msg)
            try:
                Path(temp_pdf).unlink()
            except:
                pass
        ttk.Button(win, text="Senden", command=do_send).pack(pady=10)
        win.bind('<Return>', lambda e: do_send())
        win.bind('<Escape>', lambda e: win.destroy())
    
    def open_calculator(self):
        GrossNetCalculatorDialog(self.root)
    
    def _set_status(self, msg):
        self.status_var.set(msg)

# ------------------------------------------------------------
#  Start des Programms
# ------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = EnterpriseAngebotGUI(root)
    root.mainloop()