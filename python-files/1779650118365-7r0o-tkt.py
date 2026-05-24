import subprocess
import time
import pyautogui
import random
import math

# Lance Paint
subprocess.Popen("mspaint.exe")
time.sleep(1.5)

# Récupère la taille de l'écran
screen_width, screen_height = pyautogui.size()
pyautogui.click(screen_width // 2, screen_height // 2)
time.sleep(0.5)

# Position de départ (un peu décalée aléatoirement)
x_start = screen_width // 2 - 300 + random.randint(-10, 10)
y_start = screen_height // 2 + random.randint(-5, 5)

pyautogui.moveTo(x_start, y_start)
pyautogui.mouseDown()
time.sleep(random.uniform(0.1, 0.3))  # Petite pause avant de commencer

# Liste des points cibles pour "SACUT" (les mêmes qu'avant, mais on va les brouiller)
points_bruts = [
    # S
    (0, 0), (40, 0), (40, 30), (0, 50), (0, 80), (40, 110),
    # A
    (80, 0), (120, 0), (140, 110), (100, 60), (140, 60),
    # C
    (180, 0), (220, 0), (240, 55), (220, 110), (180, 110),
    # U
    (280, 0), (280, 110), (320, 110), (360, 110), (360, 0),
    # T
    (400, 110), (400, 0), (380, 0), (420, 0)
]

# Fonction pour ajouter du bruit humain
def point_humain(base_x, base_y, step, total_steps):
    # Tremblement : plus fort au milieu du trait, faible au début/fin
    jitter_strength = 2.5 * math.sin(step / total_steps * math.pi)  # max 2.5 pixels
    jitter_x = random.uniform(-jitter_strength, jitter_strength)
    jitter_y = random.uniform(-jitter_strength, jitter_strength)
    
    # Petite dérive aléatoire (comme si la main glisse)
    drift_x = random.gauss(0, 0.5) * (step / total_steps)
    drift_y = random.gauss(0, 0.5) * (step / total_steps)
    
    return (base_x + jitter_x + drift_x, base_y + jitter_y + drift_y)

# Convertir les points relatifs en absolus
points_abs = [(x_start + x, y_start + y) for x, y in points_bruts]

# Dessiner chaque segment avec du bruit et vitesse variable
previous_x, previous_y = points_abs[0]
for i in range(1, len(points_abs)):
    target_x, target_y = points_abs[i]
    
    # Nombre de micro-étapes entre les deux points (plus on est lent, plus il y a d'étapes)
    distance = math.hypot(target_x - previous_x, target_y - previous_y)
    steps = max(5, int(distance / random.uniform(3, 8)))  # entre 3 et 8 pixels par étape
    
    for step in range(1, steps + 1):
        t = step / steps
        # Interpolation linéaire
        interp_x = previous_x + (target_x - previous_x) * t
        interp_y = previous_y + (target_y - previous_y) * t
        
        # Ajouter du bruit humain
        noisy_x, noisy_y = point_humain(interp_x, interp_y, step, steps)
        
        # Déplacer la souris avec une vitesse variable (parfois plus rapide, parfois plus lente)
        duration = random.uniform(0.008, 0.025)  # entre 8 et 25 ms par micro-mouvement
        pyautogui.moveTo(noisy_x, noisy_y, duration=duration)
        
        # Très rarement, faire une mini-pause (comme une hésitation)
        if random.random() < 0.02:  # 2% de chance par étape
            time.sleep(random.uniform(0.02, 0.08))
    
    # Petite pause entre les lettres (comme lever le stylo)
    if i in [6, 11, 16, 21]:  # après chaque lettre (S,A,C,U,T)
        time.sleep(random.uniform(0.08, 0.2))
    
    previous_x, previous_y = target_x, target_y

# Relâcher le clic
pyautogui.mouseUp()
time.sleep(0.2)

# Optionnel : jouer un petit son "plop" (si tu veux, mais pas obligatoire)
# import winsound
# winsound.Beep(800, 100)