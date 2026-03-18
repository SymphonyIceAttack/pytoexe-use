#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pyautogui
import pyperclip
import time
import keyboard
import json
import os
import sys
from datetime import datetime

# 配置
CONFIG_FILE = "positions.json"
LOG_FILE = "auto_log.txt"
DEFAULT_PAUSE = 0.3
CYCLE_INTERVAL = 3

DEFAULT_POSITIONS = {
    "table_window": {"x": 200, "y": 200},
    "table_data_cell": {"x": 300, "y": 300},
    "web_window": {"x": 800, "y": 200},
    "web_input1": {"x": 400, "y": 300},
    "web_input2": {"x": 400, "y": 350},
    "web_input3": {"x": 400, "y": 400},
    "web_data1": {"x": 600, "y": 300},
    "web_data2": {"x": 600, "y": 350},
    "web_button": {"x": 500, "y": 450}
}

class AutoTransfer:
    def __init__(self):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = DEFAULT_PAUSE
        self.positions = DEFAULT_POSITIONS.copy()
        self.load_config()
        self.cycle_count = 0
        self.success = 0
        self.fail = 0
        self.running = False
        
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(f"=== 自动化工具启动于 {datetime.now()} ===\n")
    
    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {msg}"
        print(log_msg)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_msg + "\n")
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.positions.update(saved)
                self.log(f"已加载配置: {CONFIG_FILE}")
            except:
                self.log("配置文件加载失败，使用默认配置")
    
    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.positions, f, indent=2, ensure_ascii=False)
            self.log(f"配置已保存到 {CONFIG_FILE}")
            return True
        except:
            self.log("配置保存失败")
            return False
    
    def click(self, name, double=False):
        if name not in self.positions:
            self.log(f"错误：未找到位置 '{name}'")
            return False
        
        pos = self.positions[name]
        try:
            pyautogui.moveTo(pos['x'], pos['y'], duration=0.2)
            time.sleep(0.1)
            if double:
                pyautogui.doubleClick()
                self.log(f"双击: {name}")
            else:
                pyautogui.click()
                self.log(f"单击: {name}")
            return True
        except Exception as e:
            self.log(f"点击失败 {name}: {e}")
            return False
    
    def copy(self):
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.2)
        data = pyperclip.paste()
        self.log(f"复制: {data[:30]}..." if len(data) > 30 else f"复制: {data}")
        return data
    
    def paste(self, text=None):
        if text is not None:
            pyperclip.copy(text)
            time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'v')
        self.log(f"粘贴: {text[:30]}..." if text and len(text) > 30 else f"粘贴: {text}")
        return True
    
    def switch_to(self, window_name):
        if window_name in self.positions:
            pyautogui.moveTo(self.positions[window_name]['x'], 
                           self.positions[window_name]['y'], 
                           duration=0.3)
            pyautogui.click()
            time.sleep(0.5)
            self.log(f"切换到: {window_name}")
            return True
        return False
    
    def do_cycle(self):
        self.cycle_count += 1
        self.log(f"\n>>> 开始第 {self.cycle_count} 个循环 <<<")
        
        try:
            if not self.switch_to("table_window"):
                raise Exception("无法切换到表格")
            
            if not self.click("table_data_cell"):
                raise Exception("无法点击表格数据")
            
            data1 = self.copy()
            if not data1:
                raise Exception("复制失败")
            
            if not self.switch_to("web_window"):
                raise Exception("无法切换到网页")
            
            for i in [1, 2, 3]:
                self.click(f"web_input{i}")
                time.sleep(0.2)
            
            self.paste(data1)
            self.click("web_button")
            
            if not self.click("web_data1", double=True):
                raise Exception("无法双击数据1")
            
            data2 = self.copy()
            
            self.click("web_button")
            time.sleep(0.2)
            self.click("web_button")
            
            self.paste(data2)
            self.click("web_button")
            
            if not self.click("web_data2", double=True):
                raise Exception("无法双击数据2")
            
            data3 = self.copy()
            
            if not self.switch_to("table_window"):
                raise Exception("无法切换回表格")
            
            self.paste(data3)
            
            self.success += 1
            self.log(f"✓ 第 {self.cycle_count} 个循环完成")
            return True
            
        except Exception as e:
            self.fail += 1
            self.log(f"✗ 第 {self.cycle_count} 个循环失败: {e}")
            pyautogui.press('esc')
            time.sleep(1)
            return False
    
    def calibrate(self):
        print("\n" + "="*50)
        print("位置校准模式")
        print("="*50)
        print("操作说明：")
        print("  - 将鼠标移动到目标位置")
        print("  - 按 's' 记录当前位置")
        print("  - 按 'n' 跳过当前步骤")
        print("  - 按 'q' 保存并退出")
        print("="*50)
        
        for key in self.positions.keys():
            print(f"\n当前位置：{key}")
            print(f"  当前坐标：{self.positions[key]}")
            print("  移动到目标位置后按 's'...")
            
            while True:
                if keyboard.is_pressed('s'):
                    x, y = pyautogui.position()
                    self.positions[key] = {"x": x, "y": y}
                    print(f"  ✓ 已记录: ({x}, {y})")
                    time.sleep(0.3)
                    break
                if keyboard.is_pressed('n'):
                    print(f"  → 跳过: {key}")
                    time.sleep(0.3)
                    break
                if keyboard.is_pressed('q'):
                    self.save_config()
                    print("\n校准完成并保存")
                    return
                time.sleep(0.1)
        
        self.save_config()
        print("\n所有位置校准完成！")
    
    def show_stats(self):
        print("\n" + "="*40)
        print("运行统计")
        print("="*40)
        print(f"总循环: {self.cycle_count}")
        print(f"成功: {self.success}")
        print(f"失败: {self.fail}")
        if self.cycle_count > 0:
            rate = (self.success / self.cycle_count) * 100
            print(f"成功率: {rate:.1f}%")
        print("="*40)
    
    def show_positions(self):
        x, y = pyautogui.position()
        print(f"\n当前鼠标位置: ({x}, {y})")
        print("附近的位置：")
        for name, pos in self.positions.items():
            distance = ((pos['x'] - x) ** 2 + (pos['y'] - y) ** 2) ** 0.5
            if distance < 100:
                print(f"  {name}: {pos} (距离 {distance:.0f})")
    
    def run_continuous(self):
        if self.running:
            self.log("已经在运行中")
            return
        
        self.running = True
        self.log("\n=== 开始连续运行模式 ===")
        self.log("按 F12 停止")
        
        try:
            while self.running:
                self.do_cycle()
                self.show_stats()
                
                for i in range(CYCLE_INTERVAL, 0, -1):
                    if not self.running:
                        break
                    print(f"下一循环倒计时: {i} 秒", end='\r')
                    time.sleep(1)
                print(" " * 30, end='\r')
                
        except KeyboardInterrupt:
            self.log("用户中断")
        finally:
            self.running = False
            self.log("连续运行已停止")
    
    def stop(self):
        self.running = False
        self.log("正在停止...")


def main():
    print("\n" + "="*60)
    print("     表格-网页数据同步自动化工具 v1.0")
    print("="*60)
    print("\n📋 准备工作：")
    print("  1. 打开表格软件和网页")
    print("  2. 按 F3 校准所有位置")
    print("  3. 按 F1 开始自动运行")
    print("\n🎮 快捷键：")
    print("  F1 - 连续运行")
    print("  F2 - 单次运行")
    print("  F3 - 校准位置")
    print("  F4 - 显示当前位置")
    print("  F5 - 显示统计")
    print("  F12 - 停止")
    print("  ESC - 退出程序")
    print("="*60)
    print("\n⚠️ 紧急停止：快速将鼠标移到屏幕左上角")
    print("="*60)
    
    auto = AutoTransfer()
    
    keyboard.add_hotkey('f1', lambda: auto.run_continuous())
    keyboard.add_hotkey('f2', lambda: auto.do_cycle())
    keyboard.add_hotkey('f3', lambda: auto.calibrate())
    keyboard.add_hotkey('f4', lambda: auto.show_positions())
    keyboard.add_hotkey('f5', lambda: auto.show_stats())
    keyboard.add_hotkey('f12', lambda: auto.stop())
    
    try:
        keyboard.wait('esc')
    except:
        pass
    finally:
        print("\n程序已退出")
        auto.show_stats()
        input("\n按回车键关闭窗口...")


if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    main()