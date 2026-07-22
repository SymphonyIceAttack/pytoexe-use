"""
Фейковая программа "очистки диска".
Никакие файлы реально не удаляются и не изменяются —
это просто визуальная имитация процесса для шутки/демонстрации.
"""

import time
import random
import sys


def print_progress_bar(percent, width=40):
    filled = int(width * percent // 100)
    bar = "█" * filled + "░" * (width - filled)
    sys.stdout.write(f"\r[{bar}] {percent:3d}%")
    sys.stdout.flush()


def fake_scan_stage(title, duration=2.0):
    print(f"\n{title}")
    steps = 100
    for i in range(steps + 1):
        print_progress_bar(i)
        time.sleep(duration / steps)
    print()


def main():
    print("=" * 50)
    print("   Средство очистки диска (демо-версия)")
    print("=" * 50)

    input("\nНажмите Enter, чтобы начать 'очистку'...")

    stages = [
        "Поиск временных файлов...",
        "Анализ кэша браузеров...",
        "Проверка корзины...",
        "Поиск дубликатов файлов...",
        "Очистка системного кэша...",
    ]

    total_freed = 0

    for stage in stages:
        fake_scan_stage(stage, duration=random.uniform(1.0, 2.0))
        freed = random.randint(50, 900)
        total_freed += freed
        print(f"   Найдено и 'очищено': {freed} МБ")

    print("\n" + "=" * 50)
    print("Очистка завершена!")
    print(f"Всего 'освобождено' места: {total_freed} МБ "
          f"({total_freed / 1024:.2f} ГБ)")
    print("=" * 50)
    print("\n(Это фейковая демонстрация — реальные файлы не были затронуты)")


if __name__ == "__main__":
    main()
