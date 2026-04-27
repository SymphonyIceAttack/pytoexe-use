# convert_1c_xml_to_csv.py
import os
import sys
import xml.etree.ElementTree as ET
import csv
import re
from pathlib import Path
from datetime import datetime

def get_text(element, xpath):
    """Безопасное получение текста из элемента"""
    if element is None:
        return ''
    found = element.find(xpath)
    return found.text.strip() if found is not None and found.text else ''

def parse_1c_file(xml_file_path, output_folder):
    """Конвертирует один XML файл в CSV"""
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        # Пробуем найти Body (с учетом namespace)
        body = root.find('.//{http://v8.1c.ru/edi/edi_stnd/EnterpriseData/1.17}Body')
        if body is None:
            body = root.find('.//Body')
        
        if body is None:
            return False, "Не найден Body в XML"
        
        docs = []
        items = []
        
        for doc in body.findall('.//Документ.ПоступлениеТоваровУслуг'):
            # Данные документа
            doc_data = {
                'Дата': get_text(doc, './/КлючевыеСвойства/Дата'),
                'НомерВходящего': get_text(doc, './/КлючевыеСвойства/ДанныеВходящегоДокумента/НомерВходящегоДокумента'),
                'ДатаВходящего': get_text(doc, './/КлючевыеСвойства/ДанныеВходящегоДокумента/ДатаВходящегоДокумента'),
                'Организация': get_text(doc, './/КлючевыеСвойства/Организация/Наименование'),
                'Контрагент': get_text(doc, './/КлючевыеСвойства/Контрагент/Наименование'),
                'ИНН': get_text(doc, './/КлючевыеСвойства/Контрагент/ИНН'),
                'КПП': get_text(doc, './/КлючевыеСвойства/Контрагент/КПП'),
                'СуммаДокумента': get_text(doc, './/Сумма'),
                'ВидОперации': get_text(doc, './/ВидОперации'),
                'Подразделение': get_text(doc, './/Подразделение/Наименование'),
                'Склад': get_text(doc, './/Склад/Наименование'),
                'Валюта': get_text(doc, './/Валюта/ДанныеКлассификатора/Код'),
            }
            docs.append(doc_data)
            
            # Товары
            товары = doc.find('.//Товары')
            if товары is not None:
                for item in товары.findall('.//Строка'):
                    item_data = {
                        'ДатаДокумента': doc_data['Дата'],
                        'Контрагент': doc_data['Контрагент'],
                        'НомерВходящего': doc_data['НомерВходящего'],
                        'Товар': get_text(item, './/ДанныеНоменклатуры/Номенклатура/Наименование'),
                        'КодТовара': get_text(item, './/ДанныеНоменклатуры/Номенклатура/Ссылка'),
                        'Количество': get_text(item, './/Количество'),
                        'Цена': get_text(item, './/Цена'),
                        'Сумма': get_text(item, './/Сумма'),
                        'СтавкаНДС': get_text(item, './/СтавкаНДС/Ставка'),
                        'СуммаНДС': get_text(item, './/СуммаНДС'),
                        'ЕдИзм': get_text(item, './/ЕдиницаИзмерения/ДанныеКлассификатора/Код'),
                    }
                    items.append(item_data)
        
        # Создаем имя выходного файла
        base_name = Path(xml_file_path).stem
        docs_file = output_folder / f"{base_name}_документы.csv"
        items_file = output_folder / f"{base_name}_товары.csv"
        
        # Сохраняем CSV
        if docs:
            with open(docs_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=docs[0].keys())
                writer.writeheader()
                writer.writerows(docs)
        
        if items:
            with open(items_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=items[0].keys())
                writer.writeheader()
                writer.writerows(items)
        
        return True, f"Создано {len(docs)} документов и {len(items)} товаров"
    
    except Exception as e:
        return False, str(e)

def main():
    """Основная функция - обрабатывает все XML файлы в папке"""
    
    # Определяем папки
    script_dir = Path(sys.argv[0] if getattr(sys, 'frozen', False) else __file__).parent
    input_folder = script_dir / "XML_входящие"
    output_folder = script_dir / "CSV_результаты"
    archive_folder = script_dir / "XML_архив"
    
    # Создаем папки если их нет
    input_folder.mkdir(exist_ok=True)
    output_folder.mkdir(exist_ok=True)
    archive_folder.mkdir(exist_ok=True)
    
    # Логирование
    log_file = output_folder / f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    # Ищем XML файлы
    xml_files = list(input_folder.glob("*.xml"))
    
    if not xml_files:
        with open(log_file, 'w', encoding='utf-8') as log:
            log.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log.write("Нет XML файлов для обработки\n")
            log.write(f"Поместите XML файлы в папку: {input_folder}\n")
        
        # Показываем сообщение
        print("=" * 60)
        print("НЕТ XML ФАЙЛОВ ДЛЯ ОБРАБОТКИ")
        print("=" * 60)
        print(f"Поместите XML файлы в папку:")
        print(f"{input_folder}")
        print("\nНажмите Enter для выхода...")
        input()
        return
    
    # Обрабатываем файлы
    results = []
    for xml_file in xml_files:
        print(f"Обработка: {xml_file.name}")
        success, message = parse_1c_file(xml_file, output_folder)
        
        if success:
            results.append(f"✅ {xml_file.name} - {message}")
            # Перемещаем в архив
            archive_path = archive_folder / xml_file.name
            xml_file.rename(archive_path)
        else:
            results.append(f"❌ {xml_file.name} - Ошибка: {message}")
    
    # Пишем лог
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write(f"Дата обработки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write("=" * 60 + "\n")
        for result in results:
            log.write(result + "\n")
        log.write("\n" + "=" * 60 + "\n")
        log.write(f"Обработано файлов: {len(xml_files)}\n")
        log.write(f"Результаты сохранены в: {output_folder}\n")
        log.write(f"Архив XML в: {archive_folder}\n")
    
    # Показываем результат
    print("\n" + "=" * 60)
    print("ОБРАБОТКА ЗАВЕРШЕНА")
    print("=" * 60)
    for result in results:
        print(result)
    print("\n" + "=" * 60)
    print(f"CSV файлы сохранены в: {output_folder}")
    print(f"Лог операций: {log_file}")
    print(f"Обработанные XML перемещены в: {archive_folder}")
    print("\nНажмите Enter для выхода...")
    input()

if __name__ == "__main__":
    main()