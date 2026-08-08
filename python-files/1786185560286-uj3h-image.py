#!/usr/bin/env python3
"""
Image Duplicate & Similarity Finder - GUI + Parallel version
"""

import os
import sys
import hashlib
import threading
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

try:
    from PIL import Image
    import imagehash
except ImportError:
    print("Please install required packages:\n  pip install Pillow imagehash")
    sys.exit(1)

# -------------------------------------------------
# Core logic
# -------------------------------------------------

IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
    '.webp', '.heic', '.heif', '.ico'
}

def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS

def get_file_hash(filepath: Path) -> str:
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""

def get_perceptual_hash(filepath: Path, method: str = "phash", hash_size: int = 16):
    try:
        with Image.open(filepath) as img:
            img = img.convert("RGB")
            if method == "ahash":
                return imagehash.average_hash(img, hash_size=hash_size)
            elif method == "dhash":
                return imagehash.dhash(img, hash_size=hash_size)
            elif method == "whash":
                return imagehash.whash(img, hash_size=hash_size)
            else:
                return imagehash.phash(img, hash_size=hash_size)
    except Exception:
        return None

def scan_folder(folder: Path, recursive: bool) -> List[Path]:
    images = []
    iterator = folder.rglob("*") if recursive else folder.iterdir()
    for p in iterator:
        if p.is_file() and is_image(p):
            images.append(p)
    return images

def find_exact_duplicates(images: List[Path], max_workers: int = 8) -> Dict[str, List[Path]]:
    # Group by size first
    size_groups = defaultdict(list)
    for img in images:
        try:
            size_groups[img.stat().st_size].append(img)
        except OSError:
            continue

    candidates = []
    for files in size_groups.values():
        if len(files) >= 2:
            candidates.extend(files)

    if not candidates:
        return {}

    hash_map = defaultdict(list)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {executor.submit(get_file_hash, p): p for p in candidates}
        for future in as_completed(future_to_path):
            path = future_to_path[future]
            h = future.result()
            if h:
                hash_map[h].append(path)

    return {k: v for k, v in hash_map.items() if len(v) > 1}

def find_similar_images(
    images: List[Path],
    threshold: int = 8,
    method: str = "phash",
    hash_size: int = 16,
    max_workers: int = 8,
    progress_callback=None
) -> List[List[Path]]:

    hashes = []
    total = len(images)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(get_perceptual_hash, p, method, hash_size): p
            for p in images
        }
        done = 0
        for future in as_completed(future_to_path):
            path = future_to_path[future]
            h = future.result()
            if h is not None:
                hashes.append((path, h))
            done += 1
            if progress_callback and done % 5 == 0:
                progress_callback(done, total)

    if progress_callback:
        progress_callback(total, total)

    # Group by similarity
    used = set()
    groups = []

    for i, (path1, hash1) in enumerate(hashes):
        if path1 in used:
            continue
        group = [path1]
        used.add(path1)

        for j in range(i + 1, len(hashes)):
            path2, hash2 = hashes[j]
            if path2 in used:
                continue
            if (hash1 - hash2) <= threshold:
                group.append(path2)
                used.add(path2)

        if len(group) > 1:
            groups.append(sorted(group, key=lambda p: str(p).lower()))

    return groups

# -------------------------------------------------
# GUI
# -------------------------------------------------

class DuplicateFinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Duplicate & Similarity Finder")
        self.root.geometry("980x720")
        self.root.minsize(800, 600)

        self.folder = tk.StringVar()
        self.recursive = tk.BooleanVar(value=True)
        self.mode = tk.StringVar(value="exact")          # exact | similar
        self.threshold = tk.IntVar(value=8)
        self.method = tk.StringVar(value="phash")
        self.action = tk.StringVar(value="dry-run")      # dry-run | move | delete
        self.quarantine_name = tk.StringVar(value="duplicates")

        self.groups: List[List[Path]] = []
        self.is_running = False

        self.build_ui()

    def build_ui(self):
        # ----- Top controls -----
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Folder:").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.folder, width=70).grid(row=0, column=1, padx=5)
        ttk.Button(top, text="Browse...", command=self.browse_folder).grid(row=0, column=2)

        options = ttk.LabelFrame(self.root, text="Options", padding=10)
        options.pack(fill=tk.X, padx=10, pady=5)

        ttk.Checkbutton(options, text="Include subfolders", variable=self.recursive).grid(row=0, column=0, sticky="w")

        ttk.Label(options, text="Mode:").grid(row=0, column=1, padx=(20, 5))
        ttk.Radiobutton(options, text="Exact duplicates", variable=self.mode, value="exact").grid(row=0, column=2)
        ttk.Radiobutton(options, text="Visually similar", variable=self.mode, value="similar").grid(row=0, column=3)

        ttk.Label(options, text="Threshold:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Spinbox(options, from_=0, to=20, textvariable=self.threshold, width=5).grid(row=1, column=1, sticky="w", pady=(8, 0))
        ttk.Label(options, text="(lower = stricter)").grid(row=1, column=2, sticky="w", pady=(8, 0))

        ttk.Label(options, text="Hash method:").grid(row=1, column=3, padx=(20, 5), pady=(8, 0))
        ttk.Combobox(options, textvariable=self.method, values=["phash", "ahash", "dhash", "whash"],
                     width=8, state="readonly").grid(row=1, column=4, pady=(8, 0))

        action_frame = ttk.LabelFrame(self.root, text="Action after scan", padding=10)
        action_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Radiobutton(action_frame, text="Dry-run (only show)", variable=self.action, value="dry-run").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(action_frame, text="Move to folder", variable=self.action, value="move").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(action_frame, text="Delete permanently", variable=self.action, value="delete").pack(side=tk.LEFT, padx=5)

        ttk.Label(action_frame, text="Quarantine name:").pack(side=tk.LEFT, padx=(20, 5))
        ttk.Entry(action_frame, textvariable=self.quarantine_name, width=15).pack(side=tk.LEFT)

        # Buttons
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill=tk.X)

        self.scan_btn = ttk.Button(btn_frame, text="▶ Start Scan", command=self.start_scan)
        self.scan_btn.pack(side=tk.LEFT, padx=5)

        self.process_btn = ttk.Button(btn_frame, text="Process Selected Groups", command=self.process_groups, state="disabled")
        self.process_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="Clear Results", command=self.clear_results).pack(side=tk.LEFT, padx=5)

        # Progress
        self.progress = ttk.Progressbar(self.root, mode="determinate")
        self.progress.pack(fill=tk.X, padx=10, pady=5)

        self.status = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.status).pack(anchor="w", padx=10)

        # Results area
        results_frame = ttk.LabelFrame(self.root, text="Results", padding=5)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(results_frame, columns=("path", "size"), show="tree headings", selectmode="extended")
        self.tree.heading("#0", text="Group / File")
        self.tree.heading("path", text="Full Path")
        self.tree.heading("size", text="Size")
        self.tree.column("#0", width=220)
        self.tree.column("path", width=500)
        self.tree.column("size", width=100)

        scroll_y = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Log
        self.log = scrolledtext.ScrolledText(self.root, height=6, state="disabled")
        self.log.pack(fill=tk.X, padx=10, pady=5)

    def browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder.set(path)

    def log_msg(self, msg: str):
        self.log.configure(state="normal")
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.configure(state="disabled")

    def clear_results(self):
        self.tree.delete(*self.tree.get_children())
        self.groups = []
        self.process_btn.configure(state="disabled")
        self.progress["value"] = 0
        self.status.set("Ready")
        self.log.configure(state="normal")
        self.log.delete("1.0", tk.END)
        self.log.configure(state="disabled")

    def start_scan(self):
        if self.is_running:
            return

        folder = Path(self.folder.get())
        if not folder.is_dir():
            messagebox.showerror("Error", "Please select a valid folder.")
            return

        self.clear_results()
        self.is_running = True
        self.scan_btn.configure(state="disabled")
        self.status.set("Scanning...")

        thread = threading.Thread(target=self.run_scan, args=(folder,), daemon=True)
        thread.start()

    def run_scan(self, folder: Path):
        try:
            images = scan_folder(folder, self.recursive.get())
            self.root.after(0, lambda: self.log_msg(f"Found {len(images)} images."))

            if not images:
                self.root.after(0, lambda: self.finish_scan("No images found."))
                return

            def progress_cb(current, total):
                self.root.after(0, lambda: self.update_progress(current, total))

            if self.mode.get() == "exact":
                self.root.after(0, lambda: self.status.set("Computing exact hashes (parallel)..."))
                groups_dict = find_exact_duplicates(images)
                self.groups = list(groups_dict.values())
            else:
                self.root.after(0, lambda: self.status.set("Computing perceptual hashes (parallel)..."))
                self.groups = find_similar_images(
                    images,
                    threshold=self.threshold.get(),
                    method=self.method.get(),
                    progress_callback=progress_cb
                )

            self.root.after(0, self.display_results)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, lambda: self.finish_scan("Error occurred."))

    def update_progress(self, current, total):
        if total > 0:
            self.progress["value"] = (current / total) * 100
            self.status.set(f"Processing... {current}/{total}")

    def display_results(self):
        self.tree.delete(*self.tree.get_children())

        if not self.groups:
            self.log_msg("No duplicates / similar images found.")
            self.finish_scan("Done – nothing to clean.")
            return

        total_extra = 0
        for i, group in enumerate(self.groups, 1):
            group_id = self.tree.insert("", "end", text=f"Group {i} ({len(group)} files)", open=True)
            for j, path in enumerate(group):
                try:
                    size = f"{path.stat().st_size / 1024:.1f} KB"
                except OSError:
                    size = "?"
                tag = "keep" if j == 0 else "extra"
                self.tree.insert(group_id, "end", text="→ KEEP" if j == 0 else "  extra",
                                 values=(str(path), size), tags=(tag,))
                if j > 0:
                    total_extra += 1

        self.tree.tag_configure("keep", foreground="#006400")
        self.tree.tag_configure("extra", foreground="#8B0000")

        self.log_msg(f"Found {len(self.groups)} groups ({total_extra} extra files).")
        self.process_btn.configure(state="normal")
        self.finish_scan(f"Done – {len(self.groups)} groups found.")

    def finish_scan(self, msg: str):
        self.is_running = False
        self.scan_btn.configure(state="normal")
        self.status.set(msg)
        self.progress["value"] = 100

    def process_groups(self):
        if not self.groups:
            return

        action = self.action.get()
        if action == "dry-run":
            messagebox.showinfo("Dry-run", "Dry-run mode – no files will be changed.")
            return

        total_extra = sum(len(g) - 1 for g in self.groups)
        confirm = messagebox.askyesno(
            "Confirm",
            f"You are about to {action} {total_extra} file(s).\n\nContinue?"
        )
        if not confirm:
            return

        quarantine = None
        if action == "move":
            folder = Path(self.folder.get())
            quarantine = folder / self.quarantine_name.get()
            quarantine.mkdir(exist_ok=True)

        removed = 0
        for group in self.groups:
            for path in group[1:]:  # keep the first one
                try:
                    if action == "delete":
                        path.unlink()
                        self.log_msg(f"Deleted: {path}")
                    else:
                        dest = quarantine / path.name
                        counter = 1
                        while dest.exists():
                            dest = quarantine / f"{path.stem}_{counter}{path.suffix}"
                            counter += 1
                        path.rename(dest)
                        self.log_msg(f"Moved: {path.name}")
                    removed += 1
                except Exception as e:
                    self.log_msg(f"Failed: {path} → {e}")

        messagebox.showinfo("Finished", f"Processed {removed} file(s).")
        self.clear_results()

# -------------------------------------------------
# Main
# -------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    # Optional: make it look a bit more modern on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")

    app = DuplicateFinderApp(root)
    root.mainloop()