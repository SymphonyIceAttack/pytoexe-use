# -*- coding: utf-8 -*-
"""
Программа подбора марок для письма (Windows-версия) от Ахмадеева А А
"""

import sys
import os

# На Windows часто нужна явная настройка кодировки консоли
if sys.platform == "win32":
    # Пытаемся установить utf-8, если не получается — оставляем как есть
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Для старых версий Python
        import codecs

        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach(), 'replace')
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach(), 'replace')

    # Также можно попробовать включить виртуальный терминал (Windows 10+)
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        pass

# Данные о марках (актуальные на момент написания)
stamps = [
    {"value": 50.00, "count": 139},
    {"value": 10.00, "count": 299},
    {"value": 4.00, "count": 3},
    {"value": 3.00, "count": 80},
    {"value": 2.00, "count": 20},  # было 1.92 → заменил на 2.00 (как в твоём последнем коде)
    {"value": 1.00, "count": 4},  # было 0.98 → заменил на 1.00
]


def make_change(target_rub):
    target_kop = int(round(target_rub * 100))
    values_kop = [int(round(s["value"] * 100)) for s in stamps]
    counts = [s["count"] for s in stamps]

    INF = 10 ** 9
    dp = [INF] * (target_kop + 1)
    dp[0] = 0

    prev = [None] * (target_kop + 1)

    for i in range(len(values_kop)):
        v = values_kop[i]
        if v == 0:
            continue
        max_k = min(counts[i], target_kop // v)

        for already in range(target_kop, -1, -1):
            if dp[already] == INF:
                continue
            for k in range(1, max_k + 1):
                new_sum = already + k * v
                if new_sum > target_kop:
                    break
                new_count = dp[already] + k
                if new_count < dp[new_sum]:
                    dp[new_sum] = new_count
                    used = [0] * len(stamps) if prev[already] is None else prev[already][:]
                    used[i] += k
                    prev[new_sum] = used

    if dp[target_kop] == INF:
        return None, None

    used = prev[target_kop]
    result_lines = []
    total = 0

    for i, cnt in enumerate(used):
        if cnt > 0:
            result_lines.append(f"{cnt} шт. × {stamps[i]['value']:.2f} руб.")
            total += cnt

    # Сортируем по убыванию номинала
    result_lines.sort(key=lambda x: float(x.split('×')[1].strip().split()[0]), reverse=True)

    return total, result_lines


def main():
    os.system('cls' if os.name == 'nt' else 'clear')  # очистка экрана в Windows

    print("═" * 50)
    print("  ПОДБОР МАРОК ДЛЯ ПИСЬМА  (Windows версия)")
    print("═" * 50)
    print("Доступные марки и остатки:\n")

    for s in stamps:
        print(f"  {s['value']:6.2f} руб.  —  {s['count']:3d} шт.")

    print("\n" + "─" * 50)
    print("Введите сумму письма в рублях (например: 76  или  144,50)")
    print("Для выхода наберите:  exit  или  q  или  выход\n")

    while True:
        try:
            line = input("Сумма → ").strip()

            if line.lower() in ("exit", "q", "quit", "выход", "вых", ""):
                print("\nДо свидания!")
                input("\nНажмите Enter для закрытия окна...")
                sys.exit(0)

            amount = float(line.replace(",", "."))

            if amount <= 0:
                print("Ошибка: сумма должна быть больше 0\n")
                continue

            total, lines = make_change(amount)

            print("\n" + "─" * 50)
            if total is None:
                print("НЕВОЗМОЖНО подобрать точную сумму с текущим запасом марок\n")
            else:
                print(f"Всего марок: {total}")
                for line in lines:
                    print("   " + line)
                print()

        except ValueError:
            print("Ошибка: введите число (например 80.5) или exit\n")
        except KeyboardInterrupt:
            print("\nПрограмма прервана")
            input("Нажмите Enter для выхода...")
            break


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\nПроизошла ошибка:")
        print(e)
        input("\nНажмите Enter для закрытия...")