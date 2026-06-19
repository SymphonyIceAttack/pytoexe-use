import json
import os
import webbrowser
import tkinter as tk
from tkinter import messagebox

CONFIG_FILE = "config.json"

# ---------- Theme ----------
BG = "#1e1e2e"
PANEL_BG = "#27293d"
FG = "#e0e0f0"
ACCENT = "#7c5cff"
ACCENT_HOVER = "#9279ff"
DANGER = "#ff5c5c"
DANGER_HOVER = "#ff7a7a"
STATUS_BG = "#15151f"


def load_servers():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_servers(servers):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(servers, f, indent=2)
    except OSError as e:
        messagebox.showerror("Save Error", f"Could not save config.json:\n{e}")


class RobloxLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎮 Roblox Server Launcher")
        self.geometry("400x300")
        self.minsize(320, 240)
        self.configure(bg=BG)

        self.servers = load_servers()
        self.selected_index = None
        self.server_buttons = []

        self._build_layout()
        self._refresh_server_list()

    # ---------- UI construction ----------
    def _build_layout(self):
        # Header
        header = tk.Label(
            self, text="🎮 Roblox Server Launcher",
            bg=BG, fg=FG, font=("Segoe UI", 13, "bold"), pady=10
        )
        header.pack(fill="x")

        # Scrollable server list area
        list_container = tk.Frame(self, bg=BG)
        list_container.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        self.canvas = tk.Canvas(list_container, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.list_frame = tk.Frame(self.canvas, bg=BG)

        self.list_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Bottom button bar
        btn_bar = tk.Frame(self, bg=BG)
        btn_bar.pack(fill="x", padx=10, pady=5)

        self.add_btn = tk.Button(
            btn_bar, text="➕ Add Server", command=self.open_add_popup,
            bg=ACCENT, fg="white", activebackground=ACCENT_HOVER,
            activeforeground="white", relief="flat", padx=10, pady=5,
            font=("Segoe UI", 9, "bold"), cursor="hand2"
        )
        self.add_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.delete_btn = tk.Button(
            btn_bar, text="🗑 Delete Server", command=self.delete_selected,
            bg=DANGER, fg="white", activebackground=DANGER_HOVER,
            activeforeground="white", relief="flat", padx=10, pady=5,
            font=("Segoe UI", 9, "bold"), cursor="hand2"
        )
        self.delete_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            self, textvariable=self.status_var, bg=STATUS_BG, fg=FG,
            anchor="w", padx=10, pady=4, font=("Segoe UI", 9)
        )
        status_bar.pack(fill="x", side="bottom")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ---------- Server list rendering ----------
    def _refresh_server_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self.server_buttons = []

        if not self.servers:
            empty_label = tk.Label(
                self.list_frame, text="No servers saved yet.\nClick 'Add Server' to get started.",
                bg=BG, fg="#8888a0", font=("Segoe UI", 9), pady=20
            )
            empty_label.pack(fill="x")
            return

        for i, server in enumerate(self.servers):
            row = tk.Frame(self.list_frame, bg=PANEL_BG)
            row.pack(fill="x", pady=3, padx=2)

            btn = tk.Button(
                row, text=f"▶  {server['name']}", anchor="w",
                bg=PANEL_BG, fg=FG, activebackground=ACCENT,
                activeforeground="white", relief="flat", padx=10, pady=8,
                font=("Segoe UI", 10), cursor="hand2",
                command=lambda idx=i: self.launch_server(idx)
            )
            btn.pack(side="left", fill="x", expand=True)

            # Click to select (for deletion) without launching - right click
            btn.bind("<Button-3>", lambda e, idx=i: self.select_server(idx))

            self.server_buttons.append((row, btn))

        self._highlight_selection()

    def select_server(self, idx):
        self.selected_index = idx
        self._highlight_selection()
        self.status_var.set(f"Selected: {self.servers[idx]['name']} (right-click to select, then Delete)")

    def _highlight_selection(self):
        for i, (row, btn) in enumerate(self.server_buttons):
            if i == self.selected_index:
                row.configure(bg=ACCENT)
                btn.configure(bg=ACCENT)
            else:
                row.configure(bg=PANEL_BG)
                btn.configure(bg=PANEL_BG)

    # ---------- Actions ----------
    def launch_server(self, idx):
        server = self.servers[idx]
        self.selected_index = idx
        self._highlight_selection()
        self.status_var.set("Launching...")
        self.update_idletasks()

        code = server.get("code", "")
        url = f"roblox://navigation/share_links?code={code}&type=Server"

        try:
            opened = webbrowser.open(url)
            if not opened:
                raise RuntimeError("System reported the link could not be opened.")
            self.status_var.set(f"Launched: {server['name']}")
            # Reset status back to Ready after a short delay
            self.after(3000, lambda: self.status_var.set("Ready"))
        except Exception as e:
            self.status_var.set("Launch failed")
            messagebox.showerror(
                "Launch Error",
                f"Could not launch Roblox.\n\n"
                f"Make sure Roblox is installed and try again.\n\nDetails: {e}"
            )
            self.after(2000, lambda: self.status_var.set("Ready"))

    def delete_selected(self):
        if self.selected_index is None or self.selected_index >= len(self.servers):
            messagebox.showinfo(
                "No Selection",
                "Right-click a server in the list to select it first, then click Delete Server."
            )
            return

        server = self.servers[self.selected_index]
        confirm = messagebox.askyesno(
            "Confirm Delete", f"Delete server '{server['name']}'?"
        )
        if confirm:
            del self.servers[self.selected_index]
            self.selected_index = None
            save_servers(self.servers)
            self._refresh_server_list()
            self.status_var.set("Server deleted")
            self.after(2000, lambda: self.status_var.set("Ready"))

    def open_add_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Add Server")
        popup.configure(bg=BG)
        popup.resizable(False, False)
        popup.geometry("320x200")
        popup.transient(self)
        popup.grab_set()

        # Center popup over main window
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 160
        y = self.winfo_y() + (self.winfo_height() // 2) - 100
        popup.geometry(f"+{x}+{y}")

        tk.Label(
            popup, text="Server Name", bg=BG, fg=FG, font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 0))
        name_entry = tk.Entry(
            popup, bg=PANEL_BG, fg=FG, insertbackground=FG,
            relief="flat", font=("Segoe UI", 10)
        )
        name_entry.pack(fill="x", padx=15, pady=(2, 10), ipady=4)

        tk.Label(
            popup, text="Share Code", bg=BG, fg=FG, font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=15, pady=(0, 0))
        code_entry = tk.Entry(
            popup, bg=PANEL_BG, fg=FG, insertbackground=FG,
            relief="flat", font=("Segoe UI", 10)
        )
        code_entry.pack(fill="x", padx=15, pady=(2, 15), ipady=4)

        def submit():
            name = name_entry.get().strip()
            code = code_entry.get().strip()
            if not name or not code:
                messagebox.showwarning("Missing Info", "Please enter both a name and a share code.", parent=popup)
                return
            self.servers.append({"name": name, "code": code})
            save_servers(self.servers)
            self._refresh_server_list()
            self.status_var.set(f"Added: {name}")
            self.after(2000, lambda: self.status_var.set("Ready"))
            popup.destroy()

        btn_frame = tk.Frame(popup, bg=BG)
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))

        save_btn = tk.Button(
            btn_frame, text="Save", command=submit,
            bg=ACCENT, fg="white", activebackground=ACCENT_HOVER,
            activeforeground="white", relief="flat", padx=10, pady=5,
            font=("Segoe UI", 9, "bold"), cursor="hand2"
        )
        save_btn.pack(side="right", padx=(5, 0))

        cancel_btn = tk.Button(
            btn_frame, text="Cancel", command=popup.destroy,
            bg=PANEL_BG, fg=FG, activebackground="#3a3a55",
            activeforeground=FG, relief="flat", padx=10, pady=5,
            font=("Segoe UI", 9), cursor="hand2"
        )
        cancel_btn.pack(side="right")

        name_entry.focus_set()
        popup.bind("<Return>", lambda e: submit())


if __name__ == "__main__":
    app = RobloxLauncher()
    app.mainloop()
