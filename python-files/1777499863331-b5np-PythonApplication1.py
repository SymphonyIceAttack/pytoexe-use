import tkinter as tk
import math
import random

# --- Настройки игры ---
WIDTH, HEIGHT = 1600, 1000
TANK_SIZE = 40
BULLET_SIZE = 6
PLAYER_SPEED = 6
ENEMY_SPEED = 4
BULLET_SPEED = 10

# --- НОВОЕ: Счётчик очков ---
player_score = 0 # Сколько раз игрок убил ИИ
enemy_score = 0  # Сколько раз ИИ убил игрока

# --- Инициализация окна ---
root = tk.Tk()
root.title("Танчики (Tkinter) - Наведение на цель")
root.resizable(False, False)
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='white')
canvas.pack()

# --- НОВОЕ: Отрисовка счётчика в углу ---
score_text = canvas.create_text(10, 10, anchor='nw', text=f"{player_score}/{enemy_score}", font=('Arial', 10), fill='black')

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
    def __init__(self, x, y, color, speed):
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.rect = canvas.create_rectangle(x, y, x + TANK_SIZE, y + TANK_SIZE, fill=color)
        self.bullets = []

    def move(self, dx=0, dy=0):
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed

        if 0 <= new_x <= WIDTH - TANK_SIZE and 0 <= new_y <= HEIGHT - TANK_SIZE:
            self.x = new_x
            self.y = new_y
            canvas.coords(self.rect, self.x, self.y, self.x + TANK_SIZE, self.y + TANK_SIZE)

    def shoot(self, target_x, target_y):
        start_x = self.x + TANK_SIZE / 2
        start_y = self.y + TANK_SIZE / 2

        dx = target_x - start_x
        dy = target_y - start_y
        dist = math.hypot(dx, dy)

        if dist == 0:
            return

        vx = (dx / dist) * BULLET_SPEED
        vy = (dy / dist) * BULLET_SPEED

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
            bullet['x'] += bullet['vx']
            bullet['y'] += bullet['vy']
            canvas.move(bullet['id'], bullet['vx'], bullet['vy'])
            
            coords = canvas.coords(bullet['id'])
            if coords[1] < 0 or coords[1] > HEIGHT or coords[0] < 0 or coords[0] > WIDTH:
                canvas.delete(bullet['id'])
                self.bullets.remove(bullet)

# --- Создание танков ---
player = Tank(50, HEIGHT - TANK_SIZE - 50, 'green', PLAYER_SPEED)
enemy = Tank(WIDTH - TANK_SIZE - 50, 50, 'blue', ENEMY_SPEED)

# --- НОВОЕ: Логика перезапуска и подсчёта очков ---
def restart_game(who_won):
    """
    Перезапускает игру и обновляет счёт.
    who_won: 'player' если убил игрок, 'enemy' если убил ИИ.
    """
    global player_score, enemy_score

    if who_won == 'player':
         player_score += 1
    elif who_won == 'enemy':
         enemy_score += 1

    # Обновляем текст на холсте
    canvas.itemconfig(score_text, text=f"{player_score}/{enemy_score}")
    
    # Сброс позиций танков и пуль
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
    # Движение игрока по WASD с его скоростью (6)
    if keys['w']:
        player.move(dy=-1)
    if keys['s']:
        player.move(dy=1)
    if keys['a']:
        player.move(dx=-1)
    if keys['d']:
        player.move(dx=1)
    
    # Стрельба игрока по Пробелу
    if keys['space']:
        target_x = enemy.x + TANK_SIZE / 2
        target_y = enemy.y + TANK_SIZE / 2
        
        player.shoot(target_x, target_y)
        keys['space'] = False 

    # Логика ИИ: преследование игрока со своей скоростью (4)
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
    
    # Проверка: попали ли пули врага в игрока?
    for bullet in enemy.bullets[:]:
         if canvas.find_overlapping(*canvas.coords(bullet['id']))[0] == player.rect:
             restart_game('enemy') # Передаём информацию о победителе для подсчёта очков
             break

    # Проверка: попали ли пули игрока во врага?
    for bullet in player.bullets[:]:
         if canvas.find_overlapping(*canvas.coords(bullet['id']))[0] == enemy.rect:
             restart_game('player') # Передаём информацию о победителе для подсчёта очков
             break

    root.after(30, game_loop) 

# Запуск игры
game_loop()
root.mainloop()