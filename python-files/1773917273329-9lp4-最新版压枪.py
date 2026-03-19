import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import uuid
import re
import json

class RazerMacroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("通用鼠标宏生成器")
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
        ttk.Label(btn_frame, text="[脚本导出]").pack()
        # === 新增：导出 罗技Lua 按钮 ===
        ttk.Button(btn_frame, text="🟢 导出 罗技Lua", command=self.export_lua).pack(pady=5, fill="x")
        ttk.Button(btn_frame, text="🐍 导出 雷蛇XML", command=self.export_xml).pack(pady=5, fill="x")

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
        index = self.preview_text.index(f"@{event.x},{event.y}")
        line_num = index.split('.')[0]
        line_text = self.preview_text.get(f"{line_num}.0", f"{line_num}.end")
        
        match = re.search(r'(第|间隔)(\d+)', line_text)
        if match:
            bullet_idx = int(match.group(2))
            for g in self.groups:
                if g['start'] <= bullet_idx <= g['end']:
                    self.entry_start.delete(0, tk.END); self.entry_start.insert(0, g['start'])
                    self.entry_end.delete(0, tk.END); self.entry_end.insert(0, g['end'])
                    self.entry_x.delete(0, tk.END); self.entry_x.insert(0, g['x'])
                    self.entry_y.delete(0, tk.END); self.entry_y.insert(0, g['y'])
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
                    offsets[i]['x'] = g['x']
                    offsets[i]['y'] = -g['y'] # 核心：将用户的直觉Y翻转为罗技/雷蛇物理Y (向下为正)
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
            dx_driver, dy_driver = a['x'], a['y']
            dx_user, dy_user = dx_driver, -dy_driver 
            
            cum_x += dx_driver
            cum_y += dy_driver
            
            if mode == 'auto':
                self.preview_text.insert(tk.END, f"间隔{a['idx']:02d}: 输入(X:{dx_user}, Y:{dy_user}) => 驱动偏移量 X:{dx_driver} Y:{dy_driver}\n")
            else:
                self.preview_text.insert(tk.END, f"第{a['idx']:02d}发: 点击! -> 输入(X:{dx_user}, Y:{dy_user}) => 驱动偏移量 X:{dx_driver} Y:{dy_driver}\n")

    # === 工程文件存取 ===
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

    # === 原生XML导出 (雷蛇) ===
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
                global_y += item['y']
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
                dy = item['y']
                
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
            messagebox.showinfo("完成", f"导出 XML 成功！请导入到雷云中。")

    # === 新增：Lua 脚本导出 (罗技) ===
    def export_lua(self):
        ms_interval, offsets = self.calculate()
        if not ms_interval: return
        
        name = self.entry_name.get()
        mode = self.fire_mode.get()
        
        try:
            start_delay_ms = int(float(self.entry_start_delay.get()) * 1000)
        except:
            start_delay_ms = 35

        # 将位移数据格式化为 Lua 的 Table 语法
        valid_offsets = offsets[:-1]
        lua_table_lines = []
        for item in valid_offsets:
            lua_table_lines.append(f"    {{x = {item['x']}, y = {item['y']}}}")
        lua_table_str = ",\n".join(lua_table_lines)

        # 组装 Lua 代码模板
        lua_content = f"""-- 罗技 G HUB / LGS 压枪宏脚本
-- 宏名称: {name}
-- 自动生成

local config = {{
    trigger_button = 1, -- 触发按键: 1=左键, 2=右键, 3=中键, 4/5=侧键
    require_ads = true, -- 是否需要按住右键(3)才触发压枪 (true=是, false=否)
    start_delay = {start_delay_ms}, -- 启动延迟(毫秒)
    sleep_time = {ms_interval}, -- 每发子弹间隔(毫秒)
    mode = "{mode}" -- 射击模式: "auto" (全自动) 或 "semi" (半自动连点)
}}

local recoil_table = {{
{lua_table_str}
}}

-- 防护标识，防止半自动模式下产生无限递归死循环
local is_firing = false

function OnEvent(event, arg)
    -- 监听指定按键按下事件
    if event == "MOUSE_BUTTON_PRESSED" and arg == config.trigger_button then
        
        -- 判断是否需要开镜联动
        if config.require_ads and not IsMouseButtonPressed(3) then
            return
        end

        if is_firing then return end
        is_firing = true

        Sleep(config.start_delay)

        if config.mode == "auto" then
            -- 全自动模式：持续按住不断下拉
            for i = 1, #recoil_table do
                -- 检测按键是否松开，松开则中断
                if not IsMouseButtonPressed(config.trigger_button) then break end
                
                MoveMouseRelative(recoil_table[i].x, recoil_table[i].y)
                Sleep(config.sleep_time)
            end
            
        elseif config.mode == "semi" then
            -- 半自动模式：脚本接管点击 + 下拉
            for i = 1, #recoil_table do
                if not IsMouseButtonPressed(config.trigger_button) then break end
                
                -- 模拟鼠标左键点击
                PressMouseButton(1)
                Sleep(20) 
                ReleaseMouseButton(1)
                
                -- 移动鼠标
                MoveMouseRelative(recoil_table[i].x, recoil_table[i].y)
                
                -- 补偿延迟时间
                local wait_time = config.sleep_time - 20
                if wait_time < 10 then wait_time = 10 end
                Sleep(wait_time)
            end
        end
        
        is_firing = false
    end
    
    -- 保底：按键释放时重置状态
    if event == "MOUSE_BUTTON_RELEASED" and arg == config.trigger_button then
        is_firing = false
    end
end
"""
        
        fpath = filedialog.asksaveasfilename(initialfile=f"{name}.lua", filetypes=[("Lua 脚本", "*.lua")])
        if fpath:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(lua_content)
            messagebox.showinfo("完成", f"导出 Lua 成功！请打开罗技 G HUB/LGS，在配置文件中新建脚本并粘贴代码。")

if __name__ == "__main__":
    root = tk.Tk()
    app = RazerMacroApp(root)
    root.mainloop()