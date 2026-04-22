import keyboard
import random
import time
import threading

# Состояние каждой клавиши отдельно
states = {
    'e': False,
    'f': False,
    'h': False
}

def natural_delay():
    mode = random.random()

    if mode < 0.65:
        delay = random.randint(100, 130)
    elif mode < 0.90:
        delay = random.randint(103, 150)
    else:
        delay = random.randint(157, 276)

    return delay / 1000


def micro_pause():
    if random.random() < 0.12:
        return random.uniform(0.18, 0.55)
    return 0


def press_key(key):
    keyboard.press(key)
    time.sleep(random.uniform(0.018, 0.055))
    keyboard.release(key)


def auto_press(key):
    while states[key]:
        press_key(key)

        time.sleep(natural_delay())

        extra = micro_pause()
        if extra > 0:
            time.sleep(extra)


def toggle(key):
    states[key] = not states[key]

    if states[key]:
        threading.Thread(target=auto_press, args=(key,), daemon=True).start()
        print(f"{key.upper()} ВКЛ")
    else:
        print(f"{key.upper()} ВЫКЛ")


# Горячие клавиши:
keyboard.add_hotkey('e', lambda: toggle('e'))
keyboard.add_hotkey('f', lambda: toggle('f'))
keyboard.add_hotkey('h', lambda: toggle('h'))

print("E = старт/стоп E")
print("F = старт/стоп F")
print("H = старт/стоп H")
print("ESC = выход")

keyboard.wait('esc')