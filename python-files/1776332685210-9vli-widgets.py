import customtkinter as ctk
from config import (BG_DARK, BG_PANEL, BG_CARD, BG_CARD2, ACCENT, ACCENT2,
                    SUCCESS, WARNING, DANGER, TEXT_PRIMARY, TEXT_MUTED, BORDER,
                    SIDEBAR_W, state)

SIDEBAR_ITEMS = [
    "Logs",
    "Database Queries",
    "Password Vault",
    "Mock & Sim Activation",
    "Invoice Pregeneration",
    "Consumption",
    "Sim Deletion",
    "Log Analysis",
]

# ─── Widget helpers ───────────────────────────────────────────────
def lbl(parent, text, size=13, weight="normal", color=TEXT_PRIMARY, **kw):
    return ctk.CTkLabel(parent, text=text, font=("Segoe UI", size, weight),
                        text_color=color, **kw)

def card(parent, **kw):
    d = dict(fg_color=BG_CARD, corner_radius=12, border_color=BORDER, border_width=1)
    d.update(kw)
    return ctk.CTkFrame(parent, **d)

def btn(parent, text, cmd, fg=ACCENT, hover=ACCENT2, tc="#000000", w=160, h=40, **kw):
    return ctk.CTkButton(parent, text=text, command=cmd,
                         fg_color=fg, hover_color=hover, text_color=tc,
                         font=("Segoe UI", 12, "bold"), corner_radius=8,
                         width=w, height=h, **kw)

def inp(parent, ph="", w=260, show="", **kw):
    return ctk.CTkEntry(parent, placeholder_text=ph, show=show,
                        fg_color=BG_CARD2, border_color=BORDER,
                        text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_MUTED,
                        font=("Segoe UI", 12), width=w, height=36, **kw)

def hsep(parent):
    ctk.CTkFrame(parent, height=1, fg_color=BORDER).pack(fill="x", pady=6)

def badge(parent, text, color=ACCENT):
    f = ctk.CTkFrame(parent, fg_color=BG_CARD2, corner_radius=6,
                     border_color=color, border_width=1)
    ctk.CTkLabel(f, text=text, font=("Segoe UI", 10, "bold"),
                 text_color=color).pack(padx=8, pady=2)
    return f


# ══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════
class Sidebar(ctk.CTkFrame):
    def __init__(self, master, items, active=None, on_select=None, on_back=None, on_config=None):
        super().__init__(master, width=SIDEBAR_W, fg_color=BG_PANEL, corner_radius=0)
        self.pack_propagate(False)
        self.on_select = on_select

        # Header
        hdr = ctk.CTkFrame(self, fg_color=ACCENT, corner_radius=0, height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="MONTOOL", font=("Courier New", 14, "bold"),
                     text_color="#000").pack(expand=True)

        # State badges
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(fill="x", padx=10, pady=6)
        if state.project:
            badge(bf, state.project, color=WARNING).pack(fill="x", pady=2)
        if state.env:
            badge(bf, state.env, color=SUCCESS).pack(fill="x", pady=2)

        hsep(self)

        # Menu buttons
        self.btns = {}
        for item in items:
            b = ctk.CTkButton(
                self, text=item, anchor="w",
                fg_color=BG_CARD2 if item == active else "transparent",
                hover_color=BG_CARD,
                text_color=ACCENT if item == active else TEXT_PRIMARY,
                font=("Segoe UI", 12, "bold" if item == active else "normal"),
                corner_radius=6, height=38,
                command=lambda i=item: self._sel(i)
            )
            b.pack(fill="x", padx=8, pady=2)
            self.btns[item] = b

        # Bottom controls
        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.pack(side="bottom", fill="x", padx=8, pady=10)
        if getattr(state, "evidence_panel_opener", None):
            ctk.CTkButton(
                bot,
                text="📷  Evidence",
                fg_color=BG_CARD2,
                hover_color=BG_CARD,
                text_color=ACCENT,
                font=("Segoe UI", 11, "bold"),
                corner_radius=6,
                height=32,
                command=state.evidence_panel_opener,
            ).pack(fill="x", pady=2)
        if on_config:
            ctk.CTkButton(bot, text="⚙  Config", fg_color=BG_CARD2, hover_color=BG_CARD,
                          text_color=TEXT_MUTED, font=("Segoe UI", 11), corner_radius=6,
                          height=32, command=on_config).pack(fill="x", pady=2)
        if on_back:
            ctk.CTkButton(bot, text="← Back", fg_color="transparent", hover_color=BG_CARD,
                          text_color=TEXT_MUTED, font=("Segoe UI", 11), corner_radius=6,
                          height=32, command=on_back).pack(fill="x", pady=2)

    def _sel(self, item):
        for k, b in self.btns.items():
            active = k == item
            b.configure(fg_color=BG_CARD2 if active else "transparent",
                        text_color=ACCENT if active else TEXT_PRIMARY,
                        font=("Segoe UI", 12, "bold" if active else "normal"))
        if self.on_select:
            self.on_select(item)


# ══════════════════════════════════════════════════════════════════
#  CENTERED CONTAINER helper (replaces place())
# ══════════════════════════════════════════════════════════════════
def centered(parent):
    """Returns a centered column frame using pure pack — works on Windows."""
    outer = ctk.CTkFrame(parent, fg_color="transparent")
    outer.pack(fill="both", expand=True)
    outer.columnconfigure(0, weight=1)
    outer.rowconfigure(0, weight=1)
    inner = ctk.CTkFrame(outer, fg_color="transparent")
    inner.grid(row=0, column=0)
    return outer, inner

