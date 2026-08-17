import random
import math

while True:
    try:
        user_number = float(input("Введите число: "))
        break
    except ValueError:
        print("Ошибка! Введите число, а не текст.")

random_factor = random.uniform(0.0, 2.0)
result = user_number * random_factor

# Строгое математическое округление (0.5 всегда вверх)
rounded_result = math.floor(result + 0.5)

print(f"Случайный множитель: {random_factor:.4f}")
print(f"Результат умножения: {result:.4f}")
print(f"Округлённое число: {rounded_result}")