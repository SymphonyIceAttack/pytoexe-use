from tkinter import*
from tkinter import ttk
import os
import winsound
import requests
import urllib.request
import hashlib
from tkinter.messagebox import showinfo, askyesno
import wget
from tkinter import colorchooser
from tkinter.colorchooser import askcolor

sound1 = 'sound1.wav'
sound2='Sound_11359.wav'


# Система уровней
level=0

if not os.path.exists('file.txt'):
    with open("file.txt", "x") as file:
        file.write(str(level))

with open("file.txt", "r") as file:
    content = file.read()

level=int(content)
print('Ваш общий престиж: '+str(level))

file.close()

# Регистрация\вход

def init_file():  # Инициализация файла, если этого не сделать програма вылетит м ошибкой, что файла нет
    """Создает файл пользователей"""
    if not os.path.exists('users.txt'):
        with open('users.txt', 'w'):
            pass


def add_user(login: str, password: str) -> bool:
    """Добавляет пользователя в файл"""
    with open('users.txt', 'r') as f:
        users = f.read().splitlines()  # Считываем всех пользователей из файла

    for user in users:
        args = user.split(':')
        if login == args[0]:  # Если логин уже есть, парль не проверяем, шанс взлома увеличится(кто-то мб узнает пароль)
            return False  # Тут можно написать что угодно, будь то HTML статус(409 - conflict), либо просто фразу ошибки

    with open('users.txt', 'a') as f:
        f.write(f'{login}:{password}\n')  # Добавляем нового пользователя
    return True


def get_user(login: str, password: str) -> bool:
    """Проверяет логин и пароль пользователя"""
    with open('users.txt', 'r') as f:
        users = f.read().splitlines()  # Считываем всех пользователей из файла

    for user in users:
        args = user.split(':')
        if login == args[0] and password == args[1]:  # Если пользователь с таким логином и паролем существует
            return True
    return False


def main_loop(login: str):
    """Главный цикл программы"""
    print(f'Привет, {login}!')  # Тут основная часть программы


init_file()

while True:
    print('''Добро пожаловать! Выберите пункт меню:
    1. Вход
    2. Регистрация
    3. Выход''')

    user_input = input()
    if user_input == '1':  # Условия можно заменить на: user_input.lower() == 'вход'
        print('Введите логин:')
        login = input()

        print('Введите пароль:')
        password = input()

        result = get_user(login, hashlib.sha256(password.encode()).hexdigest())

        if result:
            print('Вы вошли в систему')
            break  # Выходим из цикла
        else:
            print('Неверный логин или пароль')

    elif user_input == '2':
        print('Введите логин:')
        login = input()

        print('Введите пароль:')
        password = input()

        print('Повторите пароль:')
        password_repeat = input()

        if password != password_repeat:
            print('Пароли не совпадают!')
            continue

        result = add_user(login, hashlib.sha256(
            password.encode()).hexdigest())  # Вызываем функцию добавления пользователя. И хешируем пароль(безопасность)

        if not result:
            print('Пользователь с таким логином уже существует')
        else:
            print('Регистрация прошла успешно!')

    elif user_input == '3':
        print('Завершение работы')
        break  # Выходим из цикла



#Функции вкладок


def accaunt():
    global password

    window6=Tk()
    window6.title('Мой аккаунт')
    window6.geometry('600x500')
    window6.resizable(False,False)

    lbl4=Label(window6,text='Мой логин: '+login, font='Times 25')
    lbl4.pack(anchor=CENTER)


    def show_password():
        inform2=showinfo(f'Мой пароль',"Мой пароль:"+str(password)+'. Никому не говорите свой пароль!')


    btn1=Button(window6, text='Показать мой пароль', command=show_password)
    btn1.pack(anchor=CENTER)

    lbl5=Label(window6, text='Мой общий престиж(чтобы его обновить, перезагрузите приложение): '+str(level))
    lbl5.pack(anchor=CENTER)



def info():
    inform=showinfo("Подробнее о приложении", "Приложение создано для установки пиратских(не лицензионных) программ и игр.ВЫ берёте ответственность за свой компьютер!\nОбщий престиж- это цифра, которую можно увеличить кол-вом скачанных игр. Общий престиж увеличивается со всех аккаунтов, на которых вы скачивали игры. Если Вы хотети обнулить ваш престиж(что на вряд ли), то удалить файл под простым названием file.\nЕсли у Вас остались вопросы, то напишите свои мысли на нашем форуме, где с радостью ответят на Ваши вопросы!")

def info1():
    inform1=showinfo("Предстоящие обновления", "1.Кастомизация\n 2.Разработка форума\n 3.Упрощение регистрации")

def info2():
    inform2=showinfo("Форум", "Если у Вас остались вопросы, предложения или жалобы, то напишите ваши мысли в нашем форуме по ссылке:\nhttps://nexa.forumes.ru/. Там также будут сообщения об обновлении приложения")

def change_color(step=0):
    g = abs((step*8) % 512 - 255)
    b = 255 - g
    lbl.configure(fg=f"#00{g:0>2x}{b:0>2x}")
    lbl1.configure(fg=f"#00{g:0>2x}{b:0>2x}")
    lbly1.configure(fg=f"#00{g:0>2x}{b:0>2x}")
    root.after(5000 * 8 // 256, lambda: change_color(step+1))


#ЗДЕСЬ НАЧИНАЮТСЯ ИГРЫ И ПРОГРАММЫ <3

def terratia():
    global level
    global file

    file = open("data.txt", "w")

    url_terraria = 'https://thelastgame.ru/terraria/'

    file = requests.get(url_terraria)
    destination = 'Terraria_1.4.4.9v4.torrent'

    open(destination,'wb').write(file.content)

    lbl3.config(text='Торент-файл с Terraria уже скачан')

    level+=1
    with open("file.txt", "w") as file:
        file.write(str(level))



def picskel():
    window=Tk()
    window.title('Пиксельные игры')
    window.geometry('500x500')
    window.resizable(False,False)

    btn_terraria=Button(window,text='Скачать Terraria', command=terratia)
    btn_terraria.pack()

    window.mainloop()

    return window

def shooter():
    window1=Tk()
    window1.title('Шутер')
    window1.geometry('500x500')
    window1.resizable(False,False)

    window1.mainloop()

    return window1

def survival():
    window2=Tk()
    window2.title('Выживание')
    window2.geometry('500x500')
    window2.resizable(False,False)

    window2.mainloop()

    return window2

def golovolomki():
    window3=Tk()
    window3.title('Головоломки')
    window3.geometry('500x500')
    window3.resizable(False,False)



    window3.mainloop()

    return window3

def simulator():
    window4=Tk()
    window4.title('Симуляторы')
    window4.geometry('500x500')
    window4.resizable(False,False)

    window4.mainloop()


root=Tk()
root.title('Nexa')
root.geometry('700x800')
root.resizable(False,False)


#Интерфейс


menu = Menu()

menu.add_cascade(label="Мой аккаунт",  background="black", command=accaunt)
menu.add_cascade(label="Подробнее о приложении",  background="black", command=info)
menu.add_cascade(label="Предстоящие обновления",  background="black", command=info1)
menu.add_cascade(label="Форум",  background="black", command=info2)

lbl=Label(text='Добро пожаловать в Nexa!', font='Times 30')
lbl.pack()

lbl2=Label(text='Это приложение для установки пиратских игр. Некоторые игры не имеют мультиплеер!', font='Times 10')
lbl2.pack()

lbl3=Label(text='', font='Times 20')
lbl3.pack()

lbl1=Label(text='●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●', font='Times 20')
lbl1.pack()

lbly1=Label(text='●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●', font='Times 20')
lbly1.pack(side=BOTTOM)

pic=Button(text='Пиксельные игры', command=picskel, font='Times 20')
pic.pack()

pic1=Button(text='Шутеры', command=shooter, font='Times 20')
pic1.pack()

pic2=Button(text='Выживание', command=survival, font='Times 20')
pic2.pack()

pic3=Button(text='Головоломки', command=golovolomki, font='Times 20')
pic3.pack()

pic4=Button(text='Симуляторы', command=simulator, font='Times 20')
pic4.pack()


root.after(1, change_color)

root.config(menu=menu)
root.mainloop()
