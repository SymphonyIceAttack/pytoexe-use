import time
import os
from colorama import init, Fore, Back, Style

# Инициализация colorama для цветных сообщений
init()

def clear_screen():
    """Очистка экрана консоли"""
    os.system('cls' if os.name == 'nt' else 'clear')

def loading_animation(duration=2):
    """Анимация загрузки с точками"""
    print(Fore.CYAN + "Инициализация системы..." + Style.RESET_ALL)
    for _ in range(duration * 4):
        print(Fore.YELLOW + "." + Style.RESET_ALL, end="", flush=True)
        time.sleep(0.25)
    print()

def show_menu():
    """Отображение главного меню"""
    clear_screen()
    print(Fore.GREEN + "=" * 50)
    print("      СИСТЕМА ЗАГРУЗКИ МОДУЛЯ ЧИТА")
    print("=" * 50 + Style.RESET_ALL)
    print(Fore.WHITE + "Доступные операции:" + Style.RESET_ALL)
    print(Fore.CYAN + "1. " + Fore.WHITE + "Запустить чит-модуль")
    print(Fore.CYAN + "2. " + Fore.WHITE + "Оптимизировать ОЗУ")
    print(Fore.CYAN + "3. " + Fore.WHITE + "Выйти из системы")
    print(Fore.GREEN + "-" * 50 + Style.RESET_ALL)

def fake_cheat_loader():
    while True:
        show_menu()
        choice = input(Fore.YELLOW + "Выберите действие (1-3): " + Style.RESET_ALL).strip()

        if choice == '1':
            clear_screen()
            print(Fore.MAGENTA + "ЗАПУСК ЧИТ-МОДУЛЯ..." + Style.RESET_ALL)
            loading_animation(3)

            # Прогресс-бар загрузки
            print(Fore.CYAN + "Загрузка компонентов:" + Style.RESET_ALL)
            for i in range(0, 101, 25):
                time.sleep(0.8)
                bar = "[" + "█" * (i // 10) + " " * (10 - i // 10) + "]"
                print(f"{Fore.GREEN}{bar} {i}%{Style.RESET_ALL}")

            print(Fore.GREEN + "\n✓ [+] успешно лоаднут." + Style.RESET_ALL)
            input(Fore.CYAN + "\nНажмите Enter для продолжения..." + Style.RESET_ALL)

        elif choice == '2':
            clear_screen()

            loading_animation(2)

            print(Fore.WHITE + "Текущие параметры:" + Style.RESET_ALL)
            print(f"  {Fore.CYAN}• Объём:{Style.RESET_ALL} 8 ГБ DDR4")
            print(f"  {Fore.CYAN}• Частота:{Style.RESET_ALL} 3200 МГц")
            print(f"  {Fore.CYAN}• Тайминги:{Style.RESET_ALL} 16-18-18-36")

            print(Fore.YELLOW + "\nОптимизация параметров..." + Style.RESET_ALL)
            time.sleep(1.5)
            input(Fore.CYAN + "\nНажмите Enter для продолжения..." + Style.RESET_ALL)

        elif choice == '3':
            clear_screen()
            print(Fore.RED + "ЗАКРЫТИЕ СИСТЕМЫ..." + Style.RESET_ALL)
            loading_animation(1)
            print(Fore.GREEN + "Система безопасно закрыта. До новых встреч!" + Style.RESET_ALL)
            break

        else:
            print(Fore.RED + "\nОшибка: Неверный выбор! Введите 1, 2 или 3." + Style.RESET_ALL)
            time.sleep(1.5)

if __name__ == "__main__":
    fake_cheat_loader()