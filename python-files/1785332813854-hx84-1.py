import os
import xml.etree.ElementTree as ET
import argparse
import logging
from pathlib import Path
from datetime import datetime

class FileDeleter:
    def __init__(self, xml_path, search_path=None, recursive=True, 
                 case_sensitive=False, backup=False, dry_run=False):
        """
        Инициализация класса для поиска и удаления файлов.
        
        Args:
            xml_path (str): Путь к XML-файлу со списком файлов для удаления
            search_path (str): Путь для поиска файлов (по умолчанию текущая директория)
            recursive (bool): Рекурсивный поиск в поддиректориях
            case_sensitive (bool): Учитывать регистр при поиске
            backup (bool): Создавать резервную копию перед удалением
            dry_run (bool): Тестовый режим без фактического удаления
        """
        self.xml_path = xml_path
        self.search_path = search_path or os.getcwd()
        self.recursive = recursive
        self.case_sensitive = case_sensitive
        self.backup = backup
        self.dry_run = dry_run
        
        # Настройка логирования
        self.setup_logging()
        
    def setup_logging(self):
        """Настройка системы логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('file_deleter.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def parse_xml(self):
        """
        Парсинг XML-файла для получения списка файлов.
        
        Returns:
            list: Список имен файлов для удаления
        """
        try:
            tree = ET.parse(self.xml_path)
            root = tree.getroot()
            
            files_to_delete = []
            
            # Пытаемся найти файлы в разных возможных структурах XML
            for elem in root.iter():
                if elem.tag.lower() in ['file', 'filename', 'name', 'delete']:
                    if elem.text and elem.text.strip():
                        files_to_delete.append(elem.text.strip())
            
            # Если не нашли в элементах, ищем в атрибутах
            if not files_to_delete:
                for elem in root.iter():
                    for attr_name in ['name', 'filename', 'file', 'path']:
                        if attr_name in elem.attrib:
                            files_to_delete.append(elem.attrib[attr_name])
            
            if not files_to_delete:
                self.logger.warning("В XML-файле не найдено имен файлов для удаления")
            
            return files_to_delete
            
        except ET.ParseError as e:
            self.logger.error(f"Ошибка парсинга XML-файла: {e}")
            raise
        except FileNotFoundError:
            self.logger.error(f"XML-файл не найден: {self.xml_path}")
            raise
    
    def find_files(self, filename):
        """
        Поиск файлов по имени.
        
        Args:
            filename (str): Имя файла для поиска
            
        Returns:
            list: Список найденных путей к файлам
        """
        found_files = []
        
        if self.recursive:
            walk_pattern = '**/*'
        else:
            walk_pattern = '*'
        
        search_path = Path(self.search_path)
        
        try:
            for file_path in search_path.glob(walk_pattern):
                if file_path.is_file():
                    # Сравнение имен файлов с учетом или без учета регистра
                    if self.case_sensitive:
                        match = file_path.name == filename
                    else:
                        match = file_path.name.lower() == filename.lower()
                    
                    if match:
                        found_files.append(file_path)
        
        except PermissionError as e:
            self.logger.error(f"Ошибка доступа при поиске: {e}")
        
        return found_files
    
    def backup_file(self, file_path):
        """
        Создание резервной копии файла.
        
        Args:
            file_path (Path): Путь к файлу
            
        Returns:
            bool: True если резервная копия создана успешно
        """
        try:
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_name
            
            with open(file_path, 'rb') as source:
                with open(backup_path, 'wb') as target:
                    target.write(source.read())
            
            self.logger.info(f"Создана резервная копия: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка создания резервной копии {file_path}: {e}")
            return False
    
    def delete_file(self, file_path):
        """
        Удаление файла.
        
        Args:
            file_path (Path): Путь к файлу для удаления
            
        Returns:
            bool: True если файл успешно удален
        """
        try:
            if self.backup:
                self.backup_file(file_path)
            
            if not self.dry_run:
                os.remove(file_path)
                self.logger.info(f"Файл удален: {file_path}")
            else:
                self.logger.info(f"[DRY RUN] Был бы удален: {file_path}")
            
            return True
            
        except PermissionError:
            self.logger.error(f"Нет прав на удаление файла: {file_path}")
            return False
        except Exception as e:
            self.logger.error(f"Ошибка удаления файла {file_path}: {e}")
            return False
    
    def process(self):
        """
        Основной метод обработки - поиск и удаление файлов.
        """
        self.logger.info("=" * 60)
        self.logger.info("Запуск программы поиска и удаления файлов")
        self.logger.info(f"XML-файл: {self.xml_path}")
        self.logger.info(f"Путь поиска: {self.search_path}")
        self.logger.info(f"Рекурсивный поиск: {self.recursive}")
        self.logger.info(f"Учет регистра: {self.case_sensitive}")
        self.logger.info(f"Резервное копирование: {self.backup}")
        self.logger.info(f"Тестовый режим: {self.dry_run}")
        self.logger.info("=" * 60)
        
        # Получаем список файлов из XML
        files_to_delete = self.parse_xml()
        
        if not files_to_delete:
            self.logger.warning("Список файлов для удаления пуст")
            return
        
        self.logger.info(f"Найдено {len(files_to_delete)} файлов в XML для поиска")
        
        total_found = 0
        total_deleted = 0
        
        # Поиск и удаление каждого файла
        for filename in files_to_delete:
            self.logger.info(f"Поиск файла: {filename}")
            found_files = self.find_files(filename)
            
            if not found_files:
                self.logger.warning(f"Файл не найден: {filename}")
                continue
            
            self.logger.info(f"Найдено совпадений: {len(found_files)}")
            total_found += len(found_files)
            
            for file_path in found_files:
                if self.delete_file(file_path):
                    total_deleted += 1
        
        # Вывод статистики
        self.logger.info("=" * 60)
        self.logger.info("РЕЗУЛЬТАТЫ ВЫПОЛНЕНИЯ:")
        self.logger.info(f"Всего найдено файлов: {total_found}")
        self.logger.info(f"Успешно удалено: {total_deleted}")
        self.logger.info(f"Ошибок удаления: {total_found - total_deleted}")
        self.logger.info("=" * 60)


def create_sample_xml():
    """Создание примера XML-файла"""
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<files_to_delete>
    <description>Список файлов для удаления</description>
    <file>test1.txt</file>
    <file>temp_data.csv</file>
    <file>old_report.pdf</file>
    <file>backup_2023.log</file>
    <filename>Документ.docx</filename>
</files_to_delete>
"""
    
    with open('file.xml', 'w', encoding='utf-8') as f:
        f.write(sample_xml)
    
    print("Создан пример XML-файла: file.xml")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='Программа для поиска и удаления файлов по списку из XML',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Поиск файлов из file.xml в текущей директории
  python file_deleter.py file.xml
  
  # Поиск в указанной директории рекурсивно
  python file_deleter.py file.xml -p /home/user/documents -r
  
  # Тестовый запуск без удаления
  python file_deleter.py file.xml --dry-run
  
  # С учетом регистра и созданием резервных копий
  python file_deleter.py file.xml -c -b
  
  # Создать пример XML-файла
  python file_deleter.py --create-sample
        """
    )
    
    parser.add_argument(
        'xml_file',
        nargs='?',
        help='Путь к XML-файлу со списком файлов для удаления'
    )
    
    parser.add_argument(
        '-p', '--path',
        default=os.getcwd(),
        help='Путь для поиска файлов (по умолчанию: текущая директория)'
    )
    
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        default=True,
        help='Рекурсивный поиск в поддиректориях (по умолчанию: включен)'
    )
    
    parser.add_argument(
        '--no-recursive',
        action='store_false',
        dest='recursive',
        help='Отключить рекурсивный поиск'
    )
    
    parser.add_argument(
        '-c', '--case-sensitive',
        action='store_true',
        default=False,
        help='Учитывать регистр при поиске файлов'
    )
    
    parser.add_argument(
        '-b', '--backup',
        action='store_true',
        default=False,
        help='Создавать резервную копию перед удалением'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=False,
        help='Тестовый режим (без фактического удаления файлов)'
    )
    
    parser.add_argument(
        '--create-sample',
        action='store_true',
        help='Создать пример XML-файла (file.xml)'
    )
    
    args = parser.parse_args()
    
    # Создание примера XML
    if args.create_sample:
        create_sample_xml()
        return
    
    # Проверка наличия XML-файла
    if not args.xml_file:
        parser.error("Необходимо указать XML-файл или использовать --create-sample")
    
    # Создание и запуск обработчика
    try:
        deleter = FileDeleter(
            xml_path=args.xml_file,
            search_path=args.path,
            recursive=args.recursive,
            case_sensitive=args.case_sensitive,
            backup=args.backup,
            dry_run=args.dry_run
        )
        
        deleter.process()
        
    except KeyboardInterrupt:
        print("\nПрограмма прервана пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())