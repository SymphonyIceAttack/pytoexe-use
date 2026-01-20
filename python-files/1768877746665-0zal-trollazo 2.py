# PANTALLA AZUL FALSA (BSOD) CON RETRASO
# Al ejecutar: NO PASA NADA durante un tiempo → luego aparece la BSOD
# SALIDA SECRETA: CTRL + ALT + Q

import pygame
import sys
import time
import random

pygame.init()

# ---- CONFIGURACIÓN ----
DELAY_INICIAL = random.randint(25, 60)  # segundos sin que pase nada
EXIT_COMBO = (pygame.K_LCTRL, pygame.K_LALT, pygame.K_q)

# ---- PANTALLA ----
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("")

clock = pygame.time.Clock()

# ---- COLORES ----
BLUE = (0, 120, 215)
WHITE = (245, 245, 245)

# ---- FUENTES ----
title_font = pygame.font.SysFont("segoeui", 72)
text_font = pygame.font.SysFont("segoeui", 26)
small_font = pygame.font.SysFont("segoeui", 22)

# ---- CONTROL ----
pygame.mouse.set_visible(True)
pygame.event.set_grab(False)

start_time = time.time()
bsod_active = False
progress = 0

def draw_bsod(p):
    screen.fill(BLUE)

    # Cara triste
    sad = title_font.render(":(", True, WHITE)
    screen.blit(sad, (80, 60))

    # Texto principal
    t1 = text_font.render(
        "Your PC ran into a problem and needs to restart.", True, WHITE
    )
    t2 = text_font.render(
        "We're just collecting some error info, and then we'll restart for you.",
        True, WHITE
    )
    screen.blit(t1, (80, 160))
    screen.blit(t2, (80, 200))

    # Progreso falso
    prog = small_font.render(f"{p}% complete", True, WHITE)
    screen.blit(prog, (80, 260))

    # Código de error falso
    err = small_font.render(
        "Stop code: CRITICAL_PROCESS_DIED", True, WHITE
    )
    screen.blit(err, (80, HEIGHT - 120))

    pygame.display.flip()

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            keys = pygame.key.get_pressed()
            # SALIDA SECRETA
            if keys[pygame.K_LCTRL] and keys[pygame.K_LALT] and event.key == pygame.K_q:
                pygame.event.set_grab(False)
                pygame.mouse.set_visible(True)
                pygame.quit()
                sys.exit()

    # FASE 1: No pasa nada (parece que el exe no hace nada)
    if not bsod_active:
        if time.time() - start_time >= DELAY_INICIAL:
            bsod_active = True
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)
            progress = 0
        else:
            # Pantalla completamente normal / negra
            screen.fill((0, 0, 0))
            pygame.display.flip()

    # FASE 2: BSOD falsa
    else:
        progress = min(100, progress + random.randint(0, 2))
        draw_bsod(progress)
        time.sleep(random.uniform(0.05, 0.15))

    clock.tick(60)
