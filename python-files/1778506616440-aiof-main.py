import os

def extract_segments_with_remainder(input_filepath, signature_str):
    """
    Анализирует большой файл, находит повторяющиеся вхождения сигнатуры.
    Каждый сегмент, включающий начальную сигнатуру и байты до следующей сигнатуры (исключая ее),
    сохраняется в отдельный файл. Если после последней найденной сигнатуры остаются данные,
    они также сохраняются в отдельный файл. Имена выходных файлов формируются с 6-значным
    порядковым номером с ведущими нулями. Файлы сохраняются в ту же директорию, что и исходный.

    Args:
        input_filepath (str): Путь к исходному файлу.
        signature_str (str): Сигнатура в символьном виде.
    """
    signature = signature_str.encode('utf-8')
    input_dir = os.path.dirname(input_filepath)
    if not input_dir:
        input_dir = '.'

    try:
        with open(input_filepath, 'rb') as infile:
            file_content = infile.read()

        current_pos = 0
        segment_count = 0
        last_signature_end = -1

        while True:
            start_index = file_content.find(signature, current_pos)
            if start_index == -1:
                break  # Сигнатура больше не найдена

            # Ищем следующую сигнатуру, начиная после начала текущей
            end_index = file_content.find(signature, start_index + len(signature))

            if end_index == -1:
                # Если конечной сигнатуры не найдено, записываем остаток файла
                # от начала текущей сигнатуры до конца файла
                remainder = file_content[start_index:]
                segment_count += 1
                output_filename_number = f"{segment_count:06d}"
                output_filepath = os.path.join(input_dir, f"{output_filename_number}_remainder.bin")
                with open(output_filepath, 'wb') as outfile:
                    outfile.write(remainder)
                print(f"Остаток после последней сигнатуры сохранен в: {output_filepath}")
                last_signature_end = len(file_content) # Отмечаем, что файл обработан до конца
                break
            else:
                # Извлекаем сегмент между началом первой сигнатуры и началом второй
                segment_data = file_content[start_index:end_index]
                segment_count += 1
                output_filename_number = f"{segment_count:06d}"
                output_filepath = os.path.join(input_dir, f"{output_filename_number}.bin")
                with open(output_filepath, 'wb') as outfile:
                    outfile.write(segment_data)
                print(f"Сегмент №{segment_count} сохранен в: {output_filepath}")
                last_signature_end = end_index # Обновляем позицию конца последней найденной сигнатуры
                current_pos = end_index # Продолжаем поиск с конца текущей конечной сигнатуры

        # Если после цикла last_signature_end указывает на конец файла (была найдена последняя сигнатура, но не было остатка)
        # или если файл был полностью пройден, но остаток не был записан (например, если последняя сигнатура оказалась в самом конце файла)
        # Этот блок становится не нужен, так как обработка остатка происходит внутри цикла.

    except FileNotFoundError:
        print(f"Ошибка: Исходный файл не найден по пути {input_filepath}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

# Пример использования:
# input_file_path = 'your_large_file.bin' # Укажите путь к вашему файлу
# signature_to_find = 'MARKER'           # Укажите вашу сигнатуру
# extract_segments_with_remainder(input_file_path, signature_to_find)