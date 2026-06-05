import fitz  # PyMuPDF
import pandas as pd
import os
import numpy as np
import cv2
from rapidocr_onnxruntime import RapidOCR

# --- 配置路径 ---
pdf_path = r"G:\1、成考（2026年开始叫非脱产）\2、历年成招录取名单花名册扫描件\1993-2024年成人高校统一招生考试录取名单\2023年录取花名册\2023年录取2024级花名册标记版\2023年录取2024级花名册标记版合并.pdf"
excel_path = r"G:\1、成考（2026年开始叫非脱产）\2、历年成招录取名单花名册扫描件\1993-2024年成人高校统一招生考试录取名单\2023年录取花名册\2023年录取2024级花名册标记版\导入系统2023年录取学生模板总表2674人.xls"
output_dir = r"G:\1、成考（2026年开始叫非脱产）\2、历年成招录取名单花名册扫描件\1993-2024年成人高校统一招生考试录取名单\2023年录取花名册\2023年录取2024级花名册标记版\2023年录取2024级花名册标记版合并-20260605.pdf"

final_output_filename = os.path.join(output_dir, "2023年录取2024级花名册标记版合并-20260605.pdf")
font_file = "C:/Windows/Fonts/msyh.ttc"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)


def preprocess_image_for_ocr(img_array):
    """图像预处理：灰度化 + 二值化增强对比度"""
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    processed_img = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
    return processed_img


def clean_cell(value):
    """把 Excel 空值统一处理为空字符串。"""
    if pd.isna(value):
        return ""
    return str(value).strip()


def process_and_merge_compressed():
    print("正在读取Excel数据...")
    df_excel = pd.read_excel(excel_path, dtype=str)
    df_excel.columns = df_excel.columns.str.strip()

    # 确保需要的列都在
    required_cols = ['考生号', '姓名', '学号', '证件号', '班级']
    for col in required_cols:
        if col not in df_excel.columns:
            if col == '学号':
                df_excel['学号'] = ""
            else:
                print(f"Excel中找不到 '{col}' 列，请检查表头！")
                return

    excel_records = df_excel.to_dict('records')

    print("正在初始化 OCR 引擎...")
    engine = RapidOCR()

    doc = fitz.open(pdf_path)
    final_pdf = fitz.open()
    match_count = 0

    # 全局记录已处理的考生号，确保绝对不重复
    processed_ksh = set()

    for page_num in range(len(doc)):
        print(f"\n正在处理原始第 {page_num + 1} 页...")
        page = doc[page_num]

        zoom = 2.5
        mat = fitz.Matrix(zoom, zoom)
        pix_high_res = page.get_pixmap(matrix=mat)

        img_array = np.frombuffer(pix_high_res.samples, dtype=np.uint8).reshape(pix_high_res.h, pix_high_res.w,
                                                                                pix_high_res.n)
        if pix_high_res.n == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
        elif pix_high_res.n == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        img_array = preprocess_image_for_ocr(img_array)

        result, _ = engine(img_array)
        if result is None:
            continue

        bg_pix = page.get_pixmap(dpi=360)
        bg_bytes = bg_pix.tobytes("jpg", 80)
        page_rect = page.rect

        for line in result:
            box = line[0]
            # 去除所有空格，转为大写（统一处理身份证X）
            text = line[1].replace(" ", "").strip().upper()

            matched_row = None

            # 终极精确匹配逻辑：拿 Excel 里的长号码去文本里找
            # 解决 OCR 把序号(如77) 和 考生号 连在一起识别的问题
            for row in excel_records:
                excel_ksh = clean_cell(row.get('考生号', ''))
                excel_sfz = clean_cell(row.get('证件号', '')).upper()

                # 必须保证是长号码（防误撞），并且完整存在于 OCR 识别的这一行里
                # 考生号通常是 14 位，身份证是 18 位
                if (len(excel_ksh) >= 14 and excel_ksh in text) or \
                   (len(excel_sfz) >= 15 and excel_sfz in text):
                    matched_row = row
                    break

            if matched_row:
                ksh = clean_cell(matched_row.get('考生号', ''))

                # 核心去重：同一个考生号绝不生成两遍
                if ksh in processed_ksh:
                    continue

                processed_ksh.add(ksh)
                name = clean_cell(matched_row.get('姓名', ''))
                student_id = clean_cell(matched_row.get('学号', ''))
                class_name = clean_cell(matched_row.get('班级', ''))

                y_pos_ocr = (box[0][1] + box[3][1]) / 2
                y_pos_pdf = y_pos_ocr / zoom

                # 勾号的 X 坐标
                x_pos_check = 25

                new_page = final_pdf.new_page(width=page_rect.width, height=page_rect.height)
                new_page.insert_image(page_rect, stream=bg_bytes)

                text_to_add = "  ".join(part for part in [name, student_id, class_name] if part)
                new_page.insert_text((40, 40), text_to_add, fontname="msyh", fontfile=font_file, fontsize=14,
                                     color=(0, 0, 0))
                new_page.insert_text((x_pos_check, y_pos_pdf + 4), "√", fontname="msyh", fontfile=font_file,
                                     fontsize=12, color=(0, 0, 0))

                match_count += 1
                print(f"  √ 成功匹配第 {match_count} 个考生: {name} (考生号: {ksh})")

    doc.close()

    print(f"\n正在保存合并文件，共包含 {match_count} 页...")
    final_pdf.save(final_output_filename, garbage=4, deflate=True)
    final_pdf.close()

    print(f"全部处理完成！精确定位了 {match_count} 人。文件已保存至：{final_output_filename}")


if __name__ == "__main__":
    process_and_merge_compressed()
