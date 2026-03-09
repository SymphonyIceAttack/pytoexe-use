import os

while True:
    # Получить путь к папке (Тут надо ввести)
    folder_path = input("Введите путь к папке (или 'exit' для выхода): ")

    if folder_path.lower()== 'exit':
        print("Выход осуществляется...")
        break

    #Проверяем существует ли указанная папка
    if not os.path.exists(folder_path):
        print("Папка не найдена. Попробуйте ещё раз.")
        continue

    #Отображаем содержымое
    print("Посмотри вниз.")
    print("Содержимое папки:")
    for filename in os.listdir(folder_path):
        print(filename)

    input("Нажмите энтер для продолжения.")