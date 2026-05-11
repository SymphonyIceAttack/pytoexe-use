import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import sqlite3
import subprocess
import sys
import os

def open_admin():
    root.destroy()
    subprocess.run([sys.executable, "admin_panel.py"])

def open_student(student_id):
    root.destroy()
    subprocess.run([sys.executable, "student_panel.py", str(student_id)])

def admin_login():
    username = entry_user.get()
    password = entry_pass.get()
    conn = sqlite3.connect('raj_lms.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM admin WHERE username=? AND password=?", (username, password))
    if cur.fetchone():
        open_admin()
    else:
        messagebox.showerror("Error", "Invalid Admin Credentials")
    conn.close()

def student_login():
    email = entry_user.get()
    password = entry_pass.get()
    conn = sqlite3.connect('raj_lms.db')
    cur = conn.cursor()
    cur.execute("SELECT id FROM students WHERE email=? AND password=?", (email, password))
    student = cur.fetchone()
    if student:
        open_student(student[0])
    else:
        messagebox.showerror("Error", "Invalid Student Credentials")
    conn.close()

# GUI
root = tk.Tk()
root.title("राज कम्प्युटर इन्स्टिट्यूट नायगाव")
root.geometry("500x450")
root.configure(bg="#f0f0f0")

# Logo display
try:
    img = Image.open("logo.jpeg")
    img = img.resize((150, 100), Image.Resampling.LANCZOS)
    logo_img = ImageTk.PhotoImage(img)
    tk.Label(root, image=logo_img, bg="#f0f0f0").pack(pady=10)
except:
    tk.Label(root, text="RAJ COMPUTER INSTITUTE", font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=10)

tk.Label(root, text="नायगाव", font=("Arial", 12), bg="#f0f0f0").pack()

frame = tk.Frame(root, bg="#f0f0f0")
frame.pack(pady=20)

tk.Label(frame, text="Email/Username:", bg="#f0f0f0").grid(row=0, column=0, padx=5, pady=5)
entry_user = tk.Entry(frame, width=25)
entry_user.grid(row=0, column=1, padx=5, pady=5)

tk.Label(frame, text="Password:", bg="#f0f0f0").grid(row=1, column=0, padx=5, pady=5)
entry_pass = tk.Entry(frame, show="*", width=25)
entry_pass.grid(row=1, column=1, padx=5, pady=5)

btn_admin = tk.Button(root, text="Admin Login", bg="blue", fg="white", width=20, command=admin_login)
btn_admin.pack(pady=5)

btn_student = tk.Button(root, text="Student Login", bg="green", fg="white", width=20, command=student_login)
btn_student.pack(pady=5)

root.mainloop()