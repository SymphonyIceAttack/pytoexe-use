import tkinter as tk
from tkinter import messagebox

def open_menu():
    messagebox.showinfo("Menu", "Menu Opened")

app = tk.Tk()
app.title("Fake Menu")
# כאן הגדלנו את החלון לרוחב ולגובה
app.geometry("600x400")  # רוחב 600 פיקסלים, גובה 400 פיקסלים
app.resizable(False, False)  # לא ניתן לשנות גודל

# אפשר לשים תווית גדולה למראה של Menu
tk.Label(app, text="FAKE MENU", font=("Consolas", 24, "bold")).pack(pady=20)

# כפתורים גדולים
tk.Button(app, text="OPEN", width=30, height=3, command=open_menu).pack(pady=10)
tk.Button(app, text="EXIT", width=30, height=3, command=app.destroy).pack(pady=10)

app.mainloop()
