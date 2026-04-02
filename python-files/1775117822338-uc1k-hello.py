# hello.py
import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.title("Hello World")
root.geometry("400x200")
root.config(bg="#2c3e50")

label = tk.Label(root, text="Hello World!", font=("微软雅黑",24,"bold"), fg="white", bg="#2c3e50")
label.pack(pady=40)

def say_hello():
    messagebox.showinfo("提示", "你好！这是AI做的程序～")

btn = tk.Button(root, text="点我", font=("微软雅黑",14), bg="#3498db", fg="white", command=say_hello)
btn.pack()

root.mainloop()