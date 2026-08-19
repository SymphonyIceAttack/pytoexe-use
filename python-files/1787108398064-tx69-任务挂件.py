import tkinter as tk
from tkinter import ttk
import json
import os
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")

def load_tasks():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_tasks():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

tasks = load_tasks()  # list of {"text":..., "done":..., "date":...}

root = tk.Tk()
root.title("任务挂件")
root.geometry("260x420+1400+700")  # 默认放右下角，可按需改
root.attributes("-topmost", True)
root.configure(bg="#f5f7fa")

try:
    root.iconbitmap(default="")  # 没图标文件也不报错
except Exception:
    pass

# 顶部进度条
title = tk.Label(root, text="今日工作任务", bg="#f5f7fa", font=("微软雅黑", 11, "bold"))
title.pack(pady=(6, 2))

progress_var = tk.DoubleVar()
progress = ttk.Progressbar(root, variable=progress_var, maximum=100, length=220)
progress.pack(pady=(0, 2))
progress_label = tk.Label(root, text="0/0 完成 · 0%", bg="#f5f7fa", fg="#555")
progress_label.pack()

# 列表区
list_frame = tk.Frame(root, bg="#f5f7fa")
list_frame.pack(fill="both", expand=True, padx=8, pady=4)

chk_vars = {}

def refresh():
    for w in list_frame.winfo_children():
        w.destroy()
    chk_vars.clear()
    total = len(tasks)
    done = sum(1 for t in tasks if t["done"])
    pct = int(done / total * 100) if total else 0
    progress_var.set(pct)
    progress_label.config(text=f"{done}/{total} 完成 · {pct}%")
    for idx, t in enumerate(tasks):
        var = tk.BooleanVar(value=t["done"])
        chk_vars[idx] = var
        cb = tk.Checkbutton(
            list_frame, text=t["text"], variable=var,
            bg="#f5f7fa", anchor="w", justify="left",
            command=lambda i=idx, v=var: toggle(i, v)
        )
        if t["done"]:
            cb.config(fg="#999", font=("微软雅黑", 9, "overstrike"))
        else:
            cb.config(fg="#222", font=("微软雅黑", 9))
        cb.pack(fill="x", pady=1)

def toggle(idx, var):
    tasks[idx]["done"] = var.get()
    save_tasks()
    refresh()

# 输入区
entry = tk.Entry(root, width=24, font=("微软雅黑", 9))
entry.pack(pady=(2, 2))

def add_task(evt=None):
    txt = entry.get().strip()
    if not txt:
        return
    tasks.append({"text": txt, "done": False, "date": datetime.now().strftime("%Y-%m-%d")})
    entry.delete(0, tk.END)
    save_tasks()
    refresh()

add_btn = tk.Button(root, text="添加", width=8, command=add_task)
add_btn.pack(pady=(0, 4))
entry.bind("<Return>", add_task)

# 清空已完成
def clear_done():
    global tasks
    tasks = [t for t in tasks if not t["done"]]
    save_tasks()
    refresh()

clear_btn = tk.Button(root, text="清除已完成", width=12, command=clear_done)
clear_btn.pack(pady=(0, 6))

refresh()
root.mainloop()