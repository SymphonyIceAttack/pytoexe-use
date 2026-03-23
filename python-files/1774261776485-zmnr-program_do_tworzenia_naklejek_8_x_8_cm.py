import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont

# Stałe
DPI = 300
CM_TO_INCH = 0.393701
SIZE_CM = 8
SIZE_PX = int(SIZE_CM * CM_TO_INCH * DPI)

class StickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Generator naklejek 8x8 cm")

        tk.Label(root, text="Wpisz tekst (np. wymiary opakowania):").pack()
        self.text_entry = tk.Entry(root, width=40)
        self.text_entry.pack(pady=5)

        tk.Button(root, text="Generuj naklejkę", command=self.generate_sticker).pack(pady=10)

    def generate_sticker(self):
        text = self.text_entry.get()
        if not text:
            return

        # Tworzenie obrazu
        img = Image.new('RGB', (SIZE_PX, SIZE_PX), 'white')
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 80)
        except:
            font = ImageFont.load_default()

        # Wyśrodkowanie tekstu
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        position = ((SIZE_PX - text_width) // 2, (SIZE_PX - text_height) // 2)
        draw.text(position, text, fill="black", font=font)

        # Zapis pliku
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png")])
        if file_path:
            img.save(file_path, dpi=(DPI, DPI))

if __name__ == "__main__":
    root = tk.Tk()
    app = StickerApp(root)
    root.mainloop()
