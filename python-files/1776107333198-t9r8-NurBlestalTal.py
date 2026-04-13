import tkinter as tk
import threading
import time
import ctypes

class CheatMenu:
    def init(self):
        self.menu_visible = False
        self.root = None
        print("✅ NurBlestalTal запущен! Нажми ПРАВЫЙ SHIFT для открытия меню")
        self.check_key_loop()
    
    def check_key_loop(self):
        """Проверяет нажатие правого Shift (VK_RSHIFT = 0xA1)"""
        user32 = ctypes.windll.user32
        
        while True:
            # 0xA1 = правый Shift
            if user32.GetAsyncKeyState(0xA1) & 0x8000:
                self.toggle_menu()
                time.sleep(0.3)  # защита от повторного срабатывания
            time.sleep(0.05)
    
    def toggle_menu(self):
        if self.menu_visible:
            self.close_menu()
        else:
            self.open_menu()
    
    def open_menu(self):
        if self.root is not None:
            try:
                self.root.destroy()
            except:
                pass
        
        self.root = tk.Tk()
        self.root.title("NurBlestalTal - Меню")
        self.root.geometry("400x500")
        self.root.configure(bg='#0a0a1a')
        
        # Чтобы окно было поверх всех окон
        self.root.attributes('-topmost', True)
        
        # Красивый заголовок
        tk.Label(self.root, text="⚡ NurBlestalTal ⚡", 
                font=('Arial', 20, 'bold'), 
                bg='#0a0a1a', fg='#ff4444').pack(pady=15)
        
        tk.Label(self.root, text="BY: łøwłighŧ", 
                font=('Arial', 10, 'italic'),
                bg='#0a0a1a', fg='#888888').pack()
        
        tk.Label(self.root, text="\n=== ВЫБЕРИ ФУНКЦИЮ ===\n", 
                bg='#0a0a1a', fg='#88aaff').pack()
        
        # Кнопки функций
        btn_frame = tk.Frame(self.root, bg='#0a0a1a')
        btn_frame.pack(pady=10)
        
        def toggle_killaura():
            print("⚔️ Killaura переключен")
        
        def toggle_esp():
            print("👁️ ESP переключен")
        
        def toggle_fly():
            print("🕊️ Fly переключен")
        
        def toggle_speed():
            print("⚡ Speed переключен")
        
        tk.Button(btn_frame, text="⚔️ Killaura", command=toggle_killaura,
                 bg='#aa3333', fg='white', width=25, height=2, font=('Arial', 11)).pack(pady=5)
        
        tk.Button(btn_frame, text="👁️ ESP / X-Ray", command=toggle_esp,
                 bg='#33aa33', fg='white', width=25, height=2, font=('Arial', 11)).pack(pady=5)
        
        tk.Button(btn_frame, text="🕊️ Fly / NoFall", command=toggle_fly,
                 bg='#3333aa', fg='white', width=25, height=2, font=('Arial', 11)).pack(pady=5)
        
        tk.Button(btn_frame, text="⚡ Speed / Scaffold", command=toggle_speed,
                 bg='#aa8833', fg='white', width=25, height=2, font=('Arial', 11)).pack(pady=5)
        
        # Кнопка закрытия
        tk.Button(btn_frame, text="❌ ЗАКРЫТЬ МЕНЮ", command=self.close_menu,
                 bg='#333333', fg='white', width=25, height=2, font=('Arial', 11)).pack(pady=20)
        
        self.menu_visible = True
        self.root.protocol("WM_DELETE_WINDOW", self.close_menu)
        self.root.mainloop()
    
    def close_menu(self):
        self.menu_visible = False
        if self.root:
            try:
                self.root.destroy()
            except:
                pass
            self.root = None

if name == "main":
    menu = CheatMenu()