import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xml.etree.ElementTree as ET

# ---------- Helpers ----------

MEDIA_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv",
    ".png", ".jpg", ".jpeg", ".bmp", ".gif",
    ".mp3", ".wav", ".aiff", ".flac"
}

def is_media_file(path):
    ext = os.path.splitext(path)[1].lower()
    return ext in MEDIA_EXTENSIONS

def extract_paths(tree):
    results = []

    for elem in tree.iter():
        for attr, value in elem.attrib.items():
            if not value.strip():
                continue

            # Smarter filtering
            if ("file" in attr.lower() or "path" in attr.lower()) and is_media_file(value):
                results.append((elem, attr, value))

    return results


# ---------- Core Logic ----------

def load_files():
    paths = filedialog.askopenfilenames(
        title="Select GLMixer Files",
        filetypes=[("GLMixer Files", "*.glm")]
    )
    file_list_var.set(list(paths))
    update_file_listbox()

def select_folder():
    folder = filedialog.askdirectory(title="Select New Media Folder")
    folder_var.set(folder)

def update_file_listbox():
    listbox_files.delete(0, tk.END)
    for f in file_list_var.get():
        listbox_files.insert(tk.END, f)

def preview_changes():
    preview_tree.delete(*preview_tree.get_children())

    new_folder = folder_var.get()
    if not new_folder:
        messagebox.showerror("Error", "Select a folder first.")
        return

    total = 0

    for file_path in file_list_var.get():
        try:
            tree = ET.parse(file_path)
            paths = extract_paths(tree)

            for elem, attr, old_path in paths:
                filename = os.path.basename(old_path)
                new_path = os.path.join(new_folder, filename)

                exists = os.path.exists(new_path)

                preview_tree.insert(
                    "",
                    "end",
                    values=(os.path.basename(file_path), old_path, new_path, "✔" if exists else "❌")
                )
                total += 1

        except Exception as e:
            messagebox.showerror("Error", f"{file_path}\n{e}")
            return

    status_var.set(f"Preview loaded: {total} paths found")

def apply_changes():
    new_folder = folder_var.get()
    if not new_folder:
        messagebox.showerror("Error", "Select a folder first.")
        return

    confirm = messagebox.askyesno("Confirm", "Apply changes to all files?")
    if not confirm:
        return

    updated_files = 0
    total_changes = 0

    for file_path in file_list_var.get():
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            changes = 0

            for elem, attr, old_path in extract_paths(tree):
                filename = os.path.basename(old_path)
                new_path = os.path.join(new_folder, filename)

                elem.attrib[attr] = new_path
                changes += 1

            if changes > 0:
                new_file = os.path.splitext(file_path)[0] + "_updated.glm"
                tree.write(new_file, encoding="utf-8", xml_declaration=True)

                updated_files += 1
                total_changes += changes

        except Exception as e:
            messagebox.showerror("Error", f"{file_path}\n{e}")
            return

    messagebox.showinfo(
        "Done",
        f"{updated_files} files updated\n{total_changes} paths changed"
    )


# ---------- UI ----------

root = tk.Tk()
root.title("GLMixer Path Fixer Pro")
root.geometry("900x500")

file_list_var = tk.Variable(value=[])
folder_var = tk.StringVar()
status_var = tk.StringVar(value="Ready")

# Top controls
frame_top = tk.Frame(root)
frame_top.pack(fill="x", padx=10, pady=5)

tk.Button(frame_top, text="Add .glm Files", command=load_files).pack(side="left")
tk.Button(frame_top, text="Select Folder", command=select_folder).pack(side="left", padx=5)

tk.Entry(frame_top, textvariable=folder_var, width=50).pack(side="left", padx=5)

# File list
listbox_files = tk.Listbox(root, height=5)
listbox_files.pack(fill="x", padx=10, pady=5)

# Preview table
columns = ("File", "Old Path", "New Path", "Exists")
preview_tree = ttk.Treeview(root, columns=columns, show="headings")

for col in columns:
    preview_tree.heading(col, text=col)
    preview_tree.column(col, anchor="w", width=200)

preview_tree.pack(fill="both", expand=True, padx=10, pady=5)

# Buttons
frame_bottom = tk.Frame(root)
frame_bottom.pack(fill="x", padx=10, pady=5)

tk.Button(frame_bottom, text="Preview", command=preview_changes, bg="blue", fg="white").pack(side="left")
tk.Button(frame_bottom, text="Apply Changes", command=apply_changes, bg="green", fg="white").pack(side="left", padx=5)

tk.Label(frame_bottom, textvariable=status_var).pack(side="right")

root.mainloop()