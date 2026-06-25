import sys
from pathlib import Path

def extract_powder_data_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except FileNotFoundError:
        print("Ошибка: файл не найден")
        return
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return

    start_marker = "loop_\n _pd_proc_point_id\n _pd_proc_2theta_corrected\n _pd_proc_d_spacing\n _pd_proc_intensity_net\n _pd_calc_intensity_net\n _pd_proc_ls_weight"
    start_index = content.find(start_marker)
    if start_index == -1:
        print("Ошибка: Не найден блок с данными")
        return

    next_loop_index = content.find("loop_", start_index + len(start_marker))
    end_index = len(content) if next_loop_index == -1 else next_loop_index

    data_block = content[start_index + len(start_marker):end_index].strip()
    lines = data_block.split('\n')

    extracted_data = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line:
            parts = stripped_line.split()
            if len(parts) == 6:
                extracted_data.append(f"{parts[1]}\t{parts[3]}\t{parts[4]}")

    if not extracted_data:
        print("Ошибка: Не удалось извлечь данные")
        return

    # Определяем расширение выходного файла
    if file_path.endswith('.cif'):
        output_file_path = file_path.replace('.cif', '_extracted.txt')
    elif file_path.endswith('.txt'):
        output_file_path = file_path.replace('.txt', '_extracted.txt')
    else:
        output_file_path = file_path + '_extracted.txt'

    try:
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write("2theta\tproc_intensity\tcalc_intensity\n")
            output_file.write("\n".join(extracted_data))
        print(f"Данные сохранены в файл: {output_file_path}")
    except Exception as e:
        print(f"Ошибка при сохранении: {e}")

def get_file_path():
    while True:
        print("\nИнструкция:")
        print("  Введите полный путь к файлу .cif или .txt")
        print("  Или перетащите файл в окно консоли")
        print("  Для выхода введите 'exit' или 'q'")
        print("-" * 50)
        
        file_path = input("Путь: ").strip().strip('"').strip("'")
        
        if file_path.lower() in ['exit', 'q', 'выход']:
            sys.exit(0)
        
        if not file_path:
            print("Путь не может быть пустым")
            continue
        
        path = Path(file_path)
        
        if not path.exists():
            print("Файл не найден")
            continue
        
        if not path.is_file():
            print("Это не файл")
            continue
        
        # Разрешаем .cif и .txt файлы
        if not (file_path.lower().endswith('.cif') or file_path.lower().endswith('.txt')):
            print("Поддерживаются только файлы .cif и .txt")
            continue
        
        try:
            with open(path, 'rb') as test_file:
                pass
        except:
            print("Нет доступа к файлу")
            continue
        
        return str(path)

if __name__ == "__main__":
    file_path = get_file_path()
    extract_powder_data_from_file(file_path)
    input("\nНажмите Enter для выхода...")