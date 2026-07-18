import tempfile
import requests
import pygame
import time
import os

url = "https://soundbuttonsworld.com/api/upload/download?id=5d4e4bde-bbae-4ff6-8fc7-36c27672296b.mp3"

r = requests.get(url, headers={
    "User-Agent": "Mozilla/5.0"
})

if r.status_code != 200:
    print("Failed to download:", r.status_code)
    exit()

fd, path = tempfile.mkstemp(suffix=".mp3")
os.close(fd)

with open(path, "wb") as f:
    f.write(r.content)

pygame.mixer.init()
pygame.mixer.music.load(path)
pygame.mixer.music.play()

while pygame.mixer.music.get_busy():
    time.sleep(0.1)

pygame.quit()
os.remove(path)