import win32print
import win32api
import time

def print_to_godex(printer_name: str, ezpl_commands: str, encoding: str = 'cp437') -> bool:
    """
    Отправка команд EZPL на принтер Godex через драйвер Windows.
    
    Args:
        printer_name: Имя принтера в системе (точное совпадение!)
        ezpl_commands: Строка с командами на языке EZPL
        encoding: Кодировка (по умолчанию 'cp437' — стандарт для термопринтеров)
    
    Returns:
        True при успешной отправке, иначе False
    """
    try:
        # Открываем принтер
        hprinter = win32print.OpenPrinter(printer_name)
        
        # Подготавливаем данные документа
        doc_info = ("Godex Label", None, None)
        win32print.StartDocPrinter(hprinter, 1, doc_info)
        win32print.StartPagePrinter(hprinter)
        
        # Отправляем сырые данные
        raw_data = ezpl_commands.encode(encoding)
        win32print.WritePrinter(hprinter, raw_data)
        
        # Завершаем печать
        win32print.EndPagePrinter(hprinter)
        win32print.EndDocPrinter(hprinter)
        win32print.ClosePrinter(hprinter)
        
        print(f"✅ Метка успешно отправлена на принтер '{printer_name}'")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка печати: {e}")
        return False

def create_sample_label(text: str = "Hello World") -> str:
    """
    Генерация простой метки на языке EZPL.
    """
    return f"""SIZE 60 mm, 30 mm
GAP 2 mm, 0 mm
CLS
TEXT 10,10,"1",0,1,1,"{text}"
TEXT 10,40,"1",0,1,1,"Godex GE330"
BARCODE 10,80,"128",50,0,0,2,4,"1234567890"
PRINT 1
"""

if __name__ == "__main__":
    # 🔍 Как узнать точное имя принтера:
    #   1. Откройте «Панель управления → Устройства и принтеры»
    #   2. Или выполните в Python:
    #      print(win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL))
    
    PRINTER_NAME = "Godex GE330"  # ⚠️ Замените на имя вашего принтера!
    
    # Проверка существования принтера
    printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]
    if PRINTER_NAME not in printers:
        print(f"⚠️ Принтер '{PRINTER_NAME}' не найден. Доступные принтеры:")
        for p in printers:
            print(f"  - {p}")
        exit(1)
    
    # Формируем метку
    label = create_sample_label("Тестовая печать")
    
    # Отправляем на печать
    success = print_to_godex(PRINTER_NAME, label)
    
    if success:
        print("🖨️ Печать запущена. Подождите 2–3 секунды...")
        time.sleep(3)  # Опционально: ожидание завершения печати