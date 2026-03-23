import tkinter as tk
from tkinter import filedialog

# Stałe dla rozmiaru naklejki 8x8 cm w pikselach
CM_TO_PX = 37.8  # przybliżone, do wyświetlania na ekranie
SIZE_CM = 8
SIZE_PX = int(SIZE_CM * CM_TO_PX)

class StickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Naklejki 8x8 cm")

        tk.Label(root, text="Wpisz tekst (np. wymiary opakowania):").pack(pady=5)
        self.entry = tk.Entry(root, width=30)
        self.entry.pack(pady=5)

        tk.Button(root, text="Zapisz naklejkę", command=self.save_sticker).pack(pady=10)

    def save_sticker(self):
        text = self.entry.get()
        if not text:
            return

        canvas = tk.Canvas(self.root, width=SIZE_PX, height=SIZE_PX, bg="white")
        canvas.create_text(SIZE_PX//2, SIZE_PX//2, text=text, font=("Arial", 40), fill="black")

        file_path = filedialog.asksaveasfilename(defaultextension=".ps", filetypes=[("PostScript", "*.ps")])
        if file_path:
            canvas.postscript(file=file_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = StickerApp(root)
    root.mainloop()