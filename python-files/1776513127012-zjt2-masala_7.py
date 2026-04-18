import tkinter as tk
from tkinter import messagebox, font
import math

# ─── Ranglar ───────────────────────────────────────────────
BG       = "#12082a"
CARD     = "#1e1040"
ACCENT   = "#a78bfa"
ACCENT2  = "#f472b6"
TEXT     = "#f1f5f9"
SUBTEXT  = "#94a3b8"
ENTRY_BG = "#2d1b69"
BORDER   = "#4c1d95"

def hisobla():
    try:
        r = float(entry_r.get())
        if r <= 0:
            messagebox.showerror("Xato", "Radius musbat bo'lishi kerak!")
            return

        # Lug'at
        aylana = {"radius": r}

        # Yuza
        yuza = math.pi * aylana["radius"] ** 2

        result_var.set(f"{yuza:.4f}")
        lugat_var.set(f'{{"radius": {r}}}')
        pi_var.set(f"π × {r}² = π × {r*r:.4f}")
        animate_result()

    except ValueError:
        messagebox.showerror("Xato", "Iltimos, raqam kiriting!")

def animate_result():
    for i, c in enumerate([ACCENT2, ACCENT, TEXT]):
        root.after(i * 120, lambda col=c: result_label.config(fg=col))

def clear_all():
    entry_r.delete(0, tk.END)
    result_var.set("—")
    lugat_var.set("—")
    pi_var.set("—")

# ─── Asosiy oyna ───────────────────────────────────────────
root = tk.Tk()
root.title("Masala 7 — Aylana Yuzasi")
root.geometry("460x540")
root.resizable(False, False)
root.configure(bg=BG)

title_font  = font.Font(family="Courier New", size=14, weight="bold")
label_font  = font.Font(family="Courier New", size=10)
entry_font  = font.Font(family="Courier New", size=14)
result_font = font.Font(family="Courier New", size=30, weight="bold")
small_font  = font.Font(family="Courier New", size=9)
formula_font= font.Font(family="Courier New", size=10, slant="italic")

# ─── Header ────────────────────────────────────────────────
tk.Frame(root, bg=ACCENT, height=5).pack(fill="x")

# Aylana rasm (canvas)
canvas = tk.Canvas(root, bg=BG, width=460, height=90, highlightthickness=0)
canvas.pack()
cx, cy, cr = 230, 50, 38
canvas.create_oval(cx-cr, cy-cr, cx+cr, cy+cr,
                   outline=ACCENT, width=2, fill="")
canvas.create_oval(cx-cr*0.6, cy-cr*0.6, cx+cr*0.6, cy+cr*0.6,
                   outline=ACCENT2, width=1, fill="", dash=(4,4))
canvas.create_line(cx, cy, cx+cr, cy, fill=ACCENT2, width=2)
canvas.create_text(cx+cr//2, cy-12, text="r", fill=ACCENT2,
                   font=formula_font)
canvas.create_text(230, 83, text="● AYLANA YUZASI ●",
                   fill=ACCENT, font=title_font)

tk.Label(root, text="Masala 7 | Lug'at yordamida S = π·r² hisoblash",
         bg=BG, fg=SUBTEXT, font=small_font).pack()

# ─── Karta ─────────────────────────────────────────────────
card = tk.Frame(root, bg=CARD, bd=0, pady=18, padx=30,
                highlightthickness=1, highlightbackground=BORDER)
card.pack(fill="both", expand=True, padx=25, pady=14)

row = tk.Frame(card, bg=CARD)
row.pack(fill="x", pady=8)
tk.Label(row, text="Radius (r) :", bg=CARD, fg=SUBTEXT,
         font=label_font, width=14, anchor="w").pack(side="left")
entry_r = tk.Entry(row, bg=ENTRY_BG, fg=TEXT, font=entry_font,
                   insertbackground=ACCENT, relief="flat",
                   highlightthickness=1, highlightbackground=BORDER,
                   width=12)
entry_r.pack(side="left", ipady=7)

tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=10)

# Formula
tk.Label(card, text="Formula: S = π × r²",
         bg=CARD, fg=SUBTEXT, font=formula_font, anchor="w").pack(fill="x")
pi_var = tk.StringVar(value="—")
tk.Label(card, textvariable=pi_var, bg=ENTRY_BG, fg=ACCENT2,
         font=small_font, anchor="w", padx=8, pady=5).pack(fill="x", pady=4)

# Lug'at
tk.Label(card, text="Lug'at:", bg=CARD, fg=SUBTEXT,
         font=label_font, anchor="w").pack(fill="x", pady=(6,0))
lugat_var = tk.StringVar(value="—")
tk.Label(card, textvariable=lugat_var, bg=ENTRY_BG, fg=ACCENT,
         font=small_font, anchor="w", padx=8, pady=5).pack(fill="x", pady=2)

# Natija
tk.Label(card, text="Yuza (S):", bg=CARD, fg=SUBTEXT,
         font=label_font, anchor="w").pack(fill="x", pady=(10,0))
result_var = tk.StringVar(value="—")
result_label = tk.Label(card, textvariable=result_var, bg=CARD,
                        fg=TEXT, font=result_font)
result_label.pack()

# ─── Tugmalar ──────────────────────────────────────────────
btn_frame = tk.Frame(root, bg=BG)
btn_frame.pack(pady=6)

tk.Button(btn_frame, text="  HISOBLA  ", bg=ACCENT, fg="#12082a",
          font=title_font, relief="flat", padx=20, pady=9,
          cursor="hand2", command=hisobla).pack(side="left", padx=6)

tk.Button(btn_frame, text="  TOZALA  ", bg=ENTRY_BG, fg=SUBTEXT,
          font=label_font, relief="flat", padx=16, pady=9,
          cursor="hand2", command=clear_all).pack(side="left", padx=6)

tk.Label(root, text="© PDT Amaliy Mashg'ulot | Masala 7",
         bg=BG, fg=BORDER, font=small_font).pack(pady=6)

root.mainloop()
