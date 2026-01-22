import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import csv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# =======================
# قاعدة البيانات
# =======================
conn = sqlite3.connect('accounting.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    currency TEXT NOT NULL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    amount REAL,
    currency TEXT,
    issue_date TEXT,
    due_date TEXT,
    status TEXT DEFAULT 'Unpaid',
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER,
    amount REAL,
    currency TEXT,
    payment_date TEXT,
    FOREIGN KEY(invoice_id) REFERENCES invoices(invoice_id)
)
''')

conn.commit()

# =======================
# وظائف البرنامج
# =======================

def add_customer(name, phone, email, currency):
    c.execute('INSERT INTO customers (name, phone, email, currency) VALUES (?, ?, ?, ?)', (name, phone, email, currency))
    conn.commit()
    messagebox.showinfo('نجاح', f'تم إضافة العميل: {name}')


def add_invoice(customer_id, amount, currency, issue_date, due_date):
    c.execute('INSERT INTO invoices (customer_id, amount, currency, issue_date, due_date) VALUES (?, ?, ?, ?, ?)',
              (customer_id, amount, currency, issue_date, due_date))
    conn.commit()
    messagebox.showinfo('نجاح', f'تم إضافة فاتورة للعميل ID {customer_id}')


def add_payment(invoice_id, amount, currency, payment_date):
    c.execute('INSERT INTO payments (invoice_id, amount, currency, payment_date) VALUES (?, ?, ?, ?)',
              (invoice_id, amount, currency, payment_date))
    c.execute('SELECT SUM(amount) FROM payments WHERE invoice_id=?', (invoice_id,))
    total_paid = c.fetchone()[0] or 0
    c.execute('SELECT amount FROM invoices WHERE invoice_id=?', (invoice_id,))
    invoice_amount = c.fetchone()[0]
    status = 'Paid' if total_paid >= invoice_amount else 'Partial'
    c.execute('UPDATE invoices SET status=? WHERE invoice_id=?', (status, invoice_id))
    conn.commit()
    messagebox.showinfo('نجاح', f'تم تسجيل الدفع للفواتير ID {invoice_id}')


def get_customers():
    c.execute('SELECT customer_id, name FROM customers')
    return c.fetchall()


def get_invoices_by_customer(customer_id):
    c.execute('SELECT invoice_id, amount, currency, issue_date, due_date, status FROM invoices WHERE customer_id=?', (customer_id,))
    return c.fetchall()


def get_payments_by_invoice(invoice_id):
    c.execute('SELECT amount, currency, payment_date FROM payments WHERE invoice_id=?', (invoice_id,))
    return c.fetchall()

# =======================
# واجهة رسومية
# =======================

class AccountingApp:
    def __init__(self, master):
        self.master = master
        master.title('برنامج المحاسبة للتحصيل')
        master.geometry('800x600')

        tab_control = ttk.Notebook(master)
        self.tab_customers = ttk.Frame(tab_control)
        self.tab_invoices = ttk.Frame(tab_control)
        self.tab_payments = ttk.Frame(tab_control)
        self.tab_statements = ttk.Frame(tab_control)

        tab_control.add(self.tab_customers, text='العملاء')
        tab_control.add(self.tab_invoices, text='الفواتير')
        tab_control.add(self.tab_payments, text='المدفوعات')
        tab_control.add(self.tab_statements, text='كشف حساب')
        tab_control.pack(expand=1, fill='both')

        self.create_customers_tab()
        self.create_invoices_tab()
        self.create_payments_tab()
        self.create_statements_tab()

    # ======= العملاء =======
    def create_customers_tab(self):
        tk.Label(self.tab_customers, text='الاسم').grid(row=0, column=0)
        self.customer_name = tk.Entry(self.tab_customers)
        self.customer_name.grid(row=0, column=1)

        tk.Label(self.tab_customers, text='الهاتف').grid(row=1, column=0)
        self.customer_phone = tk.Entry(self.tab_customers)
        self.customer_phone.grid(row=1, column=1)

        tk.Label(self.tab_customers, text='البريد الإلكتروني').grid(row=2, column=0)
        self.customer_email = tk.Entry(self.tab_customers)
        self.customer_email.grid(row=2, column=1)

        tk.Label(self.tab_customers, text='العملة (₪/د.ع/$)').grid(row=3, column=0)
        self.customer_currency = tk.Entry(self.tab_customers)
        self.customer_currency.grid(row=3, column=1)

        tk.Button(self.tab_customers, text='إضافة عميل', command=self.add_customer_gui).grid(row=4, column=1)

    def add_customer_gui(self):
        add_customer(self.customer_name.get(), self.customer_phone.get(), self.customer_email.get(), self.customer_currency.get())
        self.customer_name.delete(0, tk.END)
        self.customer_phone.delete(0, tk.END)
        self.customer_email.delete(0, tk.END)
        self.customer_currency.delete(0, tk.END)

    # ======= الفواتير =======
    def create_invoices_tab(self):
        tk.Label(self.tab_invoices, text='اختيار العميل').grid(row=0, column=0)
        self.invoice_customer = ttk.Combobox(self.tab_invoices, values=[f'{c[0]} - {c[1]}' for c in get_customers()])
        self.invoice_customer.grid(row=0, column=1)

        tk.Label(self.tab_invoices, text='المبلغ').grid(row=1, column=0)
        self.invoice_amount = tk.Entry(self.tab_invoices)
        self.invoice_amount.grid(row=1, column=1)

        tk.Label(self.tab_invoices, text='العملة (₪/د.ع/$)').grid(row=2, column=0)
        self.invoice_currency = tk.Entry(self.tab_invoices)
        self.invoice_currency.grid(row=2, column=1)

        tk.Label(self.tab_invoices, text='تاريخ الإصدار (YYYY-MM-DD)').grid(row=3, column=0)
        self.invoice_issue_date = tk.Entry(self.tab_invoices)
        self.invoice_issue_date.grid(row=3, column=1)

        tk.Label(self.tab_invoices, text='تاريخ الاستحقاق (YYYY-MM-DD)').grid(row=4, column=0)
        self.invoice_due_date = tk.Entry(self.tab_invoices)
        self.invoice_due_date.grid(row=4, column=1)

        tk.Button(self.tab_invoices, text='إضافة فاتورة', command=self.add_invoice_gui).grid(row=5, column=1)

    def add_invoice_gui(self):
        customer_id = int(self.invoice_customer.get().split(' - ')[0])
        add_invoice(customer_id, float(self.invoice_amount.get()), self.invoice_currency.get(), self.invoice_issue_date.get(), self.invoice_due_date.get())
        self.invoice_amount.delete(0, tk.END)
        self.invoice_currency.delete(0, tk.END)
        self.invoice_issue_date.delete(0, tk.END)
        self.invoice_due_date.delete(0, tk.END)

    # ======= المدفوعات =======
    def create_payments_tab(self):
        tk.Label(self.tab_payments, text='رقم الفاتورة').grid(row=0, column=0)
        self.payment_invoice_id = tk.Entry(self.tab_payments)
        self.payment_invoice_id.grid(row=0, column=1)

        tk.Label(self.tab_payments, text='المبلغ المدفوع').grid(row=1, column=0)
        self.payment_amount = tk.Entry(self.tab_payments)
        self.payment_amount.grid(row=1, column=1)

        tk.Label(self.tab_payments, text='العملة (₪/د.ع/$)').grid(row=2, column=0)
        self.payment_currency = tk.Entry(self.tab_payments)
        self.payment_currency.grid(row=2, column=1)

        tk.Label(self.tab_payments, text='تاريخ الدفع (YYYY-MM-DD)').grid(row=3, column=0)
        self.payment_date = tk.Entry(self.tab_payments)
        self.payment_date.grid(row=3, column=1)

        tk.Button(self.tab_payments, text='تسجيل دفع', command=self.add_payment_gui).grid(row=4, column=1)

    def add_payment_gui(self):
        add_payment(int(self.payment_invoice_id.get()), float(self.payment_amount.get()), self.payment_currency.get(), self.payment_date.get())
        self.payment_invoice_id.delete(0, tk.END)
        self.payment_amount.delete(0, tk.END)
        self.payment_currency.delete(0, tk.END)
        self.payment_date.delete(0, tk.END)

    # ======= كشف الحساب =======
    def create_statements_tab(self):
        tk.Label(self.tab_statements, text='اختر العميل').grid(row=0, column=0)
        self.statement_customer = ttk.Combobox(self.tab_statements, values=[f'{c[0]} - {c[1]}' for c in get_customers()])
        self.statement_customer.grid(row=0, column=1)
        tk.Button(self.tab_statements, text='عرض كشف الحساب', command=self.show_statement).grid(row=1, column=1)

        self.statement_text = tk.Text(self.tab_statements, width=100, height=25)
        self.statement_text.grid(row=2, column=0, columnspan=4)

        tk.Button(self.tab_statements, text='تصدير CSV', command=self.export_csv).grid(row=3, column=0)
        tk.Button(self.tab_statements, text='تصدير PDF', command=self.export_pdf).grid(row=3, column=1)

    def show_statement(self):
        self.statement_text.delete(1.0, tk.END)
        customer_id = int(self.statement_customer.get().split(' - ')[0])
        c.execute('SELECT name FROM customers WHERE customer_id=?', (customer_id,))
        customer_name = c.fetchone()[0]
        self.statement_text.insert(tk.END, f'كشف حساب العميل: {customer_name}\n\n')

        invoices = get_invoices_by_customer(customer_id)
        total_invoices = 0
        total_paid = 0

        for inv in invoices:
            invoice_id, amount, currency, issue_date, due_date, status = inv
            self.statement_text.insert(tk.END, f'فاتورة ID {invoice_id} - المبلغ: {amount} {currency} - الحالة: {status} - إصدار: {issue_date} - استحقاق: {due_date}\n')
            total_invoices += amount
            payments = get_payments_by_invoice(invoice_id)
            paid_sum = sum([p[0] for p in payments])
            total_paid += paid_sum
            self.statement_text.insert(tk.END, f'  المدفوع: {paid_sum} {currency}\n')

        balance = total_invoices - total_paid
        self.statement_text.insert(tk.END, f'المجموع: {total_invoices}, المدفوع: {total_paid}, الرصيد الحالي: {balance}\n')

    def export_csv(self):
        customer_id = int(self.statement_customer.get().split(' - ')[0])
        invoices = get_invoices_by_customer(customer_id)
        filename = f'statement_customer_{customer_id}.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['فاتورة ID', 'المبلغ', 'العملة', 'تاريخ الإصدار', 'تاريخ الاستحقاق', 'الحالة', 'المدفوع'])
            for inv in invoices:
                invoice_id, amount, currency, issue_date, due_date, status = inv
                payments = get_payments_by_invoice(invoice_id)
                paid_sum = sum([p[0] for p in payments])
                writer.writerow([invoice_id, amount, currency, issue_date, due_date, status, paid_sum])
        messagebox.showinfo('نجاح', f'تم تصدير كشف الحساب إلى {filename}')

    def export_pdf(self):
        customer_id = int(self.statement_customer.get().split(' - ')[0])
        invoices = get_invoices_by_customer(customer_id)
        c.execute('SELECT name FROM customers WHERE customer_id=?', (customer_id,))
        customer_name = c.fetchone()[0]

        filename = f'statement_customer_{customer_id}.pdf'
        pdf = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        pdf.setFont('Helvetica', 12)
        y = height - 50
        pdf.drawString(50, y, f'كشف حساب العميل: {customer_name}')
        y -= 30

        pdf.drawString(50, y, 'فاتورة ID | المبلغ | العملة | إصدار | استحقاق | الحالة | المدفوع')
        y -= 20

        for inv in invoices:
            invoice_id, amount, currency, issue_date, due_date, status = inv
            payments = get_payments_by_invoice(invoice_id)
            paid_sum = sum([p[0] for p in payments])
            line = f'{invoice_id} | {amount} | {currency} | {issue_date} | {due_date} | {status} | {paid_sum}'
            pdf.drawString(50, y, line)
            y -= 20
            if y < 50:
                pdf.showPage()
                pdf.setFont('Helvetica', 12)
                y = height - 50

        total_invoices = sum([inv[1] for inv in invoices])
        total_paid = sum([sum([p[0] for p in get_payments_by_invoice(inv[0])]) for inv in invoices])
        balance = total_invoices - total_paid
        pdf.drawString(50, y, f'المجموع: {total_invoices}, المدفوع: {total_paid}, الرصيد الحالي: {balance}')
        pdf.save()
        messagebox.showinfo('نجاح', f'تم تصدير كشف الحساب إلى {filename}')


if __name__ == '__main__':
    root = tk.Tk()
    app = AccountingApp(root)
    root.mainloop()
