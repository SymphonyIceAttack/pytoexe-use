import sys, sqlite3, csv
from datetime import date
from PySide6.QtWidgets import *
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

DB = "DIPSMS.db"

# ---------------- DATABASE INIT ----------------
def init_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS pharmacy(
        id INTEGER PRIMARY KEY,
        name TEXT, address TEXT, phone TEXT, vat TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS suppliers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS purchases(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id INTEGER,
        entry_date TEXT,
        total REAL,
        payment_type TEXT,
        paid REAL,
        credit REAL,
        cycle_days INTEGER,
        remarks TEXT
    )""")
    con.commit()
    con.close()

# ---------------- PREVIEW WINDOW ----------------
class PreviewWindow(QDialog):
    def __init__(self, data, headers, title="Preview"):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(800, 500)
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(data))
        for i, row in enumerate(data):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        self.table.resizeColumnsToContents()
        layout.addWidget(self.table)
        btn = QPushButton("Export to CSV")
        btn.clicked.connect(lambda: self.export_csv(data, headers))
        layout.addWidget(btn)
        self.setLayout(layout)

    def export_csv(self, data, headers):
        path, _ = QFileDialog.getSaveFileName(self, "", "", "CSV (*.csv)")
        if not path: return
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerows(data)
        QMessageBox.information(self, "Done", "CSV exported successfully!")

# ---------------- MAIN APP ----------------
class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DIP SUPPLIER MANAGEMENT SYSTEM")
        self.resize(1100, 700)

        tabs = QTabWidget()
        tabs.addTab(self.pharmacy_tab(), "Pharmacy Profile")
        tabs.addTab(self.supplier_tab(), "Suppliers")
        tabs.addTab(self.purchase_tab(), "Purchase / Payment")
        tabs.addTab(self.report_tab(), "Reports & Ledger")
        tabs.addTab(self.import_tab(), "CSV Import")

        self.setCentralWidget(tabs)
        self.load_suppliers()
        self.load_pharmacy()

    # ---------------- PHARMACY ----------------
    def pharmacy_tab(self):
        w = QWidget()
        f = QFormLayout()
        self.ph_name = QLineEdit()
        self.ph_addr = QLineEdit()
        self.ph_phone = QLineEdit()
        self.ph_vat = QLineEdit()
        btn = QPushButton("Save Pharmacy Details")
        btn.clicked.connect(self.save_pharmacy)
        for label, widget in [("Pharmacy Name", self.ph_name),
                              ("Address", self.ph_addr),
                              ("Phone", self.ph_phone),
                              ("VAT Number", self.ph_vat)]:
            f.addRow(label, widget)
        f.addRow(btn)
        w.setLayout(f)
        return w

    def save_pharmacy(self):
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute("DELETE FROM pharmacy")
        cur.execute("INSERT INTO pharmacy VALUES(1,?,?,?,?)",
                    (self.ph_name.text(), self.ph_addr.text(),
                     self.ph_phone.text(), self.ph_vat.text()))
        con.commit(); con.close()
        QMessageBox.information(self, "Saved", "Pharmacy details saved")

    def load_pharmacy(self):
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute("SELECT name,address,phone,vat FROM pharmacy")
        r = cur.fetchone()
        con.close()
        if r:
            self.ph_name.setText(r[0])
            self.ph_addr.setText(r[1])
            self.ph_phone.setText(r[2])
            self.ph_vat.setText(r[3])

    # ---------------- SUPPLIERS ----------------
    def supplier_tab(self):
        w = QWidget()
        l = QVBoxLayout()
        self.sup = QLineEdit()
        btn = QPushButton("Add Supplier")
        btn.clicked.connect(self.add_supplier)
        l.addWidget(QLabel("Supplier Name"))
        l.addWidget(self.sup)
        l.addWidget(btn)
        w.setLayout(l)
        return w

    def add_supplier(self):
        if not self.sup.text(): return
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute("INSERT OR IGNORE INTO suppliers(name) VALUES(?)", (self.sup.text(),))
        con.commit(); con.close()
        self.sup.clear()
        self.load_suppliers()

    # ---------------- PURCHASE ----------------
    def purchase_tab(self):
        w = QWidget()
        f = QFormLayout()
        self.cmb = QComboBox()
        self.dt = QDateEdit(QDate.currentDate())
        self.dt.setCalendarPopup(True)
        self.total = QLineEdit()
        self.pay_type = QComboBox(); self.pay_type.addItems(["Cash", "Cheque", "Credit"])
        self.paid = QLineEdit()
        self.cycle = QComboBox(); self.cycle.addItems(["0", "30", "60", "90"])
        self.rem = QLineEdit()
        btn = QPushButton("Save & Print Payment Slip")
        btn.clicked.connect(self.save_purchase)
        for label, widget in [("Supplier", self.cmb),
                              ("Date", self.dt),
                              ("Total Bill", self.total),
                              ("Payment Type", self.pay_type),
                              ("Paid Amount", self.paid),
                              ("Credit Cycle", self.cycle),
                              ("Remarks", self.rem)]:
            f.addRow(label, widget)
        f.addRow(btn)
        w.setLayout(f)
        return w

    def save_purchase(self):
        total = float(self.total.text())
        paid = float(self.paid.text() or 0)
        credit = total - paid
        con = sqlite3.connect(DB); cur = con.cursor()
        cur.execute("""INSERT INTO purchases
        (supplier_id,entry_date,total,payment_type,paid,credit,cycle_days,remarks)
        VALUES((SELECT id FROM suppliers WHERE name=?),?,?,?,?,?,?,?)""",
                    (self.cmb.currentText(), self.dt.date().toString("yyyy-MM-dd"),
                     total, self.pay_type.currentText(), paid, credit,
                     int(self.cycle.currentText()), self.rem.text()))
        con.commit(); con.close()
        self.print_slip(total, paid, credit)
        QMessageBox.information(self, "Saved", "Purchase saved & slip generated")

    # ---------------- PAYMENT SLIP ----------------
    def print_slip(self, total, paid, credit):
        con = sqlite3.connect(DB); cur = con.cursor()
        cur.execute("SELECT name,address,phone,vat FROM pharmacy"); ph = cur.fetchone(); con.close()
        html = f"""
        <h2>{ph[0]}</h2>
        <p>{ph[1]}<br>Phone: {ph[2]}<br>VAT: {ph[3]}</p>
        <hr>
        <h3>Payment Slip</h3>
        <p>Supplier: {self.cmb.currentText()}</p>
        <p>Date: {self.dt.date().toString("dd-MM-yyyy")}</p>
        <p>Total: {total}</p>
        <p>Paid: {paid}</p>
        <p>Credit: {credit}</p>
        <p>Mode: {self.pay_type.currentText()}</p>
        """
        doc = QTextDocument(); doc.setHtml(html)
        printer = QPrinter(QPrinter.HighResolution); printer.setPageSize(QPrinter.A4)
        dlg = QPrintDialog(printer, self)
        if dlg.exec(): doc.print_(printer)

    # ---------------- REPORTS ----------------
    def report_tab(self):
        w = QWidget(); l = QVBoxLayout()
        btns = [
            ("Supplier-wise Payment Report", self.rep_supplier_preview),
            ("Payment Mode Summary", self.rep_payment_preview),
            ("Supplier Ledger with Balance", self.ledger_preview),
            ("Monthly Purchase Report", self.monthly_preview),
            ("Advance Cheque / Credit Register", self.advance_preview)
        ]
        for t,f in btns: l.addWidget(QPushButton(t, clicked=f))
        w.setLayout(l); return w

    # ---------------- PREVIEW FUNCTIONS ----------------
    def rep_supplier_preview(self):
        con = sqlite3.connect(DB); cur = con.cursor()
        cur.execute("""SELECT s.name,p.payment_type,SUM(p.total) FROM purchases p
        JOIN suppliers s ON s.id=p.supplier_id GROUP BY s.name,p.payment_type""")
        data = cur.fetchall(); con.close()
        PreviewWindow(data, ["Supplier","Payment Type","Amount"], "Supplier Payment Report").exec()

    def rep_payment_preview(self):
        con = sqlite3.connect(DB); cur = con.cursor()
        cur.execute("SELECT payment_type,SUM(total) FROM purchases GROUP BY payment_type")
        data = cur.fetchall(); con.close()
        PreviewWindow(data, ["Payment Type","Total"], "Payment Mode Summary").exec()

    def ledger_preview(self):
        con = sqlite3.connect(DB); cur = con.cursor()
        cur.execute("""SELECT s.name, SUM(p.total) as total_purchase, SUM(p.paid) as total_paid,
        SUM(p.credit) as balance FROM suppliers s
        LEFT JOIN purchases p ON s.id=p.supplier_id GROUP BY s.id""")
        data = cur.fetchall(); con.close()
        PreviewWindow(data, ["Supplier","Total Purchase","Total Paid","Balance"], "Supplier Ledger").exec()

    def monthly_preview(self):
        con = sqlite3.connect(DB); cur = con.cursor()
        cur.execute("""SELECT strftime('%Y-%m',entry_date) as month, s.name, SUM(total)
        FROM purchases p JOIN suppliers s ON s.id=p.supplier_id GROUP BY month, s.id""")
        data = cur.fetchall(); con.close()
        PreviewWindow(data, ["Month","Supplier","Total Purchase"], "Monthly Purchase Report").exec()

    def advance_preview(self):
        con = sqlite3.connect(DB); cur = con.cursor()
        cur.execute("""SELECT s.name, entry_date, payment_type, paid, credit
        FROM purchases p JOIN suppliers s ON s.id=p.supplier_id
        WHERE payment_type IN ('Cheque','Credit')""")
        data = cur.fetchall(); con.close()
        PreviewWindow(data, ["Supplier","Date","Mode","Paid","Credit"], "Advance Cheque / Credit Register").exec()

    # ---------------- CSV IMPORT ----------------
    def import_tab(self):
        w = QWidget(); l = QVBoxLayout(); btn = QPushButton("Import Purchase CSV"); btn.clicked.connect(self.import_csv); l.addWidget(btn); w.setLayout(l); return w

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "", "", "CSV (*.csv)"); 
        if not path: return
        con = sqlite3.connect(DB); cur = con.cursor()
        with open(path,newline="") as f: r=csv.DictReader(f); 
        for row in r:
            cur.execute("INSERT OR IGNORE INTO suppliers(name) VALUES(?)",(row["Vendor Name"],))
            cur.execute("""INSERT INTO purchases
            (supplier_id,entry_date,total,payment_type,paid,credit,cycle_days,remarks)
            VALUES((SELECT id FROM suppliers WHERE name=?),?,?,?,?,?,?,?)""",
                        (row["Vendor Name"],row["Date"],float(row["Total Incl. VAT"]),
                         "Credit",float(row["Total Incl. VAT"]),float(row["Total Incl. VAT"]),30,row.get("Remarks","")))
        con.commit(); con.close(); self.load_suppliers(); QMessageBox.information(self,"Done","CSV imported")

    # ---------------- UTIL ----------------
    def load_suppliers(self):
        self.cmb.clear()
        con = sqlite3.connect(DB); cur = con.cursor()
        cur.execute("SELECT name FROM suppliers ORDER BY name")
        for r in cur.fetchall(): self.cmb.addItem(r[0])
        con.close()

# ---------------- RUN ----------------
if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec())
