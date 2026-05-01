import tkinter as tk
from tkinter import ttk, scrolledtext
import sys
import threading
import time

# 重定向输出/错误到GUI文本框


class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)  # 自动滚动到底部
        self.text_widget.configure(state=tk.DISABLED)

    def flush(self):
        pass

# 主窗口类


class CodeRunnerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python 代码执行工具")
        self.root.geometry("900x700")

        # 运行线程控制
        self.running_thread = None
        self.stop_flag = False

        # ========== 代码输入框 ==========
        ttk.Label(root, text="请输入要执行的代码：", font=("微软雅黑", 11)).pack(pady=5)
        self.code_text = scrolledtext.ScrolledText(
            root, width=100, height=15, font=("Consolas", 10))
        self.code_text.pack(pady=5, padx=10)

        # ========== 输入框 ==========
        ttk.Label(root, text="输入（input() 内容）：", font=("微软雅黑", 11)).pack(pady=2)
        self.input_entry = ttk.Entry(root, width=80, font=("微软雅黑", 10))
        self.input_entry.pack(pady=2)

        # ========== 按钮区域 ==========
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=8)

        self.run_btn = ttk.Button(
            btn_frame, text="运行代码", command=self.start_run_thread)
        self.run_btn.grid(row=0, column=0, padx=10)

        self.stop_btn = ttk.Button(
            btn_frame, text="结束运行", command=self.stop_run, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=10)

        # ========== 输出框 ==========
        ttk.Label(root, text="控制台输出：", font=("微软雅黑", 11)).pack(pady=5)
        self.output_text = scrolledtext.ScrolledText(
            root, width=100, height=15, font=("Consolas", 10))
        self.output_text.pack(pady=5, padx=10)
        self.output_text.configure(state=tk.DISABLED)

        # 重定向标准输出和错误
        sys.stdout = RedirectText(self.output_text)
        sys.stderr = RedirectText(self.output_text)

    # 运行代码（在线程里执行，防止界面卡死）
    def run_code(self):
        self.run_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.stop_flag = False

        try:
            # 清空输出
            self.output_text.configure(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END)
            self.output_text.configure(state=tk.DISABLED)

            # 获取代码
            code = self.code_text.get(1.0, tk.END)

            # 准备局部变量（让 input 可用）
            local_vars = {}

            # 自定义 input 函数，从输入框获取内容
            def gui_input(prompt=""):
                if self.stop_flag:
                    raise KeyboardInterrupt
                print(prompt, end="")
                return self.input_entry.get()

            local_vars["input"] = gui_input

            # 执行代码
            exec(code, globals(), local_vars)

        except KeyboardInterrupt:
            print("\n[已手动停止运行]")
        except Exception as e:
            print(f"\n[错误] {e}")
        finally:
            self.run_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)

    # 启动线程运行
    def start_run_thread(self):
        self.running_thread = threading.Thread(target=self.run_code)
        self.running_thread.start()

    # 结束运行
    def stop_run(self):
        self.stop_flag = True
        print("\n[正在停止...]")


# 启动程序
if __name__ == "__main__":
    window = tk.Tk()
    app = CodeRunnerGUI(window)
    window.mainloop()
