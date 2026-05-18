import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import webbrowser
import tempfile
from docx import Document
import diff_match_patch as dmp_module

class DiffTool:
    def __init__(self, root):
        self.root = root
        self.root.title("文件差异标注工具 - 副文本差异高亮")
        self.root.geometry("720x520")
        self.root.resizable(True, True)

        # 文件路径变量
        self.master_path = tk.StringVar()
        self.slave_path = tk.StringVar()

        # 存储提取的文本
        self.master_text = ""
        self.slave_text = ""

        self.create_widgets()

    def create_widgets(self):
        # 主框架
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 主文本区域
        master_frame = tk.LabelFrame(main_frame, text="📄 主文本（不会被标注）", font=("微软雅黑", 10, "bold"), padx=10, pady=10)
        master_frame.pack(fill=tk.X, pady=(0, 12))

        tk.Label(master_frame, text="文件路径：").grid(row=0, column=0, sticky="w")
        tk.Entry(master_frame, textvariable=self.master_path, width=60, state="readonly").grid(row=0, column=1, padx=6)
        tk.Button(master_frame, text="选择主文本文件", command=self.select_master).grid(row=0, column=2)

        self.master_preview = scrolledtext.ScrolledText(master_frame, height=8, wrap=tk.WORD, state="normal")
        self.master_preview.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky="nsew")
        master_frame.grid_columnconfigure(1, weight=1)

        # 副文本区域
        slave_frame = tk.LabelFrame(main_frame, text="✏️ 副文本（将高亮与主文本的差异）", font=("微软雅黑", 10, "bold"), padx=10, pady=10)
        slave_frame.pack(fill=tk.X, pady=(0, 12))

        tk.Label(slave_frame, text="文件路径：").grid(row=0, column=0, sticky="w")
        tk.Entry(slave_frame, textvariable=self.slave_path, width=60, state="readonly").grid(row=0, column=1, padx=6)
        tk.Button(slave_frame, text="选择副文本文件", command=self.select_slave).grid(row=0, column=2)

        self.slave_preview = scrolledtext.ScrolledText(slave_frame, height=8, wrap=tk.WORD, state="normal")
        self.slave_preview.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky="nsew")
        slave_frame.grid_columnconfigure(1, weight=1)

        # 按钮区域
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        tk.Button(btn_frame, text="🔍 对比并标注差异", command=self.compare_and_show, bg="#4caf50", fg="white", font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ 清空所有", command=self.clear_all, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ 退出", command=self.root.quit, bg="#9e9e9e", fg="white").pack(side=tk.RIGHT, padx=5)

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪 | 请选择主文本和副文本文件")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def select_master(self):
        path = filedialog.askopenfilename(
            title="选择主文本文件",
            filetypes=[("Word 文档", "*.docx"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if path:
            self.master_path.set(path)
            self.load_and_preview(path, self.master_preview, is_master=True)

    def select_slave(self):
        path = filedialog.askopenfilename(
            title="选择副文本文件",
            filetypes=[("Word 文档", "*.docx"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if path:
            self.slave_path.set(path)
            self.load_and_preview(path, self.slave_preview, is_master=False)

    def load_and_preview(self, path, preview_widget, is_master):
        """加载文件内容并在预览区显示，同时存储文本到对应变量"""
        try:
            text = self.extract_text_from_file(path)
            if is_master:
                self.master_text = text
            else:
                self.slave_text = text

            # 更新预览区
            preview_widget.config(state="normal")
            preview_widget.delete(1.0, tk.END)
            preview_widget.insert(tk.END, text)
            preview_widget.config(state="disabled")
            self.status_var.set(f"已加载: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("错误", f"读取文件失败: {str(e)}")
            self.status_var.set("加载失败")

    def extract_text_from_file(self, filepath):
        """根据扩展名提取文本内容，支持 .docx 和 .txt"""
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".docx":
            doc = Document(filepath)
            paragraphs = [para.text for para in doc.paragraphs]
            return "\n".join(paragraphs)
        elif ext == ".txt":
            # 尝试常见编码
            encodings = ["utf-8", "gbk", "gb2312", "latin-1"]
            for enc in encodings:
                try:
                    with open(filepath, "r", encoding=enc) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise ValueError("无法识别文本编码，请将文件另存为 UTF-8 编码")
        else:
            raise ValueError(f"不支持的文件格式: {ext}，请使用 .docx 或 .txt 文件")

    def compare_and_show(self):
        """执行差异对比，生成 HTML 报告并打开浏览器"""
        if not self.master_text.strip() and not self.slave_text.strip():
            messagebox.showwarning("提示", "请先加载主文本和副文本文件")
            return
        if not self.master_text.strip():
            messagebox.showwarning("提示", "主文本内容为空，无法对比")
            return

        # 使用 diff-match-patch 进行字符级差异
        dmp = dmp_module.diff_match_patch()
        diffs = dmp.diff_main(self.master_text, self.slave_text)
        dmp.diff_cleanupSemantic(diffs)

        # 生成 HTML 报告
        html_content = self.generate_html_report(diffs, self.master_text, self.slave_text)

        # 保存临时文件并打开浏览器
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            temp_path = f.name
        webbrowser.open(f"file://{temp_path}")
        self.status_var.set("已生成差异报告，浏览器已打开")

    def generate_html_report(self, diffs, master_text, slave_text):
        """
        生成完整的 HTML 报告：
        - 副文本差异标注（绿色高亮显示新增/修改）
        - 列出主文本中有但副文本缺失的内容（删除片段）
        """
        # 构建副文本高亮（仅展示 op == 1 的插入部分，op == 0 正常，op == -1 忽略）
        slave_html_parts = []
        # 同时收集删除片段（主文本独有）用于摘要
        delete_snippets = []

        for op, data in diffs:
            if op == 0:  # 相同
                slave_html_parts.append(self.escape_html(data))
            elif op == 1:  # 副文本新增（相对于主文本）
                slave_html_parts.append(f'<span class="diff-ins">{self.escape_html(data)}</span>')
            elif op == -1:  # 主文本独有（副文本缺失）
                delete_snippets.append(data)

        slave_diff_html = "".join(slave_html_parts)

        # 生成缺失内容摘要（去重且限制过长）
        unique_deletes = []
        seen = set()
        for snip in delete_snippets:
            if snip not in seen and snip.strip():
                seen.add(snip)
                # 截取过长片段
                display = snip if len(snip) <= 200 else snip[:200] + "……"
                unique_deletes.append(display)

        delete_summary_html = ""
        if unique_deletes:
            items = "\n".join([f"<li>{self.escape_html(item)}</li>" for item in unique_deletes])
            delete_summary_html = f"""
            <div class="summary-card">
                <h3>📌 主文本独有内容（副文本缺失）</h3>
                <p>以下内容存在于主文本中，但在副文本中没有找到。这些差异不会标注在副文本正文中，特此列出供参考：</p>
                <ul>{items}</ul>
            </div>
            """
        else:
            delete_summary_html = '<div class="summary-card"><h3>✅ 主文本与副文本完全一致</h3><p>主文本中所有内容均在副文本中找到匹配，没有缺失内容。</p></div>'

        # 主文本纯预览（不标注）
        master_plain_html = f'<pre class="plain-text">{self.escape_html(master_text)}</pre>'

        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>文本差异标注报告 - 副文本差异高亮</title>
    <style>
        body {{
            font-family: 'Segoe UI', 'Roboto', 'Noto Sans', system-ui, sans-serif;
            max-width: 1300px;
            margin: 30px auto;
            padding: 20px;
            background: #f5f7fb;
            color: #1e2a3e;
        }}
        .container {{
            background: white;
            border-radius: 24px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.05);
            overflow: hidden;
        }}
        header {{
            background: linear-gradient(135deg, #1e293b, #0f172a);
            color: white;
            padding: 24px 30px;
        }}
        header h1 {{
            margin: 0 0 6px;
            font-weight: 600;
        }}
        header p {{
            margin: 0;
            opacity: 0.8;
        }}
        .diff-section {{
            padding: 24px 30px;
            border-bottom: 1px solid #e9edf2;
        }}
        .diff-section h2 {{
            font-size: 1.5rem;
            margin-top: 0;
            margin-bottom: 16px;
            color: #0f2b3d;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .diff-highlight-box {{
            background: #fefefe;
            border: 1px solid #e2e8f0;
            border-radius: 20px;
            padding: 20px;
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
            background-color: #fafcff;
        }}
        .diff-ins {{
            background-color: #dcfce7;
            color: #166534;
            border-radius: 6px;
            padding: 0px 2px;
            font-weight: 500;
            box-decoration-break: clone;
            -webkit-box-decoration-break: clone;
            border-bottom: 1px solid #86efac;
        }}
        .summary-card {{
            background: #fef9e3;
            border-left: 6px solid #eab308;
            padding: 16px 24px;
            margin-top: 28px;
            border-radius: 18px;
        }}
        .summary-card h3 {{
            margin-top: 0;
            color: #b45309;
        }}
        .summary-card ul {{
            margin-bottom: 0;
            padding-left: 20px;
        }}
        .summary-card li {{
            margin: 8px 0;
            font-family: monospace;
            background: #fff6e0;
            padding: 4px 8px;
            border-radius: 12px;
            list-style-type: square;
        }}
        .plain-text {{
            background: #f1f5f9;
            padding: 16px;
            border-radius: 16px;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 13px;
            line-height: 1.5;
            margin: 0;
            overflow-x: auto;
        }}
        footer {{
            text-align: center;
            padding: 16px;
            font-size: 0.75rem;
            color: #6c86a3;
            border-top: 1px solid #eef2f8;
        }}
        .badge {{
            background: #eef2ff;
            color: #2563eb;
            border-radius: 40px;
            padding: 4px 12px;
            font-size: 0.7rem;
            font-weight: normal;
        }}
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>📑 文本差异标注报告</h1>
        <p>副文本中以 <span style="background:#dcfce7; padding:0 4px;">绿色高亮</span> 标记相对于主文本的差异（新增或修改）</p>
    </header>

    <div class="diff-section">
        <h2>✏️ 副文本差异标注 <span class="badge">高亮部分 = 与主文本不同之处</span></h2>
        <div class="diff-highlight-box">
            {slave_diff_html if slave_diff_html else '<span style="color:#94a3b8;">[副文本内容为空]</span>'}
        </div>
    </div>

    <div class="diff-section">
        <h2>📄 主文本原文 <span class="badge">未标注（参考原文）</span></h2>
        <div class="diff-highlight-box">
            {master_plain_html}
        </div>
    </div>

    <div class="diff-section">
        {delete_summary_html}
    </div>

    <footer>
        差异算法：diff-match-patch (字符级) | 本报告由文件对比工具自动生成
    </footer>
</div>
</body>
</html>"""
        return html_template

    @staticmethod
    def escape_html(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def clear_all(self):
        self.master_path.set("")
        self.slave_path.set("")
        self.master_text = ""
        self.slave_text = ""
        self.master_preview.config(state="normal")
        self.master_preview.delete(1.0, tk.END)
        self.master_preview.config(state="disabled")
        self.slave_preview.config(state="normal")
        self.slave_preview.delete(1.0, tk.END)
        self.slave_preview.config(state="disabled")
        self.status_var.set("已清空所有内容")

def main():
    root = tk.Tk()
    app = DiffTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()