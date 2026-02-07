
import os
from tkinter import Tk, Label, Entry, Text, Button, filedialog, StringVar, END, messagebox

def pilih_folder():
    folder = filedialog.askdirectory()
    folder_var.set(folder)

def preview():
    folder = folder_var.get()
    prefix = prefix_var.get()
    names = text_names.get("1.0", END).strip().splitlines()

    if not folder or not os.path.isdir(folder):
        messagebox.showerror("Error", "Pilih folder foto yang valid.")
        return

    files = sorted([f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    if not files:
        messagebox.showinfo("Info", "Tidak ada foto di folder.")
        return

    preview_text.delete("1.0", END)
    idx = 0
    for name in names:
        count = 1
        while idx < len(files):
            old = files[idx]
            new = f"{prefix}{name}_{count:03d}{os.path.splitext(old)[1]}"
            preview_text.insert(END, f"{old}  ->  {new}\n")
            idx += 1
            count += 1
            break

def jalankan():
    folder = folder_var.get()
    prefix = prefix_var.get()
    names = text_names.get("1.0", END).strip().splitlines()

    if not folder or not os.path.isdir(folder):
        messagebox.showerror("Error", "Pilih folder foto yang valid.")
        return

    files = sorted([f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    if not files:
        messagebox.showinfo("Info", "Tidak ada foto di folder.")
        return

    idx = 0
    success = 0
    for name in names:
        count = 1
        while idx < len(files):
            old = files[idx]
            old_path = os.path.join(folder, old)
            new_name = f"{prefix}{name}_{count:03d}{os.path.splitext(old)[1]}"
            new_path = os.path.join(folder, new_name)
            try:
                os.rename(old_path, new_path)
                success += 1
            except Exception as e:
                messagebox.showerror("Error", f"Gagal rename {old}: {e}")
                return
            idx += 1
            count += 1
            break

    messagebox.showinfo("Selesai", f"Berhasil rename {success} file.")

root = Tk()
root.title("D-STUDIO Sortir Foto")

Label(root, text="Folder Foto:").grid(row=0, column=0, sticky="w")
folder_var = StringVar()
Entry(root, textvariable=folder_var, width=40).grid(row=0, column=1)
Button(root, text="Pilih Folder", command=pilih_folder).grid(row=0, column=2)

Label(root, text="Awalan Nama File:").grid(row=1, column=0, sticky="w")
prefix_var = StringVar(value="D-STUDIO_")
Entry(root, textvariable=prefix_var, width=40).grid(row=1, column=1)

Label(root, text="Daftar Nama (satu baris satu nama):").grid(row=2, column=0, sticky="w")
text_names = Text(root, width=50, height=8)
text_names.grid(row=3, column=0, columnspan=3)

Button(root, text="Preview", command=preview).grid(row=4, column=0)
Button(root, text="Jalankan", command=jalankan).grid(row=4, column=1)

Label(root, text="Preview Hasil:").grid(row=5, column=0, sticky="w")
preview_text = Text(root, width=70, height=8)
preview_text.grid(row=6, column=0, columnspan=3)

root.mainloop()
