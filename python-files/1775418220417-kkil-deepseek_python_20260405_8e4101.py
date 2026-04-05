import tkinter as tk
import sys
import os

def demo_blocker():
    root = tk.Tk()
    root.title("ДЕМОНСТРАЦИЯ")
    root.geometry("800x600")
    root.attributes('-fullscreen', True)
    root.configure(bg='black')
    
    def exit_demo():
        root.destroy()
        sys.exit(0)
    
    # Защита от Alt+F4 (только для демонстрации)
    def on_close():
        pass  # Блокируем стандартное закрытие
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    
    btn_exit = tk.Button(root, text="ВЫХОД (ДЕМО-РЕЖИМ)", command=exit_demo, 
                         font=("Arial", 20), bg="red", fg="white")
    btn_exit.pack(pady=50)
    
    label = tk.Label(root, text="WINDOWS ЗАБЛОКИРОВАН by MRVHack!", 
                     font=("Arial", 32, "bold"), fg="red", bg="black")
    label.pack(expand=True)
    
    # Перехват клавиш
    def on_keypress(event):
        if event.keysym == 'Alt_L' or event.keysym == 'F4':
            return "break"
    
    root.bind_all('<Key>', on_keypress)
    
    root.mainloop()

if __name__ == "__main__":
    demo_blocker()