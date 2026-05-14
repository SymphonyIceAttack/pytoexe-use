"""
Space Context · App
Stile ispirato a spacecontext.it — dark, minimal, tecnico.
Richiede Python 3.8+ (solo librerie standard: tkinter)
"""

import tkinter as tk
from tkinter import font as tkfont
import webbrowser
import threading
import time

# ── Palette ──────────────────────────────────────────────────────────────────
BG        = "#0e0e0e"   # sfondo principale
BG2       = "#161616"   # sfondo card
BG3       = "#1e1e1e"   # hover / bordi
ACCENT    = "#e8e0c8"   # testo principale (crema)
MUTED     = "#6b6b6b"   # testo secondario
DIM       = "#2a2a2a"   # separatori
GOLD      = "#c8a96e"   # accento dorato
GOLD_DIM  = "#3d2e14"   # sfondo badge

FONT_TITLE   = ("Courier New", 28, "bold")
FONT_LABEL   = ("Courier New", 10)
FONT_MONO    = ("Courier New", 9)
FONT_NAV     = ("Courier New", 11)
FONT_BADGE   = ("Courier New", 8)
FONT_STAT_N  = ("Courier New", 22, "bold")
FONT_STAT_L  = ("Courier New", 8)
FONT_CARD_T  = ("Courier New", 11, "bold")
FONT_CARD_D  = ("Courier New", 9)

LINKS = {
    "Software":  "https://spacecontext.it/pages/software",
    "YaibaSMP":  "https://spacecontext.it/pages/yaiba",
    "Discord":   "https://spacecontext.it/pages/discord",
    "Premium":   "https://spacecontext.it/pages/premium",
    "Contatta":  "https://spacecontext.it/pages/contatta",
}

CARDS = [
    ("⚡", "Software",  "Programmi sviluppati\ndal team Space Context."),
    ("🎮", "YaibaSMP",  "Il server Minecraft\ndella community."),
    ("💬", "Discord",   "Unisciti alla community\nper supporto e news."),
    ("✦",  "Premium",   "Sblocca tutti i contenuti\nesclusivi con Premium."),
]

STATS = [("500+", "Utenti"), ("12", "Programmi"), ("24/7", "Supporto")]

# ── Animazione titolo (glitch leggero) ───────────────────────────────────────
GLITCH_CHARS = "█▓░SPACE CONTEXT▒▓█"

class SpaceContextApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Space Context · Home")
        self.geometry("820x640")
        self.resizable(False, False)
        self.configure(bg=BG)

        self._title_glitch = False
        self._build_ui()
        self._start_ticker()

    # ── Build UI ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Navbar ──
        nav = tk.Frame(self, bg=BG, pady=0)
        nav.pack(fill="x", padx=32, pady=(20, 0))

        logo = tk.Label(nav, text="SPACE CONTEXT", font=FONT_LABEL,
                        bg=BG, fg=ACCENT, cursor="hand2")
        logo.pack(side="left")
        logo.bind("<Button-1>", lambda e: webbrowser.open("https://spacecontext.it"))

        for name, url in list(LINKS.items()):
            btn = tk.Label(nav, text=name, font=FONT_LABEL,
                           bg=BG, fg=MUTED, cursor="hand2", padx=10)
            btn.pack(side="right")
            btn.bind("<Enter>", lambda e, b=btn: b.config(fg=ACCENT))
            btn.bind("<Leave>", lambda e, b=btn: b.config(fg=MUTED))
            btn.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))

        # separator
        tk.Frame(self, bg=DIM, height=1).pack(fill="x", padx=32, pady=(12, 0))

        # ── Badge versione ──
        badge_row = tk.Frame(self, bg=BG)
        badge_row.pack(anchor="w", padx=36, pady=(24, 4))
        badge = tk.Label(badge_row, text="  v2.0 — Ora disponibile  ",
                         font=FONT_BADGE, bg=GOLD_DIM, fg=GOLD, padx=4, pady=2)
        badge.pack(side="left")

        # ── Titolo ──
        self._title_lbl = tk.Label(self, text="SPACE  CONTEXT",
                                   font=FONT_TITLE, bg=BG, fg=ACCENT)
        self._title_lbl.pack(anchor="w", padx=36, pady=(8, 4))

        # ── Sottotitolo ──
        tk.Label(self, text="Software, tool e risorse per la community.  Semplice. Veloce. Potente.",
                 font=FONT_LABEL, bg=BG, fg=MUTED).pack(anchor="w", padx=36)

        # ── CTA buttons ──
        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(anchor="w", padx=36, pady=(16, 0))
        self._make_cta(btn_row, "↓  Scarica ora",
                       "https://spacecontext.it/pages/software", primary=True)
        self._make_cta(btn_row, "✦  Abbonamento Premium",
                       "https://spacecontext.it/pages/premium", primary=False)

        # ── Stats ──
        stats_row = tk.Frame(self, bg=BG)
        stats_row.pack(anchor="w", padx=36, pady=(28, 0))
        for i, (val, lbl) in enumerate(STATS):
            cell = tk.Frame(stats_row, bg=BG)
            cell.grid(row=0, column=i*2, padx=(0, 6))
            tk.Label(cell, text=val, font=FONT_STAT_N, bg=BG, fg=ACCENT).pack()
            tk.Label(cell, text=lbl.upper(), font=FONT_STAT_L, bg=BG, fg=MUTED).pack()
            if i < len(STATS) - 1:
                tk.Label(stats_row, text="│", font=FONT_LABEL,
                         bg=BG, fg=DIM).grid(row=0, column=i*2+1, padx=12)

        # ── Divider + sezione ──
        tk.Frame(self, bg=DIM, height=1).pack(fill="x", padx=32, pady=(28, 0))
        sec = tk.Frame(self, bg=BG)
        sec.pack(fill="x", padx=36, pady=(14, 0))
        tk.Label(sec, text="// esplora", font=FONT_MONO, bg=BG, fg=GOLD).pack(side="left")

        sec2_lbl = tk.Frame(self, bg=BG)
        sec2_lbl.pack(anchor="w", padx=36, pady=(4, 2))
        tk.Label(sec2_lbl, text="Cosa trovi qui",
                 font=("Courier New", 15, "bold"), bg=BG, fg=ACCENT).pack(side="left")
        tk.Label(self, text="Tutto quello che Space Context offre, in un click.",
                 font=FONT_MONO, bg=BG, fg=MUTED).pack(anchor="w", padx=36, pady=(0, 14))

        # ── Cards ──
        cards_frame = tk.Frame(self, bg=BG)
        cards_frame.pack(fill="x", padx=32)
        for i, (icon, title, desc) in enumerate(CARDS):
            self._make_card(cards_frame, icon, title, desc, col=i)

        # ── Footer ──
        tk.Frame(self, bg=DIM, height=1).pack(fill="x", padx=32, pady=(22, 0))
        footer = tk.Frame(self, bg=BG, pady=10)
        footer.pack(fill="x", padx=36)
        tk.Label(footer,
                 text="SPACE CONTEXT · SOFTWARES  © 2026 — Tutti i diritti riservati",
                 font=FONT_MONO, bg=BG, fg=MUTED).pack(side="left")

        # ticker in basso a destra
        self._ticker_lbl = tk.Label(footer, text="", font=FONT_MONO,
                                    bg=BG, fg=GOLD)
        self._ticker_lbl.pack(side="right")

    # ── CTA button ───────────────────────────────────────────────────────────
    def _make_cta(self, parent, text, url, primary):
        if primary:
            fg, bg_c, hover_bg = BG, ACCENT, GOLD
        else:
            fg, bg_c, hover_bg = ACCENT, BG3, BG2

        btn = tk.Label(parent, text=text, font=FONT_NAV,
                       bg=bg_c, fg=fg if primary else ACCENT,
                       padx=16, pady=7, cursor="hand2", relief="flat")
        btn.pack(side="left", padx=(0, 10))

        def on_enter(e):
            btn.config(bg=hover_bg, fg=BG if primary else GOLD)
        def on_leave(e):
            btn.config(bg=bg_c, fg=fg if primary else ACCENT)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<Button-1>", lambda e: webbrowser.open(url))

    # ── Card sezione ─────────────────────────────────────────────────────────
    def _make_card(self, parent, icon, title, desc, col):
        card = tk.Frame(parent, bg=BG2, padx=16, pady=14,
                        highlightthickness=1, highlightbackground=DIM,
                        cursor="hand2")
        card.grid(row=0, column=col, padx=(0, 10), sticky="nsew")
        parent.columnconfigure(col, weight=1)

        url = LINKS.get(title, "https://spacecontext.it")

        tk.Label(card, text=icon, font=("Courier New", 16),
                 bg=BG2, fg=GOLD).pack(anchor="w")
        tk.Label(card, text=title, font=FONT_CARD_T,
                 bg=BG2, fg=ACCENT).pack(anchor="w", pady=(4, 2))
        tk.Label(card, text=desc, font=FONT_CARD_D,
                 bg=BG2, fg=MUTED, justify="left").pack(anchor="w")
        arrow = tk.Label(card, text="Vai →", font=FONT_CARD_D,
                         bg=BG2, fg=GOLD)
        arrow.pack(anchor="w", pady=(8, 0))

        def on_enter(e):
            card.config(bg=BG3, highlightbackground=GOLD_DIM)
            for w in card.winfo_children():
                w.config(bg=BG3)
        def on_leave(e):
            card.config(bg=BG2, highlightbackground=DIM)
            for w in card.winfo_children():
                w.config(bg=BG2)
        def on_click(e):
            webbrowser.open(url)

        for widget in [card] + card.winfo_children():
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

    # ── Ticker in background ─────────────────────────────────────────────────
    def _start_ticker(self):
        msgs = [
            "play.yaibasmp.cloud  ·  online",
            "v2.0  ·  nuovo aggiornamento",
            "premium  ·  sblocca tutto",
            "discord  ·  unisciti ora",
        ]
        self._ticker_msgs = msgs
        self._ticker_idx  = 0
        self._tick()

    def _tick(self):
        msg = self._ticker_msgs[self._ticker_idx]
        self._animate_ticker(msg, 0)

    def _animate_ticker(self, msg, i):
        if i <= len(msg):
            self._ticker_lbl.config(text=msg[:i] + ("▌" if i < len(msg) else ""))
            self.after(35, self._animate_ticker, msg, i + 1)
        else:
            self.after(2600, self._next_tick)

    def _next_tick(self):
        self._ticker_idx = (self._ticker_idx + 1) % len(self._ticker_msgs)
        self._clear_ticker(self._ticker_lbl.cget("text"), 0)

    def _clear_ticker(self, txt, i):
        if i <= len(txt):
            self._ticker_lbl.config(text=txt[:max(0, len(txt)-i)])
            self.after(18, self._clear_ticker, txt, i + 1)
        else:
            self.after(200, self._tick)


if __name__ == "__main__":
    app = SpaceContextApp()
    app.mainloop()
