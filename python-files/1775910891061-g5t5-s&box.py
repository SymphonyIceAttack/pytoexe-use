import webbrowser
import time
import subprocess

print("Запуск S&Box")
time.sleep(5)

print("Запуск античита")
time.sleep(5)

print("Компиляция шейдеров")
time.sleep(10)

print("Установка необходимых библиотек")
time.sleep(5)

print("Проверка копии игры")
time.sleep(2)

url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
webbrowser.open(url)
time.sleep(2)

for _ in range(50):
    subprocess.run(
        ["powershell", "-command", "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"],
        capture_output=True,
        shell=False
    )
    time.sleep(0.05)