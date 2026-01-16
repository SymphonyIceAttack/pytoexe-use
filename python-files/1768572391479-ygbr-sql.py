import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date, timedelta

# ================= DATABASE =================
def connect_db():
    return sqlite3.connect("gym.db")

def setup_db():
    conn = connect_db()
    c = conn.cursor()

    # جدول المستخدمين
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT,
        password TEXT
    )
    """)

    # جدول المتدربين
    c.execute("""
    CREATE TABLE IF NOT EXISTS trainees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        age INTEGER
    )
    """)

    # جدول الاشتراكات
    c.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trainee_id INTEGER,
        start_date TEXT,
        end_date TEXT,
        price REAL,
        paid TEXT
    )
    """)

    # مستخدم افتراضي
    c.execute("SELECT * FROM users")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES ('admin', '1234')")

    conn.commit()
    conn.close()

# ================= MAIN APP =================
def main_app():
    root = tk.Tk()
    root.title("نظام إدارة الجيم")
    root.geometry("900x600")

    tabs = ttk.Notebook(root)

    # -------- المتدربين --------
    tab_trainees = ttk.Frame(tabs)
    tabs.add(tab_trainees, text="المتدربين")

    tk.Label(tab_trainees, text="الاسم").pack()
    name_e = tk.Entry(tab_trainees)
    name_e.pack()

    tk.Label(tab_trainees, text="الهاتف").pack()
    phone_e = tk.Entry(tab_trainees)
    phone_e.pack()

    tk.Label(tab_trainees, text="العمر").pack()
    age_e = tk.Entry(tab_trainees)
    age_e.pack()

    def add_trainee():
        if name_e.get() == "" or phone_e.get() == "" or age_e.get() == "":
            messagebox.showerror("خطأ", "الرجاء إدخال جميع البيانات")
            return
        conn = connect_db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO trainees VALUES (NULL, ?, ?, ?)",
            (name_e.get(), phone_e.get(), age_e.get())
        )
        conn.commit()
        conn.close()
        load_trainees()
        name_e.delete(0, tk.END)
        phone_e.delete(0, tk.END)
        age_e.delete(0, tk.END)

    tk.Button(tab_trainees, text="إضافة متدرب", command=add_trainee).pack(pady=5)

    cols = ("ID", "الاسم", "الهاتف", "العمر")
    trainees_table = ttk.Treeview(tab_trainees, columns=cols, show="headings")
    for col in cols:
        trainees_table.heading(col, text=col)
    trainees_table.pack(expand=True, fill="both")

    def load_trainees():
        trainees_table.delete(*trainees_table.get_children())
        conn = connect_db()
        c = conn.cursor()
        c.execute("SELECT * FROM trainees")
        for row in c.fetchall():
            trainees_table.insert("", "end", values=row)
        conn.close()

    load_trainees()

    # تعديل متدرب
    def edit_trainee():
        selected = trainees_table.selection()
        if not selected:
            messagebox.showerror("خطأ", "اختر متدرب للتعديل")
            return
        trainee_id, name, phone, age = trainees_table.item(selected[0])["values"]

        edit_win = tk.Toplevel()
        edit_win.title("تعديل بيانات المتدرب")

        tk.Label(edit_win, text="الاسم").pack()
        name_e2 = tk.Entry(edit_win); name_e2.pack(); name_e2.insert(0, name)

        tk.Label(edit_win, text="الهاتف").pack()
        phone_e2 = tk.Entry(edit_win); phone_e2.pack(); phone_e2.insert(0, phone)

        tk.Label(edit_win, text="العمر").pack()
        age_e2 = tk.Entry(edit_win); age_e2.pack(); age_e2.insert(0, age)

        def save_changes():
            conn = connect_db()
            c = conn.cursor()
            c.execute("""
                UPDATE trainees SET name=?, phone=?, age=? WHERE id=?
            """, (name_e2.get(), phone_e2.get(), age_e2.get(), trainee_id))
            conn.commit()
            conn.close()
            load_trainees()
            edit_win.destroy()

        tk.Button(edit_win, text="حفظ التغييرات", command=save_changes).pack(pady=5)

    tk.Button(tab_trainees, text="تعديل المتدرب المحدد", command=edit_trainee).pack(pady=5)

    # حذف متدرب
    def delete_trainee():
        selected = trainees_table.selection()
        if not selected:
            messagebox.showerror("خطأ", "اختر متدرب للحذف")
            return
        trainee_id = trainees_table.item(selected[0])["values"][0]

        conn = connect_db()
        c = conn.cursor()
        # حذف الاشتراكات أولاً
        c.execute("DELETE FROM subscriptions WHERE trainee_id=?", (trainee_id,))
        # ثم حذف المتدرب
        c.execute("DELETE FROM trainees WHERE id=?", (trainee_id,))
        conn.commit()
        conn.close()
        load_trainees()
        load_subs()

    tk.Button(tab_trainees, text="حذف المتدرب المحدد", command=delete_trainee).pack(pady=5)

    # -------- الاشتراكات --------
    tab_subs = ttk.Frame(tabs)
    tabs.add(tab_subs, text="الاشتراكات")

    tk.Label(tab_subs, text="ID المتدرب").pack()
    trainee_id_e = tk.Entry(tab_subs)
    trainee_id_e.pack()

    tk.Label(tab_subs, text="مدة الاشتراك (أيام)").pack()
    days_e = tk.Entry(tab_subs)
    days_e.pack()

    tk.Label(tab_subs, text="السعر").pack()
    price_e = tk.Entry(tab_subs)
    price_e.pack()

    tk.Label(tab_subs, text="الحالة").pack()
    paid_var = tk.StringVar(value="مدفوع")
    ttk.Combobox(tab_subs, textvariable=paid_var,
                 values=["مدفوع", "غير مدفوع"]).pack()

    def add_subscription():
        if trainee_id_e.get() == "" or days_e.get() == "" or price_e.get() == "":
            messagebox.showerror("خطأ", "الرجاء إدخال جميع البيانات")
            return
        try:
            start = date.today()
            end = start + timedelta(days=int(days_e.get()))
        except ValueError:
            messagebox.showerror("خطأ", "مدة الاشتراك يجب أن تكون رقم")
            return

        conn = connect_db()
        c = conn.cursor()
        c.execute("SELECT * FROM trainees WHERE id=?", (trainee_id_e.get(),))
        if not c.fetchone():
            messagebox.showerror("خطأ", "ID المتدرب غير موجود")
            conn.close()
            return

        c.execute("""
            INSERT INTO subscriptions
            VALUES (NULL, ?, ?, ?, ?, ?)
        """, (
            trainee_id_e.get(),
            start.isoformat(),
            end.isoformat(),
            price_e.get(),
            paid_var.get()
        ))
        conn.commit()
        conn.close()
        load_subs()
        trainee_id_e.delete(0, tk.END)
        days_e.delete(0, tk.END)
        price_e.delete(0, tk.END)

    tk.Button(tab_subs, text="إضافة اشتراك", command=add_subscription).pack(pady=5)

    cols2 = ("ID", "متدرب", "بداية", "نهاية", "السعر", "الحالة")
    subs_table = ttk.Treeview(tab_subs, columns=cols2, show="headings")
    for col in cols2:
        subs_table.heading(col, text=col)
    subs_table.pack(expand=True, fill="both")

    def load_subs():
        subs_table.delete(*subs_table.get_children())
        conn = connect_db()
        c = conn.cursor()
        c.execute("""
            SELECT subscriptions.id, trainees.name, subscriptions.start_date,
                   subscriptions.end_date, subscriptions.price, subscriptions.paid
            FROM subscriptions
            JOIN trainees ON trainees.id = subscriptions.trainee_id
        """)
        for row in c.fetchall():
            end = date.fromisoformat(row[3])
            days_left = (end - date.today()).days

            tag = ""
            if days_left < 0:
                tag = "expired"
            elif days_left <= 5:
                tag = "warning"
            else:
                tag = "ok"

            subs_table.insert("", "end", values=row, tags=(tag,))
        conn.close()

        # إعداد الألوان
        subs_table.tag_configure("expired", background="#ff9999")  # أحمر فاتح
        subs_table.tag_configure("warning", background="#fff799")  # أصفر فاتح
        subs_table.tag_configure("ok", background="#b3ffb3")       # أخضر فاتح

    load_subs()

    # حذف اشتراك
    def delete_subscription():
        selected = subs_table.selection()
        if not selected:
            messagebox.showerror("خطأ", "اختر اشتراك للحذف")
            return
        sub_id = subs_table.item(selected[0])["values"][0]

        conn = connect_db()
        c = conn.cursor()
        c.execute("DELETE FROM subscriptions WHERE id=?", (sub_id,))
        conn.commit()
        conn.close()
        load_subs()

    tk.Button(tab_subs, text="حذف الاشتراك المحدد", command=delete_subscription).pack(pady=5)

    # -------- تنبيه الاشتراكات --------
    def check_expiring_subs():
        today = date.today()
        conn = connect_db()
        c = conn.cursor()
        c.execute("""
            SELECT trainees.name, subscriptions.end_date
            FROM subscriptions
            JOIN trainees ON trainees.id = subscriptions.trainee_id
        """)

        expired = []
        warning = []

        for name, end_date in c.fetchall():
            end = date.fromisoformat(end_date)
            days_left = (end - today).days

            if days_left < 0:
                expired.append(f"{name} (منتهي)")
            elif days_left <= 5:
                warning.append(f"{name} (باقي {days_left} أيام)")

        conn.close()

        if expired or warning:
            msg = ""
            if expired:
                msg += "🟥 اشتراكات منتهية:\n" + "\n".join(expired) + "\n\n"
            if warning:
                msg += "🟨 اشتراكات قربت تنتهي:\n" + "\n".join(warning)

            messagebox.showwarning("تنبيه الاشتراكات", msg)

    check_expiring_subs()

    tabs.pack(expand=True, fill="both")
    root.mainloop()

# ================= LOGIN =================
def login():
    conn = connect_db()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (user_entry.get(), pass_entry.get())
    )
    if c.fetchone():
        login_win.destroy()
        main_app()
    else:
        messagebox.showerror("خطأ", "اسم المستخدم أو كلمة المرور غلط")
    conn.close()

# ================= LOGIN WINDOW =================
setup_db()

login_win = tk.Tk()
login_win.title("تسجيل الدخول")
login_win.geometry("300x200")

tk.Label(login_win, text="اسم المستخدم").pack(pady=5)
user_entry = tk.Entry(login_win)
user_entry.pack()

tk.Label(login_win, text="كلمة المرور").pack(pady=5)
pass_entry = tk.Entry(login_win, show="*")
pass_entry.pack()

tk.Button(login_win, text="دخول", command=login).pack(pady=10)

login_win.mainloop()
