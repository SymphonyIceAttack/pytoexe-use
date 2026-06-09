print("Введите пароль")
a = int(input(""))
if a == 2938 :
    открыть = input("Открыть из: Конфигуратор, Сайт, Инструкция, amnezia приложение, ")
    if открыть == "Конфигуратор" :
        import random

        fruits = ["https://drive.google.com/uc?export=download&confirm=no_antivirus&id=1qZ_9SYKoSXEAXi71BCUy5E2D4kFmgD5T  Скачайте и вставьте","https://drive.google.com/uc?export=download&confirm=no_antivirus&id=132sPE7BUAjEonC5Myi1pr9D5S0oMmEq0  Скачайте и вставьте","https://drive.google.com/uc?export=download&confirm=no_antivirus&id=1IhnnN0CceOqTAboKNGkW2KtIsXYzNb8o  Скачайте и вставьте"]
        random_fruit = random.choice(fruits)
        print(random_fruit)
    elif открыть == "Инструкция":
        print("1. Нажмите «Файл с настройками», или «Импорт туннелей из файла» 2. Импортируйте «WARP-(X)» 3. Подключите")
    elif открыть == "amnezia приложение":
        print("скачать приложение для apple: https://apps.apple.com/us/app/amneziawg/id6478942365,  для Windows: https://drive.google.com/drive/folders/1zt6hTSr6nCp4ZH7jffWwe7EWnjXsFvKD?usp=sharing,  для Android: https://play.google.com/store/apps/details?id=org.amnezia.awg&hl=en")
    elif открыть == "Сайт":
        print("amnezia.org")
else:
    print("Не верный пароль")
input("Чтобы закрыть, введите текст и нажмите enter ")