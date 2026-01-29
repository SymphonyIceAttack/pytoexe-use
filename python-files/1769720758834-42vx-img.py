import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageOps
import os

# ------------------- FUNCTION -------------------
def process_image():
    file_path = filedialog.askopenfilename(filetypes=[("Image files","*.png;*.jpg;*.jpeg")])
    if not file_path:
        return

    try:
        # Load image
        img = Image.open(file_path).convert("RGBA")
        
        # Fill background with white (simple removal)
        background = Image.new("RGBA", img.size, (255,255,255,255))
        img_clean = Image.alpha_composite(background, img)
        
        # Resize proportionally to fit inside square (short side)
        min_side = min(img_clean.size)
        img_square = ImageOps.contain(img_clean, (min_side, min_side))
        
        # Create final canvas 1630x1080
        final_img = Image.new("RGB", (1630,1080), "white")
        
        # Paste centered
        x = (1630 - img_square.width)//2
        y = (1080 - img_square.height)//2
        final_img.paste(img_square.convert("RGB"), (x, y))
        
        # Save output
        output_file = os.path.join(os.path.dirname(file_path), "processed_image.jpg")
        final_img.save(output_file)
        messagebox.showinfo("Done", f"Image processed and saved as:\n{output_file}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# ------------------- GUI -------------------
root = tk.Tk()
root.title("Image Processor 1630x1080")
root.geometry("450x200")

tk.Label(root, text="Turn any image into 1630x1080 with white background", wraplength=400).pack(pady=20)
tk.Button(root, text="Select Image & Process", command=process_image, width=30, height=2).pack(pady=20)

root.mainloop()
