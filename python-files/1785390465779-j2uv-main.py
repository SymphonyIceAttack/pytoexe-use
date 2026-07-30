# -*- coding: utf-8 -*-
"""
大小写转换工具
- 输入: 任意大小写混合的英文
- 输出: 全部大写 / 全部小写
- 按钮: 转大写 / 转小写 / 复制输出
仅依赖 Python 标准库 (tkinter)
"""

import tkinter as tk
from tkinter import ttk, messagebox


class CaseConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("大小写转换工具")
        self.root.geometry("640x520")
        self.root.minsize(480, 400)

        self._build_ui()

    def _build_ui(self):
        # --- 输入区 ---
        in_frame = ttk.LabelFrame(self.root, text="  输入 (英文, 任意大小写)  ", padding=8)
        in_frame.pack(fill="both", expand=True, padx=10, pady=(10, 4))

        self.input_text = tk.Text(
            in_frame, height=7, font=("Consolas", 11), wrap="word", undo=True
        )
        in_scroll = ttk.Scrollbar(in_frame, orient="vertical", command=self.input_text.yview)
        self.input_text.configure(yscrollcommand=in_scroll.set)
        self.input_text.pack(side="left", fill="both", expand=True)
        in_scroll.pack(side="right", fill="y")

        # --- 转换按钮区 ---
        conv_frame = ttk.Frame(self.root, padding=8)
        conv_frame.pack(fill="x", padx=10, pady=4)

        ttk.Button(conv_frame, text="转大写  (UPPERCASE)",
                   command=self.to_upper).pack(side="left", padx=4, expand=True, fill="x")
        ttk.Button(conv_frame, text="转小写  (lowercase)",
                   command=self.to_lower).pack(side="left", padx=4, expand=True, fill="x")
        ttk.Button(conv_frame, text="清空输入",
                   command=self.clear_input).pack(side="left", padx=4)

        # --- 输出区 ---
        out_frame = ttk.LabelFrame(self.root, text="  输出  ", padding=8)
        out_frame.pack(fill="both", expand=True, padx=10, pady=4)

        self.output_text = tk.Text(
            out_frame, height=7, font=("Consolas", 11), wrap="word",
            state="disabled", bg="#f5f5f5"
        )
        out_scroll = ttk.Scrollbar(out_frame, orient="vertical", command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=out_scroll.set)
        self.output_text.pack(side="left", fill="both", expand=True)
        out_scroll.pack(side="right", fill="y")

        # --- 复制按钮区 ---
        copy_frame = ttk.Frame(self.root, padding=8)
        copy_frame.pack(fill="x", padx=10, pady=(4, 10))

        ttk.Button(copy_frame, text="清空输出",
                   command=self.clear_output).pack(side="left", padx=4)
        ttk.Button(copy_frame, text="复制输出  (Copy to Clipboard)",
                   command=self.copy_output).pack(side="right", padx=4, expand=True, fill="x")

    def _get_input(self) -> str:
        return self.input_text.get("1.0", "end-1c")

    def _set_output(self, text: str):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)
        self.output_text.config(state="disabled")

    def to_upper(self):
        src = self._get_input()
        if not src.strip():
            messagebox.showwarning("提示", "请先在输入框里输入内容")
            return
        self._set_output(src.upper())

    def to_lower(self):
        src = self._get_input()
        if not src.strip():
            messagebox.showwarning("提示", "请先在输入框里输入内容")
            return
        self._set_output(src.lower())

    def clear_input(self):
        self.input_text.delete("1.0", "end")

    def clear_output(self):
        self._set_output("")

    def copy_output(self):
        text = self.output_text.get("1.0", "end-1c")
        if not text:
            messagebox.showwarning("提示", "输出为空, 无可复制内容")
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            # 关键: update() 后才能在窗口关闭后保留剪贴板内容
            self.root.update()
            messagebox.showinfo("已复制", f"已复制 {len(text)} 个字符到剪贴板\n可直接 Ctrl+V 粘贴")
        except Exception as e:
            messagebox.showerror("复制失败", f"无法写入剪贴板: {e}")


def main():
    root = tk.Tk()
    CaseConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
