# -*- coding: utf-8 -*-
"""
SMT零件位置核对工具（最终稳定版）
功能：导入坐标文件 → 生成带勾选框的核对表 → 导出可直接打印的PDF
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import os

# 注册中文字体，解决PDF乱码
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
FONT_CN = 'STSong-Light'

class SMTPositionCheckTool:
    def __init__(self, root):
        self.root = root
        self.root.title("SMT零件位置核对工具 V1.0")
        self.root.geometry("800x550")
        
        self.cad_path = ""
        self.cad_data = None
        
        # 创建界面
        self.create_ui()
    
    def create_ui(self):
        # 文件导入区
        frame_file = ttk.LabelFrame(self.root, text="文件导入")
        frame_file.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(frame_file, text="选择CAD坐标文件", command=self.load_cad).grid(row=0, column=0, padx=5, pady=5)
        self.lbl_cad = ttk.Label(frame_file, text="未选择文件")
        self.lbl_cad.grid(row=0, column=1, padx=5, pady=5)
        
        # 操作按钮区
        frame_btn = ttk.Frame(self.root)
        frame_btn.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(frame_btn, text="预览零件数据", command=self.preview_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_btn, text="导出PDF核对表", command=self.export_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_btn, text="清空数据", command=self.clear_data).pack(side=tk.LEFT, padx=5)
        
        # 日志输出区
        frame_log = ttk.LabelFrame(self.root, text="运行日志")
        frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.text_log = tk.Text(frame_log, height=20)
        self.text_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log("=== SMT零件位置核对工具已启动 ===")
        self.log("支持格式：.csv / .xlsx / .xls 坐标文件")
        self.log("使用步骤：导入坐标文件 → 预览数据 → 导出PDF打印")
    
    def log(self, msg):
        """输出日志信息"""
        self.text_log.insert(tk.END, msg + "\n")
        self.text_log.see(tk.END)
    
    def load_cad(self):
        """加载CAD坐标文件"""
        path = filedialog.askopenfilename(
            title="选择CAD坐标文件",
            filetypes=[("表格文件", "*.csv *.xlsx *.xls"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if not path:
            return
        
        try:
            # 自动识别文件格式
            if path.endswith('.csv') or path.endswith('.txt'):
                self.cad_data = pd.read_csv(path, encoding='gbk')
            else:
                self.cad_data = pd.read_excel(path)
            
            self.cad_path = path
            self.lbl_cad.config(text=os.path.basename(path))
            self.log(f"✅ 坐标文件加载成功：{os.path.basename(path)}")
            self.log(f"📊 共识别到 {len(self.cad_data)} 个零件")
        except Exception as e:
            messagebox.showerror("错误", f"文件加载失败：{str(e)}")
    
    def preview_data(self):
        """预览零件数据"""
        if self.cad_data is None:
            messagebox.showwarning("提示", "请先导入坐标文件！")
            return
        
        self.log("\n=== 零件数据预览 ===")
        # 自动匹配常见列名
        cols = self.cad_data.columns.str.lower()
        try:
            ref_col = [c for c in cols if '位号' in c or 'designator' in c or 'ref' in c or 'refdes' in c][0]
            x_col = [c for c in cols if 'x' in c and 'coord' not in c][0]
            y_col = [c for c in cols if 'y' in c and 'coord' not in c][0]
            part_col = [c for c in cols if '零件' in c or 'part' in c or '料号' in c or 'comment' in c or 'value' in c][0]
        except:
            messagebox.showerror("错误", "坐标文件必须包含：位号、X坐标、Y坐标、零件号/值 列！")
            return
        
        # 输出前20个零件预览（避免刷屏）
        for idx, row in self.cad_data.head(20).iterrows():
            ref = str(row[ref_col])
            x = round(float(row[x_col]), 2)
            y = round(float(row[y_col]), 2)
            part = str(row[part_col])
            self.log(f"【{ref}】 零件：{part} | X：{x} | Y：{y}")
        
        if len(self.cad_data) > 20:
            self.log(f"... 还有 {len(self.cad_data)-20} 个零件未显示")
        self.log("\n✅ 数据预览完成，可导出PDF！")
    
    def export_pdf(self):
        """导出PDF核对表"""
        if self.cad_data is None:
            messagebox.showwarning("提示", "请先导入坐标文件！")
            return
        
        save_path = filedialog.asksaveasfilename(
            title="保存PDF核对表",
            defaultextension=".pdf",
            filetypes=[("PDF文件", "*.pdf")]
        )
        if not save_path:
            return
        
        try:
            c = canvas.Canvas(save_path, pagesize=A4)
            c.setFont(FONT_CN, 12)
            
            # PDF标题
            c.drawString(200, 800, "SMT零件位置核对表")
            c.drawString(50, 780, f"文件名称：{os.path.basename(self.cad_path)}")
            c.drawString(50, 760, "-" * 80)
            
            # 表格表头
            y = 720
            c.drawString(50, y, "位号")
            c.drawString(150, y, "零件型号/料号")
            c.drawString(350, y, "X坐标")
            c.drawString(450, y, "Y坐标")
            c.drawString(550, y, "核对状态")
            y -= 20
            
            # 自动匹配列名
            cols = self.cad_data.columns.str.lower()
            ref_col = [c for c in cols if '位号' in c or 'designator' in c or 'ref' in c or 'refdes' in c][0]
            x_col = [c for c in cols if 'x' in c and 'coord' not in c][0]
            y_col = [c for c in cols if 'y' in c and 'coord' not in c][0]
            part_col = [c for c in cols if '零件' in c or 'part' in c or '料号' in c or 'comment' in c or 'value' in c][0]
            
            # 写入零件数据，自动换页
            for _, row in self.cad_data.iterrows():
                if y < 50:
                    c.showPage()
                    c.setFont(FONT_CN, 12)
                    y = 800
                
                ref = str(row[ref_col])
                part = str(row[part_col])
                x = str(round(float(row[x_col]), 2))
                y_val = str(round(float(row[y_col]), 2))
                
                c.drawString(50, y, ref)
                c.drawString(150, y, part)
                c.drawString(350, y, x)
                c.drawString(450, y, y_val)
                c.drawString(550, y, "□ 已核对")
                y -= 15
            
            c.save()
            self.log(f"\n✅ PDF导出成功：{save_path}")
            messagebox.showinfo("完成", "PDF核对表已生成，可直接打印给员工使用！")
        except Exception as e:
            messagebox.showerror("错误", f"PDF导出失败：{str(e)}")
    
    def clear_data(self):
        """清空所有数据"""
        self.cad_path = ""
        self.cad_data = None
        self.lbl_cad.config(text="未选择文件")
        self.text_log.delete(1.0, tk.END)
        self.log("🧹 数据已清空，可重新导入文件")

if __name__ == "__main__":
    root = tk.Tk()
    app = SMTPositionCheckTool(root)
    root.mainloop()