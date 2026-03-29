import time
import subprocess
import psutil

ram = psutil.virtual_memory()
disk = psutil.disk_usage('/')

print("Starting OS")
time.sleep(1)
print("loading...")
time.sleep(0.5)
print(f"RAM: {ram.total / (1024**3):.2f} ГБ")
print(f"\nROM: {disk.total / (1024**3):.2f} ГБ")
time.sleep(1)
print("wicr")
print("v.1.1")
while True:
    command1 = input("Enter command: ")
    if command1 == "info":
        print("wicr.versions.3.1 NT")

    if command1 == "wicr calc":
        subprocess.Popen("calc.exe")

    if command1 == "win11 calc":
        subprocess.Popen("calc_win11.exe")

    if command1 == "mp5":
        subprocess.Popen('Windows Media player\Wmplayer.exe')

    if command1 == "exp":
        subprocess.Popen("exp.exe")

    if command1 == "exp7":
        subprocess.Popen("exp7.exe")

    if command1 == "brows":
        subprocess.Popen('Internet Explorer\iexplore.exe')

    if command1 == "help":
        print("info - информация о системе")
        print("wicr calc - запускает калькулятор wicr")
        print("win11 calc - запускает калькулятор windows 10-11")
        print("mp5 - запускает медиа плеер Windows 7-11")
        print("exp - открывает проводник windows 10-11")
        print("exp7 - открывает проводник windows 7")
        print("brows - открывает браузер windows 7-11")
        