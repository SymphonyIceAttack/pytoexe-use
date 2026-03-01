import tkinter as tk
from tkinter import messagebox
import os
import subprocess

# Function for Boost button
def boost():
    try:
        # System tweaks
        subprocess.run('powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61', shell=True)
        subprocess.run('powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61', shell=True)
        subprocess.run('sc stop SysMain', shell=True)
        subprocess.run('sc stop XblGameSave', shell=True)
        subprocess.run('sc stop XboxNetApiSvc', shell=True)
        subprocess.run('sc stop XboxGipSvc', shell=True)
        subprocess.run('bcdedit /set useplatformtick yes', shell=True)
        subprocess.run('bcdedit /set disabledynamictick yes', shell=True)
        messagebox.showinfo('Ultimate Tweak', 'System Boost Applied!')
    except Exception as e:
        messagebox.showerror('Error', str(e))

# Function for Network button
def network():
    try:
        subprocess.run('netsh int tcp set global autotuninglevel=disabled', shell=True)
        subprocess.run('netsh int tcp set global rss=enabled', shell=True)
        subprocess.run('netsh int tcp set global chimney=enabled', shell=True)
        subprocess.run('netsh int tcp set global dca=enabled', shell=True)
        subprocess.run('netsh winsock reset', shell=True)
        messagebox.showinfo('Ultimate Tweak', 'Network Optimized!')
    except Exception as e:
        messagebox.showerror('Error', str(e))

# Function for Clean button
def clean():
    try:
        subprocess.run('powershell -command "Clear-RecycleBin -Force"', shell=True)
        subprocess.run('del /s /q %temp%\\*', shell=True)
        subprocess.run('del /s /q C:\\Windows\\Temp\\*', shell=True)
        messagebox.showinfo('Ultimate Tweak', 'RAM & Temp Cleaned!')
    except Exception as e:
        messagebox.showerror('Error', str(e))

# GUI setup
root = tk.Tk()
root.title('Ultimate Tweak ELITE PRO')
root.geometry('300x200')
root.resizable(False, False)

# Buttons
btn_boost = tk.Button(root, text='BOOST', width=20, height=2, command=boost)
btn_boost.pack(pady=10)

btn_network = tk.Button(root, text='NETWORK', width=20, height=2, command=network)
btn_network.pack(pady=10)

btn_clean = tk.Button(root, text='CLEAN', width=20, height=2, command=clean)
btn_clean.pack(pady=10)

root.mainloop()
