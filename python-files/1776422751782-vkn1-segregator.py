import os
import shutil
import sys

# folder gdzie leży EXE
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))

# folder PDF (obok programu)
SOURCE_DIR = os.path.join(BASE_DIR, "PDFy")

def extract_surname(filename):
    name = os.path.splitext(filename)[0]
    parts = name.split("_")
    return parts[0] if parts else "INNE"

def organize_pdfs():
    if not os.path.exists(SOURCE_DIR):
        print("Brak folderu PDFy!")
        return

    for file in os.listdir(SOURCE_DIR):
        if file.lower().endswith(".pdf"):
            surname = extract_surname(file)

            target_folder = os.path.join(SOURCE_DIR, surname)
            os.makedirs(target_folder, exist_ok=True)

            src = os.path.join(SOURCE_DIR, file)
            dst = os.path.join(target_folder, file)

            shutil.move(src, dst)
            print(f"Przeniesiono: {file} -> {surname}/")

if __name__ == "__main__":
    organize_pdfs()