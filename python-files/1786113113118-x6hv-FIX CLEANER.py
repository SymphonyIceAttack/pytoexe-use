import os, time, sys
from datetime import datetime

p = r"E:\Minecraft\game\logs\latest

# Строки, которые нужно удалять
REMOVE_STRINGS = [
    "Liminar client initialized: variant=Free, functions=61",
    "[Liminar IRC/INFO]: [System] [CHAT] Info§8 > §rIRC connected: #legacylibrary"
],"

def c():
    try:
        if not os.path.exists(p):
            return

        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        filtered = [
            line for line in lines
            if not any(text in line for text in REMOVE_STRINGS)
        ]

        if len(filtered) != len(lines):
            with open(p, 'w', encoding='utf-8', errors='ignore') as f:
                f.writelines(filtered)
            print(datetime.now().strftime('%H:%M:%S'))

    except:
        pass

if len(sys.argv) > 1 and sys.argv[1] == "--once":
    c()
else:
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    while True:
        c()
        time.sleep(3)
