#  -*- coding: UTF-8 -*-

# MindPlus
# Python
import pyautogui


for index in range(5):
    pyautogui.hotkey(*['win','r'])
    pyautogui.keyDown(key="cmd")
    pyautogui.keyDown(key="enter")
    pyautogui.moveTo(400, 300, duration = 0, tween=pyautogui.linear)
    pyautogui.press(keys="f11", presses=1)
    pyautogui.press(keys="shiftleft", presses=1)
    pyautogui.write(message="I WILL KILL YOU!!!", interval=0)
    pyautogui.keyDown(key="enter")
    pyautogui.press(keys="shiftleft", presses=1)
    pyautogui.write(message="I WILL KILL YOU!!!", interval=0)
    pyautogui.keyDown(key="enter")