import os
import tkinter as tk

# File where tasks will be stored
TASKS_FILE = "tasks.txt"


def load_tasks():
    """Loads tasks from a text file into the listbox upon starting."""
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r", encoding="utf-8") as file:
            for line in file:
                task = line.strip()
                if task:
                    listbox.insert(tk.END, task)

                    # Ensure existing checked items are correctly colored gray
                    if task.startswith("✓ "):
                        listbox.itemconfig(listbox.size() - 1, fg="gray")


def save_tasks():
    """Saves all current tasks from the listbox into a text file."""
    with open(TASKS_FILE, "w", encoding="utf-8") as file:
        tasks = listbox.get(0, tk.END)
        for task in tasks:
            file.write(task + "\n")


def add_task(event=None):
    """Adds a new task to the list and saves it."""
    task_text = entry.get().strip()
    if task_text:
        listbox.insert(tk.END, "○ " + task_text)
        entry.delete(0, tk.END)
        save_tasks()  # Save changes


def toggle_task(event):
    """Toggles a task between finished [✓] and unfinished [○] and updates storage."""
    index = listbox.nearest(event.y)

    if index >= 0 and listbox.bbox(index):
        text = listbox.get(index)

        if text.startswith("○ "):
            listbox.delete(index)
            listbox.insert(index, "✓ " + text[2:])  # Fixed slicing offset
            listbox.itemconfig(index, fg="gray")

        elif text.startswith("✓ "):
            listbox.delete(index)
            listbox.insert(index, "○ " + text[2:])  # Fixed slicing offset
            listbox.itemconfig(index, fg=current_fg)

        save_tasks()  # Save changes


def toggle_theme():
    """Switches between light and dark mode."""
    global is_dark, current_bg, current_fg
    is_dark = not is_dark

    if is_dark:
        current_bg, current_fg = "#333333", "#eeeeee"
        theme_btn.config(text="Light Mode")
        entry_bg = "#555555"
    else:
        current_bg, current_fg = "#c0c0c0", "#000000"
        theme_btn.config(text="Dark Mode")
        entry_bg = "#ffffff"

    root.config(bg=current_bg)
    top_frame.config(bg=current_bg)
    frame.config(bg=current_bg)
    bottom_frame.config(bg=current_bg)

    listbox.config(bg=current_bg, fg=current_fg, selectbackground=current_bg)
    entry.config(bg=entry_bg, fg=current_fg, insertbackground=current_fg)

    for i in range(listbox.size()):
        if listbox.get(i).startswith("✓ "):
            listbox.itemconfig(i, fg="gray")
        else:
            listbox.itemconfig(i, fg=current_fg)


# --- App Setup ---
root = tk.Tk()
root.title("Task List")
root.geometry("400x450")

# Note: Handled gracefully if you don't have the specific icon file locally
try:
    root.iconbitmap("icon.ico")
except Exception:
    pass

# Default Light Mode Colors
is_dark = False
current_bg = "#c0c0c0"
current_fg = "#000000"
root.config(bg=current_bg)

# --- Top Frame (Settings Only) ---
top_frame = tk.Frame(root, bg=current_bg)
top_frame.pack(fill=tk.X, pady=10, padx=15)

theme_btn = tk.Button(
    top_frame, text="Dark Mode", command=toggle_theme, cursor="hand2"
)
theme_btn.pack(side=tk.RIGHT)

# --- Middle Frame (Task List) ---
frame = tk.Frame(root, bg=current_bg)
frame.pack(fill=tk.BOTH, expand=True, padx=15)

listbox = tk.Listbox(
    frame,
    font=("Arial", 14),
    bg=current_bg,
    fg=current_fg,
    bd=0,
    highlightthickness=0,
    selectbackground=current_bg,
    activestyle="none",
)
listbox.pack(fill=tk.BOTH, expand=True, pady=10)

listbox.bind("<Button-1>", toggle_task)

# --- Bottom Frame (Input Area) ---
bottom_frame = tk.Frame(root, bg=current_bg)
bottom_frame.pack(fill=tk.X, pady=15, padx=15)

entry = tk.Entry(bottom_frame, font=("Arial", 14), bg="#ffffff")
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
entry.bind("<Return>", add_task)

add_btn = tk.Button(
    bottom_frame, text="Add", font=("Arial", 12), command=add_task, cursor="hand2"
)
add_btn.pack(side=tk.RIGHT)

# Load existing tasks right before running the application loop
load_tasks()

# Ensure tasks save automatically if the user closes via the standard window "X"
root.protocol("WM_DELETE_WINDOW", lambda: [save_tasks(), root.destroy()])

root.mainloop()
