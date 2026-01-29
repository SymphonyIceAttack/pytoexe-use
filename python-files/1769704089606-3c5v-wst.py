import pygame
import psutil
import cpuinfo
import GPUtil
import time

pygame.init()

WIDTH, HEIGHT = 750, 420
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mini Speccy FPS Monitor")

# Fonts
font = pygame.font.SysFont("consolas", 20)
title_font = pygame.font.SysFont("consolas", 26)

clock = pygame.time.Clock()
warning_visible = True
last_blink = time.time()

# CPU info
try:
    cpu = cpuinfo.get_cpu_info()
    cpu_name = cpu.get('brand_raw', 'CPU N/A')
except:
    cpu_name = 'CPU N/A'

def get_gpu():
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            return gpus[0]
    except:
        return None
    return None

def get_cpu_temp():
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return None
        # Common CPU sensors
        for key in ["coretemp", "k10temp", "cpu-thermal"]:
            if key in temps:
                entries = temps[key]
                vals = [e.current for e in entries if e.current is not None]
                if vals:
                    return sum(vals)/len(vals)
        # Fallback: take any available sensor
        for entries in temps.values():
            vals = [e.current for e in entries if e.current is not None]
            if vals:
                return sum(vals)/len(vals)
        return None
    except:
        return None

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((20, 20, 20))

    # FPS
    fps = int(clock.get_fps())
    fps_text = font.render(f"FPS: {fps}", True, (0, 255, 255))
    screen.blit(fps_text, (WIDTH - 120, 10))

    y = 50
    screen.blit(title_font.render("System Information", True, (255, 255, 255)), (20, y))
    y += 40

    # --- CPU ---
    cpu_temp = get_cpu_temp()
    cpu_text = f"CPU: {cpu_name} ("
    temp_text = f"{cpu_temp:.1f} °C)" if cpu_temp is not None else "N/A)"
    screen.blit(font.render(cpu_text, True, (200, 200, 200)), (20, y))
    # temp color
    if cpu_temp is None:
        color = (150, 150, 150)
    elif 20 <= cpu_temp <= 40:
        color = (0, 255, 0)
    else:
        color = (255, 0, 0)
    temp_surface = font.render(temp_text, True, color)
    screen.blit(temp_surface, (20 + font.size(cpu_text)[0], y))
    y += 30

    # --- RAM ---
    try:
        ram_gb = round(psutil.virtual_memory().total / (1024**3), 1)
        screen.blit(font.render(f"RAM: {ram_gb} GB (N/A °C)", True, (200, 200, 200)), (20, y))
    except:
        screen.blit(font.render("RAM: N/A", True, (150, 150, 150)), (20, y))
    y += 30

    # --- GPU ---
    gpu = get_gpu()
    gpu_temp_val = None
    if gpu:
        gpu_name_text = f"GPU: {gpu.name} ("
        gpu_temp_val = getattr(gpu, 'temperature', None)
        temp_text = f"{gpu_temp_val} °C)" if gpu_temp_val is not None else "N/A)"
        screen.blit(font.render(gpu_name_text, True, (200, 200, 200)), (20, y))
        # temp color
        if gpu_temp_val is None:
            color = (150, 150, 150)
        elif 20 <= gpu_temp_val <= 40:
            color = (0, 255, 0)
        else:
            color = (255, 0, 0)
        temp_surface = font.render(temp_text, True, color)
        screen.blit(temp_surface, (20 + font.size(gpu_name_text)[0], y))
    else:
        screen.blit(font.render("GPU: N/A", True, (150, 150, 150)), (20, y))
    y += 30

    # --- Warning if any temp > 40 ---
    max_temp = 0
    if cpu_temp is not None:
        max_temp = cpu_temp
    if gpu_temp_val is not None and gpu_temp_val > max_temp:
        max_temp = gpu_temp_val

    if max_temp > 40:
        if time.time() - last_blink > 0.5:
            warning_visible = not warning_visible
            last_blink = time.time()
        if warning_visible:
            screen.blit(font.render("⚠️", True, (255, 0, 0)), (320, 50))

    pygame.display.flip()
    clock.tick()  # unlimited FPS

pygame.quit()
