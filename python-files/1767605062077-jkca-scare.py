import os
import time
import random
import threading
import webbrowser

def matrixrain():
    os.system('cls')
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*()+-=[]{}|;':",./<>?アイウエオカキクケコ"
    for  in range(600):
        line = ''.join(random.choice(chars) for  in range(120))
        print("\033[92m" + line)  # Green Matrix text
        time.sleep(0.03)

print("\033[92m")  # Set green text
threading.Thread(target=matrix_rain, daemon=True).start()

time.sleep(12)  # Matrix for 12 seconds

os.system('cls')
print("\033[91m" + "\n\n\n\n\t\t\t!!! URGENT SYSTEM ALERT !!!\n\n\t\tYOUR COMPUTER HAS BEEN INFECTED\n\t\tALL FILES ARE NOW ENCRYPTED\n\t\tWEBCAM IS RECORDING YOU RIGHT NOW\n\t\tSEND $500 IN BITCOIN OR EVERYTHING GETS DELETED\n\t\tTIME REMAINING: 00:05:00\n\n".center(120))
time.sleep(15)  # Scare screen for 15 seconds

webbrowser.open("https://www.youtube.com/watch?v=dQw4w9WgXcQ")  # Rickroll blasts loud

os.system('cls')
print("\033[93m" + "\n\n\n\n\t\t\tLMAOOOOOO YOU GOT PRANKED SO HARD BRO!!!\n\t\t\tNO FILES DELETED, NO HACK, NOTHING HAPPENED\n\t\t\t- From your best friend of 8 years 😂😂😂😂\n\n\t\t\tClose this window and come laugh with me".center(120))
input("\n\nPress Enter to exit...")