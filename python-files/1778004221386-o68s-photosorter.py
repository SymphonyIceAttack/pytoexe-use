import os
import shutil
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

class PhotoSorterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Sorter")

        # UI elements
        self.canvas = tk.Canvas(root, width=800, height=600, bg="black")
        self.canvas.pack()

        # Buttons
        tk.Button(root, text="Select Source Folder", command=self.load_folder).pack()
        tk.Button(root, text="Set Left Folder", command=lambda: self.set_folder("Left")).pack()
        tk.Button(root, text="Set Right Folder", command=lambda: self.set_folder("Right")).pack()

        # State
        self.source_folder = None
        self.dest_folders = {"Left": None, "Right": None}
        self.photos = []
        self.index = 0
        self.current_image = None

        # Key bindings
        root.bind("<Left>", lambda e: self.move_photo("Left"))
        root.bind("<Right>", lambda e: self.move_photo("Right"))

    def load_folder(self):
        folder = filedialog.askdirectory(title="Select Source Folder")
        if folder:
            self.source_folder = folder
            self.photos = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
            self.index = 0
            self.show_photo()

    def set_folder(self, key):
        folder = filedialog.askdirectory(title=f"Select {key} Destination Folder")
        if folder:
            self.dest_folders[key] = folder

    def show_photo(self):
        if self.index < len(self.photos):
            path = os.path.join(self.source_folder, self.photos[self.index])
            img = Image.open(path)
            img.thumbnail((800, 600))
            self.current_image = ImageTk.PhotoImage(img)
            self.canvas.create_image(400, 300, image=self.current_image)
        else:
            self.canvas.delete("all")
            self.canvas.create_text(400, 300, text="All photos sorted!", fill="white", font=("Arial", 24))

    def move_photo(self, key):
        if self.index < len(self.photos) and self.dest_folders[key]:
            filename = self.photos[self.index]
            src = os.path.join(self.source_folder, filename)
            dst = os.path.join(self.dest_folders[key], filename)
            shutil.move(src, dst)
            self.index += 1
            self.show_photo()

if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoSorterApp(root)
    root.mainloop()
