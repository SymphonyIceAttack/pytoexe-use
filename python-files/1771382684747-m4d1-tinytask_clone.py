# tinytask_clone.py
# TinyTask 스타일 간단 자동화 프로그램
# 마우스 위치와 클릭을 기록하고 반복 재생

import pyautogui
import keyboard
import time

recording = []
print("TinyTask Clone 시작!")
print("녹화: F9, 녹화 종료: F10, 재생: 자동")

# F9 누르면 녹화 시작
keyboard.wait('F9')
print("녹화 중... F10 누르면 종료")

while True:
    if keyboard.is_pressed('F10'):
        break
    x, y = pyautogui.position()
    recording.append((x, y))
    time.sleep(0.01)  # 10ms 간격 기록

print("녹화 종료! 2초 후 재생")
time.sleep(2)

for pos in recording:
    pyautogui.moveTo(pos[0], pos[1])
    pyautogui.click()  # 클릭도 반복
    time.sleep(0.01)

print("재생 완료!")
