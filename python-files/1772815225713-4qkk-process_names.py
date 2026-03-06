import struct
import csv

# Таблица CRC8 (полная как в SQL)
CRC8_TABLE = {
    0: 0, 1: 94, 2: 188, 3: 226, 4: 97, 5: 63, 6: 221, 7: 131,
    8: 194, 9: 156, 10: 126, 11: 32, 12: 163, 13: 253, 14: 31, 15: 65,
    16: 157, 17: 195, 18: 33, 19: 127, 20: 252, 21: 162, 22: 64, 23: 30,
    24: 95, 25: 1, 26: 227, 27: 189, 28: 62, 29: 96, 30: 130, 31: 220,
    32: 35, 33: 125, 34: 159, 35: 193, 36: 66, 37: 28, 38: 254, 39: 160,
    40: 225, 41: 191, 42: 93, 43: 3, 44: 128, 45: 222, 46: 60, 47: 98,
    48: 190, 49: 224, 50: 2, 51: 92, 52: 223, 53: 129, 54: 99, 55: 61,
    56: 124, 57: 34, 58: 192, 59: 158, 60: 29, 61: 67, 62: 161, 63: 255,
    64: 70, 65: 24, 66: 250, 67: 164, 68: 39, 69: 121, 70: 155, 71: 197,
    72: 132, 73: 218, 74: 56, 75: 102, 76: 229, 77: 187, 78: 89, 79: 7,
    80: 219, 81: 133, 82: 103, 83: 57, 84: 186, 85: 228, 86: 6, 87: 88,
    88: 25, 89: 71, 90: 165, 91: 251, 92: 120, 93: 38, 94: 196, 95: 154,
    96: 101, 97: 59, 98: 217, 99: 135, 100: 4, 101: 90, 102: 184, 103: 230,
    104: 167, 105: 249, 106: 27, 107: 69, 108: 198, 109: 152, 110: 122, 111: 36,
    112: 248, 113: 166, 114: 68, 115: 26, 116: 153, 117: 199, 118: 37, 119: 123,
    120: 58, 121: 100, 122: 134, 123: 216, 124: 91, 125: 5, 126: 231, 127: 185,
    128: 140, 129: 210, 130: 48, 131: 110, 132: 237, 133: 179, 134: 81, 135: 15,
    136: 78, 137: 16, 138: 242, 139: 172, 140: 47, 141: 113, 142: 147, 143: 205,
    144: 17, 145: 79, 146: 173, 147: 243, 148: 112, 149: 46, 150: 204, 151: 146,
    152: 211, 153: 141, 154: 111, 155: 49, 156: 178, 157: 236, 158: 14, 159: 80,
    160: 175, 161: 241, 162: 19, 163: 77, 164: 206, 165: 144, 166: 114, 167: 44,
    168: 109, 169: 51, 170: 209, 171: 143, 172: 12, 173: 82, 174: 176, 175: 238,
    176: 50, 177: 108, 178: 142, 179: 208, 180: 83, 181: 13, 182: 239, 183: 177,
    184: 240, 185: 174, 186: 76, 187: 18, 188: 145, 189: 207, 190: 45, 191: 115,
    192: 202, 193: 148, 194: 118, 195: 40, 196: 171, 197: 245, 198: 23, 199: 73,
    200: 8, 201: 86, 202: 180, 203: 234, 204: 105, 205: 55, 206: 213, 207: 139,
    208: 87, 209: 9, 210: 235, 211: 181, 212: 54, 213: 104, 214: 138, 215: 212,
    216: 149, 217: 203, 218: 41, 219: 119, 220: 244, 221: 170, 222: 72, 223: 22,
    224: 233, 225: 183, 226: 85, 227: 11, 228: 136, 229: 214, 230: 52, 231: 106,
    232: 43, 233: 117, 234: 151, 235: 201, 236: 74, 237: 20, 238: 246, 239: 168,
    240: 116, 241: 42, 242: 200, 243: 150, 244: 21, 245: 75, 246: 169, 247: 247,
    248: 182, 249: 232, 250: 10, 251: 84, 252: 215, 253: 137, 254: 107, 255: 53
}

def calculate_bolid_key(num):
    """Преобразует число в BolidKey по алгоритму из SQL"""
    
    # 1. Преобразуем число в HEX (аналог CAST(@num AS VARBINARY(8)))
    hex_bytes = num.to_bytes(8, byteorder='big', signed=False)
    hex_str = hex_bytes.hex().upper()
    
    # Убираем нули (аналог REPLACE(@hex, '00', ''))
    hex_clean = hex_str.replace('00', '')
    
    # 2. Если длина HEX больше 10 символов, разворачиваем и удаляем последний байт
    if len(hex_clean) > 10:
        # Разворачиваем байты в обратном порядке
        reversed_hex = ''
        i = len(hex_clean)
        while i > 0:
            reversed_hex += hex_clean[i-2:i]
            i -= 2
        
        # Удаляем последний байт (2 символа)
        final_hex = reversed_hex[:-2]
    else:
        final_hex = hex_clean
    
    # 3. Дополняем нулями и добавляем '01'
    hex3 = ('000000' + final_hex + '01')[-14:]
    
    # 4. Вычисляем CRC8
    c = 0
    for j in range(7):  # 0 до 6 включительно
        # Извлекаем байт (2 символа)
        hex_byte = hex3[12 - j*2:14 - j*2]
        temp = int(hex_byte, 16)
        
        # Вычисляем CRC8 по таблице
        c = CRC8_TABLE[c ^ temp]
    
    # 5. Формируем CRC8 в HEX
    crc8_hex = f"{c:02X}"
    
    # 6. Формируем итоговый ключ
    key_result = (crc8_hex + hex3 + '01')[:16]
    
    return key_result

def split_full_name(full_name):
    """Разделяет полное имя на фамилию, имя и отчество"""
    parts = full_name.strip().split()
    
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        return parts[0], parts[1], ""
    elif len(parts) == 1:
        return parts[0], "", ""
    else:
        return "", "", ""

def process_input_file(input_file, output_file):
    """
    Обрабатывает входной файл с данными формата:
    ;ФИО;...;число;...
    
    Создает выходной файл NamesToFind.csv с колонками:
    Name, FirstName, MidName, Original, BolidKey
    """
    
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            
            # Создаем CSV writer с разделителем точка с запятой
            writer = csv.writer(outfile, delimiter=';')
            
            # Записываем заголовок
            writer.writerow(["Name", "FirstName", "MidName", "Original", "BolidKey"])
            
            processed = 0
            errors = 0
            skipped = 0
            
            for line_num, line in enumerate(infile, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Разделяем строку по точке с запятой
                parts = line.split(';')
                
                # Проверяем, что строка содержит достаточно полей
                if len(parts) < 5:
                    print(f"Строка {line_num}: недостаточно полей, пропускаем")
                    skipped += 1
                    continue
                
                # Первая колонка (индекс 1) - ФИО
                full_name = parts[1]
                
                # Четвертая колонка (индекс 4) - число для обработки
                num_str = parts[4]
                
                try:
                    # Разделяем ФИО
                    last_name, first_name, mid_name = split_full_name(full_name)
                    
                    # Обрабатываем число
                    if num_str and num_str.strip():
                        num = int(num_str)
                        bolid_key = calculate_bolid_key(num)
                        
                        # Записываем результат
                        writer.writerow([
                            last_name,
                            first_name,
                            mid_name,
                            num_str,
                            bolid_key
                        ])
                        processed += 1
                    else:
                        print(f"Строка {line_num}: пустое число, пропускаем")
                        skipped += 1
                    
                except ValueError as e:
                    print(f"Строка {line_num}: ошибка преобразования числа '{num_str}' - {e}")
                    errors += 1
                except Exception as e:
                    print(f"Строка {line_num}: неожиданная ошибка - {e}")
                    errors += 1
            
            print(f"\nОбработка завершена!")
            print(f"Успешно обработано: {processed}")
            print(f"Пропущено (недостаточно данных): {skipped}")
            print(f"Ошибок: {errors}")
            print(f"Результат сохранен в: {output_file}")
            
    except FileNotFoundError:
        print(f"Файл {input_file} не найден!")
    except Exception as e:
        print(f"Ошибка при обработке файлов: {e}")

def test_with_sample_data():
    """Тестирование на примере данных"""
    print("Тестирование на примере данных:")
    print("-" * 60)
    
    # Тестовые данные
    test_line = ";Федюнин Владимир Константинович;4623 087529;2200********6002;33240993912937753;;03/33;40817810090159465404;643;stop"
    print(f"Исходная строка: {test_line}")
    print()
    
    parts = test_line.split(';')
    full_name = parts[1]
    num_str = parts[4]
    
    # Разделяем ФИО
    last_name, first_name, mid_name = split_full_name(full_name)
    print(f"ФИО: {full_name}")
    print(f"  Фамилия: {last_name}")
    print(f"  Имя: {first_name}")
    print(f"  Отчество: {mid_name}")
    print()
    
    # Обрабатываем число
    num = int(num_str)
    bolid_key = calculate_bolid_key(num)
    print(f"Число: {num_str}")
    print(f"BolidKey: {bolid_key}")
    
    return last_name, first_name, mid_name, num_str, bolid_key

if __name__ == "__main__":
    print("Запуск обработчика файлов")
    print("=" * 60)
    
    # Тестирование на примере
    print("ТЕСТОВЫЙ РЕЖИМ:")
    test_with_sample_data()
    
    print("\n" + "=" * 60)
    print("ОСНОВНАЯ ОБРАБОТКА:")
    
    # Основная обработка
    input_filename = "input.txt"  # Ваш входной файл
    output_filename = "NamesToFind.csv"
    
    print(f"Чтение из: {input_filename}")
    print(f"Запись в: {output_filename}")
    
    process_input_file(input_filename, output_filename)