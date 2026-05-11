import tkinter as tk
from tkinter import messagebox
import random
import webbrowser
import time

# ── barvy & font ──────────────────────────────────────────────────────────────
BG        = "#0a0a0f"
GOLD      = "#f0c040"
RED       = "#e03030"
GREEN     = "#30e060"
GREY      = "#888888"
WHITE     = "#f0f0f0"
FONT_BIG  = ("Courier New", 22, "bold")
FONT_MED  = ("Courier New", 13, "bold")
FONT_SM   = ("Courier New", 11)

RICKROLL  = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# ── hlavní okno ───────────────────────────────────────────────────────────────
root = tk.Tk()
root.title("GTA VI — Official Release")
root.geometry("700x600")
root.configure(bg=BG)
root.resizable(False, False)

# ══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════════════
hdr = tk.Frame(root, bg=BG)
hdr.pack(pady=(20, 5))

tk.Label(hdr, text="GRAND THEFT AUTO VI", font=("Courier New", 28, "bold"),
         fg=GOLD, bg=BG).pack()
tk.Label(hdr, text="▸  OFFICIAL RELEASE  ◂", font=FONT_MED,
         fg=RED, bg=BG).pack()
tk.Label(hdr, text="Vice City  •  2026  •  Rockstar Games",
         font=FONT_SM, fg=GREY, bg=BG).pack(pady=(4, 0))

separator = tk.Frame(root, height=2, bg=GOLD)
separator.pack(fill="x", padx=40, pady=10)

# ══════════════════════════════════════════════════════════════════════════════
#  MINIHRA  – Hádej číslo (1-10)
# ══════════════════════════════════════════════════════════════════════════════
game_frame = tk.Frame(root, bg=BG, bd=2, relief="ridge",
                      highlightbackground=GOLD, highlightthickness=1)
game_frame.pack(padx=40, pady=5, fill="x")

tk.Label(game_frame, text="[ MINIGAME: VICE CITY LOTTERY ]",
         font=FONT_MED, fg=GOLD, bg=BG).pack(pady=(10, 2))
tk.Label(game_frame,
         text="Uhodni tajné číslo od 1 do 10 a vyhraj Lamborghini! 🏎️",
         font=FONT_SM, fg=WHITE, bg=BG).pack()

secret_number  = [random.randint(1, 10)]
attempts_left  = [5]

status_var = tk.StringVar(value=f"Máš {attempts_left[0]} pokusů. Zadej číslo:")

tk.Label(game_frame, textvariable=status_var,
         font=FONT_SM, fg=GREY, bg=BG).pack(pady=4)

entry_var = tk.StringVar()
entry = tk.Entry(game_frame, textvariable=entry_var, font=FONT_BIG,
                 width=4, justify="center",
                 bg="#1a1a2e", fg=GOLD, insertbackground=GOLD,
                 relief="flat", bd=4)
entry.pack(pady=4)

feedback_var = tk.StringVar(value="")
feedback_lbl = tk.Label(game_frame, textvariable=feedback_var,
                        font=FONT_MED, bg=BG)
feedback_lbl.pack(pady=2)

def reset_game():
    secret_number[0]  = random.randint(1, 10)
    attempts_left[0]  = 5
    entry_var.set("")
    feedback_var.set("")
    status_var.set(f"Máš {attempts_left[0]} pokusů. Zadej číslo:")
    feedback_lbl.config(fg=WHITE)
    guess_btn.config(state="normal")
    entry.config(state="normal")

def guess():
    raw = entry_var.get().strip()
    if not raw.isdigit():
        feedback_var.set("Zadej celé číslo!")
        feedback_lbl.config(fg=RED)
        return
    g = int(raw)
    if not (1 <= g <= 10):
        feedback_var.set("Číslo musí být 1–10!")
        feedback_lbl.config(fg=RED)
        return

    attempts_left[0] -= 1
    entry_var.set("")

    if g == secret_number[0]:
        feedback_var.set(f"✅ SPRÁVNĚ! Bylo to {secret_number[0]}! Lamborghini je tvoje! 🏎️")
        feedback_lbl.config(fg=GREEN)
        status_var.set("Vyhráls! Stiskni Reset pro novou hru.")
        guess_btn.config(state="disabled")
        entry.config(state="disabled")
    elif attempts_left[0] == 0:
        feedback_var.set(f"💀 Prohrál jsi! Číslo bylo {secret_number[0]}.")
        feedback_lbl.config(fg=RED)
        status_var.set("Game over. Stiskni Reset.")
        guess_btn.config(state="disabled")
        entry.config(state="disabled")
    elif g < secret_number[0]:
        feedback_var.set("📈 Víc!")
        feedback_lbl.config(fg=GOLD)
        status_var.set(f"Zbývá {attempts_left[0]} pokusů.")
    else:
        feedback_var.set("📉 Míň!")
        feedback_lbl.config(fg=GOLD)
        status_var.set(f"Zbývá {attempts_left[0]} pokusů.")

btn_row = tk.Frame(game_frame, bg=BG)
btn_row.pack(pady=(4, 12))

guess_btn = tk.Button(btn_row, text="  TIPNI  ", font=FONT_MED,
                      bg=RED, fg=WHITE, activebackground="#b02020",
                      relief="flat", cursor="hand2", command=guess)
guess_btn.pack(side="left", padx=6)

reset_btn = tk.Button(btn_row, text="  RESET  ", font=FONT_MED,
                      bg=GREY, fg=WHITE, activebackground="#666666",
                      relief="flat", cursor="hand2", command=reset_game)
reset_btn.pack(side="left", padx=6)

entry.bind("<Return>", lambda e: guess())

# ══════════════════════════════════════════════════════════════════════════════
#  ODKAZ – Official Trailer
# ══════════════════════════════════════════════════════════════════════════════
separator2 = tk.Frame(root, height=2, bg=RED)
separator2.pack(fill="x", padx=40, pady=10)

link_frame = tk.Frame(root, bg=BG)
link_frame.pack(pady=4)

tk.Label(link_frame, text="🎬  Sleduj oficiální trailer GTA VI:",
         font=FONT_MED, fg=WHITE, bg=BG).pack()

link_lbl = tk.Label(link_frame,
                    text="▶  Klikni sem pro Official Trailer  ◀",
                    font=("Courier New", 13, "bold", "underline"),
                    fg=GOLD, bg=BG, cursor="hand2")
link_lbl.pack(pady=4)
link_lbl.bind("<Button-1>", lambda e: webbrowser.open(RICKROLL))

tk.Label(link_frame, text="(youtube.com — Rockstar Games)",
         font=FONT_SM, fg=GREY, bg=BG).pack()

# ══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════════════════
separator3 = tk.Frame(root, height=1, bg=GREY)
separator3.pack(fill="x", padx=40, pady=10)

tk.Label(root,
         text="© 2026 Rockstar Games  •  Všechna práva vyhrazena  •  18+",
         font=("Courier New", 9), fg=GREY, bg=BG).pack(pady=(0, 10))

root.mainloop()
