import os
import win32api
import win32print
from tkinter import Tk, filedialog, Button, Listbox, END, Label

class BatchPrinter:
    def __init__(self, root):
        self.root = root
        self.root.title("Toplu Yazdırma Programı")

        self.label = Label(root, text="Klasör seç ve yazdır")
        self.label.pack()

        self.listbox = Listbox(root, width=80, height=20)
        self.listbox.pack()

        self.select_button = Button(root, text="Klasör Seç", command=self.select_folder)
        self.select_button.pack()

        self.print_button = Button(root, text="Yazdır", command=self.print_files)
        self.print_button.pack()

        self.files = []

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.files.clear()
            self.listbox.delete(0, END)

            for file in os.listdir(folder):
                if file.lower().endswith(('.pdf', '.docx', '.txt')):
                    full_path = os.path.join(folder, file)
                    self.files.append(full_path)
                    self.listbox.insert(END, file)

    def print_files(self):
        printer_name = win32print.GetDefaultPrinter()

        for file in self.files:
            try:
                print(f"Yazdırılıyor: {file}")
                win32api.ShellExecute(
                    0,
                    "print",
                    file,
                    None,
                    ".",
                    0
                )
            except Exception as e:
                print(f"Hata: {file} -> {e}")

        print("Tüm işlemler tamamlandı.")

if __name__ == "__main__":
    root = Tk()
    app = BatchPrinter(root)
    root.mainloop()
