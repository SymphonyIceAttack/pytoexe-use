import re
import sys

def process_gcode(input_file, output_file):
    # Регулярные выражения для поиска блоков
    block_pattern = re.compile(r'^\(\d+_OTVOD_TEST\d*\)$', re.MULTILINE)
    
    # Строки для удаления
    remove_lines = [
        r'^G91G28Z0',
        r'^G91 G28 Z0\.0',
        r'^G28 Y0\.0 \(end of path\)',
        r'^G91 G28 X0\.0 Y0\.0'
    ]
    
    # Флаг нахождения в нужном блоке
    in_block = False
    
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            # Проверка начала блока
            if block_pattern.match(line.strip()):
                in_block = True
                f_out.write(line)
                continue
                
            # Проверка конца блока (пустая строка или новый заголовок)
            if in_block and (line.strip() == '' or line.startswith('%') or line.startswith('O')):
                in_block = False
                
            # Обработка строк внутри блока
            if in_block:
                # Проверка на удаление
                if not any(re.match(pattern, line.strip()) for pattern in remove_lines):
                    # Проверка на добавление M521
                    if 'G90 G40 G49 G54 G17' in line:
                        f_out.write(line)
                        f_out.write('M521 P1 L5\n')
                        continue
                    
                f_out.write(line)
            else:
                f_out.write(line)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Использование: python script.py входной_файл выходной_файл")
        sys.exit(1)
        
    process_gcode(sys.argv[1], sys.argv[2])
