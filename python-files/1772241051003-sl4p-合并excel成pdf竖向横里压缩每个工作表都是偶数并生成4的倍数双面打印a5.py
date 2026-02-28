import os
import sys
import comtypes.client
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from PyPDF2 import PdfReader, PdfWriter

# 定义A4尺寸（单位：点，1点=1/72英寸，A4=595x842点）
A4_WIDTH = 595
A4_HEIGHT = 842

def excel_sheet_to_pdf(excel_file_path, temp_dir):
    """将Excel每个工作表转为独立PDF，保存到临时目录"""
    if not os.path.exists(excel_file_path):
        print(f"错误：文件 '{excel_file_path}' 不存在")
        return None
    
    file_ext = os.path.splitext(excel_file_path)[1].lower()
    if file_ext not in ['.xls', '.xlsx']:
        print(f"错误：文件 '{excel_file_path}' 不是有效的Excel文件")
        return None
    
    # 创建临时目录
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        excel = comtypes.client.CreateObject('Excel.Application')
        excel.Visible = False
        excel.DisplayAlerts = False
        
        workbook = excel.Workbooks.Open(excel_file_path)
        cm_to_points = 72 / 2.54
        margin_1cm = 1 * cm_to_points
        
        sheet_pdf_paths = []
        # 遍历每个工作表并转换为PDF
        for idx, sheet in enumerate(workbook.Sheets):
            sheet_name = sheet.Name
            sheet_pdf = os.path.join(temp_dir, f"sheet_{idx}_{sheet_name}.pdf")
            
            page_setup = sheet.PageSetup
            page_setup.PaperSize = 9  # A4
            page_setup.Orientation = 1  # 纵向
            # 1厘米页边距
            page_setup.LeftMargin = margin_1cm
            page_setup.RightMargin = margin_1cm
            page_setup.TopMargin = margin_1cm
            page_setup.BottomMargin = margin_1cm
            page_setup.HeaderMargin = 0
            page_setup.FooterMargin = 0
            # 宽度适配，高度分页
            page_setup.FitToPagesWide = 1
            page_setup.FitToPagesTall = 1000
            page_setup.Zoom = False
            
            sheet.ExportAsFixedFormat(0, sheet_pdf)
            sheet_pdf_paths.append(sheet_pdf)
            print(f"✅ 工作表 '{sheet_name}' 已转为PDF: {sheet_pdf}")
        
        workbook.Close(SaveChanges=False)
        excel.Quit()
        return sheet_pdf_paths
    
    except Exception as e:
        print(f"❌ Excel转PDF错误: {str(e)}")
        try:
            if 'workbook' in locals():
                workbook.Close(SaveChanges=False)
            if 'excel' in locals():
                excel.Quit()
        except:
            pass
        return None

def add_blank_page_if_odd(pdf_path):
    """如果PDF页数为奇数，在末尾添加空白页"""
    reader = PdfReader(pdf_path)
    page_count = len(reader.pages)
    
    # 偶数页直接返回原文件
    if page_count % 2 == 0:
        return pdf_path
    
    # 奇数页添加空白页
    writer = PdfWriter()
    # 复制原有页面
    for page in reader.pages:
        writer.add_page(page)
    
    # 创建A4空白页
    writer.add_blank_page(width=A4_WIDTH, height=A4_HEIGHT)
    # 保存补空白页后的PDF
    new_pdf_path = os.path.splitext(pdf_path)[0] + "_even.pdf"
    with open(new_pdf_path, "wb") as f:
        writer.write(f)
    
    print(f"⚠️ PDF '{pdf_path}' 页数为{page_count}(奇数)，已补空白页: {new_pdf_path}")
    return new_pdf_path

def merge_pdfs(pdf_paths, output_path):
    """合并多个PDF文件"""
    writer = PdfWriter()
    for pdf_path in pdf_paths:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            writer.add_page(page)
    
    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"📄 第一个PDF（合并+各工作表偶数页）已生成: {output_path}")
    return output_path

def add_blank_to_4x(page_list):
    """补空白页至总页数为4的倍数，返回补全后的页面列表"""
    total_pages = len(page_list)
    remainder = total_pages % 4
    blank_needed = 0 if remainder == 0 else (4 - remainder)
    
    # 补充空白页（用None占位，后续填充）
    full_pages = list(page_list)
    full_pages.extend([None] * blank_needed)
    print(f"📝 合并后总页数：{total_pages}，需补空白页至4的倍数：{blank_needed}页，补全后总页数：{len(full_pages)}")
    return full_pages

def rearrange_by_4x_rule(full_pages, output_path):
    """按4的倍数规则重排页面：1,n+1,2,n+2,...,n,2n（n=总页数/2）"""
    total_full = len(full_pages)
    n = total_full // 2  # 前半段/后半段页数
    
    # 生成重排顺序
    rearranged_order = []
    for i in range(n):
        rearranged_order.append(i)          # 前半段第i+1页
        rearranged_order.append(n + i)      # 后半段第i+1页
    
    # 生成重排后的PDF
    writer = PdfWriter()
    for idx in rearranged_order:
        if full_pages[idx] is None:
            # 填充空白页
            writer.add_blank_page(width=A4_WIDTH, height=A4_HEIGHT)
        else:
            # 填充原始页面
            writer.add_page(full_pages[idx])
    
    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"📄 第二个PDF（4的倍数重排）已生成: {output_path}")
    return output_path

def clean_temp_files(temp_dir):
    """清理临时文件"""
    if not os.path.exists(temp_dir):
        return
    for file in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, file)
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"⚠️ 清理临时文件失败 {file_path}: {e}")
    try:
        os.rmdir(temp_dir)
        print("🗑️ 临时文件已清理")
    except:
        pass

def main():
    # 隐藏Tkinter窗口，选择Excel文件（全程仅这一步手动操作）
    root = Tk()
    root.withdraw()
    print("📂 请选择要处理的Excel文件（全程仅需选这一次）...")
    excel_file = askopenfilename(
        title="选择Excel文件",
        filetypes=[("Excel文件", "*.xls;*.xlsx"), ("所有文件", "*.*")]
    )
    
    if not excel_file:
        print("❌ 未选择文件，程序退出")
        sys.exit()
    
    # 定义路径
    excel_name = os.path.splitext(os.path.basename(excel_file))[0]
    output_dir = os.path.dirname(excel_file)
    temp_dir = os.path.join(output_dir, f"{excel_name}_temp")
    merged_pdf = os.path.join(output_dir, f"{excel_name}_merged_even.pdf")  # 第一个PDF
    rearranged_pdf = os.path.join(output_dir, f"{excel_name}_rearranged_4x.pdf")  # 第二个PDF

    try:
        # 步骤1：Excel工作表转独立PDF
        sheet_pdfs = excel_sheet_to_pdf(excel_file, temp_dir)
        if not sheet_pdfs:
            raise Exception("工作表转换失败")
        
        # 步骤2：确保每个工作表PDF页数为偶数
        even_sheet_pdfs = []
        for pdf in sheet_pdfs:
            even_pdf = add_blank_page_if_odd(pdf)
            even_sheet_pdfs.append(even_pdf)
        
        # 步骤3：合并为第一个PDF（各工作表偶数页+合并）
        merge_pdfs(even_sheet_pdfs, merged_pdf)
        
        # 步骤4：读取合并后的PDF页面，准备重排
        merged_reader = PdfReader(merged_pdf)
        merged_pages = merged_reader.pages
        
        # 步骤5：补空白页至4的倍数
        full_pages = add_blank_to_4x(merged_pages)
        
        # 步骤6：按4的倍数规则重排，生成第二个PDF
        rearrange_by_4x_rule(full_pages, rearranged_pdf)
        
        # 步骤7：清理临时文件
        clean_temp_files(temp_dir)
        
        print("\n🎉 所有操作完成！")
        print(f"👉 第一个PDF（合并+各工作表偶数页）：{merged_pdf}")
        print(f"👉 第二个PDF（4的倍数重排）：{rearranged_pdf}")
    
    except Exception as e:
        print(f"\n❌ 程序执行失败：{str(e)}")
        clean_temp_files(temp_dir)
        sys.exit(1)

if __name__ == "__main__":
    # 检查依赖
    try:
        from PyPDF2 import PdfReader, PdfWriter
        import comtypes.client
    except ImportError as e:
        print(f"❌ 缺少依赖库，请先执行：")
        print(f"pip install PyPDF2 comtypes")
        sys.exit(1)
    
    main()
