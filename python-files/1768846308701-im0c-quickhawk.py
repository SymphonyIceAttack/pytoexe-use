import shutil
import tempfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import ctypes

# ================= SAFETY =================
BLOCKED_KEYWORDS = ["system32", "windows\\installer", "program files"]

def is_admin():
try:
return ctypes.windll.shell32.IsUserAnAdmin()
except:
return False

def safe_path(path):
p = path.lower()
return not any(b in p for b in BLOCKED_KEYWORDS)

# ================= PATHS =================
PATHS = {
"Windows Temp": tempfile.gettempdir(),
"User Temp": os.environ.get("TEMP"),
"Chrome Cache": os.path.expandvars(
r"%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cache"
),
"Edge Cache": os.path.expandvars(
r"%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Cache"
),
"Firefox Cache": os.path.expandvars(
r"%APPDATA%\\Mozilla\\Firefox\\Profiles"
),
}

# ================= CORE LOGIC =================
def scan_folder(path):
total = 0
files = 0
for root, _, filenames in os.walk(path, errors="ignore"):
for f in filenames:
try:
fp = os.path.join(root, f)
total += os.path.getsize(fp)
files += 1
except:
pass
return total, files

def clean_folder(path):
freed = 0
for root, dirs, files in os.walk(path, topdown=False):
for f in files:
try:
fp = os.path.join(root, f)
freed += os.path.getsize(fp)
os.remove(fp)
except:
pass
for d in dirs:
try:
shutil.rmtree(os.path.join(root, d), ignore_errors=True)
except:
pass
return freed

# ================= UI =================
class QuickHawk(tk.Tk):
def __init__(self):
super().__init__()
self.title("QuickHawk Lite – Free System Cleaner")
self.geometry("820x520")

self.items = {}
self.progress = tk.IntVar(value=0)

self.build_ui()

def build_ui(self):
tk.Label(
self,
text="QuickHawk Lite",
font=("Segoe UI", 22, "bold")
).pack(pady=10)

if not is_admin():
tk.Label(
self,
text="⚠ Run as Administrator for best results",
fg="red"
).pack()

self.list_frame = tk.Frame(self)
self.list_frame.pack(fill="both", expand=True, padx=20, pady=10)

ttk.Button(self, text="Scan System", command=self.start_scan).pack(pady=4)
ttk.Button(self, text="Clean Selected", command=self.start_clean).pack(pady=4)

self.bar = ttk.Progressbar(self, variable=self.progress, maximum=100)
self.bar.pack(fill="x", padx=20, pady=10)

def start_scan(self):
self.clear()
self.progress.set(0)

def scan():
results = {}
valid = [(k, v) for k, v in PATHS.items() if v and os.path.exists(v)]

for i, (name, path) in enumerate(valid):
if safe_path(path):
size, count = scan_folder(path)
results[name] = {
"path": path,
"size": size,
"count": count,
"var": tk.BooleanVar(value=True),
}
self.progress.set(int((i + 1) / len(valid) * 100))

self.items = results
self.render_results()

threading.Thread(target=scan, daemon=True).start()

def render_results(self):
for name, data in self.items.items():
size_mb = data["size"] / (1024 * 1024)
ttk.Checkbutton(
self.list_frame,
text=f"{name} — {data['count']} files — {size_mb:.2f} MB",
variable=data["var"]
).pack(anchor="w", pady=2)

def start_clean(self):
if not self.items:
return

if not messagebox.askyesno(
"Confirm",
"""Selected files will be permanently deleted.\nContinue?"""
):
return

self.progress.set(0)

def clean():
total = len(self.items)
done = 0
freed = 0

for data in self.items.values():
if data["var"].get():
freed += clean_folder(data["path"])
done += 1
self.progress.set(int(done / total * 100))

messagebox.showinfo(
"Cleaning Complete",
f"Freed {freed / (1024 * 1024):.2f} MB"
)

threading.Thread(target=clean, daemon=True).start()

def clear(self):
for w in self.list_frame.winfo_children():
w.destroy()

# ================= RUN =================
if __name__ == "__main__":
app = QuickHawk()
app.mainloop()
''')