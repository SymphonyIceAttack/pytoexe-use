import time

# --- Встроенные тексты для тренировки ---
DEFAULT_TEXTS = [
    "Съешь ещё этих мягких французских булок да выпей же чаю.",
    "В чащах юга жил-был цитрус? Да, но фальшивый экземпляр!",
    "Python — это мощный и простой в изучении язык программирования."
]

def load_custom_text():
    """
    Запрашивает у пользователя ввод текста.
    Позволяет вставить текст из файла (через Ctrl+V) или напечатать свой.
    """
    print("\nВставьте свой текст ниже. Для переноса строки используйте Enter.")
    print("Чтобы закончить ввод, дважды нажмите Enter.")
    print("-" * 50)
    
    lines = []
    while True:
        line = input()
        if line == "": # Пустая строка завершает ввод
            break
        lines.append(line)
    
    return "\n".join(lines)

def calculate_metrics(original, user_input, elapsed_time):
    """
    Вычисляет скорость печати и точность.
    """
    original_len = len(original)
    user_len = len(user_input)

    # Подсчет ошибок (по символам)
    min_length = min(original_len, user_len)
    errors = sum(1 for i in range(min_length) if original[i] != user_input[i])
    # Разница в длине тоже считается за ошибки
    errors += abs(original_len - user_len)

    accuracy = ((original_len - errors) / original_len * 100) if original_len > 0 else 100
    speed_cpm = (user_len / elapsed_time) * 60 if elapsed_time > 0 else 0

    return round(accuracy, 2), round(speed_cpm, 2)

def main():
    print("=== Тренажер скорости печати ===\n")

    # Выбор текста
    print("1. Использовать встроенный текст")
    print("2. Вставить свой текст")
    choice = input("Ваш выбор (1 или 2): ").strip()

    if choice == '1':
        text_to_type = random.choice(DEFAULT_TEXTS)
        print(f"\nВыбран встроенный текст:\n{text_to_type}")
    elif choice == '2':
        text_to_type = load_custom_text()
        if not text_to_type:
            print("Вы ничего не ввели. Запуск отменен.")
            return
        print(f"\nВы ввели текст длиной {len(text_to_type)} символов.")
    else:
        print("Неверный выбор. Запуск отменен.")
        return

    # Подготовка к старту
    input("\nНажмите Enter, чтобы начать тест...")

    # Старт таймера и ввод текста
    start_time = time.time()
    user_input = input("\n> ")
    end_time = time.time()

    # Расчет результатов
    elapsed_time = end_time - start_time
    accuracy, speed = calculate_metrics(text_to_type, user_input, elapsed_time)

    # Вывод результатов
    print("\n--- Результаты ---")
    print(f"Время: {elapsed_time:.2f} сек")
    print(f"Скорость: {speed} знаков/мин")
    print(f"Точность: {accuracy}%")

if __name__ == "__main__":
    import random # Импортируем здесь, чтобы не загружать модуль при импортировании файла
    main()