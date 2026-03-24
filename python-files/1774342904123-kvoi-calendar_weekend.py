import calendar
from datetime import date, timedelta
import os

def generate_weekends(start_date, pattern=(1, 3), gap=2, limit_days=365):
    """
    Генерирует множество выходных дней по циклу:
    pattern = (1, 3) → 1 день, потом 3 дня, и т.д.
    gap = 2 → между блоками 2 рабочих дня
    """
    weekends = set()
    current = start_date
    pattern_index = 0

    while len(weekends) < limit_days:
        block_size = pattern[pattern_index]

        # Добавляем блок выходных
        for i in range(block_size):
            weekends.add(current + timedelta(days=i))

        # Переход к следующему блоку
        current += timedelta(days=block_size + gap)
        pattern_index = (pattern_index + 1) % len(pattern)

    return weekends


def print_month(year, month, weekends):
    cal = calendar.Calendar(firstweekday=0)

    RED = "\033[91m"
    RESET = "\033[0m"

    print(f"Выхи Ленчика\n{calendar.month_name[month]} {year}")
    print(" Пн  Вт  Ср  Чт  Пт  Сб  Вс")

    for week in cal.monthdatescalendar(year, month):
        row = ""
        for day in week:
            if day.month != month:
                row += "    "
            elif day in weekends:
                row += f"{RED}{day.day:>3}{RESET} "
            else:
                row += f"{day.day:>3} "
        row += " "
        print(row)


# 🔧 ЯКОРЬ (из твоего марта)
start = date(2026, 3, 3)  # одиночный выходной

# Генерируем на длительный период
weekends = generate_weekends(start, limit_days=1000)

year = int(input("Введите год:"))
month = int(input("Введите месяц (01-12):"))
os.system('cls' if os.name == 'nt' else 'clear')
# Выводим апрель 2026
print_month(year, month, weekends)