import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Dip Manage")
root.geometry("800x500")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# ---------- SCAN TAB ----------
scan_tab = ttk.Frame(notebook)
notebook.add(scan_tab, text="Scan")

tk.Label(scan_tab, text="Scan Barcode", font=("Arial", 16)).pack(pady=20)
scan_entry = tk.Entry(scan_tab, font=("Arial", 18), justify="center")
scan_entry.pack(ipadx=20, ipady=10)

# ---------- INVENTORY TAB ----------
inv_tab = ttk.Frame(notebook)
notebook.add(inv_tab, text="Inventory")

tk.Label(inv_tab, text="Inventory Management", font=("Arial", 16)).pack(pady=20)

# ---------- REPORTS TAB ----------
rep_tab = ttk.Frame(notebook)
notebook.add(rep_tab, text="Reports")

tk.Label(rep_tab, text="Reports & Exports", font=("Arial", 16)).pack(pady=20)

# ---------- TOOLS TAB ----------
tools_tab = ttk.Frame(notebook)
notebook.add(tools_tab, text="Tools")

tk.Label(tools_tab, text="Utilities", font=("Arial", 16)).pack(pady=20)

# ---------- ABOUT TAB ----------
about_tab = ttk.Frame(notebook)
notebook.add(about_tab, text="About")

tk.Label(
    about_tab,
    text="Dip Manage\n\nDeveloper: Dipesh Tajpuriya\nEmail: gagagaga.com",
    font=("Arial", 14),
    justify="center"
).pack(expand=True)

root.mainloop()

