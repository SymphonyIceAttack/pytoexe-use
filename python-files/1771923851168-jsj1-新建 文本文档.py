#!/usr/bin/env python3
"""
跳一跳辅助脚本（学习版）
功能：通过图像识别自动计算跳跃距离并模拟点击
运行环境：需要安装Python及相关库
警告：仅限个人学习自动化技术使用，滥用可能导致账号限制
"""

import cv2
import numpy as np
import pyautogui
import time
import math

class JumpHelper:
    def __init__(self):
        # 颜色阈值（根据您的游戏画面调整）
        self.chessman_color_lower = np.array([130, 50, 50])    # 深紫色棋子HSV下限
        self.chessman_color_upper = np.array([160, 255, 200])  # 深紫色棋子上限
        self.platform_color_lower = np.array([35, 100, 100])   # 绿色平台HSV下限
        self.platform_color_upper = np.array([85, 255, 255])   # 绿色平台上限
        
        # 跳跃系数（需要根据实际情况调整）
        self.jump_coefficient = 1.35
        
    def capture_screen(self):
        """捕获当前屏幕"""
        screenshot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    def find_chessman(self, image):
        """定位棋子位置"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.chessman_color_lower, self.chessman_color_upper)
        
        # 形态学处理
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            # 取面积最大的轮廓
            largest_contour = max(contours, key=cv2.contourArea)
            moments = cv2.moments(largest_contour)
            if moments["m00"] > 0:
                cx = int(moments["m10"] / moments["m00"])
                cy = int(moments["m01"] / moments["m00"])
                return (cx, cy + 50)  # 返回棋子底部位置
        return None
    
    def find_target_platform(self, image, chessman_pos):
        """找到目标平台"""
        if chessman_pos is None:
            return None
            
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.platform_color_lower, self.platform_color_upper)
        
        # 排除棋子所在区域
        height, width = mask.shape
        chessman_mask = np.zeros((height, width), dtype=np.uint8)
        cv2.circle(chessman_mask, chessman_pos, 100, 255, -1)
        mask = cv2.bitwise_and(mask, cv2.bitwise_not(chessman_mask))
        
        # 查找轮廓并过滤
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        valid_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if 500 < area < 50000:  # 根据实际情况调整
                valid_contours.append(contour)
        
        if valid_contours:
            # 找到最可能的目标平台（x坐标大于棋子位置）
            target_contours = [c for c in valid_contours 
                             if cv2.boundingRect(c)[0] > chessman_pos[0]]
            if target_contours:
                target = max(target_contours, key=cv2.contourArea)
                moments = cv2.moments(target)
                if moments["m00"] > 0:
                    return (int(moments["m10"] / moments["m00"]), 
                            int(moments["m01"] / moments["m00"]))
        return None
    
    def calculate_distance(self, point1, point2):
        """计算两点间距离"""
        return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)
    
    def jump(self, distance):
        """执行跳跃操作"""
        press_time = distance * self.jump_coefficient / 1000  # 转换为秒
        
        # 模拟鼠标按下（空格键或点击）
        pyautogui.mouseDown()
        time.sleep(press_time)
        pyautogui.mouseUp()
        
        print(f"跳跃距离：{distance:.1f}像素，按压时间：{press_time:.3f}秒")
        return press_time
    
    def run(self):
        """主循环"""
        print("跳一跳辅助工具启动（按Ctrl+C停止）")
        print("请在3秒内切换到游戏窗口...")
        time.sleep(3)
        
        while True:
            try:
                # 1. 截屏
                screen = self.capture_screen()
                
                # 2. 定位棋子
                chessman_pos = self.find_chessman(screen)
                if chessman_pos is None:
                    print("未找到棋子，等待1秒...")
                    time.sleep(1)
                    continue
                
                # 3. 定位目标平台
                target_pos = self.find_target_platform(screen, chessman_pos)
                if target_pos is None:
                    print("未找到目标平台，等待1秒...")
                    time.sleep(1)
                    continue
                
                # 4. 计算距离并跳跃
                distance = self.calculate_distance(chessman_pos, target_pos)
                if 50 < distance < 800:  # 合理距离范围
                    self.jump(distance)
                    time.sleep(2)  # 等待跳跃完成
                else:
                    print(f"距离异常：{distance}，跳过")
                    time.sleep(0.5)
                    
            except KeyboardInterrupt:
                print("\n用户中断，程序退出")
                break
            except Exception as e:
                print(f"发生错误：{e}")
                time.sleep(1)

if __name__ == "__main__":
    # 免责声明
    print("=" * 60)
    print("跳一跳自动化学习脚本")
    print("警告：")
    print("1. 本代码仅用于学习图像识别和自动化技术")
    print("2. 请勿用于破坏游戏公平性")
    print("3. 使用产生的一切后果由使用者自行承担")
    print("=" * 60)
    
    # 安装提示
    try:
        import cv2
        import pyautogui
    except ImportError:
        print("请先安装依赖库：")
        print("pip install opencv-python numpy pyautogui")
        exit(1)
    
    # 运行前确认
    response = input("确认仅用于学习研究？(输入y继续): ")
    if response.lower() == 'y':
        helper = JumpHelper()
        helper.run()
    else:
        print("已取消运行")