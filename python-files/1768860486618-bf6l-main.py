# Link Monitor - Soft Dark (Single File)
# Made by Nurul Islam Hridoy

import json, os, re, subprocess, threading, time
from dataclasses import dataclass, asdict
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

APP_NAME = "Link Monitor"
DATA_FILE = "links.json"

DEFAULT_INTERVAL_SEC = 5
DEFAULT_DOWN_NOTIFY_AFTER_SEC = 20
PING_TIMEOUT_MS = 1200

IPV4_RE = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")


# ---------------- Utils ----------------
def is_valid_ipv4(ip):
    if not IPV4_RE.match(ip.strip()):
        return False
    try:
        return all(0 <= int(p) <= 255 for p in ip.split("."))
    except ValueError:
        return False


def fmt_dt(dt):
    return "-" if not dt else dt.strftime("%Y-%m-%d %H:%M:%S")


def fmt_dur(sec):
    sec = int(max(sec, 0))
    return f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d}"


def ping_once(ip):
    try:
        r = subprocess.run(
            ["ping", "-n", "1", "-w", str(PING_TIMEOUT_MS), ip],
            capture_output=True,
            creationflags=0x08000000  # Windows only
        )
        return r.returncode == 0
    except Exception:
        return False


# ---------------- Theme ----------------
def apply_soft_dark(root):
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")

    BG = "#0f172a"
    PANEL = "#111c33"
    CARD = "#0b1220"
    TEXT = "#e5e7eb"
    DOWN_BG = "#2a0f17"
    UP_BG = "#0f2a1a"

    root.configure(bg=BG)
    root.option_add("*Font", "Segoe UI 10")

    style.configure(".", background=BG, foreground=TEXT)
    style.configure("Treeview", background=CARD, foreground=TEXT, rowheight=26)
    style.configure("Treeview.Heading", background=PANEL, foreground=TEXT,
                    font=("Segoe UI", 10, "bold"))

    return {"BG": BG, "DOWN_BG": DOWN_BG, "UP_BG": UP_BG}


# ---------------- Data ----------------
@dataclass
class Link:
    name: str
    ip: str
    group: str = ""
    notify_enabled: bool = True
    down_notify_after_sec: int = 0  # 0 = global


# ---------------- App ----------------
class LinkMonitorApp:
    def __init__(self, root, colors):
        self.root = root
        self.colors = colors

        self.links = []
        self.state = {}

        self.interval = tk.IntVar(value=DEFAULT_INTERVAL_SEC)
        self.global_down_after = tk.IntVar(value=DEFAULT_DOWN_NOTIFY_AFTER_SEC)
        self.search_text = tk.StringVar()

        self._build_ui()
        self._load_links()
        self._start_polling()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._ui_tick()

    # ---------- UI ----------
    def _build_ui(self):
        self.root.title(APP_NAME)
        self.root.geometry("980x600")

        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Interval (sec)").pack(side="left")
        ttk.Spinbox(top, from_=2, to=60, width=6,
                    textvariable=self.interval).pack(side="left", padx=6)

        ttk.Label(top, text="Down notify after (sec)").pack(side="left")
        ttk.Spinbox(top, from_=5, to=600, width=6,
                    textvariable=self.global_down_after).pack(side="left", padx=6)

        ttk.Button(top, text="Add", command=self.add_link).pack(side="left", padx=6)
        ttk.Button(top, text="Edit", command=self.edit_link).pack(side="left", padx=6)
        ttk.Button(top, text="Remove", command=self.remove_link).pack(side="left", padx=6)

        ttk.Button(top, text="Import", command=self.import_links).pack(side="right", padx=6)
        ttk.Button(top, text="Export", command=self.export_links).pack(side="right", padx=6)

        filt = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        filt.pack(fill="x")

        ttk.Label(filt, text="Search").pack(side="left")
        ent = ttk.Entry(filt, textvariable=self.search_text, width=30)
        ent.pack(side="left", padx=6)
        ent.bind("<KeyRelease>", lambda e: self.refresh())

        cols = ("name", "ip", "group", "notify", "down_after", "status", "since", "downtime")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.upper())
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree.tag_configure("down", background=self.colors["DOWN_BG"])
        self.tree.tag_configure("up", background=self.colors["UP_BG"])

        credit = ttk.Label(
            self.root,
            text="Made by Nurul Islam Hridoy",
            foreground="#9ca3af",
            background=self.colors["BG"],
            font=("Segoe UI", 9)
        )
        credit.pack(side="right", anchor="s", padx=10, pady=6)

    # ---------- Persistence ----------
    def _load_links(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f).get("links", [])
            seen = set()
            for l in raw:
                try:
                    ip = l["ip"]
                    if ip in seen or not is_valid_ipv4(ip):
                        continue
                    seen.add(ip)
                    self.links.append(Link(**l))
                except Exception:
                    continue
        self._ensure_state()

    def _save_links(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"links": [asdict(l) for l in self.links]}, f, indent=2)

    def export_links(self):
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"links": [asdict(l) for l in self.links]}, f, indent=2)

    def import_links(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            self.links = [Link(**l) for l in json.load(f).get("links", [])]
        self.state = {}
        self._save_links()
        self._ensure_state()

    # ---------- Link CRUD ----------
    def add_link(self):
        self._link_dialog()

    def edit_link(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Edit", "Select a link first")
            return
        ip = sel[0]
        link = next((l for l in self.links if l.ip == ip), None)
        if link:
            self._link_dialog(link)

    def _link_dialog(self, link=None):
        win = tk.Toplevel(self.root)
        win.title("Edit Link" if link else "Add Link")
        win.resizable(False, False)
        win.grab_set()

        name = tk.StringVar(value=link.name if link else "")
        ip = tk.StringVar(value=link.ip if link else "")
        group = tk.StringVar(value=link.group if link else "")
        notify = tk.BooleanVar(value=link.notify_enabled if link else True)
        down_after = tk.IntVar(value=link.down_notify_after_sec if link else 0)

        ttk.Label(win, text="Name").grid(row=0, column=0, padx=8, pady=6, sticky="w")
        ttk.Entry(win, textvariable=name, width=34).grid(row=0, column=1, padx=8, pady=6)

        ttk.Label(win, text="IP").grid(row=1, column=0, padx=8, pady=6, sticky="w")
        eip = ttk.Entry(win, textvariable=ip, width=34)
        eip.grid(row=1, column=1, padx=8, pady=6)
        if link:
            eip.configure(state="disabled")

        ttk.Label(win, text="Group").grid(row=2, column=0, padx=8, pady=6, sticky="w")
        ttk.Entry(win, textvariable=group, width=34).grid(row=2, column=1, padx=8, pady=6)

        ttk.Label(win, text="Notify").grid(row=3, column=0, padx=8, pady=6, sticky="w")
        ttk.Checkbutton(win, variable=notify).grid(row=3, column=1, sticky="w", padx=8)

        ttk.Label(win, text="Down after (sec, 0=global)").grid(row=4, column=0, padx=8, pady=6, sticky="w")
        ttk.Spinbox(win, from_=0, to=600, textvariable=down_after, width=10).grid(row=4, column=1, sticky="w", padx=8)

        def save():
            if not name.get().strip():
                messagebox.showerror("Error", "Name required")
                return
            if not is_valid_ipv4(ip.get()):
                messagebox.showerror("Error", "Invalid IPv4")
                return

            if link:
                link.name = name.get().strip()
                link.group = group.get().strip()
                link.notify_enabled = bool(notify.get())
                link.down_notify_after_sec = int(down_after.get() or 0)
            else:
                if any(x.ip == ip.get() for x in self.links):
                    messagebox.showerror("Error", "IP already exists")
                    return
                self.links.append(Link(
                    name=name.get().strip(),
                    ip=ip.get().strip(),
                    group=group.get().strip(),
                    notify_enabled=bool(notify.get()),
                    down_notify_after_sec=int(down_after.get() or 0)
                ))
                self.state.setdefault(ip.get(), {"status": "UNKNOWN", "down": None, "notified": False})

            self._save_links()
            self._ensure_state()
            self.refresh()
            win.destroy()

        ttk.Button(win, text="Save", command=save).grid(row=5, column=1, padx=8, pady=10, sticky="e")

    def remove_link(self):
        sel = self.tree.selection()
        if not sel:
            return
        ip = sel[0]
        if not messagebox.askyesno("Confirm", f"Remove {ip}?"):
            return
        self.links = [l for l in self.links if l.ip != ip]
        self.state.pop(ip, None)
        self._save_links()
        self.refresh()

    # ---------- Monitoring ----------
    def _ensure_state(self):
        for l in self.links:
            self.state.setdefault(l.ip, {"status": "UNKNOWN", "down": None, "notified": False})

    def _start_polling(self):
        threading.Thread(target=self._poll_loop, daemon=True).start()

    def _poll_loop(self):
        while True:
            interval = max(2, int(self.interval.get() or DEFAULT_INTERVAL_SEC))
            global_th = max(1, int(self.global_down_after.get() or DEFAULT_DOWN_NOTIFY_AFTER_SEC))

            for l in list(self.links):
                st = self.state.setdefault(l.ip, {"status": "UNKNOWN", "down": None, "notified": False})
                ok = ping_once(l.ip)
                now = datetime.now()

                threshold = l.down_notify_after_sec if l.down_notify_after_sec > 0 else global_th

                if ok:
                    st.update({"status": "UP", "down": None, "notified": False})
                else:
                    if st["down"] is None:
                        st["down"] = now
                    st["status"] = "DOWN"
                    if l.notify_enabled and not st["notified"] and (now - st["down"]).total_seconds() >= threshold:
                        st["notified"] = True
                        try:
                            self.root.after(0, lambda: self.root.bell())
                        except Exception:
                            pass

            time.sleep(interval)

    # ---------- UI Refresh ----------
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        now = datetime.now()
        s = (self.search_text.get() or "").strip().lower()

        for l in self.links:
            if s and s not in f"{l.name} {l.ip} {l.group}".lower():
                continue

            st = self.state.get(l.ip, {"status": "UNKNOWN", "down": None})
            down = st["down"]
            eff = l.down_notify_after_sec if l.down_notify_after_sec > 0 else self.global_down_after.get()

            vals = (
                l.name,
                l.ip,
                (l.group or "-"),
                ("ON" if l.notify_enabled else "OFF"),
                f"{eff}s",
                st["status"],
                fmt_dt(down),
                fmt_dur((now - down).total_seconds()) if down else "-"
            )
            self.tree.insert("", "end", iid=l.ip, values=vals,
                             tags=("down" if st["status"] == "DOWN" else "up",))

    def _ui_tick(self):
        self.refresh()
        self.root.after(1000, self._ui_tick)

    def on_close(self):
        self.root.destroy()


# ---------------- Main ----------------
def main():
    root = tk.Tk()
    colors = apply_soft_dark(root)
    LinkMonitorApp(root, colors)
    root.mainloop()


if __name__ == "__main__":
    main()