import os
import subprocess

print("LN-DOS 2.0")

while True:
    command = input("Введите команду: ")

    if command == "просмотр":
        files = os.listdir()
        for file in files:
            print(file)

    elif command == "создать":
        file_name = input("Введите имя нового файла: ")
        file = open (file_name, "w")
        file.close()
        print("Файл создан!")

    elif command == "создать папку":
        directory = input("Введите имя новой папки: ")
        os.mkdir(directory)

    elif command == "удалить":
        file_name = input("Введите имя файла: ")
        if os.path.exists(file_name):
            os.remove(file_name)
            print("Файл удалён!")
        else:
            print("Такого файла не существует!")

    elif command == "удалить папку":
        directory = input("Введите имя папки для удаления:")
        os.rmdir(directory)

    elif command == "помощь":
        print("список команд")
        print("просмотр - Посмотреть файлы, находящиеся в данной дериктории.")
        print("создать - Добавить файл в данную директорию.")
        print("удалить - Удалить файл из системы.")
        print("создать папку - Создать папку в данную директорию.")
        print("удалить папку - Удалить папку из данной директории.")
        print("выход - Выйти из приложения.")
        print("переименовать - Переименовать файл или папку")
        print("проводник - Открыть проводник Windows")
        print("блокнот - Открыть блокнот Windows")
        
    elif command == "переименовать":
        old_name = input("Введите текущее имя файла или папки")
        new_name = input("Введите новое имя файла или папки")
        os.rename(old_name, new_name)

    elif command == "проводник":
        os.system("C:\windows\explorer.exe")

    elif command == "блокнот":
        os.system("C:\windows\notepad.exe")

    elif command == "выход":
        break

    else:
        print("Неверная команда!")

print("Работа завершена.") 