import pygame
import sys
import random
import time
import winsound

pygame.init()
pygame.mixer.quit()  # usamos winsound para beeps más agresivos (Windows)

# Pantalla completa
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("SYSTEM ACCESS")

WIDTH, HEIGHT = screen.get_size()
CENTER = (WIDTH // 2, HEIGHT // 2)

# Colores
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

# Fuente
font = pygame.font.SysFont("consolas", 22)

# Bloqueo de mouse y teclado
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

lines = [
    "INICIANDO PROTOCOLO DE ACCESO...",
    "CONECTANDO A SERVIDOR REMOTO...",
    "IP LOCALIZADA: 192.168.0." + str(random.randint(2, 254)),
    "ESCANEANDO ARCHIVOS DEL USUARIO...",
    "ACCESO A MEMORIA RAM...",
    "EXTRAYENDO INFORMACION...",
    "ADVERTENCIA: ACTIVIDAD SOSPECHOSA",
    "INYECCION DE PROCESO EN CURSO...",
    "DESHABILITANDO CONTROL DEL USUARIO...",
    "ERROR CRITICO DEL SISTEMA",
    "INTENTO DE RECUPERACION FALLIDO",
    "SISTEMA BLOQUEADO"
]

displayed_lines = []
clock = pygame.time.Clock()

def draw_text():
    screen.fill(BLACK)
    y = 20
    for line in displayed_lines[-30:]:
        text = font.render(line, True, GREEN)
        screen.blit(text, (20, y))
        y += 25
    pygame.display.flip()

running = True
line_index = 0
last_time = time.time()
last_beep = 0

while running:
    # Fuerza el mouse al centro constantemente (bloqueo total)
    pygame.mouse.set_pos(CENTER)

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            keys = pygame.key.get_pressed()
            # TECLA SECRETA PARA SALIR
            if keys[pygame.K_LCTRL] and keys[pygame.K_LALT] and event.key == pygame.K_q:
                pygame.event.set_grab(False)
                pygame.mouse.set_visible(True)
                pygame.quit()
                sys.exit()

    current_time = time.time()

    # Texto tipo hacker
    if current_time - last_time > random.uniform(0.25, 0.7):
        if line_index < len(lines):
            displayed_lines.append(lines[line_index])
            line_index += 1
        else:
            displayed_lines.append(
                f">>> DATA PACKET [{random.randint(1000,9999)}] TRANSFERRED"
            )
        last_time = current_time

    # Sonidos fuertes y constantes
    if current_time - last_beep > random.uniform(0.4, 0.8):
        freq = random.randint(1200, 2500)   # frecuencia alta
        dur = random.randint(120, 300)      # duración
        winsound.Beep(freq, dur)
        last_beep = current_time

    draw_text()
    clock.tick(60)
