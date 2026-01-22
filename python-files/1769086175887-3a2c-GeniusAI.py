import random

def start_bot():
    # Генерируем API ключ
    api_key = random.randint(1000, 9999)
    print(f"--- Ваш API KEY: {api_key} ---")
    print("_______________________________________")
    print("Привет! Я — GeniusAI.")
    
    # Проверка API ключа с защитой от ошибок
    try:
        user_input_key = int(input("Введите свой API key: "))
    except ValueError:
        print("Ошибка: API key должен состоять из цифр!")
        return

    if user_input_key != api_key:
        print("Неверный API key! Доступ запрещен.")
        return

    # Успешный вход
    name = input("Напиши своё имя: ")
    print(f"Привет, {name}!")
    print("Задавай вопросы (или напиши 'выход', чтобы закончить)")

    # Словарь с ответами (легко дополнять)
    responses = {
        "что по api": f"{api_key} — отличный ключ!",
        "пасхалко": "Ты наткнулся на пасхалку №1",
        "зачем создан этот чат": "Для общения",
        "кто я": f"Ты, {name}, обычный человек (или нет...)",
        "создатель": "tg: t.me/GeniusAI_info",
        "67": "Ты ребёнок!?",
        "кто ты": "Я... я GeniusAI.",
        "1488": "Ты наткнулся на пасхалку №2"
    }

    while True:
        # Приводим к нижнему регистру и убираем лишние пробелы
        query = input(f"\n[{name}]: ").lower().strip()

        if query in ["выход", "exit", "quit"]:
            print("Заходи еще")
            break
        
        # Специальная логика для имени
        if query == name.lower():
            print("Да, это имя тебе подходит")
            continue

        # Логика для секретных команд
        if query == "ILK":
            print("Access permission granted. Error detected. Stopping...")
            break
            
        if query == "create":
            password = input("Password: ")
            if password == "ILK":
                print("Creator: roma_ILK | PassKey: ILK")
            else:
                print("Access denied")
            continue

        # Поиск ответа в словаре
        if query in responses:
            print(f"[GeniusAI]: {responses[query]}")
        else:
            print("[GeniusAI]: Чтобы ваш вопрос добавили, напишите 'создатель'")

if __name__ == "__main__":
    start_bot()
