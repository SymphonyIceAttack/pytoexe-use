import pygame
import math
import random
import json
import os

# Инициализация Pygame
pygame.init()

# Размеры окна
WIDTH, HEIGHT = 800, 800
CENTER = (WIDTH // 2, HEIGHT // 2)
RADAR_RADIUS = 300

# Цвета для текста (разные сложности)
TEXT_COLORS = {
    'щадящий': (100, 200, 255),
    'лёгкий': (0, 255, 0),
    'средний': (255, 255, 0),
    'сложный': (255, 165, 0),
    'extreme': (255, 0, 0)
}

# Базовые цвета радара (всегда зелёные)
RADAR_GREEN = (0, 255, 0)
RADAR_DARK_GREEN = (0, 150, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_RED = (139, 0, 0)
GOLD = (255, 215, 0)
PURPLE = (128, 0, 128)

# Настройки экрана
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Радар - Охота на цели")
clock = pygame.time.Clock()


# --- Система достижений ---
class Achievement:
    def __init__(self, id, name, description, condition_checker, reward_points=0):
        self.id = id
        self.name = name
        self.description = description
        self.condition_checker = condition_checker
        self.unlocked = False
        self.reward_points = reward_points

    def check(self, game_data):
        if not self.unlocked and self.condition_checker(game_data):
            self.unlocked = True
            return True
        return False


class AchievementManager:
    def __init__(self):
        self.achievements = []
        self.game_data = {
            'total_kills': 0,
            'golden_kills': 0,
            'purple_kills': 0,
            'black_kills': 0,
            'max_combo': 0,
            'fast_kills': 0,
            'shop_items_bought': 0,
            'console_used': False,
            'highest_difficulty_level': {'щадящий': 0, 'лёгкий': 0, 'средний': 0, 'сложный': 0, 'extreme': 0},
            'survival_score': 0,
            'record_broken': False,
            'powerups_bought': []
        }
        self.load_achievements()
        self.load_progress()

    def load_achievements(self):
        # Навык стрельбы
        self.achievements.append(Achievement("first_shot", "Первый выстрел", "Уничтожьте первую цель (1 очко)",
                                             lambda d: d['total_kills'] >= 1))
        self.achievements.append(Achievement("marksman", "Меткий стрелок", "Уничтожьте 50 целей",
                                             lambda d: d['total_kills'] >= 50))
        self.achievements.append(Achievement("sniper", "Снайпер", "Уничтожьте 200 целей",
                                             lambda d: d['total_kills'] >= 200))
        self.achievements.append(Achievement("legend", "Легенда", "Уничтожьте 500 целей",
                                             lambda d: d['total_kills'] >= 500))

        # Особые цели
        self.achievements.append(Achievement("gold_rush", "Золотая лихорадка", "Уничтожьте первую золотую цель",
                                             lambda d: d['golden_kills'] >= 1))
        self.achievements.append(Achievement("gold_magnate", "Золотой магнат", "Уничтожьте 10 золотых целей",
                                             lambda d: d['golden_kills'] >= 10))
        self.achievements.append(Achievement("purple_haze", "Фиолетовый туман", "Уничтожьте первую фиолетовую цель",
                                             lambda d: d['purple_kills'] >= 1))
        self.achievements.append(Achievement("purple_tamer", "Укротитель фиолетовых", "Уничтожьте 20 фиолетовых целей",
                                             lambda d: d['purple_kills'] >= 20))
        self.achievements.append(Achievement("boss_killer", "Победитель босса", "Уничтожьте первого чёрного босса",
                                             lambda d: d['black_kills'] >= 1))
        self.achievements.append(Achievement("boss_hunter", "Охотник на боссов", "Уничтожьте 10 чёрных боссов",
                                             lambda d: d['black_kills'] >= 10))

        # Сложности и режимы
        self.achievements.append(Achievement("novice", "Новичок", "Пройдите уровень 5 на щадящей сложности",
                                             lambda d: d['highest_difficulty_level']['щадящий'] >= 5))
        self.achievements.append(Achievement("master", "Мастер", "Пройдите уровень 10 на сложной сложности",
                                             lambda d: d['highest_difficulty_level']['сложный'] >= 10))
        self.achievements.append(Achievement("extreme", "Экстремал", "Пройдите 5 уровней на сложности Extreme",
                                             lambda d: d['highest_difficulty_level']['extreme'] >= 5))
        self.achievements.append(Achievement("survivor", "Выживший", "Наберите 50 очков в режиме выживания",
                                             lambda d: d['survival_score'] >= 50))
        self.achievements.append(Achievement("immortal", "Бессмертный", "Наберите 200 очков в режиме выживания",
                                             lambda d: d['survival_score'] >= 200))

        # Скорость
        self.achievements.append(Achievement("fast_reaction", "Быстрая реакция", "Уничтожьте цель за 0.5 секунды",
                                             lambda d: d['fast_kills'] >= 1))
        self.achievements.append(Achievement("lightning", "Молниеносный", "Уничтожьте 10 целей за 0.5 секунды",
                                             lambda d: d['fast_kills'] >= 10))

        # Комбо и рекорды
        self.achievements.append(
            Achievement("perfect_series", "Идеальная серия", "Уничтожьте 20 целей подряд без промахов",
                        lambda d: d['max_combo'] >= 20))
        self.achievements.append(Achievement("flawless", "Безупречность", "Уничтожьте 50 целей подряд без промахов",
                                             lambda d: d['max_combo'] >= 50))
        self.achievements.append(Achievement("record_breaker", "Рекордсмен", "Побить рекорд на любой сложности",
                                             lambda d: d['record_broken']))

        # Магазин
        self.achievements.append(Achievement("shopaholic", "Шопоголик", "Купите первый предмет в магазине",
                                             lambda d: d['shop_items_bought'] >= 1))
        self.achievements.append(Achievement("collector", "Коллекционер", "Купите все типы улучшений",
                                             lambda d: len(d['powerups_bought']) >= 3))

        # Особые
        self.achievements.append(Achievement("hacker", "Хакер", "Используйте консольную команду",
                                             lambda d: d['console_used']))

    def load_progress(self):
        if os.path.exists('achievements.json'):
            try:
                with open('achievements.json', 'r') as f:
                    data = json.load(f)
                    for ach in self.achievements:
                        if ach.id in data['unlocked']:
                            ach.unlocked = True
                    self.game_data.update(data['game_data'])
            except (json.JSONDecodeError, KeyError):
                print("Файл достижений повреждён, создаём новый")
                self.save_progress()

    def save_progress(self):
        data = {
            'unlocked': [ach.id for ach in self.achievements if ach.unlocked],
            'game_data': self.game_data
        }
        with open('achievements.json', 'w') as f:
            json.dump(data, f, indent=2)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.game_data:
                if key == 'max_combo' and value > self.game_data[key]:
                    self.game_data[key] = value
                elif key == 'powerups_bought' and isinstance(value, list):
                    for item in value:
                        if item not in self.game_data[key]:
                            self.game_data[key].append(item)
                elif key != 'max_combo':
                    self.game_data[key] += value

        new_achievements = []
        for ach in self.achievements:
            if ach.check(self.game_data):
                new_achievements.append(ach)
                self.save_progress()

        return new_achievements

    def get_unlocked_count(self):
        return sum(1 for ach in self.achievements if ach.unlocked)

    def get_total_count(self):
        return len(self.achievements)


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.life = 30
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        return self.life > 0

    def draw(self, screen):
        alpha = self.life / 30
        color = (int(self.color[0] * alpha), int(self.color[1] * alpha), int(self.color[2] * alpha))
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 3)


class Console:
    def __init__(self, achievement_manager):
        self.active = False
        self.input_text = ""
        self.history = []
        self.font = pygame.font.Font(None, 28)
        self.achievement_manager = achievement_manager

    def toggle(self):
        self.active = not self.active
        if not self.active:
            self.input_text = ""

    def handle_event(self, event, radar):
        if not self.active:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.execute_command(radar)
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.toggle()
            else:
                self.input_text += event.unicode
        return True

    def execute_command(self, radar):
        if not self.input_text.startswith("?sudo"):
            self.history.append(f"Неизвестная команда: {self.input_text}")
            self.input_text = ""
            return

        command = self.input_text[5:].strip().lower()
        self.history.append(f"> {self.input_text}")

        # Ачивка за использование консоли
        if self.achievement_manager and not self.achievement_manager.game_data['console_used']:
            self.achievement_manager.update(console_used=True)
            self.history.append("Достижение разблокировано: Хакер!")

        if command == "time stop":
            radar.slow_motion = True
            radar.slow_motion_end = pygame.time.get_ticks() + 30000
            self.history.append("Время остановлено на 30 секунд!")

        elif command.startswith("set money"):
            try:
                amount = int(command.split()[2])
                radar.shop_points = amount
                self.history.append(f"Монет установлено: {amount}")
            except:
                self.history.append("Ошибка! Используйте: ?sudo set money (число)")

        elif command.startswith("set level"):
            try:
                amount = int(command.split()[2])
                radar.level = amount
                radar.difficulty_settings = radar.get_difficulty_settings()
                radar.number_of_targets = radar.difficulty_settings['targets_count']
                self.history.append(f"Уровень установлен: {amount}")
            except:
                self.history.append("Ошибка! Используйте: ?sudo set level (число)")

        elif command == "help":
            self.history.append("Доступные команды:")
            self.history.append("  ?sudo time stop - остановить время на 30 сек")
            self.history.append("  ?sudo set money (число) - установить монеты")
            self.history.append("  ?sudo set level (число) - установить уровень")
            self.history.append("  ?sudo help - показать эту справку")

        else:
            self.history.append(f"Неизвестная sudo-команда: {command}")

        self.input_text = ""

    def draw(self, screen):
        if not self.active:
            return

        overlay = pygame.Surface((WIDTH, 200))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, HEIGHT - 200))

        pygame.draw.rect(screen, RADAR_GREEN, (0, HEIGHT - 200, WIDTH, 200), 2)

        y_offset = HEIGHT - 180
        for line in self.history[-5:]:
            text = self.font.render(line, True, WHITE)
            screen.blit(text, (10, y_offset))
            y_offset += 25

        input_display = f"$ {self.input_text}_"
        input_text = self.font.render(input_display, True, GOLD)
        screen.blit(input_text, (10, HEIGHT - 30))


class Target:
    def __init__(self, pos, spawn_time, target_type, difficulty_settings, is_golden=False, is_purple=False,
                 is_black=False):
        self.pos = pos
        self.radius = 12
        self.active = True
        self.spawn_time = spawn_time
        self.detected = False
        self.detected_time = None
        self.target_type = target_type
        self.difficulty_settings = difficulty_settings
        # Для чёрных целей время увеличено
        if is_black:
            if difficulty_settings['name'] == 'средний':
                self.life_time = 5000  # 5 секунд для среднего
            else:
                self.life_time = 6000  # 6 секунд для остальных
        else:
            self.life_time = difficulty_settings['life_time']
        self.text_color = TEXT_COLORS[difficulty_settings['name']]
        self.clicked = False
        self.is_golden = is_golden
        self.is_purple = is_purple
        self.is_black = is_black
        self.hits_remaining = 2 if is_purple else (10 if is_black else 0)
        self.kill_time = None

        # Для зелёных целей: маскировка под красную после обнаружения
        self.fake_red_end_time = None
        self.is_fake_red = False

        # Для босса: увеличенный радиус
        if self.is_black:
            self.radius = 24

        self.hit_particles_timer = 0

    def detect(self, current_time):
        if not self.detected and self.active:
            self.detected = True
            self.detected_time = current_time

            if self.target_type == 'green':
                self.is_fake_red = True
                self.fake_red_end_time = current_time + 500

            return True
        return False

    def update(self, current_time):
        if self.is_fake_red and self.target_type == 'green':
            if current_time >= self.fake_red_end_time:
                self.is_fake_red = False

        if self.detected and self.active and not self.clicked:
            if current_time - self.detected_time > self.life_time:
                self.active = False
                return False
        return True

    def click(self):
        if not self.clicked and self.active:
            self.clicked = True
            self.active = False
            self.kill_time = pygame.time.get_ticks()
            return True
        return False

    def hit(self, current_time):
        if not self.active or not self.detected or self.clicked:
            return False

        self.hits_remaining -= 1
        self.hit_particles_timer = current_time

        if self.hits_remaining <= 0:
            self.clicked = True
            self.active = False
            self.kill_time = current_time
            return True

        if self.is_purple:
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(30, 80)
            new_x = self.pos[0] + math.cos(angle) * distance
            new_y = self.pos[1] + math.sin(angle) * distance

            dx = new_x - CENTER[0]
            dy = new_y - CENTER[1]
            dist_to_center = math.sqrt(dx * dx + dy * dy)
            if dist_to_center > RADAR_RADIUS - self.radius:
                new_x = CENTER[0] + (dx / dist_to_center) * (RADAR_RADIUS - self.radius - 5)
                new_y = CENTER[1] + (dy / dist_to_center) * (RADAR_RADIUS - self.radius - 5)

            self.pos = (new_x, new_y)

        return False

    def draw(self, screen, current_time):
        if not self.active or not self.detected or self.clicked:
            return

        if self.hit_particles_timer and current_time - self.hit_particles_timer < 200:
            flash_alpha = 1 - (current_time - self.hit_particles_timer) / 200
            flash_color = WHITE
            flash_radius = self.radius + 5
            pygame.draw.circle(screen, flash_color, (int(self.pos[0]), int(self.pos[1])), flash_radius, 3)

        if self.is_golden:
            blink_speed = 60
            blink = (pygame.time.get_ticks() // blink_speed) % 2
            if blink:
                color = GOLD
            else:
                color = (255, 200, 0)
            timer_color = GOLD
            show_cross = False
            show_green_dot = False
            show_white_border = True
        elif self.is_purple:
            color = PURPLE
            timer_color = PURPLE
            show_cross = False
            show_green_dot = False
            show_white_border = True
        elif self.is_black:
            blink_speed = 200
            blink = (pygame.time.get_ticks() // blink_speed) % 2
            if blink:
                color = (50, 50, 50)
            else:
                color = (20, 20, 20)
            timer_color = DARK_RED
            show_cross = False
            show_green_dot = False
            show_white_border = True
        elif self.target_type == 'red':
            blink_speed = 80
            blink = (pygame.time.get_ticks() // blink_speed) % 2
            if blink:
                color = (255, 50, 50)
            else:
                color = (200, 0, 0)
            timer_color = self.text_color
            show_cross = False
            show_green_dot = False
            show_white_border = True
        else:
            if self.is_fake_red:
                blink_speed = 80
                blink = (pygame.time.get_ticks() // blink_speed) % 2
                if blink:
                    color = (255, 50, 50)
                else:
                    color = (200, 0, 0)
                timer_color = self.text_color
                show_cross = False
                show_green_dot = True
                show_white_border = True
            else:
                blink_speed = 120
                blink = (pygame.time.get_ticks() // blink_speed) % 2
                if blink:
                    color = (0, 255, 0)
                else:
                    color = (0, 150, 0)
                timer_color = (0, 255, 0)
                show_cross = True
                show_green_dot = False
                show_white_border = False

        time_left = max(0, self.life_time - (current_time - self.detected_time))
        if time_left > 0:
            progress = time_left / self.life_time
            angle = 360 * progress

            for i in range(int(angle)):
                rad = math.radians(i)
                x = self.pos[0] + (self.radius + 5) * math.cos(rad)
                y = self.pos[1] + (self.radius + 5) * math.sin(rad)
                pygame.draw.circle(screen, timer_color, (int(x), int(y)), 1)

        pygame.draw.circle(screen, color, (int(self.pos[0]), int(self.pos[1])), self.radius)

        if show_green_dot:
            pygame.draw.circle(screen, (0, 255, 0), (int(self.pos[0]), int(self.pos[1])), 4)

        if show_cross:
            cross_size = self.radius - 4
            pygame.draw.line(screen, BLACK,
                             (self.pos[0] - cross_size, self.pos[1]),
                             (self.pos[0] + cross_size, self.pos[1]), 2)
            pygame.draw.line(screen, BLACK,
                             (self.pos[0], self.pos[1] - cross_size),
                             (self.pos[0], self.pos[1] + cross_size), 2)

        if show_white_border:
            pygame.draw.circle(screen, WHITE, (int(self.pos[0]), int(self.pos[1])), self.radius - 3, 2)

        if (self.is_purple or self.is_black) and self.hits_remaining > 0:
            hits_text = pygame.font.Font(None, 20).render(str(self.hits_remaining), True, WHITE)
            hits_rect = hits_text.get_rect(center=(self.pos[0], self.pos[1]))
            screen.blit(hits_text, hits_rect)


class Radar:
    def __init__(self, difficulty='средний', survival_mode=False, experimental_mode=False, achievement_manager=None):
        self.difficulty = difficulty
        self.survival_mode = survival_mode
        self.experimental_mode = experimental_mode
        self.achievement_manager = achievement_manager
        self.level = 1
        self.rotations = 0
        self.angle = 0
        self.targets = []
        self.score = 0
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.shop_points = 0
        self.particles = []
        self.combo = 0
        self.total_kills = 0
        self.golden_kills = 0
        self.purple_kills = 0
        self.black_kills = 0
        self.fast_kills = 0

        self.slow_motion = False
        self.slow_motion_end = 0
        self.double_points = False
        self.double_points_end = 0
        self.reveal_all = False
        self.reveal_all_end = 0

        self.high_scores = self.load_high_scores()
        self.console = Console(achievement_manager) if achievement_manager else None
        self.exit_button = pygame.Rect(WIDTH - 50, 10, 40, 40)

        self.difficulty_settings = self.get_difficulty_settings()
        self.number_of_targets = self.difficulty_settings['targets_count']

        self.generate_all_targets()

    def get_difficulty_settings(self):
        base_settings = {
            'щадящий': {
                'name': 'щадящий',
                'base_life_time': 3000,
                'base_targets_count': 2,
                'radar_speed': 0.6,
                'green_chance': 0.15,
                'purple_chance': 0.05,
                'black_chance': 0.05,
                'score_red': 1,
                'penalty_miss': 1,
                'penalty_green': 1
            },
            'лёгкий': {
                'name': 'лёгкий',
                'base_life_time': 2500,
                'base_targets_count': 2,
                'radar_speed': 0.8,
                'green_chance': 0.25,
                'purple_chance': 0.08,
                'black_chance': 0.05,
                'score_red': 1,
                'penalty_miss': 1,
                'penalty_green': 1
            },
            'средний': {
                'name': 'средний',
                'base_life_time': 2000,
                'base_targets_count': 3,
                'radar_speed': 1.0,
                'green_chance': 0.35,
                'purple_chance': 0.1,
                'black_chance': 0.05,
                'score_red': 1,
                'penalty_miss': 1,
                'penalty_green': 2
            },
            'сложный': {
                'name': 'сложный',
                'base_life_time': 1500,
                'base_targets_count': 3,
                'radar_speed': 1.2,
                'green_chance': 0.45,
                'purple_chance': 0.12,
                'black_chance': 0.05,
                'score_red': 1,
                'penalty_miss': 1,
                'penalty_green': 2
            },
            'extreme': {
                'name': 'extreme',
                'base_life_time': 1000,
                'base_targets_count': 4,
                'radar_speed': 1.5,
                'green_chance': 0.55,
                'purple_chance': 0.15,
                'black_chance': 0.05,
                'score_red': 1,
                'penalty_miss': 2,
                'penalty_green': 3
            }
        }

        settings = base_settings[self.difficulty].copy()

        level_multiplier = 1 + (self.level - 1) * 0.1
        settings['life_time'] = int(settings['base_life_time'] / level_multiplier)
        settings['targets_count'] = min(6, settings['base_targets_count'] + (self.level // 3))
        settings['radar_speed'] = settings['radar_speed'] * level_multiplier

        if self.experimental_mode:
            settings['green_chance'] = 0

        return settings

    def load_high_scores(self):
        if os.path.exists('high_scores.json'):
            try:
                with open('high_scores.json', 'r') as f:
                    return json.load(f)
            except:
                return {'щадящий': 0, 'лёгкий': 0, 'средний': 0, 'сложный': 0, 'extreme': 0, 'survival': 0,
                        'experimental': 0}
        return {'щадящий': 0, 'лёгкий': 0, 'средний': 0, 'сложный': 0, 'extreme': 0, 'survival': 0, 'experimental': 0}

    def save_high_scores(self):
        with open('high_scores.json', 'w') as f:
            json.dump(self.high_scores, f)

    def update_high_score(self):
        if self.experimental_mode:
            key = 'experimental'
        elif self.survival_mode:
            key = 'survival'
        else:
            key = self.difficulty

        if self.score > self.high_scores[key]:
            self.high_scores[key] = self.score
            self.save_high_scores()
            if self.achievement_manager:
                self.achievement_manager.update(record_broken=True)
            return True
        return False

    def generate_all_targets(self):
        active_targets = [t for t in self.targets if t.active]

        if len(active_targets) < self.number_of_targets:
            needed = self.number_of_targets - len(active_targets)

            for i in range(needed):
                distance = random.uniform(80, RADAR_RADIUS - 40)
                angle = random.uniform(0, 2 * math.pi)

                x = CENTER[0] + distance * math.cos(angle)
                y = CENTER[1] + distance * math.sin(angle)

                # Шанс золотой цели 1%
                is_golden = random.random() < 0.01

                if is_golden:
                    self.targets.append(Target((x, y), pygame.time.get_ticks(),
                                               'golden', self.difficulty_settings,
                                               is_golden=True, is_purple=False, is_black=False))
                else:
                    if self.experimental_mode:
                        rand = random.random()
                        purple_chance = self.difficulty_settings['purple_chance']
                        black_chance = self.difficulty_settings['black_chance']

                        if rand < black_chance:
                            self.targets.append(Target((x, y), pygame.time.get_ticks(),
                                                       'black', self.difficulty_settings,
                                                       is_golden=False, is_purple=False, is_black=True))
                        elif rand < black_chance + purple_chance:
                            self.targets.append(Target((x, y), pygame.time.get_ticks(),
                                                       'purple', self.difficulty_settings,
                                                       is_golden=False, is_purple=True, is_black=False))
                        else:
                            self.targets.append(Target((x, y), pygame.time.get_ticks(),
                                                       'red', self.difficulty_settings,
                                                       is_golden=False, is_purple=False, is_black=False))
                    else:
                        if random.random() < self.difficulty_settings['green_chance']:
                            self.targets.append(Target((x, y), pygame.time.get_ticks(),
                                                       'green', self.difficulty_settings,
                                                       is_golden=False, is_purple=False, is_black=False))
                        else:
                            self.targets.append(Target((x, y), pygame.time.get_ticks(),
                                                       'red', self.difficulty_settings,
                                                       is_golden=False, is_purple=False, is_black=False))

    def add_particles(self, x, y, color, count=10):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def check_radar_detection(self, current_time):
        rad = math.radians(self.angle)
        direction = (math.cos(rad), math.sin(rad))

        for target in self.targets:
            if target.active and not target.detected:
                if self.reveal_all:
                    target.detect(current_time)
                else:
                    to_target = (target.pos[0] - CENTER[0], target.pos[1] - CENTER[1])
                    target_distance = math.sqrt(to_target[0] ** 2 + to_target[1] ** 2)

                    if target_distance > 0:
                        to_target_norm = (to_target[0] / target_distance, to_target[1] / target_distance)
                        dot_product = direction[0] * to_target_norm[0] + direction[1] * to_target_norm[1]
                        dot_product = max(-1, min(1, dot_product))
                        angle_diff = math.degrees(math.acos(dot_product))

                        if angle_diff < 5:
                            target.detect(current_time)

    def draw_radar_grid(self, screen):
        pygame.draw.circle(screen, RADAR_DARK_GREEN, CENTER, RADAR_RADIUS, 3)
        pygame.draw.circle(screen, RADAR_GREEN, CENTER, RADAR_RADIUS, 1)

        for r in range(100, RADAR_RADIUS, 100):
            pygame.draw.circle(screen, RADAR_DARK_GREEN, CENTER, r, 1)

        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x = CENTER[0] + RADAR_RADIUS * math.cos(rad)
            y = CENTER[1] + RADAR_RADIUS * math.sin(rad)
            pygame.draw.line(screen, RADAR_DARK_GREEN, CENTER, (x, y), 1)

        pygame.draw.circle(screen, RADAR_GREEN, CENTER, 5)
        pygame.draw.circle(screen, WHITE, CENTER, 2)

    def draw_scan_line(self, screen):
        speed = self.difficulty_settings['radar_speed']
        if self.slow_motion:
            speed = speed * 0.5

        rad = math.radians(self.angle)
        x = CENTER[0] + RADAR_RADIUS * math.cos(rad)
        y = CENTER[1] + RADAR_RADIUS * math.sin(rad)
        pygame.draw.line(screen, RADAR_GREEN, CENTER, (x, y), 3)

        for i in range(1, 4):
            trail_angle = self.angle - i * 2
            trail_rad = math.radians(trail_angle)
            trail_x = CENTER[0] + RADAR_RADIUS * math.cos(trail_rad)
            trail_y = CENTER[1] + RADAR_RADIUS * math.sin(trail_rad)
            alpha = 200 - i * 50
            color = (0, alpha, 0)
            pygame.draw.line(screen, color, CENTER, (trail_x, trail_y), 2)

        front_angle = self.angle + 3
        front_rad = math.radians(front_angle)
        front_x = CENTER[0] + RADAR_RADIUS * math.cos(front_rad)
        front_y = CENTER[1] + RADAR_RADIUS * math.sin(front_rad)
        pygame.draw.line(screen, (0, 255, 0, 100), CENTER, (front_x, front_y), 1)

    def update_scan(self):
        speed = self.difficulty_settings['radar_speed']
        if self.slow_motion:
            speed = speed * 0.5

        self.angle += speed
        if self.angle >= 360:
            self.angle = 0
            self.rotations += 1
            self.generate_all_targets()

            if self.rotations % 5 == 0:
                self.level += 1
                # Обновляем достижения по уровням
                if self.achievement_manager:
                    current_max = self.achievement_manager.game_data['highest_difficulty_level'][self.difficulty]
                    if self.level > current_max:
                        self.achievement_manager.game_data['highest_difficulty_level'][self.difficulty] = self.level
                        self.achievement_manager.save_progress()

                self.difficulty_settings = self.get_difficulty_settings()
                self.number_of_targets = self.difficulty_settings['targets_count']
                if self.level % 3 == 0:
                    return "shop"
        return None

    def update_targets(self, current_time):
        active_targets = []
        for target in self.targets:
            if target.update(current_time):
                active_targets.append(target)
            else:
                if target.target_type == 'red' and not target.clicked:
                    self.score -= self.difficulty_settings['penalty_miss']
                    self.combo = 0
                elif target.target_type == 'green' and not target.clicked and not self.experimental_mode:
                    self.score -= self.difficulty_settings['penalty_miss']
                    self.combo = 0

        self.targets = active_targets

        active_count = len([t for t in self.targets if t.active])
        if active_count < self.number_of_targets:
            self.generate_all_targets()

        self.particles = [p for p in self.particles if p.update()]
        for p in self.particles:
            p.draw(screen)

        if self.slow_motion and current_time > self.slow_motion_end:
            self.slow_motion = False
        if self.double_points and current_time > self.double_points_end:
            self.double_points = False
        if self.reveal_all and current_time > self.reveal_all_end:
            self.reveal_all = False

    def check_click(self, mouse_pos, current_time):
        for target in self.targets:
            if target.active and target.detected and not target.clicked:
                dx = mouse_pos[0] - target.pos[0]
                dy = mouse_pos[1] - target.pos[1]
                distance = math.sqrt(dx * dx + dy * dy)

                if distance <= target.radius + 5:
                    if target.is_purple or target.is_black:
                        destroyed = target.hit(current_time)
                        if destroyed:
                            if target.is_purple:
                                self.shop_points += 2
                                self.purple_kills += 1
                                self.add_particles(target.pos[0], target.pos[1], PURPLE, 15)
                                if self.achievement_manager:
                                    self.achievement_manager.update(purple_kills=1)
                            elif target.is_black:
                                self.score += 5
                                self.shop_points += 10
                                self.black_kills += 1
                                self.add_particles(target.pos[0], target.pos[1], DARK_RED, 20)
                                if self.achievement_manager:
                                    self.achievement_manager.update(black_kills=1)
                            self.total_kills += 1
                            self.combo += 1
                            if self.achievement_manager:
                                self.achievement_manager.update(total_kills=1, max_combo=self.combo)
                        else:
                            self.add_particles(target.pos[0], target.pos[1], WHITE, 5)
                        return True, False  # (уничтожена, выход_в_меню)
                    else:
                        if target.click():
                            points = 0
                            if target.is_golden:
                                points = 50
                                self.score += points
                                self.golden_kills += 1
                                self.add_particles(target.pos[0], target.pos[1], GOLD)
                                if self.achievement_manager:
                                    self.achievement_manager.update(golden_kills=1)
                            elif target.target_type == 'red':
                                points = self.difficulty_settings['score_red']
                                if self.double_points:
                                    points *= 2
                                self.score += points
                                self.add_particles(target.pos[0], target.pos[1], (255, 0, 0))
                            elif target.target_type == 'green':
                                points = -self.difficulty_settings['penalty_green']
                                self.score += points
                                self.combo = 0
                                self.add_particles(target.pos[0], target.pos[1], (0, 255, 0))

                            self.total_kills += 1
                            self.combo += 1

                            # Проверка на быструю реакцию
                            if target.detected_time and (current_time - target.detected_time) < 500:
                                self.fast_kills += 1
                                if self.achievement_manager:
                                    self.achievement_manager.update(fast_kills=1)

                            if points > 0:
                                self.shop_points += points

                            if self.achievement_manager:
                                self.achievement_manager.update(total_kills=1, max_combo=self.combo)

                            return True, False
        return False, False

    def draw_score(self, screen):
        text_color = TEXT_COLORS[self.difficulty]
        score_color = text_color if self.score >= 0 else DARK_RED
        score_text = self.font.render(f"Счёт: {self.score}", True, score_color)
        score_rect = score_text.get_rect()
        score_rect.topright = (WIDTH - 60, 20)

        pygame.draw.rect(screen, BLACK, (score_rect.x - 10, score_rect.y - 5,
                                         score_rect.width + 20, score_rect.height + 10))
        pygame.draw.rect(screen, text_color, (score_rect.x - 10, score_rect.y - 5,
                                              score_rect.width + 20, score_rect.height + 10), 2)

        screen.blit(score_text, score_rect)

        # Кнопка выхода
        pygame.draw.rect(screen, DARK_RED, self.exit_button)
        pygame.draw.rect(screen, WHITE, self.exit_button, 2)
        exit_text = self.font.render("X", True, WHITE)
        exit_text_rect = exit_text.get_rect(center=self.exit_button.center)
        screen.blit(exit_text, exit_text_rect)

        level_text = self.small_font.render(f"Уровень: {self.level}", True, WHITE)
        screen.blit(level_text, (20, 20))

        shop_text = self.small_font.render(f"Монеты: {self.shop_points}", True, GOLD)
        screen.blit(shop_text, (20, 50))

        combo_text = self.small_font.render(f"Комбо: {self.combo}", True, WHITE)
        screen.blit(combo_text, (20, 80))

        y_offset = 110
        if self.slow_motion:
            slow_text = self.small_font.render("ЗАМЕДЛЕНИЕ!", True, (100, 200, 255))
            screen.blit(slow_text, (20, y_offset))
            y_offset += 25
        if self.double_points:
            double_text = self.small_font.render("УДВОЕНИЕ ОЧКОВ!", True, GOLD)
            screen.blit(double_text, (20, y_offset))
            y_offset += 25
        if self.reveal_all:
            reveal_text = self.small_font.render("ПОДСВЕТКА ЦЕЛЕЙ!", True, (255, 255, 100))
            screen.blit(reveal_text, (20, y_offset))

        console_hint = self.small_font.render("Нажми ` для открытия консоли", True, GRAY)
        screen.blit(console_hint, (WIDTH - 220, HEIGHT - 30))

    def draw_info(self, screen):
        pass

    def show_shop(self):
        shop_items = [
            {"name": "Замедление времени", "cost": 50, "effect": "slow", "type": "slow"},
            {"name": "Удвоение очков", "cost": 75, "effect": "double", "type": "double"},
            {"name": "Подсветка целей", "cost": 100, "effect": "reveal", "type": "reveal"}
        ]

        shop_running = True
        while shop_running:
            screen.fill(BLACK)

            title = self.font.render("МАГАЗИН", True, GOLD)
            title_rect = title.get_rect(center=(WIDTH // 2, 60))
            screen.blit(title, title_rect)

            coins_text = self.small_font.render(f"Монет: {self.shop_points}", True, GOLD)
            coins_rect = coins_text.get_rect(center=(WIDTH // 2, 110))
            screen.blit(coins_text, coins_rect)

            buttons = []
            for i, item in enumerate(shop_items):
                y = 180 + i * 80
                button_rect = pygame.Rect(WIDTH // 2 - 150, y, 300, 60)

                color = (50, 50, 50) if self.shop_points < item["cost"] else TEXT_COLORS[self.difficulty]
                pygame.draw.rect(screen, color, button_rect)
                pygame.draw.rect(screen, WHITE, button_rect, 2)

                text = self.small_font.render(f"{item['name']} - {item['cost']} монет", True, WHITE)
                text_rect = text.get_rect(center=button_rect.center)
                screen.blit(text, text_rect)

                buttons.append((button_rect, item))

            exit_button = pygame.Rect(WIDTH // 2 - 100, 500, 200, 50)
            pygame.draw.rect(screen, RADAR_GREEN, exit_button)
            pygame.draw.rect(screen, WHITE, exit_button, 2)
            exit_text = self.small_font.render("ВЫЙТИ", True, BLACK)
            exit_text_rect = exit_text.get_rect(center=exit_button.center)
            screen.blit(exit_text, exit_text_rect)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if exit_button.collidepoint(event.pos):
                        shop_running = False

                    for button_rect, item in buttons:
                        if button_rect.collidepoint(event.pos) and self.shop_points >= item["cost"]:
                            self.shop_points -= item["cost"]
                            current_time = pygame.time.get_ticks()

                            # Ачивка за покупку в магазине
                            if self.achievement_manager:
                                self.achievement_manager.update(shop_items_bought=1)
                                if item["type"] not in self.achievement_manager.game_data['powerups_bought']:
                                    self.achievement_manager.game_data['powerups_bought'].append(item["type"])
                                    self.achievement_manager.save_progress()

                            if item["effect"] == "slow":
                                self.slow_motion = True
                                self.slow_motion_end = current_time + 10000
                            elif item["effect"] == "double":
                                self.double_points = True
                                self.double_points_end = current_time + 10000
                            elif item["effect"] == "reveal":
                                self.reveal_all = True
                                self.reveal_all_end = current_time + 5000

                            shop_running = False

            pygame.display.flip()
            clock.tick(60)

        return True


class AchievementsMenu:
    def __init__(self, achievement_manager):
        self.achievement_manager = achievement_manager
        self.scroll_offset = 0
        self.scroll_speed = 30
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        self.running = True

    def run(self):
        self.running = True
        while self.running:
            screen.fill(BLACK)

            title = self.title_font.render("ДОСТИЖЕНИЯ", True, GOLD)
            title_rect = title.get_rect(center=(WIDTH // 2, 40))
            screen.blit(title, title_rect)

            progress_text = self.font.render(
                f"Прогресс: {self.achievement_manager.get_unlocked_count()}/{self.achievement_manager.get_total_count()}",
                True, WHITE)
            progress_rect = progress_text.get_rect(center=(WIDTH // 2, 80))
            screen.blit(progress_text, progress_rect)

            # Отображение списка достижений с прокруткой
            y_offset = 120 - self.scroll_offset
            for ach in self.achievement_manager.achievements:
                if y_offset > 100 and y_offset < HEIGHT - 50:
                    color = GOLD if ach.unlocked else GRAY
                    name_text = self.font.render(ach.name, True, color)
                    screen.blit(name_text, (50, y_offset))

                    desc_text = self.font.render(ach.description, True, WHITE)
                    screen.blit(desc_text, (250, y_offset))

                    status = "✓" if ach.unlocked else "○"
                    status_text = self.font.render(status, True, color)
                    screen.blit(status_text, (20, y_offset))

                y_offset += 35

            # Инструкция по прокрутке
            scroll_hint = self.font.render("Используйте колесо мыши для прокрутки | ESC для выхода", True, GRAY)
            scroll_hint_rect = scroll_hint.get_rect(center=(WIDTH // 2, HEIGHT - 30))
            screen.blit(scroll_hint, scroll_hint_rect)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                elif event.type == pygame.MOUSEWHEEL:
                    self.scroll_offset -= event.y * self.scroll_speed
                    self.scroll_offset = max(0, min(self.scroll_offset,
                                                    len(self.achievement_manager.achievements) * 35 - 500))

            pygame.display.flip()
            clock.tick(60)

        return True


class Menu:
    def __init__(self):
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 32)
        self.selected_difficulty = 'средний'
        self.survival_mode = False
        self.experimental_mode = False
        self.running = True
        self.achievement_manager = AchievementManager()

        self.difficulties = ['щадящий', 'лёгкий', 'средний', 'сложный', 'extreme']
        self.high_scores = self.load_high_scores()

    def load_high_scores(self):
        if os.path.exists('high_scores.json'):
            try:
                with open('high_scores.json', 'r') as f:
                    return json.load(f)
            except:
                return {'щадящий': 0, 'лёгкий': 0, 'средний': 0, 'сложный': 0, 'extreme': 0, 'survival': 0,
                        'experimental': 0}
        return {'щадящий': 0, 'лёгкий': 0, 'средний': 0, 'сложный': 0, 'extreme': 0, 'survival': 0, 'experimental': 0}

    def draw_button(self, text, x, y, width, height, color, is_selected=False):
        button_rect = pygame.Rect(x, y, width, height)

        if is_selected:
            button_color = color
            border_color = WHITE
            border_width = 3
        else:
            button_color = (max(0, color[0] // 3), max(0, color[1] // 3), max(0, color[2] // 3))
            border_color = GRAY
            border_width = 2

        pygame.draw.rect(screen, button_color, button_rect)
        pygame.draw.rect(screen, border_color, button_rect, border_width)

        text_surface = self.small_font.render(text, True, WHITE)
        text_rect = text_surface.get_rect(center=button_rect.center)
        screen.blit(text_surface, text_rect)

        return button_rect

    def run(self):
        while self.running:
            screen.fill(BLACK)

            title = self.font.render("РАДАР - ОХОТА НА ЦЕЛИ", True, RADAR_GREEN)
            title_rect = title.get_rect(center=(WIDTH // 2, 30))
            screen.blit(title, title_rect)

            if self.experimental_mode:
                record_key = 'experimental'
            elif self.survival_mode:
                record_key = 'survival'
            else:
                record_key = self.selected_difficulty

            high_score_text = self.small_font.render(f"Рекорд: {self.high_scores[record_key]}", True, GOLD)
            high_score_rect = high_score_text.get_rect(center=(WIDTH // 2, 80))
            screen.blit(high_score_text, high_score_rect)

            # Кнопка достижений
            achievements_rect = pygame.Rect(WIDTH - 150, 10, 140, 40)
            pygame.draw.rect(screen, PURPLE, achievements_rect)
            pygame.draw.rect(screen, WHITE, achievements_rect, 2)
            achievements_text = self.small_font.render("ДОСТИЖЕНИЯ", True, WHITE)
            achievements_text_rect = achievements_text.get_rect(center=achievements_rect.center)
            screen.blit(achievements_text, achievements_text_rect)

            diff_title = self.small_font.render("ВЫБЕРИ СЛОЖНОСТЬ:", True, WHITE)
            diff_title_rect = diff_title.get_rect(center=(WIDTH // 2, 140))
            screen.blit(diff_title, diff_title_rect)

            button_width = 140
            button_height = 50
            start_x = WIDTH // 2 - (len(self.difficulties) * (button_width + 10)) // 2 + 5

            buttons = []
            for i, difficulty in enumerate(self.difficulties):
                x = start_x + i * (button_width + 10)
                y = 180
                color = TEXT_COLORS[difficulty]
                button_rect = self.draw_button(difficulty.capitalize(), x, y, button_width, button_height,
                                               color, self.selected_difficulty == difficulty)
                buttons.append((button_rect, difficulty))

            survival_rect = pygame.Rect(WIDTH // 2 - 220, 260, 200, 50)
            survival_color = (100, 200, 255) if self.survival_mode else (50, 50, 50)
            pygame.draw.rect(screen, survival_color, survival_rect)
            pygame.draw.rect(screen, WHITE, survival_rect, 2)
            survival_text = self.small_font.render("ВЫЖИВАНИЕ", True, WHITE)
            survival_text_rect = survival_text.get_rect(center=survival_rect.center)
            screen.blit(survival_text, survival_text_rect)

            experimental_rect = pygame.Rect(WIDTH // 2 + 20, 260, 200, 50)
            experimental_color = PURPLE if self.experimental_mode else (50, 50, 50)
            pygame.draw.rect(screen, experimental_color, experimental_rect)
            pygame.draw.rect(screen, WHITE, experimental_rect, 2)
            experimental_text = self.small_font.render("ЭКСПЕРИМЕНТАЛ", True, WHITE)
            experimental_text_rect = experimental_text.get_rect(center=experimental_rect.center)
            screen.blit(experimental_text, experimental_text_rect)

            start_button_rect = pygame.Rect(WIDTH // 2 - 100, 340, 200, 60)
            pygame.draw.rect(screen, RADAR_GREEN, start_button_rect)
            pygame.draw.rect(screen, WHITE, start_button_rect, 3)
            start_text = self.font.render("НАЧАТЬ ИГРУ", True, BLACK)
            start_text_rect = start_text.get_rect(center=start_button_rect.center)
            screen.blit(start_text, start_text_rect)

            inst_y = 430
            if self.experimental_mode:
                instructions = [
                    "ЭКСПЕРИМЕНТАЛЬНЫЙ РЕЖИМ:",
                    "Красные: обычные цели (+1 очко)",
                    "Фиолетовые: 2 удара, прыгают (+2 монеты)",
                    "Чёрные (боссы): 10 ударов (+5 очков, +10 монет)",
                    "Золотые: +50 очков (редко 1%)",
                    "Каждые 5 оборотов - новый уровень",
                    "Каждые 3 уровня - магазин"
                ]
            else:
                instructions = [
                    "ОБЫЧНЫЙ РЕЖИМ:",
                    "Красные цели: +1 очко",
                    "Зелёные цели: маскируются 0.5 сек (штраф)",
                    "Золотые цели: +50 очков (редко 1%)",
                    "Каждые 5 оборотов - новый уровень",
                    "Каждые 3 уровня - магазин"
                ]

            for i, line in enumerate(instructions):
                inst_text = self.small_font.render(line, True, WHITE)
                inst_rect = inst_text.get_rect(center=(WIDTH // 2, inst_y + i * 25))
                screen.blit(inst_text, inst_rect)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return None, None, None
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if achievements_rect.collidepoint(event.pos):
                        achievements_menu = AchievementsMenu(self.achievement_manager)
                        achievements_menu.run()
                    for button_rect, difficulty in buttons:
                        if button_rect.collidepoint(event.pos):
                            self.selected_difficulty = difficulty
                    if survival_rect.collidepoint(event.pos):
                        self.survival_mode = not self.survival_mode
                        if self.survival_mode:
                            self.experimental_mode = False
                    if experimental_rect.collidepoint(event.pos):
                        self.experimental_mode = not self.experimental_mode
                        if self.experimental_mode:
                            self.survival_mode = False
                    if start_button_rect.collidepoint(event.pos):
                        return self.selected_difficulty, self.survival_mode, self.experimental_mode

            pygame.display.flip()
            clock.tick(60)


def main():
    menu = Menu()
    difficulty, survival_mode, experimental_mode = menu.run()

    if difficulty is None:
        return

    radar = Radar(difficulty, survival_mode, experimental_mode, menu.achievement_manager)
    running = True
    game_over = False
    return_to_menu = False

    while running:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_BACKQUOTE and radar.console:
                    radar.console.toggle()
                elif event.key == pygame.K_r and game_over:
                    radar = Radar(difficulty, survival_mode, experimental_mode, menu.achievement_manager)
                    game_over = False

            if radar.console and radar.console.active:
                radar.console.handle_event(event, radar)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not game_over:
                    # Проверка нажатия на кнопку выхода
                    if radar.exit_button.collidepoint(event.pos):
                        return_to_menu = True
                        running = False
                    else:
                        radar.check_click(event.pos, current_time)

        if return_to_menu:
            break

        screen.fill(BLACK)

        radar.draw_radar_grid(screen)

        radar.update_targets(current_time)
        for target in radar.targets:
            target.draw(screen, current_time)

        radar.draw_scan_line(screen)
        radar.check_radar_detection(current_time)

        radar.draw_score(screen)

        if radar.console:
            radar.console.draw(screen)

        shop_result = radar.update_scan()
        if shop_result == "shop":
            if not radar.show_shop():
                running = False

        # Обновление очков выживания для ачивок
        if survival_mode and menu.achievement_manager:
            if radar.score > menu.achievement_manager.game_data['survival_score']:
                menu.achievement_manager.game_data['survival_score'] = radar.score
                menu.achievement_manager.save_progress()

        if (survival_mode or experimental_mode) and radar.score < 0:
            game_over = True

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))

            game_over_text = radar.font.render("GAME OVER", True, DARK_RED)
            game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            screen.blit(game_over_text, game_over_rect)

            score_text = radar.small_font.render(f"Ваш счёт: {radar.score}", True, WHITE)
            score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(score_text, score_rect)

            new_record = radar.update_high_score()
            if new_record:
                record_text = radar.small_font.render("НОВЫЙ РЕКОРД!", True, GOLD)
                record_rect = record_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
                screen.blit(record_text, record_rect)

            restart_text = radar.small_font.render("Нажми R для рестарта или ESC для выхода", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120))
            screen.blit(restart_text, restart_rect)

        pygame.display.flip()
        clock.tick(60)

    # Если вышли через кнопку, запускаем меню заново
    if return_to_menu:
        main()
    else:
        pygame.quit()


if __name__ == "__main__":
    main()