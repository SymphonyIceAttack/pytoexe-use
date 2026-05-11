import os

def extract_sequences(input_filepath, signature):
    """
    Анализирует большой файл, находит заданную сигнатуру, запоминает её начало,
    находит следующую заданную сигнатуру и сохраняет всю последовательность байт
    между найденными сигнатурами в новый файл.
    После каждой записи буфера в файл выводится название файла.

    Args:
        input_filepath (str): Путь к исходному файлу.
        signature (str): Заданная сигнатура (например, "RIFF").
    """
    signature_bytes = signature.encode('ascii')
    output_dir = os.path.dirname(input_filepath)
    file_counter = 0
    part_to_save = b'' # Накапливаем данные для текущего файла

    with open(input_filepath, 'rb') as infile:
        buffer = b''
        chunk_size = 4096 # Размер чанка для чтения файла

        while True:
            chunk = infile.read(chunk_size)
            if not chunk:
                # Обработка конца файла: если есть накопленные данные, сохраняем их
                if part_to_save:
                    file_counter += 1
                    output_filename = f"{file_counter:06d}.bin"
                    output_filepath = os.path.join(output_dir, output_filename)
                    with open(output_filepath, 'wb') as outfile:
                        outfile.write(part_to_save)
                    print(f"Сохранен файл: {output_filename}")
                break

            buffer += chunk

            start_index = -1
            current_pos = 0

            while current_pos < len(buffer):
                found_index = buffer.find(signature_bytes, current_pos)

                if found_index == -1:
                    # Сигнатура не найдена дальше в буфере.
                    # Если что-то накапливаем (part_to_save), добавляем все, что осталось в буфере,
                    # кроме возможного начала следующей сигнатуры.
                    if part_to_save:
                        part_to_save += buffer[current_pos:]
                    # Сдвигаем буфер, сохраняя конец для следующей итерации
                    # +1 чтобы не потерять возможное совпадение при следующем чтении
                    buffer = buffer[max(0, len(buffer) - (len(signature_bytes) - 1)):]
                    break

                if not part_to_save:
                    # Нашли первую сигнатуру. Начинаем накапливать данные
                    part_to_save = signature_bytes # Первая сигнатура входит в файл
                    current_pos = found_index + len(signature_bytes)
                    # Перемещаем эту часть из буфера
                    buffer = buffer[current_pos:]
                    current_pos = 0 # Сбрасываем позицию для следующего поиска
                else:
                    # Нашли вторую сигнатуру. Сохраняем накопленные данные
                    part_to_save += buffer[:found_index] # Добавляем данные между сигнатурами
                    file_counter += 1
                    output_filename = f"{file_counter:06d}.bin"
                    output_filepath = os.path.join(output_dir, output_filename)
                    with open(output_filepath, 'wb') as outfile:
                        outfile.write(part_to_save)
                    print(f"Сохранен файл: {output_filename}")

                    # Сбрасываем накопленные данные и начинаем новые
                    part_to_save = signature_bytes # Новая первая сигнатура
                    current_pos = found_index + len(signature_bytes)
                    buffer = buffer[current_pos:]
                    current_pos = 0



# Пример использования:
# Создайте dummy.riff файл для тестирования, если необходимо
# import binascii
# with open("dummy.riff", "wb") as f:
#      byte_string = b'\x00' * 100 + b'RIFF' + b'data1' + b'RIFF' + b'data2' + b'RIFF' + b'data3' + b'\x00' * 50
#      f.write(byte_string)

# extract_sequences("dummy.riff", "RIFF")