import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3, os, importlib, json, shutil, glob
from datetime import datetime
import winsound

# ---------------- SETTINGS ----------------
CONFIG_FILE = "config/settings.json"
PLUGINS_DIR = "plugins"

default_settings = {
    "low_stock_limit": 5,
    "sound_alerts": True
}

# ---------------- DATABASE ----------------
os.makedirs("data", exist_ok=True)
conn = sqlite3.connect("data/dip_manage.db")
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    auto_sn TEXT,
    item_code TEXT,
    barcode TEXT UNIQUE,
    item_name TEXT,
    quantity INTEGER DEFAULT 0
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS unmatched (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode TEXT UNIQUE,
    quantity INTEGER DEFAULT 1,
    first_seen TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS scan_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode TEXT,
    status TEXT,
    scan_time TEXT
)""")
conn.commit()

# ---------------- CONFIG ----------------
os.makedirs("config", exist_ok=True)
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE,"w") as f:
        json.dump(default_settings, f)
with open(CONFIG_FILE,"r") as f:
    settings = json.load(f)

# ---------------- UTILS ----------------
def play_ok(): 
    if settings.get("sound_alerts",True): winsound.MessageBeep(winsound.MB_OK)
def play_error():
    if settings.get("sound_alerts",True): winsound.MessageBeep(winsound.MB_ICONHAND)
def clean_barcode(code): return "".join(filter(str.isalnum, code.strip()))

def reload_plugin(plugin_name):
    try:
        mod = importlib.import_module(f"{PLUGINS_DIR}.{plugin_name}")
        importlib.reload(mod)
        return mod
    except Exception as e:
        messagebox.showerror("Plugin Error", f"Failed to load {plugin_name}: {e}")
        return None

def backup_plugin(plugin_file):
    os.makedirs("plugin_versions", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy(f"{PLUGINS_DIR}/{plugin_file}", f"plugin_versions/{plugin_file}_{timestamp}.py")

# ---------------- LOAD PLUGINS ----------------
scan_plugin = reload_plugin("scan_plugin")
inventory_plugin = reload_plugin("inventory_plugin")
report_plugin = reload_plugin("report_plugin")
tools_plugin = reload_plugin("tools_plugin")

# ---------------- UI ----------------
root = tk.Tk()
root.title("Dip Manage - Plugin System")
root.geometry("950x550")
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# ---------------- SCAN TAB ----------------
scan_tab = ttk.Frame(notebook)
notebook.add(scan_tab, text="Scan")
tk.Label(scan_tab, text="Scan Barcode", font=("Arial",16)).pack(pady=10)
scan_entry = tk.Entry(scan_tab, font=("Arial",18), justify="center")
scan_entry.pack(ipadx=20, ipady=10)
scan_entry.focus()
status_label = tk.Label(scan_tab,text="Ready to Scan", font=("Arial",12))
status_label.pack(pady=5)

def scan_event(event=None):
    if scan_plugin:
        scan_plugin.scan_barcode(scan_entry,status_label,cur,conn,settings)

scan_entry.bind("<Return>", scan_event)

# ---------------- INVENTORY TAB ----------------
inv_tab = ttk.Frame(notebook)
notebook.add(inv_tab,text="Inventory")
if inventory_plugin:
    inventory_plugin.build_inventory_tab(inv_tab, cur, conn)

# ---------------- REPORTS TAB ----------------
rep_tab = ttk.Frame(notebook)
notebook.add(rep_tab,text="Reports")
if report_plugin:
    report_plugin.build_report_tab(rep_tab, cur, conn)

# ---------------- TOOLS TAB ----------------
tools_tab = ttk.Frame(notebook)
notebook.add(tools_tab,text="Tools")
if tools_plugin:
    tools_plugin.build_tools_tab(tools_tab, cur, conn)

# ---------------- ABOUT TAB ----------------
about_tab = ttk.Frame(notebook)
notebook.add(about_tab,text="About")
tk.Label(
    about_tab,
    text="Dip Manage\n\nDeveloper: Dipesh Tajpuriya\nEmail: gagagaga.com",
    font=("Arial",14),
    justify="center"
).pack(expand=True)

# ---------------- PLUGIN MANAGER TAB ----------------
plugin_manager_tab = ttk.Frame(notebook)
notebook.add(plugin_manager_tab, text="Plugin Manager")
tk.Label(plugin_manager_tab,text="Plugin Version Manager", font=("Arial",16)).pack(pady=10)

plugin_listbox = tk.Listbox(plugin_manager_tab)
plugin_listbox.pack(fill="both", expand=True, padx=10, pady=5)
version_listbox = tk.Listbox(plugin_manager_tab)
version_listbox.pack(fill="both", expand=True, padx=10, pady=5)

def load_plugins_list():
    plugin_listbox.delete(0, tk.END)
    for f in os.listdir(PLUGINS_DIR):
        if f.endswith(".py"): plugin_listbox.insert(tk.END, f)
load_plugins_list()

def load_versions(event=None):
    version_listbox.delete(0, tk.END)
    sel = plugin_listbox.curselection()
    if not sel: return
    plugin_name = plugin_listbox.get(sel[0])
    versions = glob.glob(f"plugin_versions/{plugin_name}_*.py")
    versions.sort(reverse=True)
    for v in versions: version_listbox.insert(tk.END, os.path.basename(v))
plugin_listbox.bind("<<ListboxSelect>>", load_versions)

def rollback_plugin():
    sel_plugin = plugin_listbox.curselection()
    sel_version = version_listbox.curselection()
    if not sel_plugin or not sel_version:
        messagebox.showwarning("Select","Select plugin and version")
        return
    plugin_name = plugin_listbox.get(sel_plugin[0])
    version_file = version_listbox.get(sel_version[0])
    src = os.path.join("plugin_versions",version_file)
    dst = os.path.join(PLUGINS_DIR,plugin_name)
    shutil.copy(src,dst)
    messagebox.showinfo("Done",f"{plugin_name} restored to {version_file}")
    load_plugins_list()

tk.Button(plugin_manager_tab, text="Rollback Selected Version", command=rollback_plugin).pack(pady=5)

# ---------------- RUN ----------------
root.mainloop()
