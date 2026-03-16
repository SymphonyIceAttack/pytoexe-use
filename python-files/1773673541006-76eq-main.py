import os
import sys
import time
import webbrowser
from threading import Thread

# Функція для спаму синім текстом
def spam_sixseven():
    # Код для синього тексту в консолі
    blue_color = '\033[94m'
    reset_color = '\033[0m'
    
    try:
        while True:
            print(f"{blue_color}SixSeven{reset_color}")
            time.sleep(0.1)  # Невелика затримка, щоб не перевантажувати процесор
    except KeyboardInterrupt:
        pass

# Функція для відкриття 10 вкладок з фото
def open_photo_tabs():
    # Твоє фото за посиланням (заміни на своє фото)
    photo_url = "https://freeimage.host/i/qMYpslS
    
    # Відкриваємо 10 вкладок
    for i in range(15):
        webbrowser.open_new_tab(photo_url)
        time.sleep(0.5)  # Невелика затримка між відкриттям вкладок

# Головна функція
def main():
    # Очищаємо консоль
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("=" * 50)
    print("ТЕСТ З МАТЕМАТИКИ")
    print("=" * 50)
    print("\nРозв'яжи приклад:")
    print("30 + 37 = ?")
    print("\n" + "=" * 50)
    
    while True:
        try:
            answer = input("\nТвоя відповідь: ").strip()
            
            if answer == "67":
                print("\n" + "!" * 50)
                print("ПРАВИЛЬНО! ЗАПУСКАЮ...")
                print("!" * 50 + "\n")
                
                # Розгортаємо консоль на весь екран (для Windows)
                if os.name == 'nt':
                    os.system('mode con cols=200 lines=1000')
                    os.system('color 17')  # Синій фон, білий текст
                
                # Запускаємо спам синім текстом в окремому потоці
                spam_thread = Thread(target=spam_sixseven, daemon=True)
                spam_thread.start()
                
                # Відкриваємо вкладки з фото
                print("Відкриваю 10 вкладок з фото...")
                open_photo_tabs()
                
                # Продовжуємо спам
                spam_thread.join()
                
            else:
                print("\n❌ Неправильно! Спробуй ще раз.\n")
                
        except KeyboardInterrupt:
            print("\n\nДо побачення!")
            sys.exit(0)
        except Exception as e:
            print(f"\nПомилка: {e}\n")

if __name__ == "__main__":
    main()