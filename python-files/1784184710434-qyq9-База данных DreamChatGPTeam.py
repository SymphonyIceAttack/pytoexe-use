while True:
    a = input("Напишите имя любого участника dream chatGPTeam, а программа назовет его фамилию и юзер: ").lower()
    while a != 'костя' and a != 'макар' and a != 'дима' and a != 'савелий' and a != 'андрей' and a != 'илья' and a != 'артем':
        a = input("Вы указали неверное имя, попробуйте снова: ").lower()
    if a == "костя":
        print ("Ответ: Костя Кузнецов (@Luzeq)")
    elif a == "макар":
        print ("Ответ: Макар Зрюмов (@essemseller)")
    elif a == "артем":
        print ("Ответ: Артем Битнер (@BitnerBAD1)")
    elif a == "дима":
        print ("Ответ: Дима Скоробогатов (@gaz_vpolas) или Дима Тихомиров (@Stariybogsdec)")
    elif a == "илья":
        print ("Ответ: Илья Балакирев (@ppeeppeerrr)")
    elif a == "савелий":
        print ("Ответ: Савелий Барсуков (@praying4fuksumn)")
    elif a == "андрей":
        print ("Ответ: Андрей Чуркин (@kai_angel_immortal)")

    while True:
        b = input('Хотите продолжить? (да/нет): ').lower()
        while b != "да" and b != "нет":
            b = input("Такого ответа нет, попробуйте снова: ").lower()
        if b == 'да':
            break
        elif b == 'нет':
            print("Игра окончена, приходите снова!")
            exit()