import pymem
import pymem.pattern
import struct
import time
import re

def safe_pattern_scan(pm, raw_pattern):
    found_addresses = []
    try:
        res = pymem.pattern.pattern_scan_all(pm.process_handle, raw_pattern, return_multiple=True)
        if res: found_addresses.extend(res)
    except: pass
    return list(set(found_addresses))

def main():
    process_name = 'java.exe'
    try:
        pm = pymem.Pymem(process_name)
        print(f"[+] Подключено к {process_name}")
    except pymem.exception.ProcessNotFound:
        print(f"[-] Процесс {process_name} не найден.")
        return

    # Задаем параметры для парения (Glide)
    target_val = 0.9800000190734863
    replace_val = 0.9999
    
    target_bytes = struct.pack('<d', target_val)
    replacement_bytes = struct.pack('<d', replace_val)
    original_bytes_map = {}

    print(f"[*] Сканирование константы {target_val}...")
    raw_pattern = b"".join(re.escape(bytes([b])) for b in target_bytes)
    found = safe_pattern_scan(pm, raw_pattern)
    
    # Сортируем адреса для удобства перебора
    found = sorted(found)
    print(f"[+] Найдено совпадений: {len(found)}")
    
    if len(found) == 0:
        print("[-] Совпадений не найдено. Проверьте версию игры.")
        return

    print("\n--- РЕЖИМ ТОЧЕЧНОГО ТЕСТИРОВАНИЯ ---")
    print("Инструкция: вводите номер адреса (от 0 до N), чтобы изменить его.")
    print("Чтобы вернуть оригинальное значение обратно, введите тот же номер еще раз.")
    print("Для выхода введите 'q'")

    # Сохраняем оригинальные байты каждого адреса на случай отката
    active_patches = set()
    for addr in found:
        try: original_bytes_map[addr] = pm.read_bytes(addr, 8)
        except: original_bytes_map[addr] = target_bytes

    while True:
        print("\nТекущий статус адресов:")
        for idx, addr in enumerate(found):
            status = "[АКТИВЕН (ЧИТ)]" if addr in active_patches else "[Оригинал]"
            print(f" [{idx}] {hex(addr)} {status}")

        user_input = input("\nВведите номер адреса для переключения (или 'q' for exit): ").strip()
        
        if user_input.lower() == 'q':
            # При выходе возвращаем всё в исходное состояние, чтобы игра не вылетела
            print("[*] Возврат оригинальных значений перед выходом...")
            for addr in active_patches:
                pm.write_bytes(addr, original_bytes_map[addr], 8)
            break

        try:
            idx = int(user_input)
            if idx < 0 or idx >= len(found):
                print("[-] Неверный индекс.")
                continue
                
            addr = found[idx]
            
            if addr in active_patches:
                # Если уже был изменен — возвращаем оригинал
                pm.write_bytes(addr, original_bytes_map[addr], 8)
                active_patches.remove(addr)
                print(f"[<-] Адрес {hex(addr)} восстановлен в оригинал (0.98)")
            else:
                # Если оригинал — пишем чит
                pm.write_bytes(addr, replacement_bytes, 8)
                active_patches.add(addr)
                print(f"[->] Адрес {hex(addr)} изменен на 0.9999! Проверяйте в игре.")
                
        except ValueError:
            print("[-] Пожалуйста, введите корректное число.")
        except Exception as e:
            print(f"[-] Ошибка при записи в адрес: {e}")

if __name__ == "__main__":
    main()
