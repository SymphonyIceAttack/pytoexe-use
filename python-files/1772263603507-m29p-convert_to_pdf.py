# -*- coding: utf-8 -*-
"""
将选定目录下所有 .doc / .docx 转为 PDF，输出到同一目录。
需在已安装 Microsoft Word 的 Windows 或 macOS 上运行。
"""
import os
import sys
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

try:
    from docx2pdf import convert as docx2pdf_convert
except ImportError:
    pass


def get_target_dir():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askdirectory(title="请选择包含 doc/docx 的目录")
    root.destroy()
    return path


def find_doc_files(folder):
    if not folder or not os.path.isdir(folder):
        return []
    exts = (".doc", ".docx")
    found = []
    for name in os.listdir(folder):
        base, ext = os.path.splitext(name)
        if ext.lower() in exts:
            found.append(os.path.join(folder, name))
    return sorted(found)


def run_conversion(folder):
    files = find_doc_files(folder)
    if not files:
        return 0, "该目录下没有找到 .doc 或 .docx 文件。"

    try:
        docx2pdf_convert
    except NameError:
        return 0, "未安装 docx2pdf，请运行: pip install docx2pdf"

    ok = 0
    errors = []
    for path in files:
        out_path = os.path.splitext(path)[0] + ".pdf"
        try:
            docx2pdf_convert(path, out_path)
            ok += 1
        except Exception as e:
            errors.append(f"{os.path.basename(path)}: {e}")

    if errors:
        msg = f"成功: {ok} 个，失败: {len(errors)} 个。\n\n失败文件:\n" + "\n".join(errors[:10])
        if len(errors) > 10:
            msg += f"\n... 等共 {len(errors)} 个"
    else:
        msg = f"全部完成，共转换 {ok} 个文件。\nPDF 已保存到同一目录。"
    return ok, msg


def main():
    folder = get_target_dir()
    if not folder:
        return
    ok, msg = run_conversion(folder)
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    if ok > 0 and "失败" not in msg:
        messagebox.showinfo("转换完成", msg)
    else:
        messagebox.showwarning("转换结果", msg)
    root.destroy()


if __name__ == "__main__":
    main()
    sys.exit(0)
