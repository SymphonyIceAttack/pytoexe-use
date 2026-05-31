import os
import subprocess
import time
import threading


for i in range(500):
        subprocess.Popen("start cmd", shell=True)
        time.sleep(0.1)  # Пауза, чтобы не зависла система

#time.sleep(10)

#def shutdown():
    #time.sleep(seconds)
    #os.system("shutdown /s /t 0")  # Моментальное выключение

    #thread = threading.Thread(target=shutdown)
    #thread.start()