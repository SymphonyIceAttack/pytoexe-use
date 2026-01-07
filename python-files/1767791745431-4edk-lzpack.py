import os
import zlib
import lzo
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ---------------- CONFIG ----------------
APP_TITLE = "Metin2 Auto Pack Sistemi"
THEME_COLOR = "#0d6efd"  # Mavi
# ---------------------------------------

def compress_to_lz(input_file, output_file):
    with open(input_file, "rb") as f:
        data = f.read()
    compressed = lzo.compress(data)
    with open(output_file, "wb") as f:
        f.write(compressed)

def crc32_hash(file_path):
    with open(file_path, "rb") as f:
        return format(zlib.crc32(f.read()) & 0xFFFFFFFF, "08X")

def select_pack_folder():
    folder = filedialog.askdirectory()
    pack_path.set(folder)

def select_crc_folder():
    folder = filedialog.askdirectory()
    crc_path.set(folder)

def start_pack():
    folder = pack_path.get()
    if not folder:
        messagebox.showerror("Hata", "Pack klasörü seçilmedi")
        return

    for file in os.listdir(folder):
        if file.endswith(".epk") or file.endswith(".eix"):
            full_path = os.path.join(folder, file)
            output = full_path + ".lz"
            compress_to_lz(full_path, output)
            log(f"{file} → {file}.lz")

    messagebox.showinfo("Tamamlandı", "Pack işlemi bitti")

def start_crc():
    folder = crc_path.get()
    if not folder:
        messagebox.showerror("Hata", "CRC klasörü seçilmedi")
        return

    crc_file = os.path.join(folder, "crclist.txt")
    with open(crc_file, "w") as out:
        for root, _, files in os.walk(folder):
            for file in files:
                if file == "crclist.txt":
                    continue
                full_path = os.path.join(root, file)
                crc = crc32_hash(full_path)
                relative = os.path.relpath(full_path, folder).replace("\\", "/")
                out.write(f"{relative} {crc}\n")
                log(f"CRC → {relative}")

    messagebox.showinfo("Tamamlandı", "crclist.txt oluşturuldu")

def log(text):
    log_box.insert(tk.END, text + "\n")
    log_box.see(tk.END)

# ---------------- UI ----------------
root = tk.Tk()
root.title(APP_TITLE)
root.geometry("700x500")
root.configure(bg=THEME_COLOR)

pack_path = tk.StringVar()
crc_path = tk.StringVar()

style = ttk.Style()
style.theme_use("default")
style.configure("TButton", font=("Segoe UI", 11))

frame = tk.Frame(root, bg=THEME_COLOR)
frame.pack(fill="both", expand=True, padx=20, pady=20)

tk.Label(frame, text="Metin2 Auto Pack Sistemi",
         font=("Segoe UI", 20, "bold"),
         bg=THEME_COLOR, fg="white").pack(pady=10)

ttk.Button(frame, text="Pack Klasörü Seç", command=select_pack_folder).pack(fill="x")
ttk.Button(frame, text="Pack → .lz Başlat", command=start_pack).pack(fill="x", pady=5)

ttk.Separator(frame).pack(fill="x", pady=10)

ttk.Button(frame, text="CRC Klasörü Seç", command=select_crc_folder).pack(fill="x")
ttk.Button(frame, text="CRC Hash Oluştur", command=start_crc).pack(fill="x", pady=5)

log_box = tk.Text(frame, height=12, bg="#0b5ed7", fg="white", font=("Consolas", 10))
log_box.pack(fill="both", expand=True, pady=10)

root.mainloop()
