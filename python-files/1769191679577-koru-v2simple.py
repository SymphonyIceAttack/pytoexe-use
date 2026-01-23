import sqlite3
import os
import json
from datetime import datetime
import csv

print("APP STARTED (Console Version)")

# ================= SETTINGS =================
SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "theme": "Light",
    "auto_scan": True
}

if not os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(DEFAULT_SETTINGS, f)

with open(SETTINGS_FILE, "r") as f:
    settings = json.load(f)

# ================= DATABASE =================
DB_FILE = "dip_manage_v_simple.db"
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY,
    barcode TEXT UNIQUE,
    item_name TEXT,
    original_qty INTEGER,
    scanned_qty INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY,
    user TEXT,
    barcode TEXT,
    result TEXT,
    time TEXT
)
""")

# default login
cur.execute(
    "INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'admin', 'Admin')"
)
conn.commit()

# ================= LOGIN =================
def login():
    while True:
        u = input("Username: ")
        p = input("Password: ")
        cur.execute("SELECT role FROM users WHERE username=? AND password=?", (u, p))
        r = cur.fetchone()
        if r:
            print(f"Login successful! Role: {r[0]}")
            return u, r[0]
        else:
            print("Invalid credentials. Try again.")

current_user, user_role = login()

# ================= MAIN LOOP =================
def scan(barcode):
    cur.execute("SELECT id, item_name, scanned_qty, original_qty FROM items WHERE barcode=?", (barcode,))
    item = cur.fetchone()
    if item:
        cur.execute("UPDATE items SET scanned_qty=? WHERE id=?", (item[2]+1, item[0]))
        result = "Matched"
        print(f"🟢 Matched: {item[1]}")
    else:
        result = "Unmatched"
        print("❌ Unmatched barcode")

    cur.execute(
        "INSERT INTO audit_log (user, barcode, result, time) VALUES (?, ?, ?, ?)",
        (current_user, barcode, result, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()

def export_csv():
    filename = input("Enter CSV filename to save (example: data.csv): ")
    if filename:
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Barcode", "Item Name", "Original Qty", "Scanned Qty", "Difference"])
            cur.execute("SELECT barcode, item_name, original_qty, scanned_qty, scanned_qty-original_qty FROM items")
            writer.writerows(cur.fetchall())
        print(f"CSV exported as {filename}")

def show_items():
    cur.execute("SELECT barcode, item_name, original_qty, scanned_qty, scanned_qty-original_qty FROM items")
    rows = cur.fetchall()
    print("\nCurrent Items:")
    print("Barcode | Item Name | Original | Scanned | Difference")
    for r in rows:
        print(" | ".join(map(str, r)))
    print()

# ================= CONSOLE MENU =================
while True:
    print("\n--- MENU ---")
    print("1. Scan Item")
    print("2. Show Items")
    print("3. Export CSV")
    print("4. Exit")
    choice = input("Choose an option: ")
    if choice == "1":
        code = input("Enter barcode to scan: ")
        scan(code)
    elif choice == "2":
        show_items()
    elif choice == "3":
        export_csv()
    elif choice == "4":
        print("Exiting...")
        break
    else:
        print("Invalid option, try again.")

conn.close()
