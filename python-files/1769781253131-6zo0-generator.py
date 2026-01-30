import random
def parse_numbers(s: str):
    # поддержка ввода "1 2 3" или "1,2,3"
    parts = s.replace(",", " ").split()
    if not parts:
        raise ValueError("Пустой список чисел")
    nums = []
    for p in parts:
        # можно вводить и целые, и дробные
        nums.append(float(p) if "." in p else int(p))
    return nums
def main():
    print("Генератор случайного выбора из введённых чисел")
    raw = input("Введите числа (через пробел или запятую): ").strip()
    try:
        numbers = parse_numbers(raw)
    except ValueError as e:
        print("Ошибка:", e)
        return
    print(f"Список: {numbers}")
    mode = input("Режим: 1 — выбрать одно число, 2 — выбрать несколько: ").strip() or "1"
    if mode == "1":
        choice = random.choice(numbers)
        print("Случайный выбор:", choice)
        return
    # mode == "2"
    try:
        k = int(input("Сколько чисел выбрать? ").strip())
        if k <= 0:
            raise ValueError
    except ValueError:
        print("Ошибка: введите целое число > 0")
        return
    repl = input("Повторения допустимы? (y/n): ").strip().lower() or "n"
    if repl == "y":
        result = random.choices(numbers, k=k)  # с повторениями
    else:
        if k > len(numbers):
            print("Ошибка: без повторений нельзя выбрать больше, чем есть в списке")
            return
        result = random.sample(numbers, k=k)   # без повторений
    print("Результат:", result)
if __name__ == "__main__":
    main()
