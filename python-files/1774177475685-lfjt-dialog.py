import socket
import threading
import time

host = socket.gethostname()
ip = socket.gethostbyname(host)
while True:
    print("Вы сервер или клиент?")
    print("1. Сервер")
    print("2. Клиент")
    user = 0
    try:
        user = int(input())
    except ValueError:
        print("Ошибка! Введите число 1 или 2.")
        print()
        continue

    if user == 1:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print()
        print("Надо выполнить небольшую настройку.")
        print("Введите порт. Это будет ваше место в сети. Можете выбрать любое число от 1 до 65535.")
        port = 0
        while True:
            try:
                port = int(input())
            except:
                print("Ошибка! Введите ЧИСЛО.")
                continue
            if port<=0 or port>65535:
                print("Ошибка! Введите число от 1 до 65535")
                continue
            else:
                try:
                    server.bind((ip, port))
                    break
                except:
                    print("Ошибка! Этот порт уже занят. Выберите другой.")
                    continue
        print()
        print("Ваш hostname -", host)
        print("Ваш ip -", ip)
        print("Ваш порт -", port)
        print("Клиент не сможет соеденится, если не будет знать ваш ip и порт.")
        print()
        print("Отлично! Сервер готов к открытию.")
        print("Нажмите Enter что бы открыть сервер.")
        input()
        server.listen()
        print("Сервер открыт и ждет подключений...")
        print()
        client, address = server.accept()
        print(address, "подключился!")

        def send_message():
            while True:
                mail = str(input())
                client.send(mail.encode('utf-8'))

        def accept_message():
            while True:
                message = client.recv(1024).decode('utf-8')
                print("client:", message)

        sending = threading.Thread(target=send_message)
        accepting = threading.Thread(target=accept_message)
        sending.start()
        accepting.start()

    elif user == 2:
        print("Во-первых, убедитесь, что сервер сейчас открыт. Затем введите данные для подключения:")
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            print("Введите ip сервера:")
            server_ip = input()
            print("Введите порт:")
            try:
                port = int(input())
            except:
                print("Введите ЧИСЛО, которое вам выдал сервер.")
                continue
            try:
                client.connect((server_ip, port))
                print("Успешное подключение!")
                break
            except:
                print("ip или порт неверны.")
                continue
        
        def send_message():
            while True:
                mail = str(input())
                client.send(mail.encode('utf-8'))

        def accept_message():
            while True:
                message = client.recv(1024).decode('utf-8')
                print("server:", message)

        sending = threading.Thread(target=send_message)
        accepting = threading.Thread(target=accept_message)
        sending.start()
        accepting.start()

    else:
        print("Ошибка! Введите число 1 или 2.")
        print()
        
    while True:
        time.sleep(1)
