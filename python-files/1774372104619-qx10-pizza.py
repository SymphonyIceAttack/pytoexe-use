import pygame
import random
import sys
import math
import ctypes

# --- Инициализация ---
pygame.init()
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Neon Pizza Lab: Infinite Edition")

# --- Цвета ---
BG_COLOR = (5, 5, 12)
PANEL_COLOR = (25, 25, 45)
TEXT_COLOR = (0, 255, 255)
MONEY_COLOR = (50, 255, 50)
DANGER_COLOR = (255, 50, 50)
SAUCE_COLOR = (180, 20, 20)
CHEESE_COLOR = (255, 230, 100)
PEPPERONI_COLOR = (130, 10, 10)
COLA_COLOR = (60, 30, 20)

# Шрифты
FONT_L = pygame.font.SysFont('Consolas', 40, bold=True)
FONT_M = pygame.font.SysFont('Consolas', 22)
FONT_S = pygame.font.SysFont('Consolas', 16)

class Pizza:
    def __init__(self):
        self.sauce_level = 0
        self.cheese_level = 0
        self.peps = []
        self.bake_level = 0
        self.in_oven = False
        self.soda_filled = 0
        self.dough_color = [235, 210, 170]

class Customer:
    def __init__(self):
        phrases = [
            ("Пиццу со всем и Колу!", True, True, 12, True),
            ("Просто сырную. Без напитка.", False, True, 0, False),
            ("Много пепперони и соус.", True, False, 16, False),
            ("Лепешку с соусом и Колу.", True, False, 0, True)
        ]
        chosen = random.choice(phrases)
        self.text = chosen[0]
        self.patience = 100.0

    def update(self):
        self.patience -= 0.04

class GameData:
    def __init__(self):
        self.reset_game()

    def reset_game(self):
        self.money = 100.0
        self.day = 1
        self.max_days = 10
        self.game_phase = "morning"
        self.current_customer = None
        self.pizza = None
        self.selected_slot = None
        self.wait_start_time = 0
        self.wait_duration = 0
        self.pizzas_made_today = 0 # Считаем для завершения дня

    def next_customer_logic(self):
        self.game_phase = "waiting_customer"
        self.wait_start_time = pygame.time.get_ticks()
        self.wait_duration = random.choice([3000, 5000, 10000])

def draw_bar(surf, x, y, w, h, progress, color, label=""):
    pygame.draw.rect(surf, (40, 40, 50), (x, y, w, h), border_radius=4)
    pygame.draw.rect(surf, color, (x, y, w * (min(progress, 100)/100), h), border_radius=4)
    if label:
        txt = FONT_S.render(label, True, (255, 255, 255))
        surf.blit(txt, (x + w//2 - txt.get_width()//2, y - 18))

game = GameData()
clock = pygame.time.Clock()

while True:
    W, H = screen.get_size()
    screen.fill(BG_COLOR)
    mx, my = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    now = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

    # --- 1. УТРО ---
    if game.game_phase == "morning":
        txt = FONT_L.render(f"ДЕНЬ {game.day}", True, TEXT_COLOR)
        screen.blit(txt, (W//2 - txt.get_width()//2, H//2 - 100))
        btn = pygame.Rect(W//2 - 125, H//2, 250, 60)
        pygame.draw.rect(screen, (0, 100, 200), btn, border_radius=10)
        screen.blit(FONT_M.render("НАЧАТЬ СМЕНУ", True, (255,255,255)), (btn.centerx - 70, btn.centery - 10))
        if event.type == pygame.MOUSEBUTTONDOWN and btn.collidepoint(mx, my):
            game.pizzas_made_today = 0
            game.next_customer_logic()

    # --- 2. ОЖИДАНИЕ КЛИЕНТА ---
    elif game.game_phase == "waiting_customer":
        screen.blit(FONT_M.render("Ждем клиента...", True, (100, 100, 100)), (W//2-80, H//2))
        if now - game.wait_start_time > game.wait_duration:
            game.current_customer = Customer()
            game.game_phase = "order_choice"

    # --- 3. ВЫБОР ЗАКАЗА ---
    elif game.game_phase == "order_choice":
        pygame.draw.rect(screen, PANEL_COLOR, (W//2-300, H//2-100, 600, 200), border_radius=15)
        screen.blit(FONT_M.render(f"ЗАКАЗ: {game.current_customer.text}", True, TEXT_COLOR), (W//2-250, H//2-60))
        btn_y, btn_n = pygame.Rect(W//2-200, H//2+20, 150, 50), pygame.Rect(W//2+50, H//2+20, 150, 50)
        pygame.draw.rect(screen, (0, 150, 0), btn_y, border_radius=8)
        pygame.draw.rect(screen, (150, 0, 0), btn_n, border_radius=8)
        screen.blit(FONT_M.render("ПРИНЯТЬ", True, (255,255,255)), (btn_y.x+40, btn_y.y+15))
        screen.blit(FONT_M.render("ОТКАЗАТЬ", True, (255,255,255)), (btn_n.x+35, btn_n.y+15))
        if event.type == pygame.MOUSEBUTTONDOWN:
            if btn_y.collidepoint(mx, my):
                game.pizza = Pizza(); game.game_phase = "work"
            if btn_n.collidepoint(mx, my): game.next_customer_logic()

    # --- 4. КУХНЯ ---
    elif game.game_phase == "work":
        pygame.draw.rect(screen, PANEL_COLOR, (0, 0, W, 80))
        order_txt = FONT_M.render(f"НУЖНО: {game.current_customer.text}", True, (255, 255, 100))
        screen.blit(order_txt, (W//2 - order_txt.get_width()//2, 25))
       
        game.current_customer.update()
        draw_bar(screen, 20, 45, 200, 10, game.current_customer.patience, MONEY_COLOR if game.current_customer.patience > 30 else DANGER_COLOR, "ТЕРПЕНИЕ")
        if game.current_customer.patience <= 0: game.next_customer_logic()

        # Пицца
        p_pos = (W//2 - 150, H//2 + 50)
        pygame.draw.circle(screen, game.pizza.dough_color, p_pos, 160)
        dist = math.hypot(mx - p_pos[0], my - p_pos[1])
       
        if dist < 155 and click[0]:
            if game.selected_slot == 'sauce': game.pizza.sauce_level += 0.8
            elif game.selected_slot == 'cheese': game.pizza.cheese_level += 0.8

        if game.pizza.sauce_level > 5: pygame.draw.circle(screen, SAUCE_COLOR, p_pos, min(150, int(game.pizza.sauce_level/2 + 50)))
        if game.pizza.cheese_level > 5: pygame.draw.circle(screen, CHEESE_COLOR, p_pos, min(140, int(game.pizza.cheese_level/2 + 45)))
        if dist < 155 and event.type == pygame.MOUSEBUTTONDOWN and game.selected_slot == 'pep':
            game.pizza.peps.append((mx, my))
        for p in game.pizza.peps: pygame.draw.circle(screen, PEPPERONI_COLOR, p, 14)

        # СТАКАН С КОЛОЙ
        cup_rect = pygame.Rect(p_pos[0] + 200, p_pos[1] - 50, 60, 100)
        pygame.draw.rect(screen, (200, 200, 200), cup_rect, 2)
        if game.pizza.soda_filled > 0:
            fill_h = (game.pizza.soda_filled / 100) * 96
            pygame.draw.rect(screen, COLA_COLOR, (cup_rect.x+2, cup_rect.y + (100-fill_h)-2, 56, fill_h))
        if game.selected_slot == 'soda' and cup_rect.collidepoint(mx, my) and click[0]:
            game.pizza.soda_filled = min(100, game.pizza.soda_filled + 1)

        # Прожарка
        draw_bar(screen, p_pos[0]-100, p_pos[1]+180, 200, 12, game.pizza.bake_level, (255, 215, 0) if 80 < game.pizza.bake_level <= 110 else (255, 100, 0), "ПРОЖАРКА")

        # Слоты (БЕЗЛИМИТ)
        slots_x, slots_y = W - 350, H - 150
        slot_data = [('sauce', SAUCE_COLOR, "СОУС"), ('cheese', CHEESE_COLOR, "СЫР"),
                     ('pep', PEPPERONI_COLOR, "ПЕП"), ('soda', COLA_COLOR, "КОЛА")]
        for i, (name, color, label) in enumerate(slot_data):
            r = pygame.Rect(slots_x + (i*85), slots_y, 70, 70)
            pygame.draw.rect(screen, color, r, border_radius=10)
            if game.selected_slot == name: pygame.draw.rect(screen, (255,255,255), r, 3, border_radius=10)
            screen.blit(FONT_S.render(label, True, (200, 200, 200)), (r.centerx - 15, r.y - 20))
            if event.type == pygame.MOUSEBUTTONDOWN and r.collidepoint(mx, my): game.selected_slot = name

        # Печь
        if game.pizza.in_oven:
            game.pizza.bake_level += 0.25
            if game.pizza.bake_level <= 100:
                for i in range(3):
                    if game.pizza.dough_color[i] > 100: game.pizza.dough_color[i] -= 0.1
            elif game.pizza.bake_level > 115:
                for i in range(3):
                    if game.pizza.dough_color[i] > 30: game.pizza.dough_color[i] -= 1

        btn_ov = pygame.Rect(W-280, 200, 240, 60)
        pygame.draw.rect(screen, (60, 60, 85) if not game.pizza.in_oven else (255, 100, 0), btn_ov, border_radius=10)
        screen.blit(FONT_M.render("ПЕЧЬ / ВЫНУТЬ", True, (255,255,255)), (btn_ov.centerx-75, btn_ov.centery-10))
        if event.type == pygame.MOUSEBUTTONDOWN and btn_ov.collidepoint(mx, my): game.pizza.in_oven = not game.pizza.in_oven

        # Отдать заказ
        btn_g = pygame.Rect(50, H - 100, 240, 60)
        pygame.draw.rect(screen, (0, 150, 80), btn_g, border_radius=10)
        screen.blit(FONT_M.render("ОТДАТЬ ЗАКАЗ", True, (255,255,255)), (btn_g.centerx-65, btn_g.centery-10))
        if event.type == pygame.MOUSEBUTTONDOWN and btn_g.collidepoint(mx, my):
            game.money += 40
            game.pizzas_made_today += 1
            # Завершение дня после 3-5 пицц
            if game.pizzas_made_today >= random.randint(3, 5):
                if game.day % 2 == 0: game.money += 50
                if game.day >= game.max_days: game.game_phase = "the_end"
                else: game.game_phase = "evening"
            else:
                game.next_customer_logic()

    # --- 5. ВЕЧЕР ---
    elif game.game_phase == "evening":
        screen.blit(FONT_L.render("СМЕНА ОКОНЧЕНА", True, TEXT_COLOR), (W//2-150, H//2-50))
        btn_next = pygame.Rect(W//2-100, H//2+50, 200, 50)
        pygame.draw.rect(screen, (0, 100, 255), btn_next)
        screen.blit(FONT_M.render("СЛЕД. ДЕНЬ", True, (255,255,255)), (btn_next.x+50, btn_next.y+15))
        if event.type == pygame.MOUSEBUTTONDOWN and btn_next.collidepoint(mx, my):
            game.day += 1; game.game_phase = "morning"

    # --- 6. ФИНАЛ ---
    elif game.game_phase == "the_end":
        res = ctypes.windll.user32.MessageBoxW(0, "10 дней прошли! Еще раз?", "Конец", 0x24)
        if res == 6: game.reset_game()
        else: pygame.quit(); sys.exit()

    screen.blit(FONT_M.render(f"Счет: ${game.money:.1f}", True, MONEY_COLOR), (W-180, 25))
    screen.blit(FONT_M.render(f"День: {game.day}", True, (255, 255, 255)), (W-180, 55))

    pygame.display.flip()
    clock.tick(60)