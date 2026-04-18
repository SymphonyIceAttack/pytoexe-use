# -*- coding: utf-8 -*-
"""
打印机驱动安装工具 v1.0
用于远程协助时快速诊断和获取驱动
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import platform
import json
import pyperclip
import webbrowser
from datetime import datetime

# 品牌关键词匹配
BRAND_KEYWORDS = {
    "HP": ["HP", "Hewlett", "LaserJet", "DeskJet", "OfficeJet", "PageWide", "MFP", "DesignJet"],
    "EPSON": ["EPSON", "Epson", "L series", "WF-", "XP-", "EP-"],
    "Canon": ["Canon", "G-series", "MG-", "TS-", "PIXMA", "imageCLASS", "i-SENSYS"],
    "Brother": ["Brother", "DCP-", "MFC-", "HL-", "ADS-"],
    "Samsung": ["Samsung", "SL-", "Xpress", "ProXpress"],
    "Xerox": ["Xerox", "WorkCentre", "Phaser", "VersaLink", "Altalink"],
    "Lexmark": ["Lexmark", "CS-", "CX-", "MX-", "XC-"],
    "Dell": ["Dell", "C-", "E-", "S-"],
    "Lenovo": ["Lenovo", "LJ-", "M-"],
    "Pantum": ["Pantum", "PANTUM"],
    "Fuji Xerox": ["Fuji Xerox", "FUJI XEROX", "DocuPrint"],
    "KYOCERA": ["KYOCERA", "ECOSYS", "TASKalfa"],
    "Ricoh": ["Ricoh", "SP-", "MP-", "IM-"],
    "Sharp": ["Sharp", "MX-", "AR-"],
    "Toshiba": ["Toshiba", "e-STUDIO", "eSTUDIO"],
    "KONICA MINOLTA": ["KONICA", "MINOLTA", "bizhub", "PagePro"],
    "Huawei": ["Huawei", "HUAWEI", "PixLab"],
    "联想": ["联想", "Lenovo"],
    "小米": ["小米", "MI", "XiaoMi"],
}

# 驱动下载页面
DRIVER_URLS = {
    "HP": "https://support.hp.com.cn Drivers",
    "EPSON": "https://www.epson.cn/support/lianxidianhua",
    "Canon": "https://www.canon.com.cn/supports/",
    "Brother": "https://support.brother.cn/",
    "Samsung": "https://www.samsung.com/cn/support/",
    "Xerox": "https://www.xerox.com/support/",
    "Lexmark": "https://www.lexmark.com/zh/support/",
    "Dell": "https://www.dell.com/support/kbdoc/zh-cn/",
    "Lenovo": "https://support.lenovo.com.cn/",
    "Pantum": "https://www.pantum.com/support",
    "Huawei": "https://consumer.huawei.com/cn/support/",
}

def get_system_info():
    """获取系统信息"""
    return {
        "系统": platform.system() + " " + platform.release(),
        "版本": platform.version(),
        "架构": platform.machine(),
        "主机名": platform.node(),
    }

def detect_printers():
    """检测系统打印机"""
    printers = []
    
    try:
        # Windows: 使用 wmic
        if platform.system() == "Windows":
            result = subprocess.run(
                ["wmic", "printer", "get", "name,portName,status,workOffline"],
                capture_output=True, text=True, encoding='gbk', errors='ignore'
            )
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:
                if line.strip():
                    parts = [p.strip() for p in line.split() if p.strip()]
                    if parts:
                        printers.append({
                            "name": parts[0] if len(parts) > 0 else "未知",
                            "port": parts[1] if len(parts) > 1 else "未知",
                            "status": parts[2] if len(parts) > 2 else "未知",
                            "offline": parts[3] if len(parts) > 3 else "否",
                        })
        else:
            # macOS/Linux: 使用 lpstat
            result = subprocess.run(
                ["lpstat", "-a"],
                capture_output=True, text=True
            )
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    name = line.split()[0]
                    printers.append({
                        "name": name,
                        "port": "网络/本地",
                        "status": "就绪",
                        "offline": "否",
                    })
    except Exception as e:
        printers.append({"name": f"检测失败: {str(e)}", "port": "-", "status": "-", "offline": "-"})
    
    return printers

def detect_printer_brand(printer_name):
    """检测打印机品牌"""
    name_upper = printer_name.upper()
    for brand, keywords in BRAND_KEYWORDS.items():
        for keyword in keywords:
            if keyword.upper() in name_upper:
                return brand
    return "其他"

def get_driver_url(brand):
    """获取驱动下载页面"""
    if brand in DRIVER_URLS:
        return DRIVER_URLS[brand]
    return "请百度搜索: " + brand + " 打印机驱动下载"

def generate_report(printers, system_info):
    """生成诊断报告"""
    report = []
    report.append("=" * 50)
    report.append("打印机诊断报告")
    report.append("=" * 50)
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    report.append("【系统信息】")
    for key, value in system_info.items():
        report.append(f"  {key}: {value}")
    report.append("")
    
    report.append("【检测到的打印机】")
    if printers:
        for i, p in enumerate(printers, 1):
            brand = detect_printer_brand(p["name"])
            report.append(f"  {i}. {p['name']}")
            report.append(f"     品牌: {brand}")
            report.append(f"     端口: {p['port']}")
            report.append(f"     状态: {p['status']}")
            report.append(f"     离线模式: {p['offline']}")
            report.append(f"     驱动下载: {get_driver_url(brand)}")
            report.append("")
    else:
        report.append("  未检测到打印机")
        report.append("")
    
    report.append("=" * 50)
    return "\n".join(report)

def copy_to_clipboard(text):
    """复制到剪贴板"""
    try:
        pyperclip.copy(text)
        return True
    except:
        return False

class PrinterToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("打印机驱动安装工具 v1.0")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.printers = []
        self.system_info = get_system_info()
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        # 标题
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="🖨️ 打印机驱动安装工具",
            font=("微软雅黑", 18, "bold"),
            fg="white",
            bg="#2c3e50"
        )
        title_label.pack(pady=15)
        
        # 主内容区
        main_frame = tk.Frame(self.root, padx=20, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 系统信息
        info_frame = tk.LabelFrame(main_frame, text="系统信息", font=("微软雅黑", 11))
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_text = f"系统: {self.system_info.get('系统', 'N/A')} | 架构: {self.system_info.get('架构', 'N/A')}"
        tk.Label(info_frame, text=info_text, font=("微软雅黑", 9)).pack(anchor=tk.W, padx=10, pady=5)
        
        # 按钮区
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Button(
            btn_frame, text="🔍 检测打印机",
            font=("微软雅黑", 10),
            command=self.detect_printers,
            bg="#3498db", fg="white",
            width=15, height=2
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame, text="📋 生成报告",
            font=("微软雅黑", 10),
            command=self.generate_report,
            bg="#27ae60", fg="white",
            width=15, height=2
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame, text="📋 复制信息",
            font=("微软雅黑", 10),
            command=self.copy_info,
            bg="#9b59b6", fg="white",
            width=15, height=2
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame, text="🔗 打开驱动页面",
            font=("微软雅黑", 10),
            command=self.open_driver_page,
            bg="#e67e22", fg="white",
            width=15, height=2
        ).pack(side=tk.LEFT, padx=5)
        
        # 打印机列表
        list_frame = tk.LabelFrame(main_frame, text="检测到的打印机", font=("微软雅黑", 11))
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 表格
        columns = ("序号", "打印机名称", "品牌", "端口", "状态")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        self.tree.heading("序号", text="序号")
        self.tree.heading("打印机名称", text="打印机名称")
        self.tree.heading("品牌", text="品牌")
        self.tree.heading("端口", text="端口")
        self.tree.heading("状态", text="状态")
        
        self.tree.column("序号", width=50, anchor="center")
        self.tree.column("打印机名称", width=300)
        self.tree.column("品牌", width=100, anchor="center")
        self.tree.column("端口", width=150)
        self.tree.column("状态", width=100, anchor="center")
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        
        # 报告区
        report_frame = tk.LabelFrame(main_frame, text="诊断报告", font=("微软雅黑", 11))
        report_frame.pack(fill=tk.BOTH, expand=True)
        
        self.report_text = scrolledtext.ScrolledText(
            report_frame,
            font=("Consolas", 9),
            wrap=tk.WORD,
            height=10
        )
        self.report_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 状态栏
        self.status_label = tk.Label(
            self.root,
            text="就绪",
            font=("微软雅黑", 9),
            anchor=tk.W,
            bg="#ecf0f1"
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
    def detect_printers(self):
        """检测打印机"""
        self.status_label.config(text="正在检测...")
        self.root.update()
        
        try:
            self.printers = detect_printers()
            
            # 清空表格
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # 填充数据
            for i, p in enumerate(self.printers, 1):
                brand = detect_printer_brand(p["name"])
                self.tree.insert("", tk.END, values=(i, p["name"], brand, p["port"], p["status"]))
            
            if self.printers:
                self.status_label.config(text=f"检测到 {len(self.printers)} 台打印机")
            else:
                self.status_label.config(text="未检测到打印机")
                
        except Exception as e:
            messagebox.showerror("错误", f"检测失败: {str(e)}")
            self.status_label.config(text="检测失败")
    
    def generate_report(self):
        """生成报告"""
        if not self.printers:
            messagebox.showwarning("提示", "请先点击「检测打印机」")
            return
        
        report = generate_report(self.printers, self.system_info)
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(1.0, report)
        self.status_label.config(text="报告已生成")
    
    def copy_info(self):
        """复制信息"""
        if not self.printers:
            messagebox.showwarning("提示", "请先点击「检测打印机」")
            return
        
        report = generate_report(self.printers, self.system_info)
        
        if copy_to_clipboard(report):
            messagebox.showinfo("成功", "已复制到剪贴板，可直接发送给客户")
            self.status_label.config(text="已复制到剪贴板")
        else:
            messagebox.showerror("错误", "复制失败")
    
    def open_driver_page(self):
        """打开驱动下载页面"""
        if not self.printers:
            messagebox.showwarning("提示", "请先点击「检测打印机」")
            return
        
        # 打开第一个打印机的驱动页面
        p = self.printers[0]
        brand = detect_printer_brand(p["name"])
        url = get_driver_url(brand)
        
        # 如果是完整URL，直接打开
        if url.startswith("http"):
            webbrowser.open(url)
        else:
            # 否则搜索
            search_url = f"https://www.baidu.com/s?wd={brand}+打印机驱动下载"
            webbrowser.open(search_url)
        
        self.status_label.config(text=f"已打开 {brand} 驱动下载页面")

def main():
    root = tk.Tk()
    app = PrinterToolApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
