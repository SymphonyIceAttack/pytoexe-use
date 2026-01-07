import tkinter as tk
from tkinter import ttk

---------------- CONFIG ----------------
BG = "#0b0f14"
PANEL = "#020617"
ACCENT = "#22d3ee"
TEXT = "#e5e7eb"
MUTED = "#9ca3af"
BORDER = "#1f2937"

FONT_MAIN = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_LOGO = ("Segoe UI", 18, "bold")

---------------- APP ----------------
root = tk.Tk()
root.title("SpySINT OSINT Panel")
root.geometry("1200x700")
root.configure(bg=BG)

---------------- SIDEBAR ----------------
sidebar = tk.Frame(root, bg=PANEL, width=240)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

logo = tk.Label(sidebar, text="SpySINT", fg=ACCENT, bg=PANEL, font=FONT_LOGO)
logo.pack(pady=(25, 40))

nav_buttons = {}

def show_page(name):
    for page in pages.values():
        page.pack_forget()
    pages[name].pack(fill="both", expand=True)

    for btn in nav_buttons.values():
        btn.configure(bg=PANEL, fg=MUTED)
    nav_buttons[name].configure(bg="#020617", fg=TEXT)

def nav_button(name, text):
    btn = tk.Button(
        sidebar,
        text=text,
        anchor="w",
        padx=16,
        pady=10,
        bg=PANEL,
        fg=MUTED,
        relief="flat",
        font=FONT_MAIN,
        command=lambda: show_page(name)
    )
    btn.pack(fill="x", pady=3, padx=8)
    nav_buttons[name] = btn

nav_button("osint", "OSINT")
nav_button("call", "Call Panel")
nav_button("builder", "Builder")
nav_button("about", "About")

footer = tk.Label(
    sidebar,
    text="OSINT UI • Visual Only",
    fg="#6b7280",
    bg=PANEL,
    font=("Segoe UI", 8)
)
footer.pack(side="bottom", pady=10)
---------------- MAIN AREA ----------------
main = tk.Frame(root, bg=BG)
main.pack(side="right", fill="both", expand=True)

pages = {}

def page():
    f = tk.Frame(main, bg=BG)
    return f
---------------- OSINT PAGE ----------------
osint = page()
pages["osint"] = osint

card = tk.Frame(osint, bg=PANEL, bd=1, relief="solid", highlightbackground=BORDER)
card.pack(padx=30, pady=30, fill="both", expand=True)

title = tk.Label(card, text="All-in-One OSINT Search", fg=TEXT, bg=PANEL, font=FONT_TITLE)
title.pack(anchor="w", pady=(0, 20))

grid = tk.Frame(card, bg=PANEL)
grid.pack(fill="both", expand=True)

def search_box(parent, title_text, placeholder):
    box = tk.Frame(parent, bg="#020617", bd=1, relief="solid", highlightbackground=BORDER)
    label = tk.Label(box, text=title_text, fg=TEXT, bg="#020617", font=("Segoe UI", 9, "bold"))
    entry = tk.Entry(box, bg="#020617", fg=TEXT, insertbackground=TEXT, relief="flat")

    label.pack(anchor="w", pady=(0, 6))
    entry.pack(fill="x", ipady=6)

    return box

boxes = [
    ("Breach Search", "Email / Username"),
    ("Address Search", "Street / City / ZIP"),
    ("IP / Domain Lookup", "IP or domain"),
    ("Phone Search", "Phone number"),
    ("Username Search", "Username"),
    ("Social Profile", "Profile link"),
]

for i, (t, p) in enumerate(boxes):
    b = search_box(grid, t, p)
    b.grid(row=i // 3, column=i % 3, padx=10, pady=10, sticky="nsew")

for i in range(3):
    grid.columnconfigure(i, weight=1)

---------------- CALL PAGE ----------------
call = page()
pages["call"] = call
tk.Label(call, text="Call Panel\nComing soon", fg=MUTED, bg=BG, font=FONT_TITLE).pack(expand=True)
---------------- BUILDER PAGE ----------------
builder = page()
pages["builder"] = builder
tk.Label(builder, text="Builder\nComing soon", fg=MUTED, bg=BG, font=FONT_TITLE).pack(expand=True)

---------------- ABOUT PAGE ----------------
about = page()
pages["about"] = about

about_card = tk.Frame(about, bg=PANEL, bd=1, relief="solid", highlightbackground=BORDER)
about_card.pack(padx=30, pady=30)

tk.Label(about_card, text="About", fg=TEXT, bg=PANEL, font=FONT_TITLE).pack(anchor="w")
tk.Label(about_card, text="Made by spyware", fg=TEXT, bg=PANEL).pack(anchor="w", pady=10)

---------------- START ----------------
show_page("osint")
root.mainloop()
