import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import requests
import re
import webbrowser
import os
import csv
import shutil
from datetime import datetime
from bs4 import BeautifulSoup

APP_NAME = "AutoCore v2.2.4"
DB_NAME = "autocore.db"

# ---------- POMOCNICZA FUNKCJA DO CZYSZCZENIA CENY ----------
def clean_price(p):
    if p is None:
        return 0.0
    s = str(p).replace(',', '.')
    s = re.sub(r'[^0-9.-]', '', s)
    try:
        return float(s)
    except:
        return 0.0

# ---------- KONFIGURACJA SKRAPERA ----------
SEARCH_URL = "https://www.signeda.pl/index.php?route=product/search&search={}&nlog=true"
PRICE_URL = "https://www.signeda.pl/index.php?route=product/category/prices_redesign"
CARS_URL = "https://www.signeda.pl/index.php?route=product/product/getCars"
HEADERS = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}

# ---------- BAZA DANYCH Z MIGRACJAMI ----------
class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.create_tables()
        self.migrate_tables()

    def create_tables(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE,
            product_code TEXT,
            oe_code TEXT,
            name TEXT,
            models TEXT,
            category TEXT,
            product_type TEXT,
            side TEXT,
            position TEXT,
            description TEXT,
            price REAL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            signeda_stock INTEGER DEFAULT 0,
            condition_rating INTEGER DEFAULT 0,
            damage_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            phone TEXT,
            address TEXT,
            nip TEXT,
            document_type TEXT,
            delivery_type TEXT,
            status TEXT,
            package_weight REAL,
            package_length REAL,
            package_width REAL,
            package_height REAL,
            shipping_free INTEGER DEFAULT 0,
            discount REAL DEFAULT 0,
            total_price REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            barcode TEXT,
            product_name TEXT,
            picked INTEGER DEFAULT 0,
            to_order INTEGER DEFAULT 0,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
        """)
        self.conn.commit()

    def migrate_tables(self):
        cur = self.conn.cursor()
        for col, col_type in [('force_price', 'INTEGER DEFAULT 0'),
                              ('custom_price', 'REAL DEFAULT 0'),
                              ('olx_offer_id', 'TEXT')]:
            try:
                cur.execute(f"ALTER TABLE products ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass
        for col, col_type in [('shipping_free', 'INTEGER DEFAULT 0'),
                              ('discount', 'REAL DEFAULT 0'),
                              ('total_price', 'REAL DEFAULT 0')]:
            try:
                cur.execute(f"ALTER TABLE orders ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass
        self.conn.commit()

    def get_categories(self):
        cur = self.conn.cursor()
        rows = cur.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category!=''").fetchall()
        return [r[0] for r in rows]

    def get_all_models(self):
        cur = self.conn.cursor()
        rows = cur.execute("SELECT models FROM products").fetchall()
        models = set()
        for row in rows:
            if row[0]:
                for line in row[0].split("\n"):
                    line = line.strip()
                    if line:
                        models.add(line)
        return sorted(models)

    def get_stats(self):
        cur = self.conn.cursor()
        product_count = cur.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        active_orders = cur.execute("SELECT COUNT(*) FROM orders WHERE status='NEW'").fetchone()[0]
        low_stock = cur.execute("SELECT COUNT(*) FROM products WHERE product_type='używane wielokrotne' AND stock<=2 AND stock>0").fetchone()[0]
        return product_count, active_orders, low_stock

db = Database()

# ---------- FUNKCJE SKRAPERA ----------
def get_product_data(code):
    r = requests.get(SEARCH_URL.format(code), headers=HEADERS, timeout=20)
    r.raise_for_status()
    match = re.search(r"product-card-(\d+)", r.text)
    if not match:
        return None
    product_id = match.group(1)
    soup = BeautifulSoup(r.text, "html.parser")
    name = description = link = oe = side = position = product_type = ""
    name_el = soup.select_one("a.product-cards-holder__product-card__product-details__product-name")
    if name_el:
        name = name_el.get_text(" ", strip=True)
        link = name_el.get("href", "")
    desc_el = soup.select_one(".product-cards-holder__product-card__product-details__product-description")
    if desc_el:
        description = desc_el.get_text(" ", strip=True)
    for row in soup.select("tr"):
        th = row.find("th")
        td = row.find("td")
        if not th or not td:
            continue
        key = th.get_text(" ", strip=True)
        value = td.get_text(" ", strip=True)
        if "Kod Oryginalu" in key:
            oe = value
        elif "Miejsce w Pojeździe" in key:
            if value.lower() in ["lewa", "prawa"]:
                side = value
            if value.lower() in ["przod", "tyl"]:
                position = value
        elif "Typ produktu" in key:
            product_type = value
    return {
        "product_id": product_id,
        "name": name,
        "description": description,
        "link": link,
        "oe": oe,
        "side": side,
        "position": position,
        "signeda_type": product_type
    }

def get_price_stock(product_id, code):
    data = {"route": "product/category/prices_redesign", "products": product_id, "search": code}
    r = requests.post(PRICE_URL, headers=HEADERS, data=data, timeout=20)
    js = r.json()
    html = js["prices_html"][product_id]
    soup = BeautifulSoup(html, "html.parser")
    price = ""
    stock = "0"
    regular = soup.select_one(".price-other span")
    if regular:
        price = regular.get_text(strip=True)
    else:
        promo = soup.select_one(".price")
        if promo:
            price = promo.get_text(strip=True)
    qty = soup.select_one(".quantity span")
    if qty:
        stock = qty.get_text(strip=True)
    return price, stock

def get_models(product_id):
    data = {"route": "product/product/getCars", "product_id": product_id}
    r = requests.post(CARS_URL, headers=HEADERS, data=data, timeout=20)
    html = r.json().get("html", "")
    soup = BeautifulSoup(html, "html.parser")
    models = [li.get_text(" ", strip=True) for li in soup.select("li") if li.get_text(" ", strip=True)]
    return "\n".join(models)

def fetch_part(code):
    product = get_product_data(code)
    if not product:
        return None
    price, stock = get_price_stock(product["product_id"], code)
    models = get_models(product["product_id"])
    return {
        "product_code": code,
        "oe_code": product["oe"],
        "name": product["name"],
        "description": product["description"],
        "models": models,
        "price": price,
        "signeda_stock": stock,
        "side": product["side"],
        "position": product["position"],
        "signeda_type": product["signeda_type"],
        "link": product["link"]
    }

# ---------- FUNKCJE POMOCNICZE GUI ----------
def refresh_stats(stats_label):
    prod, active, low = db.get_stats()
    stats_label.config(text=f"Produkty: {prod}  |  Aktywne zlecenia: {active}  |  Niskie stany: {low}")

def load_products_into_tree(tree, search_text="", filter_category="", filter_model=""):
    for row in tree.get_children():
        tree.delete(row)
    cur = db.conn.cursor()
    rows = cur.execute("""
        SELECT barcode, oe_code, name, product_type, category, side, position,
               stock, price, signeda_stock, models
        FROM products
    """).fetchall()
    for row in rows:
        if search_text:
            joined = " ".join(str(x).lower() for x in row)
            if search_text.lower() not in joined:
                continue
        if filter_category and filter_category != "Wszystkie":
            if row[4] != filter_category:
                continue
        if filter_model and filter_model != "Wszystkie":
            if filter_model not in str(row[10]):
                continue
        tags = ()
        if row[3] == "używane wielokrotne":
            if row[7] == 0:
                tags = ('red',)
            elif row[7] <= 2:
                tags = ('yellow',)
        tree.insert("", "end", values=row, tags=tags)
    tree.tag_configure('yellow', background='#fff7c7')
    tree.tag_configure('red', background='#ffd8d8')

def refresh_filters(category_cb, model_cb):
    categories = ["Wszystkie"] + db.get_categories()
    category_cb['values'] = categories
    models = ["Wszystkie"] + db.get_all_models()
    model_cb['values'] = models

def export_to_csv(tree, filename="raport.csv"):
    rows = []
    cols = [tree.heading(c)['text'] for c in tree['columns']]
    rows.append(cols)
    for child in tree.get_children():
        values = tree.item(child)['values']
        rows.append(values)
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    messagebox.showinfo("Eksport", f"Dane wyeksportowane do {filename}")

# ---------- OKNO PRZYJMIJ DOSTAWĘ ----------
def receive_delivery_window(root, tree, stats_label, category_cb, model_cb):
    win = tk.Toplevel(root)
    win.title("Przyjmij dostawę")
    win.geometry("500x400")
    ttk.Label(win, text="Zeskanuj kod produktu").pack(pady=10)
    entry = ttk.Entry(win, width=50)
    entry.pack(pady=5)
    entry.focus()
    info_label = ttk.Label(win, text="", wraplength=450)
    info_label.pack(pady=10)
    qty_frame = ttk.Frame(win)
    qty_frame.pack(pady=5)
    ttk.Label(qty_frame, text="Ilość:").pack(side="left")
    qty_var = tk.IntVar(value=1)
    qty_spin = ttk.Spinbox(qty_frame, from_=1, to=99, textvariable=qty_var, width=5)
    qty_spin.pack(side="left", padx=5)
    def add_or_update():
        barcode = entry.get().strip()
        if not barcode:
            return
        qty = qty_var.get()
        cur = db.conn.cursor()
        row = cur.execute("SELECT id, name, stock, product_type FROM products WHERE barcode=?", (barcode,)).fetchone()
        if row:
            prod_id, name, current_stock, ptype = row
            if ptype == "używane unikat" and current_stock > 0:
                messagebox.showerror("Błąd", "Produkt unikat już na stanie")
                return
            new_stock = current_stock + qty
            cur.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, prod_id))
            db.conn.commit()
            info_label.config(text=f"Dodano {qty} szt. {name}\nNowy stan: {new_stock}")
            pending = cur.execute("""
                SELECT oi.order_id, o.customer_name 
                FROM order_items oi JOIN orders o ON oi.order_id=o.id
                WHERE oi.barcode=? AND oi.picked=0 AND o.status IN ('NEW','READY')
            """, (barcode,)).fetchall()
            if pending:
                order_list = "\n".join([f"ID: {p[0]} - {p[1]}" for p in pending])
                if messagebox.askyesno("Oczekujące zlecenia", f"Produkt potrzebny w:\n{order_list}\nCzy odkliknąć w tych zleceniach?"):
                    for order_id, _ in pending:
                        cur.execute("UPDATE order_items SET picked=1 WHERE order_id=? AND barcode=?", (order_id, barcode))
                        cur.execute("UPDATE products SET stock=stock-1 WHERE barcode=?", (barcode,))
                    db.conn.commit()
                    messagebox.showinfo("OK", "Zaktualizowano zlecenia")
        else:
            ans = messagebox.askyesno("Nowy produkt", "Nie ma go w bazie. Czy wyszukać w Signeda? (Nie = dodaj ręcznie)")
            if ans:
                try:
                    data = fetch_part(barcode)
                    if data:
                        cur.execute("""
                            INSERT INTO products(barcode, product_code, oe_code, name, models, category,
                                                 product_type, side, position, description, price, stock, signeda_stock)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """, (barcode, data["product_code"], data["oe_code"], data["name"], data["models"],
                              "", "nowe", data["side"], data["position"], data["description"],
                              data["price"], qty, data["signeda_stock"]))
                        db.conn.commit()
                        info_label.config(text=f"Dodano z Signeda: {data['name']}\nStan: {qty}")
                    else:
                        messagebox.showerror("Błąd", "Nie znaleziono")
                        return
                except Exception as e:
                    messagebox.showerror("Błąd", str(e))
                    return
            else:
                sub = tk.Toplevel(win)
                sub.title("Dodaj ręcznie")
                sub.geometry("500x600")
                ttk.Label(sub, text=f"Dodawanie: {barcode}").pack(pady=5)
                name_e = ttk.Entry(sub, width=50)
                name_e.pack()
                oe_e = ttk.Entry(sub, width=50)
                oe_e.pack()
                price_e = ttk.Entry(sub, width=20)
                price_e.pack()
                type_var = tk.StringVar()
                type_combo = ttk.Combobox(sub, textvariable=type_var, values=["nowe", "używane unikat", "używane wielokrotne", "inne"])
                type_combo.pack()
                cat_e = ttk.Entry(sub, width=50)
                cat_e.pack()
                def save_manual():
                    cur.execute("""
                        INSERT INTO products(barcode, name, oe_code, price, product_type, category, stock)
                        VALUES (?,?,?,?,?,?,?)
                    """, (barcode, name_e.get(), oe_e.get(), price_e.get(), type_var.get(), cat_e.get(), qty))
                    db.conn.commit()
                    load_products_into_tree(tree, "", "", "")
                    refresh_filters(category_cb, model_cb)
                    refresh_stats(stats_label)
                    messagebox.showinfo("OK", "Dodano ręcznie")
                    sub.destroy()
                    win.destroy()
                ttk.Button(sub, text="Zapisz", command=save_manual).pack(pady=10)
                return
        load_products_into_tree(tree, "", "", "")
        refresh_filters(category_cb, model_cb)
        refresh_stats(stats_label)
        entry.delete(0, tk.END)
        entry.focus()
    ttk.Button(win, text="Przyjmij", command=add_or_update).pack(pady=10)
    entry.bind("<Return>", lambda e: add_or_update())

# ---------- OKNA DODAWANIA (Signeda i ręczne) ----------
def add_signeda_window(root, tree, category_cb, model_cb, stats_label):
    win = tk.Toplevel(root)
    win.title("Dodaj część Signeda")
    win.geometry("400x200")
    ttk.Label(win, text="Kod produktu").pack(pady=10)
    entry = ttk.Entry(win, width=40)
    entry.pack()
    def download():
        code = entry.get().strip()
        if not code:
            return
        try:
            data = fetch_part(code)
            if not data:
                messagebox.showerror("Błąd", "Nie znaleziono")
                return
            cur = db.conn.cursor()
            if cur.execute("SELECT id FROM products WHERE barcode=?", (code,)).fetchone():
                messagebox.showerror("Błąd", "Już istnieje")
                return
            cur.execute("""
                INSERT INTO products(barcode, product_code, oe_code, name, models, product_type,
                                     side, position, description, price, stock, signeda_stock)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (code, data["product_code"], data["oe_code"], data["name"], data["models"],
                  "nowe", data["side"], data["position"], data["description"],
                  data["price"], 0, data["signeda_stock"]))
            db.conn.commit()
            load_products_into_tree(tree, "", "", "")
            refresh_filters(category_cb, model_cb)
            refresh_stats(stats_label)
            messagebox.showinfo("OK", "Dodano (stan 0)")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Błąd", str(e))
    ttk.Button(win, text="Pobierz i zapisz", command=download).pack(pady=20)

def add_manual_window(root, tree, category_cb, model_cb, stats_label):
    win = tk.Toplevel(root)
    win.title("Dodaj część ręcznie")
    win.geometry("700x850")
    fields = {}
    ttk.Label(win, text="Kod kreskowy").pack()
    barcode_e = ttk.Entry(win, width=70)
    barcode_e.pack(pady=2)
    fields["barcode"] = barcode_e
    frame_oem = ttk.Frame(win)
    frame_oem.pack(fill="x", pady=5)
    ttk.Label(frame_oem, text="Kod OEM").pack(side="left")
    oem_e = ttk.Entry(frame_oem, width=50)
    oem_e.pack(side="left", padx=5)
    fields["oem"] = oem_e
    def fetch_by_oem():
        code = oem_e.get().strip()
        if not code:
            return
        try:
            data = fetch_part(code)
            if data:
                fields["name"].delete(0, tk.END)
                fields["name"].insert(0, data["name"])
                fields["models"].delete("1.0", tk.END)
                fields["models"].insert("1.0", data["models"])
                side_var.set(data["side"])
                position_var.set(data["position"])
                if data["signeda_type"]:
                    type_combo.set(data["signeda_type"])
            else:
                messagebox.showwarning("Uwaga", "Nie znaleziono")
        except Exception as e:
            messagebox.showerror("Błąd", str(e))
    ttk.Button(frame_oem, text="Pobierz dane", command=fetch_by_oem).pack(side="left")
    ttk.Label(win, text="Nazwa").pack()
    name_e = ttk.Entry(win, width=70)
    name_e.pack(pady=2)
    fields["name"] = name_e
    ttk.Label(win, text="Modele (linie)").pack()
    models_t = tk.Text(win, height=5, width=70)
    models_t.pack(pady=2)
    fields["models"] = models_t
    ttk.Label(win, text="Cena").pack()
    price_e = ttk.Entry(win, width=20)
    price_e.pack(pady=2)
    fields["price"] = price_e
    ttk.Label(win, text="Ilość początkowa").pack()
    stock_e = ttk.Entry(win, width=10)
    stock_e.insert(0, "1")
    stock_e.pack(pady=2)
    ttk.Label(win, text="Typ").pack()
    type_var = tk.StringVar()
    type_combo = ttk.Combobox(win, textvariable=type_var, values=["nowe", "używane unikat", "używane wielokrotne", "inne"])
    type_combo.pack(pady=2)
    ttk.Label(win, text="Kategoria").pack()
    cat_e = ttk.Entry(win, width=50)
    cat_e.pack(pady=2)
    fields["category"] = cat_e
    ttk.Label(win, text="Strona").pack()
    side_var = tk.StringVar()
    side_combo = ttk.Combobox(win, textvariable=side_var, values=["", "lewa", "prawa"])
    side_combo.pack(pady=2)
    ttk.Label(win, text="Pozycja").pack()
    position_var = tk.StringVar()
    pos_combo = ttk.Combobox(win, textvariable=position_var, values=["", "przod", "tyl"])
    pos_combo.pack(pady=2)
    ttk.Label(win, text="Opis").pack()
    desc_t = tk.Text(win, height=5, width=70)
    desc_t.pack(pady=2)
    ttk.Label(win, text="Ocena (1-5)").pack()
    rating_e = ttk.Entry(win, width=5)
    rating_e.pack()
    ttk.Label(win, text="Opis uszkodzeń").pack()
    damage_t = tk.Text(win, height=3, width=70)
    damage_t.pack(pady=2)
    def save():
        barcode = fields["barcode"].get().strip()
        if not barcode:
            messagebox.showerror("Błąd", "Kod wymagany")
            return
        cur = db.conn.cursor()
        if cur.execute("SELECT id FROM products WHERE barcode=?", (barcode,)).fetchone():
            messagebox.showerror("Błąd", "Istnieje")
            return
        try:
            stock = int(stock_e.get())
        except:
            stock = 1
        cur.execute("""
            INSERT INTO products(barcode, oe_code, name, models, category, product_type,
                                 side, position, description, price, stock, condition_rating, damage_description)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (barcode, fields["oem"].get(), fields["name"].get(), fields["models"].get("1.0", tk.END).strip(),
              fields["category"].get(), type_var.get(), side_var.get(), position_var.get(),
              desc_t.get("1.0", tk.END).strip(), fields["price"].get(), stock,
              rating_e.get() or 0, damage_t.get("1.0", tk.END).strip()))
        db.conn.commit()
        load_products_into_tree(tree, "", "", "")
        refresh_filters(category_cb, model_cb)
        refresh_stats(stats_label)
        messagebox.showinfo("OK", "Dodano")
        win.destroy()
    ttk.Button(win, text="Zapisz", command=save).pack(pady=20)

# ---------- OKNO SZCZEGÓŁÓW PRODUKTU ----------
def show_product_details_window(barcode, master_tree, category_cb, model_cb, stats_label):
    cur = db.conn.cursor()
    row = cur.execute("SELECT * FROM products WHERE barcode=?", (barcode,)).fetchone()
    if not row:
        messagebox.showerror("Błąd", "Produkt nie istnieje")
        return
    win = tk.Toplevel()
    win.title(f"Szczegóły - {barcode}")
    win.geometry("800x700")
    txt = tk.Text(win, wrap="word")
    txt.pack(fill="both", expand=True)
    cols = [desc[0] for desc in cur.description]
    for i, col in enumerate(cols):
        txt.insert(tk.END, f"{col}: {row[i]}\n")
    btn_frame = ttk.Frame(win)
    btn_frame.pack(fill="x", pady=10)
    def delete_product():
        if messagebox.askyesno("Usuń", f"Czy na pewno usunąć produkt {barcode}?"):
            cur.execute("DELETE FROM products WHERE barcode=?", (barcode,))
            db.conn.commit()
            load_products_into_tree(master_tree, "", "", "")
            refresh_filters(category_cb, model_cb)
            refresh_stats(stats_label)
            win.destroy()
            messagebox.showinfo("OK", "Usunięto")
    ttk.Button(btn_frame, text="Usuń z bazy", command=delete_product).pack(side="left", padx=5)
    def edit_product():
        edit_win = tk.Toplevel(win)
        edit_win.title("Edytuj produkt")
        edit_win.geometry("400x300")
        ttk.Label(edit_win, text="Nazwa").pack()
        name_e = ttk.Entry(edit_win, width=50)
        name_e.insert(0, row[4])
        name_e.pack()
        ttk.Label(edit_win, text="Cena").pack()
        price_e = ttk.Entry(edit_win, width=20)
        price_e.insert(0, row[12])
        price_e.pack()
        ttk.Label(edit_win, text="Stan magazynowy").pack()
        stock_e = ttk.Entry(edit_win, width=10)
        stock_e.insert(0, row[13])
        stock_e.pack()
        def save_edit():
            cur.execute("UPDATE products SET name=?, price=?, stock=? WHERE barcode=?", (name_e.get(), price_e.get(), stock_e.get(), barcode))
            db.conn.commit()
            load_products_into_tree(master_tree, "", "", "")
            refresh_stats(stats_label)
            edit_win.destroy()
            win.destroy()
            show_product_details_window(barcode, master_tree, category_cb, model_cb, stats_label)
        ttk.Button(edit_win, text="Zapisz", command=save_edit).pack(pady=10)
    ttk.Button(btn_frame, text="Edytuj", command=edit_product).pack(side="left", padx=5)
    def open_link():
        url = f"https://www.signeda.pl/index.php?route=product/search&search={barcode}"
        webbrowser.open(url)
    ttk.Button(btn_frame, text="Link do Signeda", command=open_link).pack(side="left", padx=5)
    force_var = tk.BooleanVar(value=row[17] if len(row)>17 else False)
    custom_price_var = tk.StringVar(value=row[18] if len(row)>18 else "")
    def toggle_force():
        if force_var.get():
            price_frame.pack(fill="x", pady=5)
        else:
            price_frame.pack_forget()
    force_cb = ttk.Checkbutton(btn_frame, text="Wymuś cenę", variable=force_var, command=toggle_force)
    force_cb.pack(side="left", padx=5)
    price_frame = ttk.Frame(win)
    ttk.Label(price_frame, text="Cena wymuszona:").pack(side="left")
    custom_price_e = ttk.Entry(price_frame, textvariable=custom_price_var, width=10)
    custom_price_e.pack(side="left", padx=5)
    def save_force():
        cur.execute("UPDATE products SET force_price=?, custom_price=? WHERE barcode=?", (1 if force_var.get() else 0, custom_price_var.get() or 0, barcode))
        db.conn.commit()
        messagebox.showinfo("OK", "Zapisano wymuszenie ceny")
        win.destroy()
    ttk.Button(btn_frame, text="Zapisz wymuszenie", command=save_force).pack(side="left", padx=5)
    def preview_olx():
        name = row[4]
        oe = row[3]
        price = row[12]
        product_type = row[5]
        models = row[6]
        title = f"{name} - {models.split(chr(10))[0] if models else ''}".strip()
        description = f"Kod OEM: {oe}\n"
        if product_type == "nowe":
            description += "Produkt nowy, zamiennik OEM.\n"
        else:
            description += f"Produkt używany. Stan: {row[15]}/5. Uszkodzenia: {row[16]}\n"
        description += f"Cena: {price} zł\nKontakt przez OLX."
        preview = tk.Toplevel(win)
        preview.title("Podgląd ogłoszenia OLX")
        preview.geometry("600x500")
        ttk.Label(preview, text="Tytuł:").pack(anchor="w")
        ttk.Label(preview, text=title, wraplength=550).pack(anchor="w", pady=5)
        ttk.Label(preview, text="Opis:").pack(anchor="w")
        txt_desc = tk.Text(preview, height=15, wrap="word")
        txt_desc.insert("1.0", description)
        txt_desc.pack(fill="both", expand=True)
        ttk.Label(preview, text="Cena:").pack(anchor="w")
        ttk.Label(preview, text=f"{price} zł").pack(anchor="w")
        ttk.Button(preview, text="Zamknij", command=preview.destroy).pack(pady=10)
    ttk.Button(btn_frame, text="Dodaj ogłoszenie OLX", command=preview_olx).pack(side="left", padx=5)

# ---------- ZLECENIA ----------
active_order_window = None

def add_product_to_active_order(barcode, name, oe, price):
    global active_order_window
    if active_order_window and active_order_window.winfo_exists():
        active_order_window.add_product_line(barcode, name, oe, price)
        return True
    return False

def create_order_window(root, stats_label, master_tree, category_cb, model_cb):
    global active_order_window
    if active_order_window and active_order_window.winfo_exists():
        active_order_window.lift()
        return
    win = tk.Toplevel(root)
    active_order_window = win
    win.title("Nowe zlecenie")
    win.geometry("1000x850")
    entries = {}
    labels = ["Imię i nazwisko", "Telefon", "Adres", "NIP"]
    for label in labels:
        ttk.Label(win, text=label).pack()
        e = ttk.Entry(win, width=70)
        e.pack(pady=2)
        entries[label] = e
    ttk.Label(win, text="Typ dokumentu").pack()
    doc_var = tk.StringVar()
    doc_combo = ttk.Combobox(win, textvariable=doc_var, values=["FAKTURA", "SPRZEDAŻ INNA"])
    doc_combo.pack(pady=2)
    ttk.Label(win, text="Typ dostawy").pack()
    delivery_var = tk.StringVar()
    delivery_combo = ttk.Combobox(win, textvariable=delivery_var, values=["PACZKA", "PALETA", "ODBIÓR OSOBISTY", "INNE"])
    delivery_combo.pack(pady=2)
    shipping_free_var = tk.BooleanVar()
    shipping_free_cb = ttk.Checkbutton(win, text="Wysyłka gratis", variable=shipping_free_var)
    shipping_free_cb.pack(pady=2)
    ttk.Label(win, text="Produkty (każdy w nowej linii, format: kod | nazwa | OEM | cena)").pack()
    items_text = tk.Text(win, height=12)
    items_text.pack(fill="both", expand=True, padx=10, pady=5)
    temp_frame = ttk.Frame(win)
    temp_frame.pack(fill="x", padx=10, pady=5)
    ttk.Label(temp_frame, text="Skanuj kod i naciśnij Enter lub przycisk:").pack(side="left")
    temp_entry = ttk.Entry(temp_frame, width=50)
    temp_entry.pack(side="left", padx=5)
    def add_product_line(barcode, name, oe, price):
        line = f"{barcode} | {name} | {oe} | {price}\n"
        items_text.insert(tk.END, line)
    win.add_product_line = add_product_line
    def process_barcode():
        barcode = temp_entry.get().strip()
        if not barcode:
            return
        cur = db.conn.cursor()
        row = cur.execute("SELECT name, oe_code, price, stock FROM products WHERE barcode=?", (barcode,)).fetchone()
        if row:
            name, oe, price, stock = row
            add_product_line(barcode, name, oe, price)
            temp_entry.delete(0, tk.END)
        else:
            ans = messagebox.askyesno("Nowy produkt", "Nie ma go w bazie. Czy dodać teraz?")
            if not ans:
                return
            sub = tk.Toplevel(win)
            sub.title("Dodaj brakujący produkt")
            sub.geometry("400x300")
            ttk.Label(sub, text=f"Kod: {barcode}").pack(pady=10)
            def add_from_signeda():
                try:
                    data = fetch_part(barcode)
                    if data:
                        has_stock = messagebox.askyesno("Stan magazynowy", "Czy mamy ten produkt na stanie? (Tak = stan 1, Nie = stan 0)")
                        stock = 1 if has_stock else 0
                        cur.execute("""
                            INSERT INTO products(barcode, product_code, oe_code, name, models, product_type,
                                                 side, position, description, price, stock, signeda_stock)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                        """, (barcode, data["product_code"], data["oe_code"], data["name"], data["models"],
                              "nowe", data["side"], data["position"], data["description"],
                              data["price"], stock, data["signeda_stock"]))
                        db.conn.commit()
                        add_product_line(barcode, data["name"], data["oe_code"], data["price"])
                        sub.destroy()
                        load_products_into_tree(master_tree, "", "", "")
                        refresh_filters(category_cb, model_cb)
                        refresh_stats(stats_label)
                        temp_entry.delete(0, tk.END)
                    else:
                        messagebox.showerror("Błąd", "Nie znaleziono w Signeda")
                except Exception as e:
                    messagebox.showerror("Błąd", str(e))
            def add_manual():
                man = tk.Toplevel(sub)
                man.title("Dodaj ręcznie")
                ttk.Label(man, text="Nazwa").pack()
                name_e = ttk.Entry(man, width=50)
                name_e.pack()
                ttk.Label(man, text="Kod OEM").pack()
                oe_e = ttk.Entry(man, width=50)
                oe_e.pack()
                ttk.Label(man, text="Cena").pack()
                price_e = ttk.Entry(man, width=20)
                price_e.pack()
                ttk.Label(man, text="Czy na stanie?").pack()
                stock_var = tk.BooleanVar(value=False)
                stock_cb = ttk.Checkbutton(man, text="Tak, jest na stanie", variable=stock_var)
                stock_cb.pack()
                def save_manual():
                    stock = 1 if stock_var.get() else 0
                    cur.execute("""
                        INSERT INTO products(barcode, name, oe_code, price, stock)
                        VALUES (?,?,?,?,?)
                    """, (barcode, name_e.get(), oe_e.get(), price_e.get(), stock))
                    db.conn.commit()
                    add_product_line(barcode, name_e.get(), oe_e.get(), price_e.get())
                    man.destroy()
                    sub.destroy()
                    load_products_into_tree(master_tree, "", "", "")
                    refresh_filters(category_cb, model_cb)
                    refresh_stats(stats_label)
                    temp_entry.delete(0, tk.END)
                ttk.Button(man, text="Zapisz", command=save_manual).pack(pady=10)
            ttk.Button(sub, text="Dodaj z Signeda", command=add_from_signeda).pack(pady=5)
            ttk.Button(sub, text="Dodaj ręcznie", command=add_manual).pack(pady=5)
    temp_entry.bind("<Return>", lambda e: process_barcode())
    ttk.Button(temp_frame, text="Dodaj", command=process_barcode).pack(side="left", padx=5)
    def save_order():
        if not entries["Imię i nazwisko"].get().strip():
            messagebox.showerror("Błąd", "Imię i nazwisko wymagane")
            return
        lines = items_text.get("1.0", tk.END).splitlines()
        products = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            if len(parts) < 1:
                continue
            barcode = parts[0].strip()
            cur = db.conn.cursor()
            row = cur.execute("SELECT name, price, stock FROM products WHERE barcode=?", (barcode,)).fetchone()
            if not row:
                messagebox.showerror("Błąd", f"Produkt {barcode} nie istnieje w bazie")
                return
            name, price, stock = row
            to_order = 1 if stock == 0 else 0
            products.append((barcode, name, price, to_order))
        if not products:
            messagebox.showerror("Błąd", "Brak produktów")
            return
        cur = db.conn.cursor()
        cur.execute("""
            INSERT INTO orders(customer_name, phone, address, nip, document_type, delivery_type, status, shipping_free)
            VALUES (?,?,?,?,?,?,?,?)
        """, (entries["Imię i nazwisko"].get(), entries["Telefon"].get(), entries["Adres"].get(),
              entries["NIP"].get(), doc_var.get(), delivery_var.get(), "NEW", 1 if shipping_free_var.get() else 0))
        order_id = cur.lastrowid
        total = 0
        for barcode, name, price, to_order in products:
            cur.execute("INSERT INTO order_items(order_id, barcode, product_name, to_order) VALUES (?,?,?,?)",
                        (order_id, barcode, name, to_order))
            total += clean_price(price)
        cur.execute("UPDATE orders SET total_price=? WHERE id=?", (total, order_id))
        db.conn.commit()
        refresh_stats(stats_label)
        messagebox.showinfo("AutoCore", f"Zlecenie #{order_id} zapisane\nWartość: {total:.2f} zł")
        win.destroy()
        global active_order_window
        active_order_window = None
    ttk.Button(win, text="Zatwierdź zlecenie", command=save_order).pack(pady=10)
    def on_close():
        global active_order_window
        active_order_window = None
        win.destroy()
    win.protocol("WM_DELETE_WINDOW", on_close)

def edit_order_window(order_id, parent_win, stats_label, master_tree, category_cb, model_cb):
    win = tk.Toplevel(parent_win)
    win.title(f"Edycja zlecenia #{order_id}")
    win.geometry("1000x800")
    cur = db.conn.cursor()
    order = cur.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        win.destroy()
        return
    entries = {}
    labels = ["Imię i nazwisko", "Telefon", "Adres", "NIP"]
    for i, label in enumerate(labels):
        ttk.Label(win, text=label).pack()
        e = ttk.Entry(win, width=70)
        e.insert(0, order[i+1])
        e.pack(pady=2)
        entries[label] = e
    ttk.Label(win, text="Typ dokumentu").pack()
    doc_var = tk.StringVar(value=order[5])
    doc_combo = ttk.Combobox(win, textvariable=doc_var, values=["FAKTURA", "SPRZEDAŻ INNA"])
    doc_combo.pack(pady=2)
    ttk.Label(win, text="Typ dostawy").pack()
    delivery_var = tk.StringVar(value=order[6])
    delivery_combo = ttk.Combobox(win, textvariable=delivery_var, values=["PACZKA", "PALETA", "ODBIÓR OSOBISTY", "INNE"])
    delivery_combo.pack(pady=2)
    shipping_free_var = tk.BooleanVar(value=order[11]==1)
    ttk.Checkbutton(win, text="Wysyłka gratis", variable=shipping_free_var).pack(pady=2)
    ttk.Label(win, text="Produkty (edytuj linie)").pack()
    items_text = tk.Text(win, height=12)
    items_text.pack(fill="both", expand=True, padx=10, pady=5)
    items = cur.execute("SELECT barcode, product_name, oe_code, price FROM order_items oi JOIN products p ON oi.barcode=p.barcode WHERE oi.order_id=?", (order_id,)).fetchall()
    for item in items:
        barcode, name, oe, price = item
        items_text.insert(tk.END, f"{barcode} | {name} | {oe} | {price}\n")
    add_frame = ttk.Frame(win)
    add_frame.pack(fill="x", padx=10, pady=5)
    ttk.Label(add_frame, text="Dodaj kod:").pack(side="left")
    add_entry = ttk.Entry(add_frame, width=50)
    add_entry.pack(side="left", padx=5)
    def add_new_product():
        barcode = add_entry.get().strip()
        if not barcode:
            return
        cur2 = db.conn.cursor()
        row = cur2.execute("SELECT name, oe_code, price FROM products WHERE barcode=?", (barcode,)).fetchone()
        if row:
            name, oe, price = row
            items_text.insert(tk.END, f"{barcode} | {name} | {oe} | {price}\n")
            add_entry.delete(0, tk.END)
        else:
            ans = messagebox.askyesno("Nowy produkt", "Nie istnieje w bazie. Czy dodać teraz?")
            if ans:
                messagebox.showinfo("Info", "Użyj osobnego okna 'Dodaj część' i wróć do edycji")
    ttk.Button(add_frame, text="Dodaj produkt", command=add_new_product).pack(side="left", padx=5)
    def delete_selected_lines():
        try:
            sel_start = items_text.index(tk.SEL_FIRST)
            sel_end = items_text.index(tk.SEL_LAST)
            items_text.delete(sel_start, sel_end)
        except tk.TclError:
            messagebox.showwarning("Uwaga", "Zaznacz fragment tekstu do usunięcia")
    ttk.Button(win, text="Usuń zaznaczone produkty", command=delete_selected_lines).pack(pady=5)
    def save_changes():
        cur.execute("""
            UPDATE orders SET customer_name=?, phone=?, address=?, nip=?, document_type=?, delivery_type=?, shipping_free=?
            WHERE id=?
        """, (entries["Imię i nazwisko"].get(), entries["Telefon"].get(), entries["Adres"].get(),
              entries["NIP"].get(), doc_var.get(), delivery_var.get(), 1 if shipping_free_var.get() else 0, order_id))
        cur.execute("DELETE FROM order_items WHERE order_id=?", (order_id,))
        lines = items_text.get("1.0", tk.END).splitlines()
        total = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            barcode = parts[0].strip()
            row = cur.execute("SELECT name, price, stock FROM products WHERE barcode=?", (barcode,)).fetchone()
            if row:
                name, price, stock = row
                to_order = 1 if stock == 0 else 0
                cur.execute("INSERT INTO order_items(order_id, barcode, product_name, to_order) VALUES (?,?,?,?)",
                            (order_id, barcode, name, to_order))
                total += clean_price(price)
        cur.execute("UPDATE orders SET total_price=? WHERE id=?", (total, order_id))
        db.conn.commit()
        refresh_stats(stats_label)
        messagebox.showinfo("AutoCore", "Zapisano zmiany")
        win.destroy()
    ttk.Button(win, text="Zapisz zmiany", command=save_changes).pack(pady=10)

def show_order_details(order_id, parent_win=None, stats_label=None, master_tree=None, category_cb=None, model_cb=None):
    win = tk.Toplevel(parent_win if parent_win else root)
    win.title(f"Zlecenie #{order_id}")
    win.geometry("1100x800")
    cur = db.conn.cursor()
    order = cur.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        win.destroy()
        return
    info_frame = ttk.LabelFrame(win, text="Dane zamówienia")
    info_frame.pack(fill="x", padx=10, pady=5)
    ttk.Label(info_frame, text=f"Klient: {order[1]}").grid(row=0, column=0, sticky="w")
    ttk.Label(info_frame, text=f"Tel: {order[2]}").grid(row=0, column=1, sticky="w")
    ttk.Label(info_frame, text=f"Dostawa: {order[5]}").grid(row=1, column=0, sticky="w")
    ttk.Label(info_frame, text=f"Status: {order[6]}").grid(row=1, column=1, sticky="w")
    ttk.Label(info_frame, text=f"Wysyłka gratis: {'Tak' if order[11] else 'Nie'}").grid(row=2, column=0, sticky="w")
    if order[7]:
        ttk.Label(info_frame, text=f"Waga: {order[7]} kg").grid(row=3, column=0, sticky="w")
    if order[8] and order[9] and order[10]:
        ttk.Label(info_frame, text=f"Paczka: {order[8]}x{order[9]}x{order[10]} cm").grid(row=3, column=1, sticky="w")
    items_frame = ttk.LabelFrame(win, text="Produkty")
    items_frame.pack(fill="both", expand=True, padx=10, pady=5)
    columns = ("Kod", "Nazwa", "Skontrolowany", "Do zamówienia", "Cena")
    tree_items = ttk.Treeview(items_frame, columns=columns, show="headings")
    for col in columns:
        tree_items.heading(col, text=col)
        tree_items.column(col, width=180)
    tree_items.pack(fill="both", expand=True)
    items = cur.execute("""
        SELECT oi.id, oi.barcode, oi.product_name, oi.picked, oi.to_order, p.price 
        FROM order_items oi JOIN products p ON oi.barcode=p.barcode
        WHERE oi.order_id=?
    """, (order_id,)).fetchall()
    total_sum = 0.0
    for item in items:
        picked_str = "TAK" if item[3] else "NIE"
        to_order_str = "TAK" if item[4] else ""
        price = clean_price(item[5])
        total_sum += price
        tree_items.insert("", "end", iid=item[0], values=(item[1], item[2], picked_str, to_order_str, f"{price:.2f}"))
    sum_frame = ttk.Frame(win)
    sum_frame.pack(fill="x", padx=10, pady=5)
    ttk.Label(sum_frame, text=f"Suma brutto: {total_sum:.2f} zł").pack(side="left", padx=10)
    ttk.Label(sum_frame, text="Rabat (kwota):").pack(side="left")
    discount_var = tk.StringVar(value=str(order[12] if order[12] else 0))
    discount_entry = ttk.Entry(sum_frame, textvariable=discount_var, width=10)
    discount_entry.pack(side="left", padx=5)
    final_price_var = tk.StringVar(value=f"{total_sum - (order[12] or 0):.2f}")
    ttk.Label(sum_frame, text="Do zapłaty:").pack(side="left", padx=10)
    ttk.Label(sum_frame, textvariable=final_price_var).pack(side="left")
    def apply_discount():
        try:
            disc = float(discount_var.get())
        except:
            disc = 0
        final = total_sum - disc
        if final < 0:
            final = 0
        final_price_var.set(f"{final:.2f}")
        cur.execute("UPDATE orders SET discount=?, total_price=? WHERE id=?", (disc, final, order_id))
        db.conn.commit()
        messagebox.showinfo("Rabat", f"Rabat naliczony. Nowa kwota: {final:.2f} zł")
    ttk.Button(sum_frame, text="Nalicz rabat", command=apply_discount).pack(side="left", padx=5)
    
    # ========== PRZYCISKI FUNKCYJNE ==========
    btn_frame = ttk.Frame(win)
    btn_frame.pack(fill="x", pady=10)
    
    def toggle_picked():
        sel = tree_items.selection()
        if not sel:
            messagebox.showwarning("Uwaga", "Wybierz produkt")
            return
        item_id = int(sel[0])
        current = cur.execute("SELECT picked, barcode FROM order_items WHERE id=?", (item_id,)).fetchone()
        if current[0]:
            messagebox.showinfo("Info", "Już skontrolowany")
            return
        barcode = current[1]
        stock_row = cur.execute("SELECT stock, name FROM products WHERE barcode=?", (barcode,)).fetchone()
        if not stock_row:
            messagebox.showerror("Błąd", "Brak produktu")
            return
        stock, name = stock_row
        if stock <= 0:
            if not messagebox.askyesno("Brak na stanie", f"Produkt {name} ma stan 0. Czy mimo to oznaczyć jako skompletowany?"):
                return
        else:
            cur.execute("UPDATE products SET stock=stock-1 WHERE barcode=?", (barcode,))
        cur.execute("UPDATE order_items SET picked=1 WHERE id=?", (item_id,))
        db.conn.commit()
        if stats_label:
            refresh_stats(stats_label)
        win.destroy()
        show_order_details(order_id, parent_win, stats_label, master_tree, category_cb, model_cb)
    ttk.Button(btn_frame, text="Odkliknij produkt (skanuj)", command=toggle_picked).pack(side="left", padx=5)
    
    def set_package():
        p_win = tk.Toplevel(win)
        p_win.title("Wymiary paczki")
        ttk.Label(p_win, text="Waga (kg)").pack()
        w_entry = ttk.Entry(p_win)
        w_entry.pack()
        ttk.Label(p_win, text="Długość (cm)").pack()
        l_entry = ttk.Entry(p_win)
        l_entry.pack()
        ttk.Label(p_win, text="Szerokość (cm)").pack()
        wd_entry = ttk.Entry(p_win)
        wd_entry.pack()
        ttk.Label(p_win, text="Wysokość (cm)").pack()
        h_entry = ttk.Entry(p_win)
        h_entry.pack()
        def save():
            cur.execute("UPDATE orders SET package_weight=?, package_length=?, package_width=?, package_height=? WHERE id=?",
                        (w_entry.get(), l_entry.get(), wd_entry.get(), h_entry.get(), order_id))
            db.conn.commit()
            p_win.destroy()
            win.destroy()
            show_order_details(order_id, parent_win, stats_label, master_tree, category_cb, model_cb)
        ttk.Button(p_win, text="Zapisz", command=save).pack(pady=10)
    ttk.Button(btn_frame, text="Zapisz wymiary paczki", command=set_package).pack(side="left", padx=5)
    
    def mark_ready():
        total = cur.execute("SELECT COUNT(*) FROM order_items WHERE order_id=?", (order_id,)).fetchone()[0]
        picked = cur.execute("SELECT COUNT(*) FROM order_items WHERE order_id=? AND picked=1", (order_id,)).fetchone()[0]
        if total == 0:
            messagebox.showwarning("Uwaga", "Brak produktów")
            return
        if picked != total:
            messagebox.showwarning("Uwaga", f"Brakuje {total-picked} produktów")
            return
        cur.execute("UPDATE orders SET status='READY' WHERE id=?", (order_id,))
        db.conn.commit()
        if stats_label:
            refresh_stats(stats_label)
        messagebox.showinfo("AutoCore", "Zlecenie gotowe")
        win.destroy()
        if parent_win:
            parent_win.destroy()
    ttk.Button(btn_frame, text="Zlecenie gotowe", command=mark_ready).pack(side="left", padx=5)
    
    def archive():
        cur.execute("UPDATE orders SET status='ARCHIVED' WHERE id=?", (order_id,))
        db.conn.commit()
        if stats_label:
            refresh_stats(stats_label)
        messagebox.showinfo("AutoCore", "Archiwum")
        win.destroy()
        if parent_win:
            parent_win.destroy()
    ttk.Button(btn_frame, text="Archiwizuj", command=archive).pack(side="left", padx=5)
    
    def edit_order():
        win.destroy()
        edit_order_window(order_id, parent_win, stats_label, master_tree, category_cb, model_cb)
    ttk.Button(btn_frame, text="Edytuj zlecenie", command=edit_order).pack(side="left", padx=5)

def orders_list_window(root, stats_label, master_tree, category_cb, model_cb):
    win = tk.Toplevel(root)
    win.title("Zlecenia")
    win.geometry("1200x600")
    filter_frame = ttk.Frame(win)
    filter_frame.pack(fill="x", padx=10, pady=5)
    def show_status(status):
        for row in tree.get_children():
            tree.delete(row)
        cur = db.conn.cursor()
        if status:
            rows = cur.execute("SELECT id, customer_name, phone, delivery_type, status FROM orders WHERE status=?", (status,)).fetchall()
        else:
            rows = cur.execute("SELECT id, customer_name, phone, delivery_type, status FROM orders").fetchall()
        for row in rows:
            tree.insert("", "end", values=row)
    ttk.Button(filter_frame, text="Wszystkie", command=lambda: show_status(None)).pack(side="left", padx=2)
    ttk.Button(filter_frame, text="Nowe (NEW)", command=lambda: show_status("NEW")).pack(side="left", padx=2)
    ttk.Button(filter_frame, text="Gotowe (READY)", command=lambda: show_status("READY")).pack(side="left", padx=2)
    ttk.Button(filter_frame, text="Archiwum (ARCHIVED)", command=lambda: show_status("ARCHIVED")).pack(side="left", padx=2)
    columns = ("ID", "Klient", "Telefon", "Dostawa", "Status")
    tree = ttk.Treeview(win, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150)
    tree.pack(fill="both", expand=True, padx=10, pady=5)
    def on_double_click(event):
        sel = tree.selection()
        if sel:
            order_id = tree.item(sel[0])["values"][0]
            show_order_details(order_id, win, stats_label, master_tree, category_cb, model_cb)
    tree.bind("<Double-1>", on_double_click)
    cur = db.conn.cursor()
    rows = cur.execute("SELECT id, customer_name, phone, delivery_type, status FROM orders WHERE status IN ('NEW','READY')").fetchall()
    for row in rows:
        tree.insert("", "end", values=row)

def check_product_window(root, tree, category_cb, model_cb, stats_label):
    win = tk.Toplevel(root)
    win.title("Sprawdź produkt")
    win.geometry("800x600")
    ttk.Label(win, text="Zeskanuj kod").pack(pady=10)
    entry = ttk.Entry(win, width=50)
    entry.pack(pady=5)
    entry.focus()
    result_text = tk.Text(win, wrap="word")
    result_text.pack(fill="both", expand=True, padx=10, pady=10)
    def search():
        barcode = entry.get().strip()
        if not barcode:
            return
        cur = db.conn.cursor()
        row = cur.execute("SELECT * FROM products WHERE barcode=?", (barcode,)).fetchone()
        result_text.delete("1.0", tk.END)
        if row:
            cols = [desc[0] for desc in cur.description]
            for i, col in enumerate(cols):
                result_text.insert(tk.END, f"{col}: {row[i]}\n")
        else:
            result_text.insert(tk.END, "BRAK. Możesz dodać.")
    entry.bind("<Return>", lambda e: search())
    ttk.Button(win, text="Szukaj", command=search).pack(pady=5)
    btn_frame = ttk.Frame(win)
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="Dodaj z Signeda", command=lambda: add_signeda_window(root, tree, category_cb, model_cb, stats_label)).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Dodaj ręcznie", command=lambda: add_manual_window(root, tree, category_cb, model_cb, stats_label)).pack(side="left", padx=5)

def additional_options_window(root, tree, stats_label, category_cb, model_cb):
    win = tk.Toplevel(root)
    win.title("Dodatkowe opcje")
    win.geometry("500x400")
    def backup_db():
        if not os.path.exists(DB_NAME):
            messagebox.showerror("Błąd", "Brak pliku bazy")
            return
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy(DB_NAME, backup_name)
        messagebox.showinfo("Backup", f"Utworzono kopię: {backup_name}")
    ttk.Button(win, text="Backup bazy danych", command=backup_db).pack(fill="x", padx=20, pady=5)
    def missing_parts_list():
        cur = db.conn.cursor()
        rows = cur.execute("""
            SELECT o.id, o.customer_name, oi.barcode, oi.product_name, p.stock, p.signeda_stock
            FROM order_items oi
            JOIN orders o ON oi.order_id=o.id
            JOIN products p ON oi.barcode=p.barcode
            WHERE o.status IN ('NEW','READY') AND oi.picked=0 AND (p.stock=0 OR oi.to_order=1)
            ORDER BY o.id
        """).fetchall()
        if not rows:
            messagebox.showinfo("Info", "Brak brakujących części")
            return
        filename = "brakujace_czesci.csv"
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["ID zlecenia", "Klient", "Kod produktu", "Nazwa", "Stan lokalny", "Stan Signeda"])
            writer.writerows(rows)
        messagebox.showinfo("Eksport", f"Wygenerowano plik {filename}")
    ttk.Button(win, text="Lista brakujących części do zleceń", command=missing_parts_list).pack(fill="x", padx=20, pady=5)
    def quick_olx():
        olx_win = tk.Toplevel(win)
        olx_win.title("Szybkie ogłoszenie OLX")
        olx_win.geometry("600x500")
        ttk.Label(olx_win, text="Wpisz kody produktów (jeden pod drugim):").pack(pady=5)
        codes_text = tk.Text(olx_win, height=10)
        codes_text.pack(fill="both", expand=True, padx=10, pady=5)
        def generate():
            lines = codes_text.get("1.0", tk.END).splitlines()
            barcodes = [line.strip() for line in lines if line.strip()]
            if not barcodes:
                messagebox.showerror("Błąd", "Brak kodów")
                return
            cur = db.conn.cursor()
            for barcode in barcodes:
                row = cur.execute("SELECT name, oe_code, price, product_type, models, condition_rating, damage_description FROM products WHERE barcode=?", (barcode,)).fetchone()
                if not row:
                    messagebox.showerror("Błąd", f"Nie znaleziono {barcode}")
                    return
                name, oe, price, ptype, models, rating, damage = row
                title = f"{name} - {models.split(chr(10))[0] if models else ''}".strip()
                desc = f"Kod OEM: {oe}\n"
                if ptype == "nowe":
                    desc += "Produkt nowy, zamiennik OEM.\n"
                else:
                    desc += f"Produkt używany. Stan: {rating}/5. Uszkodzenia: {damage}\n"
                desc += f"Cena: {price} zł\nKontakt przez OLX."
                preview = tk.Toplevel(olx_win)
                preview.title(f"Podgląd ogłoszenia - {barcode}")
                preview.geometry("600x500")
                ttk.Label(preview, text="Tytuł:").pack(anchor="w")
                ttk.Label(preview, text=title, wraplength=550).pack(anchor="w", pady=5)
                ttk.Label(preview, text="Opis:").pack(anchor="w")
                txt_desc = tk.Text(preview, height=15, wrap="word")
                txt_desc.insert("1.0", desc)
                txt_desc.pack(fill="both", expand=True)
                ttk.Label(preview, text="Cena:").pack(anchor="w")
                ttk.Label(preview, text=f"{price} zł").pack(anchor="w")
                ttk.Button(preview, text="Zamknij", command=preview.destroy).pack(pady=10)
        ttk.Button(olx_win, text="Generuj podgląd", command=generate).pack(pady=10)
    ttk.Button(win, text="Szybkie ogłoszenie OLX", command=quick_olx).pack(fill="x", padx=20, pady=5)
    def update_signeda():
        update_win = tk.Toplevel(win)
        update_win.title("Aktualizacja bazy Signeda")
        update_win.geometry("500x400")
        ttk.Label(update_win, text="Liczba produktów na raz (partia):").pack(pady=10)
        batch_var = tk.IntVar(value=10)
        batch_spin = ttk.Spinbox(update_win, from_=1, to=100, textvariable=batch_var, width=10)
        batch_spin.pack()
        ttk.Label(update_win, text="Co aktualizować?").pack(pady=10)
        update_price = tk.BooleanVar(value=True)
        update_stock = tk.BooleanVar(value=True)
        ttk.Checkbutton(update_win, text="Cena", variable=update_price).pack()
        ttk.Checkbutton(update_win, text="Stan Signeda", variable=update_stock).pack()
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(update_win, variable=progress_var, maximum=100)
        progress_bar.pack(fill="x", padx=20, pady=20)
        status_label = ttk.Label(update_win, text="")
        status_label.pack(pady=10)
        def start_update():
            cur = db.conn.cursor()
            rows = cur.execute("SELECT barcode, product_code, force_price FROM products WHERE force_price=0 AND product_code IS NOT NULL").fetchall()
            total = len(rows)
            if total == 0:
                messagebox.showinfo("Info", "Brak produktów do aktualizacji")
                update_win.destroy()
                return
            batch_size = batch_var.get()
            processed = 0
            progress_var.set(0)
            update_win.update_idletasks()
            def update_batch(start_idx):
                nonlocal processed
                end_idx = min(start_idx + batch_size, total)
                for i in range(start_idx, end_idx):
                    barcode, product_code, _ = rows[i]
                    status_label.config(text=f"Aktualizacja: {barcode}")
                    update_win.update_idletasks()
                    try:
                        data = fetch_part(barcode)
                        if data:
                            if update_price.get():
                                cur.execute("UPDATE products SET price=? WHERE barcode=?", (data["price"], barcode))
                            if update_stock.get():
                                cur.execute("UPDATE products SET signeda_stock=? WHERE barcode=?", (data["signeda_stock"], barcode))
                            db.conn.commit()
                    except Exception as e:
                        print(f"Błąd {barcode}: {e}")
                    processed += 1
                    progress_var.set((processed / total) * 100)
                    update_win.update_idletasks()
                if end_idx < total:
                    update_win.after(100, update_batch, end_idx)
                else:
                    messagebox.showinfo("Koniec", f"Zaktualizowano {processed} produktów")
                    load_products_into_tree(tree, "", "", "")
                    refresh_filters(category_cb, model_cb)
                    refresh_stats(stats_label)
                    update_win.destroy()
            update_batch(0)
        ttk.Button(update_win, text="Rozpocznij aktualizację", command=start_update).pack(pady=20)
    ttk.Button(win, text="Aktualizuj bazę Signeda", command=update_signeda).pack(fill="x", padx=20, pady=5)

# ---------- GŁÓWNE OKNO ----------
root = tk.Tk()
root.title(APP_NAME)
root.geometry("1800x900")

def bind_shortcuts():
    root.bind_all("<Control-d>", lambda e: add_signeda_window(root, tree, category_cb, model_cb, stats_label))
    root.bind_all("<Control-m>", lambda e: add_manual_window(root, tree, category_cb, model_cb, stats_label))
    root.bind_all("<Control-z>", lambda e: create_order_window(root, stats_label, tree, category_cb, model_cb))
    root.bind_all("<F5>", lambda e: refresh_all())

def refresh_all():
    load_products_into_tree(tree, search_var.get(), category_cb.get(), model_cb.get())
    refresh_stats(stats_label)

left_panel = tk.Frame(root, width=250, bg="#e5e5e5")
left_panel.pack(side="left", fill="y")
stats_label = ttk.Label(left_panel, text="", font=("Arial", 10), background="#e5e5e5")
stats_label.pack(pady=10, padx=10, fill="x")
refresh_stats(stats_label)

buttons = [
    ("Przyjmij dostawę", lambda: receive_delivery_window(root, tree, stats_label, category_cb, model_cb)),
    ("Dodaj część Signeda (Ctrl+D)", lambda: add_signeda_window(root, tree, category_cb, model_cb, stats_label)),
    ("Dodaj część ręcznie (Ctrl+M)", lambda: add_manual_window(root, tree, category_cb, model_cb, stats_label)),
    ("Stwórz zlecenie (Ctrl+Z)", lambda: create_order_window(root, stats_label, tree, category_cb, model_cb)),
    ("Wykonaj zlecenie", lambda: orders_list_window(root, stats_label, tree, category_cb, model_cb)),
    ("Przejrzyj zlecenia", lambda: orders_list_window(root, stats_label, tree, category_cb, model_cb)),
    ("Sprawdź w bazie", lambda: check_product_window(root, tree, category_cb, model_cb, stats_label)),
    ("Dodatkowe opcje", lambda: additional_options_window(root, tree, stats_label, category_cb, model_cb)),
    ("Eksportuj do CSV", lambda: export_to_csv(tree))
]
for text, cmd in buttons:
    ttk.Button(left_panel, text=text, command=cmd).pack(fill="x", padx=10, pady=5)

right_panel = tk.Frame(root)
right_panel.pack(side="right", fill="both", expand=True)

top_bar = ttk.Frame(right_panel)
top_bar.pack(fill="x", padx=5, pady=5)
ttk.Label(top_bar, text="Szukaj:").pack(side="left")
search_var = tk.StringVar()
search_entry = ttk.Entry(top_bar, textvariable=search_var, width=30)
search_entry.pack(side="left", padx=5)
ttk.Button(top_bar, text="Odśwież", command=refresh_all).pack(side="left", padx=5)
ttk.Button(top_bar, text="Eksportuj CSV", command=lambda: export_to_csv(tree)).pack(side="right")

filter_frame = tk.Frame(right_panel)
filter_frame.pack(fill="x", padx=5, pady=5)
tk.Label(filter_frame, text="Model").pack(side="left")
model_cb = ttk.Combobox(filter_frame, width=40)
model_cb.pack(side="left", padx=5)
tk.Label(filter_frame, text="Kategoria").pack(side="left")
category_cb = ttk.Combobox(filter_frame, width=30)
category_cb.pack(side="left", padx=5)

columns = ("Kod", "OEM", "Nazwa", "Typ", "Kategoria", "Strona", "Pozycja", "Stan", "Cena", "Signeda", "Modele")
tree = ttk.Treeview(right_panel, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=120)
tree.pack(fill="both", expand=True)

def sort_column(tree, col, reverse):
    data = [(tree.set(k, col), k) for k in tree.get_children("")]
    data.sort(reverse=reverse)
    for index, (val, k) in enumerate(data):
        tree.move(k, "", index)
    tree.heading(col, command=lambda: sort_column(tree, col, not reverse))
for col in columns:
    tree.heading(col, command=lambda c=col: sort_column(tree, c, False))

def apply_filters(*args):
    load_products_into_tree(tree, search_var.get(), category_cb.get(), model_cb.get())
search_var.trace("w", apply_filters)
category_cb.bind("<<ComboboxSelected>>", apply_filters)
model_cb.bind("<<ComboboxSelected>>", apply_filters)

def on_tree_double_click(event):
    sel = tree.selection()
    if not sel:
        return
    values = tree.item(sel[0])["values"]
    barcode = values[0]
    if active_order_window and active_order_window.winfo_exists():
        name = values[2]
        oe = values[1]
        price = values[8]
        add_product_to_active_order(barcode, name, oe, price)
    else:
        show_product_details_window(barcode, tree, category_cb, model_cb, stats_label)
tree.bind("<Double-1>", on_tree_double_click)

refresh_filters(category_cb, model_cb)
load_products_into_tree(tree, "", "", "")
bind_shortcuts()
root.mainloop()