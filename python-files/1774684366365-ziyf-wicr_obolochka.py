import time
import subprocess

print("Starting OS")
time.sleep(1)
print("loading...")
time.sleep(0.5)
ram1 = "32mb"
rom1 = "128mb"
print("RAM:" + ram1)
print("ROM:" + rom1)
time.sleep(1)
print("wicr")
print("v.1.1")
while True:
    command1 = input("Enter command: ")
    if command1 == "info":
        print("LN-DOS.versions.1.")
        print("test version")
    if command1 == "startOS":
        subprocess.Popen("wicr.exe")

    if command1 == "wicr calc":
        subprocess.Popen("calc.exe")

    if command1 == "win11 calc":
        subprocess.Popen("calc_win11.exe")

    if command1 == "start":
        subprocess.Popen("wicr.exe")