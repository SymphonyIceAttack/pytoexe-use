import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure 
import matplotlib
matplotlib.use("TkAgg")



# ================== DATA ==================
df = None

DATA_COLUMNS = [
    "Name","REGION","WILAYA","DAIRA","COMMUNE","PHASE","SUBPHASE",
    "STATUS","STATRM","ON_AIR","ONAIR_2G","ONAIR_4G",
    "SITES_CLUTTER","TYPE_SITE","LAYER","TECHNOLOGY",
    "BSC","RNC","LAC","LAC_3G","TAC","LAC_RAC"
]

SUMMARY_COLUMNS = ("TYPE","VALUE","COUNT")

# ================== FUNCTIONS ==================
def load_excel():
    global df
    path = filedialog.askopenfilename(filetypes=[("Excel Files","*.xlsx *.xls")])
    if not path:
        return

    df = pd.read_excel(path)
    df.columns = df.columns.str.strip()

    wilaya_cb["values"] = sorted(df["WILAYA"].dropna().unique())
    wilaya_cb.set("")
    commune_cb.set("")
    status_cb.set("")
    statrm_cb.set("")
    onair_cb.set("")

    clear_all()

def clear_all():
    data_table.delete(*data_table.get_children())
    summary_table.delete(*summary_table.get_children())
    fig.clear()
    canvas.draw()

def on_wilaya_selected(event=None):
    if df is None:
        return

    d = df[df["WILAYA"] == wilaya_cb.get()]
    commune_cb["values"] = sorted(d["COMMUNE"].dropna().unique())
    status_cb["values"] = sorted(d["STATUS"].dropna().unique())
    statrm_cb["values"] = sorted(d["STATRM"].dropna().unique())
    onair_cb["values"] = sorted(d["ON_AIR"].dropna().unique())

    commune_cb.set("")
    status_cb.set("")
    statrm_cb.set("")
    onair_cb.set("")
    apply_filters()

def apply_filters(event=None):
    if df is None:
        return

    data = df.copy()

    if wilaya_cb.get():
        data = data[data["WILAYA"] == wilaya_cb.get()]
    if commune_cb.get():
        data = data[data["COMMUNE"] == commune_cb.get()]
    if status_cb.get():
        data = data[data["STATUS"] == status_cb.get()]
    if statrm_cb.get():
        data = data[data["STATRM"] == statrm_cb.get()]
    if onair_cb.get():
        data = data[data["ON_AIR"] == onair_cb.get()]

    update_data_table(data)
    update_summary_table(data)
    update_charts(data)

# ================== TABLES ==================
def update_data_table(data):
    data_table.delete(*data_table.get_children())
    for _, row in data.iterrows():
        item = data_table.insert("", "end",
            values=[row.get(c,"") for c in DATA_COLUMNS])

        # 🔴🟢 تلوين حسب ON_AIR
        if str(row.get("ON_AIR")).lower() in ["yes","true","1","on"]:
            data_table.item(item, tags=("onair",))
        else:
            data_table.item(item, tags=("offair",))

def update_summary_table(data):
    summary_table.delete(*summary_table.get_children())
    total = len(data)

    for col in ["STATUS","STATRM","ON_AIR"]:
        summary_table.insert("", "end",
            values=(col,"TOTAL",total), tags=("total",))

        for val,cnt in data[col].value_counts().items():
            summary_table.insert("", "end", values=(col,val,cnt))

# ================== CHARTS ==================
def update_charts(data):
    fig.clear()
    cols = ["STATUS","STATRM","ON_AIR"]

    for i,col in enumerate(cols,1):
        ax = fig.add_subplot(3,1,i)
        counts = data[col].value_counts()

        ax.bar(counts.index.astype(str), counts.values, color="#4cc9f0")
        ax.set_title(col, color="white")
        ax.set_facecolor("#1e1e1e")
        ax.tick_params(colors="white")
        ax.spines[:].set_color("white")
        ax.grid(axis="y", alpha=0.3)

        ax.text(0.95,0.9,f"TOTAL = {counts.sum()}",
            transform=ax.transAxes,
            ha="right",color="white",weight="bold")

    fig.patch.set_facecolor("#1e1e1e")
    fig.tight_layout()
    canvas.draw()

# ================== UI ==================
root = tk.Tk()
root.title("📊 Network Dashboard")
root.geometry("2200x850")
root.configure(bg="#121212")

style = ttk.Style()
style.theme_use("clam")

style.configure("Treeview",
    background="#1e1e1e",
    foreground="white",
    fieldbackground="#1e1e1e",
    rowheight=24)

style.configure("Treeview.Heading",
    background="#2a2a2a",
    foreground="white",
    font=("Arial",10,"bold"))

style.map("Treeview",
    background=[("selected","#3a86ff")])

# ===== HEADER =====
header = tk.Frame(root, bg="#0d1b2a", height=55)
header.pack(fill="x")

tk.Label(header,
    text="📡 Network Dashboard",
    bg="#0d1b2a",
    fg="white",
    font=("Segoe UI",18,"bold")
).pack(side="left", padx=20)

tk.Button(header,
    text="📂 Load Excel",
    command=load_excel,
    bg="#3a86ff",
    fg="white"
).pack(side="right", padx=20, pady=10)

# ===== FILTER BAR =====
filters = tk.Frame(root, bg="#161616")
filters.pack(fill="x", pady=4)

def add_filter(text, widget):
    f = tk.Frame(filters, bg="#161616")
    f.pack(side="left", padx=8)
    tk.Label(f, text=text, bg="#161616",
             fg="white", font=("Arial",9,"bold")).pack(anchor="w")
    widget.pack()

wilaya_cb = ttk.Combobox(filters, width=18, state="readonly")
commune_cb = ttk.Combobox(filters, width=18, state="readonly")
status_cb = ttk.Combobox(filters, width=15, state="readonly")
statrm_cb = ttk.Combobox(filters, width=15, state="readonly")
onair_cb = ttk.Combobox(filters, width=15, state="readonly")

add_filter("🏙️ WILAYA", wilaya_cb)
add_filter("🏘️ COMMUNE", commune_cb)
add_filter("📌 STATUS", status_cb)
add_filter("📡 STATRM", statrm_cb)
add_filter("🟢 ON AIR", onair_cb)

wilaya_cb.bind("<<ComboboxSelected>>", on_wilaya_selected)
commune_cb.bind("<<ComboboxSelected>>", apply_filters)
status_cb.bind("<<ComboboxSelected>>", apply_filters)
statrm_cb.bind("<<ComboboxSelected>>", apply_filters)
onair_cb.bind("<<ComboboxSelected>>", apply_filters)

# ===== SPLIT =====
paned = ttk.Panedwindow(root, orient=tk.HORIZONTAL)
paned.pack(fill="both", expand=True, padx=5, pady=5)

# DATA
frame_left = ttk.LabelFrame(paned, text="📄 DATA")
paned.add(frame_left, weight=3)

data_table = ttk.Treeview(frame_left, columns=DATA_COLUMNS, show="headings")
for c in DATA_COLUMNS:
    data_table.heading(c, text=c)
    data_table.column(c, width=110, anchor="center")

data_table.tag_configure("onair", background="#1b4332")
data_table.tag_configure("offair", background="#6a040f")

data_table.pack(fill="both", expand=True)

# SUMMARY
frame_mid = ttk.LabelFrame(paned, text="📊 SUMMARY")
paned.add(frame_mid, weight=1)

summary_table = ttk.Treeview(frame_mid, columns=SUMMARY_COLUMNS, show="headings")
for c in SUMMARY_COLUMNS:
    summary_table.heading(c, text=c)
    summary_table.column(c, width=120, anchor="center")

summary_table.tag_configure("total", background="#3a86ff", font=("Arial",10,"bold"))
summary_table.pack(fill="both", expand=True)

# CHARTS
frame_right = ttk.LabelFrame(paned, text="📈 CHARTS")
paned.add(frame_right, weight=2)

fig = Figure(figsize=(6,6))
canvas = FigureCanvasTkAgg(fig, master=frame_right)
canvas.get_tk_widget().pack(fill="both", expand=True)

root.mainloop()