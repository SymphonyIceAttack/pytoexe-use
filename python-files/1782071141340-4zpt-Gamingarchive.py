import os
import shutil


file_extensions = {
    ".txt": "Текстовая конфигурация",
    ".docx": "Текстовая информация",
    ".pdf": "Информация в PDF",
    ".jpg": "Картнки JPG",
    ".png": "Картинки PNG",
    ".mp3": "Музыка",
    ".mp4": "Видео"
}

folder_to_optimize = input("Enter the path to the folder to be optimized: ")


def create_folders():
    for folder_name in file_extensions.values():
        folder_path = os.path.join(folder_to_optimize, folder_name)
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)


def optimize():
    for file_name in os.listdir(folder_to_optimize):
        file_path = os.path.join(folder_to_optimize, file_name)
        if not os.path.isfile(file_path):
            continue
        file_extension = os.path.splitext(file_name)[1]
        if file_extension not in file_extensions:
            print("unknown extension ", file_extension)
            continue
        folder_name = file_extensions[file_extension]
        folder_path = os.path.join(folder_to_optimize, folder_name)
        shutil.move(file_path, folder_path)


create_folders()
optimize()

