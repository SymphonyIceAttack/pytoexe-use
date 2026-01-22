def remove_duplicates(input_file, output_file):
    # Используем множество для хранения уникальных строк  
    unique_lines = set()

    # Открываем входной файл для чтения  
    with open(input_file, 'r', encoding='utf-8') as infile:
        for line in infile:
            # Удаляем пробелы и добавляем строку в множество  
            unique_lines.add(line.strip())

    # Открываем выходной файл для записи  
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for line in unique_lines:
            # Записываем уникальные строки в выходной файл  
            outfile.write(line + '\n')

# Пример использования  
input_file = 'input.txt'  # ваш входной файл  
output_file = 'output.txt'  # файл для сохранения результата

remove_duplicates(input_file, output_file)


