import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import win32com.client as win32
from win32com.client import constants as wdConst

class DocFormatter:
    def __init__(self, file_path, output_dir, config):
        self.file_path = file_path
        self.output_dir = output_dir
        self.config = config   # 字典：包含所有排版参数
        self.word = None
        self.doc = None

    def process(self):
        try:
            self.word = win32.gencache.EnsureDispatch('Word.Application')
            self.word.Visible = False
            self.doc = self.word.Documents.Open(self.file_path)

            self.setup_page()
            self.apply_styles()
            self.handle_images()
            self.handle_tables()
            self.insert_header_footer()
            self.create_toc()
            self.save_and_close()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            if self.doc:
                self.doc.Close(SaveChanges=False)
            if self.word:
                self.word.Quit()

    def setup_page(self):
        page = self.doc.PageSetup
        page.TopMargin = self.word.CentimetersToPoints(2.54)
        page.BottomMargin = self.word.CentimetersToPoints(2.54)
        page.LeftMargin = self.word.CentimetersToPoints(3.17)
        page.RightMargin = self.word.CentimetersToPoints(3.17)
        page.PaperSize = wdConst.wdPaperA4

    def apply_styles(self):
        # 修改内置样式
        style_normal = self.doc.Styles('Normal')
        font = style_normal.Font
        font.Name = self.config.get('body_font', '宋体')
        font.Size = self.config.get('body_size', 12)
        style_normal.ParagraphFormat.LineSpacingRule = wdConst.wdLineSpace1pt5

        style_h1 = self.doc.Styles('标题 1')
        style_h1.Font.Name = self.config.get('h1_font', '黑体')
        style_h1.Font.Size = self.config.get('h1_size', 18)
        style_h1.Font.Bold = True
        style_h1.ParagraphFormat.Alignment = wdConst.wdAlignParagraphCenter

        # 标题2、3以此类推...

        # 全选后套用正文样式
        self.word.Selection.WholeStory()
        self.word.Selection.Style = style_normal

        # 如果需要识别“第一条”等为标题，可增加简单遍历段落逻辑
        # （略）

    def handle_images(self):
        # 遍历所有InlineShape
        for shape in self.doc.InlineShapes:
            if shape.Type == wdConst.wdInlineShapePicture:
                shape.LockAspectRatio = True
                if shape.Width > self.word.CentimetersToPoints(15):
                    shape.Width = self.word.CentimetersToPoints(15)
                shape.ConvertToShape()  # 转为Shape以设置居中
                shape.WrapFormat.Type = wdConst.wdWrapSquare
                shape.Left = wdConst.wdShapeCenter

    def handle_tables(self):
        for table in self.doc.Tables:
            table.AutoFitBehavior(wdConst.wdAutoFitWindow)
            table.Range.ParagraphFormat.Alignment = wdConst.wdAlignParagraphCenter
            table.Rows.Alignment = wdConst.wdAlignRowCenter
            # 表头加粗
            table.Rows(1).Range.Font.Bold = True
            table.Rows(1).HeadingFormat = True  # 跨页重复

    def insert_header_footer(self):
        # 页眉
        section = self.doc.Sections(1)
        header = section.Headers(wdConst.wdHeaderFooterPrimary)
        header.Range.Text = self.config.get('header_text', 'XX公司 · 内部资料')
        header.Range.ParagraphFormat.Alignment = wdConst.wdAlignParagraphRight

        # 页脚
        footer = section.Footers(wdConst.wdHeaderFooterPrimary)
        footer.Range.Text = "第 "
        footer.Range.Fields.Add(footer.Range, wdConst.wdFieldPage)
        footer.Range.InsertAfter(" 页 共 ")
        footer.Range.Fields.Add(footer.Range, wdConst.wdFieldNumPages)
        footer.Range.InsertAfter(" 页")
        footer.Range.ParagraphFormat.Alignment = wdConst.wdAlignParagraphCenter

    def create_toc(self):
        # 在文档开头插入分节符和目录
        # 简化处理：先将光标移至最前，插入目录
        self.word.Selection.HomeKey(Unit=wdConst.wdStory)
        self.word.Selection.InsertBreak(Type=wdConst.wdSectionBreakNextPage)
        self.word.Selection.HomeKey(Unit=wdConst.wdStory)
        self.word.Selection.TypeText("目录\n")
        self.word.Selection.Style = self.doc.Styles('标题 1')
        self.word.Selection.InsertBreak(Type=wdConst.wdLineBreak)

        # 插入目录域
        toc_range = self.word.Selection.Range
        toc = self.doc.TablesOfContents.Add(Range=toc_range,
                                            RightAlignPageNumbers=True,
                                            UseHeadingStyles=True,
                                            UpperHeadingLevel=1,
                                            LowerHeadingLevel=3,
                                            IncludePageNumbers=True)
        # 更新目录
        toc.Update()

    def save_and_close(self):
        base_name = os.path.splitext(os.path.basename(self.file_path))[0]
        new_name = f"{base_name}_formatted.docx"
        save_path = os.path.join(self.output_dir, new_name)
        self.doc.SaveAs(save_path)
        self.doc.Close()

# ---------- GUI 部分（简化）----------
class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Word 自动排版工具")
        self.geometry("600x450")
        self.files = []
        self.output_dir = ""

        # 文件选择按钮、参数区域、进度条等（省略）
        ttk.Button(self, text="添加文件", command=self.select_files).pack()
        ttk.Button(self, text="开始排版", command=self.start_formatting).pack()
        self.progress = ttk.Progressbar(self, length=300, mode='determinate')
        self.progress.pack()

    def select_files(self):
        self.files = filedialog.askopenfilenames(filetypes=[("Word文档", "*.docx")])
        # 显示已选文件数量

    def start_formatting(self):
        if not self.files:
            messagebox.showwarning("提示", "请先选择文件")
            return
        threading.Thread(target=self.run_batch, daemon=True).start()

    def run_batch(self):
        total = len(self.files)
        self.progress['maximum'] = total
        for i, file in enumerate(self.files):
            formatter = DocFormatter(file, self.output_dir or os.path.dirname(file), self.get_config())
            success, err = formatter.process()
            self.after(0, self.progress.step, 1)
            if not success:
                print(f"处理失败: {file} -> {err}")
        self.after(0, messagebox.showinfo, "完成", "批量排版结束")

# 启动
if __name__ == "__main__":
    app = Application()
    app.mainloop()