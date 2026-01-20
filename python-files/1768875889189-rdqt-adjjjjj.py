import subprocess
import time

url = "https://campuchiavd.github.io/vdff.mp4"
brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

resp = input("¿desea ejecutar este programa? (s/n): ").lower()
if resp != "s":
    exit()

resp = input("¿seguro? (s/n): ").lower()
if resp != "s":
    exit()

for i in range(50):
    subprocess.Popen([
        brave_path,
        "--new-window",
        "--window-size=400,300",
        url
    ])
    time.sleep(1)  # ajustá la velocidad si querés
