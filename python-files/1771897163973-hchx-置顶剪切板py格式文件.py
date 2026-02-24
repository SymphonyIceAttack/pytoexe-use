import tkinter as tk
from tkinter import messagebox

def get_clipboard_text():
    """获取剪切板内容"""
    try:
        return root.clipboard_get()
    except:
        return ""

def update_text():
    """更新文本框内容"""
    current_text = text_box.get("1.0", tk.END).strip()
    clipboard_text = get_clipboard_text()
    
    if clipboard_text and clipboard_text != current_text:
        text_box.delete("1.0", tk.END)
        text_box.insert("1.0", clipboard_text)
    
    # 每100毫秒检查一次
    root.after(100, update_text)

# --- 主程序 setup ---
root = tk.Tk()
root.title("置顶剪切板")
root.geometry("400x300")

# 设置窗口置顶
root.attributes('-topmost', True)

# 创建界面
text_box = tk.Text(root, font=("Arial", 10))
text_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# 开始监听剪切板
update_text()

root.mainloop()