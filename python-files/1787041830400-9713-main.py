import os
import re
import sys
from pathlib import Path

# 以下库需要安装，稍后我们会用 PyCharm 安装
from paddleocr import PaddleOCR
import fitz  # PyMuPDF
from PIL import Image
import pandas as pd

# ---------- 1. 初始化 OCR 引擎 ----------
ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)

# ---------- 2. 分类规则（可自行增删） ----------
CATEGORY_RULES = {
    '餐饮费': ['餐厅', '餐饮', '美食', '咖啡', '茶馆', '酒楼', '食堂', '外卖', '肯德基', '麦当劳', '星巴克'],
    '交通费': ['出租车', '滴滴', '地铁', '公交', '高铁', '机票', '火车', '加油', '停车', 'ETC', '打车'],
    '办公用品': ['文具', '打印', '纸张', '办公', '电脑', '鼠标', '键盘', 'U盘', '复印', '办公用品'],
    '差旅费': ['酒店', '住宿', '旅店', '宾馆', '民宿', '携程', '飞猪', '如家', '汉庭', '希尔顿'],
    '通讯费': ['话费', '流量', '宽带', '电信', '移动', '联通', '缴费'],
    '其他': []
}

def classify_expense(text):
    if not text:
        return '其他'
    text_lower = text.lower()
    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category
    return '其他'

# ---------- 3. 金额和发票号码提取 ----------
def extract_info_from_text(full_text):
    invoice_no = None
    total_amount = None

    # 提取发票号码（8-12位数字）
    match = re.search(r'发票号码[:：]\s*(\d{8,12})', full_text)
    if match:
        invoice_no = match.group(1)

    # 多种金额匹配模式（按优先级）
    patterns = [
        r'价税合计[^¥￥]*[¥￥]\s*([\d,]+\.\d{2})',
        r'[合计共]计[:：]?\s*[¥￥]\s*([\d,]+\.\d{2})',
        r'小写[金额]?[:：]?\s*[¥￥]\s*([\d,]+\.\d{2})',
        r'总金额[:：]?\s*[¥￥]\s*([\d,]+\.\d{2})',
    ]
    for pattern in patterns:
        match = re.search(pattern, full_text)
        if match:
            total_amount = float(match.group(1).replace(',', ''))
            return invoice_no, total_amount

    # 如果上面没匹配到，尝试匹配所有 "¥" 或 "￥" 后的数字，取最后一个
    all_money = re.findall(r'[¥￥]\s*([\d,]+\.\d{2})', full_text)
    if all_money:
        total_amount = float(all_money[-1].replace(',', ''))
        return invoice_no, total_amount

    # 最终兜底：匹配所有两位小数的数字，取最后一个
    all_decimals = re.findall(r'\b\d{1,3}(?:,\d{3})*\.\d{2}\b', full_text)
    if all_decimals:
        total_amount = float(all_decimals[-1].replace(',', ''))

    return invoice_no, total_amount

# ---------- 4. 文件处理（PDF 或 图片） ----------
def process_file(file_path):
    file_path = Path(file_path)
    # 处理 PDF
    if file_path.suffix.lower() == '.pdf':
        images = []
        pdf_document = fitz.open(file_path)
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            mat = fitz.Matrix(2.0, 2.0)      # 提高分辨率
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        pdf_document.close()
        all_text = ""
        for idx, img in enumerate(images):
            temp_path = f"temp_page_{idx}.png"
            img.save(temp_path)
            result = ocr.ocr(temp_path, cls=True)
            os.remove(temp_path)
            if result and result[0]:
                for line in result[0]:
                    all_text += line[1][0] + "\n"
        return all_text
    # 处理图片
    else:
        result = ocr.ocr(str(file_path), cls=True)
        if not result or not result[0]:
            return ""
        full_text = ""
        for line in result[0]:
            full_text += line[1][0] + "\n"
        return full_text

# ---------- 5. 主程序 ----------
def main():
    # 获取当前程序所在目录（如果是打包后的exe，则获取exe所在目录）
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent

    folder_path = base_dir / "invoices"

    if not folder_path.exists():
        print(f"错误: 请在与本程序同级的 'invoices' 文件夹中放入发票文件！")
        input("按回车键退出...")
        return

    results = []
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.pdf'}

    print("=" * 50)
    print("发票识别工具 v1.0")
    print(f"扫描文件夹: {folder_path}")
    print("=" * 50)

    for file_path in folder_path.iterdir():
        if file_path.suffix.lower() in image_extensions:
            print(f"\n正在处理: {file_path.name}...")
            try:
                full_text = process_file(file_path)
                if not full_text:
                    print(f"  ⚠️ 未能识别出文字")
                    results.append({
                        '文件名': file_path.name,
                        '发票号码': None,
                        '金额': None,
                        '类别': '其他',
                    })
                    continue

                invoice_no, amount = extract_info_from_text(full_text)
                if amount is None:
                    print(f"  ⚠️ 未能提取到金额")
                    results.append({
                        '文件名': file_path.name,
                        '发票号码': invoice_no,
                        '金额': None,
                        '类别': '其他',
                    })
                    continue

                category = classify_expense(full_text)
                results.append({
                    '文件名': file_path.name,
                    '发票号码': invoice_no,
                    '金额': amount,
                    '类别': category,
                })
                print(f"  ✅ 金额: {amount}, 分类: {category}")

            except Exception as e:
                print(f"  ❌ 处理出错: {e}")
                results.append({
                    '文件名': file_path.name,
                    '发票号码': None,
                    '金额': None,
                    '类别': '其他',
                })

    if not results:
        print("\n没有提取到任何数据。")
        input("按回车键退出...")
        return

    # 转为 DataFrame
    df = pd.DataFrame(results)
    # 筛选出成功提取金额的进行汇总
    df_success = df[df['金额'].notna()]
    if not df_success.empty:
        summary = df_success.groupby('类别')['金额'].sum().reset_index()
        summary.columns = ['类别', '费用总和']
    else:
        summary = pd.DataFrame(columns=['类别', '费用总和'])

    output_path = base_dir / "发票汇总.xlsx"
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='发票明细', index=False)
        summary.to_excel(writer, sheet_name='类别汇总', index=False)

    print("\n" + "=" * 50)
    print(f"✅ 处理完成！结果已导出到: {output_path}")
    if not summary.empty:
        print("\n--- 各类别费用总和 ---")
        print(summary.to_string(index=False))
    print("=" * 50)
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()