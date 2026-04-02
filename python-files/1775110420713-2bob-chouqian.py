import tkinter as tk
from tkinter import ttk, messagebox
import random

# ====================== 固定名单（52人） ======================
NAMES = [
    "钟文斌", "尹鑫辰", "谢树培", "梁博", "张艺微", "王源旭", "杨心怡", "梁君浩", "杨珊珊",
    "贺菊花", "唐英翔", "梁于锴", "张镇杭", "胡健程", "罗武俊", "冯子琪", "曾阔航", "龙鑫权",
    "吴易达", "李宸磊", "朱军源", "张嘉怡", "欧阳美晴", "谭佳旺", "唐馨", "雷雨欣", "邓吉帅",
    "李游", "贺舜福", "欧阳吉祥", "李洪瑞", "彭靖轩", "黄安琪", "唐扬", "盘晨熙", "彭紫嫣",
    "骆星武", "廖媛媛", "曾嘉航", "罗一鸣", "谭群凯", "张青硕", "赵世泽", "史育宁", "邓敬轩",
    "黄湘源", "陈夕", "胡诗琪", "李奕璇", "杨紫瑜", "周思曼", "张焱茗"
]
# ===================================================================

def draw():
    try:
        count = int(var_count.get())
    except:
        messagebox.showwarning("提示", "请选择抽取人数")
        return

    if count < 1 or count > len(NAMES):
        messagebox.showwarning("提示", f"人数必须在 1~{len(NAMES)} 之间")
        return

    # 随机不重复抽取
    random.shuffle(NAMES)
    result = NAMES[:count]

    # 显示结果
    text_result.delete("1.0", tk.END)
    text_result.insert(tk.END, "🎉 抽签结果：\n\n")
    for i, name in enumerate(result, 1):
        text_result.insert(tk.END, f"{i}. {name}\n")

# ====================== 界面 ======================
root = tk.Tk()
root.title("固定名单抽签软件（52人）")
root.geometry("580x600")  # 加宽加高，适配52人名单展示

# 标题
tk.Label(root, text="📋 当前参与人员（共52人）", font=("微软雅黑", 12, "bold")).pack(pady=5)

# 展示固定名单（分行显示，更清晰）
text_names = tk.Text(root, width=70, height=12)
text_names.pack(pady=5)
# 按每行8人排版展示名单，方便查看
name_display = ""
for idx, name in enumerate(NAMES, 1):
    name_display += f"{idx:2d}. {name}  "
    if idx % 8 == 0:
        name_display += "\n"
text_names.insert(tk.END, name_display)
text_names.config(state=tk.DISABLED)  # 锁定名单，防止修改

# 选择抽取人数
tk.Label(root, text="选择抽取人数：", font=("微软雅黑", 11)).pack(pady=3)
var_count = tk.StringVar()
cbo_num = ttk.Combobox(root, textvariable=var_count, width=10, state="readonly")
cbo_num['values'] = [str(i) for i in range(1, len(NAMES)+1)]
cbo_num.current(0)  # 默认选1人
cbo_num.pack(pady=5)

# 抽签按钮（加大样式）
draw_btn = ttk.Button(root, text="开始抽签", command=draw, width=20)
draw_btn.pack(pady=10)

# 结果展示区
tk.Label(root, text="抽签结果：", font=("微软雅黑", 11)).pack()
text_result = tk.Text(root, width=70, height=12)
text_result.pack(pady=5)

root.mainloop()