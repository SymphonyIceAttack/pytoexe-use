import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import os

FILE = "pages.json"
SETTINGS_FILE = "settings.json"

# =====================
# ДАННЫЕ
# =====================
def load_pages():
    if os.path.exists(FILE):
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_pages():
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"theme": "dark"}

def save_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

pages = load_pages()
settings = load_settings()
current_page = None

# =====================
# ТЕМЫ
# =====================
LIGHT = {
    "bg": "#ffffff",
    "sidebar": "#f5f5f5",
    "text": "#000000",
    "btn": "#e0e0e0",
    "hover": "#d6d6d6"
}

DARK = {
    "bg": "#191919",
    "sidebar": "#202020",
    "text": "#ffffff",
    "btn": "#2a2a2a",
    "hover": "#333333"
}

theme = DARK if settings["theme"] == "dark" else LIGHT

# =====================
# UI
# =====================
root = tk.Tk()
root.title("Notion 1.0")
root.geometry("1200x700")

sidebar = tk.Frame(root, width=250)
sidebar.pack(side="left", fill="y")

list_frame = tk.Frame(sidebar)
list_frame.pack(fill="both", expand=True)

main = tk.Frame(root)
main.pack(side="right", fill="both", expand=True)

# =====================
# ГЛАВНАЯ
# =====================
home_frame = tk.Frame(main)

home_label = tk.Label(home_frame, text="Notion 1.0", font=("Arial", 30, "bold"))
home_label.pack(pady=20)

home_desc = tk.Label(
    home_frame,
    text="Редактор заметок как \nСоздавай страницы и управляй ими \n\n далешь мого обновлений",
    font=("Arial", 14)
)
home_desc.pack()

def show_home():
    global current_page
    current_page = None
    text.pack_forget()
    toolbar.pack_forget()
    home_frame.pack(fill="both", expand=True)

# =====================
# БЛОКИ
# =====================
def add_text():
    text.insert(tk.INSERT, "\n")

def add_heading():
    text.insert(tk.INSERT, "\n# ")

def add_checkbox():
    text.insert(tk.INSERT, "\n[ ] ")

def toggle_checkbox():
    line = text.get("insert linestart", "insert lineend")
    if "[ ]" in line:
        new = line.replace("[ ]", "[+]")
    elif "[+]" in line:
        new = line.replace("[+]", "[ ]")
    else:
        return
    text.delete("insert linestart", "insert lineend")
    text.insert("insert linestart", new)

def add_divider():
    text.insert(tk.INSERT, "\n--------------------\n")

# =====================
# СТРАНИЦЫ
# =====================
def open_page(name):
    global current_page
    current_page = name

    home_frame.pack_forget()
    toolbar.pack(fill="x")
    text.pack(fill="both", expand=True)

    text.delete("1.0", tk.END)
    text.insert(tk.END, pages[name])

    title_label.config(text=name)

def render_pages(filtered=None):
    for w in list_frame.winfo_children():
        w.destroy()

    data = filtered if filtered else pages

    if not data:
        tk.Label(list_frame, text="❌ Ничего не найдено").pack()
        return

    for name in data:
        lbl = tk.Label(list_frame, text="📄 " + name, anchor="w", padx=10)
        lbl.pack(fill="x", pady=2)

        lbl.bind("<Button-1>", lambda e, n=name: open_page(n))

def new_page():
    name = simpledialog.askstring("Новая", "Название:")
    if name:
        pages[name] = ""
        save_pages()
        render_pages()

def delete_page():
    global current_page
    if current_page:
        if messagebox.askyesno("Удалить", "Удалить страницу?"):
            del pages[current_page]
            current_page = None
            save_pages()
            render_pages()
            show_home()

# =====================
# ПОИСК / СИНК
# =====================
def search():
    q = simpledialog.askstring("Поиск", "Название:")
    if q:
        filtered = {k: v for k in pages if q.lower() in k.lower()}
        render_pages(filtered)

def sync():
    global pages
    pages = load_pages()
    render_pages()
    messagebox.showinfo("Синхронизация", "Обновлено")

# =====================
# ТЕМА
# =====================
def toggle_theme():
    global theme
    if theme == DARK:
        theme = LIGHT
        settings["theme"] = "light"
    else:
        theme = DARK
        settings["theme"] = "dark"

    save_settings()
    apply_theme()

def apply_theme():
    root.configure(bg=theme["bg"])
    sidebar.configure(bg=theme["sidebar"])
    list_frame.configure(bg=theme["sidebar"])
    main.configure(bg=theme["bg"])
    home_frame.configure(bg=theme["bg"])
    toolbar.configure(bg=theme["sidebar"])

    text.configure(bg=theme["bg"], fg=theme["text"], insertbackground=theme["text"])

    title_label.configure(bg=theme["bg"], fg=theme["text"])
    home_label.configure(bg=theme["bg"], fg=theme["text"])
    home_desc.configure(bg=theme["bg"], fg=theme["text"])

    # sidebar кнопки
    for widget in sidebar.winfo_children():
        if isinstance(widget, tk.Button):
            widget.configure(
                bg=theme["btn"],
                fg=theme["text"],
                activebackground=theme["hover"],
                bd=0
            )

    # список страниц
    for widget in list_frame.winfo_children():
        if isinstance(widget, tk.Label):
            widget.configure(bg=theme["sidebar"], fg=theme["text"])

            widget.bind("<Enter>", lambda e, w=widget: w.configure(bg=theme["hover"]))
            widget.bind("<Leave>", lambda e, w=widget: w.configure(bg=theme["sidebar"]))

    # toolbar
    for widget in toolbar.winfo_children():
        if isinstance(widget, tk.Button):
            widget.configure(
                bg=theme["btn"],
                fg=theme["text"],
                activebackground=theme["hover"],
                bd=0
            )

# =====================
# АВТОСОХРАНЕНИЕ
# =====================
def auto_save(event=None):
    if current_page:
        pages[current_page] = text.get("1.0", tk.END)
        save_pages()

# =====================
# TOOLBAR
# =====================
toolbar = tk.Frame(main)

tk.Button(toolbar, text="H1", command=add_heading).pack(side="left")
tk.Button(toolbar, text="☑", command=add_checkbox).pack(side="left")
tk.Button(toolbar, text="✔", command=toggle_checkbox).pack(side="left")
tk.Button(toolbar, text="—", command=add_divider).pack(side="left")

# =====================
# SIDEBAR
# =====================
tk.Button(sidebar, text="🏠 Главная", command=show_home).pack(fill="x")
tk.Button(sidebar, text="+ Новая", command=new_page).pack(fill="x")
tk.Button(sidebar, text="🗑 Удалить", command=delete_page).pack(fill="x")
tk.Button(sidebar, text="🔍 Поиск", command=search).pack(fill="x")
tk.Button(sidebar, text="🔄 Сохранить", command=sync).pack(fill="x")
tk.Button(sidebar, text="🌗 Тема", command=toggle_theme).pack(fill="x")

# =====================
# MAIN
# =====================
title_label = tk.Label(main, text="Главная", font=("Arial", 28))
title_label.pack()

text = tk.Text(main, wrap="word", font=("Arial", 13))
text.bind("<KeyRelease>", auto_save)

# =====================
# ЗАПУСК
# =====================
render_pages()
apply_theme()
show_home()

root.mainloop()