import os
import zipfile
import tarfile
import rarfile
from tkinter import Tk, filedialog, Button, Label, messagebox, StringVar
from tqdm import tqdm

def is_target_file(filename):
    """Проверяет, соответствует ли файл критериям поиска."""
    prefixes = ['GRETRO', 'PRETRO']
    suffixes = ['.prj', '.tiff', '.tiff.aux.xml', '.tiff.ovr', '.xml']
    return any(filename.startswith(prefix) for prefix in prefixes) and \
           any(filename.endswith(suffix) for suffix in suffixes)

def extract_target_files(archive_path, output_base_dir):
    """Извлекает целевые файлы из архива с сохранением структуры."""
    archive_name = os.path.splitext(os.path.basename(archive_path))[0]
    output_dir = os.path.join(output_base_dir, archive_name)

    if os.path.exists(output_dir):
        print(f"Папка {output_dir} уже существует, пропускаем архив.")
        return

    os.makedirs(output_dir, exist_ok=True)

    try:
        if archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as archive:
                file_list = archive.namelist()
                for file_info in tqdm(file_list, desc=f"Обработка {archive_name}"):
                    if is_target_file(file_info):
                        archive.extract(file_info, output_dir)
        elif archive_path.endswith(('.tar', '.tar.gz', '.tgz')):
            mode = 'r:gz' if archive_path.endswith(('.tar.gz', '.tgz')) else 'r:'
            with tarfile.open(archive_path, mode) as archive:
                for member in tqdm(archive.getmembers(), desc=f"Обработка {archive_name}"):
                    if member.isfile() and is_target_file(member.name):
                        archive.extract(member, output_dir)
        elif archive_path.endswith('.rar'):
            with rarfile.RarFile(archive_path) as archive:
                for file_info in tqdm(archive.infolist(), desc=f"Обработка {archive_name}"):
                    if is_target_file(file_info.filename):
                        archive.extract(file_info.filename, output_dir)
    except Exception as e:
        print(f"Ошибка при обработке архива {archive_path}: {e}")

def process_archives(input_dir, output_dir):
    """Обрабатывает все архивы в указанной папке."""
    supported_extensions = ('.zip', '.tar', '.tar.gz', '.tgz', '.rar')
    archives = [f for f in os.listdir(input_dir) if f.endswith(supported_extensions)]

    if not archives:
        messagebox.showwarning("Предупреждение", "В выбранной папке нет поддерживаемых архивов.")
        return

    for archive in archives:
        archive_path = os.path.join(input_dir, archive)
        extract_target_files(archive_path, output_dir)

def select_input_folder():
    folder = filedialog.askdirectory(title="Выберите папку с архивами")
    input_folder_var.set(folder)

def select_output_folder():
    folder = filedialog.askdirectory(title="Выберите папку для извлечения")
    output_folder_var.set(folder)

def start_processing():
    input_dir = input_folder_var.get()
    output_dir = output_folder_var.get()

    if not input_dir or not output_dir:
        messagebox.showerror("Ошибка", "Пожалуйста, выберите обе папки.")
        return

    process_archives(input_dir, output_dir)
    messagebox.showinfo("Готово", "Обработка завершена!")

# Создание интерфейса
root = Tk()
root.title("Распаковщик архивов")
root.geometry("500x200")

input_folder_var = StringVar()
output_folder_var = StringVar()

Label(root, text="Папка с архивами:").pack(pady=5)
Button(root, textvariable=input_folder_var, command=select_input_folder, width=50).pack(pady=5)

Label(root, text="Папка для извлечения:").pack(pady=5)
Button(root, textvariable=output_folder_var, command=select_output_folder, width=50).pack(pady=5)

Button(root, text="Начать обработку", command=start_processing, bg="green", fg="white").pack(pady=20)

root.mainloop()
