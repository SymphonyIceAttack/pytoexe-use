#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Μεσιτικό Βοήθημα v2.6 – Professional Edition (Bilingual / Δίγλωσσο)
============================================================
Modern UI • Εικόνες • PDF • Calendar Widget • Matching
• Multi-language Support (Ελληνικά / English)
"""

import os
import sys
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import (
    Tk, Frame, Label, Entry, Button, Text, Scrollbar, StringVar, IntVar,
    Toplevel, messagebox, ttk, filedialog, Menu, LabelFrame, Canvas, BooleanVar
)
from tkinter.ttk import Notebook, Treeview, Combobox, Style, Separator

import pandas as pd

# Optional deps
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image as RLImage, HRFlowable
    )
    from reportlab.lib.units import cm, mm
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    from tkcalendar import Calendar, DateEntry
    HAS_TKCALENDAR = True
except ImportError:
    HAS_TKCALENDAR = False

# ============================================================
# ΔΙΓΛΩΣΣΑ ΚΕΙΜΕΝΑ (TRANSLATIONS)
# ============================================================
LANG = {
    "el": {
        "app_title": "Μεσιτικό Βοήθημα v2.6  •  Professional",
        "header_title": "  Μεσιτικό Βοήθημα",
        "header_sub": "v2.6 Professional",
        "header_info": "Πελάτες  •  Ακίνητα  •  Επισκέψεις  •  Matching  •  PDF",
        "ready": "Έτοιμο",
        # Menus
        "menu_file": "Αρχείο",
        "menu_refresh": "Ανανέωση δεδομένων",
        "menu_exit": "Έξοδος",
        "menu_export": "Εξαγωγή",
        "menu_excel_full": "Excel Πλήρης Αναφορά",
        "menu_pdf_general": "PDF Γενική Αναφορά",
        "menu_tools": "Εργαλεία",
        "menu_compare": "Σύγκριση 2 Ακινήτων",
        "menu_lang": "Γλώσσα / Language",
        # Tabs
        "tab_dash": "  Dashboard  ",
        "tab_clients": "  Πελάτες  ",
        "tab_props": "  Ακίνητα  ",
        "tab_visits": "  Επισκέψεις  ",
        "tab_reports": "  Αναφορές  ",
        "tab_calc": "  Υπολογισμοί  ",
        # Dashboard
        "kpi_clients": "Πελάτες",
        "kpi_props": "Ακίνητα",
        "kpi_avail": "Διαθέσιμα",
        "kpi_val": "Αξία Διαθέσιμων",
        "kpi_visits": "Προγρ. Επισκέψεις",
        "recent_activity": "Πρόσφατη Δραστηριότητα",
        "quick_actions": "Γρήγορες Ενέργειες",
        "btn_new_client": "＋  Νέος Πελάτης",
        "btn_new_prop": "＋  Νέο Ακίνητο",
        "btn_new_visit": "＋  Νέα Επίσκεψη",
        "btn_pdf_rep": "📄  PDF Γενική Αναφορά",
        "btn_refresh": "🔄  Ανανέωση",
        "no_activity": "Δεν υπάρχει ακόμα δραστηριότητα.",
        # Buttons / Common
        "btn_new": "＋ Νέο",
        "btn_edit": "✎ Επεξεργασία",
        "btn_delete": "🗑 Διαγραφή",
        "btn_save": "Αποθήκευση",
        "btn_cancel": "Ακύρωση",
        "search": "Αναζήτηση",
        "status_lbl": "Κατάσταση:",
        "all": "Όλα",
        # Clients
        "client_cols": ["ID", "Όνομα", "Τηλέφωνο", "Email", "Τύπος", "Min_ΤΜ", "Υπνοδ.", "Έτος_Από", "Budget", "Σημειώσεις"],
        "match_btn": "🔍 Matching",
        # Properties
        "prop_cols": ["ID", "Διεύθυνση", "Τ.μ.", "Τιμή", "Τύπος", "Υπνοδ.", "Έτος", "Κατάσταση", "Μεσίτης", "Εικόνα"],
        "img_btn": "🖼 Εικόνα",
        "pdf_prop_btn": "📄 PDF Ακινήτου",
        # Visits & Calendar
        "calendar": "Ημερολόγιο",
        "today": "Σήμερα",
        "clear_filter": "Καθαρισμός φίλτρου",
        "visit_cols": ["ID", "Ημερομηνία", "Ώρα", "Πελάτης", "Ακίνητο", "Κατάσταση", "Σημειώσεις"],
        "visit_filters": ["Όλες", "Προγραμματισμένες", "Σήμερα", "Επόμενες 7 ημέρες", "Ολοκληρωμένες", "Ακυρωμένες"],
        "btn_done": "✅ Ολοκληρώθηκε",
        "btn_cancel_v": "❌ Ακύρωση",
        # Calculations
        "loan_title": "  🏦  Στεγαστικό Δάνειο  ",
        "yield_title": "  📈  Απόδοση (Yield)  ",
        "costs_title": "  💶  Έξοδα Αγοράς / Μεταβίβασης  ",
        "calc_btn": "Υπολογισμός",
        "amort_btn": "Πίνακας Αποπληρωμής",
    },
    "en": {
        "app_title": "Real Estate Assistant v2.6  •  Professional",
        "header_title": "  Real Estate Assistant",
        "header_sub": "v2.6 Professional",
        "header_info": "Clients  •  Properties  •  Visits  •  Matching  •  PDF",
        "ready": "Ready",
        # Menus
        "menu_file": "File",
        "menu_refresh": "Refresh data",
        "menu_exit": "Exit",
        "menu_export": "Export",
        "menu_excel_full": "Excel Full Report",
        "menu_pdf_general": "PDF General Report",
        "menu_tools": "Tools",
        "menu_compare": "Compare 2 Properties",
        "menu_lang": "Γλώσσα / Language",
        # Tabs
        "tab_dash": "  Dashboard  ",
        "tab_clients": "  Clients  ",
        "tab_props": "  Properties  ",
        "tab_visits": "  Visits  ",
        "tab_reports": "  Reports  ",
        "tab_calc": "  Calculators  ",
        # Dashboard
        "kpi_clients": "Clients",
        "kpi_props": "Properties",
        "kpi_avail": "Available",
        "kpi_val": "Available Value",
        "kpi_visits": "Upcoming Visits",
        "recent_activity": "Recent Activity",
        "quick_actions": "Quick Actions",
        "btn_new_client": "＋  New Client",
        "btn_new_prop": "＋  New Property",
        "btn_new_visit": "＋  New Visit",
        "btn_pdf_rep": "📄  PDF General Report",
        "btn_refresh": "🔄  Refresh",
        "no_activity": "No activity yet.",
        # Buttons / Common
        "btn_new": "＋ New",
        "btn_edit": "✎ Edit",
        "btn_delete": "🗑 Delete",
        "btn_save": "Save",
        "btn_cancel": "Cancel",
        "search": "Search",
        "status_lbl": "Status:",
        "all": "All",
        # Clients
        "client_cols": ["ID", "Name", "Phone", "Email", "Type", "Min_Sqm", "Beds", "Year_From", "Budget", "Notes"],
        "match_btn": "🔍 Matching",
        # Properties
        "prop_cols": ["ID", "Address", "Sqm", "Price", "Type", "Beds", "Year", "Status", "Agent", "Image"],
        "img_btn": "🖼 Image",
        "pdf_prop_btn": "📄 Property PDF",
        # Visits & Calendar
        "calendar": "Calendar",
        "today": "Today",
        "clear_filter": "Clear Filter",
        "visit_cols": ["ID", "Date", "Time", "Client", "Property", "Status", "Notes"],
        "visit_filters": ["All", "Scheduled", "Today", "Next 7 Days", "Completed", "Cancelled"],
        "btn_done": "✅ Completed",
        "btn_cancel_v": "❌ Cancel",
        # Calculations
        "loan_title": "  🏦  Mortgage Loan  ",
        "yield_title": "  📈  Rental Yield  ",
        "costs_title": "  💶  Purchase & Transfer Costs  ",
        "calc_btn": "Calculate",
        "amort_btn": "Amortization Table",
    }
}

CURRENT_LANG = "el"

def t(key):
    return LANG[CURRENT_LANG].get(key, key)


# ============================================================
# ΡΥΘΜΙΣΕΙΣ & ΔΕΔΟΜΕΝΑ
# ============================================================
DATA_DIR = Path(__file__).parent / "data"
CLIENTS_FILE = DATA_DIR / "pelates.xlsx"
PROPERTIES_FILE = DATA_DIR / "akinita.xlsx"
VISITS_FILE = DATA_DIR / "episkepseis.xlsx"
REPORTS_DIR = DATA_DIR / "anafores"
IMAGES_DIR = DATA_DIR / "eikones"

CLIENT_COLUMNS = [
    "ID", "Όνομα", "Τηλέφωνο", "Email", "Τύπος_Ενδιαφέροντος",
    "Ελάχιστα_ΤΜ", "Υπνοδωμάτια", "Έτος_Κατασκευής_Από", "Budget",
    "Σημειώσεις", "Ημερομηνία_Καταχώρησης"
]
PROPERTY_COLUMNS = [
    "ID", "Διεύθυνση", "Τετραγωνικά", "Τιμή", "Τύπος", "Υπνοδωμάτια",
    "Έτος_Κατασκευής", "Κατάσταση", "Μεσίτης", "Σημειώσεις",
    "Εικόνα", "Ημερομηνία_Καταχώρησης"
]
VISIT_COLUMNS = [
    "ID", "Ημερομηνία", "Ώρα", "Πελάτης_ID", "Πελάτης", "Ακίνητο_ID",
    "Ακίνητο", "Κατάσταση", "Σημειώσεις", "Ημερομηνία_Καταχώρησης"
]

PROPERTY_TYPES = ["Οποιοδήποτε", "Διαμέρισμα", "Μονοκατοικία", "Μεζονέτα",
                  "Οικόπεδο", "Επαγγελματικό", "Αποθήκη", "Άλλο"]
PROPERTY_STATUSES = ["Διαθέσιμο", "Υπό διαπραγμάτευση", "Πωλήθηκε",
                     "Ενοικιάστηκε", "Ανενεργό"]
VISIT_STATUSES = ["Προγραμματισμένη", "Ολοκληρώθηκε", "Ακυρώθηκε", "Αναβλήθηκε"]

# Χρώματα modern
C_PRIMARY = "#1a365d"
C_ACCENT = "#2b6cb0"
C_SUCCESS = "#38a169"
C_DANGER = "#e53e3e"
C_WARNING = "#dd6b20"
C_BG = "#f7fafc"
C_CARD = "#ffffff"
C_TEXT = "#2d3748"
C_MUTED = "#718096"


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def load_df(path, columns):
    ensure_data_dir()
    if path.exists():
        try:
            df = pd.read_excel(path, engine="openpyxl", dtype=str)
            for col in columns:
                if col not in df.columns:
                    df[col] = ""
            df["ID"] = pd.to_numeric(df["ID"], errors="coerce").fillna(0).astype(int)
            for col in df.columns:
                if col != "ID":
                    df[col] = df[col].astype(object).fillna("")
            return df[columns]
        except Exception:
            pass
    return pd.DataFrame(columns=columns)


def save_df(df, path):
    ensure_data_dir()
    df.to_excel(path, index=False, engine="openpyxl")


def load_clients(): return load_df(CLIENTS_FILE, CLIENT_COLUMNS)
def save_clients(df): save_df(df, CLIENTS_FILE)
def load_properties(): return load_df(PROPERTIES_FILE, PROPERTY_COLUMNS)
def save_properties(df): save_df(df, PROPERTIES_FILE)
def load_visits(): return load_df(VISITS_FILE, VISIT_COLUMNS)
def save_visits(df): save_df(df, VISITS_FILE)


def next_id(df):
    if df.empty or "ID" not in df.columns:
        return 1
    try:
        val = pd.to_numeric(df["ID"], errors="coerce").max()
        return 1 if pd.isna(val) else int(val) + 1
    except Exception:
        return 1


def safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        s = str(value).replace("€", "").replace(" ", "").strip()
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        return float(s)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        return int(safe_float(value, default))
    except Exception:
        return default


def format_currency(amount):
    try:
        val = safe_float(amount)
        if val == 0:
            return ""
        return f"{val:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(amount)


# ============================================================
# ΚΥΡΙΑ ΕΦΑΡΜΟΓΗ
# ============================================================
class MesitikoApp(Tk):
    def __init__(self):
        super().__init__()
        self.title(t("app_title"))
        self.geometry("1360x860")
        self.minsize(1100, 720)
        self.configure(bg=C_BG)

        self._setup_styles()
        self._build_menu()
        self._build_header()
        self._build_notebook()
        self._build_statusbar()

        self.refresh_all()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_styles(self):
        style = Style()
        style.theme_use("clam")

        style.configure("TNotebook", background=C_BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=[16, 8], font=("Segoe UI", 10),
                        background="#e2e8f0", foreground=C_TEXT)
        style.map("TNotebook.Tab",
                  background=[("selected", C_PRIMARY)],
                  foreground=[("selected", "white")])

        style.configure("Treeview", rowheight=30, font=("Segoe UI", 10),
                        background="white", fieldbackground="white",
                        foreground=C_TEXT)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                        background=C_PRIMARY, foreground="white", relief="flat")
        style.map("Treeview.Heading", background=[("active", C_ACCENT)])
        style.map("Treeview", background=[("selected", "#bee3f8")],
                  foreground=[("selected", C_PRIMARY)])

        style.configure("TButton", font=("Segoe UI", 10), padding=7)
        style.configure("Card.TFrame", background=C_CARD)

    def _build_header(self):
        if hasattr(self, "header_frame"):
            self.header_frame.destroy()
        self.header_frame = Frame(self, bg=C_PRIMARY, height=58)
        self.header_frame.pack(fill="x")
        self.header_frame.pack_propagate(False)

        Label(self.header_frame, text=t("header_title"), font=("Segoe UI", 17, "bold"),
              bg=C_PRIMARY, fg="white").pack(side="left", padx=14, pady=12)
        Label(self.header_frame, text=t("header_sub"), font=("Segoe UI", 9),
              bg=C_PRIMARY, fg="#a0aec0").pack(side="left", pady=14)

        right = Frame(self.header_frame, bg=C_PRIMARY)
        right.pack(side="right", padx=16)
        Label(right, text=t("header_info"),
              font=("Segoe UI", 9), bg=C_PRIMARY, fg="#a0aec0").pack(side="right")

    def _build_statusbar(self):
        if hasattr(self, "statusbar_frame"):
            self.statusbar_frame.destroy()
        self.statusbar_frame = Frame(self, bg="#edf2f7", height=26)
        self.statusbar_frame.pack(side="bottom", fill="x")
        self.status = Label(self.statusbar_frame, text=t("ready"), anchor="w", bg="#edf2f7",
                            fg=C_MUTED, font=("Segoe UI", 9), padx=10)
        self.status.pack(side="left", fill="x", expand=True)
        self.clock_lbl = Label(self.statusbar_frame, text="", bg="#edf2f7", fg=C_MUTED,
                               font=("Segoe UI", 9), padx=10)
        self.clock_lbl.pack(side="right")
        self._update_clock()

    def _update_clock(self):
        self.clock_lbl.config(text=datetime.now().strftime("%d/%m/%Y  %H:%M"))
        self.after(30000, self._update_clock)

    def set_status(self, text):
        self.status.config(text=text)
        self.after(4500, lambda: self.status.config(text=t("ready")))

    def _build_menu(self):
        menubar = Menu(self)
        self.config(menu=menubar)

        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu_file"), menu=file_menu)
        file_menu.add_command(label=t("menu_refresh"), command=self.refresh_all)
        file_menu.add_separator()
        file_menu.add_command(label=t("menu_exit"), command=self.on_close)

        export_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu_export"), menu=export_menu)
        export_menu.add_command(label=t("menu_excel_full"), command=self.export_report_excel)
        export_menu.add_command(label=t("menu_pdf_general"), command=self.export_report_pdf)

        tools_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu_tools"), menu=tools_menu)
        tools_menu.add_command(label=t("menu_compare"), command=self.compare_properties)

        lang_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu_lang"), menu=lang_menu)
        lang_menu.add_command(label="Ελληνικά (Greek)", command=lambda: self.change_language("el"))
        lang_menu.add_command(label="English", command=lambda: self.change_language("en"))

    def change_language(self, lang_code):
        global CURRENT_LANG
        CURRENT_LANG = lang_code
        self.title(t("app_title"))
        self._build_menu()
        self._build_header()
        self._build_statusbar()
        self._build_notebook()
        self.refresh_all()
        self.set_status(f"Language / Γλώσσα changed")

    def _build_notebook(self):
        if hasattr(self, "nb"):
            self.nb.destroy()
        self.nb = Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=(8, 4))

        self.tab_dash = Frame(self.nb, bg=C_BG)
        self.tab_clients = Frame(self.nb, bg=C_BG)
        self.tab_properties = Frame(self.nb, bg=C_BG)
        self.tab_visits = Frame(self.nb, bg=C_BG)
        self.tab_reports = Frame(self.nb, bg=C_BG)
        self.tab_calc = Frame(self.nb, bg=C_BG)

        self.nb.add(self.tab_dash, text=t("tab_dash"))
        self.nb.add(self.tab_clients, text=t("tab_clients"))
        self.nb.add(self.tab_properties, text=t("tab_props"))
        self.nb.add(self.tab_visits, text=t("tab_visits"))
        self.nb.add(self.tab_reports, text=t("tab_reports"))
        self.nb.add(self.tab_calc, text=t("tab_calc"))

        self._build_dashboard_tab()
        self._build_clients_tab()
        self._build_properties_tab()
        self._build_visits_tab()
        self._build_reports_tab()
        self._build_calc_tab()

    # ============================================================
    # DASHBOARD – Modern Cards
    # ============================================================
    def _build_dashboard_tab(self):
        outer = Frame(self.tab_dash, bg=C_BG)
        outer.pack(fill="both", expand=True, padx=18, pady=16)

        # KPI cards row
        self.kpi_row = Frame(outer, bg=C_BG)
        self.kpi_row.pack(fill="x", pady=(0, 16))

        self.kpi_labels = {}
        cards_info = [
            ("clients", t("kpi_clients"), "#3182ce"),
            ("props", t("kpi_props"), "#38a169"),
            ("avail", t("kpi_avail"), "#d69e2e"),
            ("value", t("kpi_val"), "#805ad5"),
            ("visits", t("kpi_visits"), "#e53e3e"),
        ]
        for key, title, color in cards_info:
            card = Frame(self.kpi_row, bg=C_CARD, highlightbackground="#e2e8f0",
                         highlightthickness=1, padx=18, pady=14)
            card.pack(side="left", fill="both", expand=True, padx=6)
            Label(card, text=title, font=("Segoe UI", 9), bg=C_CARD,
                  fg=C_MUTED).pack(anchor="w")
            lbl = Label(card, text="—", font=("Segoe UI", 20, "bold"),
                        bg=C_CARD, fg=color)
            lbl.pack(anchor="w", pady=(4, 0))
            self.kpi_labels[key] = lbl

        # Recent + quick info
        bottom = Frame(outer, bg=C_BG)
        bottom.pack(fill="both", expand=True)

        left = Frame(bottom, bg=C_CARD, highlightbackground="#e2e8f0",
                     highlightthickness=1, padx=16, pady=14)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        Label(left, text=t("recent_activity"), font=("Segoe UI", 12, "bold"),
              bg=C_CARD, fg=C_PRIMARY).pack(anchor="w")
        self.activity_text = Text(left, height=12, font=("Segoe UI", 10),
                                  bg="#f8fafc", relief="flat", wrap="word")
        self.activity_text.pack(fill="both", expand=True, pady=(8, 0))

        right = Frame(bottom, bg=C_CARD, highlightbackground="#e2e8f0",
                      highlightthickness=1, padx=16, pady=14)
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))
        Label(right, text=t("quick_actions"), font=("Segoe UI", 12, "bold"),
              bg=C_CARD, fg=C_PRIMARY).pack(anchor="w")
        btn_style = {"font": ("Segoe UI", 10), "relief": "flat", "padx": 12, "pady": 8}
        Button(right, text=t("btn_new_client"), command=self.add_client_dialog,
               bg=C_SUCCESS, fg="white", **btn_style).pack(fill="x", pady=6)
        Button(right, text=t("btn_new_prop"), command=self.add_property_dialog,
               bg=C_ACCENT, fg="white", **btn_style).pack(fill="x", pady=6)
        Button(right, text=t("btn_new_visit"), command=self.add_visit_dialog,
               bg=C_WARNING, fg="white", **btn_style).pack(fill="x", pady=6)
        Button(right, text=t("btn_pdf_rep"), command=self.export_report_pdf,
               bg=C_DANGER, fg="white", **btn_style).pack(fill="x", pady=6)
        Button(right, text=t("btn_refresh"), command=self.refresh_all,
               bg="#4a5568", fg="white", **btn_style).pack(fill="x", pady=6)

    def refresh_dashboard(self):
        df_c = load_clients()
        df_p = load_properties()
        df_v = load_visits()

        total_c = len(df_c)
        total_p = len(df_p)
        avail = 0
        total_val = 0.0
        if not df_p.empty:
            mask = df_p["Κατάσταση"].astype(str).str.lower().str.contains("διαθέσιμο|διαθεσιμο|available", na=False)
            avail_df = df_p[mask]
            avail = len(avail_df)
            total_val = sum(safe_float(x) for x in avail_df["Τιμή"])

        upcoming = 0
        if not df_v.empty:
            upcoming = len(df_v[df_v["Κατάσταση"].astype(str).str.contains("Προγραμματισμένη|Scheduled", na=False)])

        self.kpi_labels["clients"].config(text=str(total_c))
        self.kpi_labels["props"].config(text=str(total_p))
        self.kpi_labels["avail"].config(text=str(avail))
        self.kpi_labels["value"].config(text=format_currency(total_val) or "0 €")
        self.kpi_labels["visits"].config(text=str(upcoming))

        # Activity
        lines = []
        if not df_v.empty:
            recent_v = df_v.sort_values("ID", ascending=False).head(5)
            for _, r in recent_v.iterrows():
                lines.append(f"📅  {r['Ημερομηνία']} {r['Ώρα']}  •  {r['Πελάτης']} → {r['Ακίνητο']}  [{r['Κατάσταση']}]")
        if not df_c.empty:
            recent_c = df_c.sort_values("ID", ascending=False).head(3)
            for _, r in recent_c.iterrows():
                lines.append(f"👤  Νέος πελάτης: {r['Όνομα']}  ({r.get('Ημερομηνία_Καταχώρησης', '')})")
        if not lines:
            lines = [t("no_activity")]

        self.activity_text.config(state="normal")
        self.activity_text.delete("1.0", "end")
        self.activity_text.insert("1.0", "\n\n".join(lines))
        self.activity_text.config(state="disabled")

    # ============================================================
    # ΠΕΛΑΤΕΣ (CLIENTS)
    # ============================================================
    def _build_clients_tab(self):
        top = Frame(self.tab_clients, bg=C_BG)
        top.pack(fill="x", padx=12, pady=10)

        def btn(txt, cmd, bg):
            return Button(top, text=txt, command=cmd, bg=bg, fg="white",
                          font=("Segoe UI", 10), relief="flat", padx=11, pady=5)

        btn(t("btn_new"), self.add_client_dialog, C_SUCCESS).pack(side="left", padx=3)
        btn(t("btn_edit"), self.edit_client_dialog, C_ACCENT).pack(side="left", padx=3)
        btn(t("match_btn"), self.match_client_properties, "#0bc5ea").pack(side="left", padx=3)
        btn(t("btn_delete"), self.delete_client, C_DANGER).pack(side="left", padx=3)

        search_f = Frame(top, bg=C_BG)
        search_f.pack(side="right")
        Label(search_f, text=t("search"), bg=C_BG, fg=C_MUTED,
              font=("Segoe UI", 9)).pack(side="left", padx=(0, 6))
        self.client_search = StringVar()
        self.client_search.trace_add("write", lambda *a: self.refresh_clients())
        Entry(search_f, textvariable=self.client_search, width=24,
              font=("Segoe UI", 10), relief="solid", bd=1).pack(side="left")

        tree_frame = Frame(self.tab_clients, bg=C_BG)
        tree_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        cols = t("client_cols")
        self.clients_tree = Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.clients_tree.heading(c, text=c.replace("_", " "))
            w = 42 if c == "ID" else (145 if c in ("Όνομα", "Name", "Email") else 88)
            self.clients_tree.column(c, width=w, anchor="w")
        vsb = Scrollbar(tree_frame, orient="vertical", command=self.clients_tree.yview)
        self.clients_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.clients_tree.pack(fill="both", expand=True)
        self.clients_tree.bind("<Double-1>", lambda e: self.edit_client_dialog())

    def refresh_clients(self):
        for item in self.clients_tree.get_children():
            self.clients_tree.delete(item)
        df = load_clients()
        q = self.client_search.get().strip().lower() if hasattr(self, "client_search") else ""
        for _, row in df.iterrows():
            if q:
                hay = " ".join(str(row.get(c, "")).lower() for c in
                               ["Όνομα", "Τηλέφωνο", "Email", "Τύπος_Ενδιαφέροντος", "Σημειώσεις"])
                if q not in hay:
                    continue
            budget = safe_float(row["Budget"])
            self.clients_tree.insert("", "end", values=(
                row["ID"], row["Όνομα"], str(row["Τηλέφωνο"]), row["Email"],
                row["Τύπος_Ενδιαφέροντος"], row["Ελάχιστα_ΤΜ"], row["Υπνοδωμάτια"],
                row["Έτος_Κατασκευής_Από"],
                format_currency(budget) if budget else row["Budget"],
                row["Σημειώσεις"]
            ))

    def _get_selected_client_id(self):
        sel = self.clients_tree.selection()
        if not sel:
            messagebox.showwarning("Προσοχή", "Επιλέξτε πρώτα έναν πελάτη." if CURRENT_LANG=="el" else "Please select a client first.")
            return None
        return safe_int(self.clients_tree.item(sel[0])["values"][0])

    def add_client_dialog(self):
        self._client_form_dialog(None)

    def edit_client_dialog(self):
        cid = self._get_selected_client_id()
        if cid is None:
            return
        df = load_clients()
        row = df[df["ID"] == cid]
        if row.empty:
            return
        self._client_form_dialog(row.iloc[0])

    def _client_form_dialog(self, existing):
        win = Toplevel(self)
        win.title("Επεξεργασία Πελάτη" if existing is not None else "Νέος Πελάτης")
        win.geometry("520x560")
        win.transient(self)
        win.grab_set()
        win.configure(bg=C_BG)

        fields = [
            ("Όνομα *" if CURRENT_LANG=="el" else "Name *", "Όνομα"),
            ("Τηλέφωνο" if CURRENT_LANG=="el" else "Phone", "Τηλέφωνο"),
            ("Email", "Email"),
            ("Ελάχιστα τ.μ." if CURRENT_LANG=="el" else "Min Sqm", "Ελάχιστα_ΤΜ"),
            ("Ελάχιστα Υπνοδωμάτια" if CURRENT_LANG=="el" else "Min Bedrooms", "Υπνοδωμάτια"),
            ("Έτος Κατασκευής (από)" if CURRENT_LANG=="el" else "Year Built (from)", "Έτος_Κατασκευής_Από"),
            ("Budget (€)", "Budget"),
            ("Σημειώσεις" if CURRENT_LANG=="el" else "Notes", "Σημειώσεις"),
        ]
        entries = {}
        row_idx = 0
        for i in range(3):
            label, key = fields[i]
            Label(win, text=label, bg=C_BG, font=("Segoe UI", 10)).grid(row=row_idx, column=0, sticky="w", padx=16, pady=5)
            e = Entry(win, width=38, font=("Segoe UI", 10))
            e.grid(row=row_idx, column=1, padx=16, pady=5)
            if existing is not None:
                e.insert(0, str(existing.get(key, "") or ""))
            entries[key] = e
            row_idx += 1

        Label(win, text="Τύπος Ακινήτου" if CURRENT_LANG=="el" else "Property Type", bg=C_BG, font=("Segoe UI", 10)).grid(row=row_idx, column=0, sticky="w", padx=16, pady=5)
        type_var = StringVar()
        type_cb = Combobox(win, textvariable=type_var, values=PROPERTY_TYPES, width=35,
                           font=("Segoe UI", 10), state="readonly")
        type_cb.grid(row=row_idx, column=1, padx=16, pady=5)
        if existing is not None and existing.get("Τύπος_Ενδιαφέροντος"):
            type_var.set(existing["Τύπος_Ενδιαφέροντος"])
        else:
            type_cb.current(0)
        row_idx += 1

        for i in range(3, len(fields)):
            label, key = fields[i]
            Label(win, text=label, bg=C_BG, font=("Segoe UI", 10)).grid(row=row_idx, column=0, sticky="w", padx=16, pady=5)
            e = Entry(win, width=38, font=("Segoe UI", 10))
            e.grid(row=row_idx, column=1, padx=16, pady=5)
            if existing is not None:
                e.insert(0, str(existing.get(key, "") or ""))
            entries[key] = e
            row_idx += 1

        def save():
            name = entries["Όνομα"].get().strip()
            if not name:
                messagebox.showerror("Σφάλμα", "Το όνομα είναι υποχρεωτικό." if CURRENT_LANG=="el" else "Name is required.", parent=win)
                return
            df = load_clients()
            if existing is not None:
                cid = safe_int(existing["ID"])
                idx_list = df.index[df["ID"] == cid].tolist()
                if not idx_list:
                    return
                idx = idx_list[0]
                for key in entries:
                    df.at[idx, key] = str(entries[key].get().strip())
                df.at[idx, "Τύπος_Ενδιαφέροντος"] = type_var.get()
                save_clients(df)
            else:
                new_row = {
                    "ID": next_id(df), "Όνομα": name,
                    "Τηλέφωνο": str(entries["Τηλέφωνο"].get().strip()),
                    "Email": entries["Email"].get().strip(),
                    "Τύπος_Ενδιαφέροντος": type_var.get(),
                    "Ελάχιστα_ΤΜ": str(entries["Ελάχιστα_ΤΜ"].get().strip()),
                    "Υπνοδωμάτια": str(entries["Υπνοδωμάτια"].get().strip()),
                    "Έτος_Κατασκευής_Από": str(entries["Έτος_Κατασκευής_Από"].get().strip()),
                    "Budget": str(entries["Budget"].get().strip()),
                    "Σημειώσεις": entries["Σημειώσεις"].get().strip(),
                    "Ημερομηνία_Καταχώρησης": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_clients(df)
            win.destroy()
            self.refresh_all()
            self.set_status("Saved")

        btn_f = Frame(win, bg=C_BG)
        btn_f.grid(row=row_idx, column=0, columnspan=2, pady=18)
        Button(btn_f, text=t("btn_save"), command=save, bg=C_SUCCESS, fg="white",
               font=("Segoe UI", 10, "bold"), relief="flat", padx=16, pady=6).pack(side="left", padx=8)
        Button(btn_f, text=t("btn_cancel"), command=win.destroy, bg="#718096", fg="white",
               font=("Segoe UI", 10), relief="flat", padx=16, pady=6).pack(side="left", padx=8)

    def delete_client(self):
        cid = self._get_selected_client_id()
        if cid is None:
            return
        if messagebox.askyesno("Επιβεβαίωση", "Είστε σίγουροι για τη διαγραφή;" if CURRENT_LANG=="el" else "Are you sure you want to delete?"):
            df = load_clients()
            df = df[df["ID"] != cid]
            save_clients(df)
            self.refresh_all()
            self.set_status("Deleted")

    def match_client_properties(self):
        cid = self._get_selected_client_id()
        if cid is None:
            return
        df_clients = load_clients()
        client_rows = df_clients[df_clients["ID"] == cid]
        if client_rows.empty:
            return
        client = client_rows.iloc[0]
        df_props = load_properties()
        if df_props.empty:
            messagebox.showinfo("Matching", "Δεν υπάρχουν ακίνητα." if CURRENT_LANG=="el" else "No properties found.")
            return

        matched = df_props.copy()
        matched = matched[matched["Κατάσταση"].astype(str).str.lower().str.contains("διαθέσιμο|διαθεσιμο|available", na=True)]

        c_budget = safe_float(client.get("Budget", 0))
        c_type = str(client.get("Τύπος_Ενδιαφέροντος", "")).strip()
        c_sqm = safe_float(client.get("Ελάχιστα_ΤΜ", 0))
        c_beds = safe_int(client.get("Υπνοδωμάτια", 0))
        c_year = safe_int(client.get("Έτος_Κατασκευής_Από", 0))

        scores = []
        for _, row in matched.iterrows():
            score = max_score = 0
            max_score += 30
            price = safe_float(row["Τιμή"])
            if c_budget <= 0 or price <= 0 or price <= c_budget:
                score += 30
            elif price <= c_budget * 1.1:
                score += 15
            max_score += 25
            if not c_type or c_type in ("Οποιοδήποτε", "Any") or str(row["Τύπος"]).strip().lower() == c_type.lower():
                score += 25
            max_score += 20
            sqm = safe_float(row["Τετραγωνικά"])
            if c_sqm <= 0 or sqm >= c_sqm:
                score += 20
            elif sqm >= c_sqm * 0.9:
                score += 10
            max_score += 15
            beds = safe_int(row["Υπνοδωμάτια"])
            if c_beds <= 0 or beds >= c_beds:
                score += 15
            max_score += 10
            year = safe_int(row["Έτος_Κατασκευής"])
            if c_year <= 0 or year >= c_year:
                score += 10
            pct = int(round((score / max_score) * 100)) if max_score else 0
            scores.append((pct, row))

        scores.sort(key=lambda x: x[0], reverse=True)

        win = Toplevel(self)
        win.title(f"Matching • {client['Όνομα']}")
        win.geometry("1000x500")
        win.configure(bg=C_BG)
        info = (f"👤 {client['Όνομα']}  |  Budget: {format_currency(c_budget) or ('Χωρίς όριο' if CURRENT_LANG=='el' else 'No limit')}  |  "
                f"Τύπος: {c_type or ('Όλοι' if CURRENT_LANG=='el' else 'All')}  |  Min τ.μ.: {c_sqm or '-'}  |  Υπν.: {c_beds or '-'}")
        Label(win, text=info, font=("Segoe UI", 10, "bold"), bg="#ebf8ff",
              fg=C_PRIMARY, padx=12, pady=10).pack(fill="x")

        tree_frame = Frame(win, bg=C_BG)
        tree_frame.pack(fill="both", expand=True, padx=12, pady=8)
        cols = ("Score", "ID", "Διεύθυνση", "Τ.μ.", "Τιμή", "Τύπος", "Υπνοδ.", "Έτος", "Κατάσταση")
        tree = Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=85 if c != "Διεύθυνση" else 190, anchor="w")
        vsb = Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        for pct, row in scores:
            tree.insert("", "end", values=(
                f"{pct}%", row["ID"], row["Διεύθυνση"], row["Τετραγωνικά"],
                format_currency(safe_float(row["Τιμή"])), row["Τύπος"],
                row["Υπνοδωμάτια"], row["Έτος_Κατασκευής"], row["Κατάσταση"]
            ))
        Label(win, text=f"Βρέθηκαν {len(scores)} ακίνητα" if CURRENT_LANG=="el" else f"Found {len(scores)} properties",
              font=("Segoe UI", 10, "bold"), bg=C_BG, fg=C_SUCCESS).pack(pady=8)

    # ============================================================
    # ΑΚΙΝΗΤΑ (PROPERTIES)
    # ============================================================
    def _build_properties_tab(self):
        top = Frame(self.tab_properties, bg=C_BG)
        top.pack(fill="x", padx=12, pady=10)

        def btn(txt, cmd, bg):
            return Button(top, text=txt, command=cmd, bg=bg, fg="white",
                          font=("Segoe UI", 10), relief="flat", padx=10, pady=5)

        btn(t("btn_new"), self.add_property_dialog, C_SUCCESS).pack(side="left", padx=3)
        btn(t("btn_edit"), self.edit_property_dialog, C_ACCENT).pack(side="left", padx=3)
        btn(t("img_btn"), self.view_property_image, "#805ad5").pack(side="left", padx=3)
        btn(t("pdf_prop_btn"), self.export_property_pdf, C_DANGER).pack(side="left", padx=3)
        btn(t("btn_delete"), self.delete_property, "#c53030").pack(side="left", padx=3)

        Label(top, text=t("status_lbl"), bg=C_BG, fg=C_MUTED).pack(side="left", padx=(18, 4))
        self.prop_status_filter = StringVar(value=t("all"))
        Combobox(top, textvariable=self.prop_status_filter,
                 values=[t("all")] + PROPERTY_STATUSES, width=16, state="readonly").pack(side="left")
        self.prop_status_filter.trace_add("write", lambda *a: self.refresh_properties())

        search_f = Frame(top, bg=C_BG)
        search_f.pack(side="right")
        Label(search_f, text=t("search"), bg=C_BG, fg=C_MUTED,
              font=("Segoe UI", 9)).pack(side="left", padx=(0, 6))
        self.prop_search = StringVar()
        self.prop_search.trace_add("write", lambda *a: self.refresh_properties())
        Entry(search_f, textvariable=self.prop_search, width=22,
              font=("Segoe UI", 10), relief="solid", bd=1).pack(side="left")

        tree_frame = Frame(self.tab_properties, bg=C_BG)
        tree_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        cols = t("prop_cols")
        self.props_tree = Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.props_tree.heading(c, text=c)
            self.props_tree.column(c, width=90 if c not in ("Διεύθυνση", "Address") else 175, anchor="w")
        vsb = Scrollbar(tree_frame, orient="vertical", command=self.props_tree.yview)
        self.props_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.props_tree.pack(fill="both", expand=True)
        self.props_tree.bind("<Double-1>", lambda e: self.edit_property_dialog())

    def refresh_properties(self):
        for item in self.props_tree.get_children():
            self.props_tree.delete(item)
        df = load_properties()
        q = self.prop_search.get().strip().lower() if hasattr(self, "prop_search") else ""
        st_f = self.prop_status_filter.get() if hasattr(self, "prop_status_filter") else t("all")

        for _, row in df.iterrows():
            if st_f != t("all") and str(row.get("Κατάσταση", "")) != st_f:
                continue
            if q:
                hay = " ".join(str(row.get(c, "")).lower() for c in
                               ["Διεύθυνση", "Τύπος", "Κατάσταση", "Μεσίτης", "Σημειώσεις"])
                if q not in hay:
                    continue
            price = safe_float(row["Τιμή"])
            img = ("Ναι" if CURRENT_LANG=="el" else "Yes") if str(row.get("Εικόνα", "")).strip() else "—"
            self.props_tree.insert("", "end", values=(
                row["ID"], row["Διεύθυνση"], row["Τετραγωνικά"],
                format_currency(price) if price else row["Τιμή"],
                row["Τύπος"], row["Υπνοδωμάτια"], row["Έτος_Κατασκευής"],
                row["Κατάσταση"], row["Μεσίτης"], img
            ))

    def _get_selected_prop_id(self):
        sel = self.props_tree.selection()
        if not sel:
            messagebox.showwarning("Προσοχή", "Επιλέξτε πρώτα ένα ακίνητο." if CURRENT_LANG=="el" else "Please select a property first.")
            return None
        return safe_int(self.props_tree.item(sel[0])["values"][0])

    def add_property_dialog(self):
        self._property_form_dialog(None)

    def edit_property_dialog(self):
        pid = self._get_selected_prop_id()
        if pid is None:
            return
        df = load_properties()
        row = df[df["ID"] == pid]
        if row.empty:
            return
        self._property_form_dialog(row.iloc[0])

    def _property_form_dialog(self, existing):
        win = Toplevel(self)
        win.title("Επεξεργασία Ακινήτου" if existing is not None else "Νέο Ακίνητο")
        win.geometry("580x660")
        win.transient(self)
        win.grab_set()
        win.configure(bg=C_BG)

        fields_entry = [
            ("Διεύθυνση *" if CURRENT_LANG=="el" else "Address *", "Διεύθυνση"),
            ("Τετραγωνικά (τ.μ.)" if CURRENT_LANG=="el" else "Sqm", "Τετραγωνικά"),
            ("Τιμή (€)" if CURRENT_LANG=="el" else "Price (€)", "Τιμή"),
            ("Υπνοδωμάτια" if CURRENT_LANG=="el" else "Bedrooms", "Υπνοδωμάτια"),
            ("Έτος Κατασκευής" if CURRENT_LANG=="el" else "Year Built", "Έτος_Κατασκευής"),
            ("Μεσίτης" if CURRENT_LANG=="el" else "Agent", "Μεσίτης"),
            ("Σημειώσεις" if CURRENT_LANG=="el" else "Notes", "Σημειώσεις"),
        ]
        entries = {}
        row_idx = 0
        image_path_var = StringVar(value=str(existing.get("Εικόνα", "") or "") if existing is not None else "")

        for i in range(3):
            label, key = fields_entry[i]
            Label(win, text=label, bg=C_BG, font=("Segoe UI", 10)).grid(row=row_idx, column=0, sticky="w", padx=16, pady=4)
            e = Entry(win, width=42, font=("Segoe UI", 10))
            e.grid(row=row_idx, column=1, padx=16, pady=4)
            if existing is not None:
                e.insert(0, str(existing.get(key, "") or ""))
            entries[key] = e
            row_idx += 1

        Label(win, text="Τύπος" if CURRENT_LANG=="el" else "Type", bg=C_BG, font=("Segoe UI", 10)).grid(row=row_idx, column=0, sticky="w", padx=16, pady=4)
        type_var = StringVar()
        type_cb = Combobox(win, textvariable=type_var, values=PROPERTY_TYPES[1:], width=39,
                           font=("Segoe UI", 10), state="readonly")
        type_cb.grid(row=row_idx, column=1, padx=16, pady=4)
        if existing is not None and existing.get("Τύπος"):
            type_var.set(existing["Τύπος"])
        else:
            type_cb.current(0)
        row_idx += 1

        for i in range(3, len(fields_entry)):
            label, key = fields_entry[i]
            Label(win, text=label, bg=C_BG, font=("Segoe UI", 10)).grid(row=row_idx, column=0, sticky="w", padx=16, pady=4)
            e = Entry(win, width=42, font=("Segoe UI", 10))
            e.grid(row=row_idx, column=1, padx=16, pady=4)
            if existing is not None:
                e.insert(0, str(existing.get(key, "") or ""))
            entries[key] = e
            row_idx += 1

        Label(win, text="Κατάσταση" if CURRENT_LANG=="el" else "Status", bg=C_BG, font=("Segoe UI", 10)).grid(row=row_idx, column=0, sticky="w", padx=16, pady=4)
        status_var = StringVar()
        status_cb = Combobox(win, textvariable=status_var, values=PROPERTY_STATUSES, width=39,
                             font=("Segoe UI", 10), state="readonly")
        status_cb.grid(row=row_idx, column=1, padx=16, pady=4)
        if existing is not None and existing.get("Κατάσταση"):
            status_var.set(existing["Κατάσταση"])
        else:
            status_cb.current(0)
        row_idx += 1

        Label(win, text="Εικόνα" if CURRENT_LANG=="el" else "Image", bg=C_BG, font=("Segoe UI", 10)).grid(row=row_idx, column=0, sticky="w", padx=16, pady=4)
        img_f = Frame(win, bg=C_BG)
        img_f.grid(row=row_idx, column=1, sticky="w", padx=16, pady=4)
        Entry(img_f, textvariable=image_path_var, width=28, font=("Segoe UI", 9),
              state="readonly").pack(side="left")
        Button(img_f, text="Επιλογή…" if CURRENT_LANG=="el" else "Browse…", command=lambda: self._pick_image(image_path_var, preview_lbl),
               relief="flat", bg="#4a5568", fg="white", padx=8).pack(side="left", padx=5)
        row_idx += 1

        preview_lbl = Label(win, bg="#edf2f7", width=42, height=7, text="(χωρίς εικόνα)" if CURRENT_LANG=="el" else "(no image)")
        preview_lbl.grid(row=row_idx, column=0, columnspan=2, pady=8)
        row_idx += 1
        if image_path_var.get() and HAS_PIL:
            self._show_thumbnail(image_path_var.get(), preview_lbl)

        def save():
            address = entries["Διεύθυνση"].get().strip()
            if not address:
                messagebox.showerror("Σφάλμα", "Η διεύθυνση είναι υποχρεωτική." if CURRENT_LANG=="el" else "Address is required.", parent=win)
                return
            df = load_properties()
            if existing is not None:
                pid = safe_int(existing["ID"])
                idx_list = df.index[df["ID"] == pid].tolist()
                if not idx_list:
                    return
                idx = idx_list[0]
                for key in entries:
                    df.at[idx, key] = str(entries[key].get().strip())
                df.at[idx, "Τύπος"] = type_var.get()
                df.at[idx, "Κατάσταση"] = status_var.get()
                df.at[idx, "Εικόνα"] = image_path_var.get()
                save_properties(df)
            else:
                new_row = {
                    "ID": next_id(df), "Διεύθυνση": address,
                    "Τετραγωνικά": str(entries["Τετραγωνικά"].get().strip()),
                    "Τιμή": str(entries["Τιμή"].get().strip()),
                    "Τύπος": type_var.get(),
                    "Υπνοδωμάτια": str(entries["Υπνοδωμάτια"].get().strip()),
                    "Έτος_Κατασκευής": str(entries["Έτος_Κατασκευής"].get().strip()),
                    "Κατάσταση": status_var.get(),
                    "Μεσίτης": entries["Μεσίτης"].get().strip(),
                    "Σημειώσεις": entries["Σημειώσεις"].get().strip(),
                    "Εικόνα": image_path_var.get(),
                    "Ημερομηνία_Καταχώρησης": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_properties(df)
            win.destroy()
            self.refresh_all()
            self.set_status("Saved")

        btn_f = Frame(win, bg=C_BG)
        btn_f.grid(row=row_idx, column=0, columnspan=2, pady=14)
        Button(btn_f, text=t("btn_save"), command=save, bg=C_SUCCESS, fg="white",
               font=("Segoe UI", 10, "bold"), relief="flat", padx=16, pady=6).pack(side="left", padx=8)
        Button(btn_f, text=t("btn_cancel"), command=win.destroy, bg="#718096", fg="white",
               font=("Segoe UI", 10), relief="flat", padx=16, pady=6).pack(side="left", padx=8)

    def _pick_image(self, path_var, preview_lbl):
        path = filedialog.askopenfilename(
            title="Επιλογή εικόνας" if CURRENT_LANG=="el" else "Select Image",
            filetypes=[("Εικόνες" if CURRENT_LANG=="el" else "Images", "*.jpg *.jpeg *.png *.webp *.bmp"), ("Όλα" if CURRENT_LANG=="el" else "All", "*.*")]
        )
        if path:
            try:
                ensure_data_dir()
                src = Path(path)
                dest = IMAGES_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{src.name}"
                shutil.copy2(src, dest)
                path_var.set(str(dest))
            except Exception:
                path_var.set(path)
            if HAS_PIL:
                self._show_thumbnail(path_var.get(), preview_lbl)

    def _show_thumbnail(self, path, label_widget):
        if not HAS_PIL or not path or not Path(path).exists():
            label_widget.config(image="", text="(χωρίς εικόνα)" if CURRENT_LANG=="el" else "(no image)")
            return
        try:
            img = Image.open(path)
            img.thumbnail((300, 170))
            photo = ImageTk.PhotoImage(img)
            label_widget.config(image=photo, text="")
            label_widget.image = photo
        except Exception:
            label_widget.config(image="", text="(σφάλμα εικόνας)" if CURRENT_LANG=="el" else "(image error)")

    def view_property_image(self):
        pid = self._get_selected_prop_id()
        if pid is None:
            return
        df = load_properties()
        row = df[df["ID"] == pid]
        if row.empty:
            return
        path = str(row.iloc[0].get("Εικόνα", "") or "")
        if not path or not Path(path).exists():
            messagebox.showinfo("Εικόνα" if CURRENT_LANG=="el" else "Image", "Δεν υπάρχει εικόνα για αυτό το ακίνητο." if CURRENT_LANG=="el" else "No image for this property.")
            return
        if not HAS_PIL:
            messagebox.showinfo("Εικόνα", f"Διαδρομή:\n{path}")
            return
        win = Toplevel(self)
        win.title(f"Εικόνα • {row.iloc[0]['Διεύθυνση']}")
        win.geometry("720x520")
        try:
            img = Image.open(path)
            img.thumbnail((700, 480))
            photo = ImageTk.PhotoImage(img)
            lbl = Label(win, image=photo)
            lbl.image = photo
            lbl.pack(expand=True)
        except Exception as e:
            Label(win, text=f"Σφάλμα: {e}").pack()

    def export_property_pdf(self):
        if not HAS_REPORTLAB:
            messagebox.showerror("Σφάλμα", "Χρειάζεται: pip install reportlab")
            return
        pid = self._get_selected_prop_id()
        if pid is None:
            return
        df = load_properties()
        row = df[df["ID"] == pid]
        if row.empty:
            return
        r = row.iloc[0]

        try:
            ensure_data_dir()
            safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in str(r["Διεύθυνση"]))[:40]
            out_file = REPORTS_DIR / f"akinito_{pid}_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

            doc = SimpleDocTemplate(str(out_file), pagesize=A4,
                                    rightMargin=1.8*cm, leftMargin=1.8*cm,
                                    topMargin=1.5*cm, bottomMargin=1.5*cm)
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle("T", parent=styles["Heading1"], fontSize=18,
                                         textColor=colors.HexColor("#1a365d"), spaceAfter=6)
            normal = ParagraphStyle("N", parent=styles["Normal"], fontSize=10, leading=14)

            story = []
            story.append(Paragraph("Δελτίο Ακινήτου" if CURRENT_LANG=="el" else "Property Sheet", title_style))
            story.append(Paragraph(f"ID: {r['ID']}  •  {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e0"), spaceAfter=12))

            img_path = str(r.get("Εικόνα", "") or "")
            if img_path and Path(img_path).exists() and HAS_PIL:
                try:
                    story.append(RLImage(img_path, width=12*cm, height=7.5*cm, kind="proportional"))
                    story.append(Spacer(1, 10))
                except Exception:
                    pass

            data = [
                ["Διεύθυνση" if CURRENT_LANG=="el" else "Address", str(r["Διεύθυνση"])],
                ["Τύπος" if CURRENT_LANG=="el" else "Type", str(r["Τύπος"])],
                ["Τετραγωνικά" if CURRENT_LANG=="el" else "Sqm", f"{r['Τετραγωνικά']} τ.μ."],
                ["Τιμή" if CURRENT_LANG=="el" else "Price", format_currency(safe_float(r["Τιμή"])) or str(r["Τιμή"])],
                ["Υπνοδωμάτια" if CURRENT_LANG=="el" else "Bedrooms", str(r["Υπνοδωμάτια"])],
                ["Έτος Κατασκευής" if CURRENT_LANG=="el" else "Year Built", str(r["Έτος_Κατασκευής"])],
                ["Κατάσταση" if CURRENT_LANG=="el" else "Status", str(r["Κατάσταση"])],
                ["Μεσίτης" if CURRENT_LANG=="el" else "Agent", str(r["Μεσίτης"])],
                ["Σημειώσεις" if CURRENT_LANG=="el" else "Notes", str(r.get("Σημειώσεις", "") or "—")],
                ["Καταχώρηση" if CURRENT_LANG=="el" else "Registered", str(r.get("Ημερομηνία_Καταχώρησης", ""))],
            ]
            t = Table(data, colWidths=[4.5*cm, 11*cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#edf2f7")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2d3748")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 20))
            story.append(Paragraph("Μεσιτικό Βοήθημα v2.6  •  Εμπιστευτικό" if CURRENT_LANG=="el" else "Real Estate Assistant v2.6  •  Confidential", 
                                   ParagraphStyle("F", parent=normal, fontSize=8, textColor=colors.grey)))

            doc.build(story)
            messagebox.showinfo("PDF", f"Saved:\n{out_file}")
            self.set_status("PDF created")
        except Exception as e:
            messagebox.showerror("PDF Error", str(e))

    def delete_property(self):
        pid = self._get_selected_prop_id()
        if pid is None:
            return
        if messagebox.askyesno("Επιβεβαίωση", "Διαγραφή ακινήτου;" if CURRENT_LANG=="el" else "Delete property?"):
            df = load_properties()
            df = df[df["ID"] != pid]
            save_properties(df)
            self.refresh_all()
            self.set_status("Deleted")

    def compare_properties(self):
        df = load_properties()
        if len(df) < 2:
            messagebox.showinfo("Σύγκριση" if CURRENT_LANG=="el" else "Compare", "Χρειάζονται τουλάχιστον 2 ακίνητα." if CURRENT_LANG=="el" else "At least 2 properties required.")
            return
        names = [f"{r['ID']} – {r['Διεύθυνση']} ({format_currency(safe_float(r['Τιμή']))})" for _, r in df.iterrows()]

        win = Toplevel(self)
        win.title("Σύγκριση Ακινήτων" if CURRENT_LANG=="el" else "Property Comparison")
        win.geometry("720x420")
        win.configure(bg=C_BG)

        Label(win, text="Επιλέξτε 2 ακίνητα για σύγκριση" if CURRENT_LANG=="el" else "Select 2 properties to compare", font=("Segoe UI", 11, "bold"),
              bg=C_BG, fg=C_PRIMARY).pack(pady=12)

        f = Frame(win, bg=C_BG)
        f.pack(pady=8)
        Label(f, text="Ακίνητο Α:" if CURRENT_LANG=="el" else "Property A:", bg=C_BG).grid(row=0, column=0, padx=8)
        var_a = StringVar()
        Combobox(f, textvariable=var_a, values=names, width=45, state="readonly").grid(row=0, column=1, padx=8)
        Label(f, text="Ακίνητο Β:" if CURRENT_LANG=="el" else "Property B:", bg=C_BG).grid(row=1, column=0, padx=8, pady=8)
        var_b = StringVar()
        Combobox(f, textvariable=var_b, values=names, width=45, state="readonly").grid(row=1, column=1, padx=8)

        result = Text(win, height=14, font=("Consolas", 10), bg="white", relief="solid", bd=1)
        result.pack(fill="both", expand=True, padx=16, pady=10)

        def do_compare():
            if not var_a.get() or not var_b.get():
                return
            try:
                id_a = int(var_a.get().split("–")[0].strip())
                id_b = int(var_b.get().split("–")[0].strip())
            except Exception:
                return
            ra = df[df["ID"] == id_a].iloc[0]
            rb = df[df["ID"] == id_b].iloc[0]
            lines = [
                f"{'Field' if CURRENT_LANG=='en' else 'Πεδίο':<22} {'Property A' if CURRENT_LANG=='en' else 'Ακίνητο Α':<28} {'Property B' if CURRENT_LANG=='en' else 'Ακίνητο Β'}",
                "-" * 78,
                f"{'Διεύθυνση' if CURRENT_LANG=='el' else 'Address':<22} {str(ra['Διεύθυνση'])[:26]:<28} {str(rb['Διεύθυνση'])[:26]}",
                f"{'Τιμή' if CURRENT_LANG=='el' else 'Price':<22} {format_currency(safe_float(ra['Τιμή'])):<28} {format_currency(safe_float(rb['Τιμή']))}",
                f"{'τ.μ.' if CURRENT_LANG=='el' else 'Sqm':<22} {str(ra['Τετραγωνικά']):<28} {str(rb['Τετραγωνικά'])}",
                f"{'Τύπος' if CURRENT_LANG=='el' else 'Type':<22} {str(ra['Τύπος']):<28} {str(rb['Τύπος'])}",
                f"{'Υπνοδωμάτια' if CURRENT_LANG=='el' else 'Bedrooms':<22} {str(ra['Υπνοδωμάτια']):<28} {str(rb['Υπνοδωμάτια'])}",
                f"{'Έτος' if CURRENT_LANG=='el' else 'Year':<22} {str(ra['Έτος_Κατασκευής']):<28} {str(rb['Έτος_Κατασκευής'])}",
                f"{'Κατάσταση' if CURRENT_LANG=='el' else 'Status':<22} {str(ra['Κατάσταση']):<28} {str(rb['Κατάσταση'])}",
                f"{'Μεσίτης' if CURRENT_LANG=='el' else 'Agent':<22} {str(ra['Μεσίτης']):<28} {str(rb['Μεσίτης'])}",
            ]
            p_a, s_a = safe_float(ra["Τιμή"]), safe_float(ra["Τετραγωνικά"])
            p_b, s_b = safe_float(rb["Τιμή"]), safe_float(rb["Τετραγωνικά"])
            if s_a > 0 and s_b > 0:
                lines.append(f"{'€ / τ.μ.':<22} {format_currency(p_a/s_a):<28} {format_currency(p_b/s_b)}")
            result.delete("1.0", "end")
            result.insert("1.0", "\n".join(lines))

        Button(win, text="Σύγκριση" if CURRENT_LANG=="el" else "Compare", command=do_compare, bg=C_ACCENT, fg="white",
               font=("Segoe UI", 10, "bold"), relief="flat", padx=14, pady=6).pack(pady=6)

    # ============================================================
    # ΕΠΙΣΚΕΨΕΙΣ (VISITS)
    # ============================================================
    def _build_visits_tab(self):
        main = Frame(self.tab_visits, bg=C_BG)
        main.pack(fill="both", expand=True, padx=12, pady=10)

        left = Frame(main, bg=C_BG)
        left.pack(side="left", fill="y", padx=(0, 12))

        Label(left, text=t("calendar"), font=("Segoe UI", 11, "bold"),
              bg=C_BG, fg=C_PRIMARY).pack(anchor="w", pady=(0, 6))

        if HAS_TKCALENDAR:
            self.cal = Calendar(left, selectmode="day", date_pattern="dd/mm/yyyy",
                                font=("Segoe UI", 9), background=C_PRIMARY,
                                foreground="white", headersbackground=C_ACCENT,
                                normalbackground="white", weekendbackground="#fff5f5",
                                othermonthbackground="#edf2f7", othermonthwebackground="#edf2f7")
            self.cal.pack()
            self.cal.bind("<<CalendarSelected>>", self._on_calendar_select)
            Button(left, text=t("today"), command=self._cal_today,
                   bg=C_ACCENT, fg="white", relief="flat", font=("Segoe UI", 9)).pack(pady=8, fill="x")
            Button(left, text=t("clear_filter"), command=self._clear_cal_filter,
                   bg="#718096", fg="white", relief="flat", font=("Segoe UI", 9)).pack(fill="x")
        else:
            Label(left, text="Install tkcalendar:\npip install tkcalendar", bg=C_BG, fg=C_MUTED).pack()

        right = Frame(main, bg=C_BG)
        right.pack(side="left", fill="both", expand=True)

        top = Frame(right, bg=C_BG)
        top.pack(fill="x", pady=(0, 8))

        def btn(txt, cmd, bg):
            return Button(top, text=txt, command=cmd, bg=bg, fg="white",
                          font=("Segoe UI", 9), relief="flat", padx=9, pady=4)

        btn(t("btn_new"), self.add_visit_dialog, C_SUCCESS).pack(side="left", padx=2)
        btn(t("btn_edit"), self.edit_visit_dialog, C_ACCENT).pack(side="left", padx=2)
        btn(t("btn_done"), lambda: self.set_visit_status("Ολοκληρώθηκε" if CURRENT_LANG=="el" else "Completed"), C_SUCCESS).pack(side="left", padx=2)
        btn(t("btn_cancel_v"), lambda: self.set_visit_status("Ακυρώθηκε" if CURRENT_LANG=="el" else "Cancelled"), C_WARNING).pack(side="left", padx=2)
        btn(t("btn_delete"), self.delete_visit, C_DANGER).pack(side="left", padx=2)

        Label(top, text=t("status_lbl"), bg=C_BG, fg=C_MUTED).pack(side="left", padx=(14, 4))
        self.visit_filter = StringVar(value=t("visit_filters")[0])
        Combobox(top, textvariable=self.visit_filter,
                 values=t("visit_filters"),
                 width=16, state="readonly").pack(side="left")
        self.visit_filter.trace_add("write", lambda *a: self.refresh_visits())

        self.cal_filter_date = None

        tree_frame = Frame(right, bg=C_BG)
        tree_frame.pack(fill="both", expand=True)

        cols = t("visit_cols")
        self.visits_tree = Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.visits_tree.heading(c, text=c)
            self.visits_tree.column(c, width=95 if c not in ("Πελάτης", "Ακίνητο", "Σημειώσεις", "Client", "Property", "Notes") else 150, anchor="w")
        vsb = Scrollbar(tree_frame, orient="vertical", command=self.visits_tree.yview)
        self.visits_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.visits_tree.pack(fill="both", expand=True)
        self.visits_tree.bind("<Double-1>", lambda e: self.edit_visit_dialog())

    def _on_calendar_select(self, event=None):
        if not HAS_TKCALENDAR:
            return
        self.cal_filter_date = self.cal.get_date()
        self.visit_filter.set(t("visit_filters")[0])
        self.refresh_visits()
        self.set_status(f"Filter date: {self.cal_filter_date}")

    def _cal_today(self):
        if HAS_TKCALENDAR:
            self.cal.selection_set(datetime.now().date())
            self._on_calendar_select()

    def _clear_cal_filter(self):
        self.cal_filter_date = None
        self.refresh_visits()
        self.set_status("Filter cleared")

    def _mark_calendar_events(self):
        if not HAS_TKCALENDAR or not hasattr(self, "cal"):
            return
        try:
            self.cal.calevent_remove("all")
        except Exception:
            pass
        df = load_visits()
        for _, row in df.iterrows():
            try:
                d = datetime.strptime(str(row["Ημερομηνία"]), "%d/%m/%Y").date()
                st = str(row.get("Κατάσταση", ""))
                tag = "done" if "Ολοκληρώθηκε" in st or "Completed" in st else ("cancel" if "Ακυρώθηκε" in st or "Cancelled" in st else "pending")
                self.cal.calevent_create(d, f"{row['Ώρα']} {row['Πελάτης']}", tag)
            except Exception:
                pass
        try:
            self.cal.tag_config("pending", background="#fed7d7", foreground="#c53030")
            self.cal.tag_config("done", background="#c6f6d5", foreground="#276749")
            self.cal.tag_config("cancel", background="#e2e8f0", foreground="#718096")
        except Exception:
            pass

    def refresh_visits(self):
        for item in self.visits_tree.get_children():
            self.visits_tree.delete(item)
        df = load_visits()
        if df.empty:
            self._mark_calendar_events()
            return

        f = self.visit_filter.get() if hasattr(self, "visit_filter") else t("visit_filters")[0]
        today = datetime.now().date()
        cal_date = getattr(self, "cal_filter_date", None)

        filters = t("visit_filters")
        for _, row in df.iterrows():
            status = str(row.get("Κατάσταση", ""))
            date_str = str(row.get("Ημερομηνία", ""))
            show = True

            if cal_date:
                if date_str != cal_date:
                    show = False
            elif f == filters[1] and "Προγραμματισμένη" not in status and "Scheduled" not in status:
                show = False
            elif f == filters[4] and "Ολοκληρώθηκε" not in status and "Completed" not in status:
                show = False
            elif f == filters[5] and "Ακυρώθηκε" not in status and "Cancelled" not in status:
                show = False
            elif f in (filters[2], filters[3]):
                try:
                    d = datetime.strptime(date_str, "%d/%m/%Y").date()
                    if f == filters[2] and d != today:
                        show = False
                    if f == filters[3] and not (today <= d <= today + timedelta(days=7)):
                        show = False
                except Exception:
                    show = False

            if show:
                self.visits_tree.insert("", "end", values=(
                    row["ID"], row["Ημερομηνία"], row["Ώρα"], row["Πελάτης"],
                    row["Ακίνητο"], row["Κατάσταση"], row["Σημειώσεις"]
                ))
        self._mark_calendar_events()

    def _get_selected_visit_id(self):
        sel = self.visits_tree.selection()
        if not sel:
            messagebox.showwarning("Προσοχή", "Επιλέξτε πρώτα μια επίσκεψη." if CURRENT_LANG=="el" else "Please select a visit first.")
            return None
        return safe_int(self.visits_tree.item(sel[0])["values"][0])

    def add_visit_dialog(self):
        self._visit_form_dialog(None)

    def edit_visit_dialog(self):
        vid = self._get_selected_visit_id()
        if vid is None:
            return
        df = load_visits()
        row = df[df["ID"] == vid]
        if row.empty:
            return
        self._visit_form_dialog(row.iloc[0])

    def _visit_form_dialog(self, existing):
        win = Toplevel(self)
        win.title("Επεξεργασία Επίσκεψης" if existing is not None else "Νέα Επίσκεψη")
        win.geometry("540x460")
        win.transient(self)
        win.grab_set()
        win.configure(bg=C_BG)

        df_c = load_clients()
        df_p = load_properties()
        client_names = [f"{r['ID']} – {r['Όνομα']}" for _, r in df_c.iterrows()]
        prop_names = [f"{r['ID']} – {r['Διεύθυνση']}" for _, r in df_p.iterrows()]

        Label(win, text="Ημερομηνία:" if CURRENT_LANG=="el" else "Date:", bg=C_BG, font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=16, pady=7)
        if HAS_TKCALENDAR:
            date_entry = DateEntry(win, width=18, font=("Segoe UI", 10),
                                   date_pattern="dd/mm/yyyy", background=C_PRIMARY,
                                   foreground="white", headersbackground=C_ACCENT)
            date_entry.grid(row=0, column=1, sticky="w", padx=16, pady=7)
            if existing is not None:
                try:
                    date_entry.set_date(datetime.strptime(str(existing["Ημερομηνία"]), "%d/%m/%Y"))
                except Exception:
                    pass
        else:
            date_entry = Entry(win, width=22, font=("Segoe UI", 10))
            date_entry.grid(row=0, column=1, sticky="w", padx=16, pady=7)
            date_entry.insert(0, existing["Ημερομηνία"] if existing is not None else datetime.now().strftime("%d/%m/%Y"))

        Label(win, text="Ώρα:" if CURRENT_LANG=="el" else "Time:", bg=C_BG, font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=16, pady=7)
        e_time = Entry(win, width=22, font=("Segoe UI", 10))
        e_time.grid(row=1, column=1, sticky="w", padx=16, pady=7)
        e_time.insert(0, existing["Ώρα"] if existing is not None else "18:00")

        Label(win, text="Πελάτης:" if CURRENT_LANG=="el" else "Client:", bg=C_BG, font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w", padx=16, pady=7)
        client_var = StringVar()
        cb_client = Combobox(win, textvariable=client_var, values=client_names, width=36, state="readonly")
        cb_client.grid(row=2, column=1, sticky="w", padx=16, pady=7)
        if existing is not None and client_names:
            for n in client_names:
                if n.startswith(str(existing.get("Πελάτης_ID", "")) + " –"):
                    client_var.set(n)
                    break

        Label(win, text="Ακίνητο:" if CURRENT_LANG=="el" else "Property:", bg=C_BG, font=("Segoe UI", 10)).grid(row=3, column=0, sticky="w", padx=16, pady=7)
        prop_var = StringVar()
        cb_prop = Combobox(win, textvariable=prop_var, values=prop_names, width=36, state="readonly")
        cb_prop.grid(row=3, column=1, sticky="w", padx=16, pady=7)
        if existing is not None and prop_names:
            for n in prop_names:
                if n.startswith(str(existing.get("Ακίνητο_ID", "")) + " –"):
                    prop_var.set(n)
                    break

        Label(win, text="Κατάσταση:" if CURRENT_LANG=="el" else "Status:", bg=C_BG, font=("Segoe UI", 10)).grid(row=4, column=0, sticky="w", padx=16, pady=7)
        status_var = StringVar()
        cb_status = Combobox(win, textvariable=status_var, values=VISIT_STATUSES, width=36, state="readonly")
        cb_status.grid(row=4, column=1, sticky="w", padx=16, pady=7)
        if existing is not None:
            status_var.set(existing.get("Κατάσταση", "Προγραμματισμένη"))
        else:
            cb_status.current(0)

        Label(win, text="Σημειώσεις:" if CURRENT_LANG=="el" else "Notes:", bg=C_BG, font=("Segoe UI", 10)).grid(row=5, column=0, sticky="w", padx=16, pady=7)
        e_notes = Entry(win, width=38, font=("Segoe UI", 10))
        e_notes.grid(row=5, column=1, sticky="w", padx=16, pady=7)
        if existing is not None:
            e_notes.insert(0, str(existing.get("Σημειώσεις", "") or ""))

        def save():
            if HAS_TKCALENDAR:
                date_s = date_entry.get_date().strftime("%d/%m/%Y")
            else:
                date_s = date_entry.get().strip()
            time_s = e_time.get().strip()
            if not date_s or not client_var.get() or not prop_var.get():
                messagebox.showerror("Σφάλμα", "Required fields missing.", parent=win)
                return
            try:
                cid = int(client_var.get().split("–")[0].strip())
                cname = client_var.get().split("–", 1)[1].strip()
                pid = int(prop_var.get().split("–")[0].strip())
                pname = prop_var.get().split("–", 1)[1].strip()
            except Exception:
                return

            df = load_visits()
            if existing is not None:
                vid = safe_int(existing["ID"])
                idx_list = df.index[df["ID"] == vid].tolist()
                if not idx_list:
                    return
                idx = idx_list[0]
                df.at[idx, "Ημερομηνία"] = date_s
                df.at[idx, "Ώρα"] = time_s
                df.at[idx, "Πελάτης_ID"] = str(cid)
                df.at[idx, "Πελάτης"] = cname
                df.at[idx, "Ακίνητο_ID"] = str(pid)
                df.at[idx, "Ακίνητο"] = pname
                df.at[idx, "Κατάσταση"] = status_var.get()
                df.at[idx, "Σημειώσεις"] = e_notes.get().strip()
                save_visits(df)
            else:
                new_row = {
                    "ID": next_id(df), "Ημερομηνία": date_s, "Ώρα": time_s,
                    "Πελάτης_ID": str(cid), "Πελάτης": cname,
                    "Ακίνητο_ID": str(pid), "Ακίνητο": pname,
                    "Κατάσταση": status_var.get(), "Σημειώσεις": e_notes.get().strip(),
                    "Ημερομηνία_Καταχώρησης": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_visits(df)
            win.destroy()
            self.refresh_all()
            self.set_status("Saved")

        btn_f = Frame(win, bg=C_BG)
        btn_f.grid(row=6, column=0, columnspan=2, pady=20)
        Button(btn_f, text=t("btn_save"), command=save, bg=C_SUCCESS, fg="white",
               font=("Segoe UI", 10, "bold"), relief="flat", padx=16, pady=6).pack(side="left", padx=8)
        Button(btn_f, text=t("btn_cancel"), command=win.destroy, bg="#718096", fg="white",
               font=("Segoe UI", 10), relief="flat", padx=16, pady=6).pack(side="left", padx=8)

    def set_visit_status(self, new_status):
        vid = self._get_selected_visit_id()
        if vid is None:
            return
        df = load_visits()
        idx_list = df.index[df["ID"] == vid].tolist()
        if not idx_list:
            return
        df.at[idx_list[0], "Κατάσταση"] = new_status
        save_visits(df)
        self.refresh_visits()
        self.set_status(f"Status → {new_status}")

    def delete_visit(self):
        vid = self._get_selected_visit_id()
        if vid is None:
            return
        if messagebox.askyesno("Επιβεβαίωση", "Διαγραφή επίσκεψης;" if CURRENT_LANG=="el" else "Delete visit?"):
            df = load_visits()
            df = df[df["ID"] != vid]
            save_visits(df)
            self.refresh_visits()
            self.set_status("Deleted")

    # ============================================================
    # ΑΝΑΦΟΡΕΣ (REPORTS)
    # ============================================================
    def _build_reports_tab(self):
        top = Frame(self.tab_reports, bg=C_BG)
        top.pack(fill="x", padx=14, pady=12)

        Button(top, text=t("btn_refresh"), command=self.refresh_reports,
               bg=C_ACCENT, fg="white", font=("Segoe UI", 10, "bold"),
               relief="flat", padx=12, pady=6).pack(side="left", padx=4)
        Button(top, text="📁 Excel", command=self.export_report_excel,
               bg=C_SUCCESS, fg="white", font=("Segoe UI", 10, "bold"),
               relief="flat", padx=12, pady=6).pack(side="left", padx=4)
        Button(top, text="📄 PDF", command=self.export_report_pdf,
               bg=C_DANGER, fg="white", font=("Segoe UI", 10, "bold"),
               relief="flat", padx=12, pady=6).pack(side="left", padx=4)

        text_frame = Frame(self.tab_reports, bg=C_BG)
        text_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.report_text = Text(text_frame, font=("Consolas", 10), bg="white",
                                fg=C_TEXT, wrap="word", relief="solid", bd=1)
        vsb = Scrollbar(text_frame, orient="vertical", command=self.report_text.yview)
        self.report_text.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.report_text.pack(fill="both", expand=True)

    def refresh_reports(self):
        df_c = load_clients()
        df_p = load_properties()
        df_v = load_visits()
        available_props = df_p[df_p["Κατάσταση"].astype(str).str.lower().str.contains("διαθέσιμο|διαθεσιμο|available", na=False)] if not df_p.empty else pd.DataFrame()
        total_val = sum(safe_float(p) for p in available_props["Τιμή"]) if not available_props.empty else 0.0
        upcoming = len(df_v[df_v["Κατάσταση"].astype(str).str.contains("Προγραμματισμένη|Scheduled", na=False)]) if not df_v.empty else 0

        if CURRENT_LANG == "el":
            lines = [
                "════════════════════════════════════════════════════════════",
                "              ΓΕΝΙΚΗ ΑΝΑΦΟΡΑ ΧΑΡΤΟΦΥΛΑΚΙΟΥ",
                f"              {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                "════════════════════════════════════════════════════════════",
                "",
                f"  • Πελάτες:                      {len(df_c)}",
                f"  • Ακίνητα:                      {len(df_p)}",
                f"  • Διαθέσιμα:                    {len(available_props)}",
                f"  • Συνολική Αξία Διαθέσιμων:     {format_currency(total_val)}",
                f"  • Προγραμματισμένες Επισκέψεις: {upcoming}",
                "",
                "────────────────────────────────────────────────────────────",
                "  ΚΑΤΑΝΟΜΗ ΑΝΑ ΤΥΠΟ",
                "────────────────────────────────────────────────────────────",
            ]
        else:
            lines = [
                "════════════════════════════════════════════════════════════",
                "              PORTFOLIO GENERAL REPORT",
                f"              {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                "════════════════════════════════════════════════════════════",
                "",
                f"  • Clients:                      {len(df_c)}",
                f"  • Properties:                   {len(df_p)}",
                f"  • Available:                    {len(available_props)}",
                f"  • Available Value:              {format_currency(total_val)}",
                f"  • Scheduled Visits:             {upcoming}",
                "",
                "────────────────────────────────────────────────────────────",
                "  DISTRIBUTION BY TYPE",
                "────────────────────────────────────────────────────────────",
            ]

        if not df_p.empty and "Τύπος" in df_p.columns:
            for t, c in df_p["Τύπος"].value_counts().items():
                lines.append(f"    {str(t):<24} {c}")
        else:
            lines.append("    (no data)")

        lines += ["", "────────────────────────────────────────────────────────────",
                  "  ΚΑΤΑΝΟΜΗ ΑΝΑ ΚΑΤΑΣΤΑΣΗ" if CURRENT_LANG=="el" else "  DISTRIBUTION BY STATUS",
                  "────────────────────────────────────────────────────────────"]
        if not df_p.empty and "Κατάσταση" in df_p.columns:
            for t, c in df_p["Κατάσταση"].value_counts().items():
                lines.append(f"    {str(t):<24} {c}")
        else:
            lines.append("    (no data)")

        self.report_text.config(state="normal")
        self.report_text.delete("1.0", "end")
        self.report_text.insert("1.0", "\n".join(lines))
        self.report_text.config(state="disabled")

    def export_report_excel(self):
        try:
            ensure_data_dir()
            out = REPORTS_DIR / f"anafora_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            with pd.ExcelWriter(out, engine="openpyxl") as writer:
                load_clients().to_excel(writer, sheet_name="Clients" if CURRENT_LANG=="en" else "Πελάτες", index=False)
                load_properties().to_excel(writer, sheet_name="Properties" if CURRENT_LANG=="en" else "Ακίνητα", index=False)
                load_visits().to_excel(writer, sheet_name="Visits" if CURRENT_LANG=="en" else "Επισκέψεις", index=False)
            messagebox.showinfo("Excel", f"Saved:\n{out}")
            self.set_status("Excel OK")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_report_pdf(self):
        if not HAS_REPORTLAB:
            messagebox.showerror("Error", "pip install reportlab")
            return
        try:
            ensure_data_dir()
            out = REPORTS_DIR / f"anafora_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            doc = SimpleDocTemplate(str(out), pagesize=A4,
                                    rightMargin=1.6*cm, leftMargin=1.6*cm,
                                    topMargin=1.4*cm, bottomMargin=1.4*cm)
            styles = getSampleStyleSheet()
            title = ParagraphStyle("T", parent=styles["Heading1"], fontSize=16,
                                   textColor=colors.HexColor("#1a365d"))
            normal = styles["Normal"]
            story = [Paragraph("Real Estate Assistant – Report" if CURRENT_LANG=="en" else "Μεσιτικό Βοήθημα – Γενική Αναφορά", title),
                     Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), normal),
                     Spacer(1, 14)]

            df_c, df_p, df_v = load_clients(), load_properties(), load_visits()
            avail = df_p[df_p["Κατάσταση"].astype(str).str.lower().str.contains("διαθέσιμο|διαθεσιμο|available", na=False)] if not df_p.empty else pd.DataFrame()
            total_val = sum(safe_float(p) for p in avail["Τιμή"]) if not avail.empty else 0.0
            upcoming = len(df_v[df_v["Κατάσταση"].astype(str).str.contains("Προγραμματισμένη|Scheduled", na=False)]) if not df_v.empty else 0

            if CURRENT_LANG == "el":
                data = [["Μετρική", "Τιμή"],
                        ["Πελάτες", str(len(df_c))],
                        ["Ακίνητα", str(len(df_p))],
                        ["Διαθέσιμα", str(len(avail))],
                        ["Αξία Διαθέσιμων", format_currency(total_val)],
                        ["Προγραμματισμένες Επισκέψεις", str(upcoming)]]
            else:
                data = [["Metric", "Value"],
                        ["Clients", str(len(df_c))],
                        ["Properties", str(len(df_p))],
                        ["Available", str(len(avail))],
                        ["Available Value", format_currency(total_val)],
                        ["Scheduled Visits", str(upcoming)]]

            t = Table(data, colWidths=[8*cm, 6*cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a365d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f7fafc")),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 18))

            doc.build(story)
            messagebox.showinfo("PDF", f"Saved:\n{out}")
            self.set_status("PDF OK")
        except Exception as e:
            messagebox.showerror("PDF Error", str(e))

    # ============================================================
    # ΥΠΟΛΟΓΙΣΜΟΙ (CALCULATORS)
    # ============================================================
    def _build_calc_tab(self):
        container = Frame(self.tab_calc, bg=C_BG)
        container.pack(fill="both", expand=True, padx=16, pady=14)

        # Loan
        loan = LabelFrame(container, text=t("loan_title"), font=("Segoe UI", 11, "bold"),
                          bg=C_CARD, fg=C_PRIMARY, padx=14, pady=12)
        loan.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        Label(loan, text="Amount (€):" if CURRENT_LANG=="en" else "Ποσό (€):", bg=C_CARD).grid(row=0, column=0, sticky="w", pady=3)
        self.e_loan_amount = Entry(loan, width=14)
        self.e_loan_amount.grid(row=0, column=1, padx=8, pady=3)
        self.e_loan_amount.insert(0, "100000")

        Label(loan, text="Rate %:" if CURRENT_LANG=="en" else "Επιτόκιο %:", bg=C_CARD).grid(row=1, column=0, sticky="w", pady=3)
        self.e_loan_rate = Entry(loan, width=14)
        self.e_loan_rate.grid(row=1, column=1, padx=8, pady=3)
        self.e_loan_rate.insert(0, "3.5")

        Label(loan, text="Years:" if CURRENT_LANG=="en" else "Έτη:", bg=C_CARD).grid(row=2, column=0, sticky="w", pady=3)
        self.e_loan_years = Entry(loan, width=14)
        self.e_loan_years.grid(row=2, column=1, padx=8, pady=3)
        self.e_loan_years.insert(0, "20")

        Button(loan, text=t("calc_btn"), command=self._calc_loan,
               bg=C_ACCENT, fg="white", relief="flat").grid(row=3, column=0, columnspan=2, pady=8)
        self.lbl_loan_result = Label(loan, text="Monthly Payment: —" if CURRENT_LANG=="en" else "Μηνιαία Δόση: —", font=("Segoe UI", 10, "bold"),
                                     bg=C_CARD, fg=C_SUCCESS, wraplength=260)
        self.lbl_loan_result.grid(row=4, column=0, columnspan=2, pady=4)
        Button(loan, text=t("amort_btn"), command=self._show_amortization,
               bg="#4a5568", fg="white", relief="flat").grid(row=5, column=0, columnspan=2, pady=4)

        # Yield
        yf = LabelFrame(container, text=t("yield_title"), font=("Segoe UI", 11, "bold"),
                        bg=C_CARD, fg=C_PRIMARY, padx=14, pady=12)
        yf.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

        Label(yf, text="Purchase Price (€):" if CURRENT_LANG=="en" else "Τιμή Αγοράς (€):", bg=C_CARD).grid(row=0, column=0, sticky="w", pady=3)
        self.e_yield_price = Entry(yf, width=14)
        self.e_yield_price.grid(row=0, column=1, padx=8, pady=3)
        self.e_yield_price.insert(0, "150000")

        Label(yf, text="Monthly Rent (€):" if CURRENT_LANG=="en" else "Μηνιαίο Ενοίκιο (€):", bg=C_CARD).grid(row=1, column=0, sticky="w", pady=3)
        self.e_yield_rent = Entry(yf, width=14)
        self.e_yield_rent.grid(row=1, column=1, padx=8, pady=3)
        self.e_yield_rent.insert(0, "650")

        Label(yf, text="Annual Expenses (€):" if CURRENT_LANG=="en" else "Ετήσια Έξοδα (€):", bg=C_CARD).grid(row=2, column=0, sticky="w", pady=3)
        self.e_yield_expenses = Entry(yf, width=14)
        self.e_yield_expenses.grid(row=2, column=1, padx=8, pady=3)
        self.e_yield_expenses.insert(0, "1200")

        Button(yf, text=t("calc_btn"), command=self._calc_yield,
               bg=C_ACCENT, fg="white", relief="flat").grid(row=3, column=0, columnspan=2, pady=8)
        self.lbl_yield_result = Label(yf, text="Yield: —", font=("Segoe UI", 10, "bold"),
                                      bg=C_CARD, fg=C_SUCCESS, wraplength=260)
        self.lbl_yield_result.grid(row=4, column=0, columnspan=2, pady=4)

        # Costs
        cf = LabelFrame(container, text=t("costs_title"), font=("Segoe UI", 11, "bold"),
                        bg=C_CARD, fg=C_PRIMARY, padx=14, pady=12)
        cf.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=8)

        Label(cf, text="Property Price (€):" if CURRENT_LANG=="en" else "Αξία Ακινήτου (€):", bg=C_CARD).grid(row=0, column=0, sticky="w", pady=3)
        self.e_cost_price = Entry(cf, width=16)
        self.e_cost_price.grid(row=0, column=1, padx=8, pady=3)
        self.e_cost_price.insert(0, "120000")

        Label(cf, text="Tax %:", bg=C_CARD).grid(row=1, column=0, sticky="w", pady=3)
        self.e_cost_tax = Entry(cf, width=16)
        self.e_cost_tax.grid(row=1, column=1, padx=8, pady=3)
        self.e_cost_tax.insert(0, "3.09")

        Label(cf, text="Agent %:" if CURRENT_LANG=="en" else "Μεσιτικά %:", bg=C_CARD).grid(row=2, column=0, sticky="w", pady=3)
        self.e_cost_realtor = Entry(cf, width=16)
        self.e_cost_realtor.grid(row=2, column=1, padx=8, pady=3)
        self.e_cost_realtor.insert(0, "2.0")

        Label(cf, text="Notary %:" if CURRENT_LANG=="en" else "Συμβολαιογράφος %:", bg=C_CARD).grid(row=3, column=0, sticky="w", pady=3)
        self.e_cost_notary = Entry(cf, width=16)
        self.e_cost_notary.grid(row=3, column=1, padx=8, pady=3)
        self.e_cost_notary.insert(0, "1.5")

        Button(cf, text=t("calc_btn"), command=self._calc_costs,
               bg=C_SUCCESS, fg="white", relief="flat").grid(row=4, column=0, columnspan=2, pady=8)
        self.lbl_cost_result = Label(cf, text="Extras: —", font=("Segoe UI", 10, "bold"),
                                     bg=C_CARD, fg=C_PRIMARY, wraplength=520, justify="left")
        self.lbl_cost_result.grid(row=5, column=0, columnspan=2, pady=4)

        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)

    def _calc_loan(self):
        amount = safe_float(self.e_loan_amount.get())
        rate_annual = safe_float(self.e_loan_rate.get())
        years = safe_int(self.e_loan_years.get())
        if amount <= 0 or rate_annual <= 0 or years <= 0:
            self.lbl_loan_result.config(text="Invalid values.")
            return
        r = (rate_annual / 100) / 12
        n = years * 12
        monthly = (amount * r * (1 + r)**n) / ((1 + r)**n - 1)
        total_paid = monthly * n
        self.lbl_loan_result.config(
            text=f"{'Monthly' if CURRENT_LANG=='en' else 'Μηνιαία Δόση'}: {format_currency(monthly)}\nTotal: {format_currency(total_paid)}"
        )

    def _show_amortization(self):
        amount = safe_float(self.e_loan_amount.get())
        rate_annual = safe_float(self.e_loan_rate.get())
        years = safe_int(self.e_loan_years.get())
        if amount <= 0 or rate_annual <= 0 or years <= 0:
            return
        r = (rate_annual / 100) / 12
        n = years * 12
        monthly = (amount * r * (1 + r)**n) / ((1 + r)**n - 1)

        win = Toplevel(self)
        win.title("Amortization" if CURRENT_LANG=="en" else "Πίνακας Αποπληρωμής")
        win.geometry("720x520")
        cols = ("Month", "Payment", "Interest", "Principal", "Balance") if CURRENT_LANG=="en" else ("Μήνας", "Δόση", "Τόκος", "Κεφάλαιο", "Υπόλοιπο")
        tree = Treeview(win, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=120, anchor="e")
        vsb = Scrollbar(win, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        balance = amount
        for m in range(1, n + 1):
            interest = balance * r
            principal = monthly - interest
            balance = max(0, balance - principal)
            tree.insert("", "end", values=(
                m, f"{monthly:,.2f}", f"{interest:,.2f}",
                f"{principal:,.2f}", f"{balance:,.2f}"
            ))

    def _calc_yield(self):
        price = safe_float(self.e_yield_price.get())
        rent = safe_float(self.e_yield_rent.get())
        expenses = safe_float(self.e_yield_expenses.get())
        if price <= 0 or rent <= 0:
            self.lbl_yield_result.config(text="Invalid values.")
            return
        annual_rent = rent * 12
        gross = (annual_rent / price) * 100
        net = ((annual_rent - expenses) / price) * 100
        self.lbl_yield_result.config(
            text=f"Annual: {format_currency(annual_rent)}\nGross: {gross:.2f}%\nNet: {net:.2f}%"
        )

    def _calc_costs(self):
        price = safe_float(self.e_cost_price.get())
        tax_pct = safe_float(self.e_cost_tax.get())
        realtor_pct = safe_float(self.e_cost_realtor.get())
        notary_pct = safe_float(self.e_cost_notary.get())
        if price <= 0:
            return
        tax = price * (tax_pct / 100)
        realtor = price * (realtor_pct / 100)
        notary = price * (notary_pct / 100)
        total_extras = tax + realtor + notary
        total_sum = price + total_extras
        self.lbl_cost_result.config(
            text=f"Extras: {format_currency(total_extras)}\n➡️ Total Cost: {format_currency(total_sum)}"
        )

    # ============================================================
    # ΓΕΝΙΚΑ
    # ============================================================
    def refresh_all(self):
        self.refresh_clients()
        self.refresh_properties()
        self.refresh_visits()
        self.refresh_reports()
        self.refresh_dashboard()
        self.set_status("Refreshed")

    def on_close(self):
        self.destroy()


if __name__ == "__main__":
    ensure_data_dir()
    app = MesitikoApp()
    app.mainloop()
