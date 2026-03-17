from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random

# Настройка игры
app = Ursina()
window.title = '3D Шутер'
window.borderless = False
window.fullscreen = False
window.exit_button.visible = False
window.fps_counter.enabled = True

# Переменные игры
health = 100
score = 0
weapon_mode = 'gun'  # 'gun' или 'knife'

# Класс врага
class Enemy(Entity):
    def __init__(self, position=(0,0,0)):
        super().__init__(
            model='cube',
            color=color.red,
            scale=1,
            position=position,
            collider='box'
        )
        self.speed = 1
        self.health = 30
        
    def update(self):
        # Движение к игроку
        direction = (player.position - self.position).normalized()
        self.position += direction * self.speed * time.dt
        
        # Поворот к игроку
        self.look_at(player.position)
        
        # Проверка на урон от ножа
        if weapon_mode == 'knife' and distance(player.position, self.position) < 3:
            if held_keys['left mouse']:
                self.health -= 50 * time.dt
                self.color = color.white
            else:
                self.color = color.red
        else:
            self.color = color.red
        
        # Смерть врага
        if self.health <= 0:
            destroy(self)
            global score
            score += 10

# Оружие
class Weapon(Entity):
    def __init__(self):
        super().__init__(
            parent=camera.ui,
            model='cube',
            color=color.gray,
            position=(0.5, -0.4, 1),
            scale=(0.3, 0.1, 0.5),
            rotation=(0, 0, 0)
        )
        # Ствол для пулемёта
        self.barrel = Entity(
            parent=self,
            model='cube',
            color=color.dark_gray,
            position=(0, 0, 0.3),
            scale=(0.1, 0.1, 0.3)
        )
        # Рукоятка
        self.handle = Entity(
            parent=self,
            model='cube',
            color=color.brown,
            position=(0, -0.1, -0.1),
            scale=(0.1, 0.1, 0.2)
        )
        # Лезвие ножа (изначально скрыто)
        self.blade = Entity(
            parent=self,
            model='cube',
            color=color.light_gray,
            position=(0, 0, 0.5),
            scale=(0.05, 0.05, 0.4),
            visible=False
        )
        
    def switch_to_knife(self):
        self.model = None
        self.color = color.clear
        self.barrel.visible = False
        self.handle.visible = True
        self.blade.visible = True
        self.scale = (0.2, 0.2, 0.5)
        
    def switch_to_gun(self):
        self.model = 'cube'
        self.color = color.gray
        self.barrel.visible = True
        self.handle.visible = True
        self.blade.visible = False
        self.scale = (0.3, 0.1, 0.5)

# Игрок
class Player(FirstPersonController):
    def __init__(self):
        super().__init__()
        self.speed = 8
        self.health = 100
        self.max_health = 100
        self.cursor.visible = False
        
    def update(self):
        super().update()
        # Проверка столкновения с врагами
        for enemy in enemies:
            if distance(self.position, enemy.position) < 1.5:
                self.health -= 20 * time.dt
                if self.health <= 0:
                    print('Game Over!')
                    application.quit()

# Интерфейс
class HealthBar(Entity):
    def __init__(self):
        super().__init__(
            parent=camera.ui,
            model='quad',
            color=color.green,
            scale=(0.3, 0.03),
            position=(-0.65, 0.45)
        )
        self.bg = Entity(
            parent=camera.ui,
            model='quad',
            color=color.dark_gray,
            scale=(0.3, 0.03),
            position=(-0.65, 0.45)
        )
        
    def update(self):
        self.scale_x = 0.3 * (player.health / player.max_health)
        if player.health < 30:
            self.color = color.red
        elif player.health < 60:
            self.color = color.orange

class ScoreText(Text):
    def __init__(self):
        super().__init__(
            text='Score: 0',
            position=(-0.85, 0.4),
            scale=2,
            color=color.white
        )

class WeaponText(Text):
    def __init__(self):
        super().__init__(
            text='GUN (1)',
            position=(0.7, 0.4),
            scale=1.5,
            color=color.white
        )

# Создание объектов
player = Player()
weapon = Weapon()
health_bar = HealthBar()
score_text = ScoreText()
weapon_text = WeaponText()

# Стена для тестирования
wall = Entity(
    model='cube',
    color=color.azure,
    scale=(20, 5, 1),
    position=(0, 2, 20),
    collider='box'
)

# Пол
ground = Entity(
    model='plane',
    texture='grass',
    scale=50,
    collider='box'
)

# Стены по бокам
left_wall = Entity(
    model='cube',
    color=color.gray,
    scale=(1, 5, 50),
    position=(-25, 2, 0),
    collider='box'
)

right_wall = Entity(
    model='cube',
    color=color.gray,
    scale=(1, 5, 50),
    position=(25, 2, 0),
    collider='box'
)

back_wall = Entity(
    model='cube',
    color=color.gray,
    scale=(50, 5, 1),
    position=(0, 2, -25),
    collider='box'
)

# Освещение
Sky(color=color.light_gray)
sun = DirectionalLight(shadows=True)
sun.look_at(Vec3(1, -1, 1))

# Список врагов
enemies = []

# Функция спавна врагов
def spawn_enemy():
    if len(enemies) < 5:
        x = random.uniform(-15, 15)
        z = random.uniform(-15, 15)
        enemy = Enemy(position=(x, 1, z))
        enemies.append(enemy)

# Таймер спавна врагов
spawn_timer = 0

# Функция стрельбы
def shoot():
    if weapon_mode == 'gun':
        # Создаём пулю
        bullet = Entity(
            model='sphere',
            color=color.yellow,
            scale=0.2,
            position=player.position + (0, 1, 0) + player.forward * 2,
            collider='sphere'
        )
        bullet.animate_position(
            bullet.position + player.forward * 50,
            duration=1,
            curve=curve.linear
        )
        # Проверка попадания
        def check_hit():
            for enemy in enemies:
                if distance(bullet.position, enemy.position) < 1.5:
                    enemy.health -= 50
                    destroy(bullet)
                    return
            destroy(bullet, delay=1)
        bullet.check_hit = check_hit

# Функция обновления игры
def update():
    global spawn_timer, weapon_mode, score
    
    # Спавн врагов
    spawn_timer += time.dt
    if spawn_timer > 3:
        spawn_enemy()
        spawn_timer = 0
    
    # Переключение оружия
    if held_keys['1']:
        weapon_mode = 'gun'
        weapon.switch_to_gun()
        weapon_text.text = 'GUN (1)'
    if held_keys['2']:
        weapon_mode = 'knife'
        weapon.switch_to_knife()
        weapon_text.text = 'KNIFE (2)'
    
    # Стрельба (для пулемёта - зажатие)
    if weapon_mode == 'gun' and held_keys['left mouse']:
        shoot()
    
    # Обновление интерфейса
    score_text.text = f'Score: {score}'
    
    # Проверка пуль
    for bullet in scene.entities:
        if hasattr(bullet, 'check_hit'):
            bullet.check_hit()

# Создаём первого врага сразу
spawn_enemy()

# Запуск игры
app.run()