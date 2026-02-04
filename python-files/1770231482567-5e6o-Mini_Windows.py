import tkinter as tk
from tkinter import simpledialog
from datetime import datetime

# ---------------- Mini Apps ----------------
class Calculator(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.expression = ""
        self.display = tk.Entry(self, font=("Arial", 16), bd=2, relief="ridge", justify="right")
        self.display.pack(expand=True, fill="both")

        btns_frame = tk.Frame(self)
        btns_frame.pack()

        buttons = [
            ['7','8','9','/'],
            ['4','5','6','*'],
            ['1','2','3','-'],
            ['0','.','=','+']
        ]

        for r, row in enumerate(buttons):
            row_frame = tk.Frame(btns_frame)
            row_frame.pack(expand=True, fill="both")
            for c, char in enumerate(row):
                b = tk.Button(row_frame, text=char, font=("Arial", 14), command=lambda ch=char: self.press(ch))
                b.pack(side="left", expand=True, fill="both")

    def press(self, char):
        if char == "=":
            try:
                self.expression = str(eval(self.expression))
            except:
                self.expression = "Erreur"
        else:
            self.expression += char
        self.display.delete(0, tk.END)
        self.display.insert(tk.END, self.expression)

def open_calculator(master):
    win = MiniWindow(master, taskbar, "Calculatrice")
    Calculator(win.content).pack(expand=True, fill="both")

def open_notepad(master):
    win = MiniWindow(master, taskbar, "Bloc-notes")
    text = tk.Text(win.content, wrap="word")
    text.pack(expand=True, fill="both")

# ---------------- Mini Window ----------------
class MiniWindow(tk.Frame):
    def __init__(self, master, taskbar, title="Fenêtre"):
        super().__init__(master, bg="#dcdcdc", bd=2, relief="raised")
        self.master = master
        self.taskbar = taskbar
        self.title_text = title
        self.visible = True

        self.width = 300
        self.height = 200
        self.place(x=100, y=100, width=self.width, height=self.height)

        # Barre de titre
        self.title_bar = tk.Frame(self, bg="#1e90ff", height=25)
        self.title_bar.pack(fill="x")

        tk.Label(self.title_bar, text=title, bg="#1e90ff", fg="white").pack(side="left", padx=5)

        tk.Button(self.title_bar, text="—", bg="#1e90ff", fg="white", bd=0, command=self.toggle).pack(side="right")
        tk.Button(self.title_bar, text="✕", bg="#ff4d4d", fg="white", bd=0, command=self.close).pack(side="right")

        # Contenu
        self.content = tk.Frame(self, bg="#f0f0f0")
        self.content.pack(expand=True, fill="both")

        # Drag
        self.title_bar.bind("<Button-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.do_move)

        # Redimension
        self.bind("<Button-3>", self.start_resize)
        self.bind("<B3-Motion>", self.do_resize)

        self.taskbar.add_window(self)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        x = self.winfo_x() + event.x - self.x
        y = self.winfo_y() + event.y - self.y
        self.place(x=x, y=y, width=self.width, height=self.height)

    def start_resize(self, event):
        self.resizing = True
        self.start_width = self.width
        self.start_height = self.height
        self.start_x = event.x_root
        self.start_y = event.y_root

    def do_resize(self, event):
        if hasattr(self, 'resizing') and self.resizing:
            dx = event.x_root - self.start_x
            dy = event.y_root - self.start_y
            self.width = max(150, self.start_width + dx)
            self.height = max(100, self.start_height + dy)
            self.place(x=self.winfo_x(), y=self.winfo_y(), width=self.width, height=self.height)

    def toggle(self):
        if self.visible:
            self.place_forget()
        else:
            self.place(x=100, y=100, width=self.width, height=self.height)
        self.visible = not self.visible

    def close(self):
        self.taskbar.remove_window(self)
        self.destroy()

# ---------------- Taskbar ----------------
class Taskbar(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#202020", height=40)
        self.pack(side="bottom", fill="x")
        self.buttons = {}
        self.clock = tk.Label(self, bg="#202020", fg="white")
        self.clock.pack(side="right", padx=10)
        self.update_clock()

    def add_window(self, window):
        btn = tk.Button(self, text=window.title_text, bg="#404040", fg="white", relief="flat", command=window.toggle)
        btn.pack(side="left", padx=5, pady=5)
        self.buttons[window] = btn

    def remove_window(self, window):
        btn = self.buttons.pop(window, None)
        if btn:
            btn.destroy()

    def update_clock(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.clock.config(text=now)
        self.after(1000, self.update_clock)

# ---------------- Desktop ----------------
class Desktop(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#2e8b57")
        self.pack(expand=True, fill="both")
        self.icons = []

        # Icônes du bureau
        self.add_icon("Bloc-notes", open_notepad, 50, 50)
        self.add_icon("Calculatrice", open_calculator, 50, 120)

    def add_icon(self, name, command, x, y):
        icon = tk.Button(self, text=name, width=12, height=2, command=lambda: command(root))
        icon.place(x=x, y=y)
        self.icons.append(icon)

# ---------------- Main ----------------
root = tk.Tk()
root.title("Mini Windows Python")
root.geometry("1000x600")

taskbar = Taskbar(root)
desktop = Desktop(root)

# Démarrer button
def open_start_menu():
    menu = tk.Toplevel(root)
    menu.title("Menu Démarrer")
    menu.geometry("200x300+0+300")
    menu.resizable(False, False)
    tk.Label(menu, text="Menu Démarrer", bg="#1e90ff", fg="white").pack(fill="x")
    tk.Button(menu, text="Bloc-notes", command=lambda: [open_notepad(root), menu.destroy()]).pack(fill="x")
    tk.Button(menu, text="Calculatrice", command=lambda: [open_calculator(root), menu.destroy()]).pack(fill="x")
    tk.Button(menu, text="Fermer Menu", command=menu.destroy).pack(fill="x")

start_btn = tk.Button(taskbar, text="Démarrer", bg="#404040", fg="white", relief="flat", command=open_start_menu)
start_btn.pack(side="left", padx=5, pady=5)

root.mainloop()