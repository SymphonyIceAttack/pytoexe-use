import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import pandas as pd
import shutil
import os
import zipfile

def log(msg):
    txt.configure(state="normal")
    txt.insert("end", msg + "\n")
    txt.see("end")
    txt.configure(state="disabled")

def choose_file(entry, filetypes=(("PDF files","*.pdf"),("All files","*.*"))):
    path = filedialog.askopenfilename(filetypes=filetypes)
    if path:
        entry.delete(0, "end")
        entry.insert(0, path)

def choose_dir(entry):
    path = filedialog.askdirectory()
    if path:
        entry.delete(0, "end")
        entry.insert(0, path)

def run_copy_pack(source_pdf, destination_folder, csv_path, dateset):
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        log(f"Error reading CSV: {e}")
        return

    os.makedirs(destination_folder, exist_ok=True)

    for name in df.iloc[:, 0]:
        name = str(name).strip()
        # create Cluster PAC_{name}_{dateset}.pdf
        new_filename = os.path.join(destination_folder, f"PAC Report__{name}_{dateset}.pdf")
        try:
            shutil.copy2(source_pdf, new_filename)
            log(f"Created: {new_filename}")
        except Exception as e:
            log(f"Error creating {new_filename}: {e}")

        # create Cluster PAC Package_{name}_{dateset}.pdf
        pdf_path = os.path.join(destination_folder, f"Cluster PAC Package_{name}_{dateset}.pdf")
        try:
            shutil.copy2(source_pdf, pdf_path)
            log(f"Created: {pdf_path}")
        except Exception as e:
            log(f"Error creating {pdf_path}: {e}")

        # make a zip file containing the Package PDF
        zip_path = os.path.join(destination_folder, f"Cluster PAC Package_{name}_{dateset}.zip")
        try:
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.write(pdf_path, arcname=os.path.basename(pdf_path))
            log(f"Created ZIP: {zip_path}")
        except Exception as e:
            log(f"Error creating ZIP {zip_path}: {e}")

def start_process():
    src = ent_source.get().strip()
    dest = ent_dest.get().strip()
    csvp = ent_csv.get().strip()
    ds = ent_dateset.get().strip()

    if not all([src, dest, csvp, ds]):
        messagebox.showwarning("Missing input", "All cells should be filled.")
        return

    btn_run.config(state="disabled")
    log("Starting...")

    def worker():
        try:
            run_copy_pack(src, dest, csvp, ds)
            log("Completed.")
            messagebox.showinfo("Done", "Finish.")
        finally:
            btn_run.config(state="normal")

    threading.Thread(target=worker, daemon=True).start()

# --- GUI ---
root = tk.Tk()
root.title("Cluster PAC Batch Creator")

frm = ttk.Frame(root, padding=10)
frm.grid(sticky="nsew")

ttk.Label(frm, text="Source PDF :").grid(row=0, column=0, sticky="w")
ent_source = ttk.Entry(frm, width=60)
ent_source.grid(row=0, column=1, padx=5)
ttk.Button(frm, text="Browse", command=lambda: choose_file(ent_source, (("PDF files","*.pdf"),("All files","*.*")))).grid(row=0, column=2)

ttk.Label(frm, text="CSV Sitelist Path :").grid(row=1, column=0, sticky="w")
ent_csv = ttk.Entry(frm, width=60)
ent_csv.grid(row=1, column=1, padx=5)
ttk.Button(frm, text="Browse", command=lambda: choose_file(ent_csv, (("CSV files","*.csv"),("All files","*.*")))).grid(row=1, column=2)

ttk.Label(frm, text="Destination Folder :").grid(row=2, column=0, sticky="w")
ent_dest = ttk.Entry(frm, width=60)
ent_dest.grid(row=2, column=1, padx=5)
ttk.Button(frm, text="Browse", command=lambda: choose_dir(ent_dest)).grid(row=2, column=2)

ttk.Label(frm, text="Date :").grid(row=3, column=0, sticky="w")
ent_dateset = ttk.Entry(frm, width=20)
ent_dateset.grid(row=3, column=1, sticky="w", pady=5)

btn_run = ttk.Button(frm, text="Run", command=start_process)
btn_run.grid(row=4, column=1, sticky="w", pady=(0,10))

txt = tk.Text(frm, width=90, height=15, state="disabled")
txt.grid(row=5, column=0, columnspan=3, pady=(5,0))

root.columnconfigure(0, weight=1)
root.mainloop()