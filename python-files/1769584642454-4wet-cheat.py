import os
import time

# Количество окон, которое нужно открыть (для примера ставим 5)
num_windows = 1000000

for _ in range(num_windows):
    os.system('start cmd')

    # Немного ждем, чтобы окна успели открыться
    time.sleep(0.1)
