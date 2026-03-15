import tkinter as tk
import random

class GoldRushFullScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Gold Rush: Fullscreen")
        
        # Tam ekran ayarları
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self.root.destroy()) # ESC ile çıkış
        
        # Ekran boyutlarını al
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        
        self.canvas = tk.Canvas(self.root, width=self.screen_w, height=self.screen_h, bg="#1e272e", highlightthickness=0)
        self.canvas.pack()

        # Oyuncu ve Değişkenler
        # Sepeti ekranın altına yerleştir
        self.basket_w = 100
        self.basket = self.canvas.create_rectangle(self.screen_w//2 - 50, self.screen_h - 100, 
                                                 self.screen_w//2 + 50, self.screen_h - 80, 
                                                 fill="#f1c40f", outline="white", width=2)
        self.score = 0
        self.lives = 3
        self.speed = 7
        self.items = []
        self.boss_active = False

        # Arayüz
        self.txt_score = self.canvas.create_text(100, 50, text=f"Score: {self.score}", fill="gold", font=("Arial", 20, "bold"))
        self.txt_lives = self.canvas.create_text(self.screen_w - 100, 50, text=f"Lives: {self.lives}", fill="#ff4757", font=("Arial", 20, "bold"))
        self.canvas.create_text(self.screen_w//2, 30, text="ESC to Exit", fill="#57606f", font=("Arial", 10))
        
        self.root.bind("<Left>", lambda e: self.move(-60))
        self.root.bind("<Right>", lambda e: self.move(60))
        
        self.spawn_loop()
        self.update_loop()
        self.root.mainloop()

    def move(self, dx):
        c = self.canvas.coords(self.basket)
        if c[0] + dx >= 0 and c[2] + dx <= self.screen_w:
            self.canvas.move(self.basket, dx, 0)

    def spawn_boss(self):
        self.boss_active = True
        x = random.randint(100, self.screen_w - 300)
        boss = self.canvas.create_oval(x, -250, x+250, 0, fill="#2f3542", outline="#ff4757", width=5)
        self.items.append([boss, "boss"])

    def spawn_loop(self):
        if self.lives <= 0: return
        
        if self.score > 0 and self.score % 10 == 0 and not self.boss_active:
            self.spawn_boss()
        
        if not self.boss_active:
            x = random.randint(50, self.screen_w - 50)
            if random.random() < 0.25:
                obj = self.canvas.create_oval(x, 0, x+30, 30, fill="black", outline="red", width=2)
                self.items.append([obj, "bomb"])
            else:
                obj = self.canvas.create_oval(x, 0, x+25, 25, fill="#f1c40f", outline="white")
                self.items.append([obj, "gold"])
        
        self.root.after(700, self.spawn_loop)

    def update_loop(self):
        if self.lives <= 0: return

        for item_data in self.items[:]:
            obj, kind = item_data
            current_speed = self.speed if kind != "boss" else self.speed + 4
            self.canvas.move(obj, 0, current_speed)
            
            pos = self.canvas.coords(obj)
            b_pos = self.canvas.coords(self.basket)

            if (pos[2] >= b_pos[0] and pos[0] <= b_pos[2] and pos[3] >= b_pos[1] and pos[1] <= b_pos[3]):
                if kind == "gold":
                    self.score += 1
                    self.speed += 0.2
                elif kind == "bomb":
                    self.lives -= 1
                elif kind == "boss":
                    self.lives = 0
                
                self.refresh_ui()
                self.remove_item(item_data)
                if kind == "boss": self.boss_active = False
            
            elif pos[1] > self.screen_h:
                if kind == "gold": self.lives -= 1
                if kind == "boss": self.boss_active = False
                self.refresh_ui()
                self.remove_item(item_data)

        self.root.after(20, self.update_loop) if self.lives > 0 else self.game_over()

    def remove_item(self, item_data):
        self.canvas.delete(item_data[0])
        if item_data in self.items: self.items.remove(item_data)

    def refresh_ui(self):
        self.canvas.itemconfig(self.txt_score, text=f"Score: {self.score}")
        self.canvas.itemconfig(self.txt_lives, text=f"Lives: {self.lives}")

    def game_over(self):
        self.canvas.create_rectangle(0, 0, self.screen_w, self.screen_h, fill="black", stipple="gray50")
        self.canvas.create_text(self.screen_w//2, self.screen_h//2 - 50, text="GAME OVER", fill="red", font=("Arial", 60, "bold"))
        self.canvas.create_text(self.screen_w//2, self.screen_h//2 + 50, text=f"Final Score: {self.score}", fill="white", font=("Arial", 30))
        self.canvas.create_text(self.screen_w//2, self.screen_h//2 + 120, text="Press ESC to Close", fill="#57606f", font=("Arial", 15))

GoldRushFullScreen()
