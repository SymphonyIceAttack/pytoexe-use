import pyautogui
import keyboard
import time
import math
import random
from threading import Thread

class MegaCheat:
    def __init__(self):
        self.running = True
        self.screen_w, self.screen_h = pyautogui.size()
        self.center_x, self.center_y = self.screen_w // 2, self.screen_h // 2
        
        self.modes = {
            'killaura': False,
            'aimbot': False,
            'auto_click': False,
            'trigger': False
        }
        
        self.settings = {
            'cps': 12,
            'range': 4.5,
            'smooth': 5
        }
        
        print("""
╔═══════════════════════════════════╗
║        MEGA CHEAT 24H            ║
╠═══════════════════════════════════╣
║ [F1] KillAura                     ║
║ [F2] Aimbot                       ║
║ [F3] AutoClick                    ║
║ [F4] TriggerBot                   ║
║ [0]  Выключить всё                ║
║ [F6] Выход                        ║
║                                   ║
║ [=] + CPS  [-] - CPS              ║
╚═══════════════════════════════════╝
        """)
        
    def find_enemy(self):
        try:
            screenshot = pyautogui.screenshot(region=(
                self.center_x - 150, self.center_y - 150, 300, 300
            ))
            
            for x in range(0, 300, 15):
                for y in range(0, 300, 15):
                    try:
                        r, g, b = screenshot.getpixel((x, y))
                        if (g > 80 and g < 200) or (r > 150 and g > 150):
                            return (
                                self.center_x - 150 + x,
                                self.center_y - 150 + y
                            )
                    except:
                        continue
            return None
        except:
            return None
    
    def killaura_thread(self):
        while self.running:
            if self.modes['killaura']:
                enemy = self.find_enemy()
                if enemy:
                    dx = enemy[0] - self.center_x
                    dy = enemy[1] - self.center_y
                    if abs(dx) < 200 and abs(dy) < 200:
                        pyautogui.click()
                        time.sleep(1.0/self.settings['cps'])
            time.sleep(0.01)
    
    def aimbot_thread(self):
        while self.running:
            if self.modes['aimbot']:
                enemy = self.find_enemy()
                if enemy:
                    dx = enemy[0] - self.center_x
                    dy = enemy[1] - self.center_y
                    pyautogui.moveRel(dx//self.settings['smooth'], 
                                    dy//self.settings['smooth'])
            time.sleep(0.01)
    
    def auto_click_thread(self):
        while self.running:
            if self.modes['auto_click']:
                pyautogui.click()
                time.sleep(0.05)
            time.sleep(0.01)
    
    def trigger_thread(self):
        while self.running:
            if self.modes['trigger']:
                pixel = pyautogui.pixel(self.center_x, self.center_y)
                if pixel[0] > 150 or pixel[1] > 150:
                    pyautogui.click()
            time.sleep(0.01)
    
    def ui(self):
        while self.running:
            if keyboard.is_pressed('f6'):
                self.running = False
                break
                
            if keyboard.is_pressed('f1'):
                self.modes['killaura'] = not self.modes['killaura']
                print(f"KillAura: {'ON' if self.modes['killaura'] else 'OFF'}")
                time.sleep(0.2)
                
            if keyboard.is_pressed('f2'):
                self.modes['aimbot'] = not self.modes['aimbot']
                print(f"Aimbot: {'ON' if self.modes['aimbot'] else 'OFF'}")
                time.sleep(0.2)
                
            if keyboard.is_pressed('f3'):
                self.modes['auto_click'] = not self.modes['auto_click']
                print(f"AutoClick: {'ON' if self.modes['auto_click'] else 'OFF'}")
                time.sleep(0.2)
                
            if keyboard.is_pressed('f4'):
                self.modes['trigger'] = not self.modes['trigger']
                print(f"Trigger: {'ON' if self.modes['trigger'] else 'OFF'}")
                time.sleep(0.2)
                
            if keyboard.is_pressed('0'):
                for m in self.modes: self.modes[m] = False
                print("ALL OFF")
                time.sleep(0.2)
                
            if keyboard.is_pressed('='):
                self.settings['cps'] = min(20, self.settings['cps'] + 1)
                print(f"CPS: {self.settings['cps']}")
                time.sleep(0.1)
                
            if keyboard.is_pressed('-'):
                self.settings['cps'] = max(1, self.settings['cps'] - 1)
                print(f"CPS: {self.settings['cps']}")
                time.sleep(0.1)
            
            time.sleep(0.05)
    
    def run(self):
        threads = [
            Thread(target=self.killaura_thread),
            Thread(target=self.aimbot_thread),
            Thread(target=self.auto_click_thread),
            Thread(target=self.trigger_thread),
            Thread(target=self.ui)
        ]
        
        for t in threads:
            t.daemon = True
            t.start()
        
        try:
            while self.running:
                time.sleep(0.1)
        except:
            pass

if __name__ == "__main__":
    cheat = MegaCheat()
    cheat.run()
