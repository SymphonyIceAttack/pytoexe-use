import os
import sys
from pathlib import Path

def process_mif(source_path):
    # 1. Формируем путь для выходного файла
    src_file = Path(source_path)
    output_file = src_file.with_name(f"{src_file.stem}_.mif")

    # 2. Встроенный шаблон из 8 строк (больше не нужен внешний файл)
    header = [
        'VERSION 300',
        'Charset "WindowsCyrillic"',
        'Delimiter ","',
        'CoordSys NonEarth Units "m" Bounds (2000, 2000) (50000, 60000)',
        'COLUMNS 1',
        'NFILD Char(20)',
        'DATA',
        'REGION 1'
    ]

    # 3. Читаем исходный файл
    with open(source_path, 'r', encoding='utf-8') as f:
        source_lines = [line.rstrip('\n') for line in f.readlines()]

    # 4. Ищем строку с "Region 1" и извлекаем число
    region_idx = -1
    region_number = ""
    for i, line in enumerate(source_lines):
        if line.strip().upper().startswith("REGION 1"):
            region_idx = i
            parts = line.strip().split()
            if len(parts) > 1:
                region_number = parts[1]
            break
    
    if region_idx == -1:
        print(f"Ошибка: в файле '{source_path}' не найдена строка 'Region 1'.")
        return

    # 5. Собираем новый файл
    new_lines = header[:]
    
    # Переносим цифру на 9-ю строку
    if region_number:
        new_lines.append(region_number)

    # 6. Обрабатываем остальные строки (начиная со строки после Region 1)
    for line in source_lines[region_idx + 1:]:
        stripped = line.strip()
        if not stripped:
            continue
        
        parts = stripped.split()
        # Проверяем, является ли строка координатами (два числа)
        if len(parts) >= 2:
            try:
                float(parts[0])
                float(parts[1])
                # Меняем колонки местами
                new_lines.append(f"{parts[1]} {parts[0]}")
                continue
            except ValueError:
                pass
        
        # Если это не координаты (например, PEN или Brush), оставляем без изменений
        new_lines.append(stripped)

    # 7. Сохраняем результат
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
        
    print(f"✅ Готово! Файл успешно обработан и сохранен как: {output_file}")

if __name__ == "__main__":
    # Определяем путь к исходному файлу
    if len(sys.argv) > 1:
        source_file = sys.argv[1]
    else:
        source_file = input("Введите путь к исходному файлу (или перетащите файл в окно консоли): ").strip().strip('"')
    
    # Проверяем существование файла
    if not os.path.exists(source_file):
        print(f"❌ Исходный файл не найден: {source_file}")
    else:
        process_mif(source_file)
        
    input("\nНажмите Enter для выхода...")