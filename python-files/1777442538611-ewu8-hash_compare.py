import hashlib
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox


def is_sha256_hash(value: str) -> bool:
    return bool(re.fullmatch(r"[a-fA-F0-9]{64}", value.strip()))


def hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve(value: str) -> tuple[str, str]:
    value = value.strip()
    if is_sha256_hash(value):
        return value.lower(), "hash"
    else:
        return hash_file(value), "file"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SHA256 Comparator")
        self.resizable(False, False)
        self.configure(padx=20, pady=20)

        # ── Input 1 ──────────────────────────────────────────
        tk.Label(self, text="Input 1 — File or SHA256 Hash", anchor="w").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 2)
        )
        self.entry1 = tk.Entry(self, width=55)
        self.entry1.grid(row=1, column=0, columnspan=2, padx=(0, 6))
        tk.Button(self, text="Browse…", command=lambda: self.browse(self.entry1)).grid(
            row=1, column=2
        )

        # ── Input 2 ──────────────────────────────────────────
        tk.Label(self, text="Input 2 — File or SHA256 Hash", anchor="w").grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(14, 2)
        )
        self.entry2 = tk.Entry(self, width=55)
        self.entry2.grid(row=3, column=0, columnspan=2, padx=(0, 6))
        tk.Button(self, text="Browse…", command=lambda: self.browse(self.entry2)).grid(
            row=3, column=2
        )

        # ── Compare button ────────────────────────────────────
        tk.Button(
            self,
            text="Compare",
            command=self.compare,
            bg="#0066cc",
            fg="white",
            padx=10,
            pady=4,
        ).grid(row=4, column=0, columnspan=3, pady=(16, 10))

        # ── Results ───────────────────────────────────────────
        self.result_frame = tk.LabelFrame(self, text="Result", padx=10, pady=10)
        self.result_frame.grid(row=5, column=0, columnspan=3, sticky="we")

        self.result_label = tk.Label(
            self.result_frame, text="—", font=("Helvetica", 13, "bold"), width=40
        )
        self.result_label.pack()

        tk.Label(self.result_frame, text="Hash 1:").pack(anchor="w", pady=(8, 0))
        self.hash1_var = tk.StringVar()
        tk.Entry(
            self.result_frame,
            textvariable=self.hash1_var,
            state="readonly",
            width=70,
        ).pack(fill="x")

        tk.Label(self.result_frame, text="Hash 2:").pack(anchor="w", pady=(6, 0))
        self.hash2_var = tk.StringVar()
        tk.Entry(
            self.result_frame,
            textvariable=self.hash2_var,
            state="readonly",
            width=70,
        ).pack(fill="x")

    def browse(self, entry: tk.Entry):
        path = filedialog.askopenfilename()
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def compare(self):
        val1 = self.entry1.get().strip()
        val2 = self.entry2.get().strip()

        if not val1 or not val2:
            messagebox.showwarning("Missing input", "Please provide both inputs.")
            return

        try:
            hash1, type1 = resolve(val1)
            hash2, type2 = resolve(val2)
        except FileNotFoundError as e:
            messagebox.showerror("File not found", str(e))
            return
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        self.hash1_var.set(hash1)
        self.hash2_var.set(hash2)

        if hash1 == hash2:
            self.result_label.config(text="✅  MATCH", fg="green")
        else:
            self.result_label.config(text="❌  NO MATCH", fg="red")


if __name__ == "__main__":
    app = App()
    app.mainloop()