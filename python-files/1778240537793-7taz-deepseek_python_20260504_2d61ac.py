"""
SANTUM - Упрощенная копия Roblox
С многопользовательским режимом, редактором карт и создателем скинов
"""

import pygame
import socket
import threading
import json
import random
import sys
import pickle
from collections import defaultdict
import time

# Инициализация Pygame
pygame.init()
pygame.font.init()

# Константы
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
BLOCK_SIZE = 40

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)

class NetworkManager:
    """Менеджер сетевого взаимодействия"""
    def __init__(self):
        self.client_socket = None
        self.server_socket = None
        self.is_server = False
        self.players = {}
        self.game_objects = []
        self.player_id = str(random.randint(1000, 9999))
        
    def start_server(self, host='localhost', port=5555):
        """Запуск сервера"""
        self.is_server = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((host, port))
            self.server_socket.listen(10)
            print(f"Сервер запущен на {host}:{port}")
            
            # Запускаем поток для принятия подключений
            threading.Thread(target=self.accept_connections, daemon=True).start()
        except Exception as e:
            print(f"Ошибка запуска сервера: {e}")
            self.is_server = False
    
    def accept_connections(self):
        """Принятие входящих подключений"""
        while self.is_server:
            try:
                client, address = self.server_socket.accept()
                print(f"Подключен клиент: {address}")
                
                # Отправляем ID игрока
                client.send(self.player_id.encode())
                
                # Запускаем поток для обработки клиента
                threading.Thread(target=self.handle_client, 
                               args=(client, address), daemon=True).start()
            except:
                break
    
    def handle_client(self, client, address):
        """Обработка клиента"""
        while self.is_server:
            try:
                data = client.recv(4096)
                if not data:
                    break
                    
                message = json.loads(data.decode())
                
                if message['type'] == 'player_update':
                    self.players[message['id']] = message['data']
                    
                    # Отправляем обновление всем клиентам
                    response = {
                        'type': 'world_update',
                        'players': self.players,
                        'objects': self.game_objects
                    }
                    client.send(json.dumps(response).encode())
                    
                elif message['type'] == 'object_placed':
                    self.game_objects.append(message['data'])
                    
            except:
                break
        
        client.close()
    
    def connect_to_server(self, host='localhost', port=5555):
        """Подключение к серверу"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))
            
            # Получаем ID
            self.player_id = self.client_socket.recv(1024).decode()
            print(f"Подключен к серверу. ID: {self.player_id}")
            
            # Запускаем поток для получения данных
            threading.Thread(target=self.receive_data, daemon=True).start()
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False
    
    def receive_data(self):
        """Получение данных от сервера"""
        while True:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    break
                    
                message = json.loads(data.decode())
                if message['type'] == 'world_update':
                    self.players = message['players']
                    self.game_objects = message['objects']
                    
            except:
                break
    
    def send_player_data(self, data):
        """Отправка данных игрока"""
        if self.client_socket:
            try:
                message = {
                    'type': 'player_update',
                    'id': self.player_id,
                    'data': data
                }
                self.client_socket.send(json.dumps(message).encode())
            except:
                pass
    
    def send_object_placed(self, obj_data):
        """Отправка данных о размещенном объекте"""
        if self.client_socket:
            try:
                message = {
                    'type': 'object_placed',
                    'data': obj_data
                }
                self.client_socket.send(json.dumps(message).encode())
            except:
                pass
    
    def close(self):
        """Закрытие соединений"""
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()

class SkinCreator:
    """Создатель скинов"""
    def __init__(self, screen):
        self.screen = screen
        self.current_color = RED
        self.skin_data = [[RED for _ in range(8)] for _ in range(8)]
        self.drawing = False
        self.skins = {}
        self.current_skin = "default"
        
    def draw_editor(self):
        """Отрисовка редактора скинов"""
        # Фон
        pygame.draw.rect(self.screen, WHITE, (50, 50, 400, 500))
        pygame.draw.rect(self.screen, BLACK, (50, 50, 400, 500), 2)
        
        # Сетка
        for i in range(8):
            for j in range(8):
                x = 50 + i * 50
                y = 50 + j * 50
                color = self.skin_data[j][i]
                pygame.draw.rect(self.screen, color, (x, y, 50, 50))
                pygame.draw.rect(self.screen, BLACK, (x, y, 50, 50), 2)
        
        # Палитра цветов
        colors = [RED, GREEN, BLUE, YELLOW, PURPLE, CYAN, WHITE, BLACK]
        for i, color in enumerate(colors):
            x = 500 + (i % 4) * 50
            y = 50 + (i // 4) * 50
            pygame.draw.rect(self.screen, color, (x, y, 40, 40))
            pygame.draw.rect(self.screen, BLACK, (x, y, 40, 40), 2)
            if color == self.current_color:
                pygame.draw.rect(self.screen, WHITE, (x, y, 40, 40), 4)
        
        # Кнопки
        font = pygame.font.Font(None, 24)
        
        # Сохранить скин
        save_btn = pygame.Rect(500, 200, 150, 40)
        pygame.draw.rect(self.screen, GREEN, save_btn)
        text = font.render("Сохранить", True, WHITE)
        self.screen.blit(text, (525, 210))
        
        # Загрузить скин
        load_btn = pygame.Rect(500, 250, 150, 40)
        pygame.draw.rect(self.screen, BLUE, load_btn)
        text = font.render("Загрузить", True, WHITE)
        self.screen.blit(text, (525, 260))
        
        return save_btn, load_btn
    
    def handle_click(self, pos):
        """Обработка кликов в редакторе"""
        x, y = pos
        
        # Сетка
        if 50 <= x <= 450 and 50 <= y <= 450:
            grid_x = (x - 50) // 50
            grid_y = (y - 50) // 50
            if 0 <= grid_x < 8 and 0 <= grid_y < 8:
                self.skin_data[grid_y][grid_x] = self.current_color
                return True
        
        # Палитра
        colors = [RED, GREEN, BLUE, YELLOW, PURPLE, CYAN, WHITE, BLACK]
        for i, color in enumerate(colors):
            pal_x = 500 + (i % 4) * 50
            pal_y = 50 + (i // 4) * 50
            if pal_x <= x <= pal_x + 40 and pal_y <= y <= pal_y + 40:
                self.current_color = color
                return True
        
        return False
    
    def save_skin(self, name):
        """Сохранить скин"""
        self.skins[name] = [row[:] for row in self.skin_data]
        self.current_skin = name
    
    def load_skin(self, name):
        """Загрузить скин"""
        if name in self.skins:
            self.skin_data = [row[:] for row in self.skins[name]]
            self.current_skin = name

class Map:
    """Карта игры"""
    def __init__(self):
        self.width = 25
        self.height = 19
        self.tiles = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.spawn_points = [(2, 2), (22, 16)]
        
    def add_tile(self, x, y, tile_type="block"):
        """Добавить тайл"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x] = tile_type
    
    def remove_tile(self, x, y):
        """Удалить тайл"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x] = None
    
    def is_solid(self, x, y):
        """Проверка на твердый блок"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x] is not None
        return True
    
    def draw(self, screen, camera_x, camera_y):
        """Отрисовка карты"""
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x]:
                    tile_x = x * BLOCK_SIZE - camera_x
                    tile_y = y * BLOCK_SIZE - camera_y
                    
                    # Проверка видимости
                    if -BLOCK_SIZE <= tile_x <= SCREEN_WIDTH and -BLOCK_SIZE <= tile_y <= SCREEN_HEIGHT:
                        color = GRAY
                        if self.tiles[y][x] == "spawn":
                            color = GREEN
                        elif self.tiles[y][x] == "danger":
                            color = RED
                        
                        pygame.draw.rect(screen, color, 
                                       (tile_x, tile_y, BLOCK_SIZE, BLOCK_SIZE))
                        pygame.draw.rect(screen, BLACK, 
                                       (tile_x, tile_y, BLOCK_SIZE, BLOCK_SIZE), 2)

class Player:
    """Игрок"""
    def __init__(self, x, y, color=RED):
        self.x = x
        self.y = y
        self.color = color
        self.vx = 0
        self.vy = 0
        self.width = 30
        self.height = 40
        self.on_ground = False
        self.speed = 5
        self.jump_power = -12
        
    def update(self, map_obj):
        """Обновление позиции"""
        # Гравитация
        self.vy += 0.8
        
        # Движение
        self.x += self.vx
        self.y += self.vy
        
        # Коллизии
        self.check_collisions(map_obj)
        
        # Трение
        self.vx *= 0.9
        
    def check_collisions(self, map_obj):
        """Проверка коллизий"""
        # Границы экрана
        self.x = max(0, min(self.x, map_obj.width * BLOCK_SIZE - self.width))
        
        # Коллизии с блоками
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        for y in range(map_obj.height):
            for x in range(map_obj.width):
                if map_obj.tiles[y][x]:
                    block_rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, 
                                           BLOCK_SIZE, BLOCK_SIZE)
                    
                    if player_rect.colliderect(block_rect):
                        # Определение стороны коллизии
                        dx = self.x - block_rect.x
                        dy = self.y - block_rect.y
                        
                        if abs(dx) > abs(dy):
                            if dx > 0:
                                self.x = block_rect.right
                            else:
                                self.x = block_rect.x - self.width
                            self.vx = 0
                        else:
                            if dy > 0:
                                self.y = block_rect.bottom
                                self.vy = 0
                                self.on_ground = True
                            else:
                                self.y = block_rect.y - self.height
                                self.vy = 0
    
    def move(self, dx):
        """Движение влево/вправо"""
        self.vx = dx * self.speed
    
    def jump(self):
        """Прыжок"""
        if self.on_ground:
            self.vy = self.jump_power
            self.on_ground = False
    
    def draw(self, screen, camera_x, camera_y):
        """Отрисовка игрока"""
        player_x = self.x - camera_x
        player_y = self.y - camera_y
        
        # Тело
        pygame.draw.rect(screen, self.color, 
                        (player_x, player_y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, 
                        (player_x, player_y, self.width, self.height), 2)
        
        # Лицо
        eye_color = WHITE
        pygame.draw.circle(screen, eye_color, 
                          (int(player_x + 10), int(player_y + 10)), 4)
        pygame.draw.circle(screen, eye_color, 
                          (int(player_x + 20), int(player_y + 10)), 4)
        pygame.draw.circle(screen, BLACK, 
                          (int(player_x + 10), int(player_y + 10)), 2)
        pygame.draw.circle(screen, BLACK, 
                          (int(player_x + 20), int(player_y + 10)), 2)

class Game:
    """Основной класс игры Santum"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("SANTUM - Roblox Copy")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Состояния игры
        self.states = ["menu", "editor", "skin_creator", "playing"]
        self.current_state = "menu"
        
        # Компоненты
        self.network = NetworkManager()
        self.skin_creator = SkinCreator(self.screen)
        self.map = Map()
        self.player = Player(100, 100, RED)
        
        # Камера
        self.camera_x = 0
        self.camera_y = 0
        
        # Чат
        self.chat_messages = []
        self.chat_input = ""
        self.chat_active = False
        
        # Таймер
        self.last_time = time.time()
        
        # Кнопки для разных режимов
        self.buttons = {}
        
        # Создаем базовую карту
        self.create_default_map()
        
    def create_default_map(self):
        """Создание базовой карты"""
        # Пол
        for x in range(self.map.width):
            self.map.add_tile(x, self.map.height - 1)
        
        # Стены
        for y in range(self.map.height):
            self.map.add_tile(0, y)
            self.map.add_tile(self.map.width - 1, y)
        
        # Платформы
        for x in range(5, 10):
            self.map.add_tile(x, 15)
        
        for x in range(15, 20):
            self.map.add_tile(x, 13)
        
        # Точки спавна
        self.map.add_tile(2, self.map.height - 3, "spawn")
        self.map.add_tile(22, self.map.height - 3, "spawn")
    
    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.network.close()
                
            elif event.type == pygame.KEYDOWN:
                if self.current_state == "playing":
                    if event.key == pygame.K_SPACE:
                        self.player.jump()
                    elif event.key == pygame.K_t:
                        self.chat_active = True
                        self.chat_input = ""
                    elif event.key == pygame.K_ESCAPE:
                        self.current_state = "menu"
                    
                if self.chat_active:
                    if event.key == pygame.K_RETURN:
                        if self.chat_input:
                            self.chat_messages.append(f"Я: {self.chat_input}")
                            self.chat_active = False
                            self.chat_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        self.chat_input = self.chat_input[:-1]
                    else:
                        if event.unicode.isprintable():
                            self.chat_input += event.unicode
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_click(event.pos, event.button)
    
    def handle_mouse_click(self, pos, button):
        """Обработка кликов мыши"""
        x, y = pos
        
        if self.current_state == "menu":
            self.handle_menu_click(x, y)
            
        elif self.current_state == "editor":
            self.handle_editor_click(x, y, button)
            
        elif self.current_state == "skin_creator":
            self.handle_skin_creator_click(x, y)
    
    def handle_menu_click(self, x, y):
        """Обработка кликов в меню"""
        # Играть
        if 362 <= x <= 662 and 200 <= y <= 250:
            self.current_state = "playing"
        
        # Редактор карт
        elif 362 <= x <= 662 and 270 <= y <= 320:
            self.current_state = "editor"
        
        # Создатель скинов
        elif 362 <= x <= 662 and 340 <= y <= 390:
            self.current_state = "skin_creator"
        
        # Сервер
        elif 362 <= x <= 662 and 410 <= y <= 460:
            self.network.start_server()
        
        # Подключение
        elif 362 <= x <= 662 and 480 <= y <= 530:
            self.network.connect_to_server()
        
        # Выход
        elif 362 <= x <= 662 and 550 <= y <= 600:
            self.running = False
    
    def handle_editor_click(self, x, y, button):
        """Обработка кликов в редакторе"""
        # Конвертация в координаты карты
        map_x = (x + self.camera_x) // BLOCK_SIZE
        map_y = (y + self.camera_y) // BLOCK_SIZE
        
        if button == 1:  # Левая кнопка
            self.map.add_tile(map_x, map_y, "block")
            self.network.send_object_placed({
                'x': map_x,
                'y': map_y,
                'type': 'block'
            })
        elif button == 3:  # Правая кнопка
            self.map.remove_tile(map_x, map_y)
    
    def handle_skin_creator_click(self, x, y):
        """Обработка кликов в создателе скинов"""
        buttons = self.skin_creator.draw_editor()
        self.skin_creator.handle_click((x, y))
        
        if buttons[0].collidepoint(x, y):  # Сохранить
            self.skin_creator.save_skin(f"skin_{len(self.skin_creator.skins)}")
        elif buttons[1].collidepoint(x, y):  # Загрузить
            if self.skin_creator.skins:
                self.skin_creator.load_skin(list(self.skin_creator.skins.keys())[-1])
    
    def update(self):
        """Обновление игры"""
        if self.current_state == "playing":
            # Управление
            keys = pygame.key.get_pressed()
            if not self.chat_active:
                if keys[pygame.K_a]:
                    self.player.move(-1)
                elif keys[pygame.K_d]:
                    self.player.move(1)
                else:
                    self.player.move(0)
            
            # Обновление игрока
            self.player.update(self.map)
            
            # Камера следует за игроком
            self.camera_x = self.player.x - SCREEN_WIDTH // 2
            self.camera_y = self.player.y - SCREEN_HEIGHT // 2
            
            # Отправка данных игрока
            player_data = {
                'x': self.player.x,
                'y': self.player.y,
                'color': list(self.player.color)
            }
            self.network.send_player_data(player_data)
        
        elif self.current_state == "editor":
            # Управление камерой в редакторе
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.camera_x -= 10
            if keys[pygame.K_RIGHT]:
                self.camera_x += 10
            if keys[pygame.K_UP]:
                self.camera_y -= 10
            if keys[pygame.K_DOWN]:
                self.camera_y += 10
            if keys[pygame.K_ESCAPE]:
                self.current_state = "menu"
    
    def draw(self):
        """Отрисовка"""
        self.screen.fill(WHITE)
        
        if self.current_state == "menu":
            self.draw_menu()
        elif self.current_state == "editor":
            self.draw_editor()
        elif self.current_state == "skin_creator":
            self.draw_skin_creator()
        elif self.current_state == "playing":
            self.draw_game()
        
        pygame.display.flip()
    
    def draw_menu(self):
        """Отрисовка главного меню"""
        # Заголовок
        font_large = pygame.font.Font(None, 74)
        title = font_large.render("SANTUM", True, BLUE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 100))
        self.screen.blit(title, title_rect)
        
        # Подзаголовок
        font_small = pygame.font.Font(None, 36)
        subtitle = font_small.render("Roblox Copy", True, BLACK)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH//2, 150))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Кнопки
        buttons = [
            ("Играть", (SCREEN_WIDTH//2, 225)),
            ("Редактор карт", (SCREEN_WIDTH//2, 295)),
            ("Создатель скинов", (SCREEN_WIDTH//2, 365)),
            ("Запустить сервер", (SCREEN_WIDTH//2, 435)),
            ("Подключиться", (SCREEN_WIDTH//2, 505)),
            ("Выход", (SCREEN_WIDTH//2, 575))
        ]
        
        font_button = pygame.font.Font(None, 36)
        for text, pos in buttons:
            button_rect = pygame.Rect(pos[0] - 150, pos[1] - 25, 300, 50)
            pygame.draw.rect(self.screen, BLUE, button_rect)
            pygame.draw.rect(self.screen, BLACK, button_rect, 2)
            
            text_surface = font_button.render(text, True, WHITE)
            text_rect = text_surface.get_rect(center=pos)
            self.screen.blit(text_surface, text_rect)
    
    def draw_editor(self):
        """Отрисовка редактора карт"""
        # Отрисовка сетки
        for y in range(self.map.height):
            for x in range(self.map.width):
                rect_x = x * BLOCK_SIZE - self.camera_x
                rect_y = y * BLOCK_SIZE - self.camera_y
                
                if 0 <= rect_x <= SCREEN_WIDTH and 0 <= rect_y <= SCREEN_HEIGHT:
                    # Сетка
                    pygame.draw.rect(self.screen, LIGHT_GRAY, 
                                   (rect_x, rect_y, BLOCK_SIZE, BLOCK_SIZE), 1)
        
        # Отрисовка карты
        self.map.draw(self.screen, self.camera_x, self.camera_y)
        
        # Инструкции
        font = pygame.font.Font(None, 24)
        instructions = [
            "ЛКМ - разместить блок",
            "ПКМ - удалить блок",
            "Стрелки - движение камеры",
            "ESC - назад в меню"
        ]
        
        for i, text in enumerate(instructions):
            surface = font.render(text, True, BLACK)
            self.screen.blit(surface, (10, 10 + i * 25))
    
    def draw_skin_creator(self):
        """Отрисовка создателя скинов"""
        self.skin_creator.draw_editor()
        
        # Инструкции
        font = pygame.font.Font(None, 24)
        instructions = [
            "Выберите цвет из палитры",
            "Кликните по сетке для рисования",
            "ESC - назад в меню"
        ]
        
        for i, text in enumerate(instructions):
            surface = font.render(text, True, BLACK)
            self.screen.blit(surface, (10, 550 + i * 25))
    
    def draw_game(self):
        """Отрисовка игры"""
        # Фон
        pygame.draw.rect(self.screen, (135, 206, 235), 
                        (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Карта
        self.map.draw(self.screen, self.camera_x, self.camera_y)
        
        # Игрок
        self.player.draw(self.screen, self.camera_x, self.camera_y)
        
        # Другие игроки
        for player_id, player_data in self.network.players.items():
            if player_id != self.network.player_id:
                other_x = player_data['x'] - self.camera_x
                other_y = player_data['y'] - self.camera_y
                color = tuple(player_data.get('color', RED))
                
                pygame.draw.rect(self.screen, color, 
                               (other_x, other_y, 30, 40))
                pygame.draw.rect(self.screen, BLACK, 
                               (other_x, other_y, 30, 40), 2)
        
        # HUD
        font = pygame.font.Font(None, 24)
        fps_text = font.render(f"FPS: {int(self.clock.get_fps())}", True, BLACK)
        self.screen.blit(fps_text, (10, 10))
        
        players_text = font.render(f"Игроков: {len(self.network.players) + 1}", 
                                  True, BLACK)
        self.screen.blit(players_text, (10, 35))
        
        # Чат
        self.draw_chat()
    
    def draw_chat(self):
        """Отрисовка чата"""
        font = pygame.font.Font(None, 24)
        chat_y = SCREEN_HEIGHT - 150
        
        # Фон чата
        if self.chat_active:
            pygame.draw.rect(self.screen, (0, 0, 0, 128), 
                           (10, chat_y - 10, 300, 140))
        
        # Сообщения
        for i, message in enumerate(self.chat_messages[-5:]):
            text = font.render(message, True, WHITE)
            self.screen.blit(text, (15, chat_y + i * 25))
        
        # Поле ввода
        if self.chat_active:
            input_text = font.render(f"> {self.chat_input}", True, WHITE)
            self.screen.blit(input_text, (15, chat_y + 125))
    
    def run(self):
        """Запуск игры"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()