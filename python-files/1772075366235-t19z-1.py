import pyautogui
import cv2
import numpy as np
import easyocr
import time
from PIL import Image

# 初始化 OCR 阅读器（支持中文和英文）
reader = easyocr.Reader(['ch_sim', 'en'])

def select_area():
    """让用户通过鼠标拖拽选择区域，返回截图和区域坐标 (x, y, width, height)"""
    print("请将鼠标移动到区域左上角，按下并拖动到右下角，然后松开鼠标...")
    pyautogui.alert('点击确定后，立即用鼠标拖拽选择区域。')
    
    # 获取屏幕尺寸
    screen_width, screen_height = pyautogui.size()
    
    # 记录开始和结束坐标
    print("按下鼠标左键开始选择...")
    start_x, start_y = pyautogui.position()
    print(f"起点: ({start_x}, {start_y})")
    
    # 等待用户松开鼠标
    while pyautogui.mousePressed():
        time.sleep(0.1)
    end_x, end_y = pyautogui.position()
    print(f"终点: ({end_x}, {end_y})")
    
    # 计算区域
    x = min(start_x, end_x)
    y = min(start_y, end_y)
    width = abs(end_x - start_x)
    height = abs(end_y - start_y)
    
    # 截取区域
    screenshot = pyautogui.screenshot(region=(x, y, width, height))
    return screenshot, (x, y, width, height)

def calibrate_delete_button(region_coords):
    """让用户手动点击一个删除按钮，返回相对区域的偏移量"""
    print("请将鼠标移动到任意一个删除按钮上，然后按回车...")
    input("按回车键继续...")
    btn_x, btn_y = pyautogui.position()
    
    # 计算相对于区域左上角的偏移
    rel_x = btn_x - region_coords[0]
    rel_y = btn_y - region_coords[1]
    print(f"删除按钮相对坐标: ({rel_x}, {rel_y})")
    return rel_x, rel_y

def find_text_positions(image, keyword):
    """在图像中查找包含关键词的文本，返回每个文本的中心坐标列表"""
    # 将 PIL 图像转换为 OpenCV 格式
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # 使用 easyocr 识别文本
    results = reader.readtext(img_cv)
    
    positions = []
    for (bbox, text, confidence) in results:
        if keyword in text:
            # 计算文本中心点
            pts = np.array(bbox)
            center_x = int(np.mean(pts[:, 0]))
            center_y = int(np.mean(pts[:, 1]))
            positions.append((center_x, center_y))
            print(f"找到目标: '{text}' 在 ({center_x}, {center_y})")
    
    return positions

def click_positions(region_coords, positions, offset_x, offset_y):
    """点击每个目标位置偏移后的坐标"""
    base_x, base_y, _, _ = region_coords
    for (cx, cy) in positions:
        # 计算实际屏幕坐标
        click_x = base_x + cx + offset_x
        click_y = base_y + cy + offset_y
        pyautogui.click(click_x, click_y)
        print(f"点击 ({click_x}, {click_y})")
        time.sleep(0.3)  # 等待界面响应，可根据需要调整

def main():
    print("=== 自动删除门店项脚本 ===")
    
    # 步骤1：选择区域
    region_img, region_coords = select_area()
    print(f"已选择区域: {region_coords}")
    
    # 步骤2：校准删除按钮偏移
    offset_x, offset_y = calibrate_delete_button(region_coords)
    print(f"删除按钮偏移量: ({offset_x}, {offset_y})")
    
    # 步骤3：识别文本位置
    print("正在识别区域中的文本...")
    positions = find_text_positions(region_img, "门店")
    
    if not positions:
        print("未找到包含'门店'的文本。")
        return
    
    print(f"找到 {len(positions)} 个目标，准备点击...")
    
    # 步骤4：执行点击
    input("按回车键开始自动点击...")
    click_positions(region_coords, positions, offset_x, offset_y)
    
    print("完成！")

if __name__ == "__main__":
    main()