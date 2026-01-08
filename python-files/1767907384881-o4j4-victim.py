import tkinter as tk

root = tk.Tk()
root.title("Пример")
root.geometry("300x150")

label = tk.Label(root, text="Привет, мир!", font=("Arial", 14))
label.pack(pady=40)

root.mainloop()