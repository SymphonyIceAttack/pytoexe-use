import datetime

print("===================================")
print("      ЧАТ-БОТ ДЛЯ МЕССЕНДЖЕРА")
print("===================================")

def show_help():
    return """
Доступные команды:
/start  - запуск бота
/help   - список команд
/time   - текущее время
/date   - сегодняшняя дата
/echo   - повтор текста
/exit   - выход из программы
"""

while True:

    command = input("\nВведите команду: ")

    # Команда запуска
    if command == "/start":
        print("Бот успешно запущен!")

    # Помощь
    elif command == "/help":
        print(show_help())

    # Время
    elif command == "/time":
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        print("Текущее время:", current_time)

    # Дата
    elif command == "/date":
        current_date = datetime.datetime.now().strftime("%d.%m.%Y")
        print("Сегодняшняя дата:", current_date)

    # Повтор текста
    elif command == "/echo":
        text = input("Введите текст: ")
        print("Бот повторяет:", text)

    # Выход
    elif command == "/exit":
        print("Работа бота завершена.")
        break

    # Неизвестная команда
    else:
        print("Ошибка: команда не распознана")
        print("Введите /help для списка команд")