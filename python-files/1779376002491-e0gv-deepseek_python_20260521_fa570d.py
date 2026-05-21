import os
import sys
import subprocess
import time

def main():
    print("=" * 40)
    print("ОЧИСТКА ПЕРЕД ИГРОЙ")
    print("=" * 40)
    print()
    
    # 1. Чистим временные файлы
    print("[1/3] Чищу временные файлы...")
    temp_dirs = [os.environ.get('TEMP'), os.environ.get('TMP')]
    deleted = 0
    for temp_dir in temp_dirs:
        if temp_dir and os.path.exists(temp_dir):
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for name in files:
                    try:
                        os.remove(os.path.join(root, name))
                        deleted += 1
                    except:
                        pass
    print(f"      Удалено файлов: {deleted}")
    
    # 2. Очищаем корзину
    print("[2/3] Очищаю корзину...")
    try:
        subprocess.run('rd /s /q C:\\$Recycle.bin 2>nul', shell=True)
        print("      Корзина очищена")
    except:
        print("      Не удалось очистить корзину")
    
    # 3. Чистим кэш DNS
    print("[3/3] Чищу DNS кэш...")
    subprocess.run('ipconfig /flushdns', shell=True, capture_output=True)
    print("      DNS кэш очищен")
    
    print()
    print("=" * 40)
    print("ГОТОВО! Можно запускать игру")
    print("=" * 40)
    print()
    print("Советы:")
    print("- Закрой браузер перед игрой")
    print("- Поставь игру на весь экран, а не в окне")
    print("- В Roblox уменьши графику на 1-2 пункта")
    print("- В Lost Light поставь пресет 'Низкий'")
    print()
    input("Нажми Enter для выхода...")

if __name__ == "__main__":
    main()