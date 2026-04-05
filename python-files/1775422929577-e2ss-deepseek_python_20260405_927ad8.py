import tkinter as tk
from PIL import Image, ImageTk
import requests
from io import BytesIO
import sys

def demo_blocker():
    root = tk.Tk()
    root.title("")
    root.geometry("800x600")
    root.attributes('-fullscreen', True)
    root.configure(bg='black')
    
    def exit_demo():
        root.destroy()
        sys.exit(0)
    
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    
    # Загрузка картинки с муравьём из интернета
    try:
        url = "https://i.pinimg.com/736x/7f/71/39/7f7139a89573d3e355bfa11382758952.jpg"
        response = requests.get(url, timeout=5)
        img_data = Image.open(BytesIO(response.content))
        img_data = img_data.resize((200, 150), Image.Resampling.LANCZOS)
        ant_image = ImageTk.PhotoImage(img_data)
        image_label = tk.Label(root, image=ant_image, bg='black')
        image_label.pack(pady=10)
    except:
        # Если картинка не загрузилась - текст вместо неё
        image_label = tk.Label(root, text="🐜", font=("Arial", 60), bg='black', fg='white')
        image_label.pack(pady=10)
    
    label = tk.Label(
        root, 
        text="WINDOWS ЗАБЛОКИРОВАН by MRVHack!", 
        font=("Arial", 36, "bold"), 
        fg="red", 
        bg="black"
    )
    label.pack(expand=True)
    
    # Кнопка выхода (маленькая серая)
    btn_exit = tk.Button(
        root, 
        text="выход", 
        command=exit_demo,
        font=("Arial", 8),
        bg="#404040",
        fg="#606060",
        activebackground="#404040",
        activeforeground="#606060",
        relief=tk.FLAT,
        borderwidth=0,
        padx=3,
        pady=1
    )
    btn_exit.place(x=760, y=570, width=30, height=15)
    
    def on_keypress(event):
        if event.keysym in ('Alt_L', 'Alt_R', 'F4', 'Escape'):
            return "break"
    
    root.bind_all('<Key>', on_keypress)
    root.mainloop()

if __name__ == "__main__":
    # Установка Pillow если нет: pip install pillow requests
    demo_blocker()