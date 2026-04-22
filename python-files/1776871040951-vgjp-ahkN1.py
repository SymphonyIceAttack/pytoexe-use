
import tkinter as tk
from tkinter import ttk
import threading, random, time
import keyboard

states={'e':False,'f':False,'h':False}

def natural_delay():
    mode=random.random()
    if mode<0.65: delay=random.randint(130,240)
    elif modestop<0.90: delay=random.randint(103,150)
    else: delay=random.randint(241,316)
    return delay/1000

def micro_pause():
    return random.uniform(0.18,0.55) if random.random()<0.12 else 0

def press_key(key):
    keyboard.press(key); time.sleep(random.uniform(0.018,0.055)); keyboard.release(key)

def worker(key):
    while states[key]:
        press_key(key)
        time.sleep(natural_delay())
        p=micro_pause()
        if p: time.sleep(p)

def toggle(key, btn):
    states[key]=not states[key]
    if states[key]:
        btn.config(text=f"{key.upper()}: ON")
        threading.Thread(target=worker,args=(key,),daemon=True).start()
    else:
        btn.config(text=f"{key.upper()}: OFF")

root=tk.Tk()
root.title("Simple AutoKey")
root.geometry("260x220")
root.resizable(False,False)

ttk.Label(root,text="Нажми кнопку для старта/стопа").pack(pady=10)

buttons={}
for k in ['e','f','h']:
    b=tk.Button(root,text=f"{k.upper()}: OFF",width=18,height=2)
    b.config(command=lambda kk=k, bb=b: toggle(kk,bb))
    b.pack(pady=5)
    buttons[k]=b

ttk.Label(root,text="Горячие клавиши: E / F / H\nESC закрыть").pack(pady=10)

keyboard.add_hotkey('e', lambda: root.after(0, lambda: toggle('e', buttons['e'])))
keyboard.add_hotkey('f', lambda: root.after(0, lambda: toggle('f', buttons['f'])))
keyboard.add_hotkey('h', lambda: root.after(0, lambda: toggle('h', buttons['h'])))
keyboard.add_hotkey('esc', lambda: root.after(0, root.destroy))

root.mainloop()