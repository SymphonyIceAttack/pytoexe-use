import subprocess
import re
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

VIDEO_EXTENSIONS = [".mkv", ".mp4", ".avi"]
EPISODE_REGEX = re.compile(r"S(\d{1,2})E(\d{1,2})", re.IGNORECASE)

def sizeof_fmt(num):
    for unit in ["B","KB","MB","GB","TB"]:
        if num < 1024:
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} PB"

def build_tree(path, prefix=""):
    entries = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
    lines = []
    for i, entry in enumerate(entries):
        connector = "+-- " if i == len(entries) - 1 else "+-- "
        lines.append(prefix + connector + entry.name)
        if entry.is_dir():
            extension = "    " if i == len(entries) - 1 else "�   "
            lines.extend(build_tree(entry, prefix + extension))
    return lines

def mediainfo(file):
    try:
        return subprocess.check_output(
            ["mediainfo", file],
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8"
        )
    except:
        return "MediaInfo non disponible"

def generate(folder):
    videos = [f for f in folder.rglob("*") if f.suffix.lower() in VIDEO_EXTENSIONS]
    if not videos:
        messagebox.showerror("Erreur", "Aucun fichier vid�o d�tect�.")
        return

    total_size = sum(f.stat().st_size for f in videos)
    seasons = set()
    episodes = []

    for v in videos:
        match = EPISODE_REGEX.search(v.name)
        if match:
            seasons.add(int(match.group(1)))
            episodes.append(match.group(0).upper())

    seasons_sorted = sorted(seasons)

    bbcode = []
    bbcode.append("[b][u]?? S�RIE � PACK COMPLET[/u][/b]\n")
    bbcode.append(f"{folder.name}\n\n")

    bbcode.append("[b][u]?? CONTENU[/u][/b]\n")
    bbcode.append("[code]\n")
    bbcode.append(folder.name + "/\n")
    bbcode.extend(line + "\n" for line in build_tree(folder))
    bbcode.append("[/code]\n\n")

    bbcode.append("[b][u]?? INFORMATIONS G�N�RALES[/u][/b]\n")
    bbcode.append(f"- Saisons incluses : S{seasons_sorted[0]:02d} � S{seasons_sorted[-1]:02d}\n")
    bbcode.append(f"- Nombre total d��pisodes : {len(episodes)}\n")
    bbcode.append(f"- Taille totale : {sizeof_fmt(total_size)}\n\n")

    bbcode.append("[b][u]?? MEDIAINFO (�pisode exemple)[/u][/b]\n")
    bbcode.append("[code]\n")
    bbcode.append(mediainfo(str(videos[0])))
    bbcode.append("\n[/code]\n\n")

    bbcode.append("[b][u]??? CAPTURES D��CRAN[/u][/b]\n")
    bbcode.append(
        "[img]LIEN_IMAGE_1[/img]\n"
        "[img]LIEN_IMAGE_2[/img]\n"
        "[img]LIEN_IMAGE_3[/img]\n\n"
    )

    bbcode.append("[b][u]?? DESCRIPTION[/u][/b]\n")
    bbcode.append(
        "Pack complet des saisons 1 � 9.\n"
        "Qualit� homog�ne sur l�ensemble des �pisodes.\n"
        "Aucun logo, aucun watermark.\n"
        "Compatible PC / TV / Plex.\n"
        "Merci pour le seed ??\n"
    )

    output_file = folder / "presentation_sharewood_bbcode_S01_S09.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(bbcode)

    messagebox.showinfo("Termin�", f"Pr�sentation g�n�r�e :\n{output_file}")

def browse_folder():
    path = filedialog.askdirectory()
    if path:
        generate(Path(path))

def drop_folder(event):
    folder_path = event.data
    if folder_path:
        generate(Path(folder_path))

root = tk.Tk()
root.title("G�n�rateur Sharewood � Pack S01 � S09")
root.geometry("520x180")
root.resizable(False, False)

tk.Label(root, text="Glisser-d�poser le dossier de la s�rie ici ou cliquer sur Parcourir :", font=("Segoe UI", 10)).pack(pady=10)

browse_btn = tk.Button(root, text="?? Parcourir", command=lambda: browse_folder(), width=20)
browse_btn.pack(pady=5)

tk.Label(root, text="Ou glisser-d�poser le dossier sur cette fen�tre :", font=("Segoe UI", 9)).pack(pady=10)

# Gestion simple du drag & drop
try:
    import tkinterdnd2 as tkdnd
    root = tkdnd.TkinterDnD.Tk()
    root.drop_target_register('*')
    root.dnd_bind('<<Drop>>', drop_folder)
except:
    pass  # Glisser-d�poser non activ�, mais bouton fonctionne

root.mainloop()

