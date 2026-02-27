#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ROM Playlist Manager GUI (Standard Tkinter)
-------------------------------------------

This app generates .m3u playlists for games in a folder,
automatically detecting multi-disc/multi-cartridge games based
on filename markers such as:

(Disc 1), (Disc A), [Disk 2], (CD C), (Cartridge 1), etc.

Features:
- Optional playlists for single-disc games
- Optional moving of processed game files into a subfolder
- Add prefix to playlist entries
- Filter files by extension
- Scrollable log window
- Fully standard library, compatible with online EXE builders

Cheat-sheet (how filenames are interpreted):

+----------------+----------------+----------------+---------------------------------------------+
| Example Marker | Multi-Disc?    | Base Filename  | Notes / Reasoning                           |
+----------------+----------------+----------------+---------------------------------------------+
| (Disc 1)       | ✅ Yes         | Filename       | Number after keyword in parentheses        |
| (Disc A)       | ✅ Yes         | Filename       | Letter A mapped to 1                        |
| [Disk 1]       | ✅ Yes         | Filename       | Number after keyword in square brackets    |
| [Disk B]       | ✅ Yes         | Filename       | Letter B mapped to 2                        |
| (CD 3)         | ✅ Yes         | Filename       | Number after keyword in parentheses        |
| (CD C)         | ✅ Yes         | Filename       | Letter C mapped to 3                        |
| [Cartridge 1]  | ✅ Yes         | Filename       | Number marker                               |
| (Cartridge A)  | ✅ Yes         | Filename       | Letter marker                               |
| (Disc 3]       | ✅ Yes         | Filename       | Mixed bracket accepted                       |
| (Disk B)       | ✅ Yes         | Filename       | Letter B in parentheses                      |
| (Cartridge Style)| ❌ No        | Filename       | No number/letter -> single-disc             |
| (USA)          | ❌ No         | Filename       | Keyword not present -> single-disc          |
| [Rev 1]        | ❌ No         | Filename       | Keyword not present -> single-disc          |
| Game.iso       | ❌ No         | Game.iso       | No marker -> single-disc                     |
| (Disc1)        | ✅ Yes         | Filename       | No space between keyword and number -> matched|
| [Disk A] Extra]| ✅ Yes         | Filename       | First valid bracket is captured; extra text ignored|
| Zelda.iso      | ❌ No         | Zelda.iso      | Single-disc, no marker                       |
+----------------+----------------+----------------+---------------------------------------------+
"""

import re
from pathlib import Path
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# --- Regex to detect multi-disc/cartridge markers (numbers or letters) ---
disc_token = re.compile(
    r"[\(\[]\s*(Disc|Disk|CD|Cartridge)\s*([0-9A-Z])\s*[\)\]]",
    re.IGNORECASE
)

# Map letters A-Z to numbers 1-26
letter_map = {chr(i): i - 64 for i in range(65, 91)}

# --- Clean filename helper ---
def clean_name(name: str) -> str:
    """Remove extra spaces and spaces before dots."""
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"\s+\.", ".", name)
    return name.strip()

# --- Main GUI App ---
class PlaylistGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ROM Playlist Manager")
        self.geometry("700x550")

        # Folder selection
        tk.Label(self, text="Select ROM folder:").pack(pady=(10,0))
        folder_frame = tk.Frame(self)
        folder_frame.pack(pady=5, fill="x", padx=10)
        self.folder_entry = tk.Entry(folder_frame)
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(folder_frame, text="Browse", command=self.browse_folder).pack(side="right", padx=5)

        # Prefix
        tk.Label(self, text="Prefix for playlist entries (optional):").pack(pady=(10,0))
        self.prefix_entry = tk.Entry(self)
        self.prefix_entry.pack(fill="x", padx=10)

        # Single-disc playlist checkbox
        self.single_disc_var = tk.IntVar(value=1)
        tk.Checkbutton(self, text="Create playlist for single-disc games", variable=self.single_disc_var).pack(pady=5)

        # Subfolder
        tk.Label(self, text="Move processed files to subfolder (optional):").pack(pady=(10,0))
        self.subfolder_entry = tk.Entry(self)
        self.subfolder_entry.pack(fill="x", padx=10)

        # Extensions filter
        tk.Label(self, text="Allowed extensions (comma separated, optional):").pack(pady=(10,0))
        self.ext_entry = tk.Entry(self)
        self.ext_entry.pack(fill="x", padx=10)

        # Run button
        tk.Button(self, text="Generate Playlists", command=self.run_process).pack(pady=10)

        # Log window
        self.log = scrolledtext.ScrolledText(self, height=12)
        self.log.pack(fill="both", expand=True, padx=10, pady=(5,10))
        self.log.configure(state="disabled")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)

    def log_msg(self, msg):
        self.log.configure(state="normal")
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.configure(state="disabled")

    def run_process(self):
        folder = self.folder_entry.get()
        if not folder:
            messagebox.showerror("Error", "Please select a folder.")
            return

        prefix = self.prefix_entry.get().strip()
        subfolder_name = self.subfolder_entry.get().strip()
        allowed_exts = [e.strip().lower() for e in self.ext_entry.get().split(",") if e.strip()]
        create_single = self.single_disc_var.get() == 1

        folder_path = Path(folder)
        if not folder_path.is_dir():
            messagebox.showerror("Error", "Folder does not exist.")
            return

        move_files = False
        if subfolder_name:
            target_dir = folder_path / subfolder_name
            target_dir.mkdir(exist_ok=True)
            move_files = True

        files = [p for p in folder_path.iterdir() if p.is_file()]
        groups = defaultdict(list)
        singles = []

        for p in files:
            if allowed_exts and p.suffix.lower().lstrip(".") not in allowed_exts:
                continue
            if p.suffix.lower() == ".m3u":
                continue  # ignore existing playlists
            m = list(disc_token.finditer(p.name))
            if m:
                first = m[0]
                num = first.group(2)
                if num.isalpha():
                    num = letter_map.get(num.upper(), 0)
                else:
                    num = int(num)
                base = clean_name(p.name[:first.start()] + p.name[first.end():])
                groups[base].append((num, p.name))
            else:
                singles.append(p.name)

        # Process multi-disc groups
        for base, lst in groups.items():
            lst.sort(key=lambda x: x[0])
            m3u_path = folder_path / (Path(base).stem + ".m3u")
            with open(m3u_path, "w", encoding="utf-8", newline="\n") as fout:
                for _, fname in lst:
                    fout.write(f"{prefix}{fname}\n")
            self.log_msg(f"Created playlist: {m3u_path.name} ({len(lst)} entries)")
            if move_files:
                for _, fname in lst:
                    src = folder_path / fname
                    src.rename(target_dir / fname)

        # Process single-disc if enabled
        if create_single:
            for fname in singles:
                base = Path(fname).stem
                m3u_path = folder_path / (base + ".m3u")
                with open(m3u_path, "w", encoding="utf-8", newline="\n") as fout:
                    fout.write(f"{prefix}{fname}\n")
                self.log_msg(f"Created single-disc playlist: {m3u_path.name}")
                if move_files:
                    src = folder_path / fname
                    src.rename(target_dir / fname)

        self.log_msg("Processing complete!")

if __name__ == "__main__":
    app = PlaylistGUI()
    app.mainloop()