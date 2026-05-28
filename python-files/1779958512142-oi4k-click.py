from pynput import mouse, keyboard
import pyautogui
import time
import json

events = []
recording = True

print("Запись началась.")
print("Нажми ESC для остановки записи.")

start_time = time.time()


def on_click(x, y, button, pressed):
    if recording:
        events.append({
            "type": "click",
            "x": x,
            "y": y,
            "button": str(button),
            "pressed": pressed,
            "time": time.time() - start_time
        })


def on_move(x, y):
    if recording:
        events.append({
            "type": "move",
            "x": x,
            "y": y,
            "time": time.time() - start_time
        })


def on_press(key):
    global recording

    if key == keyboard.Key.esc:
        recording = False
        return False


mouse_listener = mouse.Listener(
    on_click=on_click,
    on_move=on_move
)

keyboard_listener = keyboard.Listener(
    on_press=on_press
)

mouse_listener.start()
keyboard_listener.start()

keyboard_listener.join()

mouse_listener.stop()

with open("macro.json", "w") as f:
    json.dump(events, f)

print("Запись сохранена.")

time.sleep(2)

while True:
    print("Повтор действий через 10 минут...")
    time.sleep(10)

    with open("macro.json", "r") as f:
        events = json.load(f)

    for i, event in enumerate(events):
        if i > 0:
            delay = event["time"] - events[i - 1]["time"]
            time.sleep(delay)

        if event["type"] == "click":
            pyautogui.click(event["x"], event["y"])

    print("Макрос выполнен.")
