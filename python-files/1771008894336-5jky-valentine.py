import tkinter as tk
import random
import math

class ValentineApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("💕 Will u be my valentine? 💕")
        self.root.geometry("700x600")
        self.root.configure(bg='#ff9a9e')
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(self.root, width=700, height=600, bg='#ff9a9e', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Счётчики
        self.no_shrinks = 0
        self.max_resize = 10
        self.celebration_shown = False

        # Позиция кнопки Нет
        self.no_x, self.no_y = 350, 380
        self.no_moving = False

        self.setup_ui()
        self.flying_hearts()
        self.animate()

    def setup_ui(self):
        # Главная надпись
        self.title = self.canvas.create_text(350, 120, text="Will u be", 
                                           font=('Segoe UI Emoji', 36, 'bold'), fill='#e91e63')
        self.subtitle = self.canvas.create_text(350, 170, text="my valentine?", 
                                              font=('Segoe UI Emoji', 38, 'bold'), fill='#ad1457')
        
        # Сердечки вокруг надписи (ФОНОВЫЕ)
        self.decor_hearts = []
        for i in range(8):
            angle = i * 45
            x = 350 + 120 * math.cos(math.radians(angle))
            y = 150 + 40 * math.sin(math.radians(angle))
            heart = self.canvas.create_text(x, y, text="💖", font=('Segoe UI Emoji', 24), fill='#ff4081')
            self.decor_hearts.append(heart)

        # 🔥 КНОПКА НЕТ
        self.no_btn = self.canvas.create_rectangle(self.no_x-70, self.no_y-35, self.no_x+70, self.no_y+35, 
                                                 fill='#f44336', outline='#d32f2f', width=4, tags='no_button')
        self.no_glow = self.canvas.create_rectangle(self.no_x-75, self.no_y-40, self.no_x+75, self.no_y+40, 
                                                  fill='#ff5722', outline='', stipple='gray50', tags='no_button')
        self.no_text = self.canvas.create_text(self.no_x, self.no_y, text="💔 НЕТ 💔", 
                                             font=('Segoe UI Emoji', 18, 'bold'), fill='white', tags='no_button')
        
        # ✅ КНОПКА ДА
        self.yes_shadow = self.canvas.create_rectangle(220, 330, 340, 400, fill='#4caf50', outline='', tags='yes_button')
        self.yes_btn = self.canvas.create_rectangle(210, 320, 330, 390, fill='#8bc34a', 
                                                  outline='#4caf50', width=4, tags='yes_button')
        self.yes_gradient = self.canvas.create_rectangle(215, 325, 335, 395, fill='#c8e6c9', outline='', tags='yes_button')
        self.yes_text = self.canvas.create_text(270, 355, text="💚 ДА 💚", 
                                              font=('Segoe UI Emoji', 20, 'bold'), fill='white', tags='yes_button')

        # Привязка событий ПО ТЕГАМ
        self.canvas.tag_bind('yes_button', '<Button-1>', self.on_yes)
        self.canvas.tag_bind('no_button', '<Button-1>', self.on_no)
        self.canvas.tag_bind('no_button', '<Enter>', self.on_no_enter)

        # Кнопки НАД всем
        self.canvas.tag_raise('yes_button')
        self.canvas.tag_raise('no_button')

    def on_no_enter(self, event):
        self.no_moving = True

    def on_no(self, event):
        self.no_shrinks += 1
        if self.no_shrinks <= self.max_resize:
            scale_no = 0.88 ** self.no_shrinks
            scale_yes = 1.12 ** self.no_shrinks
            
            # Обновляем позицию кнопки Нет
            self.canvas.coords(self.no_btn, self.no_x-70*scale_no, self.no_y-35*scale_no, 
                             self.no_x+70*scale_no, self.no_y+35*scale_no)
            self.canvas.coords(self.no_glow, self.no_x-75*scale_no, self.no_y-40*scale_no, 
                             self.no_x+75*scale_no, self.no_y+40*scale_no)
            self.canvas.coords(self.no_text, self.no_x, self.no_y)
            
            # Масштабируем Да
            self.canvas.scale('yes_button', 270, 355, scale_yes, scale_yes)

        self.no_moving = False
        self.canvas.tag_raise('no_button')

    def on_yes(self, event):
        if not self.celebration_shown:
            self.celebration_shown = True
            self.show_celebration()

    def show_celebration(self):
        """🎉 НАДПИСИ В ЦЕНТРЕ ЭКРАНА (опущены ниже!)"""
        self.canvas.delete('all')
        
        # Градиентный фон
        for i in range(0, 700, 50):
            self.canvas.create_rectangle(i, 0, i+30, 600, fill=f'#f8bbd9', outline='')
        
        # ✅ НАДПИСИ ПЕРЕМЕЩЕНЫ В ЦЕНТР (Y=220, 280, 330, 520)
        self.canvas.create_text(350, 220, text="💖 Е ЮХУ УРА! 💖", font=('Segoe UI Emoji', 48, 'bold'), fill='#ff1744')
        self.canvas.create_text(350, 280, text="Я теперь оч счастиливи!", 
                              font=('Segoe UI Emoji', 26, 'bold'), fill='#e91e63')
        self.canvas.create_text(350, 330, text="💕 Будешь моим мабоем forever? 💕", 
                              font=('Segoe UI Emoji', 24), fill='#ad1457')
        self.canvas.create_text(350, 520, text="14 февраля 2026 © YOUR KIRIL 💝", 
                              font=('Segoe UI Emoji', 14), fill='#757575')
        
        self.celebration_loop()

    def celebration_loop(self):
        for _ in range(30):
            self.launch_magic_heart()
            if random.random() > 0.3:
                self.launch_rainbow_star()
        self.root.after(1500, self.celebration_loop)

    def launch_magic_heart(self):
        x, y = random.randint(0, 700), random.randint(0, 600)
        sizes = [28, 32, 36, 42]
        heart = self.canvas.create_text(x, y, text=random.choice(['💖', '💕', '💗', '💝']), 
                                      font=('Segoe UI Emoji', random.choice(sizes)), 
                                      fill=random.choice(['#ff4081', '#f06292', '#ec407a']))
        vx, vy = random.uniform(-8, 8), random.uniform(-20, -4)
        self.animate_particle(heart, vx, vy, sparkle=True)

    def launch_rainbow_star(self):
        x, y = random.randint(0, 700), random.randint(0, 600)
        colors = ['#ffd700', '#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#f0932b']
        star = self.canvas.create_text(x, y, text="✨", font=('Segoe UI Emoji', 28), fill=random.choice(colors))
        vx, vy = random.uniform(-12, 12), random.uniform(-25, -5)
        self.animate_particle(star, vx, vy)

    def animate_particle(self, item, vx, vy, sparkle=False):
        def step():
            self.canvas.move(item, vx, vy)
            coords = self.canvas.coords(item)
            if coords[1] > 620:
                self.canvas.delete(item)
            else:
                if sparkle and random.random() < 0.1:
                    self.canvas.itemconfig(item, font=('Segoe UI Emoji', 20))
                self.root.after(25, step)
        step()

    def flying_hearts(self):
        for _ in range(25):
            self.root.after(random.randint(300, 2500), lambda: self.launch_magic_heart())

    def animate(self):
        if self.no_moving:
            mx = self.root.winfo_pointerx() - self.root.winfo_rootx()
            my = self.root.winfo_pointery() - self.root.winfo_rooty()
            
            dx = self.no_x - mx
            dy = self.no_y - my
            dist = math.hypot(dx, dy)
            
            if dist < 130:
                speed = 2.5
                self.no_x += (dx / dist) * speed if dist > 0 else 0
                self.no_y += (dy / dist) * speed if dist > 0 else 0
                
                self.no_x = max(100, min(600, self.no_x))
                self.no_y = max(80, min(480, self.no_y))
                
                scale = 0.95 ** self.no_shrinks if self.no_shrinks > 0 else 1
                self.canvas.coords(self.no_btn, self.no_x-70*scale, self.no_y-35*scale, 
                                 self.no_x+70*scale, self.no_y+35*scale)
                self.canvas.coords(self.no_glow, self.no_x-75*scale, self.no_y-40*scale, 
                                 self.no_x+75*scale, self.no_y+40*scale)
                self.canvas.coords(self.no_text, self.no_x, self.no_y)
                self.canvas.tag_raise('no_button')
        
        self.root.after(25, self.animate)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ValentineApp()
    app.run()
