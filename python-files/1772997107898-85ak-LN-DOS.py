import os

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
        directory = input("Введите имя новой директории: ")
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
        print("просмотр - Посмотреть файлы, находящиеся в данной директории.")
        print("создать - Добавить файл в данную директоррию.")
        print("удалить - Удалить файл из системы.")
        print("создать папку - Создать папку в данную директорию.")
        print("удалить папку - Удалить папку из данной директории.")
        print("выход - Выйти из приложения.")

    elif command == "выход":
        break

    else:
        print("Неверная команда!")

print("Работа завершена.")