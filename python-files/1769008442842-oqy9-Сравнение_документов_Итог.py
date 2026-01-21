#!/usr/bin/env python3
"""
Приложение для сравнения документов закупок
Автоматически находит и сравнивает Word (XML) и HTML файлы в указанной папке
"""

import os
import sys
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

# Для GUI
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("Внимание: Tkinter не установлен. Запускается консольная версия.")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('procurement_comparator.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PhoneNormalizer:
    """Класс для нормализации и сравнения телефонных номеров"""
    
    @staticmethod
    def normalize(phone: str) -> str:
        """Нормализует телефонный номер к формату 7XXXXXXXXXX"""
        if not phone:
            return ""
        
        # Оставляем только цифры
        digits = re.sub(r'[^\d]', '', phone)
        
        # Убираем ведущий + если он был
        if phone.startswith('+'):
            pass  # уже убрали в digits
        
        # Приводим к единому формату
        if len(digits) == 11:
            if digits.startswith('8'):
                digits = '7' + digits[1:]
            elif digits.startswith('7'):
                pass
            else:
                digits = '7' + digits[1:]
        elif len(digits) == 10:
            digits = '7' + digits
        
        return digits
    
    @staticmethod
    def are_equal(phone1: str, phone2: str) -> bool:
        """Сравнивает два телефонных номера после нормализации"""
        return PhoneNormalizer.normalize(phone1) == PhoneNormalizer.normalize(phone2)


class ProcurementFileComparator:
    """Основной класс для сравнения файлов закупок"""
    
    # Ключевые слова для идентификации файлов
    WORD_KEYWORDS = ['<?xml', 'word/document.xml', 'w:document', 'mso-application']
    HTML_KEYWORDS = ['<!DOCTYPE html', '<html', 'html>']
    REQUIRED_FIELDS = ['purchase_id', 'kpp', 'email', 'phone']
    
    def __init__(self):
        self.folder_path = None
        self.word_file = None
        self.html_file = None
        self.word_data = {}
        self.html_data = {}
        self.differences = []
        self.results = {}
    
    def set_folder(self, folder_path: str) -> bool:
        """Установка папки для поиска файлов"""
        folder_path = Path(folder_path)
        if not folder_path.exists():
            logger.error(f"Папка не существует: {folder_path}")
            return False
        
        if not folder_path.is_dir():
            logger.error(f"Указанный путь не является папкой: {folder_path}")
            return False
        
        self.folder_path = folder_path
        logger.info(f"Установлена папка: {folder_path}")
        return True
    
    def find_files(self) -> Tuple[bool, str]:
        """Поиск Word и HTML файлов в папке"""
        if not self.folder_path:
            return False, "Папка не указана"
        
        word_files = []
        html_files = []
        
        # Рекурсивный поиск файлов
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                file_path = Path(root) / file
                
                # Проверка на Word файл (XML)
                if self._is_word_file(file_path):
                    word_files.append(file_path)
                
                # Проверка на HTML файл
                elif self._is_html_file(file_path):
                    html_files.append(file_path)
        
        # Выбор наиболее подходящих файлов
        self.word_file = self._select_best_file(word_files, 'Word')
        self.html_file = self._select_best_file(html_files, 'HTML')
        
        if not self.word_file:
            return False, "Не найден Word файл (XML формат)"
        
        if not self.html_file:
            return False, "Не найден HTML файл"
        
        logger.info(f"Найден Word файл: {self.word_file}")
        logger.info(f"Найден HTML файл: {self.html_file}")
        
        return True, "Файлы найдены"
    
    def _is_word_file(self, file_path: Path) -> bool:
        """Проверка, является ли файл Word XML файлом"""
        try:
            ext = file_path.suffix.lower()
            if ext in ['.doc', '.docx', '.xml']:
                # Проверяем содержимое
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(5000)  # Читаем начало файла
                
                # Ищем характерные признаки Word XML
                for keyword in self.WORD_KEYWORDS:
                    if keyword.lower() in content.lower():
                        return True
                
                # Проверяем на бинарный Word файл
                if ext == '.doc':
                    # Проверяем наличие маркеров Word
                    with open(file_path, 'rb') as f:
                        header = f.read(8)
                        # OLE2 файл (бинарный .doc)
                        if header.startswith(b'\xd0\xcf\x11\xe0'):
                            return False  # Пока не поддерживаем бинарные .doc
                        # XML-based (может быть .doc с XML)
                        return b'<?xml' in header or b'<w:' in header
            
            return False
            
        except Exception as e:
            logger.debug(f"Ошибка при проверке файла {file_path}: {e}")
            return False
    
    def _is_html_file(self, file_path: Path) -> bool:
        """Проверка, является ли файл HTML"""
        try:
            ext = file_path.suffix.lower()
            if ext in ['.html', '.htm']:
                return True
            
            if ext in ['.xml', '.txt']:
                # Проверяем содержимое
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(1000)
                
                for keyword in self.HTML_KEYWORDS:
                    if keyword.lower() in content.lower():
                        return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Ошибка при проверке HTML файла {file_path}: {e}")
            return False
    
    def _select_best_file(self, files: List[Path], file_type: str) -> Optional[Path]:
        """Выбор наиболее подходящего файла из списка"""
        if not files:
            return None
        
        if len(files) == 1:
            return files[0]
        
        # Приоритет по размеру (больший файл обычно содержит больше данных)
        files_sorted = sorted(files, key=lambda f: f.stat().st_size, reverse=True)
        
        # Для Word файлов - ищем с ключевыми словами
        if file_type == 'Word':
            for f in files_sorted:
                try:
                    with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                        if 'бенефициар' in content.lower() or 'гарант' in content.lower():
                            return f
                except:
                    continue
        
        # Для HTML файлов - ищем с информацией о контракте
        elif file_type == 'HTML':
            for f in files_sorted:
                try:
                    with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                        if 'контракт' in content.lower() or 'заказчик' in content.lower():
                            return f
                except:
                    continue
        
        # Возвращаем самый большой файл
        return files_sorted[0] if files_sorted else None
    
    def extract_data(self) -> bool:
        """Извлечение данных из обоих файлов"""
        if not self.word_file or not self.html_file:
            logger.error("Не все файлы найдены для извлечения данных")
            return False
        
        try:
            # Извлечение данных из Word файла
            self.word_data = self._extract_from_word(self.word_file)
            logger.info("Данные из Word файла извлечены")
            
            # Извлечение данных из HTML файла
            self.html_data = self._extract_from_html(self.html_file)
            logger.info("Данные из HTML файла извлечены")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении данных: {e}")
            return False
    
    def _extract_from_word(self, file_path: Path) -> Dict:
        """Извлечение данных из Word XML файла"""
        data = {field: None for field in self.REQUIRED_FIELDS}
        
        try:
            # Чтение файла
            content = ""
            if file_path.suffix.lower() == '.docx':
                # Для .docx извлекаем из архива
                content = self._extract_from_docx(file_path)
            else:
                # Для .xml и .doc читаем напрямую
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            
            # Проверяем, что содержимое извлеклось
            if not content or len(content) < 100:
                logger.warning(f"Содержимое Word файла слишком короткое или пустое: {len(content) if content else 0} символов")
                return data
            
            # Логируем начало контента для отладки
            logger.debug(f"Начало Word контента (первые 500 символов): {content[:500]}")
            
            # Извлечение данных с помощью регулярных выражений
            data['purchase_id'] = self._extract_purchase_id_from_word(content)
            data['kpp'] = self._extract_kpp_from_word(content)
            data['email'] = self._extract_email_from_word(content)
            data['phone'] = self._extract_phone_from_word(content)
            
            # Логирование извлеченных данных для отладки
            logger.info(f"Извлечено из Word: {data}")
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении данных из Word файла {file_path}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return data
    
    def _extract_from_docx(self, file_path: Path) -> str:
        """Извлечение содержимого из .docx файла"""
        import zipfile
        
        content = ""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Пробуем несколько возможных путей к документу
                possible_paths = [
                    'word/document.xml',
                    'document.xml',
                    'word/document.xml.rels',
                    'docProps/core.xml'
                ]
                
                for xml_path in possible_paths:
                    if xml_path in zip_ref.namelist():
                        with zip_ref.open(xml_path) as xml_file:
                            xml_content = xml_file.read()
                            try:
                                # Пробуем декодировать как UTF-8
                                content = xml_content.decode('utf-8')
                            except UnicodeDecodeError:
                                # Пробуем другие кодировки
                                content = xml_content.decode('cp1251', errors='ignore')
                        
                        if content and len(content) > 100:
                            logger.debug(f"Найден и прочитан файл в .docx: {xml_path}")
                            break
                
                if not content:
                    # Если не нашли стандартные пути, ищем любой XML файл
                    xml_files = [f for f in zip_ref.namelist() if f.endswith('.xml')]
                    for xml_file in xml_files:
                        with zip_ref.open(xml_file) as f:
                            try:
                                xml_content = f.read()
                                content = xml_content.decode('utf-8', errors='ignore')
                                if 'закупк' in content.lower() or 'контракт' in content.lower():
                                    logger.debug(f"Найден релевантный XML в .docx: {xml_file}")
                                    break
                            except:
                                continue
        
        except Exception as e:
            logger.warning(f"Не удалось распаковать .docx {file_path}: {e}")
            # Пробуем прочитать файл как обычный текст (может быть .doc в текстовом формате)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except:
                pass
        
        return content
    
    def _find_beneficiary_section(self, content: str) -> str:
        """Находит раздел бенефициара в документе (расширенный поиск)"""
        # Ищем секцию "Место нахождения, телефон, адрес электронной почты бенефициара"
        # Это наиболее точный маркер для данных бенефициара
        marker = 'Место нахождения, телефон, адрес электронной почты бенефициара'
        pos = content.find(marker)
        
        if pos == -1:
            # Пробуем альтернативные варианты
            marker = 'бенефициара</w:t>'
            positions = [m.start() for m in re.finditer(marker, content, re.IGNORECASE)]
            if positions:
                # Берём последнее вхождение (обычно это секция с контактами)
                pos = positions[-1]
            else:
                return ""
        
        # Берём содержимое до следующего раздела (обычно "Информация о закупке")
        end_markers = [
            'Информация о закупке',
            'Условия независимой гарантии',
            'Идентификационный код закупки',
            '</w:tbl>',  # конец таблицы
        ]
        
        section_end = len(content)
        for end_marker in end_markers:
            end_pos = content.find(end_marker, pos + 100)
            if end_pos != -1 and end_pos < section_end:
                section_end = end_pos
        
        return content[pos:section_end]
    
    def _extract_data_from_table_cell(self, content: str, marker: str, max_distance: int = 2000) -> str:
        """Извлекает данные из ячейки таблицы после указанного маркера.
        
        Собирает все текстовые фрагменты из <w:t> элементов в одну строку.
        """
        pos = content.find(marker)
        if pos == -1:
            return ""
        
        # Берём контент после маркера до конца строки таблицы
        cell_content = content[pos:pos + max_distance]
        
        # Находим конец текущей строки таблицы
        row_end = cell_content.find('</w:tr>')
        if row_end != -1:
            cell_content = cell_content[:row_end]
        
        # Извлекаем все тексты из <w:t> элементов
        texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', cell_content)
        
        return ''.join(texts)
    
    def _extract_purchase_id_from_word(self, content: str) -> Optional[str]:
        """Извлечение идентификационного кода закупки из Word файла
        
        Код закупки - 36-значное число, может быть разбито на части в XML
        """
        try:
            # Метод 1: Ищем после метки "Идентификационный код закупки"
            marker = 'Идентификационный код закупки'
            pos = content.find(marker)
            
            if pos != -1:
                # Берём ячейку после метки (до конца строки таблицы)
                cell_content = content[pos:pos + 1500]
                row_end = cell_content.find('</w:tr>')
                if row_end != -1:
                    cell_content = cell_content[:row_end]
                
                # Собираем все цифры из <w:t> элементов
                digit_fragments = re.findall(r'<w:t[^>]*>(\d+)</w:t>', cell_content)
                if digit_fragments:
                    combined = ''.join(digit_fragments)
                    # Ищем 36-значный код
                    if len(combined) >= 36:
                        code = combined[:36]
                        logger.info(f"Найден код закупки (из частей): {code}")
                        return code
            
            # Метод 2: Ищем целиком 36-значный код
            match = re.search(r'>(\d{36})<', content)
            if match:
                logger.info(f"Найден код закупки (целиком): {match.group(1)}")
                return match.group(1)
            
            # Метод 3: Ищем любое 36-значное число
            match = re.search(r'\b(\d{36})\b', content)
            if match:
                logger.info(f"Найден код закупки (fallback): {match.group(1)}")
                return match.group(1)
                
        except Exception as e:
            logger.error(f"Ошибка при извлечении кода закупки: {e}")
        
        return None
    
    def _extract_kpp_from_word(self, content: str) -> Optional[str]:
        """Извлечение КПП бенефициара из Word файла
        
        В документах банковской гарантии КПП идут в порядке:
        1. КПП гаранта (банка)
        2. КПП принципала (поставщика)
        3. КПП бенефициара (заказчика) - нужен нам
        
        КПП находится в отдельной ячейке таблицы после метки "КПП"
        Иногда КПП разбит на несколько XML-элементов (например: 50240100 + 2 = 502401002)
        """
        try:
            # Метод 1: Ищем КПП после каждой метки "КПП" в таблице
            # Учитываем, что значение может быть разбито на несколько <w:t> элементов
            kpp_values = []
            
            # Разбиваем по меткам КПП
            kpp_sections = content.split('>КПП<')
            logger.info(f"Найдено {len(kpp_sections) - 1} меток КПП")
            
            for i, section in enumerate(kpp_sections[1:], 1):  # пропускаем первую часть до первого КПП
                # Ищем ячейку таблицы с значением КПП (до следующей строки таблицы)
                # Ограничиваем поиск до </w:tr> (конец строки таблицы)
                row_end = section.find('</w:tr>')
                if row_end == -1:
                    row_end = 1000
                cell_content = section[:row_end]
                
                # Собираем все цифры из <w:t> элементов в этой ячейке
                # Паттерн: <w:t>ЦИФРЫ</w:t> или <w:t ...>ЦИФРЫ</w:t>
                digits_in_cell = re.findall(r'<w:t[^>]*>(\d+)</w:t>', cell_content)
                
                if digits_in_cell:
                    # Объединяем все цифры
                    combined = ''.join(digits_in_cell)
                    # Берем первые 9 цифр (КПП)
                    if len(combined) >= 9:
                        kpp = combined[:9]
                        kpp_values.append(kpp)
                        logger.info(f"КПП #{i}: {kpp} (из частей: {digits_in_cell})")
            
            # Берём третий КПП (бенефициара)
            if len(kpp_values) >= 3:
                kpp = kpp_values[2]
                logger.info(f"Найден КПП бенефициара (3-й): {kpp}")
                return kpp
            
            # Метод 2: Старый паттерн для цельных КПП
            kpp_pattern = r'КПП</w:t>.*?<w:t[^>]*>(\d{9})</w:t>'
            all_kpp = re.findall(kpp_pattern, content, re.IGNORECASE | re.DOTALL)
            
            if len(all_kpp) >= 3:
                kpp = all_kpp[2]
                logger.info(f"Найден КПП бенефициара (паттерн 2): {kpp}")
                return kpp
            
            # Метод 3: Ищем все 9-значные числа похожие на КПП
            all_9digit = re.findall(r'>(\d{9})<', content)
            kpp_candidates = [d for d in all_9digit if d.endswith('001') or d.endswith('002')]
            
            if len(kpp_candidates) >= 3:
                kpp = kpp_candidates[2]
                logger.info(f"Найден КПП бенефициара (по паттерну XXX001/002): {kpp}")
                return kpp
            
            # Метод 4: Fallback - любое третье 9-значное число не начинающееся с 0
            if len(all_9digit) >= 3:
                valid_kpp = [d for d in all_9digit if not d.startswith('0')]
                if len(valid_kpp) >= 3:
                    logger.info(f"Найден КПП бенефициара (fallback): {valid_kpp[2]}")
                    return valid_kpp[2]
        
        except Exception as e:
            logger.error(f"Ошибка при извлечении КПП: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return None
    
    def _extract_email_from_word(self, content: str) -> Optional[str]:
        """Извлечение email бенефициара из Word файла
        
        Email находится в секции "Место нахождения, телефон, адрес электронной почты бенефициара"
        Может быть разбит на части в XML (например: info@gku-mo + 7 + . + ru)
        """
        try:
            # Метод 1: Ищем в секции бенефициара и собираем из частей
            marker = 'Место нахождения, телефон, адрес электронной почты бенефициара'
            pos = content.find(marker)
            
            if pos != -1:
                # Берём расширенную область (до следующего раздела)
                cell_content = content[pos:pos + 5000]
                
                # Ищем конец секции - следующий раздел
                end_markers = ['Информация о закупке', 'Условия независимой гарантии', 'Идентификационный код']
                for end_marker in end_markers:
                    end_pos = cell_content.find(end_marker)
                    if end_pos != -1:
                        cell_content = cell_content[:end_pos]
                        break
                
                # Собираем ВСЕ тексты из <w:t> элементов подряд
                texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', cell_content)
                combined_text = ''.join(texts)  # БЕЗ пробелов - для сборки разбитых значений
                
                # Ищем email в собранном тексте (строгий паттерн - только буквы, цифры, точки, дефисы, подчёркивания)
                email_pattern = r'[a-zA-Z][a-zA-Z0-9._-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                emails = re.findall(email_pattern, combined_text)
                
                # Фильтруем служебные email
                for email in emails:
                    if 'sber' not in email.lower() and 'sberbank' not in email.lower() and 'sb.bg' not in email.lower() and 'puls' not in email.lower():
                        logger.info(f"Найден email бенефициара: {email}")
                        return email
            
            # Метод 2: Позиционный поиск после последнего "бенефициара"
            beneficiary_positions = [m.start() for m in re.finditer('бенефициара</w:t>', content)]
            
            if beneficiary_positions:
                last_beneficiary_pos = beneficiary_positions[-1]
                search_area = content[last_beneficiary_pos:last_beneficiary_pos + 5000]
                
                # Собираем тексты без пробелов
                texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', search_area)
                combined_text = ''.join(texts)
                
                email_pattern = r'[a-zA-Z][a-zA-Z0-9._-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                emails = re.findall(email_pattern, combined_text)
                
                for email in emails:
                    if 'sber' not in email.lower() and 'sb.bg' not in email.lower() and 'puls' not in email.lower():
                        logger.info(f"Найден email (позиционный метод): {email}")
                        return email
            
            # Метод 3: Fallback - ищем во всём документе
            all_emails = re.findall(r'[a-zA-Z][a-zA-Z0-9._-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
            filtered = [e for e in all_emails if 'sber' not in e.lower() and 'sb.bg' not in e.lower() and 'puls' not in e.lower()]
            if filtered:
                for email in filtered:
                    if 'info@' in email.lower() or 'gku' in email.lower() or 'yandex' in email.lower():
                        return email
                return filtered[0] if filtered else None
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении email: {e}")
        
        return None
    
    def _extract_phone_from_word(self, content: str) -> Optional[str]:
        """Извлечение телефона бенефициара из Word файла
        
        Телефон находится в секции "Место нахождения, телефон, адрес электронной почты бенефициара"
        Может быть разбит на части в XML (например: 7-495-646729 + 7)
        """
        try:
            # ВАЖНО: Паттерны для телефонов
            phone_patterns = [
                # Формат 7-XXX-XXXXXXX
                r'7-\d{3}-\d{7}',
                # Формат 7-XXXX-XXXXXX  
                r'7-\d{4}-\d{6}',
                # Формат +7 XXXX XX XX XX
                r'\+7\s*\d{3,4}\s+\d{2}\s+\d{2}\s+\d{2}',
                # Формат +7-XXX-XXX-XX-XX
                r'\+7-\d{3}-\d{3}-\d{2}-\d{2}',
                # Формат +7 (XXX) XXX-XX-XX
                r'\+7\s*\(\d{3}\)\s*\d{3}-\d{2}-\d{2}',
                # Формат +7(XXX)XXX-XX-XX
                r'\+7\(\d{3}\)\d{3}-\d{2}-\d{2}',
            ]
            
            # Метод 1: Ищем в секции бенефициара и собираем из частей
            marker = 'Место нахождения, телефон, адрес электронной почты бенефициара'
            pos = content.find(marker)
            
            if pos != -1:
                # Берём расширенную область
                cell_content = content[pos:pos + 5000]
                
                # Ищем конец секции
                end_markers = ['Информация о закупке', 'Условия независимой гарантии', 'Идентификационный код']
                for end_marker in end_markers:
                    end_pos = cell_content.find(end_marker)
                    if end_pos != -1:
                        cell_content = cell_content[:end_pos]
                        break
                
                # Собираем ВСЕ тексты из <w:t> элементов БЕЗ пробелов
                texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', cell_content)
                combined_text = ''.join(texts)
                
                # Ищем телефон в собранном тексте
                for pattern in phone_patterns:
                    matches = re.findall(pattern, combined_text)
                    if matches:
                        phone = matches[0]
                        digits = re.sub(r'[^\d]', '', phone)
                        if not self._is_oktmo(digits):
                            logger.info(f"Найден телефон бенефициара: {phone}")
                            return phone
            
            # Метод 2: Позиционный поиск после последнего "бенефициара"
            beneficiary_positions = [m.start() for m in re.finditer('бенефициара</w:t>', content)]
            if beneficiary_positions:
                last_pos = beneficiary_positions[-1]
                search_area = content[last_pos:last_pos + 5000]
                
                # Собираем тексты без пробелов
                texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', search_area)
                combined_text = ''.join(texts)
                
                for pattern in phone_patterns:
                    matches = re.findall(pattern, combined_text)
                    if matches:
                        phone = matches[0]
                        digits = re.sub(r'[^\d]', '', phone)
                        if not self._is_oktmo(digits):
                            if not ('500' in phone and '55' in phone):
                                logger.info(f"Найден телефон (позиционный): {phone}")
                                return phone
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении телефона: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return None
    
    def _is_oktmo(self, digits: str) -> bool:
        """Проверяет, является ли число кодом ОКТМО"""
        # ОКТМО - это 8 или 11 цифр, начинается с кода региона (01-99)
        # Телефоны начинаются с 7 или 8
        if len(digits) == 11:
            # Если начинается с 7 или 8 - это телефон
            if digits[0] in '78':
                return False
            # Если начинается с кода региона (не 7 и не 8) - это ОКТМО
            return True
        if len(digits) == 10:
            # 10 цифр - скорее всего телефон без кода страны
            return False
        return False
    
    def _extract_from_html(self, file_path: Path) -> Dict:
        """Извлечение данных из HTML файла"""
        data = {field: None for field in self.REQUIRED_FIELDS}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Извлечение данных
            data['purchase_id'] = self._extract_purchase_id_from_html(content)
            
            # Извлечение из блока 2.1
            customer_info = self._extract_customer_info_from_html(content)
            data['kpp'] = customer_info.get('kpp')
            data['email'] = customer_info.get('email')
            data['phone'] = customer_info.get('phone')
            
            logger.info(f"Извлечено из HTML: {data}")
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении данных из HTML: {e}")
        
        return data
    
    def _extract_purchase_id_from_html(self, content: str) -> Optional[str]:
        """Извлечение идентификационного кода закупки из раздела 1.2"""
        try:
            # Ищем раздел 1.2
            markers = [
                '1.2. Основание заключения контракта',
                '1.2 Основание заключения контракта',
            ]
            
            for marker in markers:
                pos = content.find(marker)
                if pos != -1:
                    # Ищем таблицу после маркера
                    table_start = content.find('<table', pos)
                    if table_start != -1:
                        table_end = self._find_table_end(content, table_start)
                        table_content = content[table_start:table_end]
                        
                        # Ищем идентификационный код закупки
                        patterns = [
                            r'Идентификационный код закупки[^<]*</td>\s*<td[^>]*>([^<]+)</td>',
                            r'код закупки[^<]*</td>\s*<td[^>]*>([^<]+)</td>',
                            r'>(\d{36})<',
                        ]
                        
                        for pattern in patterns:
                            match = re.search(pattern, table_content, re.IGNORECASE | re.DOTALL)
                            if match:
                                code = match.group(1).strip()
                                code = re.sub(r'[^\d]', '', code)
                                if len(code) == 36:
                                    return code
            
            # Fallback: ищем по всему документу
            match = re.search(r'\b(\d{36})\b', content)
            if match:
                return match.group(1)
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении ID закупки из HTML: {e}")
        
        return None
    
    def _extract_customer_info_from_html(self, content: str) -> Dict:
        """Извлечение информации о заказчике из раздела 2.1"""
        info = {'kpp': None, 'email': None, 'phone': None}
        
        try:
            # Ищем раздел 2.1
            markers = [
                '2.1. Информация о заказчике',
                '2.1 Информация о заказчике',
            ]
            
            for marker in markers:
                pos = content.find(marker)
                if pos != -1:
                    # Ищем таблицу после маркера
                    table_start = content.find('<table', pos)
                    if table_start != -1:
                        table_end = self._find_table_end(content, table_start)
                        table_content = content[table_start:table_end]
                        
                        # Извлекаем КПП
                        kpp_match = re.search(r'КПП[^<]*</td>\s*<td[^>]*>([^<]+)</td>', table_content, re.IGNORECASE | re.DOTALL)
                        if kpp_match:
                            kpp = re.sub(r'[^\d]', '', kpp_match.group(1))
                            if len(kpp) == 9:
                                info['kpp'] = kpp
                        
                        # Извлекаем email
                        email_match = re.search(r'Адрес электронной почты[^<]*</td>\s*<td[^>]*>([^<]+)</td>', table_content, re.IGNORECASE | re.DOTALL)
                        if email_match:
                            email = email_match.group(1).strip()
                            if re.match(r'[\w\.-]+@[\w\.-]+\.\w+', email):
                                info['email'] = email
                        
                        # Извлекаем телефон
                        phone_match = re.search(r'Номер контактного телефона[^<]*</td>\s*<td[^>]*>([^<]+)</td>', table_content, re.IGNORECASE | re.DOTALL)
                        if phone_match:
                            info['phone'] = phone_match.group(1).strip()
                        
                        break
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении информации о заказчике: {e}")
        
        return info
    
    def _find_table_end(self, content: str, start: int) -> int:
        """Находит конец таблицы с учетом вложенных таблиц"""
        depth = 0
        pos = start
        
        while pos < len(content):
            open_tag = content.find('<table', pos + 1)
            close_tag = content.find('</table>', pos + 1)
            
            if close_tag == -1:
                return len(content)
            
            if open_tag != -1 and open_tag < close_tag:
                depth += 1
                pos = open_tag
            else:
                if depth == 0:
                    return close_tag + 8
                depth -= 1
                pos = close_tag
        
        return len(content)
    
    def compare_data(self) -> Dict:
        """Сравнение извлеченных данных"""
        self.differences = []
        comparison_result = {
            'all_match': True,
            'details': {},
            'differences': []
        }
        
        field_names = {
            'purchase_id': 'Идентификационный код закупки',
            'kpp': 'КПП',
            'email': 'Адрес электронной почты',
            'phone': 'Номер контактного телефона'
        }
        
        for field in self.REQUIRED_FIELDS:
            word_value = self.word_data.get(field)
            html_value = self.html_data.get(field)
            
            # Специальная обработка для телефонов - нормализация перед сравнением
            if field == 'phone':
                match = PhoneNormalizer.are_equal(word_value or '', html_value or '') if word_value and html_value else False
            else:
                match = word_value == html_value if word_value and html_value else False
            
            comparison_result['details'][field] = {
                'word': word_value,
                'html': html_value,
                'match': match
            }
            
            if not match:
                comparison_result['all_match'] = False
                self.differences.append((field, field_names[field], word_value, html_value))
                comparison_result['differences'].append({
                    'field': field,
                    'name': field_names[field],
                    'word': word_value,
                    'html': html_value
                })
        
        self.results = comparison_result
        return comparison_result
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """Генерация отчета о сравнении"""
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.folder_path / f'comparison_report_{timestamp}.txt'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("ОТЧЕТ О СРАВНЕНИИ ДОКУМЕНТОВ\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Дата сравнения: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
            f.write(f"Папка: {self.folder_path}\n")
            f.write(f"Word файл: {self.word_file}\n")
            f.write(f"HTML файл: {self.html_file}\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("ИЗВЛЕЧЕННЫЕ ДАННЫЕ:\n")
            f.write("=" * 80 + "\n\n")
            
            field_names = {
                'purchase_id': 'Идентификационный код закупки',
                'kpp': 'КПП',
                'email': 'Адрес электронной почты',
                'phone': 'Номер контактного телефона'
            }
            
            f.write("Из Word файла:\n")
            for field, name in field_names.items():
                value = self.word_data.get(field, 'Не найден')
                f.write(f"  {name}: {value}\n")
            
            f.write("\nИз HTML файла:\n")
            for field, name in field_names.items():
                value = self.html_data.get(field, 'Не найден')
                f.write(f"  {name}: {value}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("РЕЗУЛЬТАТЫ СРАВНЕНИЯ:\n")
            f.write("=" * 80 + "\n\n")
            
            if self.results.get('all_match'):
                f.write("✅ ВСЕ ДАННЫЕ СОВПАДАЮТ!\n")
            else:
                f.write("⚠️ ЕСТЬ НЕСОВПАДЕНИЯ!\n\n")
                
                if self.differences:
                    f.write(f"Обнаружено {len(self.differences)} расхождений:\n\n")
                    for diff in self.differences:
                        field, name, word_val, html_val = diff
                        f.write(f"• {name}:\n")
                        f.write(f"    Word: {word_val if word_val else 'Не найден'}\n")
                        f.write(f"    HTML: {html_val if html_val else 'Не найден'}\n")
                        
                        # Для телефонов показываем нормализованные значения
                        if field == 'phone' and word_val and html_val:
                            f.write(f"    Word (норм.): {PhoneNormalizer.normalize(word_val)}\n")
                            f.write(f"    HTML (норм.): {PhoneNormalizer.normalize(html_val)}\n")
                        f.write("\n")
        
        logger.info(f"Отчет сохранен: {output_path}")
        return str(output_path)


# Графический интерфейс
class ProcurementComparatorGUI:
    """Графический интерфейс приложения"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Сравнение документов")
        self.root.geometry("900x700")
        
        self.comparator = ProcurementFileComparator()
        
        # Настройка стилей
        self.setup_styles()
        
        # Создание интерфейса
        self.create_widgets()
        
        # Центрирование окна
        self.center_window()
    
    def setup_styles(self):
        """Настройка стилей элементов"""
        style = ttk.Style()
        
        # Настройка цветов
        self.root.configure(bg='#f0f0f0')
        
        # Стиль для заголовков
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'), background='#f0f0f0')
        style.configure('Section.TLabel', font=('Arial', 11, 'bold'), background='#f0f0f0')
        
        # Стиль для кнопок
        style.configure('Action.TButton', font=('Arial', 10), padding=5)
        style.configure('Primary.TButton', font=('Arial', 10, 'bold'), padding=5)
    
    def center_window(self):
        """Центрирование окна на экране"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Создание элементов интерфейса"""
        # Главный контейнер
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка весов для растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Сравнение документов", 
                                style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Раздел 1: Выбор файлов
        folder_frame = ttk.LabelFrame(main_frame, text="1. Выбор файлов", padding="10")
        folder_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        folder_frame.columnconfigure(1, weight=1)
        
        self.folder_label = ttk.Label(folder_frame, text="Файлы не выбраны", 
                                      wraplength=600, relief='solid', padding=5)
        self.folder_label.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(folder_frame, text="Word файл", 
                  command=self.select_word_file, style='Primary.TButton').grid(row=1, column=0, sticky=tk.W)
        
        ttk.Button(folder_frame, text="HTML файл", 
                  command=self.select_html_file, style='Action.TButton').grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # Раздел 2: Найденные файлы
        files_frame = ttk.LabelFrame(main_frame, text="2. Найденные файлы", padding="10")
        files_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        files_frame.columnconfigure(0, weight=1)
        
        # Фрейм для Word файла
        word_frame = ttk.Frame(files_frame)
        word_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(word_frame, text="Word файл:", width=12, anchor=tk.W).grid(row=0, column=0, sticky=tk.W)
        self.word_file_label = ttk.Label(word_frame, text="Не найден", foreground='red')
        self.word_file_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Фрейм для HTML файла
        html_frame = ttk.Frame(files_frame)
        html_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(html_frame, text="HTML файл:", width=12, anchor=tk.W).grid(row=0, column=0, sticky=tk.W)
        self.html_file_label = ttk.Label(html_frame, text="Не найден", foreground='red')
        self.html_file_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Раздел 3: Сравнение
        compare_frame = ttk.LabelFrame(main_frame, text="3. Сравнение данных", padding="10")
        compare_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(compare_frame, text="Извлечь и сравнить данные", 
                  command=self.compare_data, style='Primary.TButton').grid(row=0, column=0, sticky=tk.W)
        
        ttk.Button(compare_frame, text="Создать отчет", 
                  command=self.generate_report, style='Action.TButton').grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Раздел 4: Результаты
        results_frame = ttk.LabelFrame(main_frame, text="4. Результаты", padding="10")
        results_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Текстовое поле с прокруткой
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, 
                                                      font=('Courier', 10))
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Статусная строка
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                               relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def select_word_file(self):
        """Выбор Word файла"""
        file_path = filedialog.askopenfilename(
            title="Выберите Word файл",
            filetypes=[("Word файлы", "*.doc *.docx"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.comparator.word_file = Path(file_path)
            self.folder_label.config(text=f"Word: {Path(file_path).name}")
            self.word_file_label.config(text=Path(file_path).name, foreground='green')
            self.update_status(f"Выбран Word файл: {Path(file_path).name}")
    
    def select_html_file(self):
        """Выбор HTML файла"""
        file_path = filedialog.askopenfilename(
            title="Выберите HTML файл",
            filetypes=[("HTML файлы", "*.html *.htm"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.comparator.html_file = Path(file_path)
            # Обновляем метку
            current_text = self.folder_label.cget("text")
            if current_text.startswith("Word:"):
                self.folder_label.config(text=f"{current_text}\nHTML: {Path(file_path).name}")
            else:
                self.folder_label.config(text=f"HTML: {Path(file_path).name}")
            self.html_file_label.config(text=Path(file_path).name, foreground='green')
            self.update_status(f"Выбран HTML файл: {Path(file_path).name}")
    
    def compare_data(self):
        """Извлечение и сравнение данных"""
        if not self.comparator.word_file or not self.comparator.html_file:
            messagebox.showwarning("Предупреждение", "Сначала найдите файлы")
            return
        
        self.update_status("Извлечение данных...")
        self.root.update()
        
        # Извлечение данных
        if not self.comparator.extract_data():
            messagebox.showerror("Ошибка", "Не удалось извлечь данные из файлов")
            return
        
        # Сравнение
        results = self.comparator.compare_data()
        
        # Отображение результатов
        self.display_results(results)
        
        if results['all_match']:
            self.update_status("✅ Все данные совпадают!")
        else:
            self.update_status(f"⚠️ Обнаружено {len(results['differences'])} расхождений")
    
    def display_results(self, results: Dict):
        """Отображение результатов сравнения"""
        self.results_text.delete(1.0, tk.END)
        
        field_names = {
            'purchase_id': 'Идентификационный код закупки',
            'kpp': 'КПП',
            'email': 'Адрес электронной почты',
            'phone': 'Номер контактного телефона'
        }
        
        # Заголовок
        self.results_text.insert(tk.END, "=" * 60 + "\n")
        self.results_text.insert(tk.END, "РЕЗУЛЬТАТЫ СРАВНЕНИЯ\n")
        self.results_text.insert(tk.END, "=" * 60 + "\n\n")
        
        # Детальное сравнение
        for field, name in field_names.items():
            detail = results['details'].get(field, {})
            word_val = detail.get('word', 'Не найден')
            html_val = detail.get('html', 'Не найден')
            match = detail.get('match', False)
            
            status = "✅" if match else "❌"
            self.results_text.insert(tk.END, f"{status} {name}:\n")
            self.results_text.insert(tk.END, f"   Word: {word_val if word_val else 'Не найден'}\n")
            self.results_text.insert(tk.END, f"   HTML: {html_val if html_val else 'Не найден'}\n")
            
            # Для телефонов показываем нормализованные значения
            if field == 'phone' and word_val and html_val:
                word_norm = PhoneNormalizer.normalize(word_val)
                html_norm = PhoneNormalizer.normalize(html_val)
                self.results_text.insert(tk.END, f"   Word (норм.): {word_norm}\n")
                self.results_text.insert(tk.END, f"   HTML (норм.): {html_norm}\n")
            
            self.results_text.insert(tk.END, "\n")
        
        # Итог
        self.results_text.insert(tk.END, "=" * 60 + "\n")
        if results['all_match']:
            self.results_text.insert(tk.END, "✅ ВСЕ ДАННЫЕ СОВПАДАЮТ!\n")
        else:
            self.results_text.insert(tk.END, f"⚠️ ОБНАРУЖЕНО {len(results['differences'])} РАСХОЖДЕНИЙ\n")
    
    def generate_report(self):
        """Генерация отчета"""
        if not self.comparator.results:
            messagebox.showwarning("Предупреждение", "Сначала выполните сравнение данных")
            return
        
        report_path = self.comparator.generate_report()
        messagebox.showinfo("Успех", f"Отчет сохранен:\n{report_path}")
        self.update_status(f"Отчет сохранен: {report_path}")
    
    def update_status(self, message: str):
        """Обновление статусной строки"""
        self.status_var.set(message)


def run_console_mode():
    """Запуск в консольном режиме"""
    print("=" * 60)
    print("Сравнение документов")
    print("=" * 60)
    
    comparator = ProcurementFileComparator()
    
    # Запрос пути к папке
    folder_path = input("\nВведите путь к папке с файлами: ").strip()
    
    if not folder_path:
        print("Путь не указан. Выход.")
        return
    
    if not comparator.set_folder(folder_path):
        print("Ошибка: указанная папка не существует")
        return
    
    # Поиск файлов
    print("\nПоиск файлов...")
    success, message = comparator.find_files()
    
    if not success:
        print(f"Ошибка: {message}")
        return
    
    print(f"Найден Word файл: {comparator.word_file}")
    print(f"Найден HTML файл: {comparator.html_file}")
    
    # Извлечение данных
    print("\nИзвлечение данных...")
    if not comparator.extract_data():
        print("Ошибка при извлечении данных")
        return
    
    # Сравнение
    print("\nСравнение данных...")
    results = comparator.compare_data()
    
    # Вывод результатов
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ СРАВНЕНИЯ")
    print("=" * 60)
    
    field_names = {
        'purchase_id': 'Идентификационный код закупки',
        'kpp': 'КПП',
        'email': 'Адрес электронной почты',
        'phone': 'Номер контактного телефона'
    }
    
    for field, name in field_names.items():
        detail = results['details'].get(field, {})
        word_val = detail.get('word', 'Не найден')
        html_val = detail.get('html', 'Не найден')
        match = detail.get('match', False)
        
        status = "✅" if match else "❌"
        print(f"\n{status} {name}:")
        print(f"   Word: {word_val if word_val else 'Не найден'}")
        print(f"   HTML: {html_val if html_val else 'Не найден'}")
        
        if field == 'phone' and word_val and html_val:
            print(f"   Word (норм.): {PhoneNormalizer.normalize(word_val)}")
            print(f"   HTML (норм.): {PhoneNormalizer.normalize(html_val)}")
    
    print("\n" + "=" * 60)
    if results['all_match']:
        print("✅ ВСЕ ДАННЫЕ СОВПАДАЮТ!")
    else:
        print(f"⚠️ ОБНАРУЖЕНО {len(results['differences'])} РАСХОЖДЕНИЙ")
    
    # Генерация отчета
    generate = input("\nСоздать отчет? (y/n): ").strip().lower()
    if generate == 'y':
        report_path = comparator.generate_report()
        print(f"Отчет сохранен: {report_path}")


def main():
    """Главная функция"""
    if GUI_AVAILABLE:
        root = tk.Tk()
        app = ProcurementComparatorGUI(root)
        root.mainloop()
    else:
        run_console_mode()


if __name__ == "__main__":
    main()
