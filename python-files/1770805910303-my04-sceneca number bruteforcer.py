import time
import threading
import tkinter as tk
import keyboard

stop_flag = False

def generate_combos(length):
    max_num = 10 ** length
    for n in range(max_num):
        yield str(n).zfill(length)

def type_combos(length, delay):
    global stop_flag

    if delay > 0:
        print(f"Starting in {delay} seconds...")
        time.sleep(delay)

    for combo in generate_combos(length):
        if stop_flag:
            print("Stopped.")
            return

        # Type the combo
        keyboard.write(combo)

        time.sleep(0.05)

        # Erase it
        for _ in range(length):
            keyboard.press_and_release("backspace")

def start_typing(length, delay):
    global stop_flag
    stop_flag = False
    threading.Thread(target=type_combos, args=(length, delay), daemon=True).start()

def stop_typing():
    global stop_flag
    stop_flag = True

def open_gui():
    root = tk.Tk()
    root.title("Combo Typer")

    tk.Label(root, text="Length:").pack()
    entry_length = tk.Entry(root)
    entry_length.pack()

    tk.Label(root, text="Delay (seconds):").pack()
    entry_delay = tk.Entry(root)
    entry_delay.insert(0, "5")
    entry_delay.pack()

    def on_start():
        try:
            length = int(entry_length.get())
            delay = float(entry_delay.get())
            start_typing(length, delay)
        except:
            pass

    tk.Button(root, text="Start", command=on_start).pack(pady=5)
    tk.Button(root, text="Stop", command=stop_typing).pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    open_gui()
