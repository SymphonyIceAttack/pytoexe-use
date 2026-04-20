import tkinter as tk
import math
import random

# --- Настройки игры ---
WIDTH, HEIGHT = 1600, 1200
TANK_SIZE = 40
BULLET_SIZE = 6
SPEED = 5
BULLET_SPEED = 10 # Увеличили скорость для наглядности

# --- Инициализация окна ---
root = tk.Tk()
root.title("Танчики (Tkinter) - Наведение на цель")
root.resizable(False, False)
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='white')
canvas.pack()

# --- Управление игроком ---
keys = {
    'w': False,
    's': False,
    'a': False,
    'd': False,
    'space': False
}

def key_press(event):
    if event.keysym in keys:
        keys[event.keysym] = True

def key_release(event):
    if event.keysym in keys:
        keys[event.keysym] = False

root.bind_all('<KeyPress>', key_press)
root.bind_all('<KeyRelease>', key_release)

# --- Класс для танка ---
class Tank:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.rect = canvas.create_rectangle(x, y, x + TANK_SIZE, y + TANK_SIZE, fill=color)
        self.bullets = [] # Список пуль (каждая пуля — словарь с координатами и вектором)

    def move(self, dx=0, dy=0):
        new_x = self.x + dx * SPEED
        new_y = self.y + dy * SPEED

        if 0 <= new_x <= WIDTH - TANK_SIZE and 0 <= new_y <= HEIGHT - TANK_SIZE:
            self.x = new_x
            self.y = new_y
            canvas.coords(self.rect, self.x, self.y, self.x + TANK_SIZE, self.y + TANK_SIZE)

    def shoot(self, target_x, target_y):
        # Вычисляем вектор направления к цели в момент выстрела
        start_x = self.x + TANK_SIZE / 2
        start_y = self.y + TANK_SIZE / 2

        dx = target_x - start_x
        dy = target_y - start_y
        dist = math.hypot(dx, dy)

        if dist == 0: # Защита от деления на ноль (если танки в одной точке)
            return

        # Нормализуем вектор и умножаем на скорость пули
        vx = (dx / dist) * BULLET_SPEED
        vy = (dy / dist) * BULLET_SPEED

        # Создаём пулю в центре танка
        bullet_x = start_x - BULLET_SIZE / 2
        bullet_y = start_y - BULLET_SIZE / 2

        bullet_id = canvas.create_oval(bullet_x, bullet_y, 
                                    bullet_x + BULLET_SIZE, bullet_y + BULLET_SIZE, 
                                    fill='black')
        
        self.bullets.append({
            'id': bullet_id,
            'x': bullet_x,
            'y': bullet_y,
            'vx': vx,
            'vy': vy
        })

    def update_bullets(self):
        for bullet in self.bullets[:]:
            # Двигаем пулю по её вектору скорости (vx, vy)
            bullet['x'] += bullet['vx']
            bullet['y'] += bullet['vy']
            canvas.move(bullet['id'], bullet['vx'], bullet['vy'])
            
            # Удаляем пулю, если она вылетела за экран
            coords = canvas.coords(bullet['id'])
            if coords[1] < 0 or coords[1] > HEIGHT or coords[0] < 0 or coords[0] > WIDTH:
                canvas.delete(bullet['id'])
                self.bullets.remove(bullet)

# --- Создание танков ---
player = Tank(50, HEIGHT - TANK_SIZE - 50, 'green') # Зелёный — снизу слева
enemy = Tank(WIDTH - TANK_SIZE - 50, 50, 'blue')   # Синий — сверху справа

# --- Функция перезапуска игры ---
def restart_game():
    player.x = 50
    player.y = HEIGHT - TANK_SIZE - 50
    enemy.x = WIDTH - TANK_SIZE - 50
    enemy.y = 50

    canvas.coords(player.rect, player.x, player.y, player.x + TANK_SIZE, player.y + TANK_SIZE)
    canvas.coords(enemy.rect, enemy.x, enemy.y, enemy.x + TANK_SIZE, enemy.y + TANK_SIZE)
    
    for b in player.bullets:
        canvas.delete(b['id'])
    for b in enemy.bullets:
        canvas.delete(b['id'])
        
    player.bullets.clear()
    enemy.bullets.clear()

# --- Главный игровой цикл ---
def game_loop():
    # Движение игрока по WASD
    if keys['w']:
        player.move(dy=-1)
    if keys['s']:
        player.move(dy=1)
    if keys['a']:
        player.move(dx=-1)
    if keys['d']:
        player.move(dx=1)
    
    # Стрельба игрока по Пробелу (с ограничением частоты стрельбы)
    if keys['space']:
        # Стреляем в текущее положение врага
        target_x = enemy.x + TANK_SIZE / 2
        target_y = enemy.y + TANK_SIZE / 2
        
        player.shoot(target_x, target_y)
        keys['space'] = False # Сброс флага для одного выстрела

    # Логика ИИ: преследование игрока и стрельба на опережение
    if enemy.x < player.x:
        enemy.move(dx=1)
    elif enemy.x > player.x:
        enemy.move(dx=-1)
        
    if enemy.y < player.y:
        enemy.move(dy=1)
    elif enemy.y > player.y:
        enemy.move(dy=-1)
    
    # Стрельба ИИ (случайно) в текущее положение игрока
    if random.random() < 0.02: 
        target_x = player.x + TANK_SIZE / 2
        target_y = player.y + TANK_SIZE / 2
        
        enemy.shoot(target_x, target_y)
    
    # Обновление пуль (движение по вектору)
    player.update_bullets()
    enemy.update_bullets()
    
    # Проверка попаданий (столкновения пуль с танками)
    p_coords = canvas.coords(player.rect)
    e_coords = canvas.coords(enemy.rect)
    
    for bullet in enemy.bullets[:]:
        # Проверяем пересечение пули с игроком
        if canvas.find_overlapping(*canvas.coords(bullet['id']))[0] == player.rect:
            restart_game()
            break

    for bullet in player.bullets[:]:
         # Проверяем пересечение пули с врагом
         if canvas.find_overlapping(*canvas.coords(bullet['id']))[0] == enemy.rect:
             restart_game()
             break

    root.after(30, game_loop) # Повторение цикла (около 33 FPS)

# Запуск игры
game_loop()
root.mainloop()