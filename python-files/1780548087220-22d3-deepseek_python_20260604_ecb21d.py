import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import shutil
import json
import subprocess
import platform
from pathlib import Path
from datetime import datetime

# ==================== CONFIGURATION ====================
ROOT_DIR = Path.home() / "MediaVault"          # main folder where everything is stored
MEDIA_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',   # images
    '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'       # videos
}
METADATA_FILE = ".mediamanager.json"           # stores separators inside each folder

# ==================== HELPER FUNCTIONS ====================
def is_media_file(filename: str) -> bool:
    """Check if file has a media extension."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in MEDIA_EXTENSIONS

def get_file_size_str(filepath: Path) -> str:
    """Return human-readable file size."""
    size = filepath.stat().st_size
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def open_file_with_default_app(filepath: Path):
    """Open file with system default application."""
    if platform.system() == "Windows":
        os.startfile(filepath)
    elif platform.system() == "Darwin":          # macOS
        subprocess.run(["open", filepath])
    else:                                        # Linux
        subprocess.run(["xdg-open", filepath])

def get_metadata(folder_path: Path) -> dict:
    """Read metadata file from folder, return dict with 'separators' list."""
    meta_path = folder_path / METADATA_FILE
    if meta_path.exists():
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"separators": []}
    else:
        return {"separators": []}

def save_metadata(folder_path: Path, metadata: dict):
    """Save metadata to folder."""
    meta_path = folder_path / METADATA_FILE
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def add_separator(folder_path: Path, caption: str) -> dict:
    """Add a separator to folder's metadata and return updated metadata."""
    meta = get_metadata(folder_path)
    new_sep = {
        "id": str(datetime.now().timestamp()),
        "caption": caption,
        "created": datetime.now().isoformat()
    }
    meta.setdefault("separators", []).append(new_sep)
    save_metadata(folder_path, meta)
    return meta

def delete_separator(folder_path: Path, sep_id: str):
    """Remove a separator by its id."""
    meta = get_metadata(folder_path)
    meta["separators"] = [s for s in meta.get("separators", []) if s.get("id") != sep_id]
    save_metadata(folder_path, meta)

# ==================== MAIN APPLICATION ====================
class MediaManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Media Manager - Folder Shell")
        self.geometry("1100x700")
        self.minsize(800, 500)

        # Ensure root directory exists
        ROOT_DIR.mkdir(exist_ok=True)

        # Current selected folder path
        self.current_folder = ROOT_DIR

        # Build UI
        self.create_widgets()
        self.refresh_tree()          # load folder tree
        self.refresh_content()       # load content of root folder

        # Bind global events
        self.bind("<Configure>", self.on_resize)

    # ---------------------- UI Creation ----------------------
    def create_widgets(self):
        style = ttk.Style(self)
        # Use a modern theme if available
        available_themes = style.theme_names()
        if 'vista' in available_themes:
            style.theme_use('vista')
        elif 'clam' in available_themes:
            style.theme_use('clam')

        # Top frame: search bar
        top_frame = ttk.Frame(self, padding="5")
        top_frame.pack(fill=tk.X, side=tk.TOP)

        ttk.Label(top_frame, text="Search folders:", font=('', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.refresh_tree())
        search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Button(top_frame, text="Clear", command=self.clear_search).pack(side=tk.LEFT, padx=5)

        # Main paned window (left tree, right content)
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left frame: folder tree
        left_frame = ttk.Frame(self.paned)
        self.paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Folder Structure", font=('', 10, 'bold')).pack(anchor=tk.W, padx=5, pady=2)
        tree_scroll = ttk.Scrollbar(left_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree = ttk.Treeview(left_frame, yscrollcommand=tree_scroll.set, selectmode='browse')
        self.tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Right frame: content panel
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=3)

        # Toolbar
        toolbar = ttk.Frame(right_frame)
        toolbar.pack(fill=tk.X, pady=(0,5))
        ttk.Button(toolbar, text="📁 New Folder", command=self.create_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📤 Upload Media", command=self.upload_media).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✚ Add Separator", command=self.add_separator_ui).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_content).pack(side=tk.LEFT, padx=2)

        # Content treeview (files, folders, separators)
        content_scroll = ttk.Scrollbar(right_frame)
        content_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_tree = ttk.Treeview(right_frame, columns=("type", "size"), show="tree headings",
                                         yscrollcommand=content_scroll.set)
        self.content_tree.heading("#0", text="Name")
        self.content_tree.heading("type", text="Type")
        self.content_tree.heading("size", text="Size")
        self.content_tree.column("#0", width=400)
        self.content_tree.column("type", width=120)
        self.content_tree.column("size", width=100)
        self.content_tree.pack(fill=tk.BOTH, expand=True)
        content_scroll.config(command=self.content_tree.yview)

        # Bind double-click and right-click
        self.content_tree.bind("<Double-1>", self.on_content_double_click)
        self.content_tree.bind("<Button-3>", self.on_content_right_click)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ---------------------- Folder Tree Logic ----------------------
    def clear_search(self):
        self.search_var.set("")
        self.refresh_tree()

    def refresh_tree(self):
        """Rebuild the folder tree respecting search filter."""
        # Remember currently selected folder path
        selected = self.current_folder
        self.tree.delete(*self.tree.get_children())
        # Insert root node
        search_term = self.search_var.get().strip().lower()
        self._insert_folder_node("", ROOT_DIR, search_term)
        # Expand root node
        self.tree.item(ROOT_DIR.as_posix(), open=True)
        # Try to reselect the previous folder
        if selected and selected != ROOT_DIR:
            try:
                self.tree.selection_set(selected.as_posix())
                self.tree.see(selected.as_posix())
            except tk.TclError:
                pass

    def _insert_folder_node(self, parent, folder_path: Path, search_term: str):
        """Recursively insert folders that match search (or have matching children)."""
        # Decide if this folder should be shown
        show = (search_term == "") or (search_term in folder_path.name.lower())
        children_match = False
        try:
            items = sorted([p for p in folder_path.iterdir() if p.is_dir()])
        except PermissionError:
            return

        child_nodes = []
        for sub in items:
            # Recursively check children
            child_shown = self._insert_folder_node(folder_path.as_posix(), sub, search_term)
            if child_shown:
                children_match = True
                child_nodes.append(sub)

        if show or children_match or folder_path == ROOT_DIR:
            # Insert this folder
            node_id = folder_path.as_posix()
            # Determine label: show relative path from root? just name
            label = folder_path.name if folder_path != ROOT_DIR else "📁 MediaVault (root)"
            if folder_path == ROOT_DIR:
                label = "📁 MediaVault (root)"
            else:
                label = f"📁 {folder_path.name}"
            self.tree.insert(parent, "end", iid=node_id, text=label, open=False)
            # Insert children that were already added (to keep order)
            for sub in child_nodes:
                # children already inserted via recursion, but we need to reattach? 
                # In recursion they are attached to node_id, so it's fine
                pass
            return True
        else:
            return False

    def on_tree_select(self, event):
        """User selected a folder in the tree."""
        selection = self.tree.selection()
        if selection:
            path_str = selection[0]
            self.current_folder = Path(path_str)
            self.refresh_content()
            self.status_var.set(f"Current: {self.current_folder}")

    # ---------------------- Content Panel Logic ----------------------
    def refresh_content(self):
        """Refresh right panel: show subfolders, separators, media files."""
        self.content_tree.delete(*self.content_tree.get_children())
        if not self.current_folder.exists():
            self.status_var.set(f"Folder does not exist: {self.current_folder}")
            return

        # 1. Subfolders
        subfolders = []
        try:
            for item in self.current_folder.iterdir():
                if item.is_dir() and item.name != METADATA_FILE:
                    subfolders.append(item)
        except PermissionError:
            pass
        subfolders.sort(key=lambda x: x.name.lower())
        for folder in subfolders:
            self.content_tree.insert("", "end", iid=folder.as_posix(), text=f"📁 {folder.name}",
                                     values=("Folder", ""), tags=("folder",))

        # 2. Separators from metadata
        meta = get_metadata(self.current_folder)
        separators = meta.get("separators", [])
        for sep in separators:
            sep_id = sep.get("id")
            caption = sep.get("caption", "Untitled")
            display = f"--- {caption} ---"
            self.content_tree.insert("", "end", iid=f"sep_{sep_id}", text=display,
                                     values=("Separator", ""), tags=("separator",))

        # 3. Media files
        media_files = []
        try:
            for item in self.current_folder.iterdir():
                if item.is_file() and is_media_file(item.name):
                    media_files.append(item)
        except PermissionError:
            pass
        media_files.sort(key=lambda x: x.name.lower())
        for file in media_files:
            size_str = get_file_size_str(file)
            # Determine type icon
            ext = os.path.splitext(file.name)[1].lower()
            if ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}:
                icon = "🖼️"
                ftype = "Image"
            else:
                icon = "🎬"
                ftype = "Video"
            self.content_tree.insert("", "end", iid=file.as_posix(), text=f"{icon} {file.name}",
                                     values=(ftype, size_str), tags=("file",))

        # Configure tag colors
        self.content_tree.tag_configure("folder", foreground="#2c3e50", font=('', 9, 'bold'))
        self.content_tree.tag_configure("separator", foreground="#8e44ad", font=('', 9, 'italic'))
        self.content_tree.tag_configure("file", foreground="#2980b9")

    def on_content_double_click(self, event):
        """Open folder or file on double-click."""
        item = self.content_tree.selection()[0] if self.content_tree.selection() else None
        if not item:
            return
        # Check if it's a folder
        if item.startswith("sep_"):
            return   # separators do nothing
        path = Path(item)
        if path.exists() and path.is_dir():
            # Navigate into folder
            self.current_folder = path
            self.refresh_tree()   # update tree selection
            self.refresh_content()
            # Select in tree
            try:
                self.tree.selection_set(path.as_posix())
                self.tree.see(path.as_posix())
            except:
                pass
        elif path.exists() and path.is_file():
            open_file_with_default_app(path)
        else:
            messagebox.showerror("Error", "Item no longer exists")

    def on_content_right_click(self, event):
        """Show context menu for delete/remove."""
        item = self.content_tree.identify_row(event.y)
        if not item:
            return
        self.content_tree.selection_set(item)
        # Determine item type
        if item.startswith("sep_"):
            sep_id = item.replace("sep_", "")
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Remove Separator", command=lambda: self.delete_separator_item(sep_id))
            menu.post(event.x_root, event.y_root)
        else:
            path = Path(item)
            if path.exists():
                menu = tk.Menu(self, tearoff=0)
                menu.add_command(label="Delete", command=lambda: self.delete_file_or_folder(path))
                menu.post(event.x_root, event.y_root)

    # ---------------------- Actions ----------------------
    def create_folder(self):
        """Create new subfolder inside current folder."""
        name = simpledialog.askstring("New Folder", "Enter folder name:", parent=self)
        if not name:
            return
        # Sanitize name
        name = "".join(c for c in name if c not in r'\/:*?"<>|')
        if not name:
            messagebox.showerror("Error", "Invalid folder name")
            return
        new_path = self.current_folder / name
        try:
            new_path.mkdir(exist_ok=False)
            self.status_var.set(f"Folder created: {name}")
            self.refresh_tree()
            self.refresh_content()
        except FileExistsError:
            messagebox.showerror("Error", "Folder already exists")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create folder: {e}")

    def upload_media(self):
        """Upload media files into current folder."""
        filetypes = [
            ("Media files", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp *.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
            ("All files", "*.*")
        ]
        files = filedialog.askopenfilenames(title="Select media files", filetypes=filetypes)
        if not files:
            return
        copied = 0
        skipped = 0
        for src in files:
            src_path = Path(src)
            dest = self.current_folder / src_path.name
            if dest.exists():
                if not messagebox.askyesno("File exists", f"{dest.name} already exists. Overwrite?"):
                    skipped += 1
                    continue
            try:
                shutil.copy2(src_path, dest)
                copied += 1
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy {src_path.name}: {e}")
        self.status_var.set(f"Uploaded {copied} files, skipped {skipped}")
        self.refresh_content()

    def add_separator_ui(self):
        """Add a visual separator with a caption."""
        caption = simpledialog.askstring("Add Separator", "Caption for separator:", parent=self)
        if caption is None:
            return
        if caption.strip() == "":
            caption = "Separator"
        add_separator(self.current_folder, caption.strip())
        self.refresh_content()
        self.status_var.set(f"Separator added: {caption}")

    def delete_separator_item(self, sep_id):
        """Delete a separator by its id."""
        delete_separator(self.current_folder, sep_id)
        self.refresh_content()
        self.status_var.set("Separator removed")

    def delete_file_or_folder(self, path: Path):
        """Delete a file or folder (with confirmation)."""
        if path.is_dir():
            if messagebox.askyesno("Confirm Delete", f"Delete folder '{path.name}' and all its contents?"):
                try:
                    shutil.rmtree(path)
                    self.status_var.set(f"Deleted folder: {path.name}")
                    # If we deleted the current folder, go up
                    if self.current_folder == path:
                        self.current_folder = path.parent
                    self.refresh_tree()
                    self.refresh_content()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete folder: {e}")
        else:
            if messagebox.askyesno("Confirm Delete", f"Delete file '{path.name}'?"):
                try:
                    path.unlink()
                    self.status_var.set(f"Deleted file: {path.name}")
                    self.refresh_content()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete file: {e}")

    def on_resize(self, event):
        """Adjust column widths on resize (simple)."""
        if event.widget == self:
            width = self.content_tree.winfo_width()
            self.content_tree.column("#0", width=max(200, width - 300))


# ==================== RUN ====================
if __name__ == "__main__":
    app = MediaManagerApp()
    app.mainloop()