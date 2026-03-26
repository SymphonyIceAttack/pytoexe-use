"""
作者：Cherry5033MC
协议：MIT
意味着你可以免费商用、商用此代码，但是必须保留原作者的版权声明和许可信息。
此程序默认仅适用于Windows！提供支持版本为Win10 22H2至Win11 22H2！其余版本不提供支持
其他系统请在最后几行修改
"""
import tkinter as tk
import subprocess
from tkinter.scrolledtext import ScrolledText
import webbrowser

def show_file_and_continue(file_path, callback):
    """
    显示 TXT 文件内容的窗口，点击确认后执行回调函数。
    
    :param file_path: TXT 文件路径
    :param callback: 点击确认后执行的回调函数（无参数）
    """
    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        content = f"错误：文件 '{file_path}' 未找到。"
    except Exception as e:
        content = f"读取文件时出错：{e}"

    # 创建主窗口
    root = tk.Tk()
    root.title("文件内容展示")
    root.geometry("1200x800")

    # 添加一个带滚动条的文本框显示内容
    text_area = ScrolledText(root, wrap=tk.WORD, font=("Consolas", 10))
    text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    text_area.insert(tk.END, content)
    text_area.config(state=tk.DISABLED)  # 设置为只读

    # 确认按钮
    def on_confirm():
        root.destroy()          # 关闭窗口
        callback()              # 执行后续操作

    btn = tk.Button(root, text="确认", command=on_confirm, width=10)
    btn.pack(pady=10)

    # 进入消息循环
    root.mainloop()

def after_confirm():
    """点击确认后要执行的操作"""
    # 这里可以放置任何后续代码，例如继续执行其他任务

if __name__ == "__main__":
    # 替换为你的 TXT 文件路径
    file_path = "lisence.txt"
    show_file_and_continue(file_path, after_confirm)
#启动http服务器，防止浏览器file协议安全设置
# 创建隐藏窗口的进程
subprocess.Popen(
    ['python', '-m', 'http.server', '2824'],
    creationflags=subprocess.CREATE_NO_WINDOW  # 仅 Windows
)
#其他系统改法：
#os.system("python -m http.server 2824")

#生成列表
subprocess.Popen(
    ['node', 'generate_filelist.js'],
    creationflags=subprocess.CREATE_NO_WINDOW  # 仅 Windows
)
#其他系统改法：
#os.system("node generate_filelist.js")
url = "http://localhost:2824"
webbrowser.open(url)            # 使用默认浏览器打开
