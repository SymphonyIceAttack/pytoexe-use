import tkinter as tk
def say_hello():
   label.config(text="你好，Python！")
root = tk.Tk()
root.title("Tkinter示例")
label = tk.Label(root, text="点击按钮试试")
label.pack(pady=10)
btn = tk.Button(root, text="点击我", command=say_hello)
btn.pack(pady=5)
root.mainloop()
