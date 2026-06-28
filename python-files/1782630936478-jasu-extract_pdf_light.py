import os
import re
import pdfplumber
from glob import glob
from openpyxl import Workbook

def extract_info_from_pdf(pdf_path):
    """从单个PDF中提取所需字段"""
    full_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
    except Exception as e:
        print(f"⚠️ 读取 {os.path.basename(pdf_path)} 出错: {e}")
        return None

    # 正则匹配
    patterns = {
        "Student Name": r"Student Name:\s*(.+)",
        "Address": r"Address:\s*(.+)",
        "City": r"City:\s*(.+)",
        "State": r"State:\s*(.+)",
        "Postal Code": r"Postal Code:\s*(.+)",
        "Date of Birth": r"Date of Birth:\s*(.+)",
        "SSN": r"Social Security Number:\s*(.+)",
    }

    data = {}
    for key, pat in patterns.items():
        match = re.search(pat, full_text, re.IGNORECASE)
        data[key] = match.group(1).strip() if match else ""

    # 拆分姓名
    full_name = data.get("Student Name", "")
    if full_name:
        parts = full_name.rsplit(" ", 1)
        first_name, last_name = parts if len(parts) == 2 else (full_name, "")
    else:
        first_name, last_name = "", ""

    # 合并地址
    address_parts = [data.get("Address", ""), data.get("City", ""), 
                     data.get("State", ""), data.get("Postal Code", "")]
    full_address = ", ".join([p for p in address_parts if p.strip()])

    return {
        "First Name": first_name,
        "Last Name": last_name,
        "Full Address": full_address,
        "Date of Birth": data.get("Date of Birth", ""),
        "SSN": data.get("SSN", ""),
        "Source File": os.path.basename(pdf_path)
    }


def batch_extract():
    pdf_folder = "pdfs"
    output_excel = "output.xlsx"

    # 1. 检查文件夹
    if not os.path.exists(pdf_folder):
        print(f"❌ 未找到 '{pdf_folder}' 文件夹，请创建并放入PDF文件。")
        input("按 Enter 键退出...")  # 暂停，防止窗口关闭
        return

    pdf_files = glob(os.path.join(pdf_folder, "*.pdf"))
    if not pdf_files:
        print(f"❌ 在 '{pdf_folder}' 中没有找到任何PDF文件。")
        input("按 Enter 键退出...")
        return

    print(f"🔍 发现 {len(pdf_files)} 个PDF文件，开始提取...")
    all_rows = []
    for pdf_file in pdf_files:
        print(f"  处理: {os.path.basename(pdf_file)}")
        row = extract_info_from_pdf(pdf_file)
        if row:
            all_rows.append(row)

    if not all_rows:
        print("⚠️ 没有成功提取到任何数据，请检查PDF格式。")
        input("按 Enter 键退出...")
        return

    # 2. 使用 openpyxl 直接写入 Excel（不需要 pandas）
    wb = Workbook()
    ws = wb.active
    ws.title = "Extracted Data"
    
    headers = ["First Name", "Last Name", "Full Address", "Date of Birth", "SSN", "Source File"]
    ws.append(headers)
    
    for row_data in all_rows:
        ws.append([row_data[h] for h in headers])
    
    wb.save(output_excel)
    print(f"✅ 提取完成！共 {len(all_rows)} 条记录，已保存至: {output_excel}")
    input("按 Enter 键退出...")  # 处理完后暂停，让你看到完成提示


if __name__ == "__main__":
    batch_extract()