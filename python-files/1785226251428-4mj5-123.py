import os
import re
import openpyxl
from xml.etree.ElementTree import Element, SubElement, ElementTree

def parse_coordinates(text):
    """Парсит координаты из разных форматов в десятичные градусы"""
    text = str(text).strip()
    if not text or text == 'None':
        return None, None

    # 1. Попытка распарсить формат ГМС (Градусы, Минуты, Секунды)
    # Пример: 44°56'15.24"с.ш., 33°47'23.79
    dms_pattern = r"(\d+)[°]\s*(\d+)[']\s*([\d.]+)[\"]?\s*(?:с\.?\s*ш\.?)?\s*,?\s*(\d+)[°]\s*(\d+)[']\s*([\d.]+)[\"]?"
    match = re.search(dms_pattern, text, re.IGNORECASE)
    if match:
        lat = int(match.group(1)) + int(match.group(2))/60 + float(match.group(3))/3600
        lon = int(match.group(4)) + int(match.group(5))/60 + float(match.group(6))/3600
        return lat, lon

    # 2. Попытка распарсить десятичный формат
    # Пример: 44,844833° с.ш. 33,661876 или 44.99246, 34.090588
    clean_text = text.lower().replace('с.ш.', '').replace('с. ш.', '').replace('°', ' ').replace(',', '.')
    parts = re.split(r'\s+', clean_text.strip())
    
    nums = []
    for p in parts:
        try:
            nums.append(float(p))
        except ValueError:
            pass
            
    if len(nums) >= 2:
        return nums[0], nums[1]

    return None, None

def main():
    print("="*40)
    print(" Конвертер XLSX -> KML")
    print("="*40)
    
    # Ищем все xlsx файлы в текущей директории
    current_dir = os.path.dirname(os.path.abspath(__file__))
    xlsx_files = [f for f in os.listdir(current_dir) if f.endswith('.xlsx')]
    
    if not xlsx_files:
        print("\n[Ошибка] В папке со скриптом не найдено файлов .xlsx!")
        input("Нажмите Enter для выхода...")
        return

    # Выводим меню
    print("\nДоступные файлы:")
    for i, file in enumerate(xlsx_files):
        print(f"  {i + 1}. {file}")
    
    while True:
        try:
            choice = int(input(f"\nВыберите номер файла (1-{len(xlsx_files)}): ")) - 1
            if 0 <= choice < len(xlsx_files):
                break
            print("Неверный номер, попробуйте снова.")
        except ValueError:
            print("Введите число!")

    selected_file = os.path.join(current_dir, xlsx_files[choice])
    print(f"\n[INFO] Чтение файла: {xlsx_files[choice]}...")

    # Читаем Excel
    wb = openpyxl.load_workbook(selected_file, read_only=True)
    ws = wb.active

    # Создаем структуру KML
    kml = Element('kml', xmlns="http://www.opengis.net/kml/2.2")
    document = SubElement(kml, 'Document')
    doc_name = SubElement(document, 'name')
    doc_name.text = "Exported Points"

    processed_count = 0
    error_count = 0

    # Пропускаем первую строку (заголовок), начинаем со 2-й
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or len(row) < 2:
            continue
            
        point_name = str(row[0]).strip()
        coord_str = str(row[1]).strip()
        
        lat, lon = parse_coordinates(coord_str)
        
        if lat is not None and lon is not None:
            placemark = SubElement(document, 'Placemark')
            pm_name = SubElement(placemark, 'name')
            pm_name.text = point_name
            
            point = SubElement(placemark, 'Point')
            coords = SubElement(point, 'coordinates')
            # В KML формат координат: Долгота, Широта, Высота
            coords.text = f"{lon},{lat},0"
            processed_count += 1
        else:
            print(f"  [!] Не удалось распарсить координаты для точки '{point_name}': {coord_str}")
            error_count += 1

    wb.close()

    # Сохраняем KML
    output_file = os.path.join(current_dir, "output_points.kml")
    tree = ElementTree(kml)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)

    print(f"\n[УСПЕХ] Обработано точек: {processed_count}")
    if error_count > 0:
        print(f"[ВНИМАНИЕ] Пропущено точек с ошибками: {error_count}")
    print(f"[INFO] Файл сохранен: {output_file}")
    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()