import cv2
import numpy as np
import pandas as pd
import os
from PIL import Image
import pytesseract
from pathlib import Path
import sys

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

IMAGE_LEFT_REGION = 0.25
MIN_LINE_LENGTH_RATIO = 0.6
MIN_BLOCK_HEIGHT = 150

def find_qa_blocks(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return None, []
    height, width = img.shape[:2]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)[1]

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (int(width * MIN_LINE_LENGTH_RATIO), 1))
    lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
    contours, _ = cv2.findContours(lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    y_positions = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w > width * MIN_LINE_LENGTH_RATIO and h < 10:
            y_positions.append(y)
    y_positions = sorted(list(set(y_positions))))

    blocks = []
    prev_y = 0
    for y in y_positions:
        if y - prev_y > MIN_BLOCK_HEIGHT:
            blocks.append((prev_y, y))
            prev_y = y
    if height - prev_y > MIN_BLOCK_HEIGHT:
        blocks.append((prev_y, height))

    return img, blocks

def crop_product_image_from_block(img, y1, y2):
    height, width = img.shape[:2]
    block_img = img[y1:y2, 0:int(width * IMAGE_LEFT_REGION)]
    block_gray = cv2.cvtColor(block_img, cv2.COLOR_BGR2GRAY)
    block_gray = cv2.GaussianBlur(block_gray, (5, 5), 0)

    edges = cv2.Canny(block_gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best_contour = None
    max_area = 0
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if 0.8 < w / h < 1.2 and w > 60 and h > 60:
            area = w * h
            if area > max_area:
                max_area = area
                best_contour = (x, y, w, h)

    if best_contour:
        x, y, w, h = best_contour
        cropped = block_img[y:y+h, x:x+w]
        return cropped
    return None

def extract_question_from_block(img, y1, y2):
    height, width = img.shape[:2]
    block_img = img[y1:y2, int(width * IMAGE_LEFT_REGION):]
    try:
        text = pytesseract.image_to_string(block_img, lang="chi_sim")
        return text.strip()
    except:
        return ""

def process_all_screenshots(folder_path):
    all_rows = []
    out_img_dir = "裁剪好的商品图"
    os.makedirs(out_img_dir, exist_ok=True)

    valid_suffix = (".jpg", ".jpeg", ".png")
    img_files = [f for f in Path(folder_path).glob("*") if f.suffix.lower() in valid_suffix]

    if not img_files:
        print("❌ 文件夹内未找到 jpg/png 图片！")
        input("按回车退出...")
        return

    for img_idx, img_file in enumerate(img_files):
        print(f"正在处理：{img_file.name}")
        img, blocks = find_qa_blocks(str(img_file))
        if not blocks:
            print(f"⚠️ 未识别到问答区块：{img_file.name}")
            continue

        product_imgs = []
        questions = []

        for block_idx, (y1, y2) in enumerate(blocks):
            cropped_img = crop_product_image_from_block(img, y1, y2)
            if cropped_img is not None:
                save_path = os.path.join(out_img_dir, f"{img_idx}_{block_idx}.jpg")
                cv2.imwrite(save_path, cropped_img)
                product_imgs.append(save_path)

            question = extract_question_from_block(img, y1, y2)
            if question:
                questions.append(question)

        row = {}
        for i, img_path in enumerate(product_imgs):
            row[f"商品图{i+1}"] = img_path
        row["问题合集"] = "\n".join(questions)
        all_rows.append(row)

    if all_rows:
        excel_name = "淘宝问答批量提取结果.xlsx"
        df = pd.DataFrame(all_rows)
        df.to_excel(excel_name, index=False)
        print(f"\n✅ 处理完成！")
        print(f"📁 裁剪图片目录：{out_img_dir}")
        print(f"📊 Excel 文件：{excel_name}")
    else:
        print("❌ 未解析到有效数据")

    input("\n全部执行完毕，按回车键关闭窗口...")

if __name__ == "__main__":
    print("=" * 50)
    print("      淘宝问大家 智能切图+文字提取工具")
    print("  使用方法：直接把截图文件夹拖拽到本窗口")
    print("=" * 50)

    if len(sys.argv) > 1:
        target_folder = sys.argv[1]
    else:
        target_folder = input("请粘贴截图文件夹完整路径：").strip().strip('"')

    if not os.path.isdir(target_folder):
        print("❌ 路径无效，请检查文件夹地址！")
        input("按回车退出...")
        sys.exit()

    process_all_screenshots(target_folder)