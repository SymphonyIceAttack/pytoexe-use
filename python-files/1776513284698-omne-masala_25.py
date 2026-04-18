import tkinter as tk
from tkinter import messagebox, font

# ─── Ranglar ───────────────────────────────────────────────
BG       = "#0a1628"
CARD     = "#112240"
ACCENT   = "#64ffda"
ACCENT2  = "#ffd700"
TEXT     = "#ccd6f6"
SUBTEXT  = "#8892b0"
ENTRY_BG = "#1e3a5f"
BORDER   = "#233554"
RED      = "#ff6b6b"
GREEN    = "#64ffda"

nuqtalar_lugat = []   # global ro'yxat

def qosh():
    try:
        x = float(entry_x.get())
        y = float(entry_y.get())
        nuqta = {"x": x, "y": y}
        nuqtalar_lugat.append(nuqta)
        entry_x.delete(0, tk.END)
        entry_y.delete(0, tk.END)
        yangilash()
    except ValueError:
        messagebox.showerror("Xato", "X va Y raqam bo'lishi kerak!")

def yangilash():
    # Barcha nuqtalar
    listbox_all.delete(0, tk.END)
    for i, n in enumerate(nuqtalar_lugat):
        listbox_all.insert(tk.END, f"  Nuqta {i+1}:  x={n['x']}, y={n['y']}")

    # 1-chorak filtri: x>0 va y>0
    birinchi_chorak = [n for n in nuqtalar_lugat if n["x"] > 0 and n["y"] > 0]
    listbox_q1.delete(0, tk.END)
    if birinchi_chorak:
        for n in birinchi_chorak:
            listbox_q1.insert(tk.END, f"  ✓  x={n['x']}, y={n['y']}")
    else:
        listbox_q1.insert(tk.END, "  — hech qanday nuqta yo'q —")

    count_var.set(f"Jami: {len(nuqtalar_lugat)}  |  I-chorak: {len(birinchi_chorak)}")
    draw_canvas(birinchi_chorak)

def draw_canvas(q1_list):
    c.delete("all")
    W, H = 340, 200
    ox, oy = W // 2, H // 2

    # Grid
    for i in range(0, W, 20):
        c.create_line(i, 0, i, H, fill="#1e3a5f", width=1)
    for i in range(0, H, 20):
        c.create_line(0, i, W, i, fill="#1e3a5f", width=1)

    # Chorак 1 highlight
    c.create_rectangle(ox, 0, W, oy, fill="#0d2b1a", outline="")

    # O'qlar
    c.create_line(0, oy, W, oy, fill=SUBTEXT, width=1, arrow="last")
    c.create_line(ox, H, ox, 0, fill=SUBTEXT, width=1, arrow="last")
    c.create_text(W-8, oy-10, text="x", fill=SUBTEXT, font=("Courier New", 8))
    c.create_text(ox+10, 8, text="y", fill=SUBTEXT, font=("Courier New", 8))

    # Chorak belgilari
    c.create_text(ox+50, oy-20, text="I", fill=ACCENT, font=("Courier New", 10, "bold"))
    c.create_text(ox-50, oy-20, text="II", fill=SUBTEXT, font=("Courier New", 9))
    c.create_text(ox-50, oy+20, text="III", fill=SUBTEXT, font=("Courier New", 9))
    c.create_text(ox+50, oy+20, text="IV", fill=SUBTEXT, font=("Courier New", 9))

    # Barcha nuqtalar
    for n in nuqtalar_lugat:
        px = ox + n["x"] * 15
        py = oy - n["y"] * 15
        if -ox < px-ox < ox and -oy < py-oy < oy:
            c.create_oval(px-3, py-3, px+3, py+3, fill=SUBTEXT, outline="")

    # 1-chorak nuqtalar
    for n in q1_list:
        px = ox + n["x"] * 15
        py = oy - n["y"] * 15
        if 0 < px-ox and 0 < -(py-oy):
            c.create_oval(px-5, py-5, px+5, py+5, fill=ACCENT, outline=ACCENT2, width=2)

def tozala():
    global nuqtalar_lugat
    nuqtalar_lugat = []
    yangilash()

# ─── Oyna ──────────────────────────────────────────────────
root = tk.Tk()
root.title("Masala 25 — I-Chorak Nuqtalari")
root.geometry("600x680")
root.resizable(False, False)
root.configure(bg=BG)

title_font  = font.Font(family="Courier New", size=13, weight="bold")
label_font  = font.Font(family="Courier New", size=10)
entry_font  = font.Font(family="Courier New", size=13)
small_font  = font.Font(family="Courier New", size=9)
mono_font   = font.Font(family="Courier New", size=10)

tk.Frame(root, bg=ACCENT, height=4).pack(fill="x")

tk.Label(root, text="◈  I-CHORAK NUQTALARI  ◈", bg=BG, fg=ACCENT,
         font=title_font, pady=14).pack()
tk.Label(root, text="Masala 25 | Faqat 1-chorakdagi nuqtalarni ajratish",
         bg=BG, fg=SUBTEXT, font=small_font).pack()

# ─── Kiritish paneli ───────────────────────────────────────
input_frame = tk.Frame(root, bg=CARD, padx=20, pady=14,
                       highlightthickness=1, highlightbackground=BORDER)
input_frame.pack(fill="x", padx=20, pady=10)

row = tk.Frame(input_frame, bg=CARD)
row.pack(fill="x")

tk.Label(row, text="X:", bg=CARD, fg=SUBTEXT, font=label_font, width=3).pack(side="left")
entry_x = tk.Entry(row, bg=ENTRY_BG, fg=TEXT, font=entry_font,
                   insertbackground=ACCENT, relief="flat",
                   highlightthickness=1, highlightbackground=BORDER, width=8)
entry_x.pack(side="left", ipady=6, padx=4)

tk.Label(row, text="Y:", bg=CARD, fg=SUBTEXT, font=label_font, width=3).pack(side="left")
entry_y = tk.Entry(row, bg=ENTRY_BG, fg=TEXT, font=entry_font,
                   insertbackground=ACCENT, relief="flat",
                   highlightthickness=1, highlightbackground=BORDER, width=8)
entry_y.pack(side="left", ipady=6, padx=4)

tk.Button(row, text="  QO'SH  ", bg=ACCENT, fg="#0a1628",
          font=label_font, relief="flat", padx=14, pady=6,
          cursor="hand2", command=qosh).pack(side="left", padx=8)

tk.Button(row, text=" TOZALA ", bg=ENTRY_BG, fg=SUBTEXT,
          font=small_font, relief="flat", padx=10, pady=6,
          cursor="hand2", command=tozala).pack(side="left")

# ─── Ko'rgazma ─────────────────────────────────────────────
mid = tk.Frame(root, bg=BG)
mid.pack(fill="both", expand=True, padx=20)

# Chap — ro'yxatlar
left = tk.Frame(mid, bg=BG)
left.pack(side="left", fill="both", expand=True)

tk.Label(left, text="Barcha nuqtalar (lug'atlar ro'yxati):",
         bg=BG, fg=SUBTEXT, font=small_font, anchor="w").pack(fill="x", pady=(8,2))
listbox_all = tk.Listbox(left, bg=CARD, fg=TEXT, font=mono_font,
                         selectbackground=ACCENT, selectforeground=BG,
                         relief="flat", highlightthickness=1,
                         highlightbackground=BORDER, height=7)
listbox_all.pack(fill="x")

tk.Label(left, text="✓ I-chorak nuqtalari (x>0 va y>0):",
         bg=BG, fg=ACCENT, font=small_font, anchor="w").pack(fill="x", pady=(10,2))
listbox_q1 = tk.Listbox(left, bg=CARD, fg=ACCENT, font=mono_font,
                        selectbackground=ACCENT2, selectforeground=BG,
                        relief="flat", highlightthickness=1,
                        highlightbackground=ACCENT, height=5)
listbox_q1.pack(fill="x")

count_var = tk.StringVar(value="Jami: 0  |  I-chorak: 0")
tk.Label(left, textvariable=count_var, bg=BG, fg=ACCENT2,
         font=small_font, anchor="w").pack(fill="x", pady=4)

# O'ng — koordinata tekisligi
right = tk.Frame(mid, bg=BG, padx=10)
right.pack(side="right")

tk.Label(right, text="Koordinata tekisligi:",
         bg=BG, fg=SUBTEXT, font=small_font).pack(pady=(8,2))
c = tk.Canvas(right, bg="#0a1628", width=340, height=200,
              highlightthickness=1, highlightbackground=BORDER)
c.pack()
draw_canvas([])

tk.Label(root, text="© PDT Amaliy Mashg'ulot | Masala 25",
         bg=BG, fg=BORDER, font=small_font).pack(pady=10)

root.mainloop()
