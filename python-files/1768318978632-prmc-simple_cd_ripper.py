import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import winsound

# --- Ρυθμίσεις --- #
MAX_SPEED = 84  # Μέγιστη ταχύτητα
FAKE_TRACKS = 3  # placeholder για tracks (πραγματικό ripping χρειάζεται cdparanoia / cdda2wav)

# --- Functions --- #
def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        output_entry.delete(0, tk.END)
        output_entry.insert(0, folder)

def rip_cd():
    folder = output_entry.get()
    speed = int(speed_var.get())
    if not folder:
        messagebox.showwarning("Warning", "Διάλεξε φάκελο εξόδου!")
        return
    if speed < 1 or speed > MAX_SPEED:
        messagebox.showwarning("Warning", f"Διάλεξε ταχύτητα 1-{MAX_SPEED}!")
        return

    # Προσοχή: placeholder ripping
    messagebox.showinfo("Info", f"Ξεκινάει το ripping στα {speed}x ...")
    try:
        for i in range(1, FAKE_TRACKS + 1):
            file_path = os.path.join(folder, f"Track{i}.wav")
            with open(file_path, "wb") as f:
                f.write(b"FAKE WAV DATA")  # placeholder για πραγματικά WAV
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return

    winsound.Beep(1000, 500)
    messagebox.showinfo("Done", "Το ripping ολοκληρώθηκε!")

# --- GUI --- #
root = tk.Tk()
root.title("Simple CD Ripper")

# Background image
try:
    img = Image.open("feather.png")  # πρέπει να υπάρχει feather.png στον ίδιο φάκελο
    img = img.resize((400, 300), Image.ANTIALIAS)
    bg_img = ImageTk.PhotoImage(img)
    bg_label = tk.Label(root, image=bg_img)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
except:
    root.configure(bg="white")  # fallback

# Speed menu
tk.Label(root, text="Speed (1x-84x):").place(x=20, y=20)
speed_var = tk.IntVar(value=1)
speed_menu = tk.OptionMenu(root, speed_var, *range(1, MAX_SPEED + 1))
speed_menu.place(x=150, y=15)

# Output folder
tk.Label(root, text="Output Folder:").place(x=20, y=60)
output_entry = tk.Entry(root, width=25)
output_entry.place(x=150, y=60)
tk.Button(root, text="Browse", command=browse_folder).place(x=320, y=55)

# RIP button
tk.Button(root, text="RIP CD", command=rip_cd, bg="green", fg="white").place(x=150, y=120)

root.geometry("400x200")
root.mainloop()
