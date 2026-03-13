import tkinter as tk
import random
import time
import math

# Настройки игры
WIDTH = 1000
HEIGHT = 700
FPS = 60

class ForestGame:
    def __init__(self, root):
        self.root = root
        self.root.title("🏕️ Выживание в лесу - Игра")
        self.root.resizable(False, False)
        
        # Создаем холст
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='#1a3d1a')
        self.canvas.pack()
        
        # Игрок
        self.player_x = WIDTH // 2
        self.player_y = HEIGHT // 2
        self.player_size = 25
        self.player = self.canvas.create_rectangle(
            self.player_x - self.player_size,
            self.player_y - self.player_size,
            self.player_x + self.player_size,
            self.player_y + self.player_size,
            fill='brown', outline='orange', width=3
        )
        
        # Статистика
        self.wood = 0
        self.berries = 0
        self.energy = 100
        self.score = 0
        
        # Счетчики на экране
        self.wood_text = self.canvas.create_text(100, 30, 
            text=f"🪵 Дрова: {self.wood}", fill='white', font=("Arial", 14))
        self.berries_text = self.canvas.create_text(250, 30, 
            text=f"🍓 Ягоды: {self.berries}", fill='white', font=("Arial", 14))
        self.energy_text = self.canvas.create_text(400, 30, 
            text=f"⚡ Энергия: {self.energy}%", fill='white', font=("Arial", 14))
        self.score_text = self.canvas.create_text(800, 30, 
            text=f"🏆 Счет: {self.score}", fill='gold', font=("Arial", 16, "bold"))
        
        # Предметы на карте
        self.items = []
        self.enemies = []
        self.bonuses = []
        
        # Управление
        self.keys = {'w': False, 'a': False, 's': False, 'd': False, 
                    'space': False}
        self.bind_keys()
        
        # Создаем стартовые предметы
        self.spawn_items(10)
        self.spawn_enemies(5)
        self.spawn_bonuses(3)
        
        # Счетчик времени
        self.last_spawn = time.time()
        
        # Запуск игры
        self.game_loop()
    
    def bind_keys(self):
        """Привязка клавиш"""
        self.root.bind('<KeyPress>', self.key_press)
        self.root.bind('<KeyRelease>', self.key_release)
        self.root.bind('<space>', self.space_press)
    
    def key_press(self, event):
        if event.keysym in self.keys:
            self.keys[event.keysym] = True
    
    def key_release(self, event):
        if event.keysym in self.keys:
            self.keys[event.keysym] = False
    
    def space_press(self, event):
        """Пробел - выстрел ягодой"""
        self.shoot_berry()
    
    def shoot_berry(self):
        """Стрельба ягодами во врагов"""
        if self.berries > 0:
            self.berries -= 1
            # Создаем снаряд
            self.items.append({
                'type': 'berry_shot',
                'x': self.player_x,
                'y': self.player_y - 20,
                'dx': 0,
                'dy': -10,
                'id': None
            })
            self.update_stats()
    
    def move_player(self):
        """Движение игрока"""
        speed = 5
        dx, dy = 0, 0
        
        if self.keys['w'] and self.player_y > self.player_size:
            dy -= speed
        if self.keys['s'] and self.player_y < HEIGHT - self.player_size:
            dy += speed
        if self.keys['a'] and self.player_x > self.player_size:
            dx -= speed
        if self.keys['d'] and self.player_x < WIDTH - self.player_size:
            dx += speed
        
        # Диагональное движение
        if dx != 0 and dy != 0:
            dx *= 0.7
            dy *= 0.7
        
        self.player_x += dx
        self.player_y += dy
        
        self.canvas.coords(self.player,
            self.player_x - self.player_size,
            self.player_y - self.player_size,
            self.player_x + self.player_size,
            self.player_y + self.player_size)
    
    def spawn_items(self, count):
        """Создание предметов"""
        for _ in range(count):
            x = random.randint(50, WIDTH-50)
            y = random.randint(50, HEIGHT-50)
            item_type = random.choice(['wood', 'berry'])
            
            if item_type == 'wood':
                color = 'saddle brown'
                shape = self.canvas.create_rectangle(
                    x-10, y-10, x+10, y+10,
                    fill=color, outline='gold', width=2
                )
            else:
                color = 'red'
                shape = self.canvas.create_oval(
                    x-8, y-8, x+8, y+8,
                    fill=color, outline='darkred', width=2
                )
            
            self.items.append({
                'type': item_type,
                'x': x,
                'y': y,
                'id': shape
            })
    
    def spawn_enemies(self, count):
        """Создание врагов"""
        for _ in range(count):
            x = random.randint(50, WIDTH-50)
            y = random.randint(50, HEIGHT-50)
            enemy = self.canvas.create_text(x, y, text='🐺', 
                                          font=("Arial", 30), fill='gray')
            self.enemies.append({
                'x': x,
                'y': y,
                'id': enemy,
                'speed': random.uniform(1, 3)
            })
    
    def spawn_bonuses(self, count):
        """Создание бонусов"""
        for _ in range(count):
            x = random.randint(50, WIDTH-50)
            y = random.randint(50, HEIGHT-50)
            bonus = self.canvas.create_text(x, y, text='✨', 
                                          font=("Arial", 30), fill='gold')
            self.bonuses.append({
                'x': x,
                'y': y,
                'id': bonus
            })
    
    def move_enemies(self):
        """Движение врагов к игроку"""
        for enemy in self.enemies:
            # Вектор к игроку
            dx = self.player_x - enemy['x']
            dy = self.player_y - enemy['y']
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist > 0:
                enemy['x'] += (dx / dist) * enemy['speed']
                enemy['y'] += (dy / dist) * enemy['speed']
            
            self.canvas.coords(enemy['id'], enemy['x'], enemy['y'])
    
    def check_collisions(self):
        """Проверка столкновений"""
        player_coords = [
            self.player_x - self.player_size,
            self.player_y - self.player_size,
            self.player_x + self.player_size,
            self.player_y + self.player_size
        ]
        
        # Сбор предметов
        for item in self.items[:]:
            if 'id' in item and item['id']:
                coords = self.canvas.coords(item['id'])
                if coords and len(coords) >= 4:
                    if (player_coords[2] > coords[0] and 
                        player_coords[0] < coords[2] and
                        player_coords[3] > coords[1] and 
                        player_coords[1] < coords[3]):
                        
                        self.canvas.delete(item['id'])
                        self.items.remove(item)
                        
                        if item['type'] == 'wood':
                            self.wood += 1
                            self.score += 10
                        else:
                            self.berries += 1
                            self.score += 5
                            self.energy = min(100, self.energy + 10)
        
        # Столкновение с врагами
        for enemy in self.enemies[:]:
            enemy_coords = self.canvas.bbox(enemy['id'])
            if enemy_coords:
                if (player_coords[2] > enemy_coords[0] and 
                    player_coords[0] < enemy_coords[2] and
                    player_coords[3] > enemy_coords[1] and 
                    player_coords[1] < enemy_coords[3]):
                    
                    self.energy -= 15
                    self.canvas.delete(enemy['id'])
                    self.enemies.remove(enemy)
                    
                    if self.energy <= 0:
                        self.game_over()
        
        # Сбор бонусов
        for bonus in self.bonuses[:]:
            bonus_coords = self.canvas.bbox(bonus['id'])
            if bonus_coords:
                if (player_coords[2] > bonus_coords[0] and 
                    player_coords[0] < bonus_coords[2] and
                    player_coords[3] > bonus_coords[1] and 
                    player_coords[1] < bonus_coords[3]):
                    
                    self.canvas.delete(bonus['id'])
                    self.bonuses.remove(bonus)
                    self.score += 50
                    self.energy = min(100, self.energy + 30)
        
        self.update_stats()
    
    def update_stats(self):
        """Обновление статистики"""
        self.canvas.itemconfig(self.wood_text, text=f"🪵 Дрова: {self.wood}")
        self.canvas.itemconfig(self.berries_text, text=f"🍓 Ягоды: {self.berries}")
        self.canvas.itemconfig(self.energy_text, text=f"⚡ Энергия: {self.energy}%")
        self.canvas.itemconfig(self.score_text, text=f"🏆 Счет: {self.score}")
    
    def game_over(self):
        """Конец игры"""
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, 
                                    fill='black', stipple='gray50')
        self.canvas.create_text(WIDTH//2, HEIGHT//2-50, 
            text="💀 ТЫ НЕ ВЫЖИЛ 💀", 
            fill='red', font=("Arial", 40, "bold"))
        self.canvas.create_text(WIDTH//2, HEIGHT//2+50, 
            text=f"🏆 Итоговый счет: {self.score}", 
            fill='white', font=("Arial", 24))
        self.canvas.create_text(WIDTH//2, HEIGHT//2+100, 
            text="Нажми R для перезапуска", 
            fill='gray', font=("Arial", 18))
        
        self.root.bind('r', self.restart_game)
    
    def restart_game(self, event):
        """Перезапуск игры"""
        # Очищаем холст
        self.canvas.delete("all")
        
        # Сбрасываем параметры
        self.__init__(self.root)
    
    def game_loop(self):
        """Основной игровой цикл"""
        if self.energy > 0:
            # Движение
            self.move_player()
            self.move_enemies()
            
            # Проверка столкновений
            self.check_collisions()
            
            # Спавн новых предметов
            if time.time() - self.last_spawn > 5:
                self.spawn_items(3)
                self.spawn_enemies(1)
                if random.random() > 0.5:
                    self.spawn_bonuses(1)
                self.last_spawn = time.time()
            
            # Потеря энергии со временем
            if random.random() < 0.01:
                self.energy -= 1
                if self.energy < 0:
                    self.energy = 0
                self.update_stats()
        
        self.root.after(int(1000/FPS), self.game_loop)

# Запуск игры
if __name__ == "__main__":
    root = tk.Tk()
    game = ForestGame(root)
    root.mainloop()