import random


def fmt(x: float):
    """Возвращает int, если число целое, иначе float без изменений"""
    return int(x) if x.is_integer() else x


def print_result(data):
    """Форматированный вывод списка чисел"""
    print("Результат:", [fmt(x) for x in data])


try:
    # Чтение и преобразование входных данных
    nums = [float(x) for x in input("Введите числа через пробел: ").split()]
    if not nums:
        raise ValueError

    print(
        "\n1 — По возрастанию"
        "\n2 — По убыванию"
        "\n3 — Уникальные + сортировка"
        "\n4 — Мин / Макс / Среднее"
        "\n5 — Случайное перемешивание"
    )

    match input("Выбор (1–5): "):
        case "1":
            print_result(sorted(nums))

        case "2":
            print_result(sorted(nums, reverse=True))

        case "3":
            print_result(sorted(set(nums)))

        case "4":
            total = sum(nums)
            count = len(nums)
            print(
                "Минимум:", fmt(min(nums)),
                "\nМаксимум:", fmt(max(nums)),
                "\nСреднее:", fmt(total / count)
            )

        case "5":
            random.shuffle(nums)
            print_result(nums)

        case _:
            print("Ошибка: неверный пункт меню")

except ValueError:
    print("Ошибка: введите корректные числа")

input("\nНажмите Enter для выхода...")