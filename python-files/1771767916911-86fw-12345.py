import os
import shutil

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

# Проверка пути, чтобы не выйти за ROOT_DIR
def safe_path(path):
    abs_path = os.path.abspath(os.path.join(ROOT_DIR, path))
    if not abs_path.startswith(ROOT_DIR):
        raise Exception("Доступ за пределы корневой папки запрещён!")
    return abs_path

# Файловые команды
def list_files(path="."):
    try:
        abs_path = safe_path(path)
        return "\n".join(os.listdir(abs_path)) or "Папка пуста"
    except Exception as e:
        return f"Ошибка: {e}"

def create_folder(path):
    try:
        abs_path = safe_path(path)
        os.makedirs(abs_path, exist_ok=True)
        return f"Папка '{path}' создана"
    except Exception as e:
        return f"Ошибка: {e}"

def delete_path(path):
    try:
        abs_path = safe_path(path)
        if os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
            return f"Папка '{path}' удалена"
        elif os.path.isfile(abs_path):
            os.remove(abs_path)
            return f"Файл '{path}' удалён"
        else:
            return "Файл или папка не найдены"
    except Exception as e:
        return f"Ошибка: {e}"

# Мини-логика "ChatGPT-стиля"
def agent_response(user_message):
    msg = user_message.lower()
    if "покажи файлы" in msg or "list" in msg:
        return "list ."
    elif "создай папку" in msg or "mkdir" in msg:
        folder = user_message.split()[-1]
        return f"mkdir {folder}"
    elif "удали" in msg or "delete" in msg:
        target = user_message.split()[-1]
        return f"delete {target}"
    else:
        return "Неизвестная команда"

# Основной цикл агента
def main():
    print(f"=== Локальный агент работает в папке {ROOT_DIR} ===")
    print("Доступные команды: 'покажи файлы', 'создай папку <имя>', 'удали <имя>', 'выход'")
    while True:
        user_input = input("Ты: ")
        if user_input.lower() in ["выход", "exit"]:
            break

        command = agent_response(user_input)
        print("Агент предлагает команду:", command)

        # Выполнение команды
        if command.startswith("list"):
            print(list_files(command[5:]))
        elif command.startswith("mkdir"):
            print(create_folder(command[6:]))
        elif command.startswith("delete"):
            print(delete_path(command[7:]))
        else:
            print(command)

if __name__ == "__main__":
    main()