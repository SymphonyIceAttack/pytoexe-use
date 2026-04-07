import re
import tkinter as tk
from tkinter import scrolledtext, messagebox

class TextCorrector:
    """文本标点符号与空格修正核心逻辑"""
    
    # 成对标点符号映射（左符号 -> 右符号）
    PAIRS = {
        '(': ')', '[': ']', '{': '}', '（': '）', '【': '】', '《': '》',
        '“': '”', '‘': '’', '<': '>', '「': '」', '『': '』'
    }
    
    # 需要合并重复的标点符号集合（排除特殊处理的句点）
    REPEAT_PUNCTUATIONS = set('，。！？；：、＂＇＂＇.,!?;:;')
    
    @staticmethod
    def fix_extra_spaces(text: str) -> str:
        """修正多余空格：
        1. 将连续多个空格替换为单个空格
        2. 去除每行行尾的空格
        3. 保留行首缩进（不删除行首空格）
        4. 保留换行符结构
        """
        lines = text.splitlines()
        fixed_lines = []
        for line in lines:
            # 去除行尾空格
            line = line.rstrip(' ')
            # 将行内连续空格替换为单个空格（保留制表符\t不变）
            line = re.sub(r' {2,}', ' ', line)
            fixed_lines.append(line)
        # 整体去除首尾空白行（可选，避免输出开头/结尾多余空行）
        result = '\n'.join(fixed_lines)
        result = result.strip('\n')
        return result

    @staticmethod
    def fix_repeated_punctuation(text: str) -> str:
        """修正重复标点符号（如 ,, -> ,   ！！ -> ！）
        特殊处理英文句点 '.' : 连续2个句点 -> 1个句点；连续3个及以上 -> 保留3个作为省略号
        注意：中文省略号（……）由两个三点组成，此处不做转换，保持原样
        """
        if not text:
            return text
        
        result = []
        i = 0
        n = len(text)
        
        while i < n:
            ch = text[i]
            # 检查是否为需要处理的标点符号
            if ch in TextCorrector.REPEAT_PUNCTUATIONS:
                j = i + 1
                # 统计连续相同标点的数量
                while j < n and text[j] == ch:
                    j += 1
                count = j - i
                
                # 特殊处理英文句点 '.'
                if ch == '.':
                    if count == 2:
                        # 两个句点 -> 一个句点
                        result.append('.')
                    elif count >= 3:
                        # 三个及以上句点 -> 保留三个句点作为省略号
                        result.append('...')
                    else:
                        result.append('.')
                else:
                    # 其他标点：多个重复只保留一个
                    result.append(ch)
                i = j
            else:
                result.append(ch)
                i += 1
        return ''.join(result)

    @staticmethod
    def fix_unmatched_pairs(text: str) -> str:
        """修正成对标点符号的前后不对称问题：
        1. 删除多余的右符号（没有匹配的左符号）
        2. 在末尾补充缺失的右符号（左符号未闭合）
        注意：仅处理 PAIRS 中定义的成对符号，支持嵌套
        """
        stack = []  # 存储左符号及其位置索引
        to_remove = set()  # 记录需要删除的右符号索引
        
        # 第一遍扫描：标记多余右符号，并记录未匹配的左符号
        for idx, ch in enumerate(text):
            if ch in TextCorrector.PAIRS:  # 左符号
                stack.append((ch, idx))
            elif ch in TextCorrector.PAIRS.values():  # 右符号
                if stack:
                    left_ch, _ = stack[-1]
                    # 检查是否匹配
                    if TextCorrector.PAIRS[left_ch] == ch:
                        stack.pop()  # 匹配成功，弹出左符号
                    else:
                        # 不匹配：当前右符号视为多余
                        to_remove.add(idx)
                else:
                    # 栈空，没有左符号可匹配，多余右符号
                    to_remove.add(idx)
        
        # 构建新字符串：删除多余右符号
        filtered_chars = [ch for idx, ch in enumerate(text) if idx not in to_remove]
        filtered_text = ''.join(filtered_chars)
        
        # 重新扫描剩余文本，找出未匹配的左符号（此时文本已删除多余右符号）
        remaining_left = []
        for ch in filtered_text:
            if ch in TextCorrector.PAIRS:
                remaining_left.append(ch)
            elif ch in TextCorrector.PAIRS.values():
                if remaining_left and TextCorrector.PAIRS[remaining_left[-1]] == ch:
                    remaining_left.pop()
                # 注意：经过第一轮删除，理论上不会再出现不匹配的右符号，但防御处理：忽略
        
        # 为所有未匹配的左符号补全对应的右符号
        suffix = ''.join(TextCorrector.PAIRS[ch] for ch in reversed(remaining_left))
        return filtered_text + suffix

    @staticmethod
    def full_correction(text: str) -> str:
        """执行完整修正流程：多余空格 -> 重复标点 -> 成对符号不对称"""
        if not text:
            return ""
        step1 = TextCorrector.fix_extra_spaces(text)
        step2 = TextCorrector.fix_repeated_punctuation(step1)
        step3 = TextCorrector.fix_unmatched_pairs(step2)
        return step3


class CorrectionApp:
    """图形界面应用程序"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("文本标点修正工具 v1.0")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # 设置样式
        self.root.option_add('*Font', ('微软雅黑', 10))
        
        # 创建主框架
        main_frame = tk.Frame(root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 输入区域
        input_label = tk.Label(main_frame, text="输入文本（可直接粘贴）:", anchor='w')
        input_label.pack(fill=tk.X, pady=(0, 5))
        
        self.input_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=12, 
                                                    font=('Consolas', 10), relief=tk.SUNKEN, borderwidth=1)
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 按钮区域
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.correct_btn = tk.Button(btn_frame, text="🔧 开始修正", command=self.correct_text, 
                                     bg='#4CAF50', fg='white', padx=10, pady=5, font=('微软雅黑', 10, 'bold'))
        self.correct_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = tk.Button(btn_frame, text="🗑️ 清空全部", command=self.clear_all, 
                                   bg='#f44336', fg='white', padx=10, pady=5)
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.copy_btn = tk.Button(btn_frame, text="📋 复制结果", command=self.copy_output, 
                                  bg='#2196F3', fg='white', padx=10, pady=5)
        self.copy_btn.pack(side=tk.LEFT)
        
        # 示例按钮
        self.example_btn = tk.Button(btn_frame, text="📝 加载示例", command=self.load_example, 
                                     padx=10, pady=5)
        self.example_btn.pack(side=tk.RIGHT)
        
        # 输出区域
        output_label = tk.Label(main_frame, text="修正结果:", anchor='w')
        output_label.pack(fill=tk.X, pady=(10, 5))
        
        self.output_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=12, 
                                                     font=('Consolas', 10), relief=tk.SUNKEN, borderwidth=1)
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor='w')
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 绑定快捷键
        self.root.bind('<Control-v>', lambda e: self.paste_shortcut())
        self.root.bind('<Control-V>', lambda e: self.paste_shortcut())
        
    def paste_shortcut(self):
        """粘贴快捷键支持"""
        try:
            text = self.root.clipboard_get()
            self.input_text.insert(tk.INSERT, text)
            self.status_var.set("已粘贴文本")
        except:
            pass
    
    def correct_text(self):
        """执行修正并显示结果"""
        raw_text = self.input_text.get("1.0", tk.END).rstrip("\n")
        if not raw_text.strip():
            messagebox.showinfo("提示", "请输入或粘贴需要修正的文本")
            return
        
        try:
            self.status_var.set("正在修正中...")
            self.root.update()
            
            corrected = TextCorrector.full_correction(raw_text)
            
            # 清空输出框并显示结果
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", corrected)
            self.status_var.set(f"修正完成。原始长度: {len(raw_text)} 字符 → 修正后: {len(corrected)} 字符")
        except Exception as e:
            messagebox.showerror("错误", f"修正过程中发生异常:\n{str(e)}")
            self.status_var.set("修正失败")
    
    def clear_all(self):
        """清空输入和输出区域"""
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.status_var.set("已清空所有内容")
    
    def copy_output(self):
        """复制输出内容到剪贴板"""
        output = self.output_text.get("1.0", tk.END).rstrip("\n")
        if output:
            self.root.clipboard_clear()
            self.root.clipboard_append(output)
            self.status_var.set("结果已复制到剪贴板")
        else:
            messagebox.showinfo("提示", "输出区域为空，请先执行修正")
    
    def load_example(self):
        """加载示例文本，展示各种错误类型"""
        example = """您好，，世界！这是一个测试文本。。。  看看效果如何。
例如：括号不对称（左边缺少右括号
还有【书名号没闭合
多余的空格：这里    有    很多空格。
重复标点：真的吗？？？太好啦！！！  
不匹配的右括号）这里多了一个右括号
英文省略号：这是...正确的三个点，但四个句点....应该变成三个点。
引号示例：“左引号未闭合
混合情况：你好【世界】）不匹配的括号
行尾空格测试：   这一行前面有空格但保留   行尾空格去掉    """
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", example)
        self.status_var.set("已加载示例文本，点击「开始修正」查看效果")


def main():
    root = tk.Tk()
    app = CorrectionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()