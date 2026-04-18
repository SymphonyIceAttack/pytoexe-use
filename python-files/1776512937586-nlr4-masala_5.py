import tkinter as tk
from tkinter import messagebox, font

# ─── Ranglar va stil ───────────────────────────────────────
BG        = "#0f1923"
CARD      = "#1a2637"
ACCENT    = "#00c9a7"
ACCENT2   = "#ff6b6b"
TEXT      = "#e8f0fe"
SUBTEXT   = "#8899aa"
ENTRY_BG  = "#243040"
BORDER    = "#2e4060"

def hisobla():
    try:
        a = float(entry_a.get())
        b = float(entry_b.get())
        c = float(entry_c.get())

        if a <= 0 or b <= 0 or c <= 0:
            messagebox.showerror("Xato", "Tomonlar musbat son bo'lishi kerak!")
            return

        # Lug'at
        uchburchak = {"a": a, "b": b, "c": c}

        # Perimetr
        perimetr = uchburchak["a"] + uchburchak["b"] + uchburchak["c"]

        # Natijani ko'rsatish
        result_var.set(f"{perimetr:.2f}")
        lugat_var.set(f'{{"a": {a}, "b": {b}, "c": {c}}}')
        animate_result()

    except ValueError:
        messagebox.showerror("Xato", "Iltimos, raqam kiriting!")

def animate_result():
    result_label.config(fg=ACCENT)
    root.after(300, lambda: result_label.config(fg=TEXT))

def clear_all():
    entry_a.delete(0, tk.END)
    entry_b.delete(0, tk.END)
    entry_c.delete(0, tk.END)
    result_var.set("—")
    lugat_var.set("—")

# ─── Asosiy oyna ───────────────────────────────────────────
root = tk.Tk()
root.title("Masala 5 — Uchburchak Perimetri")
root.geometry("480x540")
root.resizable(False, False)
root.configure(bg=BG)

# Font
title_font   = font.Font(family="Courier New", size=15, weight="bold")
label_font   = font.Font(family="Courier New", size=10)
entry_font   = font.Font(family="Courier New", size=13)
result_font  = font.Font(family="Courier New", size=28, weight="bold")
small_font   = font.Font(family="Courier New", size=9)

# ─── Header ────────────────────────────────────────────────
header = tk.Frame(root, bg=ACCENT, height=5)
header.pack(fill="x")

tk.Label(root, text="▲  UCHBURCHAK  ▲", bg=BG, fg=ACCENT,
         font=title_font, pady=18).pack()

tk.Label(root, text="Masala 5 | Lug'at yordamida perimetr hisoblash",
         bg=BG, fg=SUBTEXT, font=small_font).pack()

# ─── Karta ─────────────────────────────────────────────────
card = tk.Frame(root, bg=CARD, bd=0, pady=20, padx=30,
                highlightthickness=1, highlightbackground=BORDER)
card.pack(fill="both", expand=True, padx=25, pady=18)

def make_row(parent, label_text, var=None):
    row = tk.Frame(parent, bg=CARD)
    row.pack(fill="x", pady=6)
    tk.Label(row, text=label_text, bg=CARD, fg=SUBTEXT,
             font=label_font, width=18, anchor="w").pack(side="left")
    e = tk.Entry(row, bg=ENTRY_BG, fg=TEXT, font=entry_font,
                 insertbackground=ACCENT, relief="flat",
                 highlightthickness=1, highlightbackground=BORDER,
                 width=10)
    e.pack(side="left", ipady=6, padx=(0, 4))
    return e

entry_a = make_row(card, "Tomon a :")
entry_b = make_row(card, "Tomon b :")
entry_c = make_row(card, "Tomon c :")

# Separator
tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=12)

# Lug'at ko'rinishi
tk.Label(card, text="Lug'at:", bg=CARD, fg=SUBTEXT, font=label_font,
         anchor="w").pack(fill="x")
lugat_var = tk.StringVar(value="—")
tk.Label(card, textvariable=lugat_var, bg=ENTRY_BG, fg=ACCENT2,
         font=small_font, anchor="w", padx=8, pady=6,
         relief="flat", wraplength=380).pack(fill="x", pady=4)

# Natija
tk.Label(card, text="Perimetr:", bg=CARD, fg=SUBTEXT,
         font=label_font, anchor="w").pack(fill="x", pady=(10, 0))
result_var = tk.StringVar(value="—")
result_label = tk.Label(card, textvariable=result_var, bg=CARD,
                        fg=TEXT, font=result_font)
result_label.pack()

# ─── Tugmalar ──────────────────────────────────────────────
btn_frame = tk.Frame(root, bg=BG)
btn_frame.pack(pady=4)

tk.Button(btn_frame, text="  HISOBLA  ", bg=ACCENT, fg="#0f1923",
          font=title_font, relief="flat", padx=20, pady=10,
          cursor="hand2", command=hisobla).pack(side="left", padx=6)

tk.Button(btn_frame, text="  TOZALA  ", bg=ENTRY_BG, fg=SUBTEXT,
          font=label_font, relief="flat", padx=16, pady=10,
          cursor="hand2", command=clear_all).pack(side="left", padx=6)

tk.Label(root, text="© PDT Amaliy Mashg'ulot | Masala 5",
         bg=BG, fg=BORDER, font=small_font).pack(pady=8)

root.mainloop()
