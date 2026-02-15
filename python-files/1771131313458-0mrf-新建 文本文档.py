import os
import shutil
from PIL import Image
from typing import Optional

# 颜色判定规则
COLOR_FOLDERS = {
    "红色": {"r_min": 150, "g_max": 100, "b_max": 100},
    "黄色": {"r_min": 200, "g_min": 180, "b_max": 100},
    "蓝色": {"r_max": 100, "g_max": 120, "b_min": 150},
    "绿色": {"r_max": 100, "g_min": 150, "b_max": 120},
    "粉色": {"r_min": 200, "g_min": 150, "b_min": 180, "r_gap": 50, "b_gap": 30},
    "紫色": {"r_min": 150, "g_max": 120, "b_min": 150},
    "白色": {"r_min": 220, "g_min": 220, "b_min": 220},
    "黑色": {"r_max": 50, "g_max": 50, "b_max": 50}
}
SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')

def get_average_rgb(image_path: str) -> Optional[tuple[int, int, int]]:
    try:
        with Image.open(image_path) as img:
            img = img.resize((100, 100)).convert('RGB')
            pixels = list(img.getdata())
            total_r = total_g = total_b = 0
            for r, g, b in pixels:
                total_r += r
                total_g += g
                total_b += b
            avg_r = total_r // len(pixels)
            avg_g = total_g // len(pixels)
            avg_b = total_b // len(pixels)
            return (avg_r, avg_g, avg_b)
    except Exception as e:
        print(f"读取图片 {image_path} 失败：{e}")
        return None

def determine_main_color(avg_rgb: tuple[int, int, int]) -> str:
    r, g, b = avg_rgb
    if r >= COLOR_FOLDERS["白色"]["r_min"] and g >= COLOR_FOLDERS["白色"]["g_min"] and b >= COLOR_FOLDERS["白色"]["b_min"]:
        return "白色"
    elif r <= COLOR_FOLDERS["黑色"]["r_max"] and g <= COLOR_FOLDERS["黑色"]["g_max"] and b <= COLOR_FOLDERS["黑色"]["b_max"]:
        return "黑色"
    elif (r >= COLOR_FOLDERS["粉色"]["r_min"] and g >= COLOR_FOLDERS["粉色"]["g_min"] and 
          b >= COLOR_FOLDERS["粉色"]["b_min"] and r - g < COLOR_FOLDERS["粉色"]["r_gap"] and 
          g - b < COLOR_FOLDERS["粉色"]["b_gap"]):
        return "粉色"
    elif r >= COLOR_FOLDERS["紫色"]["r_min"] and g <= COLOR_FOLDERS["紫色"]["g_max"] and b >= COLOR_FOLDERS["紫色"]["b_min"]:
        return "紫色"
    elif r >= COLOR_FOLDERS["红色"]["r_min"] and g <= COLOR_FOLDERS["红色"]["g_max"] and b <= COLOR_FOLDERS["红色"]["b_max"]:
        return "红色"
    elif r >= COLOR_FOLDERS["黄色"]["r_min"] and g >= COLOR_FOLDERS["黄色"]["g_min"] and b <= COLOR_FOLDERS["黄色"]["b_max"]:
        return "黄色"
    elif r <= COLOR_FOLDERS["蓝色"]["r_max"] and g <= COLOR_FOLDERS["蓝色"]["g_max"] and b >= COLOR_FOLDERS["蓝色"]["b_min"]:
        return "蓝色"
    elif r <= COLOR_FOLDERS["绿色"]["r_max"] and g >= COLOR_FOLDERS["绿色"]["g_min"] and b <= COLOR_FOLDERS["绿色"]["b_max"]:
        return "绿色"
    else:
        return "其他颜色"

def create_color_folders(base_dir: str) -> None:
    all_folders = list(COLOR_FOLDERS.keys()) + ["其他颜色"]
    for folder in all_folders:
        folder_path = os.path.join(base_dir, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"创建文件夹：{folder_path}")

def classify_images_by_color(source_dir: str, target_base_dir: str, copy_mode: bool = True) -> None:
    create_color_folders(target_base_dir)
    file_count = 0
    success_count = 0
    for filename in os.listdir(source_dir):
        if not filename.lower().endswith(SUPPORTED_FORMATS):
            continue
        file_count += 1
        source_path = os.path.join(source_dir, filename)
        if os.path.isdir(source_path):
            continue
        
        avg_rgb = get_average_rgb(source_path)
        if not avg_rgb:
            continue
        
        main_color = determine_main_color(avg_rgb)
        target_folder = os.path.join(target_base_dir, main_color)
        target_path = os.path.join(target_folder, filename)
        
        counter = 1
        while os.path.exists(target_path):
            name, ext = os.path.splitext(filename)
            target_path = os.path.join(target_folder, f"{name}_{counter}{ext}")
            counter += 1
        
        try:
            if copy_mode:
                shutil.copy2(source_path, target_path)
            else:
                shutil.move(source_path, target_path)
            success_count += 1
            print(f"[{success_count}] {filename} -> {main_color}")
        except Exception as e:
            print(f"处理 {filename} 失败：{e}")
    
    print(f"\n===== 分类完成 ======")
    print(f"扫描文件总数：{file_count}")
    print(f"成功分类：{success_count}")
    print(f"失败数量：{file_count - success_count}")
    input("\n按回车键退出程序...")  # 防止运行完成后闪退

def main():
    print("===== 图片按颜色分类工具 =====")
    source_dir = input("请输入待分类图片的文件夹路径：").strip()
    if not os.path.isdir(source_dir):
        print(f"错误：目录 {source_dir} 不存在！")
        input("按回车键退出...")
        return
    
    target_dir = input("请输入分类后图片存放的基础文件夹路径：").strip()
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"创建基础目录：{target_dir}")
    
    mode_choice = input("请选择处理模式（1=复制图片，2=移动图片，默认1）：").strip()
    copy_mode = True if mode_choice != "2" else False
    
    print("\n开始分类图片...")
    classify_images_by_color(source_dir, target_dir, copy_mode)

if __name__ == "__main__":
    main()