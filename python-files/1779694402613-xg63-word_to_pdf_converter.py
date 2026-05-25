import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from docx2pdf import convert


class WordToPDFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Word to PDF Converter")
        self.root.geometry("520x300")
        self.root.resizable(False, False)

        title_label = tk.Label(
            root,
            text="Select one or more Word files",
            font=("Arial", 14)
        )
        title_label.pack(pady=15)

        select_button = tk.Button(
            root,
            text="Select Word Files",
            font=("Arial", 11),
            width=25,
            height=2,
            command=self.select_files
        )
        select_button.pack(pady=10)

        self.log_box = tk.Text(
            root,
            width=62,
            height=10,
            state=tk.DISABLED
        )
        self.log_box.pack(padx=10, pady=10)

    def write_log(self, message):
        self.log_box.config(state=tk.NORMAL)
        self.log_box.insert(tk.END, message + "\\n")
        self.log_box.see(tk.END)
        self.log_box.config(state=tk.DISABLED)

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Choose Word files",
            filetypes=[
                ("Word Files", "*.docx *.doc")
            ]
        )

        if not files:
            return

        thread = threading.Thread(
            target=self.convert_files,
            args=(files,),
            daemon=True
        )
        thread.start()

    def convert_files(self, files):
        success_count = 0

        for file_path in files:
            try:
                filename = os.path.basename(file_path)
                pdf_path = os.path.splitext(file_path)[0] + ".pdf"

                self.write_log(f"Converting: {filename}")

                if os.path.exists(pdf_path):
                    os.remove(pdf_path)

                convert(file_path, pdf_path)

                self.write_log(f"SUCCESS: {os.path.basename(pdf_path)}")
                success_count += 1

            except Exception as e:
                self.write_log(f"ERROR: {filename}")
                self.write_log(str(e))

        messagebox.showinfo(
            "Completed",
            f"Successfully converted {success_count} file(s) to PDF."
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = WordToPDFApp(root)
    root.mainloop()
