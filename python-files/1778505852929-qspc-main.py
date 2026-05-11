import customtkinter as ctk
import tkinter as tk
import os
import math
import random

from pygments import lex
from pygments.lexers import PythonLexer, LuaLexer
from pygments.token import Token

# ============================================
# SETTINGS
# ============================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BASE_FOLDER = "ScriptStorage"
os.makedirs(BASE_FOLDER, exist_ok=True)

default_category = os.path.join(BASE_FOLDER, "Main")

if not os.path.exists(default_category):
    os.makedirs(default_category)

# ============================================
# GET CATEGORIES
# ============================================
def get_categories():
    return [
        folder for folder in os.listdir(BASE_FOLDER)
        if os.path.isdir(os.path.join(BASE_FOLDER, folder))
    ]

# ============================================
# WINDOW
# ============================================
app = ctk.CTk()
app.title("⚡ Script Storage")
app.geometry("1450x900")
app.configure(fg_color="#050505")

# ============================================
# BACKGROUND
# ============================================
canvas = ctk.CTkCanvas(
    app,
    bg="#050505",
    highlightthickness=0
)
canvas.place(relwidth=1, relheight=1)

particles = []

for i in range(55):

    x = random.randint(0, 1450)
    y = random.randint(0, 900)

    size = random.randint(2, 5)

    particle = canvas.create_oval(
        x,
        y,
        x + size,
        y + size,
        fill="#6d28d9",
        outline=""
    )

    particles.append({
        "id": particle,
        "dx": random.uniform(-0.5, 0.5),
        "dy": random.uniform(-0.5, 0.5)
    })


def animate_background():

    width = app.winfo_width()
    height = app.winfo_height()

    canvas.delete("line")

    for p in particles:

        canvas.move(p["id"], p["dx"], p["dy"])

        coords = canvas.coords(p["id"])

        if not coords or len(coords) < 4:
            continue

        x1, y1, x2, y2 = coords

        if x1 <= 0 or x2 >= width:
            p["dx"] *= -1

        if y1 <= 0 or y2 >= height:
            p["dy"] *= -1

    for i in range(len(particles)):
        for j in range(i + 1, len(particles)):

            c1 = canvas.coords(particles[i]["id"])
            c2 = canvas.coords(particles[j]["id"])

            if not c1 or not c2:
                continue

            x1 = c1[0]
            y1 = c1[1]

            x2 = c2[0]
            y2 = c2[1]

            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

            if distance < 140:
                canvas.create_line(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill="#151515",
                    tags="line"
                )

    app.after(16, animate_background)


animate_background()

# ============================================
# MAIN FRAME
# ============================================
main_frame = ctk.CTkFrame(
    app,
    fg_color="transparent"
)
main_frame.pack(fill="both", expand=True)

# ============================================
# LEFT PANEL
# ============================================
left_frame = ctk.CTkFrame(
    main_frame,
    width=320,
    corner_radius=0,
    fg_color="#090909",
    border_width=1,
    border_color="#161616"
)
left_frame.pack(side="left", fill="y")

logo = ctk.CTkLabel(
    left_frame,
    text="⚡ Script Storage",
    font=("Segoe UI", 34, "bold"),
    text_color="white"
)
logo.pack(pady=(30, 20))

search_var = ctk.StringVar()

search_entry = ctk.CTkEntry(
    left_frame,
    placeholder_text="Search scripts...",
    textvariable=search_var,
    height=50,
    fg_color="#101010",
    border_color="#1d1d1d",
    corner_radius=14,
    font=("Segoe UI", 16)
)
search_entry.pack(fill="x", padx=20, pady=(0, 15))

# ============================================
# CATEGORY MENU
# ============================================
categories = get_categories()

selected_category = ctk.StringVar(
    value=categories[0]
)

category_menu = ctk.CTkOptionMenu(
    left_frame,
    values=categories,
    variable=selected_category,

    height=50,
    corner_radius=14,

    font=("Segoe UI", 16, "bold"),
    dropdown_font=("Segoe UI", 15),

    fg_color="#101010",
    button_color="#6d28d9",
    button_hover_color="#7c3aed",

    dropdown_fg_color="#0b0b0b",
    dropdown_hover_color="#181818",

    text_color="white",
    dropdown_text_color="white"
)

category_menu.pack(fill="x", padx=20, pady=(0, 15))

script_frame = ctk.CTkScrollableFrame(
    left_frame,
    fg_color="transparent"
)
script_frame.pack(fill="both", expand=True, padx=15, pady=10)

selected_script = None

# ============================================
# RIGHT PANEL
# ============================================
right_frame = ctk.CTkFrame(
    main_frame,
    fg_color="#050505",
    corner_radius=0
)
right_frame.pack(side="right", fill="both", expand=True)

# ============================================
# TOP BAR
# ============================================
top_bar = ctk.CTkFrame(
    right_frame,
    height=80,
    fg_color="transparent"
)
top_bar.pack(fill="x", padx=20, pady=20)

name_entry = ctk.CTkEntry(
    top_bar,
    placeholder_text="Script name...",
    height=52,
    fg_color="#101010",
    border_color="#1c1c1c",
    corner_radius=14,
    font=("Segoe UI", 16)
)
name_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

# ============================================
# NOTIFICATIONS
# ============================================
def show_notification(text, color="#7c3aed"):

    notif = ctk.CTkFrame(
        app,
        width=320,
        height=70,
        corner_radius=22,
        fg_color="#0b0b0b",
        border_width=1,
        border_color=color
    )

    glow = ctk.CTkFrame(
        notif,
        fg_color=color,
        width=240,
        height=4,
        corner_radius=50
    )

    glow.place(
        relx=0.5,
        rely=0.88,
        anchor="center",
        relwidth=0.82
    )

    label = ctk.CTkLabel(
        notif,
        text=text,
        font=("Segoe UI", 16, "bold"),
        text_color="white"
    )
    label.place(relx=0.5, rely=0.42, anchor="center")

    app.update_idletasks()

    start_x = app.winfo_width() + 400
    target_x = app.winfo_width() - 340

    y = app.winfo_height() - 100

    notif.place(x=start_x, y=y)

    current_x = start_x

    def animate_in():
        nonlocal current_x

        if current_x > target_x:

            current_x -= 35

            notif.place(x=current_x, y=y)

            app.after(8, animate_in)

        else:
            app.after(2200, animate_out)

    def animate_out():
        nonlocal current_x

        if current_x < app.winfo_width() + 400:

            current_x += 35

            notif.place(x=current_x, y=y)

            app.after(8, animate_out)

        else:
            notif.destroy()

    animate_in()

# ============================================
# TOKEN COLORS
# ============================================
TOKEN_COLORS = {
    Token.Keyword: "#c792ea",
    Token.Name: "#ffffff",
    Token.Comment: "#5c6370",
    Token.String: "#98c379",
    Token.Number: "#f78c6c",
    Token.Operator: "#89ddff",
    Token.Punctuation: "#89ddff",
    Token.Name.Function: "#82aaff",
    Token.Keyword.Function: "#c792ea",
    Token.Literal: "#ffcb6b"
}

# ============================================
# FUNCTIONS
# ============================================
def update_line_numbers():

    line_numbers.config(state="normal")

    line_numbers.delete("1.0", "end")

    total_lines = int(editor.index("end-1c").split(".")[0])

    numbers = "\n".join(str(i) for i in range(1, total_lines + 1))

    line_numbers.insert("1.0", numbers)

    line_numbers.config(state="disabled")

    line_numbers.yview_moveto(editor.yview()[0])


def highlight_syntax(event=None):

    code = editor.get("1.0", "end-1c")

    filename = name_entry.get().lower()

    if filename.endswith(".py"):
        lexer = PythonLexer()
    else:
        lexer = LuaLexer()

    for tag in editor.tag_names():
        editor.tag_delete(tag)

    row = 1
    col = 0

    for token, content in lex(code, lexer):

        length = len(content)

        start = f"{row}.{col}"

        lines = content.split("\n")

        if len(lines) > 1:
            row += len(lines) - 1
            col = len(lines[-1])
        else:
            col += length

        end = f"{row}.{col}"

        color = TOKEN_COLORS.get(token)

        if color:

            tag_name = str(token)

            editor.tag_add(tag_name, start, end)
            editor.tag_config(tag_name, foreground=color)

    update_line_numbers()


def clear_editor():

    global selected_script

    selected_script = None

    name_entry.delete(0, "end")
    editor.delete("1.0", "end")

    update_line_numbers()

    show_notification("New script")


def save_script():

    name = name_entry.get().strip()

    if not name:
        show_notification("Enter script name", "#ef4444")
        return

    category = selected_category.get()

    path = os.path.join(
        BASE_FOLDER,
        category,
        f"{name}.txt"
    )

    content = editor.get("1.0", "end")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    refresh_scripts()

    show_notification("Script saved", "#22c55e")


def load_script(name):

    global selected_script

    selected_script = name

    category = selected_category.get()

    path = os.path.join(
        BASE_FOLDER,
        category,
        f"{name}.txt"
    )

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    name_entry.delete(0, "end")
    name_entry.insert(0, name)

    editor.delete("1.0", "end")
    editor.insert("1.0", content)

    highlight_syntax()

    show_notification(f"Loaded {name}")


def delete_script():

    global selected_script

    if not selected_script:
        return

    category = selected_category.get()

    path = os.path.join(
        BASE_FOLDER,
        category,
        f"{selected_script}.txt"
    )

    if os.path.exists(path):
        os.remove(path)

    clear_editor()

    refresh_scripts()

    show_notification("Script deleted", "#ef4444")


def copy_script():

    text = editor.get("1.0", "end")

    app.clipboard_clear()
    app.clipboard_append(text)

    show_notification("Copied", "#3b82f6")

# ============================================
# BUTTONS
# ============================================
buttons_frame = ctk.CTkFrame(
    top_bar,
    fg_color="transparent"
)
buttons_frame.pack(side="right")


def make_button(text, color, hover, command):

    return ctk.CTkButton(
        buttons_frame,
        text=text,
        width=120,
        height=52,
        corner_radius=14,
        fg_color=color,
        hover_color=hover,
        font=("Segoe UI", 15, "bold"),
        command=command
    )


new_btn = make_button(
    "New",
    "#111111",
    "#1a1a1a",
    clear_editor
)
new_btn.pack(side="left", padx=5)

save_btn = make_button(
    "Save",
    "#6d28d9",
    "#7c3aed",
    save_script
)
save_btn.pack(side="left", padx=5)

copy_btn = make_button(
    "Copy",
    "#111111",
    "#1a1a1a",
    copy_script
)
copy_btn.pack(side="left", padx=5)

delete_btn = make_button(
    "Delete",
    "#991b1b",
    "#b91c1c",
    delete_script
)
delete_btn.pack(side="left", padx=5)

# ============================================
# EDITOR FRAME
# ============================================
editor_frame = ctk.CTkFrame(
    right_frame,
    fg_color="#090909",
    corner_radius=18,
    border_width=1,
    border_color="#181818"
)
editor_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

# ============================================
# TEXT CONTAINER
# ============================================
text_container = tk.Frame(
    editor_frame,
    bg="#090909",
    highlightthickness=0,
    bd=0
)

text_container.pack(
    fill="both",
    expand=True,
    padx=12,
    pady=12
)

# ============================================
# LINE NUMBERS
# ============================================
line_numbers = tk.Text(
    text_container,

    width=4,

    bg="#0b0b0b",
    fg="#4b5563",

    font=("Consolas", 15),

    relief="flat",
    bd=0,

    spacing1=2,
    spacing3=2,

    padx=8,

    state="disabled",

    wrap="none",

    takefocus=0
)

line_numbers.pack(
    side="left",
    fill="y"
)

# ============================================
# EDITOR
# ============================================
editor = tk.Text(
    text_container,

    bg="#090909",
    fg="#f5f5f5",

    insertbackground="white",

    font=("Consolas", 15),

    relief="flat",
    bd=0,

    undo=True,

    wrap="none",

    padx=14,
    pady=10,

    spacing1=2,
    spacing3=2
)

editor.pack(
    side="left",
    fill="both",
    expand=True
)

editor.bind("<KeyRelease>", highlight_syntax)

editor.bind(
    "<MouseWheel>",
    lambda e: line_numbers.yview_moveto(editor.yview()[0])
)

editor.bind(
    "<KeyRelease>",
    lambda e: (
        highlight_syntax(),
        update_line_numbers()
    )
)

update_line_numbers()

# ============================================
# SCRIPT LIST
# ============================================
def refresh_scripts():

    for widget in script_frame.winfo_children():
        widget.destroy()

    query = search_var.get().lower()

    category = selected_category.get()

    folder = os.path.join(BASE_FOLDER, category)

    for file in sorted(os.listdir(folder)):

        if file.endswith(".txt"):

            name = file[:-4]

            if query not in name.lower():
                continue

            btn = ctk.CTkButton(
                script_frame,
                text=name,
                anchor="w",
                height=52,
                corner_radius=12,
                fg_color="#101010",
                hover_color="#181818",
                border_width=1,
                border_color="#1d1d1d",
                font=("Segoe UI", 16),
                command=lambda n=name: load_script(n)
            )

            btn.pack(fill="x", pady=4)

# ============================================
# EVENTS
# ============================================
search_var.trace_add(
    "write",
    lambda *args: refresh_scripts()
)

selected_category.trace_add(
    "write",
    lambda *args: refresh_scripts()
)

refresh_scripts()

app.mainloop()
