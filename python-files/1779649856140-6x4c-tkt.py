import subprocess
import time
import pyautogui

# Lance Paint
subprocess.Popen("mspaint.exe")
time.sleep(1.5)

# Récupère la taille de l'écran
screen_width, screen_height = pyautogui.size()

# Clique au centre de l'écran pour activer Paint
pyautogui.click(screen_width // 2, screen_height // 2)
time.sleep(0.5)

# Position de départ
x_start = screen_width // 2 - 300
y_start = screen_height // 2

# Va au point de départ
pyautogui.moveTo(x_start, y_start)
pyautogui.mouseDown()

# Coordonnées pour dessiner "SACUT"
coords = [
    (x_start, y_start),
    (x_start + 40, y_start),
    (x_start + 40, y_start + 30),
    (x_start, y_start + 50),
    (x_start, y_start + 80),
    (x_start + 40, y_start + 110),
    (x_start + 80, y_start),
    (x_start + 120, y_start),
    (x_start + 140, y_start + 110),
    (x_start + 100, y_start + 60),
    (x_start + 140, y_start + 60),
    (x_start + 180, y_start),
    (x_start + 220, y_start),
    (x_start + 240, y_start + 55),
    (x_start + 220, y_start + 110),
    (x_start + 180, y_start + 110),
    (x_start + 280, y_start),
    (x_start + 280, y_start + 110),
    (x_start + 320, y_start + 110),
    (x_start + 360, y_start + 110),
    (x_start + 360, y_start),
    (x_start + 400, y_start + 110),
    (x_start + 400, y_start),
    (x_start + 380, y_start),
    (x_start + 420, y_start),
]

for x, y in coords:
    pyautogui.moveTo(x, y, duration=0.03)

pyautogui.mouseUp()