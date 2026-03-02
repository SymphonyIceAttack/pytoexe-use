import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import csv
import shutil
import os
import re
def log(msg):
    txt.configure(state="normal")
    txt.insert("end", msg + "\n")
    txt.see("end")
    txt.configure(state="disabled")

def choose_file(entry, filetypes=(("ZIP files","*.zip"), ("All files","*.*"))):
    path = filedialog.askopenfilename(filetypes=filetypes)
    if path:
        entry.delete(0, "end")
        entry.insert(0, path)

def choose_dir(entry):
    path = filedialog.askdirectory()
    if path:
        entry.delete(0, "end")
        entry.insert(0, path)

def run_copy_zip(source_zip, destination_folder, csv_path, pattern, dateset, overwrite=False):
    names = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
    except Exception as e:
        log(f"Error reading CSV: {e}")
        return

    if len(rows) < 2:
        log("CSV harus punya header dan minimal 1 data row.")
        return

    for row in rows[1:]:
        if row:  # skip baris kosong
            val = str(row[0]).strip()
            if val:
                names.append(val)

    if not names:
        log("No names found in CSV (after header).")
        return

    os.makedirs(destination_folder, exist_ok=True)

    for i, name in enumerate(names, start=1):
        s = name or f"item{i}"
        # Replace problematic characters with underscore
        s = re.sub(r"[\\/:*?\"<>|]", "_", s)
        s = s.strip().replace(" ", "_")
        clean = s
        filename = pattern.format(name=clean, index=i, date=dateset)
        if not filename.lower().endswith('.zip'):
            filename = filename + '.zip'
        dst_path = os.path.join(destination_folder, filename)

        if os.path.exists(dst_path) and not overwrite:
            log(f"Skipped (exists): {dst_path}")
            continue

        try:
            shutil.copy2(source_zip, dst_path)
            log(f"Created: {dst_path}")
        except Exception as e:
            log(f"Error creating {dst_path}: {e}")

    log("Done copying zips.")

def start_process():
    src = ent_source.get().strip()
    dest = ent_dest.get().strip()
    csvp = ent_csv.get().strip()
    pat = ent_pattern.get().strip()
    ds = ent_dateset.get().strip()
    ow = var_overwrite.get()

    if not all([src, dest, csvp, pat]):
        messagebox.showwarning("Missing input", "Source, CSV, destination and pattern must be filled.")
        return

    btn_run.config(state="disabled")
    log("Starting...")

    def worker():
        try:
            run_copy_zip(src, dest, csvp, pat, ds, overwrite=ow)
            log("Completed.")
            messagebox.showinfo("Done", "Finish.")
        finally:
            btn_run.config(state="normal")

    threading.Thread(target=worker, daemon=True).start()

# --- GUI ---
root = tk.Tk()
root.title("Mesin Penyalin ZIP")

frm = ttk.Frame(root, padding=10)
frm.grid(sticky="nsew")

ttk.Label(frm, text="Source ZIP :").grid(row=0, column=0, sticky="w")
ent_source = ttk.Entry(frm, width=60)
ent_source.grid(row=0, column=1, padx=5)
ttk.Button(frm, text="Browse", command=lambda: choose_file(ent_source, (("ZIP files","*.zip"),("All files","*.*")))).grid(row=0, column=2)

ttk.Label(frm, text="CSV Sitelist Path :").grid(row=1, column=0, sticky="w")
ent_csv = ttk.Entry(frm, width=60)
ent_csv.grid(row=1, column=1, padx=5)
ttk.Button(frm, text="Browse", command=lambda: choose_file(ent_csv, (("CSV files","*.csv"),("All files","*.*")))).grid(row=1, column=2)

ttk.Label(frm, text="Destination Folder :").grid(row=2, column=0, sticky="w")
ent_dest = ttk.Entry(frm, width=60)
ent_dest.grid(row=2, column=1, padx=5)
ttk.Button(frm, text="Browse", command=lambda: choose_dir(ent_dest)).grid(row=2, column=2)

ttk.Label(frm, text="Filename Pattern :").grid(row=3, column=0, sticky="w")
ent_pattern = ttk.Entry(frm, width=60)
ent_pattern.grid(row=3, column=1, padx=5)
# default pattern uses {name}, {index}, {date}
ent_pattern.insert(0, "Cluster PAC Package_{name}_{date}")

ttk.Label(frm, text="Date :").grid(row=4, column=0, sticky="w")
ent_dateset = ttk.Entry(frm, width=20)
ent_dateset.grid(row=4, column=1, sticky="w", pady=5)

var_overwrite = tk.BooleanVar(value=False)
chk = ttk.Checkbutton(frm, text="Overwrite existing files", variable=var_overwrite)
chk.grid(row=4, column=2, sticky="w")

btn_run = ttk.Button(frm, text="Run", command=start_process)
btn_run.grid(row=5, column=1, sticky="w", pady=(10,10))

txt = tk.Text(frm, width=90, height=15, state="disabled")
txt.grid(row=6, column=0, columnspan=3, pady=(5,0))

root.columnconfigure(0, weight=1)
root.mainloop()
