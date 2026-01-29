import tkinter as tk
from tkinter import filedialog, messagebox
import sqlite3
import csv
from datetime import datetime
import winsound
import re
import threading
import os
import shutil
import glob

# ---------------- DATABASE ----------------
conn = sqlite3.connect("dip_manage.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    auto_sn TEXT,
    item_code TEXT,
    barcode TEXT UNIQUE,
    item_name TEXT,
    quantity INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS unmatched (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode TEXT UNIQUE,
    quantity INTEGER DEFAULT 1,
    first_seen TEXT
)
""")
conn.commit()

# ---------------- FUNCTIONS ----------------
def import_data():
    file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if not file:
        return
    try:
        with open(file, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    cur.execute("""
                    INSERT INTO items (auto_sn, item_code, barcode, item_name, quantity)
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        row.get("Auto SN", ""),
                        row.get("Item Code", ""),
                        row.get("Barcode", ""),
                        row.get("Item Name", ""),
                        int(row.get("Quantity", 0))
                    ))
                except sqlite3.IntegrityError:
                    pass
        conn.commit()
        messagebox.showinfo("Success", "Data Imported Successfully")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# ---------------- BARCODE SCANNING ----------------
def validate_barcode(barcode):
    barcode = barcode.strip()
    if len(barcode) < 3:
        return False, "Too short"
    if not re.match("^[A-Za-z0-9]+$", barcode):
        return False, "Invalid characters"
    return True, ""

def process_barcode(barcode):
    barcode = barcode.strip()
    if not barcode:
        return

    valid, reason = validate_barcode(barcode)
    if not valid:
        status_label.config(text=f"⚠ Broken/Invalid: {reason}", fg="orange")
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        return

    cur.execute("SELECT id, item_name, quantity FROM items WHERE barcode=?", (barcode,))
    item = cur.fetchone()
    if item:
        new_qty = item[2] + 1
        cur.execute("UPDATE items SET quantity=? WHERE id=?", (new_qty, item[0]))
        conn.commit()
        status_label.config(text=f"✔ {item[1]} | Qty: {new_qty}", fg="green")
        winsound.MessageBeep(winsound.MB_OK)
    else:
        cur.execute("SELECT quantity FROM unmatched WHERE barcode=?", (barcode,))
        un = cur.fetchone()
        if un:
            cur.execute("UPDATE unmatched SET quantity=? WHERE barcode=?", (un[0]+1, barcode))
        else:
            cur.execute("INSERT INTO unmatched (barcode, quantity, first_seen) VALUES (?, ?, ?)",
                        (barcode, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        status_label.config(text=f"✖ Barcode not found!", fg="red")
        winsound.MessageBeep(winsound.MB_ICONHAND)

def auto_scan(event=None):
    barcode = scan_entry.get()
    scan_entry.delete(0, tk.END)
    threading.Thread(target=process_barcode, args=(barcode,), daemon=True).start()

# ---------------- EXPORT PREVIEW ----------------
def preview_export(data_type="matched"):
    preview_win = tk.Toplevel(root)
    preview_win.title(f"Preview {data_type.capitalize()} Data")
    preview_win.geometry("700x500")

    text = tk.Text(preview_win)
    text.pack(fill="both", expand=True)

    def save_preview():
        file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title=f"Save {data_type.capitalize()} Data"
        )
        if not file:
            return
        with open(file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if data_type == "matched":
                writer.writerow(["Item Name", "Barcode", "Quantity"])
            else:
                writer.writerow(["Barcode", "Quantity", "First Seen"])
            for row in preview_data:
                writer.writerow(row)
        messagebox.showinfo("Saved", f"{data_type.capitalize()} data saved successfully!")

    tk.Button(preview_win, text="Save CSV", command=save_preview, bg="green", fg="white", font=("Arial",12,"bold")).pack(pady=5)

    global preview_data
    preview_data = []
    if data_type == "matched":
        cur.execute("SELECT item_name, barcode, quantity FROM items WHERE quantity > 0")
        preview_data = cur.fetchall()
        if not preview_data:
            text.insert(tk.END, "No scanned items to export.\n")
            return
        for row in preview_data:
            text.insert(tk.END, f"{row[0]} | {row[1]} | Qty: {row[2]}\n")
    else:
        cur.execute("SELECT barcode, quantity, first_seen FROM unmatched")
        preview_data = cur.fetchall()
        if not preview_data:
            text.insert(tk.END, "No unmatched items to export.\n")
            return
        for row in preview_data:
            text.insert(tk.END, f"{row[0]} | {row[1]} | First Seen: {row[2]}\n")

# ---------------- VIEW REPORT ----------------
def view_report():
    report = tk.Toplevel(root)
    report.title("Scanned Items Report")
    report.geometry("700x500")
    text = tk.Text(report)
    text.pack(fill="both", expand=True)
    
    cur.execute("SELECT item_name, barcode, quantity FROM items WHERE quantity > 0 ORDER BY item_name")
    data = cur.fetchall()
    if not data:
        text.insert(tk.END, "No items scanned yet.\n")
        return
    for row in data:
        text.insert(tk.END, f"{row[0]} | {row[1]} | Qty: {row[2]}\n")

# ---------------- ABOUT ----------------
def show_about():
    messagebox.showinfo(
        "About Dip Manage Pro",
        "Dip Manage Pro\n\n"
        "Developer: Dipesh Tajpuriya\n"
        "Email: gagagaga.com\n\n"
        "Advanced barcode inventory management system\n"
        "Automatic scanning, real-time updates, sound alerts."
    )

# ---------------- EDIT CODE WITH VERSION CONTROL ----------------
def edit_code_with_versions():
    editor = tk.Toplevel(root)
    editor.title("Edit Code with Versions")
    editor.geometry("1000x600")

    code_text = tk.Text(editor, font=("Consolas", 12))
    code_text.pack(fill="both", expand=True, side="left")

    version_frame = tk.Frame(editor)
    version_frame.pack(fill="y", side="right", padx=5, pady=5)
    tk.Label(version_frame, text="Previous Versions", font=("Arial", 12, "bold")).pack(pady=5)
    version_listbox = tk.Listbox(version_frame, width=40)
    version_listbox.pack(fill="y", expand=True)

    versions_folder = "versions"
    os.makedirs(versions_folder, exist_ok=True)

    script_path = os.path.realpath(__file__)
    with open(script_path, "r", encoding="utf-8") as f:
        code_text.insert(tk.END, f.read())

    def load_versions():
        version_listbox.delete(0, tk.END)
        files = sorted(glob.glob(f"{versions_folder}/*.py"), reverse=True)
        for file in files:
            version_listbox.insert(tk.END, os.path.basename(file))
        return files
    version_files = load_versions()

    def save_changes():
        new_code = code_text.get("1.0", tk.END)
        try:
            compile(new_code, "<string>", "exec")
        except SyntaxError as e:
            messagebox.showerror("Syntax Error", str(e))
            return
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(versions_folder, f"dip_manage_{timestamp}.py")
            shutil.copy(script_path, backup_file)
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(new_code)
            load_versions()
            messagebox.showinfo("Success", "Code updated successfully!\nPlease restart the app to apply changes.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Button(editor, text="Apply & Save Code", command=save_changes,
              bg="green", fg="white", font=("Arial", 14, "bold"), padx=10, pady=5).pack(pady=5)

    def load_selected_version():
        sel = version_listbox.curselection()
        if not sel:
            return
        file = version_listbox.get(sel)
        with open(os.path.join(versions_folder, file), "r", encoding="utf-8") as f:
            code_text.delete("1.0", tk.END)
            code_text.insert(tk.END, f.read())

    tk.Button(version_frame, text="Load Selected Version", command=load_selected_version,
              bg="blue", fg="white", font=("Arial", 12, "bold")).pack(pady=5)

    def restore_last_good():
        files = sorted(glob.glob(f"{versions_folder}/*.py"), reverse=True)
        if not files:
            messagebox.showinfo("Info", "No previous versions found")
            return
        last_good = files[0]
        shutil.copy(last_good, script_path)
        with open(last_good, "r", encoding="utf-8") as f:
            code_text.delete("1.0", tk.END)
            code_text.insert(tk.END, f.read())
        messagebox.showinfo("Restored", f"Last good version restored: {os.path.basename(last_good)}")

    tk.Button(version_frame, text="Restore Last Good Version", command=restore_last_good,
              bg="red", fg="white", font=("Arial", 12, "bold")).pack(pady=5)

# ---------------- MANAGE ITEMS (Search/Edit/Delete) ----------------
def manage_items():
    manage_win = tk.Toplevel(root)
    manage_win.title("Manage Items")
    manage_win.geometry("800x500")

    search_frame = tk.Frame(manage_win)
    search_frame.pack(pady=5, fill="x")
    tk.Label(search_frame, text="Search:").pack(side="left")
    search_entry = tk.Entry(search_frame)
    search_entry.pack(side="left", fill="x", expand=True, padx=5)

    item_list = tk.Listbox(manage_win, font=("Arial", 12))
    item_list.pack(fill="both", expand=True, padx=10, pady=5)

    MIN_STOCK = 5

    def load_items(query=""):
        item_list.delete(0, tk.END)
        cur.execute("SELECT id, item_name, item_code, barcode, quantity FROM items WHERE item_name LIKE ? OR barcode LIKE ? OR item_code LIKE ? ORDER BY item_name",
                    (f"%{query}%", f"%{query}%", f"%{query}%"))
        for row in cur.fetchall():
            display = f"{row[1]} | {row[3]} | Qty: {row[4]}"
            if row[4] <= MIN_STOCK:
                display += " ⚠ LOW STOCK"
            item_list.insert(tk.END, display)
    load_items()

    def search_items(event=None):
        load_items(search_entry.get())
    search_entry.bind("<KeyRelease>", search_items)

    def edit_item():
        sel = item_list.curselection()
        if not sel:
            return
        index = sel[0]
        item_text = item_list.get(index)
        barcode = item_text.split("|")[1].strip()
        cur.execute("SELECT id, item_name, item_code, barcode, quantity FROM items WHERE barcode=?", (barcode,))
        item = cur.fetchone()
        if not item:
            return

        edit_win = tk.Toplevel(manage_win)
        edit_win.title("Edit Item")
        edit_win.geometry("400x300")

        tk.Label(edit_win, text="Item Name").pack()
        name_entry = tk.Entry(edit_win)
        name_entry.pack()
        name_entry.insert(0, item[1])

        tk.Label(edit_win, text="Item Code").pack()
        code_entry = tk.Entry(edit_win)
        code_entry.pack()
        code_entry.insert(0, item[2])

        tk.Label(edit_win, text="Barcode").pack()
        barcode_entry = tk.Entry(edit_win)
        barcode_entry.pack()
        barcode_entry.insert(0, item[3])

        tk.Label(edit_win, text="Quantity").pack()
        qty_entry = tk.Entry(edit_win)
        qty_entry.pack()
        qty_entry.insert(0, str(item[4]))

        def save_item():
            try:
                cur.execute("UPDATE items SET item_name=?, item_code=?, barcode=?, quantity=? WHERE id=?",
                            (name_entry.get(), code_entry.get(), barcode_entry.get(), int(qty_entry.get()), item[0]))
                conn.commit()
                messagebox.showinfo("Saved", "Item updated successfully!")
                edit_win.destroy()
                load_items(search_entry.get())
            except Exception as e:
                messagebox.showerror("Error", str(e))
        tk.Button(edit_win, text="Save Changes", command=save_item, bg="green", fg="white").pack(pady=10)

    def delete_item():
        sel = item_list.curselection()
        if not sel:
            return
        index = sel[0]
        item_text = item_list.get(index)
        barcode = item_text.split("|")[1].strip()
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {item_text}?"):
            cur.execute("DELETE FROM items WHERE barcode=?", (barcode,))
            conn.commit()
            load_items(search_entry.get())
            messagebox.showinfo("Deleted", "Item deleted successfully.")

    btn_frame = tk.Frame(manage_win)
    btn_frame.pack(pady=5)
    tk.Button(btn_frame, text="Edit Item", command=edit_item, bg="blue", fg="white").pack(side="left", padx=5)
    tk.Button(btn_frame, text="Delete Item", command=delete_item, bg="red", fg="white").pack(side="left", padx=5)

# ---------------- MAIN UI ----------------
root = tk.Tk()
root.title("Dip Manage Pro")
root.geometry("950x500")

tk.Label(root, text="DIP MANAGE PRO", font=("Arial", 20, "bold")).pack(pady=10)

scan_entry = tk.Entry(root, font=("Arial", 16), justify="center")
scan_entry.pack(pady=10, ipadx=20, ipady=8)
scan_entry.focus()
scan_entry.bind("<Return>", auto_scan)
scan_entry.bind("<Tab>", auto_scan)
scan_entry.bind("<space>", auto_scan)

status_label = tk.Label(root, text="Ready to Scan", font=("Arial", 12))
status_label.pack(pady=10)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Import CSV", width=20, command=import_data).grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="Export Matched Data", width=20, command=lambda: preview_export("matched")).grid(row=0, column=1, padx=5)
tk.Button(btn_frame, text="Export Unmatched Data", width=20, command=lambda: preview_export("unmatched")).grid(row=0, column=2, padx=5)
tk.Button(btn_frame, text="View Report", width=20, command=view_report).grid(row=0, column=3, padx=5)
tk.Button(btn_frame, text="Manage Items", width=20, command=manage_items).grid(row=0, column=4, padx=5)
tk.Button(btn_frame, text="Edit Code", width=20, command=edit_code_with_versions).grid(row=0, column=5, padx=5)
tk.Button(btn_frame, text="About", width=20, command=show_about).grid(row=0, column=6, padx=5)

root.mainloop()
