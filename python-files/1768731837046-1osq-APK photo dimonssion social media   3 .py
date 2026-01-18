from PIL import Image, ImageDraw, ImageFont, ImageTk
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, font as tkFont

CONFIG_FILE = "config.txt"
selected_files = []
paused = False

# ---------- CONFIG ----------
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = f.read().split("|")
            if len(data) == 2:
                return data[0], data[1]
    return "", ""

def save_config(import_dir, export_dir):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(f"{import_dir}|{export_dir}")

last_import_dir, last_export_dir = load_config()

# ---------- FONCTIONS ----------
def import_photos():
    global selected_files, last_import_dir
    files = filedialog.askopenfilenames(
        title="Importer images",
        initialdir=last_import_dir if last_import_dir else None,
        filetypes=[("Images", "*.jpg *.jpeg *.png *.heic")]
    )
    if files:
        selected_files = files
        last_import_dir = os.path.dirname(files[0])
        save_config(last_import_dir, output_folder_var.get())
        lbl_files.config(text=f"{len(files)} images sélectionnées")
        update_preview()

def choose_output_folder():
    global last_export_dir
    folder = filedialog.askdirectory(
        title="Choisir dossier de sortie",
        initialdir=last_export_dir if last_export_dir else None
    )
    if folder:
        output_folder_var.set(folder)
        last_export_dir = folder
        save_config(last_import_dir, last_export_dir)

def choose_logo():
    file = filedialog.askopenfilename(
        title="Choisir un logo",
        filetypes=[("Images", "*.png *.jpg *.jpeg")]
    )
    if file:
        logo_var.set(file)
        update_preview()

def toggle_pause():
    global paused
    paused = not paused
    btn_pause.config(text="▶ Reprendre" if paused else "⏸ Pause")

def choose_font():
    available_fonts = sorted(tkFont.families())
    font_window = tk.Toplevel(root)
    font_window.title("Choisir une police")
    font_window.geometry("300x400")
    font_listbox = tk.Listbox(font_window)
    font_listbox.pack(fill="both", expand=True)
    for f in available_fonts:
        font_listbox.insert("end", f)

    def set_font():
        if font_listbox.curselection():
            selected = font_listbox.get(font_listbox.curselection())
            font_var.set(selected)
            update_preview()
            font_window.destroy()

    tk.Button(font_window, text="Sélectionner", command=set_font).pack(pady=5)

# ---------- EXPORT ----------
def resize_and_export():
    global paused
    if not selected_files:
        messagebox.showwarning("Erreur", "Aucune image sélectionnée")
        return

    output_base = output_folder_var.get()
    if not output_base:
        messagebox.showwarning("Erreur", "Choisir un dossier de sortie")
        return

    presets = {
        "Instagram Post 1080x1080": (1080, 1080),
        "Instagram Vertical 1080x1350": (1080, 1350),
        "Story / TikTok 1080x1920": (1080, 1920),
        "Facebook 1200x630": (1200, 630)
    }

    if size_var.get() == "Personnalisée":
        try:
            target_w = int(custom_w.get())
            target_h = int(custom_h.get())
        except:
            messagebox.showerror("Erreur", "Dimensions invalides")
            return
    else:
        target_w, target_h = presets[size_var.get()]

    export_folder = os.path.join(output_base, "export_JPEG")
    os.makedirs(export_folder, exist_ok=True)

    text = watermark_var.get()
    logo_path = logo_var.get()
    try:
        font = ImageFont.truetype(font_var.get(), int(font_size_var.get()))
    except:
        font = ImageFont.load_default()

    progress_bar["maximum"] = len(selected_files)
    progress_bar["value"] = 0
    lbl_progress.config(text="0 %")

    for i, path in enumerate(selected_files, start=1):
        while paused:
            root.update()

        try:
            img = Image.open(path).convert("RGBA")
        except:
            continue

        # Redimension selon preset
        iw, ih = img.size
        ratio = max(target_w / iw, target_h / ih)
        img = img.resize((int(iw * ratio), int(ih * ratio)), Image.LANCZOS)
        left = (img.width - target_w) // 2
        top = (img.height - target_h) // 2
        img = img.crop((left, top, left + target_w, top + target_h))

        draw = ImageDraw.Draw(img)

        # TEXTE + police + taille + position appliqué comme aperçu
        if text:
            draw.text((text_x.get(), text_y.get()), text, font=font, fill=(255,255,255,255))

        # LOGO superposé comme aperçu
        if logo_path and os.path.exists(logo_path):
            try:
                logo_img = Image.open(logo_path).convert("RGBA")
                lw, lh = logo_img.size
                logo_img = logo_img.resize((int(lw*logo_scale.get()), int(lh*logo_scale.get())), Image.LANCZOS)
                temp_layer = Image.new("RGBA", img.size)
                temp_layer.paste(logo_img, (logo_x.get(), logo_y.get()), logo_img)
                img = Image.alpha_composite(img, temp_layer)
            except Exception as e:
                print("Erreur logo:", e)

        # Export JPEG
        img_final = img.convert("RGB")
        save_path = os.path.join(export_folder, os.path.splitext(os.path.basename(path))[0] + ".jpg")
        img_final.save(save_path, "JPEG", quality=100, subsampling=0)

        progress_bar["value"] = i
        lbl_progress.config(text=f"{int(i/len(selected_files)*100)} %")
        root.update()

    messagebox.showinfo("Terminé", "Toutes les images exportées ✔")

# ---------- APERÇU ----------
def update_preview(*args):
    if not selected_files:
        return
    path = selected_files[0]
    img = Image.open(path).convert("RGBA")
    preview_img = img.copy()
    preview_img.thumbnail((400, 400))

    draw = ImageDraw.Draw(preview_img)
    try:
        font = ImageFont.truetype(font_var.get(), int(font_size_var.get()))
    except:
        font = ImageFont.load_default()

    # Texte
    if watermark_var.get():
        draw.text((text_x.get(), text_y.get()), watermark_var.get(), font=font, fill=(255,255,255,255))

    # Logo
    if logo_var.get() and os.path.exists(logo_var.get()):
        try:
            logo_img = Image.open(logo_var.get()).convert("RGBA")
            lw, lh = logo_img.size
            logo_img = logo_img.resize((int(lw*logo_scale.get()), int(lh*logo_scale.get())), Image.LANCZOS)
            temp_layer = Image.new("RGBA", preview_img.size)
            temp_layer.paste(logo_img, (logo_x.get(), logo_y.get()), logo_img)
            preview_img = Image.alpha_composite(preview_img, temp_layer)
        except Exception as e:
            print("Erreur logo aperçu:", e)

    lbl_preview.image = ImageTk.PhotoImage(preview_img)
    lbl_preview.config(image=lbl_preview.image)

# ---------- INTERFACE ----------
root = tk.Tk()
root.title("✨ Convertisseur HD JPEG + Logo ✨")
root.geometry("720x950")
root.configure(bg="#2E3440")

button_bg = "#5E81AC"
button_fg = "#ffffff"
frame_bg = "#3B4252"
label_fg = "#ffffff"
scale_trough = "#4C566A"

def create_label(frame, text):
    return tk.Label(frame, text=text, bg=frame_bg, fg=label_fg, font=("Arial", 11, "bold"))

# Frames
frame_top = tk.Frame(root, bg=frame_bg)
frame_top.pack(fill="x", padx=15, pady=10)
frame_controls = tk.Frame(frame_top, bg=frame_bg)
frame_controls.pack(side="left", fill="y")

# Import / Output
frame_import = tk.LabelFrame(frame_controls, text="Importer Images", bg=frame_bg, fg=label_fg, padx=10, pady=10)
frame_import.pack(fill="x", pady=5)
tk.Button(frame_import, text="📂 Choisir images", command=import_photos, bg=button_bg, fg=button_fg).pack(side="left")
lbl_files = tk.Label(frame_import, text="Aucune image", bg=frame_bg, fg=label_fg)
lbl_files.pack(side="left", padx=5)

frame_out = tk.LabelFrame(frame_controls, text="Dossier de sortie", bg=frame_bg, fg=label_fg, padx=10, pady=10)
frame_out.pack(fill="x", pady=5)
output_folder_var = tk.StringVar(value=last_export_dir)
tk.Button(frame_out, text="📁 Choisir dossier", command=choose_output_folder, bg=button_bg, fg=button_fg).pack(side="left")
tk.Label(frame_out, textvariable=output_folder_var, bg=frame_bg, fg=label_fg).pack(side="left", padx=5)

# Taille / Texte / Logo
frame_size = tk.LabelFrame(frame_controls, text="Dimensions", bg=frame_bg, fg=label_fg, padx=10, pady=10)
frame_size.pack(fill="x", pady=5)
size_var = tk.StringVar(value="Instagram Post 1080x1080")
tk.OptionMenu(frame_size, size_var, "Instagram Post 1080x1080", "Instagram Vertical 1080x1350", "Story / TikTok 1080x1920", "Facebook 1200x630", "Personnalisée").pack(side="left", padx=5)
custom_w = tk.StringVar(value="1080")
custom_h = tk.StringVar(value="1080")
create_label(frame_size, "L").pack(side="left")
tk.Entry(frame_size, textvariable=custom_w, width=6).pack(side="left", padx=2)
create_label(frame_size, "H").pack(side="left")
tk.Entry(frame_size, textvariable=custom_h, width=6).pack(side="left", padx=2)

frame_logo = tk.LabelFrame(frame_controls, text="Texte / Logo", bg=frame_bg, fg=label_fg, padx=10, pady=10)
frame_logo.pack(fill="x", pady=5)
watermark_var = tk.StringVar()
tk.Entry(frame_logo, textvariable=watermark_var, width=30).grid(row=0, column=1, padx=5)
tk.Label(frame_logo, text="Texte:", bg=frame_bg, fg=label_fg).grid(row=0, column=0, sticky="w")
font_size_var = tk.IntVar(value=40)
tk.Scale(frame_logo, from_=10, to=200, orient="horizontal", variable=font_size_var, bg=frame_bg, fg=label_fg, troughcolor=scale_trough, highlightthickness=0, command=lambda e:update_preview()).grid(row=1, column=1, sticky="we")
tk.Label(frame_logo, text="Taille texte:", bg=frame_bg, fg=label_fg).grid(row=1, column=0, sticky="w")
text_x = tk.IntVar(value=10)
tk.Scale(frame_logo, from_=0, to=2000, orient="horizontal", variable=text_x, bg=frame_bg, fg=label_fg, troughcolor=scale_trough, highlightthickness=0, command=lambda e:update_preview()).grid(row=2, column=1, sticky="we")
tk.Label(frame_logo, text="Texte X:", bg=frame_bg, fg=label_fg).grid(row=2, column=0, sticky="w")
text_y = tk.IntVar(value=10)
tk.Scale(frame_logo, from_=0, to=2000, orient="horizontal", variable=text_y, bg=frame_bg, fg=label_fg, troughcolor=scale_trough, highlightthickness=0, command=lambda e:update_preview()).grid(row=3, column=1, sticky="we")
tk.Label(frame_logo, text="Texte Y:", bg=frame_bg, fg=label_fg).grid(row=3, column=0, sticky="w")

# Choisir police
font_var = tk.StringVar(value="Arial")
tk.Button(frame_logo, text="🔤 Choisir police", command=choose_font, bg=button_bg, fg=button_fg).grid(row=8, column=0)
tk.Label(frame_logo, textvariable=font_var, bg=frame_bg, fg=label_fg).grid(row=8, column=1, sticky="w")

logo_var = tk.StringVar()
tk.Button(frame_logo, text="📌 Choisir logo", command=choose_logo, bg=button_bg, fg=button_fg).grid(row=4, column=0)
tk.Label(frame_logo, textvariable=logo_var, bg=frame_bg, fg=label_fg).grid(row=4, column=1, sticky="w")
logo_x = tk.IntVar(value=10)
tk.Scale(frame_logo, from_=0, to=2000, orient="horizontal", variable=logo_x, bg=frame_bg, fg=label_fg, troughcolor=scale_trough, highlightthickness=0, command=lambda e:update_preview()).grid(row=5, column=1, sticky="we")
tk.Label(frame_logo, text="Logo X:", bg=frame_bg, fg=label_fg).grid(row=5, column=0, sticky="w")
logo_y = tk.IntVar(value=10)
tk.Scale(frame_logo, from_=0, to=2000, orient="horizontal", variable=logo_y, bg=frame_bg, fg=label_fg, troughcolor=scale_trough, highlightthickness=0, command=lambda e:update_preview()).grid(row=6, column=1, sticky="we")
tk.Label(frame_logo, text="Logo Y:", bg=frame_bg, fg=label_fg).grid(row=6, column=0, sticky="w")
logo_scale = tk.DoubleVar(value=0.2)
tk.Scale(frame_logo, from_=0.05, to=1, resolution=0.01, orient="horizontal", variable=logo_scale, bg=frame_bg, fg=label_fg, troughcolor=scale_trough, highlightthickness=0, command=lambda e:update_preview()).grid(row=7, column=1, sticky="we")
tk.Label(frame_logo, text="Échelle logo:", bg=frame_bg, fg=label_fg).grid(row=7, column=0, sticky="w")

# Aperçu
frame_preview = tk.LabelFrame(frame_top, text="Aperçu en temps réel", bg=frame_bg, fg=label_fg, font=("Arial", 12, "bold"), padx=10, pady=10)
frame_preview.pack(side="right", padx=10, pady=5, fill="both", expand=True)
lbl_preview = tk.Label(frame_preview, bg=frame_bg)
lbl_preview.pack()

# Progression
frame_progress = tk.LabelFrame(root, text="Progression", bg=frame_bg, fg=label_fg, font=("Arial", 12, "bold"), padx=10, pady=10)
frame_progress.pack(fill="x", padx=15, pady=5)
progress_bar = ttk.Progressbar(frame_progress, length=650, mode="determinate")
progress_bar.pack(pady=5)
lbl_progress = tk.Label(frame_progress, text="0 %", bg=frame_bg, fg=label_fg, font=("Arial", 11))
lbl_progress.pack()

# Boutons Export / Pause
frame_buttons = tk.Frame(root, bg=frame_bg)
frame_buttons.pack(fill="x", padx=15, pady=10)
btn_export = tk.Button(frame_buttons, text="🚀 Exporter en JPEG HD", command=resize_and_export, bg=button_bg, fg=button_fg, font=("Arial", 12, "bold"))
btn_export.pack(side="left", padx=5)
btn_pause = tk.Button(frame_buttons, text="⏸ Pause", command=toggle_pause, bg=button_bg, fg=button_fg, font=("Arial", 12, "bold"))
btn_pause.pack(side="left", padx=5)

# Traces pour mise à jour aperçu
watermark_var.trace_add("write", lambda *e:update_preview())
logo_var.trace_add("write", lambda *e:update_preview())
font_var.trace_add("write", lambda *e:update_preview())
font_size_var.trace_add("write", lambda *e:update_preview())
text_x.trace_add("write", lambda *e:update_preview())
text_y.trace_add("write", lambda *e:update_preview())
logo_x.trace_add("write", lambda *e:update_preview())
logo_y.trace_add("write", lambda *e:update_preview())
logo_scale.trace_add("write", lambda *e:update_preview())

root.mainloop()
