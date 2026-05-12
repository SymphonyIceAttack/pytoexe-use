import sys
import os
from datetime import datetime

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================


def time_to_seconds(time_str):
    h, m, s = map(int, time_str.split(":"))
    return h * 3600 + m * 60 + s


def seconds_to_hms(total_sec):
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    seconds = total_sec % 60

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def sum_seconds(time_list):
    return sum(time_to_seconds(t) for t in time_list)


# ==================== ОСНОВНАЯ ФУНКЦИЯ ====================


def read_and_sum_times(filename):

    grand_total_sec = 0
    grand_nonprod_sec = 0
    grand_support_sec = 0
    grand_dev_sec = 0

    with open(filename, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            if not line:
                print(f"Строка {line_num} пустая — пропуск")
                continue

            times = line.split("\t")

            # проверка количества элементов
            if len(times) < 5:
                print(
                    f"Ошибка в строке {line_num}: "
                    f"элементов меньше 5 ({len(times)}) — строка пропущена"
                )
                continue

            if len(times) > 5:
                print(
                    f"Ошибка в строке {line_num}: "
                    f"элементов больше 5 ({len(times)}) — строка пропущена"
                )
                continue

            # проверка формата времени
            invalid_time = False

            for t in times:
                try:
                    h, m, s = map(int, t.split(":"))

                    if m > 59 or s > 59:
                        raise ValueError

                except Exception:
                    print(f"Ошибка в строке {line_num}: неверный формат времени '{t}'")
                    invalid_time = True
                    break

            if invalid_time:
                continue

            # общая длительность
            total_sec = sum_seconds(times)

            # непродуктивная деятельность
            nonprod = times[0:2]
            nonprod_sec = sum_seconds(nonprod)

            # поддерживающая работа
            support = [times[2]]
            support_sec = sum_seconds(support)

            # развивающая работа
            dev = times[3:5]
            dev_sec = sum_seconds(dev)

            # минуты
            total_min = total_sec // 60
            nonprod_min = nonprod_sec // 60
            support_min = support_sec // 60
            dev_min = dev_sec // 60

            # проценты
            if total_min > 0:
                percent_nonprod = (nonprod_min / total_min) * 100

                percent_support = (support_min / total_min) * 100

                percent_dev = (dev_min / total_min) * 100

            else:
                percent_nonprod = 0
                percent_support = 0
                percent_dev = 0

            # вывод
            print("=" * 60)
            print(f"Тренировка #{line_num}")
            print(f"Исходные данные: {times}")

            print()
            print("Продолжительность тренировки:")
            print(f"  {total_min} мин")

            print()
            print("Непродуктивная деятельность:")
            print(f"  {nonprod_min} мин")
            print(f"  {percent_nonprod:.1f}%")

            print()
            print("Поддерживающая работа:")
            print(f"  {support_min} мин")
            print(f"  {percent_support:.1f}%")

            print()
            print("Развивающая работа:")
            print(f"  {dev_min} мин")
            print(f"  {percent_dev:.1f}%")

            print()

            # общая статистика
            grand_total_sec += total_sec
            grand_nonprod_sec += nonprod_sec
            grand_support_sec += support_sec
            grand_dev_sec += dev_sec

    # итог
    grand_total_min = grand_total_sec // 60
    grand_nonprod_min = grand_nonprod_sec // 60
    grand_support_min = grand_support_sec // 60
    grand_dev_min = grand_dev_sec // 60

    if grand_total_min > 0:
        grand_percent_nonprod = (grand_nonprod_min / 810) * 100

        grand_percent_support = (grand_support_min / 810) * 100

        grand_percent_dev = (grand_dev_min / 810) * 100

    else:
        grand_percent_nonprod = 0
        grand_percent_support = 0
        grand_percent_dev = 0

    print()
    print("#" * 60)
    print("ОБЩАЯ СТАТИСТИКА ПО ВСЕМ ТРЕНИРОВКАМ")
    print("#" * 60)

    print()
    print("Продолжительность ВСЕХ тренировок:")
    print(f"  {grand_total_min} мин")

    print()
    print("Сумма непродуктивной деятельности:")
    print(f"  {grand_nonprod_min} мин")
    print(f"  {grand_percent_nonprod:.1f}%")

    print()
    print("Сумма поддерживающей работы:")
    print(f"  {grand_support_min} мин")
    print(f"  {grand_percent_support:.1f}%")

    print()
    print("Сумма развивающей работы:")
    print(f"  {grand_dev_min} мин")
    print(f"  {grand_percent_dev:.1f}%")


# ==================== ТОЧКА ВХОДА ====================

if __name__ == "__main__":
    try:
        # если txt перетащили на exe
        if len(sys.argv) > 1:
            file = sys.argv[1]

        # иначе ищем data.txt рядом с exe
        else:
            file = "data.txt"

        # проверка существования файла
        if not os.path.exists(file):
            print(f"Файл не найден: {file}")
            input("\nНажмите Enter для выхода...")
            sys.exit(1)

        # имя output файла
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = f"output_{timestamp}.txt"

        # сохраняем stdout
        original_stdout = sys.stdout

        with open(output_file, "w", encoding="utf-8") as out:
            # дублируем вывод и в консоль и в файл
            class Tee:
                def __init__(self, *files):
                    self.files = files

                def write(self, obj):
                    for f in self.files:
                        f.write(obj)
                        f.flush()

                def flush(self):
                    for f in self.files:
                        f.flush()

            sys.stdout = Tee(sys.stdout, out)

            print(f"Обработка файла: {file}")
            print(f"Результат сохраняется в: {output_file}")
            print()

            read_and_sum_times(file)

        # возвращаем stdout
        sys.stdout = original_stdout

        print()
        print(f"Результат сохранён в файл:")
        print(output_file)

    except Exception as e:
        print(f"\nОшибка: {e}")

    # чтобы окно не закрывалось
    input("\nНажмите Enter для выхода...")
