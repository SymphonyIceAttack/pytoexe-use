import tkinter as tk
from tkinter import messagebox
import webbrowser

# Correct credentials
CORRECT_USERNAME = "admin"
CORRECT_PASSWORD = "polloland"

def login():
    username = entry_username.get()
    password = entry_password.get()

    if username == CORRECT_USERNAME and password == CORRECT_PASSWORD:
        messagebox.showinfo("Login", "Access granted. Redirecting...")
        webbrowser.open("https://rule34.xxx/index.php?page=post&s=list&tags=")
        root.destroy()  # close app
    else:
        messagebox.showerror("Login", "Invalid username or password")

# Create window
root = tk.Tk()
root.title("Login App")
root.geometry("300x200")
root.resizable(False, False)

# Username
tk.Label(root, text="Username").pack(pady=5)
entry_username = tk.Entry(root)
entry_username.pack()

# Password
tk.Label(root, text="Password").pack(pady=5)
entry_password = tk.Entry(root, show="*")
entry_password.pack()

# Login button
tk.Button(root, text="Login", command=login).pack(pady=15)

# Run app
root.mainloop()
