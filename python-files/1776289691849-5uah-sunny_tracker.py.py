"""
SUNNY'S MC NAME TRACKER
pip install requests
"""

import sys, subprocess
try:
    import requests
except ImportError:
    print("[*] Installing requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

import tkinter as tk
import threading, time, random, string, itertools, queue
from datetime import datetime, timezone

BG      = "#0a0a0a"
CARD    = "#111111"
CARD2   = "#0d0d0d"
INDIGO  = "#6366f1"   # available highlight
INDIGO2 = "#818cf8"   # available lighter
BLUE    = "#00ccff"   # random name colour
RED_C   = "#ff4455"   # clean name colour
DIM     = "#2a2a2a"
FG      = "#dddddd"
FGDIM   = "#555555"
RED     = "#ff4455"
ORANGE  = "#ffaa00"
ACCENT  = "#00ff88"
FM      = ("Consolas", 10)
FMB     = ("Consolas", 10, "bold")
FH      = ("Consolas", 13, "bold")
FBG     = ("Consolas", 19, "bold")

RAINBOW = ["#ff0000","#ff4400","#ff8800","#ffcc00","#ffff00",
           "#88ff00","#00ff88","#00ffff","#0088ff","#8800ff","#ff00ff"]

# ─── CLEAN = ALL LETTERS, NO DIGITS ───────────────────────────────────────────
def is_clean(name):
    return name.isalpha()

# ─── NAME POOLS ───────────────────────────────────────────────────────────────
_alnum = string.ascii_lowercase + string.digits
_alpha = string.ascii_lowercase

# Clean pool = all-letter names
ALL_3_CLEAN = [''.join(c) for c in itertools.product(_alpha, repeat=3)]
ALL_4_CLEAN = [''.join(c) for c in itertools.product(_alpha, repeat=4)]

# Random pool = names with at least one digit
ALL_3_RAND  = [''.join(c) for c in itertools.product(_alnum, repeat=3) if not all(x.isalpha() for x in c)]
ALL_4_RAND  = [''.join(c) for c in itertools.product(_alnum, repeat=4) if c[0].isalpha() and not all(x.isalpha() for x in c)]

for pool in [ALL_3_CLEAN, ALL_4_CLEAN, ALL_3_RAND, ALL_4_RAND]:
    random.shuffle(pool)

_ic3, _ic4, _ir3, _ir4 = [0],[0],[0],[0]

def next_name(lengths):
    # Alternate between clean and random pools
    use_clean = random.random() < 0.5
    use_3     = 3 in lengths and (4 not in lengths or random.random() < 0.5)
    if use_3:
        pool, idx = (ALL_3_CLEAN, _ic3) if use_clean else (ALL_3_RAND, _ir3)
    else:
        pool, idx = (ALL_4_CLEAN, _ic4) if use_clean else (ALL_4_RAND, _ir4)
    name = pool[idx[0] % len(pool)]
    idx[0] += 1
    return name

# ─── MOJANG API ───────────────────────────────────────────────────────────────
SINGLE_URL  = "https://api.mojang.com/users/profiles/minecraft/{}"
PROFILE_URL = "https://sessionserver.mojang.com/session/minecraft/profile/{}"
HDR = {"User-Agent": "SunnysMCTracker/1.0"}

def check_name(name):
    """Returns (status, release_date_str)
       status: 'available' | 'taken' | 'ratelimit' | 'error'
       release_date_str: date string or None
    """
    try:
        r = requests.get(SINGLE_URL.format(name), headers=HDR, timeout=5)
        if r.status_code == 404:
            return "available", None
        if r.status_code == 204:
            return "available", None
        if r.status_code == 429:
            return "ratelimit", None
        if r.status_code == 200:
            # Name is taken — try to get when it was last changed
            # (Mojang removed name history; we show last_seen approximation)
            try:
                data = r.json()
                uuid = data.get("id", "")
                # Try to get profile for more info
                # We'll just note it as taken with no release date
            except Exception:
                pass
            return "taken", None
        return "error", None
    except Exception:
        return "error", None

def get_release_date(name):
    """
    Try laby.net API to get the date this name becomes available.
    Returns a formatted date string or None.
    """
    try:
        r = requests.get(
            f"https://laby.net/api/search/names/{name}",
            headers={**HDR, "Referer": "https://laby.net/names"},
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            # Look for available_at or similar field in results
            if isinstance(data, list):
                for item in data:
                    n = item.get("user_name","") or item.get("name","")
                    if n.lower() == name.lower():
                        avail = item.get("available_at") or item.get("available_from")
                        if avail:
                            try:
                                dt = datetime.fromisoformat(avail.replace("Z","+00:00"))
                                return dt.strftime("%m/%d/%Y %I:%M %p")
                            except Exception:
                                return avail
            if isinstance(data, dict):
                avail = data.get("available_at") or data.get("available_from")
                if avail:
                    try:
                        dt = datetime.fromisoformat(avail.replace("Z","+00:00"))
                        return dt.strftime("%m/%d/%Y %I:%M %p")
                    except Exception:
                        return avail
    except Exception:
        pass
    return None

# ─── APP ──────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SUNNY'S MC NAME TRACKER")
        self.configure(bg=BG)
        self.geometry("960x640")
        self.minsize(760, 480)

        # Praying hands red emoji as window icon via wm_iconphoto
        try:
            # Create a simple PhotoImage with a skull character — tkinter limitation
            # We'll set the title bar icon using iconphoto with a generated image
            img = tk.PhotoImage(width=32, height=32)
            # Fill with dark background and draw simple skull shape
            img.put("#0a0a0a", to=(0, 0, 32, 32))
            self.iconphoto(True, img)
        except Exception:
            pass

        self.scanning     = False
        self.results      = {}
        self.lengths      = {3, 4}
        self.filter_txt   = tk.StringVar()
        self.filter_txt.trace_add("write", lambda *_: self._redraw())
        self._total       = 0
        self._avail       = 0
        self._rainbow_idx = 0
        self._q           = queue.Queue()

        self._build()
        self._process_queue()
        self._animate_rainbow()
        self._toggle_scan()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG, pady=12, padx=20)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🙏🏻", font=("Segoe UI Emoji", 20), bg=BG, fg=RED).pack(side="left", padx=(0,10))
        tk.Label(hdr, text="SUNNY'S MC NAME TRACKER", font=FBG, fg=INDIGO2, bg=BG).pack(side="left")
        self._scan_btn = tk.Button(hdr, text="⏹  STOP", font=FM,
                                   bg=RED, fg=BG, activebackground="#cc2233", activeforeground=BG,
                                   bd=0, padx=14, pady=6, cursor="hand2", command=self._toggle_scan)
        self._scan_btn.pack(side="right")
        self._status_lbl = tk.Label(hdr, text="starting…", font=FM, fg=FGDIM, bg=BG)
        self._status_lbl.pack(side="right", padx=14)

        # Stats
        stats = tk.Frame(self, bg=CARD, pady=10, padx=20)
        stats.pack(fill="x")
        self._checked_var = tk.StringVar(value="Checked: 0")
        self._avail_var   = tk.StringVar(value="Available: 0")
        tk.Label(stats, textvariable=self._checked_var, font=FM,  fg=FGDIM,  bg=CARD).pack(side="left", padx=(0,20))
        tk.Label(stats, textvariable=self._avail_var,   font=FMB, fg=INDIGO2, bg=CARD).pack(side="left", padx=(0,16))
        self._rainbow_frame = tk.Frame(stats, bg=CARD)
        self._rainbow_frame.pack(side="left")
        self._rainbow_labels = []
        self._build_rainbow("(0.0% hit rate)")

        # Legend
        leg = tk.Frame(stats, bg=CARD)
        leg.pack(side="right")
        tk.Label(leg, text="★ CLEAN",  font=("Consolas",9,"bold"), fg=RED_C, bg=CARD).pack(side="right", padx=8)
        tk.Label(leg, text="◆ RANDOM", font=("Consolas",9),        fg=BLUE,  bg=CARD).pack(side="right", padx=8)
        tk.Label(leg, text="● AVAIL",  font=("Consolas",9,"bold"), fg=INDIGO2,bg=CARD).pack(side="right", padx=8)

        # Filters
        frow = tk.Frame(self, bg=BG, pady=10, padx=20)
        frow.pack(fill="x")
        tk.Label(frow, text="FILTER:", font=FM, fg=FGDIM, bg=BG).pack(side="left")
        tk.Entry(frow, textvariable=self.filter_txt, font=FM,
                 bg=CARD, fg=INDIGO2, insertbackground=INDIGO2,
                 bd=0, relief="flat", width=16).pack(side="left", padx=8)
        tk.Label(frow, text="LENGTH:", font=FM, fg=FGDIM, bg=BG).pack(side="left", padx=(20,6))
        self._btn3  = self._mkbtn(frow, " 3 ",   lambda: self._tog_len(3))
        self._btn4  = self._mkbtn(frow, " 4 ",   lambda: self._tog_len(4))
        self._btn34 = self._mkbtn(frow, " 3+4 ", self._set_both)
        self._refresh_len_btns()
        tk.Button(frow, text="CLEAR", font=FM, bg=CARD, fg=RED,
                  bd=0, padx=10, pady=4, cursor="hand2", command=self._clear).pack(side="right")

        # Column headers
        ch = tk.Frame(self, bg=BG, padx=20, pady=4)
        ch.pack(fill="x")
        for txt, w in [("NAME",10),("TYPE",9),("STATUS",14),("RELEASE DATE",24),("LEN",5),("ACTIONS",16)]:
            tk.Label(ch, text=txt, font=FM, fg=FGDIM, bg=BG, width=w, anchor="w").pack(side="left")
        tk.Frame(self, bg=DIM, height=1).pack(fill="x", padx=20)

        # Scrollable list
        wrap = tk.Frame(self, bg=BG)
        wrap.pack(fill="both", expand=True, padx=20, pady=(4,0))
        self._canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(wrap, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self._list = tk.Frame(self._canvas, bg=BG)
        self._win  = self._canvas.create_window((0,0), window=self._list, anchor="nw")
        self._list.bind("<Configure>",
                        lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
                          lambda e: self._canvas.itemconfig(self._win, width=e.width))
        self.bind_all("<MouseWheel>",
                      lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units"))

        # Statusbar
        sbar = tk.Frame(self, bg=CARD, pady=6, padx=20)
        sbar.pack(fill="x", side="bottom")
        self._sbar_var = tk.StringVar(value="Ready.")
        tk.Label(sbar, textvariable=self._sbar_var, font=FM, fg=FGDIM, bg=CARD, anchor="w").pack(side="left")

        tk.Label(self._list, text="\n  Scanning… available names will appear here.",
                 font=FM, fg=FGDIM, bg=BG).pack(anchor="w", pady=20)

    def _build_rainbow(self, text):
        for w in self._rainbow_frame.winfo_children():
            w.destroy()
        self._rainbow_labels = []
        for ch in text:
            lbl = tk.Label(self._rainbow_frame, text=ch, font=FMB, bg=CARD, fg=RAINBOW[0])
            lbl.pack(side="left")
            self._rainbow_labels.append(lbl)

    def _animate_rainbow(self):
        for i, lbl in enumerate(self._rainbow_labels):
            lbl.config(fg=RAINBOW[(self._rainbow_idx + i) % len(RAINBOW)])
        self._rainbow_idx = (self._rainbow_idx + 1) % len(RAINBOW)
        self.after(80, self._animate_rainbow)

    def _mkbtn(self, parent, label, cmd):
        b = tk.Button(parent, text=label, font=FM, bg=DIM, fg=FG,
                      bd=0, padx=8, pady=4, cursor="hand2", command=cmd)
        b.pack(side="left", padx=2)
        return b

    def _tog_len(self, n):
        if n in self.lengths and len(self.lengths) > 1:
            self.lengths.discard(n)
        else:
            self.lengths.add(n)
        self._refresh_len_btns()
        self._redraw()

    def _set_both(self):
        self.lengths = {3, 4}
        self._refresh_len_btns()
        self._redraw()

    def _refresh_len_btns(self):
        self._btn3.config( bg=INDIGO if 3 in self.lengths else DIM, fg=FG if 3 in self.lengths else FG)
        self._btn4.config( bg=INDIGO if 4 in self.lengths else DIM, fg=FG)
        self._btn34.config(bg=INDIGO if self.lengths=={3,4} else DIM, fg=FG)

    def _clear(self):
        self.results = {}; self._total = 0; self._avail = 0
        self._update_stats(); self._redraw()

    # ─── SCAN ─────────────────────────────────────────────────────────────────
    def _toggle_scan(self):
        if self.scanning:
            self.scanning = False
            self._scan_btn.config(text="▶  START", bg=INDIGO, fg=FG)
            self._status_lbl.config(text="paused")
        else:
            self.scanning = True
            self._scan_btn.config(text="⏹  STOP", bg=RED, fg=BG)
            self._status_lbl.config(text="scanning…")
            for _ in range(5):
                threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        while self.scanning:
            name = next_name(self.lengths)
            if len(name) not in self.lengths:
                continue
            status, _ = check_name(name)
            if status == "ratelimit":
                time.sleep(5); continue
            if status == "error":
                time.sleep(0.5); continue

            # If available, try to fetch release date from laby.net
            release_date = None
            if status == "available":
                release_date = get_release_date(name)

            now = datetime.now().strftime("%H:%M:%S")
            self._q.put((name, status, release_date, now))
            time.sleep(0.3)

    def _process_queue(self):
        changed = False
        try:
            for _ in range(20):
                name, status, release_date, checked_at = self._q.get_nowait()
                self._total += 1
                if status == "available":
                    self._avail += 1
                self.results[name] = {
                    "status":       status,
                    "at":           checked_at,
                    "clean":        is_clean(name),
                    "release_date": release_date,
                }
                changed = True
        except queue.Empty:
            pass
        if changed:
            self._update_stats()
            self._redraw()
            self._status_lbl.config(text=f"scanning… {datetime.now().strftime('%H:%M:%S')}")
        self.after(300, self._process_queue)

    # ─── RENDER ───────────────────────────────────────────────────────────────
    def _redraw(self):
        q = self.filter_txt.get().lower().strip()
        rows = [
            (n, d) for n, d in self.results.items()
            if len(n) in self.lengths and (not q or q in n.lower())
        ]
        rows.sort(key=lambda x: (
            0 if x[1]["status"] == "available" else 1,
            0 if x[1]["clean"] else 1,
            x[0]
        ))
        for w in self._list.winfo_children():
            w.destroy()
        if not rows:
            tk.Label(self._list, text="\n  Scanning… available names will appear here.",
                     font=FM, fg=FGDIM, bg=BG).pack(anchor="w", pady=20)
            return
        for i, (name, data) in enumerate(rows):
            self._row(i, name, data)

    def _row(self, idx, name, data):
        status       = data["status"]
        clean        = data["clean"]
        release_date = data.get("release_date")
        bg = CARD if idx % 2 == 0 else CARD2

        # Colour logic:
        # available → indigo (both clean and random)
        # taken clean → red
        # taken random → blue
        if status == "available":
            nc = INDIGO2
        else:
            nc = RED_C if clean else BLUE

        f = tk.Frame(self._list, bg=bg, pady=7, padx=12)
        f.pack(fill="x")
        hov_map = {
            ("available", True):  "#1a1730",
            ("available", False): "#1a1730",
            ("taken",     True):  "#1e1010",
            ("taken",     False): "#101820",
        }
        hov = hov_map.get((status, clean), "#161616")
        f.bind("<Enter>", lambda e: f.config(bg=hov))
        f.bind("<Leave>", lambda e: f.config(bg=bg))

        # Name
        tk.Label(f, text=name, font=FMB, fg=nc, bg=bg, width=10, anchor="w").pack(side="left")

        # Type
        type_txt = "★ CLEAN " if clean else "◆ RANDOM"
        type_col = RED_C if clean else FGDIM
        tk.Label(f, text=type_txt, font=("Consolas",9,"bold") if clean else ("Consolas",9),
                 fg=type_col, bg=bg, width=9, anchor="w").pack(side="left")

        # Status
        if status == "available":
            st_txt, st_col, st_fnt = "● AVAILABLE", INDIGO2, FMB
        else:
            st_txt, st_col, st_fnt = "✗  taken",    FGDIM,   FM
        tk.Label(f, text=st_txt, font=st_fnt, fg=st_col, bg=bg, width=14, anchor="w").pack(side="left")

        # Release date (or dash)
        rd_txt = release_date if release_date else "—"
        rd_col = INDIGO2 if status == "available" and release_date else (nc if status=="available" else FGDIM)
        tk.Label(f, text=rd_txt, font=FM, fg=rd_col, bg=bg, width=24, anchor="w").pack(side="left")

        # Length
        tk.Label(f, text=f"{len(name)}c", font=FM, fg=FGDIM, bg=bg, width=5, anchor="w").pack(side="left")

        # Actions
        if status == "available":
            tk.Button(f, text="VERIFY", font=("Consolas",8), bg=BG, fg=INDIGO2,
                      bd=0, padx=6, pady=2, cursor="hand2",
                      activebackground=INDIGO, activeforeground=FG,
                      command=lambda n=name: self._verify(n)).pack(side="left", padx=2)
            tk.Button(f, text="laby.net ↗", font=("Consolas",8), bg=BG, fg=BLUE,
                      bd=0, padx=6, pady=2, cursor="hand2",
                      command=lambda n=name: __import__("webbrowser").open(f"https://laby.net/@{n}")
                      ).pack(side="left", padx=2)

    # ─── HELPERS ──────────────────────────────────────────────────────────────
    def _verify(self, name):
        self._sbar_var.set(f"Re-verifying '{name}'…")
        def worker():
            r, _  = check_name(name)
            rd    = get_release_date(name) if r == "available" else None
            now   = datetime.now().strftime("%H:%M:%S")
            self.results[name] = {"status": r, "at": now, "clean": is_clean(name), "release_date": rd}
            self.after(0, self._redraw)
            self.after(0, lambda: self._popup(name, r, rd))
        threading.Thread(target=worker, daemon=True).start()

    def _popup(self, name, result, release_date=None):
        clean = is_clean(name)
        p = tk.Toplevel(self)
        p.configure(bg=BG); p.title("Verify"); p.geometry("360x200"); p.resizable(False, False)
        icon  = {"available":"✔","taken":"✘","ratelimit":"⏳"}.get(result, "?")
        color = INDIGO2 if result == "available" else (ORANGE if result == "ratelimit" else FGDIM)
        tk.Label(p, text=icon, font=("Consolas",34), fg=color, bg=BG).pack(pady=(14,2))
        tag = "  ★ CLEAN" if clean else "  ◆ random"
        tk.Label(p, text=f"'{name}'{tag}", font=FH, fg=RED_C if clean else BLUE, bg=BG).pack()
        tk.Label(p, text=f"→  {result.upper()}", font=FH, fg=color, bg=BG).pack()
        if release_date:
            tk.Label(p, text=f"releases: {release_date}", font=FM, fg=INDIGO2, bg=BG).pack()
        tk.Label(p, text="via Mojang API", font=FM, fg=FGDIM, bg=BG).pack()
        tk.Button(p, text="CLOSE", font=FM, bg=CARD, fg=FG,
                  bd=0, padx=16, pady=6, command=p.destroy).pack(pady=8)

    def _update_stats(self):
        self._checked_var.set(f"Checked: {self._total:,}")
        self._avail_var.set(f"Available: {self._avail:,}")
        pct = self._avail / self._total * 100 if self._total else 0
        self._build_rainbow(f"({pct:.1f}% hit rate)")

# ─── ENTRY ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        App().mainloop()
    except Exception:
        import traceback
        root = tk.Tk()
        root.title("CRASH"); root.configure(bg="#0a0a0a"); root.geometry("620x320")
        tk.Label(root, text="CRASH", font=("Consolas",20,"bold"), fg=RED, bg="#0a0a0a").pack(pady=10)
        txt = tk.Text(root, font=("Consolas",9), bg="#111", fg=RED, bd=0)
        txt.pack(fill="both", expand=True, padx=20)
        txt.insert("1.0", traceback.format_exc())
        tk.Button(root, text="CLOSE", command=root.destroy,
                  bg="#222", fg="white", bd=0, padx=20, pady=6).pack(pady=8)
        root.mainloop()
