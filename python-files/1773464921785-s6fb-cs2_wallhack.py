# cs2_wallhack.py (компилируйте в exe через pyinstaller --onefile)
import time
from steamworks import *
import pygame
import win32gui

app_id = 730  # Замените на актуальный AppID CS2
steam = Steamworks(730)

pygame.init()
overlay = pygame.display.set_mode((800,600), pygame.NOFRAME)
hwnd = win32gui.GetForegroundWindow()

while True:
    players = steam.get_players()  # Получаем список игроков через Steam API
    overlay.fill((0,0,0))
    
    for player in players:
        x, y = screen_coords(player.position)  # Преобразование координат
        
        if player.health > 0:  # Только живых игроков
            pygame.draw.circle(overlay, (255,0,0), (x,y), 10)
    
    pygame.display.update()
    time.sleep(0.1)

def screen_coords(world_pos):
    # Алгоритм преобразования координат в экранные (примерный)
    return int(world_pos.x * 1.2 + 400), int(-world_pos.z * 1.5 + 300)