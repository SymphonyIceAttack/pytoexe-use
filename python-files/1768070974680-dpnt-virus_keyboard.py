import subprocess
import sys
import os
import keyboard
counter=0

subprocess.check_call([sys.executable, "-m", "pip", "install", "keyboard"])

def shutdown():
    os.system("shutdown /s /t 0")

def on_key(x):
    global counter
    counter+=1
    if counter==5:
        shutdown()

keyboard.on_press(on_key)

keyboard.wait()