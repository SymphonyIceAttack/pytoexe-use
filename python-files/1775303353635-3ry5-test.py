import xml.etree.ElementTree as ET
import argparse
import sys

# 📚 СЛОВАРЬ УНИКАЛЬНЫХ NV-ЭЛЕМЕНТОВ
# Это главная база знаний скрипта. Вы можете легко добавлять сюда новые параметры.
# Формат: 'Название_параметра': ('NV_ID_в_шестнадцатеричном_виде', 'длина_в_байтах')
NV_ITEMS = {
    # Идентификаторы устройств
    'imei1':       ('0x226', 8),  # IMEI для первой SIM-карты
    'imei2':       ('0x227', 8),  # IMEI для второй SIM-карты
    'meid':        ('0x797', 8),  # MEID для CDMA-сетей
    'esn':         ('0x00',  4),  # ESN, устаревший идентификатор
    'serial_num':  ('0x2E0', 16), # Серийный номер (зависит от вендора)
    
    # Сетевые адреса
    'wlan_mac':    ('0x222', 6),  # MAC-адрес Wi-Fi
    'bt_mac':      ('0x223', 6),  # MAC-адрес Bluetooth
    
    # Ключи и настройки безопасности (примеры, ID могут отличаться)
    'sec_key_1':   ('0x1234', 32),# Гипотетический ключ безопасности 1
    'sec_key_2':   ('0x5678', 16),# Гипотетический ключ безопасности 2
    # --- ДОБАВЛЯЙТЕ НОВЫЕ ПАРАМЕТРЫ ЗДЕСЬ ---
    # 'custom_param': ('0xABCD', 8),
}

def edit_xqcn(input_path, output_path, edits_to_make):
    """Редактирует указанные NV-элементы в .xqcn файле."""
    try:
        tree = ET.parse(input_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"❌ Ошибка: Не удалось распарсить {input_path}. Убедитесь, что это .xqcn файл. ({e})")
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ Ошибка: Файл '{input_path}' не найден.")
        sys.exit(1)

    changes_made = False
    # Ищем все элементы 'Stream'
    for stream in root.findall('.//Stream'):
        name_hex = stream.get('Name')
        if not name_hex:
            continue

        # Проверяем, есть ли такой ID в нашем словаре для редактирования
        for param_name, (nv_id_hex, length) in edits_to_make.items():
            if name_hex.lower() == nv_id_hex.lower()[2:]: # Сравниваем без префикса '0x'
                old_value = stream.get('Value', '').strip()
                new_value = input(f"  Введите новое значение для {param_name} (HEX, пары через пробел): ").strip()
                if old_value != new_value:
                    stream.set('Value', new_value)
                    print(f"    ✅ Изменен {param_name} (ID {nv_id_hex}): '{old_value}' -> '{new_value}'")
                    changes_made = True
                else:
                    print(f"    ℹ️ Пропущен {param_name}: новое значение совпадает со старым.")
                break # Параметр найден и обработан, выходим из внутреннего цикла

    if changes_made:
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        print(f"\n💾 Измененный файл сохранен как: {output_path}")
    else:
        print("\n⚠️ Ни один из указанных NV-элементов не был найден или изменен в файле.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Универсальный редактор уникальных NV-данных в .xqcn файле.')
    parser.add_argument('input_file', help='Путь к исходному .xqcn файлу')
    parser.add_argument('output_file', nargs='?', help='Путь для сохранения измененного файла')
    args = parser.parse_args()

    output_file = args.output_file if args.output_file else args.input_file.replace('.xqcn', '_modified.xqcn')

    print("📁 УНИВЕРСАЛЬНЫЙ РЕДАКТОР .XQCN")
    print("="*40)
    print("Доступные для редактирования параметры:")
    for i, param in enumerate(NV_ITEMS.keys(), 1):
        print(f"  {i}. {param}")
    print("="*40)

    # Запрашиваем у пользователя, какие параметры он хочет изменить
    params_to_edit = {}
    while True:
        choice = input("Введите название параметра для редактирования (или 'done' для завершения): ").strip().lower()
        if choice == 'done':
            break
        if choice not in NV_ITEMS:
            print(f"❌ Неизвестный параметр: '{choice}'. Доступные: {', '.join(NV_ITEMS.keys())}")
            continue
        params_to_edit[choice] = NV_ITEMS[choice]
        print(f"➕ Добавлен параметр: {choice} (ID {NV_ITEMS[choice][0]})")

    if not params_to_edit:
        print("❌ Не задано ни одного изменения. Выход.")
        sys.exit(0)

    edit_xqcn(args.input_file, output_file, params_to_edit)