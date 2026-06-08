import os
import fitz
import tkinter
from tkinter import filedialog

# 固定截取坐标
rect = fitz.Rect(530, 60, 680, 115)

def main():
    # 隐藏tkinter主窗口
    root = tkinter.Tk()
    root.withdraw()

    print("===== PDF数字区域截图工具 =====")
    print("请选择需要处理PDF的文件夹\n")

    # 弹出文件夹选择框
    target_dir = filedialog.askdirectory(title="选择PDF所在文件夹")
    if not target_dir:
        print("未选择文件夹，程序退出")
        input("\n按回车键关闭窗口...")
        return

    # 创建截图保存目录
    save_folder = os.path.join(target_dir, "数字截图")
    os.makedirs(save_folder, exist_ok=True)

    pdf_count = 0
    for filename in os.listdir(target_dir):
        if filename.lower().endswith(".pdf"):
            pdf_count += 1
            pdf_path = os.path.join(target_dir, filename)
            try:
                doc = fitz.open(pdf_path)
                page = doc[0]
                mat = fitz.Matrix(3, 3)
                pix = page.get_pixmap(matrix=mat, clip=rect)
                img_name = os.path.splitext(filename)[0] + ".png"
                img_path = os.path.join(save_folder, img_name)
                pix.save(img_path)
                doc.close()
                print(f"✅ 完成：{filename}")
            except Exception as e:
                print(f"❌ 失败：{filename} -> {str(e)}")

    if pdf_count == 0:
        print("\n所选文件夹内没有找到PDF文件！")
    else:
        print(f"\n🎉 处理完毕！共处理 {pdf_count} 个PDF")
        print(f"截图已保存至：{save_folder}")

    input("\n按回车键关闭窗口...")

if __name__ == "__main__":
    main()
