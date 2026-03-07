import os
import shutil
import tempfile

# Список папок для очистки
folders = [
    tempfile.gettempdir(),      # %temp%
    r"C:\Windows\Temp"           # Windows Temp
]

def clear_folder(path):
    if not os.path.exists(path):
        return

    print(f"Очистка: {path}")

    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)

        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)

            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

        except Exception as e:
            print(f"Ошибка удаления {file_path}: {e}")

for folder in folders:
    clear_folder(folder)

print("Очистка завершена!") 