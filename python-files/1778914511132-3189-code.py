import requests
import tkinter as tk
from tkinter import scrolledtext

def fetch_and_display():
    url = "http://yanabout.gt.tc/simple.txt"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.encoding = response.apparent_encoding
        response.raise_for_status()

        text_area.config(state=tk.NORMAL)
        text_area.delete("1.0", tk.END)
        text_area.insert(tk.END, response.text)
        text_area.config(state=tk.DISABLED)

        status_label.config(text=f"下载成功 | {len(response.content)} 字节")

    except requests.exceptions.ConnectionError:
        status_label.config(text="连接失败，请检查网络或地址")
    except requests.exceptions.Timeout:
        status_label.config(text="请求超时")
    except requests.exceptions.HTTPError as e:
        status_label.config(text=f"HTTP 错误: {e}")
    except Exception as e:
        status_label.config(text=f"错误: {type(e).__name__}: {e}")

root = tk.Tk()
root.title("simple.txt 内容查看器")
root.geometry("700x500")
root.configure(bg="#1e1e1e")

title_label = tk.Label(root, text="yanabout.gt.tc/simple.txt",
                       font=("Courier New", 14, "bold"),
                       fg="#e8c547", bg="#1e1e1e")
title_label.pack(pady=(15, 5))

text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD,
                                      font=("Courier New", 11),
                                      bg="#121212", fg="#d4d4d4",
                                      insertbackground="#d4d4d4",
                                      relief=tk.FLAT, bd=0)
text_area.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
text_area.config(state=tk.DISABLED)

status_label = tk.Label(root, text="点击下方按钮开始爬取",
                        font=("微软雅黑", 10),
                        fg="#7a7570", bg="#1e1e1e")
status_label.pack(pady=(0, 5))

btn = tk.Button(root, text="开始爬取", command=fetch_and_display,
                font=("微软雅黑", 11, "bold"),
                fg="#0d0d0d", bg="#e8c547",
                activebackground="#d4b43e", activeforeground="#0d0d0d",
                relief=tk.FLAT, cursor="hand2",
                padx=30, pady=6)
btn.pack(pady=(0, 15))

root.mainloop()
