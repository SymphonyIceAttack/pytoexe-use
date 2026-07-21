import sys
import sqlite3
import random
import csv
import shutil
from datetime import datetime, date
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, QLineEdit,
                             QPushButton, QMessageBox, QMainWindow, QGridLayout,
                             QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QWidget, QTabWidget, QDoubleSpinBox,
                             QSpinBox, QFormLayout, QApplication, QFileDialog, QDateEdit,
                             QFrame, QSizePolicy, QGroupBox, QStyledItemDelegate, QCompleter)
from PyQt5.QtCore import Qt, QTimer, QDate
from PyQt5.QtGui import QFont, QColor

# ==================== المندوب الخاص بالاقتراح التلقائي ====================
class AutocompleteDelegate(QStyledItemDelegate):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.items = items
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        completer = QCompleter(self.items, editor)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        editor.setCompleter(completer)
        editor.setStyleSheet(TABLE_INPUT_STYLE)
        return editor

# ==================== قاعدة البيانات ====================

def init_db():
    conn = sqlite3.connect('lina_store.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, color TEXT,
                purchase_price REAL, sale_price REAL, quantity INTEGER)''')
    try: c.execute("ALTER TABLE products ADD COLUMN avg_cost REAL DEFAULT 0")
    except: pass
    try: c.execute("ALTER TABLE products ADD COLUMN last_purchase_price REAL DEFAULT 0")
    except: pass

    c.execute('''CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER, product_name TEXT, user_name TEXT,
                customer_name TEXT, customer_phone TEXT,
                sale_price REAL, discount REAL, quantity INTEGER, total REAL, date TEXT, payment_method TEXT DEFAULT 'كاش')''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT, amount REAL, note TEXT, date TEXT, safe_name TEXT DEFAULT 'كاش')''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, phone TEXT UNIQUE, total_spent REAL DEFAULT 0, last_visit TEXT, balance REAL DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS raffle_winners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, phone TEXT, date TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY, store_name TEXT, alert_limit INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER, product_id INTEGER, product_name TEXT,
                customer_name TEXT, quantity INTEGER, total REAL, reason TEXT, date TEXT, safe_name TEXT DEFAULT 'كاش')''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS daily_reset (
                id INTEGER PRIMARY KEY, last_reset TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, phone TEXT UNIQUE, address TEXT, notes TEXT,
                balance REAL DEFAULT 0, total_purchases REAL DEFAULT 0,
                total_paid REAL DEFAULT 0, invoices_count INTEGER DEFAULT 0,
                last_deal TEXT, is_active INTEGER DEFAULT 1)''')

    c.execute('''CREATE TABLE IF NOT EXISTS purchase_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inv_number TEXT UNIQUE, date TEXT, supplier_id INTEGER,
                supplier_name TEXT, total REAL, paid REAL, remaining REAL,
                payment_method TEXT, notes TEXT, status TEXT, user_name TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER, product_id INTEGER, product_name TEXT,
                color TEXT, purchase_price REAL, sale_price REAL, quantity INTEGER, total REAL, notes TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS purchase_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_inv_id INTEGER, date TEXT, supplier_id INTEGER,
                total_returned REAL, amount_refunded REAL, reason TEXT, user_name TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS supplier_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER, date TEXT, type TEXT, ref_id INTEGER,
                debit REAL, credit REAL, balance_after REAL, note TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS supplier_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER, date TEXT, amount REAL, 
                payment_method TEXT, safe_id INTEGER, note TEXT, user_name TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS cash_boxes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE, balance REAL DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS cash_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                safe_name TEXT, date TEXT, type TEXT, ref_id TEXT,
                description TEXT, amount REAL, balance_before REAL, balance_after REAL, user_name TEXT)''')
                
    c.execute('''CREATE TABLE IF NOT EXISTS cash_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_safe TEXT, to_safe TEXT, amount REAL, date TEXT, note TEXT, user_name TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT, action TEXT, details TEXT, user_name TEXT)''')

    c.execute("SELECT COUNT(*) FROM settings")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO settings (id, store_name, alert_limit) VALUES (1, 'لينا ستور', 5)")
    c.execute("SELECT COUNT(*) FROM daily_reset")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO daily_reset (id, last_reset) VALUES (1, '')")

    c.execute("SELECT COUNT(*) FROM cash_boxes")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO cash_boxes (name, balance) VALUES ('كاش', 0), ('إنستاباي', 0), ('محفظة', 0), ('بنك', 0)")

    conn.commit(); conn.close()

# ==================== أرقام وتحويلات ====================

HINDI_MAP = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')

def normalize(text):
    return str(text).translate(HINDI_MAP)

def fmt(val):
    try: return f"{float(normalize(str(val))):,.2f}"
    except: return str(val)

# ==================== ألوان اللوجو والثيم ====================

TEAL_DARK  = "#1E3F3E"
TEAL_MID   = "#2E5D5C"
TEAL_LIGHT = "#3D7A78"
GOLD       = "#C9956C"
GOLD_DARK  = "#B8825A"
GOLD_LIGHT = "#D4A574"
CREAM      = "#F5EDE4"
CREAM2     = "#EDD5BE"
WHITE      = "#FFFFFF"
TEXT_DARK  = "#1A2E2D"
RED        = "#B71C1C"
RED2       = "#C62828"

INPUT_STYLE = f"padding:9px 12px; font-size:14px; border:2px solid {GOLD_LIGHT}; border-radius:8px; background:{WHITE}; color:{TEXT_DARK};"
BTN = "QPushButton{{background:{bg};color:white;font-weight:bold;padding:10px 18px;border-radius:8px;border:none;font-size:13px;}}QPushButton:hover{{background:{hv};}}"
TABLE_INPUT_STYLE = f"border:1px solid {TEAL_LIGHT}; background:{WHITE}; color:{TEXT_DARK}; padding:2px;"

GLOBAL_STYLE = f"""
QMainWindow{{background:{CREAM};}} QDialog{{background:{CREAM};}}
QWidget{{font-family:'Segoe UI',Tahoma,Arial,sans-serif;font-size:13px;color:{TEXT_DARK};}}
QTabWidget::pane{{border:2px solid {TEAL_MID};border-radius:10px;top:-1px;background:{WHITE};}}
QTabBar::tab{{background:{CREAM2};color:{TEAL_DARK};padding:10px 20px;margin-right:3px;
    border-top-left-radius:8px;border-top-right-radius:8px;font-weight:bold;font-size:13px;}}
QTabBar::tab:selected{{background:{TEAL_MID};color:{WHITE};}}
QTabBar::tab:hover{{background:{GOLD};color:{WHITE};}}
QTableWidget{{background:{WHITE};gridline-color:{CREAM2};border:1px solid {CREAM2};border-radius:8px;
    alternate-background-color:#F9F4EF;selection-background-color:{TEAL_MID};selection-color:white;color:{TEXT_DARK};}}
QHeaderView::section{{background:{TEAL_DARK};color:{GOLD_LIGHT};padding:9px;border:none;font-weight:bold;font-size:13px;}}
QScrollBar:vertical{{background:{CREAM};width:10px;border-radius:5px;}}
QScrollBar::handle:vertical{{background:{GOLD};border-radius:5px;}}
QComboBox{{padding:8px;border:2px solid {GOLD_LIGHT};border-radius:8px;background:white;color:{TEXT_DARK};}}
QComboBox::drop-down{{border:none;}}
QSpinBox,QDoubleSpinBox{{padding:8px;border:2px solid {GOLD_LIGHT};border-radius:8px;background:white;color:{TEXT_DARK};}}
QDateEdit{{padding:8px;border:2px solid {GOLD_LIGHT};border-radius:8px;background:white;color:{TEXT_DARK};}}
"""

def style_table(t, edit=False):
    t.setAlternatingRowColors(True)
    t.verticalHeader().setVisible(False)
    t.verticalHeader().setDefaultSectionSize(38)
    t.setSelectionBehavior(QTableWidget.SelectRows)
    if not edit:
        t.setEditTriggers(QTableWidget.NoEditTriggers)

def make_search_bar(placeholder):
    row = QHBoxLayout(); row.setSpacing(6)
    icon = QLabel("🔍"); icon.setStyleSheet("font-size:17px;")
    inp = QLineEdit(); inp.setPlaceholderText(placeholder)
    inp.setStyleSheet(INPUT_STYLE + f"border-color:{TEAL_LIGHT};")
    inp.setMinimumHeight(40)
    row.addWidget(icon); row.addWidget(inp)
    frame = QFrame()
    frame.setStyleSheet(f"background:{CREAM2};border-radius:10px;padding:4px;")
    frame.setLayout(row)
    return frame, inp

def make_date_bar(label="📅 عرض يوم:", show_all_btn=True):
    frame = QFrame()
    frame.setStyleSheet(f"background:{CREAM2};border-radius:10px;padding:4px;")
    row = QHBoxLayout(); row.setContentsMargins(8,6,8,6); row.setSpacing(8)
    lbl = QLabel(label); lbl.setStyleSheet(f"font-size:14px; font-weight:bold; color:{TEAL_DARK};")
    date_edit = QDateEdit(QDate.currentDate()); date_edit.setCalendarPopup(True); date_edit.setMinimumHeight(38)
    btn_search = QPushButton("🔍 بحث"); btn_search.setStyleSheet(BTN.format(bg=TEAL_MID, hv=TEAL_DARK))
    row.addWidget(lbl); row.addWidget(date_edit); row.addWidget(btn_search)
    btn_all = None
    if show_all_btn:
        btn_all = QPushButton("📋 الكل"); btn_all.setStyleSheet(BTN.format(bg=GOLD_DARK, hv=GOLD))
        row.addWidget(btn_all)
    row.addStretch()
    frame.setLayout(row)
    return frame, date_edit, btn_search, btn_all

# ==================== عمليات الخزنة المركزية ====================

def log_audit(user_name, action, details, conn=None):
    close_conn = False
    if conn is None:
        conn = sqlite3.connect('lina_store.db')
        close_conn = True
    c = conn.cursor()
    c.execute("INSERT INTO audit_logs (date, action, details, user_name) VALUES (?, ?, ?, ?)",
                 (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, details, user_name))
    if close_conn:
        conn.commit()
        conn.close()

def update_safe_balance(safe_name, amount, trans_type, ref_id, description, user_name, conn=None):
    if amount == 0: return True
    close_conn = False
    if conn is None:
        conn = sqlite3.connect('lina_store.db')
        close_conn = True
    c = conn.cursor()
    c.execute("SELECT balance FROM cash_boxes WHERE name=?", (safe_name,))
    res = c.fetchone()
    if not res:
        if close_conn: conn.close()
        return False
    balance_before = res[0]
    balance_after = balance_before + amount
    c.execute("UPDATE cash_boxes SET balance=? WHERE name=?", (balance_after, safe_name))
    c.execute("""INSERT INTO cash_transactions 
                 (safe_name, date, type, ref_id, description, amount, balance_before, balance_after, user_name)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (safe_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), trans_type, str(ref_id),
               description, amount, balance_before, balance_after, user_name))
    if close_conn:
        conn.commit()
        conn.close()
    return True

# ==================== شاشة الدخول ====================

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("لينا ستور")
        self.setFixedSize(420, 460)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet(f"background:{TEAL_DARK};")
        self.setLayoutDirection(Qt.RightToLeft)
        self.selected_user = "أحمد عرفة"
        self._build()

    def _build(self):
        layout = QVBoxLayout(); layout.setSpacing(16); layout.setContentsMargins(35,30,35,30)

        logo = QFrame()
        logo.setStyleSheet(f"background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {TEAL_MID},stop:1 {TEAL_DARK});border-radius:18px;border:2px solid {GOLD};")
        ll = QVBoxLayout(); ll.setContentsMargins(16,20,16,20); ll.setSpacing(6)
        t1 = QLabel("LINA  STORE"); t1.setStyleSheet(f"font-size:28px;font-weight:bold;color:{GOLD};background:transparent;letter-spacing:5px;"); t1.setAlignment(Qt.AlignCenter)
        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setStyleSheet(f"background:{GOLD};max-height:1px;")
        t2 = QLabel("نظام إدارة المحل المتكامل"); t2.setStyleSheet(f"font-size:13px;color:{CREAM};background:transparent;"); t2.setAlignment(Qt.AlignCenter)
        ll.addWidget(t1); ll.addWidget(sep); ll.addWidget(t2); logo.setLayout(ll)
        layout.addWidget(logo)

        card = QFrame(); card.setStyleSheet(f"background:{WHITE};border-radius:14px;")
        cl = QVBoxLayout(); cl.setContentsMargins(20,16,20,16); cl.setSpacing(10)
        for lbl_text, attr, is_pw in [("اختر المستخدم:", None, False), ("كلمة المرور:", "password_input", True)]:
            l = QLabel(lbl_text); l.setStyleSheet(f"font-weight:bold;color:{TEAL_DARK};"); cl.addWidget(l)
            if attr == "password_input":
                self.password_input = QLineEdit(); self.password_input.setEchoMode(QLineEdit.Password)
                self.password_input.setAlignment(Qt.AlignCenter); self.password_input.returnPressed.connect(self.check_login)
                cl.addWidget(self.password_input)
            else:
                self.user_combo = QComboBox(); self.user_combo.addItems(["أحمد عرفة", "أحمد محمد"]); cl.addWidget(self.user_combo)
        card.setLayout(cl); layout.addWidget(card)

        btn = QPushButton("دخول للنظام"); btn.setMinimumHeight(46); btn.clicked.connect(self.check_login)
        btn.setStyleSheet(f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {GOLD_DARK},stop:1 {GOLD});color:white;font-size:16px;font-weight:bold;padding:12px;border-radius:10px;border:none;}}QPushButton:hover{{background:{GOLD_DARK};}}")
        layout.addWidget(btn); self.setLayout(layout)

    def check_login(self):
        pw = self.password_input.text()
        if self.user_combo.currentIndex() == 0 and pw == "1234": self.selected_user = "أحمد عرفة"; self.accept()
        elif self.user_combo.currentIndex() == 1 and pw == "5678": self.selected_user = "أحمد محمد"; self.accept()
        else: QMessageBox.warning(self, "خطأ", "كلمة المرور غير صحيحة!")

# ==================== نوافذ حوار جديدة: الخزنة ====================
class TransferSafeDialog(QDialog):
    def __init__(self, user_name):
        super().__init__()
        self.user_name = user_name
        self.setWindowTitle("تحويل بين الخزن")
        self.setFixedSize(400, 300); self.setLayoutDirection(Qt.RightToLeft); self.setStyleSheet(f"background:{CREAM};")
        layout = QVBoxLayout(); layout.setSpacing(12)

        form = QFormLayout()
        self.amount_input = QDoubleSpinBox(); self.amount_input.setMaximum(1000000); self.amount_input.setDecimals(2)
        
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT name, balance FROM cash_boxes")
        self.safes = c.fetchall(); conn.close()
        
        self.from_safe = QComboBox()
        self.to_safe = QComboBox()
        for s in self.safes:
            self.from_safe.addItem(f"{s[0]} (رصيد: {fmt(s[1])})", s[0])
            self.to_safe.addItem(f"{s[0]} (رصيد: {fmt(s[1])})", s[0])

        self.note_input = QLineEdit()
        form.addRow("من خزنة:", self.from_safe)
        form.addRow("إلى خزنة:", self.to_safe)
        form.addRow("المبلغ:", self.amount_input)
        form.addRow("ملاحظة:", self.note_input)
        
        layout.addLayout(form)
        btn = QPushButton("✅ تأكيد التحويل"); btn.setStyleSheet(BTN.format(bg=GOLD_DARK, hv=GOLD))
        btn.clicked.connect(self.try_accept); layout.addWidget(btn)
        self.setLayout(layout)

    def try_accept(self):
        amount = self.amount_input.value()
        fs = self.from_safe.currentData()
        ts = self.to_safe.currentData()
        if fs == ts:
            QMessageBox.warning(self, "خطأ", "لا يمكن التحويل لنفس الخزنة!"); return
        if amount <= 0:
            QMessageBox.warning(self, "خطأ", "المبلغ يجب أن يكون أكبر من الصفر!"); return
        
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        try:
            c.execute("BEGIN TRANSACTION")
            c.execute("SELECT balance FROM cash_boxes WHERE name=?", (fs,))
            curr_bal = c.fetchone()[0]
            if curr_bal < amount:
                QMessageBox.warning(self, "خطأ", "الرصيد لا يكفي للتحويل!")
                conn.rollback(); return
            
            update_safe_balance(fs, -amount, "تحويل صادر", "", f"إلى {ts} - {self.note_input.text()}", self.user_name, conn)
            update_safe_balance(ts, amount, "تحويل وارد", "", f"من {fs} - {self.note_input.text()}", self.user_name, conn)
            
            c.execute("INSERT INTO cash_transfers (from_safe, to_safe, amount, date, note, user_name) VALUES (?,?,?,?,?,?)",
                      (fs, ts, amount, datetime.now().strftime("%Y-%m-%d %H:%M"), self.note_input.text(), self.user_name))
            log_audit(self.user_name, "تحويل خزنة", f"تم تحويل {amount} من {fs} إلى {ts}", conn=conn) 
            conn.commit()
            QMessageBox.information(self, "نجاح", "تم التحويل بنجاح!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "خطأ", str(e))
        finally:
            conn.close()

# ==================== نوافذ الحوار: الموردين والمشتريات ====================

class SupplierDialog(QDialog):
    def __init__(self, supplier=None):
        super().__init__()
        self.setWindowTitle("تعديل مورد" if supplier else "إضافة مورد جديد")
        self.setFixedSize(400, 360); self.setLayoutDirection(Qt.RightToLeft); self.setStyleSheet(f"background:{CREAM};")
        form = QFormLayout(); form.setSpacing(12)
        self.name_input = QLineEdit(); self.phone_input = QLineEdit()
        self.address_input = QLineEdit(); self.notes_input = QLineEdit()
        self.balance_input = QDoubleSpinBox(); self.balance_input.setMaximum(10000000); self.balance_input.setMinimum(-10000000)
        
        self.is_edit = supplier is not None
        if self.is_edit:
            self.sid = supplier[0]
            self.name_input.setText(str(supplier[1]))
            self.phone_input.setText(str(supplier[2]))
            self.address_input.setText(str(supplier[3]))
            self.notes_input.setText(str(supplier[4]))
            self.balance_input.setValue(float(supplier[5]))
            self.balance_input.setEnabled(False) 

        form.addRow("اسم المورد:", self.name_input)
        form.addRow("رقم الهاتف:", self.phone_input)
        form.addRow("العنوان:", self.address_input)
        form.addRow("ملاحظات:", self.notes_input)
        if not self.is_edit: form.addRow("رصيد افتتاحي له:", self.balance_input)

        btn = QPushButton("💾 حفظ"); btn.setStyleSheet(BTN.format(bg=TEAL_MID, hv=TEAL_DARK)); btn.clicked.connect(self.try_accept)
        layout = QVBoxLayout(); layout.addLayout(form); layout.addWidget(btn); self.setLayout(layout)

    def try_accept(self):
        if not self.name_input.text().strip(): QMessageBox.warning(self, "خطأ", "يرجى كتابة اسم المورد"); return
        self.accept()

    def get_data(self):
        return (self.name_input.text().strip(), self.phone_input.text().strip(),
                self.address_input.text().strip(), self.notes_input.text().strip(), self.balance_input.value())

class PurchaseInvoiceDialog(QDialog):
    def __init__(self, user_name, main_window):
        super().__init__()
        self.user_name = user_name
        self.main_window = main_window
        self.setWindowTitle("فاتورة مشتريات جديدة احترافية")
        self.setFixedSize(1000, 750)
        self.setLayoutDirection(Qt.RightToLeft); self.setStyleSheet(f"background:{CREAM};")
        self.is_updating = False

        main_layout = QVBoxLayout(); main_layout.setSpacing(10)
        
        # Header Info
        header_frame = QFrame(); header_frame.setStyleSheet(f"background:{CREAM2}; border-radius:10px; padding:10px;")
        h_layout = QHBoxLayout()
        
        form_h1 = QFormLayout(); form_h1.setContentsMargins(0,0,0,0)
        self.inv_num = QLineEdit(f"INV-{int(datetime.now().timestamp())}")
        self.inv_num.setStyleSheet(INPUT_STYLE); self.inv_num.setReadOnly(True)
        self.inv_date = QDateEdit(QDate.currentDate()); self.inv_date.setCalendarPopup(True); self.inv_date.setStyleSheet(INPUT_STYLE)
        
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT id, name FROM suppliers WHERE is_active=1 ORDER BY name")
        sups = c.fetchall(); conn.close()
        self.supplier_combo = QComboBox(); self.supplier_combo.setStyleSheet(INPUT_STYLE)
        for s in sups: self.supplier_combo.addItem(s[1], s[0])

        form_h1.addRow("رقم الفاتورة:", self.inv_num)
        form_h1.addRow("تاريخ الفاتورة:", self.inv_date)
        form_h1.addRow("المورد:", self.supplier_combo)
        
        h_layout.addLayout(form_h1)
        
        self.notes_input = QLineEdit(); self.notes_input.setPlaceholderText("ملاحظات عامة للفاتورة...")
        self.notes_input.setStyleSheet(INPUT_STYLE)
        h_layout.addWidget(QLabel("ملاحظات:")); h_layout.addWidget(self.notes_input)
        header_frame.setLayout(h_layout)
        main_layout.addWidget(header_frame)

        # Excel-like Table Setup
        self.table = QTableWidget(30, 8)
        self.table.setHorizontalHeaderLabels(["رقم المنتج", "اسم المنتج", "اللون", "سعر الشراء", "سعر البيع", "الكمية", "الإجمالي", "ملاحظات"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        style_table(self.table, edit=True)
        self.table.setStyleSheet(self.table.styleSheet() + f" QLineEdit {{ {TABLE_INPUT_STYLE} }}")
        self.table.itemChanged.connect(self.on_item_changed)
        main_layout.addWidget(self.table)
        
        # Load Autocomplete Data
        self.reload_autocompletes()
        
        # Prepare read-only Total Column (Col 6)
        self.is_updating = True
        for r in range(self.table.rowCount()):
            for c in range(8):
                item = QTableWidgetItem("")
                if c == 6:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QColor("#EFEFEF"))
                self.table.setItem(r, c, item)
        self.is_updating = False

        # Stats Counters below table
        stats_layout = QHBoxLayout()
        stats_layout.setContentsMargins(5, 5, 5, 5)
        self.lbl_items_count = QLabel("عدد الأصناف: 0")
        self.lbl_items_count.setStyleSheet("font-size:14px; font-weight:bold; color:#1E3F3E;")
        self.lbl_total_qty = QLabel("إجمالي الكمية: 0")
        self.lbl_total_qty.setStyleSheet("font-size:14px; font-weight:bold; color:#1E3F3E;")
        stats_layout.addWidget(self.lbl_items_count)
        stats_layout.addWidget(QLabel("  |  "))
        stats_layout.addWidget(self.lbl_total_qty)
        stats_layout.addStretch()
        main_layout.addLayout(stats_layout)

        # Footer Payment
        footer_frame = QFrame(); footer_frame.setStyleSheet(f"background:{TEAL_DARK}; color:white; border-radius:10px; padding:15px;")
        f_layout = QHBoxLayout()
        
        self.lbl_total = QLabel("الإجمالي: 0.00"); self.lbl_total.setStyleSheet("font-size:20px; font-weight:bold;")
        
        pay_layout = QGridLayout(); pay_layout.setContentsMargins(0,0,0,0)
        self.pay_inputs = {}
        row, col = 0, 0
        for safe in ["كاش", "إنستاباي", "محفظة", "بنك"]:
            lbl = QLabel(safe); lbl.setStyleSheet("color:white; font-weight:bold;")
            inp = QDoubleSpinBox(); inp.setMaximum(10000000); inp.setStyleSheet(INPUT_STYLE + "color:black;")
            inp.valueChanged.connect(self.calc_totals)
            self.pay_inputs[safe] = inp
            pay_layout.addWidget(lbl, row, col); pay_layout.addWidget(inp, row, col+1)
            row += 1;
            if row > 1: row = 0; col += 2
        
        self.lbl_remaining = QLabel("المتبقي (آجل): 0.00"); self.lbl_remaining.setStyleSheet("font-size:18px; font-weight:bold; color:#FFCDD2;")
        
        f_layout.addWidget(self.lbl_total)
        f_layout.addStretch()
        f_layout.addLayout(pay_layout)
        f_layout.addStretch()
        f_layout.addWidget(self.lbl_remaining)
        footer_frame.setLayout(f_layout)
        main_layout.addWidget(footer_frame)

        btn_save = QPushButton("💾 حفظ الفاتورة"); btn_save.setMinimumHeight(45)
        btn_save.setStyleSheet(BTN.format(bg=GOLD_DARK, hv=GOLD))
        btn_save.clicked.connect(self.save_invoice)
        main_layout.addWidget(btn_save)

        self.setLayout(main_layout)

    def reload_autocompletes(self):
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT id, name, color, last_purchase_price, sale_price FROM products")
        self.prods = c.fetchall(); conn.close()
        
        self.prod_by_id = {str(p[0]): p for p in self.prods}
        self.prod_by_name = {p[1]: p for p in self.prods}
        
        id_list = list(self.prod_by_id.keys())
        name_list = list(self.prod_by_name.keys())
        
        self.table.setItemDelegateForColumn(0, AutocompleteDelegate(id_list, self.table))
        self.table.setItemDelegateForColumn(1, AutocompleteDelegate(name_list, self.table))

    def on_item_changed(self, item):
        if self.is_updating: return
        row = item.row(); col = item.column()
        
        self.is_updating = True
        try:
            # Auto fill based on ID or Name
            if col == 0:
                txt = item.text().strip()
                if txt in self.prod_by_id:
                    p = self.prod_by_id[txt]
                    self.table.item(row, 1).setText(p[1])
                    self.table.item(row, 2).setText(p[2] if p[2] else "")
                    self.table.item(row, 3).setText(str(p[3]))
                    self.table.item(row, 4).setText(str(p[4]))
                    if not self.table.item(row, 5).text(): self.table.item(row, 5).setText("1")
                elif txt:
                    msg = QMessageBox.question(self, "غير موجود", f"المنتج رقم ({txt}) غير موجود. هل تريد إنشاء منتج جديد؟", QMessageBox.Yes | QMessageBox.No)
                    if msg == QMessageBox.Yes:
                        dlg = ProductDialog()
                        if dlg.exec_() == QDialog.Accepted:
                            n,col_n,pp,sp,q = dlg.get_data()
                            conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
                            c.execute("INSERT INTO products (name,color,purchase_price,avg_cost,last_purchase_price,sale_price,quantity) VALUES (?,?,?,?,?,?,?)", 
                                     (n,col_n,pp,pp,pp,sp,q))
                            new_id = c.lastrowid; conn.commit(); conn.close()
                            self.table.item(row, 0).setText(str(new_id))
                            self.table.item(row, 1).setText(n)
                            self.table.item(row, 2).setText(col_n)
                            self.table.item(row, 3).setText(str(pp))
                            self.table.item(row, 4).setText(str(sp))
                            self.table.item(row, 5).setText("1")
                            self.reload_autocompletes()
                            self.main_window.load_all_data()
                    else:
                        self.table.item(row, 0).setText("")
            
            elif col == 1:
                txt = item.text().strip()
                if txt in self.prod_by_name:
                    p = self.prod_by_name[txt]
                    self.table.item(row, 0).setText(str(p[0]))
                    self.table.item(row, 2).setText(p[2] if p[2] else "")
                    self.table.item(row, 3).setText(str(p[3]))
                    self.table.item(row, 4).setText(str(p[4]))
                    if not self.table.item(row, 5).text(): self.table.item(row, 5).setText("1")

            # Calculate Row Total auto (Price * Qty)
            if col in (3, 5) or (col in (0,1) and self.table.item(row, 3).text()):
                try:
                    price = float(self.table.item(row, 3).text())
                    qty = float(self.table.item(row, 5).text())
                    tot = price * qty
                    self.table.item(row, 6).setText(fmt(tot).replace(",",""))
                except ValueError:
                    self.table.item(row, 6).setText("")
        finally:
            self.is_updating = False
            self.calc_totals()

    def calc_totals(self):
        total = 0
        items_count = 0
        total_qty = 0
        
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0).text().strip() or self.table.item(r, 1).text().strip():
                try:
                    qty = float(self.table.item(r, 5).text())
                    total_qty += qty
                    items_count += 1
                except: pass
                
                try: 
                    tot = float(self.table.item(r, 6).text())
                    total += tot
                except: pass
                
        self.lbl_items_count.setText(f"عدد الأصناف: {items_count}")
        self.lbl_total_qty.setText(f"إجمالي الكمية: {int(total_qty)}")
        self.lbl_total.setText(f"الإجمالي: {fmt(total)}")
        
        paid = sum(inp.value() for inp in self.pay_inputs.values())
        rem = total - paid
        self.lbl_remaining.setText(f"المتبقي (آجل): {fmt(rem)}")
        if rem < -0.01: 
            self.lbl_remaining.setStyleSheet("font-size:18px; font-weight:bold; color:red;")
        else: 
            self.lbl_remaining.setStyleSheet("font-size:18px; font-weight:bold; color:#FFCDD2;")

    def reset_invoice(self):
        self.is_updating = True
        for r in range(self.table.rowCount()):
            for c in range(8):
                if self.table.item(r, c):
                    self.table.item(r, c).setText("")
        self.is_updating = False
        
        self.inv_num.setText(f"INV-{int(datetime.now().timestamp())}")
        self.notes_input.clear()
        for inp in self.pay_inputs.values():
            inp.setValue(0)
        self.calc_totals()
        self.supplier_combo.setCurrentIndex(-1)
        self.reload_autocompletes()

    def save_invoice(self):
        # 1. Validation for Supplier
        if self.supplier_combo.currentIndex() == -1:
            QMessageBox.warning(self, "خطأ", "يجب اختيار المورد أولاً قبل حفظ الفاتورة!")
            self.supplier_combo.setFocus()
            return
        
        total = 0
        items = []
        # 2. Iterate Rows & Validate
        for r in range(self.table.rowCount()):
            c_id = self.table.item(r, 0).text().strip()
            c_name = self.table.item(r, 1).text().strip()
            
            if not c_id and not c_name:
                continue # empty row skips
                
            if not c_id or not c_name:
                QMessageBox.warning(self, "خطأ بيانات", f"رقم أو اسم المنتج مفقود في الصف {r+1}")
                self.table.setCurrentCell(r, 0 if not c_id else 1)
                return
                
            try:
                pid = int(c_id)
                pname = c_name
                color = self.table.item(r, 2).text().strip()
                pprice = float(self.table.item(r, 3).text())
                sprice = float(self.table.item(r, 4).text())
                qty = int(self.table.item(r, 5).text())
                itot = float(self.table.item(r, 6).text())
                note = self.table.item(r, 7).text().strip()
                
                if qty <= 0:
                    QMessageBox.warning(self, "خطأ بيانات", f"الكمية غير صحيحة (أقل من أو تساوي صفر) في الصف {r+1}")
                    self.table.setCurrentCell(r, 5)
                    return
                if pprice < 0:
                    QMessageBox.warning(self, "خطأ بيانات", f"سعر الشراء غير صحيح في الصف {r+1}")
                    self.table.setCurrentCell(r, 3)
                    return
                    
                # Warning if Sale Price < Purchase Price
                if sprice < pprice:
                    msg = QMessageBox.warning(self, "تحذير تسعير", f"في الصف {r+1}: سعر البيع ({sprice}) أقل من سعر الشراء ({pprice}).\nهل تريد المتابعة وحفظ الفاتورة بهذا التسعير؟", QMessageBox.Yes | QMessageBox.No)
                    if msg == QMessageBox.No:
                        self.table.setCurrentCell(r, 4)
                        return
                
                # Check price diff for update
                update_master_price = False
                if str(pid) in self.prod_by_id:
                    old_pprice = float(self.prod_by_id[str(pid)][3])
                    if pprice != old_pprice:
                        ans = QMessageBox.question(self, "تحديث سعر المنتج", f"في الصف {r+1}: تغير سعر شراء المنتج '{pname}' من {old_pprice} إلى {pprice}.\nهل تريد تحديث سعر الشراء الافتراضي للمنتج في قاعدة البيانات؟", QMessageBox.Yes | QMessageBox.No)
                        if ans == QMessageBox.Yes:
                            update_master_price = True
                else:
                    update_master_price = True 
                
                items.append((pid, pname, color, pprice, sprice, qty, itot, note, update_master_price))
                total += itot
                
            except ValueError:
                QMessageBox.warning(self, "خطأ بيانات", f"هناك بيانات غير صحيحة (حروف بدلاً من أرقام) في الصف {r+1}")
                self.table.setCurrentCell(r, 3)
                return
        
        if not items:
            QMessageBox.warning(self, "خطأ", "الفاتورة فارغة ولا تحتوي على منتجات!")
            return

        paid_dict = {k: v.value() for k, v in self.pay_inputs.items() if v.value() > 0}
        total_paid = sum(paid_dict.values())
        rem = total - total_paid
        
        if rem < -0.01:
            QMessageBox.warning(self, "خطأ مالي", "المدفوع أكبر من إجمالي الفاتورة!")
            return

        sup_id = self.supplier_combo.currentData()
        sup_name = self.supplier_combo.currentText()
        inv_n = self.inv_num.text()
        inv_d = self.inv_date.date().toString("yyyy-MM-dd") + " " + datetime.now().strftime("%H:%M:%S")

        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        try:
            c.execute("BEGIN TRANSACTION")
            
            # Ensure safety tables exist before saving to prevent crashes
            c.execute('''CREATE TABLE IF NOT EXISTS supplier_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_id INTEGER, date TEXT, 
                amount REAL, payment_method TEXT, safe_id INTEGER, note TEXT, user_name TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS cash_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, safe_name TEXT, date TEXT, type TEXT, 
                ref_id TEXT, description TEXT, amount REAL, balance_before REAL, 
                balance_after REAL, user_name TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS supplier_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_id INTEGER, date TEXT, 
                type TEXT, ref_id INTEGER, debit REAL, credit REAL, balance_after REAL, note TEXT)''')
            
            # 1. Save Invoice
            pay_method_str = " | ".join([f"{k}: {v}" for k,v in paid_dict.items()]) if paid_dict else "آجل"
            c.execute("""INSERT INTO purchase_invoices 
                         (inv_number, date, supplier_id, supplier_name, total, paid, remaining, payment_method, notes, status, user_name)
                         VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                      (inv_n, inv_d, sup_id, sup_name, total, total_paid, rem, pay_method_str, self.notes_input.text(), 'مكتملة', self.user_name))
            inv_id = c.lastrowid
            
            # 2. Save Items & Update Stock/Prices
            for itm in items:
                # itm: pid, pname, color, pprice, sprice, qty, itot, note, update_master_price
                c.execute("""INSERT INTO purchase_items 
                             (invoice_id, product_id, product_name, color, purchase_price, sale_price, quantity, total, notes)
                             VALUES (?,?,?,?,?,?,?,?,?)""", (inv_id, itm[0], itm[1], itm[2], itm[3], itm[4], itm[5], itm[6], itm[7]))
                
                c.execute("SELECT quantity, avg_cost FROM products WHERE id=?", (itm[0],))
                curr_p = c.fetchone()
                if curr_p:
                    curr_qty = curr_p[0]; curr_avg = curr_p[1]
                    new_qty = curr_qty + itm[5]
                    new_avg = ((curr_qty * curr_avg) + itm[6]) / new_qty if new_qty > 0 else itm[3]
                    
                    if itm[8]: # update_master_price is True
                        c.execute("""UPDATE products 
                                     SET quantity=?, avg_cost=?, last_purchase_price=?, purchase_price=?, sale_price=? 
                                     WHERE id=?""", (new_qty, new_avg, itm[3], itm[3], itm[4], itm[0]))
                    else:
                        c.execute("""UPDATE products 
                                     SET quantity=?, avg_cost=?, last_purchase_price=?, sale_price=? 
                                     WHERE id=?""", (new_qty, new_avg, itm[3], itm[4], itm[0]))
            
            # 3. Update Supplier
            c.execute("""UPDATE suppliers 
                         SET balance = balance + ?, total_purchases = total_purchases + ?, total_paid = total_paid + ?, 
                             invoices_count = invoices_count + 1, last_deal = ?
                         WHERE id=?""", (rem, total, total_paid, inv_d, sup_id))
            
            # Supplier Transaction log
            c.execute("""INSERT INTO supplier_transactions (supplier_id, date, type, ref_id, debit, credit, balance_after, note)
                         VALUES (?,?,?,?,?,?,?,?)""", (sup_id, inv_d, "فاتورة مشتريات", inv_id, rem, 0, 0, "فاتورة مشتريات"))
            
            # 4. Safes Deductions
            for safe_name, amt in paid_dict.items():
                update_safe_balance(safe_name, -amt, "مشتريات", inv_id, f"فاتورة مشتريات #{inv_n} - {sup_name}", self.user_name, conn)
                c.execute("INSERT INTO supplier_payments (supplier_id, date, amount, payment_method, safe_id, note, user_name) VALUES (?,?,?,?,?,?,?)",
                          (sup_id, inv_d, amt, safe_name, 0, f"دفعة فاتورة {inv_n}", self.user_name))

            log_audit(self.user_name, "إنشاء فاتورة مشتريات", f"فاتورة {inv_n} للمورد {sup_name} بإجمالي {total}", conn=conn)
            
            conn.commit()
            
            QMessageBox.information(self, "تم بنجاح", "تم حفظ فاتورة المشتريات وتحديث المخازن والخزن بنجاح!")
            self.reset_invoice()
            self.main_window.load_all_data()
            
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "خطأ نظام", f"حدث خطأ أثناء حفظ الفاتورة:\n{str(e)}")
        finally:
            conn.close()

# ==================== نوافذ الحوار القديمة معدلة ====================

class ProductDialog(QDialog):
    def __init__(self, product=None):
        super().__init__()
        self.setWindowTitle("تعديل الشنطة" if product else "إضافة بضاعة جديدة")
        self.setFixedSize(400, 360); self.setLayoutDirection(Qt.RightToLeft); self.setStyleSheet(f"background:{CREAM};")
        form = QFormLayout(); form.setSpacing(12)
        self.name_input = QLineEdit(); self.color_input = QLineEdit()
        self.purchase_input = QDoubleSpinBox(); self.purchase_input.setMaximum(1000000); self.purchase_input.setDecimals(2)
        self.sale_input = QDoubleSpinBox(); self.sale_input.setMaximum(1000000); self.sale_input.setDecimals(2)
        self.qty_input = QSpinBox(); self.qty_input.setMaximum(100000)
        if product:
            self.name_input.setText(str(product[0])); self.color_input.setText(str(product[1]))
            try: self.purchase_input.setValue(float(normalize(str(product[2]))))
            except: pass
            try: self.sale_input.setValue(float(normalize(str(product[3]))))
            except: pass
            try: self.qty_input.setValue(int(normalize(str(product[4]))))
            except: pass
        form.addRow("اسم الشنطة:", self.name_input); form.addRow("اللون:", self.color_input)
        form.addRow("سعر الشراء:", self.purchase_input); form.addRow("سعر البيع:", self.sale_input)
        form.addRow("الكمية:", self.qty_input)
        btn = QPushButton("💾 حفظ"); btn.setStyleSheet(BTN.format(bg=TEAL_MID, hv=TEAL_DARK)); btn.clicked.connect(self.try_accept)
        layout = QVBoxLayout(); layout.addLayout(form); layout.addWidget(btn); self.setLayout(layout)

    def try_accept(self):
        if not self.name_input.text().strip(): QMessageBox.warning(self, "خطأ", "يرجى كتابة اسم الشنطة"); return
        self.accept()
    def get_data(self):
        return (self.name_input.text().strip(), self.color_input.text().strip(),
                self.purchase_input.value(), self.sale_input.value(), self.qty_input.value())

class SellProductDialog(QDialog):
    def __init__(self, products):
        super().__init__()
        self.all_products = products
        self.setWindowTitle("عملية بيع جديدة"); self.setFixedSize(460, 600)
        self.setLayoutDirection(Qt.RightToLeft); self.setStyleSheet(f"background:{CREAM};")
        layout = QVBoxLayout(); layout.setSpacing(10); layout.setContentsMargins(16,16,16,16)

        sf, self.search_box = make_search_bar("ابحث باسم الشنطة أو اللون...")
        self.search_box.textChanged.connect(self.filter_products); layout.addWidget(sf)

        form = QFormLayout(); form.setSpacing(10)
        self.product_combo = QComboBox(); self._fill_combo(products)
        self.product_combo.currentIndexChanged.connect(self.update_price)
        self.qty_input = QSpinBox(); self.qty_input.setMinimum(1); self.qty_input.valueChanged.connect(self.update_total)
        self.discount_input = QDoubleSpinBox(); self.discount_input.setMaximum(100000); self.discount_input.valueChanged.connect(self.update_total)
        self.customer_name = QLineEdit(); self.customer_phone = QLineEdit()
        
        self.pay_method = QComboBox(); self.pay_method.addItems(["كاش", "إنستاباي", "محفظة", "بنك"])

        form.addRow("الشنطة:", self.product_combo); form.addRow("الكمية:", self.qty_input)
        form.addRow("خصم:", self.discount_input); form.addRow("اسم العميل:", self.customer_name)
        form.addRow("رقم التليفون:", self.customer_phone)
        form.addRow("طريقة الدفع:", self.pay_method)
        layout.addLayout(form)

        self.total_label = QLabel("الإجمالي: 0.00 ج")
        self.total_label.setStyleSheet(f"font-size:22px;font-weight:bold;color:{WHITE};background:{TEAL_MID};padding:12px;border-radius:10px;")
        self.total_label.setAlignment(Qt.AlignCenter); layout.addWidget(self.total_label)

        btn = QPushButton("✅ تأكيد البيع"); btn.setStyleSheet(BTN.format(bg=GOLD_DARK, hv=GOLD))
        btn.clicked.connect(self.try_accept); layout.addWidget(btn); self.setLayout(layout)
        self.update_price()

    def _fill_combo(self, prods):
        self.product_combo.clear()
        for p in prods: self.product_combo.addItem(f"{p[1]}  |  {p[2]}  |  متاح: {p[5]}", p)

    def filter_products(self):
        txt = self.search_box.text().strip().lower()
        filtered = [p for p in self.all_products if not txt or txt in p[1].lower() or txt in p[2].lower()]
        self._fill_combo(filtered); self.update_price()

    def selected_product(self): return self.product_combo.currentData()
    def update_price(self):
        p = self.selected_product()
        if p: self.qty_input.setMaximum(max(int(p[5]),1))
        self.update_total()
    def update_total(self):
        p = self.selected_product()
        if not p: return
        self.total_label.setText(f"الإجمالي: {fmt(max((p[4]*self.qty_input.value())-self.discount_input.value(),0))} ج")
    def try_accept(self):
        p = self.selected_product()
        if not p or p[5] <= 0: QMessageBox.warning(self, "خطأ", "المنتج غير متوفر"); return
        if self.qty_input.value() > p[5]: QMessageBox.warning(self, "خطأ", "الكمية أكبر من المتاحة!"); return
        self.accept()
    def get_data(self):
        p = self.selected_product()
        total = max((p[4]*self.qty_input.value())-self.discount_input.value(), 0)
        return {"product_id":p[0],"product_name":p[1],"sale_price":p[4],"discount":self.discount_input.value(),
                "quantity":self.qty_input.value(),"total":total,
                "customer_name":self.customer_name.text().strip(),"customer_phone":self.customer_phone.text().strip(),
                "pay_method": self.pay_method.currentText()}

class ReturnDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تسجيل مرتجع مبيعات"); self.setFixedSize(490, 500)
        self.setLayoutDirection(Qt.RightToLeft); self.setStyleSheet(f"background:{CREAM};")
        layout = QVBoxLayout(); layout.setSpacing(10); layout.setContentsMargins(16,16,16,16)

        df, self.date_filter, btn_s, btn_a = make_date_bar("📅 ابحث بتاريخ البيع:")
        btn_s.clicked.connect(self.load_by_date); btn_a.clicked.connect(self.load_all)
        layout.addWidget(df)

        form = QFormLayout(); form.setSpacing(10)
        self.sale_combo = QComboBox(); self.sale_combo.currentIndexChanged.connect(self.on_sale_selected)
        self.qty_input = QSpinBox(); self.qty_input.setMinimum(1); self.qty_input.valueChanged.connect(self.update_total)
        self.reason_combo = QComboBox(); self.reason_combo.addItems(["تبديل منتج","عيب صناعة","رغبة العميل","أخرى"])
        self.safe_combo = QComboBox(); self.safe_combo.addItems(["كاش", "إنستاباي", "محفظة", "بنك"])
        
        form.addRow("الفاتورة:", self.sale_combo); form.addRow("الكمية المرتجعة:", self.qty_input)
        form.addRow("سبب الإرجاع:", self.reason_combo)
        form.addRow("خصم من خزنة:", self.safe_combo); layout.addLayout(form)

        self.lbl_total = QLabel("المبلغ المسترجع: 0.00 ج")
        self.lbl_total.setStyleSheet(f"font-size:16px;font-weight:bold;color:{WHITE};background:{RED2};padding:10px;border-radius:8px;")
        self.lbl_total.setAlignment(Qt.AlignCenter); layout.addWidget(self.lbl_total)

        btn = QPushButton("✅ تأكيد الإرجاع"); btn.setStyleSheet(BTN.format(bg=RED, hv=RED2))
        btn.clicked.connect(self.try_accept); layout.addWidget(btn); self.setLayout(layout)
        self.load_all()

    def load_all(self):
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT id,product_name,customer_name,quantity,total,sale_price,product_id,date,payment_method FROM sales ORDER BY id DESC LIMIT 300")
        self._fill(c.fetchall()); conn.close()

    def load_by_date(self):
        d = self.date_filter.date().toString("yyyy-MM-dd")
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT id,product_name,customer_name,quantity,total,sale_price,product_id,date,payment_method FROM sales WHERE substr(date,1,10)=? ORDER BY id DESC", (d,))
        rows = c.fetchall(); conn.close()
        if not rows: QMessageBox.information(self, "لا نتائج", f"مفيش مبيعات في {d}")
        self._fill(rows)

    def _fill(self, data):
        self.sales_data = data; self.sale_combo.clear()
        for r in data:
            cn = r[2] if r[2] else "عميل نقدي"
            self.sale_combo.addItem(f"#{r[0]} | {r[1]} | {cn} | {r[7][:10]} | {r[8]}", r)
        self.on_sale_selected()

    def on_sale_selected(self):
        d = self.sale_combo.currentData()
        if d:
            self.qty_input.setMaximum(int(d[3]))
            self.safe_combo.setCurrentText(d[8] if d[8] else "كاش")
        self.update_total()

    def update_total(self):
        d = self.sale_combo.currentData()
        if d: self.lbl_total.setText(f"المبلغ المسترجع: {fmt(d[5]*self.qty_input.value())} ج")

    def try_accept(self):
        if not self.sale_combo.currentData(): QMessageBox.warning(self, "خطأ", "لا توجد مبيعات."); return
        
        d = self.sale_combo.currentData()
        refund_amt = d[5] * self.qty_input.value()
        selected_safe = self.safe_combo.currentText()
        
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT balance FROM cash_boxes WHERE name=?", (selected_safe,))
        bal = c.fetchone()[0]
        conn.close()
        
        if bal < refund_amt:
            QMessageBox.warning(self, "رصيد غير كاف", f"لا يوجد رصيد كافي في خزنة {selected_safe} لعمل المرتجع!")
            return
            
        self.accept()

    def get_data(self):
        d = self.sale_combo.currentData(); q = self.qty_input.value()
        return {"sale_id":d[0],"product_id":d[6],"product_name":d[1],
                "customer_name":d[2] if d[2] else "عميل نقدي","quantity":q,
                "refund":d[5]*q,"reason":self.reason_combo.currentText(), "safe_name": self.safe_combo.currentText()}

class EditSaleDialog(QDialog):
    def __init__(self, qty, total):
        super().__init__()
        self.setWindowTitle("تعديل الفاتورة"); self.setFixedSize(360,220)
        self.setLayoutDirection(Qt.RightToLeft); self.setStyleSheet(f"background:{CREAM};")
        form = QFormLayout(); form.setSpacing(12)
        self.qty_input = QSpinBox(); self.qty_input.setMinimum(1); self.qty_input.setMaximum(100000); self.qty_input.setValue(qty)
        self.total_input = QDoubleSpinBox(); self.total_input.setMaximum(1000000); self.total_input.setDecimals(2); self.total_input.setValue(total)
        form.addRow("الكمية:", self.qty_input); form.addRow("الإجمالي:", self.total_input)
        btn = QPushButton("💾 حفظ التعديل"); btn.setStyleSheet(BTN.format(bg=GOLD_DARK, hv=GOLD)); btn.clicked.connect(self.accept)
        layout = QVBoxLayout(); layout.addLayout(form); layout.addWidget(btn); self.setLayout(layout)

    def get_data(self): return self.qty_input.value(), self.total_input.value()

class EditExpenseDialog(QDialog):
    def __init__(self, amount, note):
        super().__init__()
        self.setWindowTitle("تعديل المصروف"); self.setFixedSize(360,200)
        self.setLayoutDirection(Qt.RightToLeft); self.setStyleSheet(f"background:{CREAM};")
        form = QFormLayout(); form.setSpacing(12)
        self.amount_input = QDoubleSpinBox(); self.amount_input.setMaximum(1000000); self.amount_input.setDecimals(2); self.amount_input.setValue(amount)
        self.note_input = QLineEdit(note)
        form.addRow("المبلغ:", self.amount_input); form.addRow("ملاحظة:", self.note_input)
        btn = QPushButton("💾 حفظ التعديل"); btn.setStyleSheet(BTN.format(bg=GOLD_DARK, hv=GOLD)); btn.clicked.connect(self.accept)
        layout = QVBoxLayout(); layout.addLayout(form); layout.addWidget(btn); self.setLayout(layout)

    def get_data(self): return self.amount_input.value(), self.note_input.text().strip()

class SettingsDialog(QDialog):
    def __init__(self, store_name, alert_limit, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إعدادات النظام"); self.setFixedSize(380,230)
        self.setLayoutDirection(Qt.RightToLeft); self.setStyleSheet(f"background:{CREAM};")
        form = QFormLayout()
        self.name_input = QLineEdit(store_name)
        self.limit_input = QSpinBox(); self.limit_input.setValue(alert_limit); self.limit_input.setMaximum(10000)
        form.addRow("اسم المحل:", self.name_input); form.addRow("حد تنبيه النواقص:", self.limit_input)
        b1 = QPushButton("💾 نسخة احتياطية"); b1.setStyleSheet(BTN.format(bg=TEAL_MID,hv=TEAL_DARK)); b1.clicked.connect(self.backup)
        b2 = QPushButton("✅ حفظ"); b2.setStyleSheet(BTN.format(bg=GOLD_DARK,hv=GOLD)); b2.clicked.connect(self.accept)
        layout = QVBoxLayout(); layout.addLayout(form); layout.addWidget(b1); layout.addWidget(b2); self.setLayout(layout)

    def backup(self):
        try:
            shutil.copy2('lina_store.db', f'backup_lina_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.db')
            QMessageBox.information(self, "تم", "تم عمل نسخة احتياطية بنجاح!")
        except Exception as e: QMessageBox.warning(self, "خطأ", str(e))

    def get_data(self): return self.name_input.text().strip(), self.limit_input.value()

# ==================== الشاشة الرئيسية ====================

class LinaStorePro(QMainWindow):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.setWindowTitle("لينا ستور"); self.setGeometry(60,40,1200,760)
        self.setLayoutDirection(Qt.RightToLeft)
        self.load_settings(); self.check_daily_reset()
        self.init_ui(); self.load_all_data()
        self.reset_timer = QTimer(self); self.reset_timer.timeout.connect(self.check_daily_reset); self.reset_timer.start(60000)
        QTimer.singleShot(600, self.check_low_stock_alert)

    def load_settings(self):
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT store_name,alert_limit FROM settings WHERE id=1")
        res = c.fetchone(); conn.close()
        self.store_name = res[0] if res else "لينا ستور"
        self.alert_limit = res[1] if res else 5

    def check_daily_reset(self):
        today = date.today().strftime("%Y-%m-%d")
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT last_reset FROM daily_reset WHERE id=1")
        res = c.fetchone(); last = res[0] if res else ""; conn.close()
        if last != today:
            conn = sqlite3.connect('lina_store.db')
            conn.execute("UPDATE daily_reset SET last_reset=? WHERE id=1", (today,)); conn.commit(); conn.close()
            if hasattr(self, 'card_sales'): self.update_quick_stats()

    def check_low_stock_alert(self):
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT name,color,quantity FROM products WHERE quantity<=? ORDER BY quantity ASC", (self.alert_limit,))
        rows = c.fetchall(); conn.close()
        if rows:
            items = "\n".join([f"• {r[0]} ({r[1]}) — متبقي {r[2]}" for r in rows[:12]])
            extra = f"\n... و{len(rows)-12} صنف تاني" if len(rows) > 12 else ""
            QMessageBox.warning(self, "⚠️ تنبيه نواقص", f"الأصناف دي قربت تخلص:\n\n{items}{extra}")

    def update_safe_ui(self):
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT name, balance FROM cash_boxes")
        safes = c.fetchall()
        total_m = 0
        for name, bal in safes:
            total_m += bal
            if hasattr(self, f"lbl_safe_{name}"):
                getattr(self, f"lbl_safe_{name}").setText(f"{name}: {fmt(bal)} ج")
        if hasattr(self, "lbl_safe_total"):
            self.lbl_safe_total.setText(f"إجمالي الأموال: {fmt(total_m)} ج")
        conn.close()

    def init_ui(self):
        # هيدر
        hf = QFrame()
        hf.setStyleSheet(f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {TEAL_DARK},stop:0.5 {TEAL_MID},stop:1 {TEAL_DARK});")
        hf.setFixedHeight(60)
        hl = QHBoxLayout(); hl.setContentsMargins(20,0,20,0)
        lbl_brand = QLabel("LINA STORE"); lbl_brand.setStyleSheet(f"font-size:11px;font-weight:bold;color:{GOLD};background:transparent;letter-spacing:3px;")
        self.header = QLabel(f"لينا ستور  |  البائع: {self.current_user}")
        self.header.setStyleSheet(f"font-size:19px;font-weight:bold;color:{WHITE};background:transparent;")
        self.header.setAlignment(Qt.AlignCenter)
        dot = QLabel("●"); dot.setStyleSheet("color:#4CAF50;font-size:18px;background:transparent;")
        hl.addWidget(lbl_brand); hl.addWidget(self.header,1); hl.addWidget(dot); hf.setLayout(hl)

        # شريط الخزن دائم الظهور
        self.safe_bar = QFrame()
        self.safe_bar.setStyleSheet(f"background:{CREAM2}; border-bottom: 2px solid {GOLD_LIGHT};")
        self.safe_bar.setFixedHeight(40)
        safe_l = QHBoxLayout(); safe_l.setContentsMargins(20,0,20,0)
        
        self.lbl_safe_كاش = QLabel(); self.lbl_safe_كاش.setStyleSheet("font-weight:bold; color:#1B5E20;")
        self.lbl_safe_إنستاباي = QLabel(); self.lbl_safe_إنستاباي.setStyleSheet("font-weight:bold; color:#311B92;")
        self.lbl_safe_محفظة = QLabel(); self.lbl_safe_محفظة.setStyleSheet("font-weight:bold; color:#E65100;")
        self.lbl_safe_بنك = QLabel(); self.lbl_safe_بنك.setStyleSheet("font-weight:bold; color:#01579B;")
        self.lbl_safe_total = QLabel(); self.lbl_safe_total.setStyleSheet("font-weight:bold; font-size:15px; color:#B71C1C;")
        
        safe_l.addWidget(self.lbl_safe_كاش); safe_l.addWidget(QLabel(" | "))
        safe_l.addWidget(self.lbl_safe_إنستاباي); safe_l.addWidget(QLabel(" | "))
        safe_l.addWidget(self.lbl_safe_محفظة); safe_l.addWidget(QLabel(" | "))
        safe_l.addWidget(self.lbl_safe_بنك); safe_l.addStretch()
        safe_l.addWidget(self.lbl_safe_total)
        self.safe_bar.setLayout(safe_l)
        self.update_safe_ui()

        # كروت
        sl = QHBoxLayout(); sl.setSpacing(10); sl.setContentsMargins(12,8,12,4)
        self.card_prod  = self._card("المنتجات","0",TEAL_MID)
        self.card_sales = self._card("مبيعات اليوم","0 ج",GOLD_DARK)
        self.card_profit= self._card("ربح اليوم","0 ج","#2E7D32")
        self.card_low   = self._card("النواقص","0",RED2)
        self.card_cust  = self._card("العملاء","0",TEAL_LIGHT)
        for c in (self.card_prod,self.card_sales,self.card_profit,self.card_low,self.card_cust): sl.addWidget(c)

        # تبويبات
        self.tabs = QTabWidget()
        self.tabs.addTab(self.build_main_tab(),"🏠  الرئيسية")
        self.tabs.addTab(self.build_inventory_tab(),"📦  المخزن")
        self.tabs.addTab(self.build_sales_tab(),"🧾  سجل المبيعات")
        self.tabs.addTab(self.build_reports_tab(),"📊  التقارير")
        self.tabs.addTab(self.build_analytics_tab(),"🔎  التحليلات")
        self.tabs.addTab(self.build_expenses_tab(),"💸  المصروفات")
        self.tabs.addTab(self.build_raffle_tab(),"🎉  السحب")
        self.tabs.addTab(self.build_customers_tab(),"👥  العملاء")
        self.tabs.addTab(self.build_suppliers_tab(),"🏭  الموردين والمشتريات")
        self.tabs.addTab(self.build_treasury_tab(),"🏦  الخزنة")

        ml = QVBoxLayout(); ml.setSpacing(0); ml.setContentsMargins(0,0,0,0)
        ml.addWidget(hf); ml.addWidget(self.safe_bar); ml.addLayout(sl); ml.addWidget(self.tabs)
        container = QWidget(); container.setLayout(ml); self.setCentralWidget(container)

    def _card(self, title, val, color):
        f = QFrame(); f.setStyleSheet(f"background:{WHITE};border:2px solid {color};border-radius:10px;"); f.setFixedHeight(65)
        v = QVBoxLayout(); v.setContentsMargins(10,6,10,6); v.setSpacing(1)
        lv = QLabel(val); lv.setStyleSheet(f"font-size:16px;font-weight:bold;color:{color};"); lv.setAlignment(Qt.AlignCenter)
        lt = QLabel(title); lt.setStyleSheet("font-size:11px;color:#777;"); lt.setAlignment(Qt.AlignCenter)
        v.addWidget(lv); v.addWidget(lt); f.setLayout(v); f._v = lv; return f

    def _set_card(self, card, val): card._v.setText(val)

    # ==================== تبويب الرئيسية ====================
    def build_main_tab(self):
        w = QWidget(); layout = QVBoxLayout(); layout.setSpacing(18); layout.setContentsMargins(40,25,40,25)

        logo_card = QFrame()
        logo_card.setStyleSheet(f"background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {TEAL_DARK},stop:1 {TEAL_MID});border-radius:18px;border:2px solid {GOLD};")
        logo_card.setFixedHeight(120)
        lc = QVBoxLayout(); lc.setContentsMargins(20,14,20,14)
        lb = QLabel("LINA  STORE"); lb.setStyleSheet(f"font-size:34px;font-weight:bold;color:{GOLD};background:transparent;letter-spacing:6px;"); lb.setAlignment(Qt.AlignCenter)
        la = QLabel("لينا ستور  ·  نظام إدارة المحل"); la.setStyleSheet(f"font-size:13px;color:{CREAM};background:transparent;"); la.setAlignment(Qt.AlignCenter)
        lc.addWidget(lb); lc.addWidget(la); logo_card.setLayout(lc); layout.addWidget(logo_card)

        # ملخص اليوم السريع
        self.lbl_daily_summary = QLabel("📊 اليوم: مبيعات 0 ج  |  مصروفات 0 ج  |  صافي ربح 0 ج")
        self.lbl_daily_summary.setStyleSheet(f"background:{CREAM2};color:{TEAL_DARK};font-size:13px;font-weight:bold;padding:10px;border-radius:8px;border:1px solid {GOLD_LIGHT};")
        self.lbl_daily_summary.setAlignment(Qt.AlignCenter); layout.addWidget(self.lbl_daily_summary)

        row1 = QHBoxLayout(); row1.setSpacing(14)
        for text, color, color2, slot in [
            ("💰   بيع شنطة", GOLD_DARK, GOLD, self.sell_product_dialog),
            ("↩️   تسجيل مرتجع", RED, RED2, self.open_return_dialog)]:
            btn = QPushButton(text); btn.setMinimumHeight(75)
            btn.setStyleSheet(f"QPushButton{{background:{color};color:white;font-size:17px;font-weight:bold;border-radius:12px;border:none;}}QPushButton:hover{{background:{color2};}}")
            btn.clicked.connect(slot); row1.addWidget(btn)
        layout.addLayout(row1)
        
        row2 = QHBoxLayout(); row2.setSpacing(14)
        btn_buy = QPushButton("🛒   فاتورة مشتريات"); btn_buy.setMinimumHeight(50)
        btn_buy.setStyleSheet(f"QPushButton{{background:#0277BD;color:white;font-size:15px;font-weight:bold;border-radius:10px;border:none;}}QPushButton:hover{{background:#01579B;}}")
        btn_buy.clicked.connect(self.open_purchase_invoice)
        row2.addWidget(btn_buy)
        
        btn_trans = QPushButton("↔️   تحويل بين الخزن"); btn_trans.setMinimumHeight(50)
        btn_trans.setStyleSheet(f"QPushButton{{background:#6A1B9A;color:white;font-size:15px;font-weight:bold;border-radius:10px;border:none;}}QPushButton:hover{{background:#4A148C;}}")
        btn_trans.clicked.connect(self.open_transfer_dialog)
        row2.addWidget(btn_trans)
        layout.addLayout(row2)

        btn_s = QPushButton("🔧   الإعدادات"); btn_s.setMinimumHeight(50)
        btn_s.setStyleSheet(f"QPushButton{{background:{TEAL_MID};color:white;font-size:15px;font-weight:bold;border-radius:10px;border:none;}}QPushButton:hover{{background:{TEAL_DARK};}}")
        btn_s.clicked.connect(self.show_settings_dialog); layout.addWidget(btn_s)
        layout.addStretch(); w.setLayout(layout); return w

    def open_purchase_invoice(self):
        dlg = PurchaseInvoiceDialog(self.current_user, self)
        dlg.exec_()
        self.load_all_data()

    def open_transfer_dialog(self):
        dlg = TransferSafeDialog(self.current_user)
        dlg.exec_()
        self.load_all_data()

    # ==================== تبويب المخزن ====================
    def build_inventory_tab(self):
        w = QWidget(); layout = QVBoxLayout(); layout.setContentsMargins(12,12,12,12); layout.setSpacing(10)

        sf, self.inv_search = make_search_bar("ابحث باسم الشنطة أو اللون...")
        self.inv_search.textChanged.connect(self._filter_inventory)
        layout.addWidget(sf)

        bl = QHBoxLayout(); bl.setSpacing(8)
        b1 = QPushButton("➕  إضافة بضاعة"); b1.setStyleSheet(BTN.format(bg=TEAL_MID,hv=TEAL_DARK)); b1.clicked.connect(self.add_product_dialog)
        b2 = QPushButton("⚙️  تعديل / حذف"); b2.setStyleSheet(BTN.format(bg=GOLD_DARK,hv=GOLD)); b2.clicked.connect(self.delete_or_edit_product)
        bl.addWidget(b1); bl.addWidget(b2); bl.addStretch(); layout.addLayout(bl)

        self.table = QTableWidget(); self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["كود","اسم الشنطة","اللون","متوسط التكلفة","آخر سعر شراء","سعر البيع","الكمية"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        style_table(self.table); layout.addWidget(self.table)
        w.setLayout(layout); return w

    def _filter_inventory(self):
        txt = self.inv_search.text().strip()
        for r in range(self.table.rowCount()):
            if not txt:
                self.table.setRowHidden(r, False)
            else:
                name_item  = self.table.item(r, 1)
                color_item = self.table.item(r, 2)
                name_match  = name_item  and txt in name_item.text()
                color_match = color_item and txt in color_item.text()
                self.table.setRowHidden(r, not (name_match or color_match))

    def load_data(self):
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT id,name,color,avg_cost,last_purchase_price,sale_price,quantity FROM products ORDER BY name")
        rows = c.fetchall(); conn.close()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, val in enumerate(r):
                display = fmt(val) if j in (3,4,5) else str(val)
                item = QTableWidgetItem(display); item.setTextAlignment(Qt.AlignCenter)
                if j == 6 and isinstance(val, (int,float)) and val <= self.alert_limit:
                    item.setForeground(QColor(RED2)); item.setBackground(QColor("#FFF0F0"))
                self.table.setItem(i, j, item)
        self.update_quick_stats()

    def update_quick_stats(self):
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM products"); prod = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM products WHERE quantity<=?", (self.alert_limit,)); low = c.fetchone()[0]
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT SUM(total) FROM sales WHERE substr(date,1,10)=?", (today,)); sales_today = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM customers"); cust = c.fetchone()[0]
        
        c.execute("""SELECT SUM(s.total - COALESCE(p.avg_cost,0)*s.quantity)
                     FROM sales s LEFT JOIN products p ON s.product_id=p.id
                     WHERE substr(s.date,1,10)=?""", (today,))
        gross = c.fetchone()[0] or 0
        c.execute("SELECT SUM(amount) FROM expenses WHERE substr(date,1,10)=?", (today,)); exp = c.fetchone()[0] or 0
        c.execute("SELECT SUM(total) FROM returns WHERE substr(date,1,10)=?", (today,)); ret = c.fetchone()[0] or 0
        profit_today = gross - exp - ret
        conn.close()
        
        self._set_card(self.card_prod, str(prod))
        self._set_card(self.card_low, str(low))
        self._set_card(self.card_sales, f"{fmt(sales_today)} ج")
        self._set_card(self.card_profit, f"{fmt(profit_today)} ج")
        self._set_card(self.card_cust, str(cust))
        if hasattr(self, 'lbl_daily_summary'):
            self.lbl_daily_summary.setText(f"📊 اليوم: مبيعات {fmt(sales_today)} ج  |  مصروفات {fmt(exp)} ج  |  صافي ربح {fmt(profit_today)} ج")
        
        self.update_safe_ui()

    def add_product_dialog(self):
        dlg = ProductDialog()
        if dlg.exec_() == QDialog.Accepted:
            n,col,pp,sp,q = dlg.get_data()
            conn = sqlite3.connect('lina_store.db')
            conn.execute("INSERT INTO products (name,color,purchase_price,avg_cost,last_purchase_price,sale_price,quantity) VALUES (?,?,?,?,?,?,?)", 
                         (n,col,pp,pp,pp,sp,q))
            conn.commit(); conn.close(); self.load_data()

    def sell_product_dialog(self):
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT id,name,color,purchase_price,sale_price,quantity FROM products WHERE quantity>0 ORDER BY name")
        prods = c.fetchall(); conn.close()
        if not prods: QMessageBox.warning(self,"المخزن فارغ","لا يوجد بضاعة متاحة!"); return
        dlg = SellProductDialog(prods)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
            try:
                c.execute("BEGIN TRANSACTION")
                c.execute("UPDATE products SET quantity=quantity-? WHERE id=?", (data["quantity"],data["product_id"]))
                c.execute("INSERT INTO sales (product_id,product_name,user_name,customer_name,customer_phone,sale_price,discount,quantity,total,date,payment_method) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                          (data["product_id"],data["product_name"],self.current_user,data["customer_name"],data["customer_phone"],
                           data["sale_price"],data["discount"],data["quantity"],data["total"],datetime.now().strftime("%Y-%m-%d %H:%M"), data["pay_method"]))
                ref = c.lastrowid
                
                if data["customer_phone"]:
                    c.execute("INSERT OR IGNORE INTO customers (name,phone,total_spent,last_visit) VALUES (?,?,0,'')", (data["customer_name"],data["customer_phone"]))
                    c.execute("UPDATE customers SET total_spent=total_spent+?,last_visit=? WHERE phone=?", (data["total"],datetime.now().strftime("%Y-%m-%d"),data["customer_phone"]))
                
                update_safe_balance(data["pay_method"], data["total"], "مبيعات", ref, f"بيع {data['product_name']}", self.current_user, conn)
                log_audit(self.current_user, "عملية بيع", f"بيع {data['quantity']} من {data['product_name']} بـ {data['total']} ({data['pay_method']})", conn)
                
                conn.commit()
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "خطأ", str(e))
            finally:
                conn.close()
            self.load_all_data()

    def delete_or_edit_product(self):
        row = self.table.currentRow()
        if row < 0: QMessageBox.warning(self,"تنبيه","اختار صف أولاً"); return
        pid = self.table.item(row,0).text()
        msg = QMessageBox(self); msg.setWindowTitle("خيارات"); msg.setText("اختر الإجراء:")
        b_edit = msg.addButton("تعديل", QMessageBox.ActionRole)
        b_del  = msg.addButton("حذف",   QMessageBox.DestructiveRole)
        msg.addButton("إلغاء", QMessageBox.RejectRole); msg.exec_()
        if msg.clickedButton() == b_edit:
            curr = tuple(self.table.item(row,j).text() for j in range(1,7)) 
            dlg = ProductDialog((curr[0], curr[1], curr[3], curr[4], curr[5]))
            if dlg.exec_() == QDialog.Accepted:
                n,col,pp,sp,q = dlg.get_data()
                conn = sqlite3.connect('lina_store.db')
                conn.execute("UPDATE products SET name=?,color=?,purchase_price=?,sale_price=?,quantity=? WHERE id=?", (n,col,pp,sp,q,pid))
                conn.commit(); conn.close(); self.load_data()
        elif msg.clickedButton() == b_del:
            if QMessageBox.question(self,"تأكيد","هل متأكد من الحذف؟") == QMessageBox.Yes:
                conn = sqlite3.connect('lina_store.db'); conn.execute("DELETE FROM products WHERE id=?", (pid,)); conn.commit(); conn.close(); self.load_data()

    def open_return_dialog(self):
        dlg = ReturnDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
            try:
                c.execute("BEGIN TRANSACTION")
                c.execute("INSERT INTO returns (sale_id,product_id,product_name,customer_name,quantity,total,reason,date,safe_name) VALUES (?,?,?,?,?,?,?,?,?)",
                          (d["sale_id"],d["product_id"],d["product_name"],d["customer_name"],d["quantity"],d["refund"],d["reason"],datetime.now().strftime("%Y-%m-%d %H:%M"), d["safe_name"]))
                ref = c.lastrowid
                c.execute("UPDATE products SET quantity=quantity+? WHERE id=?", (d["quantity"],d["product_id"]))
                update_safe_balance(d["safe_name"], -d["refund"], "مرتجع مبيعات", ref, f"مرتجع {d['product_name']}", self.current_user, conn)
                log_audit(self.current_user, "مرتجع مبيعات", f"إرجاع {d['quantity']} من {d['product_name']} بـ {d['refund']}", conn)
                conn.commit()
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "خطأ", str(e))
            finally:
                conn.close()
            self.load_all_data()

    # ==================== سجل المبيعات ====================
    def build_sales_tab(self):
        w = QWidget(); layout = QVBoxLayout(); layout.setContentsMargins(12,12,12,12); layout.setSpacing(10)

        df, self.sales_date, btn_s, btn_a = make_date_bar("📅 مبيعات يوم:")
        btn_s.clicked.connect(self.load_sales_by_date); btn_a.clicked.connect(self.load_sales_data)
        layout.addWidget(df)

        bl = QHBoxLayout(); bl.setSpacing(8)
        b_edit = QPushButton("⚙️  تعديل / حذف فاتورة"); b_edit.setStyleSheet(BTN.format(bg=GOLD_DARK,hv=GOLD))
        b_edit.clicked.connect(self.edit_or_delete_sale)
        bl.addWidget(b_edit); bl.addStretch(); layout.addLayout(bl)

        self.sales_table = QTableWidget(); self.sales_table.setColumnCount(9)
        self.sales_table.setHorizontalHeaderLabels(["كود","التاريخ","الشنطة","البائع","العميل","التليفون","الكمية","الإجمالي", "طريقة الدفع"])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sales_table.setColumnHidden(0, True)
        style_table(self.sales_table); layout.addWidget(self.sales_table)
        w.setLayout(layout); return w

    def load_sales_data(self):
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT id,date,product_name,user_name,customer_name,customer_phone,quantity,total,payment_method FROM sales ORDER BY id DESC")
        self._fill_sales(c.fetchall()); conn.close()

    def load_sales_by_date(self):
        d = self.sales_date.date().toString("yyyy-MM-dd")
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT id,date,product_name,user_name,customer_name,customer_phone,quantity,total,payment_method FROM sales WHERE substr(date,1,10)=? ORDER BY id DESC", (d,))
        self._fill_sales(c.fetchall()); conn.close()

    def _fill_sales(self, rows):
        self.sales_table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            for j,val in enumerate(r):
                item = QTableWidgetItem(fmt(val) if j==7 else str(val) if val else "-")
                item.setTextAlignment(Qt.AlignCenter); self.sales_table.setItem(i,j,item)

    def edit_or_delete_sale(self):
        row = self.sales_table.currentRow()
        if row < 0: QMessageBox.warning(self,"تنبيه","اختار فاتورة من الجدول أولاً"); return
        sale_id = self.sales_table.item(row,0).text()
        product_name = self.sales_table.item(row,2).text()
        old_qty = int(self.sales_table.item(row,6).text())
        old_total = float(normalize(self.sales_table.item(row,7).text().replace(",","")))

        msg = QMessageBox(self); msg.setWindowTitle("خيارات الفاتورة"); msg.setText(f"الفاتورة #{sale_id} - {product_name}\nاختر الإجراء:")
        b_edit = msg.addButton("تعديل", QMessageBox.ActionRole)
        b_del  = msg.addButton("حذف نهائي", QMessageBox.DestructiveRole)
        msg.addButton("إلغاء", QMessageBox.RejectRole); msg.exec_()

        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT product_id, customer_phone, total, payment_method FROM sales WHERE id=?", (sale_id,))
        srow = c.fetchone()
        if not srow: conn.close(); return
        product_id, cust_phone, current_total, pay_method = srow
        conn.close()

        if msg.clickedButton() == b_edit:
            dlg = EditSaleDialog(old_qty, old_total)
            if dlg.exec_() == QDialog.Accepted:
                new_qty, new_total = dlg.get_data()
                conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
                try:
                    c.execute("BEGIN TRANSACTION")
                    diff_qty = new_qty - old_qty
                    c.execute("UPDATE products SET quantity=quantity-? WHERE id=?", (diff_qty, product_id))
                    c.execute("UPDATE sales SET quantity=?, total=? WHERE id=?", (new_qty, new_total, sale_id))
                    if cust_phone:
                        c.execute("UPDATE customers SET total_spent=total_spent-?+? WHERE phone=?", (current_total, new_total, cust_phone))
                    diff_money = new_total - old_total
                    if diff_money != 0:
                        update_safe_balance(pay_method, diff_money, "تعديل مبيعات", sale_id, f"فرق تعديل فاتورة {sale_id}", self.current_user, conn)
                    conn.commit()
                except Exception as e: conn.rollback(); QMessageBox.critical(self, "خطأ", str(e))
                finally: conn.close()
                self.load_all_data()
        elif msg.clickedButton() == b_del:
            if QMessageBox.question(self,"تأكيد الحذف", f"هل متأكد من حذف الفاتورة #{sale_id} نهائياً؟\nالكمية هترجع للمخزن وسيخصم المبلغ من الخزنة.") == QMessageBox.Yes:
                conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
                try:
                    c.execute("BEGIN TRANSACTION")
                    c.execute("UPDATE products SET quantity=quantity+? WHERE id=?", (old_qty, product_id))
                    if cust_phone:
                        c.execute("UPDATE customers SET total_spent=total_spent-? WHERE phone=?", (current_total, cust_phone))
                    c.execute("DELETE FROM sales WHERE id=?", (sale_id,))
                    update_safe_balance(pay_method, -current_total, "حذف مبيعات", sale_id, f"إلغاء فاتورة {sale_id}", self.current_user, conn)
                    conn.commit()
                except Exception as e: conn.rollback(); QMessageBox.critical(self, "خطأ", str(e))
                finally: conn.close()
                self.load_all_data()

    # ==================== التقارير ====================
    def build_reports_tab(self):
        w = QWidget(); layout = QVBoxLayout(); layout.setContentsMargins(12,12,12,12); layout.setSpacing(10)

        ff = QFrame(); ff.setStyleSheet(f"background:{CREAM2};border-radius:10px;padding:4px;")
        fr = QHBoxLayout(); fr.setContentsMargins(8,6,8,6); fr.setSpacing(8)
        fr.addWidget(QLabel("📅 من:"))
        self.r_from = QDateEdit(QDate.currentDate()); self.r_from.setCalendarPopup(True); fr.addWidget(self.r_from)
        fr.addWidget(QLabel("إلى:"))
        self.r_to = QDateEdit(QDate.currentDate()); self.r_to.setCalendarPopup(True); fr.addWidget(self.r_to)
        b1 = QPushButton("🔄 تحديث"); b1.setStyleSheet(BTN.format(bg=TEAL_MID,hv=TEAL_DARK)); b1.clicked.connect(self.apply_report); fr.addWidget(b1)
        b2 = QPushButton("📥 تصدير CSV"); b2.setStyleSheet(BTN.format(bg=GOLD_DARK,hv=GOLD)); b2.clicked.connect(self.export_csv); fr.addWidget(b2)
        fr.addStretch(); ff.setLayout(fr); layout.addWidget(ff)

        cl = QHBoxLayout(); cl.setSpacing(10)
        self.rpt_revenue  = self._rcard("💰 إجمالي الإيراد","0.00 ج",TEAL_MID)
        self.rpt_cost     = self._rcard("🛒 تكلفة البضاعة","0.00 ج","#1565C0")
        self.rpt_expenses = self._rcard("💸 المصروفات","0.00 ج",RED2)
        self.rpt_profit   = self._rcard("📈 صافي الربح","0.00 ج",GOLD_DARK)
        for c in (self.rpt_revenue,self.rpt_cost,self.rpt_expenses,self.rpt_profit): cl.addWidget(c)
        layout.addLayout(cl)

        self.report_table = QTableWidget(); self.report_table.setColumnCount(6)
        self.report_table.setHorizontalHeaderLabels(["التاريخ","الشنطة","البائع","العميل","الكمية","الإجمالي"])
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        style_table(self.report_table); layout.addWidget(self.report_table)
        w.setLayout(layout); return w

    def _rcard(self, title, val, color):
        f = QFrame(); f.setStyleSheet(f"background:{WHITE};border:2px solid {color};border-radius:10px;")
        v = QVBoxLayout(); v.setContentsMargins(10,8,10,8)
        lt = QLabel(title); lt.setStyleSheet(f"font-size:12px;color:{color};font-weight:bold;"); lt.setAlignment(Qt.AlignCenter)
        lv = QLabel(val);   lv.setStyleSheet(f"font-size:17px;font-weight:bold;color:{color};"); lv.setAlignment(Qt.AlignCenter)
        v.addWidget(lt); v.addWidget(lv); f.setLayout(v); f._v = lv; return f

    def apply_report(self):
        f = self.r_from.date().toString("yyyy-MM-dd"); t = self.r_to.date().toString("yyyy-MM-dd")
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("""SELECT s.date,s.product_name,s.user_name,s.customer_name,s.quantity,s.total,
                     COALESCE(p.avg_cost,0),s.quantity
                     FROM sales s LEFT JOIN products p ON s.product_id=p.id
                     WHERE substr(s.date,1,10) BETWEEN ? AND ? ORDER BY s.id DESC""", (f,t))
        rows = c.fetchall()
        c.execute("SELECT SUM(total) FROM returns WHERE substr(date,1,10) BETWEEN ? AND ?", (f,t)); ret = c.fetchone()[0] or 0
        c.execute("SELECT SUM(amount) FROM expenses WHERE substr(date,1,10) BETWEEN ? AND ?", (f,t)); exp = c.fetchone()[0] or 0
        conn.close()
        self.report_table.setRowCount(len(rows)); revenue = cost = 0; self.saved_report = []
        for i,r in enumerate(rows):
            for j in range(6):
                item = QTableWidgetItem(fmt(r[j]) if j==5 else str(r[j])); item.setTextAlignment(Qt.AlignCenter)
                self.report_table.setItem(i,j,item)
            revenue += r[5]; cost += r[6]*r[7]; self.saved_report.append(r[:6])
        self.rpt_revenue._v.setText(f"{fmt(revenue-ret)} ج")
        self.rpt_cost._v.setText(f"{fmt(cost)} ج")
        self.rpt_expenses._v.setText(f"{fmt(exp)} ج")
        self.rpt_profit._v.setText(f"{fmt((revenue-cost)-ret-exp)} ج")

    def export_csv(self):
        if not hasattr(self,'saved_report') or not self.saved_report: QMessageBox.warning(self,"خطأ","لا توجد بيانات"); return
        path,_ = QFileDialog.getSaveFileName(self,"حفظ التقرير","تقرير_لينا.csv","CSV Files (*.csv)")
        if path:
            with open(path,"w",newline="",encoding="utf-8-sig") as f:
                csv.writer(f).writerows([["التاريخ","الشنطة","البائع","العميل","الكمية","الإجمالي"]]+self.saved_report)
            QMessageBox.information(self,"تم","تم التصدير!")

    # ==================== التحليلات ====================
    def build_analytics_tab(self):
        w = QWidget(); layout = QVBoxLayout(); layout.setContentsMargins(12,12,12,12); layout.setSpacing(10)
        ff = QFrame(); ff.setStyleSheet(f"background:{CREAM2};border-radius:10px;padding:4px;")
        fr = QHBoxLayout(); fr.setContentsMargins(8,6,8,6); fr.setSpacing(8)
        fr.addWidget(QLabel("📅 من:"))
        self.a_from = QDateEdit(QDate.currentDate().addDays(-30)); self.a_from.setCalendarPopup(True); fr.addWidget(self.a_from)
        fr.addWidget(QLabel("إلى:"))
        self.a_to = QDateEdit(QDate.currentDate()); self.a_to.setCalendarPopup(True); fr.addWidget(self.a_to)
        b1 = QPushButton("🔄 تحديث التحليلات"); b1.setStyleSheet(BTN.format(bg=TEAL_MID,hv=TEAL_DARK)); b1.clicked.connect(self.refresh_analytics); fr.addWidget(b1)
        fr.addStretch(); ff.setLayout(fr); layout.addWidget(ff)

        cl = QHBoxLayout(); cl.setSpacing(10)
        self.an_curr_sales = self._rcard("💰 مبيعات الفترة","0.00 ج",TEAL_MID)
        self.an_prev_sales = self._rcard("📦 الفترة السابقة","0.00 ج","#5D4037")
        self.an_change     = self._rcard("📊 نسبة التغيير","0%",GOLD_DARK)
        self.an_best_cust  = self._rcard("🏆 أفضل عميل","-",TEAL_LIGHT)
        for c in (self.an_curr_sales,self.an_prev_sales,self.an_change,self.an_best_cust): cl.addWidget(c)
        layout.addLayout(cl)

        tables_row = QHBoxLayout(); tables_row.setSpacing(10)
        left_box = QVBoxLayout()
        lbl_top_prod = QLabel("🏅 الأكثر مبيعاً"); lbl_top_prod.setStyleSheet(f"font-weight:bold;color:{TEAL_DARK};font-size:13px;")
        left_box.addWidget(lbl_top_prod)
        self.top_products_table = QTableWidget(); self.top_products_table.setColumnCount(3)
        self.top_products_table.setHorizontalHeaderLabels(["الشنطة","الكمية المباعة","إجمالي المبيعات"])
        self.top_products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        style_table(self.top_products_table)
        left_box.addWidget(self.top_products_table)
        tables_row.addLayout(left_box)

        right_box = QVBoxLayout()
        lbl_top_cust = QLabel("👑 أفضل العملاء"); lbl_top_cust.setStyleSheet(f"font-weight:bold;color:{TEAL_DARK};font-size:13px;")
        right_box.addWidget(lbl_top_cust)
        self.top_customers_table = QTableWidget(); self.top_customers_table.setColumnCount(3)
        self.top_customers_table.setHorizontalHeaderLabels(["العميل","عدد المرات","إجمالي الشراء"])
        self.top_customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        style_table(self.top_customers_table)
        right_box.addWidget(self.top_customers_table)
        tables_row.addLayout(right_box)

        layout.addLayout(tables_row)
        w.setLayout(layout); return w

    def refresh_analytics(self):
        f = self.a_from.date().toString("yyyy-MM-dd"); t = self.a_to.date().toString("yyyy-MM-dd")
        days = self.a_from.date().daysTo(self.a_to.date()) + 1
        prev_to = self.a_from.date().addDays(-1)
        prev_from = prev_to.addDays(-(days-1))
        pf = prev_from.toString("yyyy-MM-dd"); pt = prev_to.toString("yyyy-MM-dd")

        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT COALESCE(SUM(total),0) FROM sales WHERE substr(date,1,10) BETWEEN ? AND ?", (f,t))
        curr_sales = c.fetchone()[0]
        c.execute("SELECT COALESCE(SUM(total),0) FROM sales WHERE substr(date,1,10) BETWEEN ? AND ?", (pf,pt))
        prev_sales = c.fetchone()[0]

        if prev_sales > 0: change_pct = ((curr_sales - prev_sales) / prev_sales) * 100
        else: change_pct = 100.0 if curr_sales > 0 else 0.0

        c.execute("""SELECT customer_name, SUM(total) as tot FROM sales
                     WHERE substr(date,1,10) BETWEEN ? AND ? AND customer_name!='' AND customer_name IS NOT NULL
                     GROUP BY customer_name ORDER BY tot DESC LIMIT 1""", (f,t))
        best = c.fetchone()
        best_name = best[0] if best else "-"

        c.execute("""SELECT product_name, SUM(quantity) as q, SUM(total) as tot FROM sales
                     WHERE substr(date,1,10) BETWEEN ? AND ?
                     GROUP BY product_name ORDER BY q DESC LIMIT 15""", (f,t))
        top_products = c.fetchall()

        c.execute("""SELECT customer_name, COUNT(*) as cnt, SUM(total) as tot FROM sales
                     WHERE substr(date,1,10) BETWEEN ? AND ? AND customer_name!='' AND customer_name IS NOT NULL
                     GROUP BY customer_name ORDER BY tot DESC LIMIT 15""", (f,t))
        top_customers = c.fetchall()
        conn.close()

        self.an_curr_sales._v.setText(f"{fmt(curr_sales)} ج")
        self.an_prev_sales._v.setText(f"{fmt(prev_sales)} ج")
        sign = "+" if change_pct >= 0 else ""
        self.an_change._v.setText(f"{sign}{change_pct:.1f}%")
        self.an_change._v.setStyleSheet(f"font-size:17px;font-weight:bold;color:{'#2E7D32' if change_pct>=0 else RED2};")
        self.an_best_cust._v.setText(best_name if best_name else "-")

        self.top_products_table.setRowCount(len(top_products))
        for i,r in enumerate(top_products):
            for j,val in enumerate(r):
                item = QTableWidgetItem(fmt(val) if j==2 else str(val))
                item.setTextAlignment(Qt.AlignCenter); self.top_products_table.setItem(i,j,item)

        self.top_customers_table.setRowCount(len(top_customers))
        for i,r in enumerate(top_customers):
            for j,val in enumerate(r):
                item = QTableWidgetItem(fmt(val) if j==2 else str(val))
                item.setTextAlignment(Qt.AlignCenter); self.top_customers_table.setItem(i,j,item)

    # ==================== المصروفات ====================
    def build_expenses_tab(self):
        w = QWidget(); layout = QVBoxLayout(); layout.setContentsMargins(12,12,12,12); layout.setSpacing(10)

        add_frame = QFrame(); add_frame.setStyleSheet(f"background:{CREAM2};border-radius:10px;padding:4px;")
        fr = QHBoxLayout(); fr.setContentsMargins(8,6,8,6); fr.setSpacing(8)
        self.exp_type = QComboBox(); self.exp_type.addItems(["إيجار المحل","كهرباء ومرافق","شحن ونقل","نثريات وضيافة","أخرى"])
        self.exp_amount = QDoubleSpinBox(); self.exp_amount.setMaximum(1000000); self.exp_amount.setDecimals(2)
        self.exp_note = QLineEdit(); self.exp_note.setPlaceholderText("ملاحظة (اختياري)"); self.exp_note.setStyleSheet(INPUT_STYLE)
        self.exp_safe = QComboBox(); self.exp_safe.addItems(["كاش", "إنستاباي", "محفظة", "بنك"])
        btn_add = QPushButton("➕ إضافة"); btn_add.setStyleSheet(BTN.format(bg=RED,hv=RED2)); btn_add.clicked.connect(self.add_expense)
        
        fr.addWidget(QLabel("النوع:")); fr.addWidget(self.exp_type)
        fr.addWidget(QLabel("المبلغ:")); fr.addWidget(self.exp_amount)
        fr.addWidget(QLabel("من:")); fr.addWidget(self.exp_safe)
        fr.addWidget(self.exp_note); fr.addWidget(btn_add)
        add_frame.setLayout(fr); layout.addWidget(add_frame)

        df, self.exp_date, btn_s, btn_a = make_date_bar("📅 مصروفات يوم:")
        btn_s.clicked.connect(self.load_exp_by_date); btn_a.clicked.connect(self.load_expenses_data)
        layout.addWidget(df)

        bl = QHBoxLayout(); bl.setSpacing(8)
        b_edit = QPushButton("⚙️  تعديل / حذف مصروف"); b_edit.setStyleSheet(BTN.format(bg=GOLD_DARK,hv=GOLD))
        b_edit.clicked.connect(self.edit_or_delete_expense)
        bl.addWidget(b_edit); bl.addStretch(); layout.addLayout(bl)

        self.exp_table = QTableWidget(); self.exp_table.setColumnCount(6)
        self.exp_table.setHorizontalHeaderLabels(["كود","النوع","المبلغ","ملاحظة","التاريخ","الخزنة"])
        self.exp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.exp_table.setColumnHidden(0, True)
        style_table(self.exp_table); layout.addWidget(self.exp_table)

        self.lbl_exp_total = QLabel("إجمالي المصروفات: 0.00 ج")
        self.lbl_exp_total.setStyleSheet(f"font-size:14px;font-weight:bold;color:{RED2};padding:6px;")
        layout.addWidget(self.lbl_exp_total)
        w.setLayout(layout); return w

    def add_expense(self):
        val = self.exp_amount.value()
        if val <= 0: return
        safe = self.exp_safe.currentText()
        
        conn = sqlite3.connect('lina_store.db')
        try:
            c = conn.cursor()
            c.execute("BEGIN TRANSACTION")
            c.execute("SELECT balance FROM cash_boxes WHERE name=?", (safe,))
            b = c.fetchone()
            if not b or b[0] < val:
                QMessageBox.warning(self, "خطأ", "رصيد الخزنة لا يكفي!")
                conn.rollback(); return
            
            c.execute("INSERT INTO expenses (type,amount,note,date,safe_name) VALUES (?,?,?,?,?)",
                      (self.exp_type.currentText(),val,self.exp_note.text().strip(),datetime.now().strftime("%Y-%m-%d %H:%M"), safe))
            ref = c.lastrowid
            update_safe_balance(safe, -val, "مصروفات", ref, f"{self.exp_type.currentText()} - {self.exp_note.text()}", self.current_user, conn)
            conn.commit()
            
            self.exp_amount.setValue(0); self.exp_note.clear()
            self.load_expenses_data(); self.update_quick_stats()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "خطأ", str(e))
        finally:
            conn.close()

    def load_expenses_data(self):
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT id,type,amount,note,date,safe_name FROM expenses ORDER BY id DESC")
        self._fill_exp(c.fetchall()); conn.close()

    def load_exp_by_date(self):
        d = self.exp_date.date().toString("yyyy-MM-dd")
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT id,type,amount,note,date,safe_name FROM expenses WHERE substr(date,1,10)=? ORDER BY id DESC", (d,))
        self._fill_exp(c.fetchall()); conn.close()

    def _fill_exp(self, rows):
        total = sum(r[2] for r in rows)
        self.exp_table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            for j,val in enumerate(r):
                item = QTableWidgetItem(fmt(val) if j==2 else str(val) if val else "-")
                item.setTextAlignment(Qt.AlignCenter); self.exp_table.setItem(i,j,item)
        self.lbl_exp_total.setText(f"إجمالي المصروفات: {fmt(total)} ج")

    def edit_or_delete_expense(self):
        row = self.exp_table.currentRow()
        if row < 0: QMessageBox.warning(self,"تنبيه","اختار مصروف من الجدول أولاً"); return
        exp_id = self.exp_table.item(row,0).text()
        exp_type = self.exp_table.item(row,1).text()
        old_amount = float(normalize(self.exp_table.item(row,2).text().replace(",","")))
        safe_name = self.exp_table.item(row,5).text()
        
        msg = QMessageBox(self); msg.setWindowTitle("خيارات المصروف"); msg.setText(f"{exp_type} - {fmt(old_amount)} ج\nاختر الإجراء:")
        b_del  = msg.addButton("حذف", QMessageBox.DestructiveRole)
        msg.addButton("إلغاء", QMessageBox.RejectRole); msg.exec_()

        if msg.clickedButton() == b_del:
            if QMessageBox.question(self,"تأكيد","هل متأكد من حذف المصروف واسترجاع المبلغ للخزنة؟") == QMessageBox.Yes:
                conn = sqlite3.connect('lina_store.db')
                try:
                    c = conn.cursor()
                    c.execute("BEGIN TRANSACTION")
                    c.execute("DELETE FROM expenses WHERE id=?", (exp_id,))
                    update_safe_balance(safe_name, old_amount, "حذف مصروف", exp_id, f"إلغاء مصروف {exp_type}", self.current_user, conn)
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                finally:
                    conn.close()
                self.load_all_data()

    # ==================== الموردين والمشتريات ====================
    def build_suppliers_tab(self):
        w = QWidget(); layout = QVBoxLayout(); layout.setContentsMargins(12,12,12,12); layout.setSpacing(10)

        sf, self.sup_search = make_search_bar("ابحث باسم المورد أو رقم الهاتف...")
        self.sup_search.textChanged.connect(self._filter_suppliers)
        layout.addWidget(sf)

        bl = QHBoxLayout(); bl.setSpacing(8)
        b1 = QPushButton("➕  إضافة مورد"); b1.setStyleSheet(BTN.format(bg=TEAL_MID,hv=TEAL_DARK)); b1.clicked.connect(self.add_supplier)
        b2 = QPushButton("⚙️  تعديل مورد"); b2.setStyleSheet(BTN.format(bg=GOLD_DARK,hv=GOLD)); b2.clicked.connect(self.edit_supplier)
        b3 = QPushButton("❌  إيقاف / تفعيل"); b3.setStyleSheet(BTN.format(bg=RED,hv=RED2)); b3.clicked.connect(self.toggle_supplier)
        b4 = QPushButton("💳  سداد دفعة"); b4.setStyleSheet(BTN.format(bg="#2E7D32",hv="#1B5E20")); b4.clicked.connect(self.pay_supplier)
        bl.addWidget(b1); bl.addWidget(b2); bl.addWidget(b3); bl.addWidget(b4); bl.addStretch(); layout.addLayout(bl)

        self.sup_table = QTableWidget(); self.sup_table.setColumnCount(8)
        self.sup_table.setHorizontalHeaderLabels(["كود","اسم المورد","الهاتف","الرصيد (عليه/له)","إجمالي الشراء","إجمالي المدفوع","الفواتير","الحالة"])
        self.sup_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        style_table(self.sup_table); layout.addWidget(self.sup_table)
        
        lbl = QLabel("💡 انقر مرتين على المورد لعرض كشف الحساب."); lbl.setStyleSheet("color:#666; font-style:italic;")
        layout.addWidget(lbl)
        
        self.sup_table.doubleClicked.connect(self.show_supplier_statement)
        w.setLayout(layout); return w

    def add_supplier(self):
        dlg = SupplierDialog()
        if dlg.exec_() == QDialog.Accepted:
            n, ph, addr, note, bal = dlg.get_data()
            conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
            try:
                c.execute("INSERT INTO suppliers (name, phone, address, notes, balance) VALUES (?,?,?,?,?)", (n, ph, addr, note, bal))
                conn.commit()
                self.load_suppliers()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "خطأ", "رقم الهاتف موجود مسبقاً!")
            finally:
                conn.close()

    def edit_supplier(self):
        row = self.sup_table.currentRow()
        if row < 0: QMessageBox.warning(self,"تنبيه","اختار مورد أولاً"); return
        sid = self.sup_table.item(row,0).text()
        
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT id, name, phone, address, notes, balance FROM suppliers WHERE id=?", (sid,))
        sup = c.fetchone(); conn.close()
        
        dlg = SupplierDialog(sup)
        if dlg.exec_() == QDialog.Accepted:
            n, ph, addr, note, bal = dlg.get_data()
            conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
            try:
                c.execute("UPDATE suppliers SET name=?, phone=?, address=?, notes=? WHERE id=?", (n, ph, addr, note, sid))
                conn.commit()
                self.load_suppliers()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "خطأ", "رقم الهاتف موجود لمورد آخر!")
            finally:
                conn.close()

    def toggle_supplier(self):
        row = self.sup_table.currentRow()
        if row < 0: QMessageBox.warning(self,"تنبيه","اختار مورد أولاً"); return
        sid = self.sup_table.item(row,0).text()
        status_txt = self.sup_table.item(row,7).text()
        new_status = 0 if status_txt == "نشط" else 1
        
        conn = sqlite3.connect('lina_store.db')
        conn.execute("UPDATE suppliers SET is_active=? WHERE id=?", (new_status, sid))
        conn.commit(); conn.close()
        self.load_suppliers()

    def pay_supplier(self):
        row = self.sup_table.currentRow()
        if row < 0: QMessageBox.warning(self,"تنبيه","اختار مورد أولاً"); return
        sid = self.sup_table.item(row,0).text()
        sname = self.sup_table.item(row,1).text()
        sbal = float(normalize(self.sup_table.item(row,3).text()))
        
        dlg = QDialog(self); dlg.setWindowTitle("سداد دفعة لمورد"); dlg.setFixedSize(350,220)
        dlg.setLayoutDirection(Qt.RightToLeft); dlg.setStyleSheet(f"background:{CREAM};")
        layout = QVBoxLayout(); form = QFormLayout()
        
        lbl_info = QLabel(f"المورد: {sname}\nالرصيد الحالي: {fmt(sbal)} ج")
        lbl_info.setStyleSheet("font-weight:bold;")
        layout.addWidget(lbl_info)
        
        amt_in = QDoubleSpinBox(); amt_in.setMaximum(10000000)
        safe_in = QComboBox(); safe_in.addItems(["كاش", "إنستاباي", "محفظة", "بنك"])
        note_in = QLineEdit()
        
        form.addRow("المبلغ المراد سداده:", amt_in)
        form.addRow("من خزنة:", safe_in)
        form.addRow("ملاحظة:", note_in)
        layout.addLayout(form)
        
        btn = QPushButton("✅ تأكيد السداد"); btn.setStyleSheet(BTN.format(bg=GOLD_DARK, hv=GOLD))
        layout.addWidget(btn); dlg.setLayout(layout)
        
        def do_pay():
            val = amt_in.value()
            if val <= 0: return
            safe = safe_in.currentText()
            conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
            try:
                c.execute("BEGIN TRANSACTION")
                c.execute("SELECT balance FROM cash_boxes WHERE name=?", (safe,))
                b = c.fetchone()
                if not b or b[0] < val:
                    QMessageBox.warning(dlg, "خطأ", "رصيد الخزنة لا يكفي!")
                    conn.rollback(); return
                
                dt = datetime.now().strftime("%Y-%m-%d %H:%M")
                c.execute("INSERT INTO supplier_payments (supplier_id, date, amount, payment_method, safe_id, note, user_name) VALUES (?,?,?,?,?,?,?)",
                          (sid, dt, val, safe, 0, note_in.text(), self.current_user))
                ref = c.lastrowid
                
                c.execute("UPDATE suppliers SET balance = balance - ?, total_paid = total_paid + ? WHERE id=?", (val, val, sid))
                c.execute("INSERT INTO supplier_transactions (supplier_id, date, type, ref_id, debit, credit, balance_after, note) VALUES (?,?,?,?,?,?,?,?)",
                          (sid, dt, "سداد دفعة", ref, 0, val, sbal - val, note_in.text()))
                
                update_safe_balance(safe, -val, "سداد مورد", ref, f"سداد للمورد {sname}", self.current_user, conn)
                log_audit(self.current_user, "سداد مورد", f"سداد {val} للمورد {sname} من {safe}", conn)
                
                conn.commit()
                dlg.accept()
                self.load_suppliers()
                self.update_safe_ui()
                QMessageBox.information(self, "نجاح", "تم تسجيل السداد بنجاح!")
            except Exception as e:
                conn.rollback(); QMessageBox.critical(dlg, "خطأ", str(e))
            finally: conn.close()
            
        btn.clicked.connect(do_pay)
        dlg.exec_()

    def show_supplier_statement(self):
        row = self.sup_table.currentRow()
        if row < 0: return
        sid = self.sup_table.item(row,0).text()
        
        dlg = QDialog(self); dlg.setWindowTitle("كشف حساب المورد"); dlg.setFixedSize(700,500)
        dlg.setLayoutDirection(Qt.RightToLeft); dlg.setStyleSheet(f"background:{CREAM};")
        layout = QVBoxLayout()
        
        t = QTableWidget(); t.setColumnCount(6)
        t.setHorizontalHeaderLabels(["التاريخ", "النوع", "المرجع", "مدين (عليه)", "دائن (له/سداد)", "الرصيد بعد العمليات"])
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        style_table(t); layout.addWidget(t)
        
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT date, type, ref_id, debit, credit, balance_after, note FROM supplier_transactions WHERE supplier_id=? ORDER BY id ASC", (sid,))
        rows = c.fetchall(); conn.close()
        
        t.setRowCount(len(rows))
        for i, r in enumerate(rows):
            t.setItem(i,0,QTableWidgetItem(str(r[0])))
            t.setItem(i,1,QTableWidgetItem(str(r[1])))
            t.setItem(i,2,QTableWidgetItem(str(r[2])))
            t.setItem(i,3,QTableWidgetItem(fmt(r[3])))
            t.setItem(i,4,QTableWidgetItem(fmt(r[4])))
            t.setItem(i,5,QTableWidgetItem(fmt(r[5])))
            
        dlg.setLayout(layout); dlg.exec_()

    def load_suppliers(self):
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT id, name, phone, balance, total_purchases, total_paid, invoices_count, is_active FROM suppliers ORDER BY name")
        rows = c.fetchall(); conn.close()
        self.sup_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.sup_table.setItem(i,0,QTableWidgetItem(str(r[0])))
            self.sup_table.setItem(i,1,QTableWidgetItem(str(r[1])))
            self.sup_table.setItem(i,2,QTableWidgetItem(str(r[2])))
            self.sup_table.setItem(i,3,QTableWidgetItem(fmt(r[3])))
            self.sup_table.setItem(i,4,QTableWidgetItem(fmt(r[4])))
            self.sup_table.setItem(i,5,QTableWidgetItem(fmt(r[5])))
            self.sup_table.setItem(i,6,QTableWidgetItem(str(r[6])))
            status = "نشط" if r[7] == 1 else "موقوف"
            item_s = QTableWidgetItem(status); item_s.setTextAlignment(Qt.AlignCenter)
            if r[7] == 0: item_s.setForeground(QColor(RED2))
            self.sup_table.setItem(i,7,item_s)

    def _filter_suppliers(self):
        txt = self.sup_search.text().strip()
        for r in range(self.sup_table.rowCount()):
            if not txt: self.sup_table.setRowHidden(r, False); continue
            n = self.sup_table.item(r,1); p = self.sup_table.item(r,2)
            match = (n and txt in n.text()) or (p and txt in p.text())
            self.sup_table.setRowHidden(r, not match)

    # ==================== الخزنة ====================
    def build_treasury_tab(self):
        w = QWidget(); layout = QVBoxLayout(); layout.setContentsMargins(12,12,12,12); layout.setSpacing(10)
        
        df, self.trs_date, btn_s, btn_a = make_date_bar("📅 كشف حركة يوم:")
        btn_s.clicked.connect(self.load_treasury_by_date); btn_a.clicked.connect(self.load_treasury_data)
        layout.addWidget(df)
        
        self.trs_table = QTableWidget(); self.trs_table.setColumnCount(8)
        self.trs_table.setHorizontalHeaderLabels(["التاريخ","الخزنة","النوع","المرجع","البيان","المبلغ","الرصيد بعد","المستخدم"])
        self.trs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        style_table(self.trs_table); layout.addWidget(self.trs_table)
        
        w.setLayout(layout); return w

    def load_treasury_data(self):
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT date, safe_name, type, ref_id, description, amount, balance_after, user_name FROM cash_transactions ORDER BY id DESC LIMIT 500")
        self._fill_treasury(c.fetchall()); conn.close()

    def load_treasury_by_date(self):
        d = self.trs_date.date().toString("yyyy-MM-dd")
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT date, safe_name, type, ref_id, description, amount, balance_after, user_name FROM cash_transactions WHERE substr(date,1,10)=? ORDER BY id DESC", (d,))
        self._fill_treasury(c.fetchall()); conn.close()
        
    def _fill_treasury(self, rows):
        self.trs_table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            for j,val in enumerate(r):
                item = QTableWidgetItem(fmt(val) if j in (5,6) else str(val) if val else "-")
                item.setTextAlignment(Qt.AlignCenter); self.trs_table.setItem(i,j,item)

    # ==================== العملاء والسحب ====================
    def build_customers_tab(self):
        w = QWidget(); layout = QVBoxLayout(); layout.setContentsMargins(12,12,12,12); layout.setSpacing(10)
        info = QLabel("⭐  العملاء اللي بيسجلوا تليفوناتهم محفوظين دايماً ومش بيتنسوا")
        info.setStyleSheet(f"background:#FFF8E1;color:#E65100;padding:8px;border-radius:6px;font-weight:bold;"); layout.addWidget(info)
        sf, self.cust_search = make_search_bar("ابحث باسم العميل أو رقمه...")
        self.cust_search.textChanged.connect(self._filter_customers); layout.addWidget(sf)
        df, self.cust_date, btn_s, btn_a = make_date_bar("📅 عملاء جديدين يوم:")
        btn_s.clicked.connect(self.load_cust_by_date); btn_a.clicked.connect(self.load_customers_data); layout.addWidget(df)
        bl = QHBoxLayout(); bl.setSpacing(8)
        b_edit = QPushButton("⚙️  تعديل / حذف عميل"); b_edit.setStyleSheet(BTN.format(bg=GOLD_DARK,hv=GOLD)); b_edit.clicked.connect(self.edit_or_delete_customer)
        bl.addWidget(b_edit); bl.addStretch(); layout.addLayout(bl)
        self.cust_table = QTableWidget(); self.cust_table.setColumnCount(4)
        self.cust_table.setHorizontalHeaderLabels(["اسم العميل","رقم التليفون","إجمالي مشترياته","آخر زيارة"])
        self.cust_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        style_table(self.cust_table); layout.addWidget(self.cust_table)
        w.setLayout(layout); return w

    def load_customers_data(self):
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT name,phone,total_spent,last_visit FROM customers ORDER BY total_spent DESC")
        self._fill_cust(c.fetchall()); conn.close()

    def load_cust_by_date(self):
        d = self.cust_date.date().toString("yyyy-MM-dd")
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT name,phone,total_spent,last_visit FROM customers WHERE last_visit=? ORDER BY total_spent DESC", (d,))
        self._fill_cust(c.fetchall()); conn.close()

    def _fill_cust(self, rows):
        self.cust_table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            for j,val in enumerate(r):
                item = QTableWidgetItem(fmt(val) if j==2 else str(val) if val else "-")
                item.setTextAlignment(Qt.AlignCenter); self.cust_table.setItem(i,j,item)

    def _filter_customers(self):
        txt = self.cust_search.text().strip()
        for r in range(self.cust_table.rowCount()):
            if not txt: self.cust_table.setRowHidden(r, False); continue
            n = self.cust_table.item(r,0); p = self.cust_table.item(r,1)
            match = (n and txt in n.text()) or (p and txt in p.text())
            self.cust_table.setRowHidden(r, not match)

    def edit_or_delete_customer(self):
        row = self.cust_table.currentRow()
        if row < 0: QMessageBox.warning(self,"تنبيه","اختار عميل من الجدول أولاً"); return
        cust_name = self.cust_table.item(row,0).text()
        cust_phone = self.cust_table.item(row,1).text()
        msg = QMessageBox(self); msg.setWindowTitle("خيارات العميل"); msg.setText(f"{cust_name} - {cust_phone}\nاختر الإجراء:")
        b_edit = msg.addButton("تعديل الاسم", QMessageBox.ActionRole); b_del  = msg.addButton("حذف نهائي", QMessageBox.DestructiveRole)
        msg.addButton("إلغاء", QMessageBox.RejectRole); msg.exec_()
        if msg.clickedButton() == b_edit:
            new_name, ok = self._ask_text("تعديل اسم العميل", "الاسم الجديد:", cust_name)
            if ok and new_name.strip():
                conn = sqlite3.connect('lina_store.db')
                conn.execute("UPDATE customers SET name=? WHERE phone=?", (new_name.strip(), cust_phone))
                conn.execute("UPDATE sales SET customer_name=? WHERE customer_phone=?", (new_name.strip(), cust_phone))
                conn.commit(); conn.close(); self.load_all_data()
        elif msg.clickedButton() == b_del:
            if QMessageBox.question(self,"تأكيد الحذف", f"هل متأكد من حذف {cust_name} نهائياً؟\nسجل مبيعاته السابق هيفضل موجود بس مش هيظهر في قايمة العملاء.") == QMessageBox.Yes:
                conn = sqlite3.connect('lina_store.db'); conn.execute("DELETE FROM customers WHERE phone=?", (cust_phone,)); conn.commit(); conn.close(); self.load_all_data()

    def _ask_text(self, title, label, default_text):
        dlg = QDialog(self); dlg.setWindowTitle(title); dlg.setFixedSize(340,150)
        dlg.setLayoutDirection(Qt.RightToLeft); dlg.setStyleSheet(f"background:{CREAM};")
        layout = QVBoxLayout(); lbl = QLabel(label); lbl.setStyleSheet(f"font-weight:bold;color:{TEAL_DARK};")
        inp = QLineEdit(default_text); inp.setStyleSheet(INPUT_STYLE)
        btn = QPushButton("✅ حفظ"); btn.setStyleSheet(BTN.format(bg=GOLD_DARK,hv=GOLD)); btn.clicked.connect(dlg.accept)
        layout.addWidget(lbl); layout.addWidget(inp); layout.addWidget(btn); dlg.setLayout(layout)
        ok = dlg.exec_() == QDialog.Accepted; return inp.text(), ok

    def build_raffle_tab(self):
        w = QWidget(); layout = QVBoxLayout(); layout.setContentsMargins(20,16,20,16); layout.setSpacing(14)
        lbl = QLabel("🎁  السحب بيختار عشوائي من العملاء اللي سجلوا تليفوناتهم")
        lbl.setStyleSheet(f"font-size:13px;font-weight:bold;color:white;background:{GOLD_DARK};padding:10px;border-radius:8px;"); lbl.setAlignment(Qt.AlignCenter); layout.addWidget(lbl)
        self.lbl_raffle_count = QLabel("عدد العملاء المشاركين: 0"); self.lbl_raffle_count.setStyleSheet(f"font-size:13px;color:{TEAL_DARK};"); layout.addWidget(self.lbl_raffle_count)
        self.lbl_raffle_res = QLabel("جاهزين نعمل السحب؟")
        self.lbl_raffle_res.setStyleSheet(f"font-size:24px;font-weight:bold;color:{TEAL_DARK};background:{CREAM2};padding:40px;border-radius:12px;border:2px solid {GOLD};"); self.lbl_raffle_res.setAlignment(Qt.AlignCenter); layout.addWidget(self.lbl_raffle_res)
        self.btn_roll = QPushButton("🎯  ابدأ السحب"); self.btn_roll.setMinimumHeight(50)
        self.btn_roll.clicked.connect(self.start_raffle); self.btn_roll.setStyleSheet(BTN.format(bg=GOLD_DARK,hv=GOLD)); layout.addWidget(self.btn_roll)
        lh = QLabel("آخر الفائزين:"); lh.setStyleSheet(f"font-weight:bold;color:{TEAL_DARK};"); layout.addWidget(lh)
        self.raffle_table = QTableWidget(); self.raffle_table.setColumnCount(3)
        self.raffle_table.setHorizontalHeaderLabels(["التاريخ","الاسم","التليفون"])
        self.raffle_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        style_table(self.raffle_table); layout.addWidget(self.raffle_table)
        w.setLayout(layout); return w

    def start_raffle(self):
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT name,phone FROM customers WHERE phone!='' AND phone IS NOT NULL")
        self.candidates = c.fetchall(); conn.close()
        self.lbl_raffle_count.setText(f"عدد العملاء المشاركين: {len(self.candidates)}")
        if not self.candidates: QMessageBox.warning(self,"فشل","لا توجد أرقام هواتف مسجلة!"); return
        self.btn_roll.setEnabled(False); self.counter = 0
        self.raffle_anim = QTimer(self); self.raffle_anim.timeout.connect(self._roll); self.raffle_anim.start(70)

    def _roll(self):
        self.counter += 1
        if self.counter < 18:
            self.lbl_raffle_res.setText(f"🔄 {random.choice(self.candidates)[0]}...")
        else:
            self.raffle_anim.stop(); winner = random.choice(self.candidates)
            self.lbl_raffle_res.setText(f"🎉 الفائز: {winner[0]}\n📱 {winner[1]}")
            conn = sqlite3.connect('lina_store.db')
            conn.execute("INSERT INTO raffle_winners (name,phone,date) VALUES (?,?,?)", (winner[0],winner[1],datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit(); conn.close(); self.load_raffle_history(); self.btn_roll.setEnabled(True)

    def load_raffle_history(self):
        conn = sqlite3.connect('lina_store.db'); c = conn.cursor()
        c.execute("SELECT date,name,phone FROM raffle_winners ORDER BY id DESC")
        rows = c.fetchall(); conn.close()
        self.raffle_table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            for j,val in enumerate(r):
                item = QTableWidgetItem(str(val)); item.setTextAlignment(Qt.AlignCenter); self.raffle_table.setItem(i,j,item)

    def show_settings_dialog(self):
        dlg = SettingsDialog(self.store_name,self.alert_limit,self)
        if dlg.exec_() == QDialog.Accepted:
            n,l = dlg.get_data()
            conn = sqlite3.connect('lina_store.db'); conn.execute("UPDATE settings SET store_name=?,alert_limit=? WHERE id=1",(n,l)); conn.commit(); conn.close()
            self.store_name,self.alert_limit = n,l
            self.header.setText(f"لينا ستور  |  البائع: {self.current_user}"); self.load_all_data()

    def load_all_data(self):
        self.load_data(); self.load_sales_data(); self.load_expenses_data()
        self.load_customers_data(); self.load_raffle_history()
        self.load_suppliers(); self.load_treasury_data()
        self.apply_report(); self.update_quick_stats()
        self.refresh_analytics()

# ==================== تشغيل ====================

if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLE)
    login = LoginWindow()
    if login.exec_() == QDialog.Accepted:
        window = LinaStorePro(login.selected_user)
        window.show()
        sys.exit(app.exec_())