import tkinter as tk
from tkinter import ttk


if 1 == 1:
    print("Программа запущенна")

def buttonclick():
    login_get = login.get()
    password_get = password.get()
    textprint_get = textprint.get('1.0',tk.END)
    if login_get and password_get:
        labelresult.config(text=f"привет,{login_get}! твой пароль{password_get}", fg = "green")
    elif not login_get and password_get:
        print("Ошибка 1")
        labelresult.config(text="Введите логин", fg="red")
    elif not password_get and login_get:
        print("Ошибка 1 ")
        labelresult.config(text="   Введите пароль", fg = "red")
    elif textprint_get:
        labelresult.config(text=f"Вы написали: {textprint_get}", fg = "green")



    else:
        print("Ошибка 1 ")
        labelresult.config(text="   Введите хоть что то", fg = "red")

def twobot():
    textprint_get = textprint.get('1.0',tk.END)
    if textprint_get:
        labelresult.config(text=f"Вам написали: {textprint_get}", fg="green")






l = [
    "reea"


]



win = tk.Tk()
win.geometry("300x300")
win["bg"]="green"
win.title("Опасный вирус очень очень!!!!!!!!!")
win.resizable(width=False, height=False)



textprint = tk.Text(win,width=10,height=0.5,bg="black",fg="cyan")
textprint.pack(pady=5)


label = tk.Label(win,text="введите ваше имя", font=("Arial Bold",12))
label.pack(pady=10)

login = tk.Entry(win,width=30)
login.pack(pady=5)

password = tk.Entry(win,width=30,show="*")
password.pack(pady=5)

button = tk.Button(win,text="отправить", command=twobot,bg="#FF8C00", fg="#FFFFFF")
button.pack(pady=9)

labelresult = tk.Label(win,text="", font=("Arial Bold",12))
labelresult.pack(pady=11)



button = tk.Button(win,text="поздороватся", command=buttonclick,bg="#FF8C00", fg="#FFFFFF")
button.pack(pady=7)











win.mainloop()