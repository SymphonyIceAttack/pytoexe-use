import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import uuid
import re
import json

class RazerMacroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("雷蛇宏生成器")
        self.root.geometry("1000x850")
        
        self.groups = []
        
        # === 1. 顶部基础设置 ===
        setting_frame = ttk.LabelFrame(root, text="1. 枪械参数与倍镜转换", padding=10)
        setting_frame.pack(fill="x", padx=10, pady=5)
        
        # 第一行：名称、射速、弹匣
        frame_row1 = ttk.Frame(setting_frame)
        frame_row1.pack(fill="x", pady=2)
        
        ttk.Label(frame_row1, text="宏名称:").pack(side="left", padx=5)
        self.entry_name = ttk.Entry(frame_row1, width=15)
        self.entry_name.insert(0, "Weapon_Macro")
        self.entry_name.pack(side="left", padx=5)
        
        ttk.Label(frame_row1, text="射速(RPM):").pack(side="left", padx=5)
        self.entry_rpm = ttk.Entry(frame_row1, width=8)
        self.entry_rpm.insert(0, "400")
        self.entry_rpm.pack(side="left", padx=5)
        
        ttk.Label(frame_row1, text="弹匣发数:").pack(side="left", padx=5)
        self.entry_total = ttk.Entry(frame_row1, width=8)
        self.entry_total.insert(0, "20")
        self.entry_total.pack(side="left", padx=5)

        # 第二行：启动延迟 & 倍镜转换
        frame_row2 = ttk.Frame(setting_frame)
        frame_row2.pack(fill="x", pady=5)
        
        lbl_delay = ttk.Label(frame_row2, text="启动延迟(秒):")
        lbl_delay.pack(side="left", padx=5)
        self.entry_start_delay = ttk.Entry(frame_row2, width=8)
        self.entry_start_delay.insert(0, "0.035")
        self.entry_start_delay.pack(side="left", padx=5)

        ttk.Separator(frame_row2, orient="vertical").pack(side="left", fill="y", padx=15)
        
        ttk.Label(frame_row2, text="倍镜转换: 从", foreground="blue").pack(side="left")
        self.entry_scope_from = ttk.Entry(frame_row2, width=4)
        self.entry_scope_from.insert(0, "1")
        self.entry_scope_from.pack(side="left", padx=2)
        ttk.Label(frame_row2, text="倍 转").pack(side="left")
        self.entry_scope_to = ttk.Entry(frame_row2, width=4)
        self.entry_scope_to.insert(0, "2")
        self.entry_scope_to.pack(side="left", padx=2)
        ttk.Label(frame_row2, text="倍").pack(side="left")
        ttk.Button(frame_row2, text="一键转换所有偏移量", command=self.convert_scope).pack(side="left", padx=10)
        
        # === 2. 射击模式选择 ===
        frame_mode = ttk.LabelFrame(root, text="2. 射击模式", padding=10)
        frame_mode.pack(fill="x", padx=10, pady=5)
        
        self.fire_mode = tk.StringVar(value="auto")
        
        rb_auto = ttk.Radiobutton(frame_mode, text="全自动 (按住不放 -> 持续压枪)", variable=self.fire_mode, value="auto")
        rb_auto.pack(side="left", padx=20)
        
        rb_semi = ttk.Radiobutton(frame_mode, text="半自动 (循环点击 -> 点击+移动)", variable=self.fire_mode, value="semi")
        rb_semi.pack(side="left", padx=20)

        # === 3. 分组编辑 ===
        edit_frame = ttk.LabelFrame(root, text="3. 弹道设置 (双击列表 或 点击下方预览文本 可快速修改)", padding=10)
        edit_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        input_inner_frame = ttk.Frame(edit_frame)
        input_inner_frame.pack(fill="x", pady=5)
        
        ttk.Label(input_inner_frame, text="起始:").pack(side="left")
        self.entry_start = ttk.Entry(input_inner_frame, width=5)
        self.entry_start.pack(side="left", padx=2)
        
        ttk.Label(input_inner_frame, text="结束:").pack(side="left")
        self.entry_end = ttk.Entry(input_inner_frame, width=5)
        self.entry_end.pack(side="left", padx=2)
        
        # 提示用户新的坐标系
        ttk.Label(input_inner_frame, text="X(负左/正右):", foreground="green").pack(side="left", padx=(10,0))
        self.entry_x = ttk.Entry(input_inner_frame, width=5)
        self.entry_x.insert(0, "0")
        self.entry_x.pack(side="left", padx=2)
        
        ttk.Label(input_inner_frame, text="Y(负下/正上):", foreground="green").pack(side="left", padx=(10,0))
        self.entry_y = ttk.Entry(input_inner_frame, width=5)
        self.entry_y.insert(0, "-30") # 默认压枪向下，所以是负数
        self.entry_y.pack(side="left", padx=2)
        
        ttk.Button(input_inner_frame, text="添加/修改组", command=self.add_group).pack(side="left", padx=15)
        ttk.Button(input_inner_frame, text="删除选中", command=self.delete_group).pack(side="left")

        columns = ("start", "end", "x", "y")
        self.tree = ttk.Treeview(edit_frame, columns=columns, show="headings", height=6)
        self.tree.heading("start", text="开始")
        self.tree.heading("end", text="结束")
        self.tree.heading("x", text="用户 X")
        self.tree.heading("y", text="用户 Y")
        for col in columns: self.tree.column(col, width=100, anchor="center")
        self.tree.pack(fill="x", pady=5)
        
        # 绑定树状图双击事件
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        
        # === 4. 底部 ===
        bottom_frame = ttk.LabelFrame(root, text="4. 预览与导入导出", padding=10)
        bottom_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.preview_text = tk.Text(bottom_frame, height=12, width=70, font=("Consolas", 10), cursor="hand2")
        self.preview_text.pack(side="left", fill="both", expand=True)
        # 绑定预览文本点击事件
        self.preview_text.bind("<Button-1>", self.on_preview_click)
        
        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.pack(side="right", fill="y", padx=10)
        
        ttk.Button(btn_frame, text="刷新预览", command=self.update_preview).pack(pady=5, fill="x")
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=10)
        
        ttk.Label(btn_frame, text="[工程文件管理]").pack()
        ttk.Button(btn_frame, text="📂 导入 JSON 工程", command=self.load_project).pack(pady=2, fill="x")
        ttk.Button(btn_frame, text="💾 保存 JSON 工程", command=self.save_project).pack(pady=2, fill="x")
        
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=10)
        ttk.Label(btn_frame, text="[驱动专用]").pack()
        ttk.Button(btn_frame, text="🚀 导出 雷蛇XML", command=self.export_xml).pack(pady=5, fill="x")

        # 默认数据
        self.insert_group_data(1, 20, 0, -30)
        self.update_preview()

    # ================= 功能实现 =================

    def convert_scope(self):
        """倍镜转换计算"""
        try:
            f_from = float(self.entry_scope_from.get())
            f_to = float(self.entry_scope_to.get())
            if f_from <= 0: return messagebox.showerror("错误", "原倍数不能为0")
            
            factor = f_to / f_from
            for g in self.groups:
                g['x'] = round(g['x'] * factor)
                g['y'] = round(g['y'] * factor)
            
            self.refresh_tree()
            self.update_preview()
            messagebox.showinfo("转换成功", f"所有偏移量已按照 {factor:.2f} 倍率缩放！")
        except ValueError:
            messagebox.showerror("错误", "倍数必须是数字")

    def on_tree_double_click(self, event):
        """双击列表项进入编辑模式"""
        selected = self.tree.selection()
        if not selected: return
        values = self.tree.item(selected[0], "values")
        self.entry_start.delete(0, tk.END); self.entry_start.insert(0, values[0])
        self.entry_end.delete(0, tk.END); self.entry_end.insert(0, values[1])
        self.entry_x.delete(0, tk.END); self.entry_x.insert(0, values[2])
        self.entry_y.delete(0, tk.END); self.entry_y.insert(0, values[3])

    def on_preview_click(self, event):
        """点击预览文本自动填入修改框"""
        # 获取点击的行文本
        index = self.preview_text.index(f"@{event.x},{event.y}")
        line_num = index.split('.')[0]
        line_text = self.preview_text.get(f"{line_num}.0", f"{line_num}.end")
        
        # 用正则匹配 "间隔XX" 或 "第XX发"
        match = re.search(r'(第|间隔)(\d+)', line_text)
        if match:
            bullet_idx = int(match.group(2))
            # 找到这颗子弹属于哪个组
            for g in self.groups:
                if g['start'] <= bullet_idx <= g['end']:
                    self.entry_start.delete(0, tk.END); self.entry_start.insert(0, g['start'])
                    self.entry_end.delete(0, tk.END); self.entry_end.insert(0, g['end'])
                    self.entry_x.delete(0, tk.END); self.entry_x.insert(0, g['x'])
                    self.entry_y.delete(0, tk.END); self.entry_y.insert(0, g['y'])
                    # 提供视觉反馈
                    self.preview_text.tag_add("highlight", f"{line_num}.0", f"{line_num}.end")
                    self.preview_text.tag_config("highlight", background="yellow", foreground="black")
                    self.root.after(300, lambda: self.preview_text.tag_remove("highlight", "1.0", tk.END))
                    break

    def insert_group_data(self, start, end, x, y):
        self.groups.append({"start": int(start), "end": int(end), "x": int(x), "y": int(y)})
        self.groups.sort(key=lambda k: k['start'])
        self.refresh_tree()

    def refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for g in self.groups:
            self.tree.insert("", "end", values=(g['start'], g['end'], g['x'], g['y']))

    def add_group(self):
        try:
            s, e = int(self.entry_start.get()), int(self.entry_end.get())
            x, y = int(self.entry_x.get()), int(self.entry_y.get())
            if s > e: return messagebox.showerror("错误", "开始必须小于结束")
            
            # 如果存在重叠或相同的组，先清理掉旧的
            self.groups = [g for g in self.groups if not (g['start'] == s and g['end'] == e)]
            
            self.insert_group_data(s, e, x, y)
            self.update_preview()
        except ValueError:
            messagebox.showerror("错误", "请输入数字")

    def delete_group(self):
        sel = self.tree.selection()
        if sel:
            item = self.tree.item(sel)['values']
            for g in self.groups:
                if g['start'] == item[0] and g['end'] == item[1]:
                    self.groups.remove(g)
                    break
            self.refresh_tree()
            self.update_preview()

    def calculate(self):
        try:
            rpm = int(self.entry_rpm.get())
            total = int(self.entry_total.get())
        except: return None, None
        
        ms_per_bullet = int(60000 / rpm) 
        offsets = [{"idx": i+1, "x": 0, "y": 0} for i in range(total)]
        
        for g in self.groups:
            s_idx = max(0, g['start'] - 1)
            e_idx = min(total, g['end'])
            for i in range(s_idx, e_idx):
                if i < len(offsets):
                    # === 坐标系转换逻辑 ===
                    # Windows/Razer底层: X正=右, Y正=下
                    # 用户需求直觉坐标: X正=右(不变), Y负=下(取反), Y正=上(取反)
                    offsets[i]['x'] = g['x']
                    offsets[i]['y'] = -g['y'] # 核心：将用户的直觉Y翻转为雷蛇物理Y
        return ms_per_bullet, offsets

    def update_preview(self):
        ms, offsets = self.calculate()
        if not ms: return
        
        mode = self.fire_mode.get()
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, f"模式: {'全自动' if mode == 'auto' else '半自动'}\n")
        self.preview_text.insert(tk.END, f"提示: 点击下方任意一行，即可将数据填入编辑框。\n")
        self.preview_text.insert(tk.END, f"---------------------------\n")
        
        cum_x, cum_y = 960, 540
        for i, a in enumerate(offsets[:-1]):
            # 这里为了不让用户困惑，预览仍显示【用户直觉坐标】，但旁注实际底层运作
            dx_razer, dy_razer = a['x'], a['y']
            dx_user, dy_user = dx_razer, -dy_razer 
            
            cum_x += dx_razer
            cum_y += dy_razer
            
            if mode == 'auto':
                self.preview_text.insert(tk.END, f"间隔{a['idx']:02d}: 输入(X:{dx_user}, Y:{dy_user}) => 雷蛇驱动执行累加坐标({cum_x}, {cum_y})\n")
            else:
                self.preview_text.insert(tk.END, f"第{a['idx']:02d}发: 点击! -> 输入(X:{dx_user}, Y:{dy_user}) => 雷蛇驱动偏移量 X:{dx_razer} Y:{dy_razer}\n")

    # === 工程文件存取 (推荐的脚本导入导出方式) ===
    def save_project(self):
        fpath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON 工程文件", "*.json")])
        if not fpath: return
        
        data = {
            "name": self.entry_name.get(),
            "rpm": self.entry_rpm.get(),
            "total": self.entry_total.get(),
            "start_delay": self.entry_start_delay.get(),
            "mode": self.fire_mode.get(),
            "groups": self.groups
        }
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("保存成功", "JSON 工程文件已保存，下次可直接导入继续编辑！")

    def load_project(self):
        fpath = filedialog.askopenfilename(filetypes=[("JSON 工程文件", "*.json")])
        if not fpath: return
        
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.entry_name.delete(0, tk.END); self.entry_name.insert(0, data.get("name", "Weapon_Macro"))
            self.entry_rpm.delete(0, tk.END); self.entry_rpm.insert(0, data.get("rpm", "400"))
            self.entry_total.delete(0, tk.END); self.entry_total.insert(0, data.get("total", "20"))
            self.entry_start_delay.delete(0, tk.END); self.entry_start_delay.insert(0, data.get("start_delay", "0.035"))
            self.fire_mode.set(data.get("mode", "auto"))
            self.groups = data.get("groups", [])
            
            self.refresh_tree()
            self.update_preview()
            messagebox.showinfo("导入成功", "工程数据已完整恢复！")
        except Exception as e:
            messagebox.showerror("导入失败", f"文件格式错误: {e}")

    # === 原生XML导出 ===
    def export_xml(self):
        ms_interval, offsets = self.calculate()
        if not ms_interval: return
        
        name = self.entry_name.get()
        guid = str(uuid.uuid4())
        mode = self.fire_mode.get()
        
        try:
            start_delay = float(self.entry_start_delay.get())
        except:
            start_delay = 0.035
        
        macro_events_xml = ""
        
        if mode == "auto":
            macro_events_xml += f"""    <MacroEvent>
      <Type>2</Type>
      <MouseEvent><MouseButton>0</MouseButton><State>0</State></MouseEvent>
    </MacroEvent>
    <MacroEvent>
      <Type>0</Type>
      <Number>{start_delay}</Number>
    </MacroEvent>
"""
            global_x, global_y = 960, 540
            current_buffer_str = f"        <Buffer><x>{global_x}</x><y>{global_y}</y><time>0</time></Buffer>\n"
            
            valid_offsets = offsets[:-1]
            for item in valid_offsets:
                global_x += item['x']
                global_y += item['y'] # 这里的y已经是取反后的雷蛇物理y了
                current_buffer_str += f"        <Buffer><x>{global_x}</x><y>{global_y}</y><time>{ms_interval}</time></Buffer>\n"

            total_duration = (len(valid_offsets) * ms_interval) / 1000.0
            macro_events_xml += f"""    <MacroEvent>
      <Type>3</Type>
      <Number>{total_duration:.4f}</Number> 
      <MouseEvent>
{current_buffer_str}      </MouseEvent>
    </MacroEvent>
    <MacroEvent>
      <Type>2</Type>
      <MouseEvent><MouseButton>0</MouseButton><State>1</State></MouseEvent>
    </MacroEvent>
"""
        else:
            CLICK_DURATION = 0.05
            MOVE_DURATION_MS = ms_interval - int(CLICK_DURATION * 1000)
            if MOVE_DURATION_MS < 10: MOVE_DURATION_MS = 10
            MOVE_DURATION_SEC = MOVE_DURATION_MS / 1000.0
            
            macro_events_xml += f"""    <MacroEvent>
      <Type>0</Type>
      <Number>{start_delay}</Number>
    </MacroEvent>
"""
            valid_offsets = offsets[:-1]
            for item in valid_offsets:
                dx = item['x']
                dy = item['y'] # 这里的y已经是取反后的雷蛇物理y了
                
                macro_events_xml += """    <MacroEvent>
      <Type>2</Type>
      <MouseEvent><MouseButton>0</MouseButton><State>0</State></MouseEvent>
    </MacroEvent>
"""
                macro_events_xml += f"""    <MacroEvent>
      <Type>0</Type>
      <Number>{CLICK_DURATION}</Number>
    </MacroEvent>
"""
                macro_events_xml += """    <MacroEvent>
      <Type>2</Type>
      <MouseEvent><MouseButton>0</MouseButton><State>1</State></MouseEvent>
    </MacroEvent>
"""
                if dx != 0 or dy != 0:
                    buffer_str = f"        <Buffer><x>0</x><y>0</y><time>0</time></Buffer>\n"
                    buffer_str += f"        <Buffer><x>{dx}</x><y>{dy}</y><time>{MOVE_DURATION_MS}</time></Buffer>\n"
                    
                    macro_events_xml += f"""    <MacroEvent>
      <Type>3</Type>
      <Number>{MOVE_DURATION_SEC:.4f}</Number> 
      <MouseEvent>
{buffer_str}      </MouseEvent>
    </MacroEvent>
"""
                else:
                    macro_events_xml += f"""    <MacroEvent>
      <Type>0</Type>
      <Number>{MOVE_DURATION_SEC:.4f}</Number>
    </MacroEvent>
"""

        xml_content = f"""<Macro>
  <Name>{name}</Name>
  <Guid>{guid}</Guid>
  <Version>4</Version>
  <DelaySetting>0</DelaySetting>
  <MouseMoveType>relative</MouseMoveType>
  <MacroEvents>
{macro_events_xml}  </MacroEvents>
</Macro>"""
        
        fpath = filedialog.asksaveasfilename(initialfile=f"{name}.xml", filetypes=[("XML", "*.xml")])
        if fpath:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(xml_content)
            messagebox.showinfo("完成", f"导出 XML 成功！请导入到雷蛇雷云中。")

if __name__ == "__main__":
    root = tk.Tk()
    app = RazerMacroApp(root)
    root.mainloop()