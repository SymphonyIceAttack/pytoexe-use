import tkinter as tk
from tkinter import messagebox, filedialog
import os
import datetime
import shutil
import glob

# Directory to store code versions
VERSIONS_DIR = "code_versions"
os.makedirs(VERSIONS_DIR, exist_ok=True)

# ---------------- SAVE CODE FUNCTION ----------------
def save_code():
    code = code_text.get("1.0", tk.END)
    # Syntax check
    try:
        compile(code, "<string>", "exec")
    except SyntaxError as e:
        messagebox.showerror("Syntax Error", str(e))
        return

    # Backup current file
    if current_file.get().strip():
        src_file = current_file.get().strip()
        if os.path.exists(src_file):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(VERSIONS_DIR, f"{os.path.basename(src_file)}_{timestamp}.py")
            shutil.copy(src_file, backup_file)

    # Save new code
    file = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py")])
    if file:
        with open(file, "w", encoding="utf-8") as f:
            f.write(code)
        messagebox.showinfo("Saved", f"Code saved successfully:\n{file}")
        load_versions()

# ---------------- LOAD VERSION ----------------
def load_version():
    sel = version_listbox.curselection()
    if not sel:
        return
    file = version_listbox.get(sel)
    with open(os.path.join(VERSIONS_DIR, file), "r", encoding="utf-8") as f:
        code_text.delete("1.0", tk.END)
        code_text.insert(tk.END, f.read())

# ---------------- RESTORE LAST GOOD ----------------
def restore_last_good():
    files = sorted(glob.glob(os.path.join(VERSIONS_DIR, "*.py")), reverse=True)
    if not files:
        messagebox.showinfo("Info", "No previous versions found")
        return
    last_good = files[0]
    with open(last_good, "r", encoding="utf-8") as f:
        code_text.delete("1.0", tk.END)
        code_text.insert(tk.END, f.read())
    messagebox.showinfo("Restored", f"Last good version loaded: {os.path.basename(last_good)}")

# ---------------- LOAD VERSIONS ----------------
def load_versions():
    version_listbox.delete(0, tk.END)
    files = sorted(os.listdir(VERSIONS_DIR), reverse=True)
    for file in files:
        version_listbox.insert(tk.END, file)

# ---------------- LOAD EXISTING CODE ----------------
def load_existing_code():
    file = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
    if file:
        current_file.set(file)
        with open(file, "r", encoding="utf-8") as f:
            code_text.delete("1.0", tk.END)
            code_text.insert(tk.END, f.read())

# ---------------- MAIN UI ----------------
root = tk.Tk()
root.title("Python Code Modifier")
root.geometry("1000x700")

# Current file
current_file = tk.StringVar()
file_frame = tk.Frame(root)
file_frame.pack(fill="x", padx=10, pady=5)
tk.Label(file_frame, text="Current File:").pack(side="left")
tk.Entry(file_frame, textvariable=current_file, width=60).pack(side="left", padx=5)
tk.Button(file_frame, text="Load Existing Code", command=load_existing_code, bg="blue", fg="white").pack(side="left", padx=5)

# Code Text Area
code_text = tk.Text(root, font=("Consolas", 12))
code_text.pack(fill="both", expand=True, padx=10, pady=5)

# Bottom Frame with buttons
bottom_frame = tk.Frame(root)
bottom_frame.pack(fill="x", padx=10, pady=5)

tk.Button(bottom_frame, text="Apply & Save Code", command=save_code, bg="green", fg="white", font=("Arial",12,"bold")).pack(side="left", padx=5)
tk.Button(bottom_frame, text="Restore Last Good Version", command=restore_last_good, bg="red", fg="white", font=("Arial",12,"bold")).pack(side="left", padx=5)

# Version list
version_frame = tk.Frame(root)
version_frame.pack(side="right", fill="y", padx=10, pady=5)
tk.Label(version_frame, text="Previous Versions", font=("Arial", 12, "bold")).pack()
version_listbox = tk.Listbox(version_frame, width=40)
version_listbox.pack(fill="y", expand=True)
tk.Button(version_frame, text="Load Selected Version", command=load_version, bg="blue", fg="white").pack(pady=5)

load_versions()
root.mainloop()
