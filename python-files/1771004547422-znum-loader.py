import os
import subprocess
import sys
import time

# Автоматически определяем папку, где лежит loader.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)  # Меняем рабочую директорию на папку с лоадером

ART = r'''
 '     /$$$$$$$                                 /$$$$$$                      /$$      
'    | $$__  $$                               /$$__  $$                    | $$      
'    | $$  \ $$  /$$$$$$   /$$$$$$   /$$$$$$ | $$  \__/  /$$$$$$   /$$$$$$ | $$   /$$
'    | $$  | $$ /$$__  $$ /$$__  $$ /$$__  $$|  $$$$$$  /$$__  $$ /$$__  $$| $$  /$$/
'    | $$  | $$| $$$$$$$$| $$$$$$$$| $$  \ $$ \____  $$| $$$$$$$$| $$$$$$$$| $$$$$$/ 
'    | $$  | $$| $$_____/| $$_____/| $$  | $$ /$$  \ $$| $$_____/| $$_____/| $$_  $$ 
'    | $$$$$$$/|  $$$$$$$|  $$$$$$$| $$$$$$$/|  $$$$$$/|  $$$$$$$|  $$$$$$$| $$ \  $$
'    |_______/  \_______/ \_______/| $$____/  \______/  \_______/ \_______/|__/  \__/
'                                  | $$                                              
'                                  | $$                                              
'                                  |__/                                              
'''

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_menu():
    clear()
    print(ART)
    print("[#] Никнейм: DeepSeek")
    print("[#] Количество ОЗУ: 3048")
    print("[#] Статус: не установлено.")
    print()
    print("[1] - Запустить")
    print("[2] - Указать оперативную память")
    print("[3] - Посмотреть change-logs")
    print("[0] - Выход")
    print()
    print("Выберите опцию:")

def launch_game(memory_mb=3048):
    client_jar = "client.jar"
    if not os.path.exists(client_jar):
        print(f"❌ Файл '{client_jar}' не найден в папке:\n{BASE_DIR}")
        input("\nНажмите Enter для возврата...")
        return

    java_cmd = [
        "java",
        f"-Xms{memory_mb}M",
        f"-Xmx{memory_mb}M",
        "-Djava.library.path=natives",
        "-cp", client_jar,
        "Start"
    ]

    print("\n🚀 Запуск Minecraft...")
    time.sleep(1)
    try:
        # Запускаем в фоне, без привязки к консоли
        subprocess.Popen(java_cmd, cwd=BASE_DIR)
        print("✅ Игра запущена. Лоадер закроется через 2 секунды...")
        time.sleep(2)
        sys.exit(0)
    except FileNotFoundError:
        print("❌ Java не установлена или не добавлена в PATH!")
        input("\nНажмите Enter...")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        input("\nНажмите Enter...")

def set_memory():
    try:
        mem = int(input("Введите объём ОЗУ (МБ, например 4096): "))
        if mem < 512 or mem > 8192:
            print("⚠️  Рекомендуемое значение: 2048–6144 МБ")
            input("\nНажмите Enter...")
            return
        with open("memory.txt", "w") as f:
            f.write(str(mem))
        print(f"✅ Установлено: {mem} МБ")
        input("\nНажмите Enter...")
    except ValueError:
        print("❌ Введите число!")
        input("\nНажмите Enter...")

def show_logs():
    clear()
    print(ART)
    print("\n[CHANGELOG v1.0]\n")
    print("• Добавлен модуль AutoSay")
    print("• Исправлен Speed для Matrix/Intave")
    print("• Добавлен Escape — побег от алмазника")
    print("• Улучшена стабильность лоадера")
    print("\nНажмите Enter для возврата...")
    input()

def main():
    while True:
        print_menu()
        choice = input().strip()

        if choice == "1":
            mem = 3048
            if os.path.exists("memory.txt"):
                try:
                    with open("memory.txt") as f:
                        mem = int(f.read())
                except:
                    pass
            launch_game(mem)

        elif choice == "2":
            set_memory()

        elif choice == "3":
            show_logs()

        elif choice == "0":
            print("\n👋 Пока, DeepSeek!")
            time.sleep(1)
            break

        else:
            print("\n❌ Неверный выбор.")
            time.sleep(1)

if __name__ == "__main__":
    main()