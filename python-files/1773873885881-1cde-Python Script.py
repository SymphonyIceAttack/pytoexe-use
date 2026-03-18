import pyautogui
import time
import os
import keyboard
import ctypes

# ========== НАСТРОЙКИ ==========
PASSWORD_IMAGE = r"C:\Users\444\Desktop\KOT\1.jpg"
CLICK_IMAGE_1 = r"C:\Users\444\Desktop\KOT\2.jpg"
CLICK_IMAGE_2 = r"C:\Users\444\Desktop\KOT\3.png"
CLICK_IMAGE_3 = r"C:\Users\444\Desktop\KOT\4.jpg"

CONFIDENCE = 0.8
SCAN_DELAY = 1
# ================================

# Виртуальные коды клавиш (НЕ ЗАВИСЯТ ОТ РАСКЛАДКИ!)
# Полный список: https://docs.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
VK = {
    'SHIFT': 0x10,
    'R': 0x52, 'O': 0x4F, 'D': 0x44, 'I': 0x49, 'N': 0x4E,
    '4': 0x34, '6': 0x36, '0': 0x30, '8': 0x38, '3': 0x33,
    'ENTER': 0x0D
}

def press_key(vk_code, shift=False):
    """Нажимает клавишу по виртуальному коду (минуя раскладку)"""
    if shift:
        ctypes.windll.user32.keybd_event(VK['SHIFT'], 0, 0, 0)
        time.sleep(0.01)
    
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    time.sleep(0.01)
    ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)
    time.sleep(0.01)
    
    if shift:
        ctypes.windll.user32.keybd_event(VK['SHIFT'], 0, 2, 0)
        time.sleep(0.01)

print("🔥 БОТ РАБОТАЕТ (ВВОДИТ АНГЛИЙСКИЕ БУКВЫ ПРИ ЛЮБОЙ РАСКЛАДКЕ)")
print("F11 - выход")
print("-" * 40)

# Проверка файлов
for img in [PASSWORD_IMAGE, CLICK_IMAGE_1, CLICK_IMAGE_2, CLICK_IMAGE_3]:
    if not os.path.exists(img):
        print(f"❌ Нет файла: {img}")
        exit()

pyautogui.FAILSAFE = True
stats = [0, 0, 0, 0]  # [пароли, клики2, клики3, клики4]

try:
    while True:
        if keyboard.is_pressed('F11'):
            break
        
        # ПОЛЕ ДЛЯ ПАРОЛЯ (1.jpg)
        try:
            pos = pyautogui.locateOnScreen(PASSWORD_IMAGE, confidence=CONFIDENCE)
            if pos:
                pyautogui.click(pyautogui.center(pos))
                time.sleep(0.3)
                
                print("🔑 ВВОД ПАРОЛЯ:")
                
                # R (с Shift)
                press_key(VK['R'], shift=True)
                time.sleep(0.05)
                
                # o d i o n
                press_key(VK['O'])  # o
                time.sleep(0.05)
                press_key(VK['D'])  # d
                time.sleep(0.05)
                press_key(VK['I'])  # i
                time.sleep(0.05)
                press_key(VK['O'])  # o
                time.sleep(0.05)
                press_key(VK['N'])  # n
                time.sleep(0.05)
                
                # 4 6 0 6 8 3
                press_key(VK['4'])
                time.sleep(0.05)
                press_key(VK['6'])
                time.sleep(0.05)
                press_key(VK['0'])
                time.sleep(0.05)
                press_key(VK['6'])
                time.sleep(0.05)
                press_key(VK['8'])
                time.sleep(0.05)
                press_key(VK['3'])
                time.sleep(0.05)
                
                # Enter
                press_key(VK['ENTER'])
                
                stats[0] += 1
                print(f"✅ Пароль #{stats[0]} введен")
                time.sleep(1)
        except:
            pass
        
        # 2.jpg - клик
        try:
            pos = pyautogui.locateOnScreen(CLICK_IMAGE_1, confidence=CONFIDENCE)
            if pos:
                pyautogui.click(pyautogui.center(pos))
                stats[1] += 1
                print(f"🖱 2.jpg #{stats[1]}")
                time.sleep(1)
        except:
            pass
        
        # 3.png - клик
        try:
            pos = pyautogui.locateOnScreen(CLICK_IMAGE_2, confidence=CONFIDENCE)
            if pos:
                pyautogui.click(pyautogui.center(pos))
                stats[2] += 1
                print(f"🖱 3.png #{stats[2]}")
                time.sleep(1)
        except:
            pass
        
        # 4.jpg - клик
        try:
            pos = pyautogui.locateOnScreen(CLICK_IMAGE_3, confidence=CONFIDENCE)
            if pos:
                pyautogui.click(pyautogui.center(pos))
                stats[3] += 1
                print(f"🖱 4.jpg #{stats[3]}")
                time.sleep(1)
        except:
            pass
        
        time.sleep(SCAN_DELAY)
        
except KeyboardInterrupt:
    pass

print("\n" + "="*40)
print(f"📊 Статистика:")
print(f"   Паролей: {stats[0]}")
print(f"   2.jpg: {stats[1]}")
print(f"   3.png: {stats[2]}")
print(f"   4.jpg: {stats[3]}")
input("\nEnter для выхода...")