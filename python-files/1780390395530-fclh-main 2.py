import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import os
import threading
import time

# Paths
BASE_DIR = os.getcwd()
BASE_USER = os.path.expanduser("~")

ITP_LOAD_PATH = os.path.join(
    BASE_USER,
    "IMPERIAL TOBACCO LTD",
    "Corporate Product Master Data Team - General",
    "PYTHON TOOLS",
    "ITP Load",
    "ITPLoad.py"
)
PLM_LOAD_PATH = os.path.join(
    BASE_USER,
    "IMPERIAL TOBACCO LTD",
    "Corporate Product Master Data Team - General",
    "PYTHON TOOLS",
    "PLM Load",
    "PLMLoad.py"
)

VOLUMETRICS_PATH = os.path.join(
    BASE_USER,
    "IMPERIAL TOBACCO LTD",
    "Corporate Product Master Data Team - General",
    "PYTHON TOOLS",
    "Basic Data 1",
    "Volumetrics.py"
)

PLM_SAP_CHECK_PATH = os.path.join(
    BASE_USER,
    "IMPERIAL TOBACCO LTD",
    "Corporate Product Master Data Team - General",
    "PYTHON TOOLS",
    "PLM_SAP_CHECK",
    "PLM_SAP_CHECK.py"
)

NFG_TOOL_PATH = os.path.join(
    BASE_USER,
    "IMPERIAL TOBACCO LTD",
    "Corporate Product Master Data Team - General",
    "PYTHON TOOLS",
    "NFG_CREATION",
    "NFG_Tool.py"
)
# Excel / Folder Paths
ITP_EXCEL = r"\\dehhsr112\Fileserver\MSRD_Planning & Supply\GPMD\03_Master Data Management\05 SCM-ITP\ITP"

PLM_EXCEL = os.path.join(
    BASE_USER,
    "IMPERIAL TOBACCO LTD",
    "Corporate Product Master Data Team - General",
    "PYTHON TOOLS",
    "PLM Load",
    "PLM_Data.xlsx"
)

VOLUMETRICS_EXCEL = os.path.join(
    BASE_USER,
    "IMPERIAL TOBACCO LTD",
    "Corporate Product Master Data Team - General",
    "PYTHON TOOLS",
    "Basic Data 1",
    "Volumetrics_Check.xlsx"
)

PLM_SAP_EXCEL = os.path.join(
    BASE_USER,
    "IMPERIAL TOBACCO LTD",
    "Corporate Product Master Data Team - General",
    "PYTHON TOOLS",
    "PLM_SAP_CHECK",
    "RSKU CHECK_SAP_PLM.xlsx"
)

NFG_EXCEL = os.path.join(
    BASE_USER,
    "IMPERIAL TOBACCO LTD",
    "Corporate Product Master Data Team - General",
    "PYTHON TOOLS",
    "NFG_CREATION",
    "TEMPLATE.xlsx"
)

# =========================
# FOLDERS
# =========================

ITP_FOLDER = os.path.join(
    BASE_USER,
    "IMPERIAL TOBACCO LTD",
    "Corporate Product Master Data Team - General",
    "PYTHON TOOLS",
    "ITP Load"
)

PLM_FOLDER = os.path.join(
    BASE_USER,
    "IMPERIAL TOBACCO LTD",
    "Corporate Product Master Data Team - General",
    "PYTHON TOOLS",
    "PLM Load"
)

VOLUMETRICS_FOLDER = os.path.join(
    BASE_USER,
    "IMPERIAL TOBACCO LTD",
    "Corporate Product Master Data Team - General",
    "PYTHON TOOLS",
    "Basic Data 1"
)

PLM_SAP_FOLDER = os.path.join(
    BASE_USER,
    "IMPERIAL TOBACCO LTD",
    "Corporate Product Master Data Team - General",
    "PYTHON TOOLS",
    "PLM_SAP_CHECK"
)

NFG_FOLDER = os.path.join(
    BASE_USER,
    "IMPERIAL TOBACCO LTD",
    "Corporate Product Master Data Team - General",
    "PYTHON TOOLS",
    "NFG_CREATION"
)

def run_script(path, tool_name):
    if not os.path.exists(path):
        messagebox.showerror("Error", f"File not found:\n{path}")
        return

    def task():
        set_loading(True, tool_name)

        # Simulate loading progress
        for i in range(101):
            progress["value"] = i
            root.update_idletasks()
            time.sleep(0.01)  # adjust speed here

        try:
            subprocess.Popen(["python", path])
            progress["value"] = 100
            progress.config(style="Green.Horizontal.TProgressbar")

            status_label.config(text=f"✅ {tool_name} launched successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            status_label.config(text=f"❌ Failed to launch {tool_name}")

        finally:
            set_loading(False)

    threading.Thread(target=task).start()


def set_loading(is_loading, tool_name=""):
    if is_loading:
        progress["value"] = 0
        progress.config(style="Custom.Horizontal.TProgressbar")

        status_label.config(text=f"⏳ Launching {tool_name}...")
        for btn in button_widgets:
            btn.config(state="disabled")
    else:
        for btn in button_widgets:
            btn.config(state="normal")

def open_excel(path):
    if not os.path.exists(path):
        messagebox.showerror("Error", f"Path not found:\n{path}")
        return

    try:
        os.startfile(path)
    except Exception as e:
        messagebox.showerror("Error", str(e))
        
def open_folder(path):
    if not os.path.exists(path):
        messagebox.showerror("Error", f"Folder not found:\n{path}")
        return

    os.startfile(path)        


# GUI setup
root = tk.Tk()
root.title("🚀 Python Tools Launcher")
root.geometry("600x480")
root.configure(bg="#0f172a")

root.eval('tk::PlaceWindow . center')

# Style
style = ttk.Style()
style.theme_use("clam")

# Button style
style.configure("Custom.TButton",
                font=("Segoe UI", 12, "bold"),
                padding=12,
                background="#1f2937",
                foreground="white")

# Progress bar styles
style.configure("Custom.Horizontal.TProgressbar",
                troughcolor="#1f2937",
                background="#3b82f6",  # blue
                thickness=10)

style.configure("Green.Horizontal.TProgressbar",
                troughcolor="#1f2937",
                background="#22c55e",  # green
                thickness=10)

# Main frame
main_frame = tk.Frame(root, bg="#111827")
main_frame.pack(padx=20, pady=20, fill="both", expand=True)

# Canvas (scroll area)
canvas = tk.Canvas(main_frame, bg="#111827", highlightthickness=0)
scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)

scrollable_frame = tk.Frame(canvas, bg="#111827")

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Buttons
tools = [
    ("📦 Run ITP Load Tool", ITP_LOAD_PATH, ITP_EXCEL, ITP_FOLDER),
    ("🔄 Run PLM Load Tool", PLM_LOAD_PATH, PLM_EXCEL, PLM_FOLDER),
    ("📊 Run Volumetrics Tool", VOLUMETRICS_PATH, VOLUMETRICS_EXCEL, VOLUMETRICS_FOLDER),
    ("✅ Run PLM SAP Check Tool", PLM_SAP_CHECK_PATH, PLM_SAP_EXCEL, PLM_SAP_FOLDER),
    ("🆕 Run NFG Creation Tool", NFG_TOOL_PATH, NFG_EXCEL, NFG_FOLDER)
]

button_widgets = []

for text, script_path, excel_path, folder_path in tools:

    row_frame = tk.Frame(scrollable_frame, bg="#111827")
    row_frame.pack(fill="x", pady=8, padx=20)

    # Run tool button
    btn = ttk.Button(
        row_frame,
        text=text,
        style="Custom.TButton",
        command=lambda p=script_path, t=text: run_script(p, t)
    )
    btn.pack(side="left", fill="x", expand=True)

    button_widgets.append(btn)

    # Excel button
    excel_btn = tk.Button(
        row_frame,
        text="📊 Data",
        font=("Segoe UI", 9, "bold"),
        bg="#2563eb",
        fg="white",
        relief="flat",
        padx=8,
        command=lambda p=excel_path: open_excel(p)
    )
    excel_btn.pack(side="left", padx=5)

    # Folder button
    folder_btn = tk.Button(
        row_frame,
        text="📁 Folder",
        font=("Segoe UI", 9, "bold"),
        bg="#10b981",
        fg="white",
        relief="flat",
        padx=8,
        command=lambda p=folder_path: open_folder(p)
    )
    folder_btn.pack(side="left", padx=5)

# Progress bar
progress = ttk.Progressbar(
    root,
    mode="determinate",
    length=300,
    style="Custom.Horizontal.TProgressbar"
)

progress.pack(side="bottom", fill="x", padx=20, pady=10)

# Status
status_label = tk.Label(
    root,
    text="Ready",
    bg="#0f172a",
    fg="#9ca3af",
    anchor="w"
)

status_label.pack(side="bottom", fill="x", padx=10, pady=5)

# Footer
tk.Label(root,
         text="© Your Tools Suite",
         bg="#0f172a",
         fg="#6b7280").pack(pady=10)

root.mainloop()