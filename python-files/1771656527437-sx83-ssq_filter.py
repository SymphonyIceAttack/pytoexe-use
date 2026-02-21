import tkinter as tk
from tkinter import ttk, messagebox, Canvas, Frame, Scrollbar

all_3d = [f"{i:03d}" for i in range(1000)]  # 修正：直接用字符串列表

def filter_ultimate(nums, dans_groups, two_codes_include, two_codes_exclude, kill_num,
                    hezhi_min, hezhi_max, tail_min, tail_max,
                    span_min, span_max, span_tail_min, span_tail_max,
                    ji_ou, da_xiao, zhi_he, lu012_cond,
                    duan_zu_list, zu_type):
    res = []
    # 预处理杀号
    kill_num = set(kill_num)
    
    for n_str in nums:
        a, b, c = int(n_str[0]), int(n_str[1]), int(n_str[2])
        arr = [a, b, c]
        n = int(n_str)

        # 杀号
        if kill_num & set(arr):  # 集合交集，更快
            continue

        # 无限胆组
        dan_ok = True
        for dg, need in dans_groups:
            dg_set = set(dg)
            cnt = len(dg_set & set(arr))
            if cnt != need:
                dan_ok = False
                break
        if not dan_ok:
            continue

        # 二码必出（至少包含一组）
        if two_codes_include:
            pairs = {(a,b), (a,c), (b,c)}
            pairs_norm = {tuple(sorted(p)) for p in pairs}
            found = False
            for tc in two_codes_include:
                if len(tc) == 2:  # 确保是两个数字
                    tc_sorted = tuple(sorted(tc))
                    if tc_sorted in pairs_norm:
                        found = True
                        break
            if not found:
                continue

        # 二码排除（不能包含任何一组）
        if two_codes_exclude:
            pairs = {(a,b), (a,c), (b,c)}
            pairs_norm = {tuple(sorted(p)) for p in pairs}
            exclude_found = False
            for tc in two_codes_exclude:
                if len(tc) == 2:
                    tc_sorted = tuple(sorted(tc))
                    if tc_sorted in pairs_norm:
                        exclude_found = True
                        break
            if exclude_found:  # 只要发现一组，就排除
                continue

        # 和值
        hz = sum(arr)
        if not (hezhi_min <= hz <= hezhi_max):
            continue

        # 和尾
        hw = hz % 10
        if not (tail_min <= hw <= tail_max):
            continue

        # 跨度
        sp = max(arr) - min(arr)
        if not (span_min <= sp <= span_max):
            continue

        # 跨尾
        spt = sp % 10
        if not (span_tail_min <= spt <= span_tail_max):
            continue

        # 奇偶
        ji = sum(1 for x in arr if x % 2 == 1)
        ou = 3 - ji
        if ji_ou == "全奇" and ji != 3:
            continue
        if ji_ou == "全偶" and ou != 3:
            continue
        if ji_ou == "2奇1偶" and not (ji == 2 and ou == 1):
            continue
        if ji_ou == "2偶1奇" and not (ou == 2 and ji == 1):
            continue

        # 大小
        da = sum(1 for x in arr if x >= 5)
        xiao = 3 - da
        if da_xiao == "全大" and da != 3:
            continue
        if da_xiao == "全小" and xiao != 3:
            continue
        if da_xiao == "2大1小" and not (da == 2 and xiao == 1):
            continue
        if da_xiao == "2小1大" and not (xiao == 2 and da == 1):
            continue

        # 质合
        zhi_set = {2,3,5,7}
        zh = sum(1 for x in arr if x in zhi_set)
        he = 3 - zh
        if zhi_he == "全质" and zh != 3:
            continue
        if zhi_he == "全合" and he != 3:
            continue
        if zhi_he == "2质1合" and not (zh == 2 and he == 1):
            continue
        if zhi_he == "2合1质" and not (he == 2 and zh == 1):
            continue

        # 012路
        lu0 = sum(1 for x in arr if x % 3 == 0)
        lu1 = sum(1 for x in arr if x % 3 == 1)
        lu2 = sum(1 for x in arr if x % 3 == 2)
        if lu012_cond == "0路多" and not (lu0 >= lu1 and lu0 >= lu2):
            continue
        if lu012_cond == "1路多" and not (lu1 >= lu0 and lu1 >= lu2):
            continue
        if lu012_cond == "2路多" and not (lu2 >= lu0 and lu2 >= lu1):
            continue

        # 断组 (修正逻辑：指定的组别中不能出号)
        if duan_zu_list:
            valid_duan = False
            for group in duan_zu_list:
                # 如果这一注号码中的数字，全部都不在“断”的组里，则有效
                if not any(digit in group for digit in arr):
                    valid_duan = True
                    break
            if not valid_duan:
                continue

        # 组型
        s = set(arr)
        if zu_type == "组三" and len(s) != 2:
            continue
        if zu_type == "组六" and len(s) != 3:
            continue
        if zu_type == "豹子" and len(s) != 1:
            continue

        res.append(n_str)
    return res

# ------------------- 界面 (续) -------------------

# ... (你之前的 left_frame, right_frame 定义)

# ========== 无限胆组 (续) ==========
# 这里补全滚动条逻辑
dan_canvas = tk.Canvas(dan_container, width=320, height=180, bg="#ffffff")
dan_scroll = ttk.Scrollbar(dan_container, orient="vertical", command=dan_canvas.yview)
dan_frame_inner = ttk.Frame(dan_canvas)

dan_frame_inner.bind(
    "<Configure>",
    lambda e: dan_canvas.configure(scrollregion=dan_canvas.bbox("all"))
)
dan_canvas.create_window((0, 0), window=dan_frame_inner, anchor="nw")
dan_canvas.configure(yscrollcommand=dan_scroll.set)

dan_canvas.pack(side="left", fill="both", expand=True)
dan_scroll.pack(side="right", fill="y")

# 用于存储动态生成的胆码输入框
dan_entries = []

def add_dan_row():
    row = ttk.Frame(dan_frame_inner)
    row.pack(fill="x", pady=2)
    
    ttk.Label(row, text="胆码:").pack(side="left")
    ent_dan = ttk.Entry(row, width=10)
    ent_dan.pack(side="left", padx=2)
    ent_dan.insert(0, "1,2") # 提示
    
    ttk.Label(row, text="= ").pack(side="left")
    combo_val = ttk.Combobox(row, values=["0", "1", "2", "3"], width=3)
    combo_val.pack(side="left", padx=2)
    combo_val.set("1")
    
    btn_del = ttk.Button(row, text="删除", command=lambda: row.destroy())
    btn_del.pack(side="left", padx=5)
    
    dan_entries.append((ent_dan, combo_val))

btn_add_dan = ttk.Button(dan_container, text="添加胆组", command=add_dan_row)
btn_add_dan.pack(pady=5)
add_dan_row() # 默认一行

# ========== 二码必出 ==========
erma_frame = ttk.LabelFrame(left_frame, text="二码功能", padding=8)
erma_frame.pack(fill=tk.X, pady=4)

ttk.Label(erma_frame, text="二码必出 (逗号分隔):").grid(row=0, column=0, sticky="w")
ent_erma_include = ttk.Entry(erma_frame, width=20)
ent_erma_include.grid(row=0, column=1)
ent_erma_include.insert(0, "1,2|3,4") # 示例：多组用|分隔

ttk.Label(erma_frame, text="二码排除:").grid(row=1, column=0, sticky="w")
ent_erma_exclude = ttk.Entry(erma_frame, width=20)
ent_erma_exclude.grid(row=1, column=1)
ent_erma_exclude.insert(0, "5,6")

# ========== 杀号与和值 ==========
kill_frame = ttk.LabelFrame(left_frame, text="基础过滤", padding=8)
kill_frame.pack(fill=tk.X, pady=4)

ttk.Label(kill_frame, text="杀号 (0-9):").grid(row=0, column=0, sticky="w")
ent_kill = ttk.Entry(kill_frame, width=25)
ent_kill.grid(row=0, column=1, columnspan=2)
ent_kill.insert(0, "0,8,9")

ttk.Label(kill_frame, text="和值:").grid(row=1, column=0, sticky="w")
spin_hezhi_min = ttk.Spinbox(kill_frame, from_=0, to=27, width=5)
spin_hezhi_min.grid(row=1, column=1)
spin_hezhi_min.set(10)
ttk.Label(kill_frame, text="至").grid(row=1, column=2, sticky="w")
spin_hezhi_max = ttk.Spinbox(kill_frame, from_=0, to=27, width=5)
spin_hezhi_max.grid(row=1, column=3)
spin_hezhi_max.set(20)

ttk.Label(kill_frame, text="和尾:").grid(row=2, column=0, sticky="w")
spin_tail_min = ttk.Spinbox(kill_frame, from_=0, to=9, width=5)
spin_tail_min.grid(row=2, column=1)
spin_tail_min.set(0)
ttk.Label(kill_frame, text="至")
spin_tail_min.grid(row=2, column=2, sticky="w")
spin_tail_max = ttk.Spinbox(kill_frame, from_=0, to=9, width=5)
spin_tail_max.grid(row=2, column=3)
spin_tail_max.set(9)

ttk.Label(kill_frame, text="跨度:").grid(row=3, column=0, sticky="w")
spin_span_min = ttk.Spinbox(kill_frame, from_=0, to=9, width=5)
spin_span_min.grid(row=3, column=1)
spin_span_min.set(0)
ttk.Label(kill_frame, text="至")
spin_span_min.grid(row=3, column=2, sticky="w")
spin_span_max = ttk.Spinbox(kill_frame, from_=0, to=9, width=5)
spin_span_max.grid(row=3, column=3)
spin_span_max.set(9)

ttk.Label(kill_frame, text="跨尾:").grid(row=4, column=0, sticky="w")
spin_span_tail_min = ttk.Spinbox(kill_frame, from_=0, to=9, width=5)
spin_span_tail_min.grid(row=4, column=1)
spin_span_tail_min.set(0)
ttk.Label(kill_frame, text="至")
spin_span_tail_min.grid(row=4, column=2, sticky="w")
spin_span_tail_max = ttk.Spinbox(kill_frame, from_=0, to=9, width=5)
spin_span_tail_max.grid(row=4, column=3)
spin_span_tail_max.set(9)

# ========== 形态选择 ==========
xing_frame = ttk.LabelFrame(left_frame, text="形态特征", padding=8)
xing_frame.pack(fill=tk.X, pady=4)

# 奇偶
ttk.Label(xing_frame, text="奇偶:").grid(row=0, column=0, sticky="w")
combo_jiou = ttk.Combobox(xing_frame, values=["不限", "全奇", "全偶", "2奇1偶", "2偶1奇"], state="readonly", width=8)
combo_jiou.grid(row=0, column=1)
combo_jiou.set("不限")

# 大小
ttk.Label(xing_frame, text="大小:").grid(row=1, column=0, sticky="w")
combo_daxiao = ttk.Combobox(xing_frame, values=["不限", "全大", "全小", "2大1小", "2小1大"], state="readonly", width=8)
combo_daxiao.grid(row=1, column=1)
combo_daxiao.set("不限")

# 质合
ttk.Label(xing_frame, text="质合:").grid(row=2, column=0, sticky="w")
combo_zhihe = ttk.Combobox(xing_frame, values=["不限", "全质", "全合", "2质1合", "2合1质"], state="readonly", width=8)
combo_zhihe.grid(row=2, column=1)
combo_zhihe.set("不限")

# 012路
ttk.Label(xing_frame, text="012路:").grid(row=3, column=0, sticky="w")
combo_lu = ttk.Combobox(xing_frame, values=["不限", "0路多", "1路多", "2路多"], state="readonly", width=8)
combo_lu.grid(row=3, column=1)
combo_lu.set("不限")

# ========== 断组 ==========
duan_frame = ttk.LabelFrame(left_frame, text="断组 (每行一组)", padding=8)
duan_frame.pack(fill=tk.X, pady=4)

duan_entries = []
def add_duan_row():
    row = ttk.Frame(duan_frame)
    row.pack(fill="x", pady=2)
    ent = ttk.Entry(row, width=20)
    ent.pack(side="left")
    ent.insert(0, "0,1,2")
    btn = ttk.Button(row, text="删除", command=lambda: (row.destroy(), duan_entries.remove(ent)))
    btn.pack(side="left", padx=5)
    duan_entries.append(ent)

ttk.Button(duan_frame, text="添加断组", command=add_duan_row).pack()
add_duan_row() # 默认一行

# ========== 组型 ==========
zu_frame = ttk.LabelFrame(left_frame, text="组型", padding=8)
zu_frame.pack(fill=tk.X, pady=4)

combo_zu = ttk.Combobox(zu_frame, values=["不限", "组三", "组六", "豹子"], state="readonly", width=8)
combo_zu.pack()
combo_zu.set("不限")

# ========== 右侧结果显示 ==========
result_text = tk.Text(right_frame, font=("Courier", 10), wrap="none")
result_text.pack(fill="both", expand=True, side="left")

scroll_y = ttk.Scrollbar(right_frame, orient="vertical", command=result_text.yview)
scroll_y.pack(side="right", fill="y")
result_text.config(yscrollcommand=scroll_y.set)

# ========== 按钮 ==========
btn_frame = ttk.Frame(root)
btn_frame.pack(side="bottom", fill="x", padx=10, pady=10)

def start_filter():
    try:
        # 解析胆组
        dans_groups = []
        for ent, combo in dan_entries:
            dan_text = ent.get().strip()
            need_val = int(combo.get())
            if dan_text:
                nums = [int(x.strip()) for x in dan_text.split(",") if x.strip().isdigit()]
                dans_groups.append((nums, need_val))
        
        # 解析二码
        two_codes_include = []
        inc_text = ent_erma_include.get().strip()
        if inc_text:
            for group in inc_text.split("|"):
                nums = [int(x.strip()) for x in group.split(",") if x.strip().isdigit()]
                if len(nums) == 2:
                    two_codes_include.append(nums)
        
        two_codes_exclude = []
        exc_text = ent_erma_exclude.get().strip()
        if exc_text:
            nums = [int(x.strip()) for x in exc_text.split(",") if x.strip().isdigit()]
            if len(nums) == 2:
                two_codes_exclude = [nums]
        
        # 解析杀号
        kill_num = []
        kill_text = ent_kill.get().strip()
        if kill_text:
            kill_num = [int(x.strip()) for x in kill_text.split(",") if x.strip().isdigit()]

        # 解析断组
        duan_zu_list = []
        for ent in duan_entries:
            text = ent.get().strip()
            if text:
                nums = [int(x.strip()) for x in text.split(",") if x.strip().isdigit()]
                duan_zu_list.append(nums)

        # 执行过滤
        res = filter_ultimate(
            nums=all_3d,
            dans_groups=dans_groups,
            two_codes_include=two_codes_include,
            two_codes_exclude=two_codes_exclude,
            kill_num=kill_num,
            hezhi_min=int(spin_hezhi_min.get()),
            hezhi_max=int(spin_hezhi_max.get()),
            tail_min=int(spin_tail_min.get()),
            tail_max=int(spin_tail_max.get()),
            span_min=int(spin_span_min.get()),
            span_max=int(spin_span_max.get()),
            span_tail_min=int(spin_span_tail_min.get()),
            span_tail_max=int(spin_span_tail_max.get()),
            ji_ou=combo_jiou.get() if combo_jiou.get() != "不限" else "",
            da_xiao=combo_daxiao.get() if combo_daxiao.get() != "不限" else "",
            zhi_he=combo_zhihe.get() if combo_zhihe.get() != "不限" else "",
            lu012_cond=combo_lu.get() if combo_lu.get() != "不限" else "",
            duan_zu_list=duan_zu_list,
            zu_type=combo_zu.get() if combo_zu.get() != "不限" else ""
        )

        # 显示结果
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, f"共过滤出 {len(res)} 注:\n\n")
        # 每行显示10个
        for i in range(0, len(res), 10):
            line = " ".join(res[i:i+10])
            result_text.insert(tk.END, line + "\n")

    except Exception as e:
        messagebox.showerror("错误", str(e))

btn_run = ttk.Button(btn_frame, text="开始过滤 (F5)", command=start_filter)
btn_run.pack(side="right", padx=20)

# 快捷键
root.bind('<F5>', lambda e: start_filter())

root.mainloop()