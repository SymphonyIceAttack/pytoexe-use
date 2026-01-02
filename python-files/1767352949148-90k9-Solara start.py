from colorama import init
init()

import time
import random
import os
import subprocess

subprocess.run(["solara.exe"])

def wait_back():
    input("\nНажмите Enter, чтобы вернуться назад...")


def load():
    BAR_WIDTH = 30
    progress = 0

    while progress < 100:
        jump = random.choice([0, 1, 1, 2, 3, 5])
        progress += jump
        progress = min(progress, 100)

        t = progress / 100
        delay = 0.02 + (t ** 2) * 0.18

        filled = int(BAR_WIDTH * progress / 100)
        bar = "█" * filled + "░" * (BAR_WIDTH - filled)

        print(f"\r[{bar}] {progress:3d}%", end="", flush=True)
        time.sleep(delay)

    print("\nЗагрузка завершена")


logo = r"""
   _____       _                 
  / ____|     | |                
 | (___   ___ | | __ _ _ __ __ _ 
  \___ \ / _ \| |/ _` | '__/ _` |
  ____) | (_) | | (_| | | | (_| |
 |_____/ \___/|_|\__,_|_|  \__,_|
"""


def type_logo(text, delay=0.005):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)


def typewriter(text, delay=0.03):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)


# Старт
type_logo(logo)
print()
load()
os.system("cls" if os.name == "nt" else "clear")


def main_menu():
    while True:
        print(logo)
        print()

        typewriter("Выберите:\n")
        typewriter("1. Загрузить скрипт.\n")
        typewriter("2. Мои скрипты.\n")
        typewriter("3. Помощь.\n")
        typewriter("0. Выход.\n")

        user_input = input("> ")

        if user_input == "1":
            print()
            typewriter("Вставьте скрипт:\n")
            input()

            print()
            typewriter("Скрипт загружается, пожалуйста подождите...\n")
            load()

            print()
            typewriter("Скрипт загружен, можете играть.\n")
            wait_back()

        elif user_input == "2":
            print()
            typewriter("У вас пока что нет скриптов.\n")
            wait_back()

        elif user_input == "3":
            print()
            typewriter("Помощь:\n")
            typewriter("— Enter: назад\n")
            typewriter("— 0: выход\n")
            wait_back()

        elif user_input == "0":
            typewriter("Выход...\n")
            time.sleep(1)
            break

        else:
            typewriter("Неверный ввод.\n")
            time.sleep(1)

        os.system("cls" if os.name == "nt" else "clear")


# ВАЖНО: запуск меню
main_menu()
