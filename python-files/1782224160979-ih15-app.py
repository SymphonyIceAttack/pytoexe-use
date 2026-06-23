import tkinter as tk

def say_hello():
    label.config(text="Привет, Матвей! Это твой .exe")

root = tk.Tk()
root.title("Мое приложение")
root.geometry("300x200")

label = tk.Label(root, text="Нажми кнопку")
label.pack(pady=20)

button = tk.Button(root, text="Нажми меня", command=say_hello)
button.pack()

root.mainloop()