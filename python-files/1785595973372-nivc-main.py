import json
import os
import shutil
import winsound

# Настройка путей
SAVE_DIR = "Saves"
FILE_NAME = "shopping.json"
FULL_PATH = os.path.join(SAVE_DIR, FILE_NAME)
SOUNDS_DIR = "Sounds"

def play_sound():
    """Воспроизводит один общий звук."""
    path = os.path.join(SOUNDS_DIR, "action.wav")
    
    if os.path.exists(path):
        # SND_ASYNC играет звук в фоне, не останавливая программу
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    else:
        # Если файла нет — просто ничего не делаем, программа не сломается
        pass

def ensure_save_dir():
    """Создаёт папку Saves, если её не существует."""
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

def load_shopping_list():
    """Загружает список покупок из JSON-файла в папке Saves."""
    ensure_save_dir()
    
    try:
        with open(FULL_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print("Файл не найден. Создадим пустой список.")
        return []
    except json.JSONDecodeError:
        print("Ошибка в формате JSON. Создадим пустой список.")
        return []

def save_shopping_list(shopping_list):
    """Сохраняет список покупок в JSON-файл внутри папки Saves."""
    ensure_save_dir()
    
    with open(FULL_PATH, "w", encoding="utf-8") as file:
        json.dump(shopping_list, file, ensure_ascii=False, indent=2)
    print("Изменения сохранены в файл.")
    play_sound()  # Один общий звук

def show_shopping_list(shopping_list):
    """Выводит список покупок на экран."""
    if not shopping_list:
        print("Список покупок пуст.")
        return
    
    print("\nСписок покупок:")
    for i, item in enumerate(shopping_list, start=1):
        name = item.get("name", "Без названия")
        quantity = item.get("quantity", 0)
        print(f"{i}. {name} — {quantity} шт.")
    print()
    play_sound()  # Один общий звук

def add_product(shopping_list):
    """Добавляет новый продукт в список через ввод пользователя."""
    name = input("Введите название продукта: ").strip()
    if not name:
        print("Название не может быть пустым.")
        return
    
    while True:
        quantity_str = input("Введите количество: ").strip()
        if quantity_str.isdigit():
            quantity = int(quantity_str)
            break
        else:
            print("Пожалуйста, введите целое число.")
    
    new_item = {"name": name, "quantity": quantity}
    shopping_list.append(new_item)
    print(f"Продукт '{name}' добавлен в список.\n")
    play_sound()  # Один общий звук

def clear_shopping_list(shopping_list):
    """Очищает список и удаляет папку Saves вместе с файлом."""
    confirm = input("Вы уверены, что хотите удалить весь список и папку Saves? (да/нет): ").strip().lower()
    
    if confirm == "да":
        shopping_list.clear()
        
        if os.path.exists(SAVE_DIR):
            try:
                shutil.rmtree(SAVE_DIR)
                print("Весь список покупок удалён, папка Saves и файл удалены.")
                play_sound()  # Тот же самый звук
            except OSError as e:
                print(f"Не удалось удалить папку: {e}")
        else:
            print("Список очищен, папки Saves не существовало.")
    else:
        print("Удаление отменено.")
        play_sound()  # Даже при отмене звучит тот же звук

def main():
    shopping_list = load_shopping_list()
    
    while True:
        print("Меню:")
        print("1. Показать список покупок")
        print("2. Добавить продукт")
        print("3. Сохранить и выйти")
        print("4. Удалить весь список и папку Saves")
        
        choice = input("Выберите действие (1/2/3/4): ").strip()
        
        if choice == "1":
            show_shopping_list(shopping_list)
        elif choice == "2":
            add_product(shopping_list)
        elif choice == "3":
            save_shopping_list(shopping_list)
            print("Программа завершена.")
            break
        elif choice == "4":
            clear_shopping_list(shopping_list)
        else:
            print("Неверный выбор. Попробуйте снова.\n")
            # Можно добавить звук и сюда, если хочешь
            # play_sound()

if __name__ == "__main__":
    main()
