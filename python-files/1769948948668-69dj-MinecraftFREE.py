import tkinter as tk
window = tk.Tk()
window.title("Опасный вирус")
window.geometry("500x400")
label = tk.Label(window, text="Я самый опасный вирус."
                              "Т.к я еще делаюсь разошли его 10 друзьям")
label.pack()
window.mainloop()