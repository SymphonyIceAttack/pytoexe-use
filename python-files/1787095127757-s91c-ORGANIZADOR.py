import os
import shutil
import sys

def get_downloads_folder():
    """Devuelve la ruta de la carpeta Descargas del usuario en Windows."""
    home = os.path.expanduser("~")
    return os.path.join(home, "Downloads")

def organize_by_extension_and_letter(folder_path):
    """
    Organiza los archivos de 'folder_path':
      - Carpeta por extensión (minúscula).
      - Subcarpeta por primera letra del nombre base (A-Z, Numeros, Otros).
    """
    if not os.path.exists(folder_path):
        print(f"La carpeta {folder_path} no existe.")
        return

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            base, ext = os.path.splitext(item)
            ext = ext[1:] if ext else "sin_extension"
            ext_folder = os.path.join(folder_path, ext.lower())

            # Primera letra del nombre base (sin extensión)
            if base:
                first_char = base[0].upper()
            else:
                first_char = item[0].upper() if item else "?"

            if first_char.isalpha():
                letter_folder = first_char
            elif first_char.isdigit():
                letter_folder = "Numeros"
            else:
                letter_folder = "Otros"

            dest_folder = os.path.join(ext_folder, letter_folder)
            os.makedirs(dest_folder, exist_ok=True)

            dest_path = os.path.join(dest_folder, item)
            if os.path.exists(dest_path):
                base_name, ext_name = os.path.splitext(item)
                counter = 1
                while os.path.exists(os.path.join(dest_folder, f"{base_name}_{counter}{ext_name}")):
                    counter += 1
                dest_path = os.path.join(dest_folder, f"{base_name}_{counter}{ext_name}")

            shutil.move(item_path, dest_path)
            print(f"Movido: {item} -> {dest_folder}")

if __name__ == "__main__":
    # Si se pasa un argumento, usa esa ruta; si no, usa Descargas
    target = sys.argv[1] if len(sys.argv) > 1 else get_downloads_folder()
    print(f"Organizando: {target}")
    organize_by_extension_and_letter(target)
    print("¡Organización completada!")