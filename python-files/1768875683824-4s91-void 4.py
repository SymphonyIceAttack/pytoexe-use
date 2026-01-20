import subprocess
import time

url = "https://campuchiavd.github.io/vdff.mp4"
brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

resp = input("¿querés abrir esto? (s/n): ").lower()
if resp != "s":
    exit()

resp = input("¿seguro? (s/n): ").lower()
if resp != "s":
    exit()

for i in range(50):
    subprocess.Popen([
        brave_path,
        url
    ])
    time.sleep(0.3)  # velocidad entre pestañas

