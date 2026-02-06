import tkinter as tk
from tkinter import filedialog, messagebox
import shutil
import os
import json

# ======================
# پوشه فایل‌ها
# ======================
FILES_FOLDER = "files"
os.makedirs(FILES_FOLDER, exist_ok=True)

# فایل ذخیره دانلودها
DOWNLOAD_LOG = "downloads.json"

# ======================
# رنگ‌ها و استایل
# ======================
BG = "#121212"
PANEL = "#1f1f1f"
ACCENT = "#00adee"
TEXT = "#ffffff"
SUBTEXT = "#aaaaaa"
CARD = "#181818"
HOVER = "#00cfff"

# ======================
# توابع اصلی
# ======================
def load_files():
    listbox.delete(0, tk.END)
    for f in os.listdir(FILES_FOLDER):
        listbox.insert(tk.END, f)

def search():
    key = search_entry.get().lower()
    listbox.delete(0, tk.END)
    for f in os.listdir(FILES_FOLDER):
        if key in f.lower():
            listbox.insert(tk.END, f)

def download():
    sel = listbox.curselection()
    if not sel:
        messagebox.showwarning("Warning", "Please select a file")
        return

    file_name = listbox.get(sel)
    folder = filedialog.askdirectory(title="Select download location")
    if not folder:
        return

    src = os.path.join(FILES_FOLDER, file_name)
    dst = os.path.join(folder, file_name)
    shutil.copy(src, dst)

    # ذخیره مسیر دانلود در فایل json
    if os.path.exists(DOWNLOAD_LOG):
        with open(DOWNLOAD_LOG, "r") as f:
            downloaded_files = json.load(f)
    else:
        downloaded_files = []

    downloaded_files.append(dst)

    with open(DOWNLOAD_LOG, "w") as f:
        json.dump(downloaded_files, f)

    messagebox.showinfo("Success", f"{file_name} downloaded successfully")

def show_library():
    load_files()
    info_label.config(text="Library")

def show_downloads():
    listbox.delete(0, tk.END)
    info_label.config(text="Downloads")
    if os.path.exists(DOWNLOAD_LOG):
        with open(DOWNLOAD_LOG, "r") as f:
            downloaded_files = json.load(f)
        for f in downloaded_files:
            listbox.insert(tk.END, f)

def show_about():
    listbox.delete(0, tk.END)
    info_label.config(text="About Us")
    listbox.insert(tk.END, "This program was developed by ASSASIN Group")

# ======================
# پنجره اصلی
# ======================
root = tk.Tk()
root.title("ASSASIN Launcher")
root.geometry("1100x650")
root.resizable(False, False)
root.config(bg=BG)

# ======================
# Header
# ======================
header = tk.Frame(root, bg=PANEL, height=70)
header.pack(fill="x")
logo = tk.Label(header, text="ASSASIN", font=("Arial Black", 22), bg=PANEL, fg=ACCENT)
logo.pack(side="left", padx=25)
title = tk.Label(header, text="Game Launcher", font=("Arial", 14), bg=PANEL, fg=SUBTEXT)
title.pack(side="left")

# ======================
# Sidebar
# ======================
sidebar = tk.Frame(root, bg=PANEL, width=220)
sidebar.pack(side="left", fill="y")

menu1 = tk.Button(sidebar, text="🏠  Library", font=("Arial", 14), bg=PANEL, fg=TEXT, bd=0,
                  activebackground=ACCENT, activeforeground=BG, command=show_library)
menu1.pack(anchor="w", padx=25, pady=15)

menu2 = tk.Button(sidebar, text="⬇️  Downloads", font=("Arial", 14), bg=PANEL, fg=SUBTEXT, bd=0,
                  activebackground=ACCENT, activeforeground=BG, command=show_downloads)
menu2.pack(anchor="w", padx=25)

menu3 = tk.Button(sidebar, text="ℹ️  About Us", font=("Arial", 14), bg=PANEL, fg=SUBTEXT, bd=0,
                  activebackground=ACCENT, activeforeground=BG, command=show_about)
menu3.pack(anchor="w", padx=25, pady=15)

# ======================
# Main area
# ======================
main = tk.Frame(root, bg=BG)
main.pack(side="right", fill="both", expand=True)

info_label = tk.Label(main, text="Library", font=("Arial", 14), bg=BG, fg=SUBTEXT)
info_label.pack(pady=10)

# Search
search_frame = tk.Frame(main, bg=BG)
search_frame.pack(pady=10)

search_entry = tk.Entry(search_frame, width=40, font=("Arial", 13), bg=CARD, fg=TEXT, insertbackground=TEXT, bd=0)
search_entry.pack(side="left", ipady=6)

search_btn = tk.Button(search_frame, text="Search", font=("Arial Black", 11), bg=ACCENT, fg="black", width=10, bd=0, command=search)
search_btn.pack(side="left", padx=10)

# Listbox
list_frame = tk.Frame(main, bg=BG)
list_frame.pack(pady=10)

listbox = tk.Listbox(list_frame, width=65, height=18, font=("Consolas", 13), bg=CARD, fg=TEXT,
                     selectbackground=ACCENT, selectforeground="black", bd=0, highlightthickness=0)
listbox.pack()

# Download button
download_btn = tk.Button(main, text="DOWNLOAD", font=("Arial Black", 16), bg=ACCENT, fg="black", width=22, height=2, bd=0, command=download)
download_btn.pack(pady=25)

# ======================
# Hover effect
# ======================
def hover_on(e):
    e.widget["bg"] = HOVER
def hover_off(e):
    e.widget["bg"] = ACCENT

download_btn.bind("<Enter>", hover_on)
download_btn.bind("<Leave>", hover_off)
search_btn.bind("<Enter>", hover_on)
search_btn.bind("<Leave>", hover_off)

# ======================
# Load initial files
# ======================
load_files()

root.mainloop()
