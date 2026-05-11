import keyboard
import time
import threading

run = False

def key_loop():
    global run
    while True:
        if run:
            keyboard.press_and_release('1')
            time.sleep(0.12)
            keyboard.press_and_release('2')
            time.sleep(0.12)
            keyboard.press_and_release('3')
            time.sleep(0.12)
            keyboard.press_and_release('4')
            time.sleep(0.12)
        else:
            time.sleep(0.01)

def check_key():
    global run
    while True:
        if keyboard.is_pressed('1'):
            run = True
        else:
            run = False

        if keyboard.is_pressed('f12'):
            exit()
            
        time.sleep(0.01)

if __name__ == "__main__":
    t = threading.Thread(target=key_loop, daemon=True)
    t.start()
    check_key()