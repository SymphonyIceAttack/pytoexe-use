import os
import shutil
import time
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk

# ===============================
# CONFIGURATION (editable)
# ===============================

reference_folder = ""
unsorted_folder = ""
output_folder = ""
operation_mode = "move"  # default: "move" or "copy"

# ===============================
# HELPER FUNCTIONS
# ===============================

def log(msg):
    log_box.insert(tk.END, msg + "\n")
    log_box.see(tk.END)
    root.update_idletasks()

def choose_reference():
    global reference_folder
    reference_folder = filedialog.askdirectory()
    ref_entry.delete(0, tk.END)
    ref_entry.insert(0, reference_folder)

def choose_unsorted():
    global unsorted_folder
    unsorted_folder = filedialog.askdirectory()
    uns_entry.delete(0, tk.END)
    uns_entry.insert(0, unsorted_folder)

def choose_output():
    global output_folder
    output_folder = filedialog.askdirectory()
    out_entry.delete(0, tk.END)
    out_entry.insert(0, output_folder)

def get_all_reference_files(ref_path):
    files = []
    for root_dir, _, filenames in os.walk(ref_path):
        for f in filenames:
            files.append(Path(root_dir) / f)
    return files

def get_unique_destination(dest):
    if not dest.exists():
        return dest

    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent

    counter = 1
    while True:
        new_dest = parent / f"{stem}_{counter}{suffix}"
        if not new_dest.exists():
            return new_dest
        counter += 1

# ===============================
# MAIN ORGANIZATION LOGIC
# ===============================

def organize():
    start_time = time.time()

    ref = Path(reference_folder)
    unsorted = Path(unsorted_folder)
    out = Path(output_folder)

    ref_files = get_all_reference_files(ref)
    total = len(ref_files)

    progress["maximum"] = total
    processed = 0

    for file in ref_files:
        relative_path = file.relative_to(ref)
        filename = file.name

        source_file = unsorted / filename
        dest_folder = out / relative_path.parent
        dest_folder.mkdir(parents=True, exist_ok=True)

        if source_file.exists():
            dest_file = dest_folder / filename
            dest_file = get_unique_destination(dest_file)

            if operation_mode_var.get() == "move":
                shutil.move(str(source_file), str(dest_file))
                log(f"Moved: {filename} → {dest_file}")
            else:
                shutil.copy2(str(source_file), str(dest_file))
                log(f"Copied: {filename} → {dest_file}")
        else:
            log(f"Skipped (not found): {filename}")

        processed += 1
        progress["value"] = processed

        elapsed = time.time() - start_time
        rate = elapsed / processed if processed else 0
        remaining = rate * (total - processed)
        eta_label.config(text=f"ETA: {int(remaining)} sec")
        root.update_idletasks()

    total_time = time.time() - start_time
    log(f"\nFinished in {int(total_time)} seconds.")

def start_thread():
    t = threading.Thread(target=organize)
    t.start()

# ===============================
# GUI
# ===============================

root = tk.Tk()
root.title("Video Organizer")
root.geometry("750x550")

# Top frame for title + trademark
top_frame = tk.Frame(root)
top_frame.pack(fill="x", pady=5)

title_label = tk.Label(top_frame, text="Video Organizer", font=("Arial", 16, "bold"))
title_label.pack(side="left", padx=10)

trademark_label = tk.Label(top_frame, text="MADE BY JZL for Lubim ta", fg="gray", font=("Arial", 10))
trademark_label.pack(side="left", padx=20)

# Reference folder
tk.Label(root, text="Reference Folder").pack(anchor="w", padx=10)
frame1 = tk.Frame(root)
frame1.pack(fill="x", padx=10)
ref_entry = tk.Entry(frame1)
ref_entry.pack(side="left", fill="x", expand=True)
tk.Button(frame1, text="Browse", command=choose_reference).pack(side="right")

# Unsorted folder
tk.Label(root, text="Unsorted Folder").pack(anchor="w", padx=10)
frame2 = tk.Frame(root)
frame2.pack(fill="x", padx=10)
uns_entry = tk.Entry(frame2)
uns_entry.pack(side="left", fill="x", expand=True)
tk.Button(frame2, text="Browse", command=choose_unsorted).pack(side="right")

# Output folder
tk.Label(root, text="Output Folder").pack(anchor="w", padx=10)
frame3 = tk.Frame(root)
frame3.pack(fill="x", padx=10)
out_entry = tk.Entry(frame3)
out_entry.pack(side="left", fill="x", expand=True)
tk.Button(frame3, text="Browse", command=choose_output).pack(side="right")

# Operation mode (move or copy)
tk.Label(root, text="Operation Mode").pack(anchor="w", padx=10)
operation_mode_var = tk.StringVar(value="move")
frame_mode = tk.Frame(root)
frame_mode.pack(fill="x", padx=10)
tk.Radiobutton(frame_mode, text="Move (default)", variable=operation_mode_var, value="move").pack(side="left", padx=5)
tk.Radiobutton(frame_mode, text="Copy (keep unsorted intact)", variable=operation_mode_var, value="copy").pack(side="left", padx=5)

# Start button
tk.Button(root, text="Start Organizing", command=start_thread, height=2).pack(pady=10)

# Progress bar
progress = ttk.Progressbar(root, length=600)
progress.pack(pady=5)
eta_label = tk.Label(root, text="ETA: calculating...")
eta_label.pack()

# Log window
log_box = tk.Text(root, height=15)
log_box.pack(fill="both", expand=True, padx=10, pady=10)

root.mainloop()