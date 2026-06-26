import os
import re
import glob
from datetime import datetime
from openpyxl import load_workbook


def clean_number(raw_value):
    """Удаляет все пробелы и приводит к верхнему регистру."""
    if raw_value is None:
        return ''
    cleaned = ''.join(str(raw_value).split())
    return cleaned.upper()


def is_valid_number(value):
    """Проверяет формат: две буквы (латиница/кириллица), дефис, ровно 6 цифр."""
    pattern = re.compile(r'^[A-ZА-Я]{2}-\d{6}$')
    return bool(pattern.match(value))


def process_excel_file(file_path):
    """
    Читает столбец H начиная с 7-й строки до первой пустой ячейки.
    Возвращает список кортежей (значение_для_SQL, номер_строки).
    """
    results = []
    wb = load_workbook(file_path, data_only=True)
    sheet = wb.active

    row = 7
    while True:
        cell = sheet[f'H{row}']
        raw_value = cell.value
        if raw_value is None or (isinstance(raw_value, str) and raw_value.strip() == ''):
            break

        cleaned = clean_number(raw_value)
        if is_valid_number(cleaned):
            results.append((cleaned, row))
        else:
            error_label = f"ОШИБКА_Файл_{os.path.basename(file_path)}_строка_{row}"
            results.append((error_label, row))
        row += 1

    wb.close()
    return results


def main():
    # Определяем базовую папку (там, где лежит .exe)
    if getattr(sys, 'frozen', False):
        # Запущено как скомпилированный .exe
        base_dir = os.path.dirname(sys.executable)
    else:
        # Запущено как скрипт Python (для отладки)
        base_dir = os.getcwd()

    # Папка с отчётами
    reports_dir = os.path.join(base_dir, "ВК")
    if not os.path.isdir(reports_dir):
        print(f"Папка 'ВК' не найдена по пути: {reports_dir}")
        input("Нажмите Enter для выхода...")
        return

    # Ищем все .xlsx файлы в папке ВК (без рекурсии)
    excel_files = glob.glob(os.path.join(reports_dir, '*.xlsx'))
    if not excel_files:
        print(f"В папке '{reports_dir}' нет файлов .xlsx")
        input("Нажмите Enter для выхода...")
        return

    all_numbers = []
    error_summary = []

    for file_path in excel_files:
        print(f"Обработка: {os.path.basename(file_path)}")
        try:
            file_results = process_excel_file(file_path)
            for value, row in file_results:
                all_numbers.append(value)
                if value.startswith("ОШИБКА_"):
                    error_summary.append((file_path, row, value))
        except Exception as e:
            print(f"  Ошибка при открытии {file_path}: {e}")
            continue

    if not all_numbers:
        print("Не найдено ни одного номера в отчётах.")
        input("Нажмите Enter для выхода...")
        return

    # Формируем SQL-запрос
    array_lines = ",\n".join([f"'{v}'" for v in all_numbers])
    sql_query = f"SELECT * FROM find (array[\n{array_lines}\n]);"

    # Готовим имя файла с текущей датой
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = os.path.join(base_dir, f"селект готовое_{today}.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(sql_query)

    print(f"\nSQL-запрос сохранён: {output_file}")

    # Если есть ошибки – сохраняем отдельный отчёт
    if error_summary:
        print("\nОбнаружены некорректные номера (заменены метками в SQL):")
        for _, _, label in error_summary:
            print(f"  {label}")

        error_file = os.path.join(base_dir, f"ошибки_номеров_{today}.txt")
        with open(error_file, "w", encoding="utf-8") as ef:
            ef.write("Список некорректных номеров:\n")
            for file_path, row, label in error_summary:
                ef.write(f"{label}\n")
        print(f"Детали ошибок сохранены в: {error_file}")
    else:
        print("Все номера корректны.")

    input("Готово! Нажмите Enter для завершения...")


if __name__ == "__main__":
    import sys
    main()