#!/usr/bin/env python3
import base64
import json
import mimetypes
import os
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path
try:
    from tkinter import BOTH, DISABLED, NORMAL, Button, Entry, Label, StringVar, Tk, Toplevel, filedialog, messagebox
except ImportError as err:
    TK_ERROR = err
else:
    TK_ERROR = None

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    DND_FILES = None
    TkinterDnD = None


IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
CONFIG_PATH = Path(os.environ.get("APPDATA") or Path.home() / ".config") / "tinify-gui" / "config.json"


def load_config(path=CONFIG_PATH):
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_config(config, path=CONFIG_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2))


def tinify(image_path, api_key):
    image_path = Path(image_path)
    if image_path.suffix.lower() not in IMAGE_TYPES:
        raise ValueError("Choose a JPG, PNG, WebP, or AVIF image.")

    auth = base64.b64encode(f"api:{api_key}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": mimetypes.guess_type(image_path)[0] or "application/octet-stream",
    }

    request = urllib.request.Request(
        "https://api.tinify.com/shrink",
        data=image_path.read_bytes(),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result_url = response.headers["Location"]
    except urllib.error.HTTPError as err:
        details = json.loads(err.read().decode() or "{}")
        raise RuntimeError(details.get("message") or f"Tinify failed with HTTP {err.code}") from err

    with urllib.request.urlopen(result_url, timeout=60) as response:
        return response.read()


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Tinify GUI")
        self.root.geometry("520x280")

        self.config = load_config()
        self.api_key = StringVar(value=self.config.get("api_key") or os.environ.get("TINIFY_KEY", ""))
        self.status = StringVar(value="Drop an image here, or click Choose Image.")

        Button(root, text="Settings", command=self.open_settings).pack(pady=(18, 4))

        self.drop = Label(
            root,
            text="Drop image here",
            relief="groove",
            width=52,
            height=6,
            bg="#f6f6f6",
        )
        self.drop.pack(pady=16, fill=BOTH, expand=True, padx=18)
        self.drop.bind("<Button-1>", lambda _event: self.choose_image())

        if DND_FILES:
            self.drop.drop_target_register(DND_FILES)
            self.drop.dnd_bind("<<Drop>>", self.drop_image)

        self.button = Button(root, text="Choose Image", command=self.choose_image)
        self.button.pack()
        Label(root, textvariable=self.status).pack(pady=10)

    def open_settings(self):
        win = Toplevel(self.root)
        win.title("Settings")
        win.geometry("460x150")
        key = StringVar(value=self.api_key.get())

        Label(win, text="Tinify API key").pack(pady=(18, 4))
        Entry(win, textvariable=key, show="*", width=52).pack()

        def save():
            self.config["api_key"] = key.get().strip()
            save_config(self.config)
            self.api_key.set(self.config["api_key"])
            win.destroy()

        Button(win, text="Save", command=save).pack(pady=16)

    def drop_image(self, event):
        files = self.root.tk.splitlist(event.data)
        if files:
            self.compress(files[0])

    def choose_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.avif"), ("All files", "*.*")]
        )
        if path:
            self.compress(path)

    def compress(self, path):
        api_key = self.api_key.get().strip()
        if not api_key:
            messagebox.showerror("Missing API key", "Enter your Tinify API key first.")
            return

        source = Path(path)
        target = filedialog.asksaveasfilename(
            initialfile=f"{source.stem}-compressed{source.suffix}",
            defaultextension=source.suffix,
            filetypes=[("Same format", f"*{source.suffix}"), ("All files", "*.*")],
        )
        if not target:
            return

        self.set_busy(f"Compressing {source.name}...")
        threading.Thread(target=self.compress_in_background, args=(source, target, api_key), daemon=True).start()

    def compress_in_background(self, source, target, api_key):
        try:
            output = tinify(source, api_key)
            Path(target).write_bytes(output)
            saved = source.stat().st_size - len(output)
            self.root.after(0, self.done, f"Saved {max(saved, 0) / 1024:.1f} KB -> {target}")
        except Exception as err:
            self.root.after(0, self.failed, str(err))

    def set_busy(self, text):
        self.status.set(text)
        self.button.config(state=DISABLED)

    def done(self, text):
        self.status.set(text)
        self.button.config(state=NORMAL)

    def failed(self, text):
        self.status.set("Failed.")
        self.button.config(state=NORMAL)
        messagebox.showerror("Tinify failed", text)


def self_check():
    assert ".png" in IMAGE_TYPES
    assert base64.b64encode(b"api:key").decode() == "YXBpOmtleQ=="
    test_path = Path(tempfile.gettempdir()) / "tinify-gui-self-check.json"
    save_config({"api_key": "abc"}, test_path)
    assert load_config(test_path)["api_key"] == "abc"
    test_path.unlink()
    print("self-check ok")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        self_check()
    else:
        if TK_ERROR:
            raise SystemExit("Tkinter is missing. Install python3-tk, then run this again.")
        root = TkinterDnD.Tk() if TkinterDnD else Tk()
        App(root)
        root.mainloop()
