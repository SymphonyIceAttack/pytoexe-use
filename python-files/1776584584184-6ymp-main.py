import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import sys

class PersonaEditor:
    # ---------- 字段配置（集中管理） ----------
    FIELD_CONFIG = {
        "identity": {
            "title": "【身份信息】",
            "fields": [
                ("角色名", "name", "", "entry"),
                ("昵称", "nickname", "", "entry"),
                ("性别", "gender", "", "entry"),
                ("年龄", "age", "", "entry"),
                ("生日", "birthday", "", "entry"),
                ("职业", "occupation", "", "entry"),
                ("你的身份", "identity", "", "entry"),
                ("家乡", "hometown", "", "entry"),
                ("居住地", "residence", "", "entry"),
                ("教育背景", "education", "", "entry"),
            ]
        },
        "appearance": {
            "title": "【外在形象】",
            "fields": [
                ("发型", "appearance", "", "text", 2),
                ("语音语调（清醒）", "voice_normal", "", "text", 2),
                ("语音语调（生病）", "voice_sick", "", "text", 2),
                ("感官印记", "scent", "", "text", 2),
                ("着装", "clothing", "", "text", 2),
                ("随身物品", "items", "", "text", 2),
                ("气场风度", "aura", "", "text", 2),
                ("萌属性", "moe", "", "text", 2),
            ]
        },
        "personality": {
            "title": "【灵魂构建】",
            "fields": [
                ("性格内核", "personality", "", "text", 2),
                ("行为习惯", "habits", "", "text", 2),
                ("兴趣爱好", "hobbies", "", "text", 2),
                ("日常雷点", "dislikes", "", "text", 2),
                ("语言风格", "speech", "", "text", 3),
                ("小秘密", "secret", "", "text", 2),
            ]
        },
        "social": {
            "title": "【社交谱系】",
            "fields": [
                ("社交关系\n(姓名：关系)", "roommates", "", "text", 3)
            ]
        }
    }

    def __init__(self, root):
        self.root = root
        self.root.title("AstrBot 人格编辑器")
        self.root.geometry("900x700")
        self._center_window()

        # 设置全局样式
        self._setup_styles()

        # 主布局
        self.main_pane = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

        # 左侧编辑面板
        left_frame = ttk.Frame(self.main_pane)
        self.main_pane.add(left_frame, weight=1)

        # 工具栏
        self._create_toolbar(left_frame)

        # 可滚动编辑区
        self.canvas, self.scrollable_frame = self._create_scrollable_area(left_frame)

        # 右侧预览面板（初始隐藏）
        self.right_frame = None
        self.preview_text = None
        self.preview_visible = tk.BooleanVar(value=False)
        self._create_right_panel()

        # 状态栏
        self.status_var = tk.StringVar()
        self._create_statusbar(root)

        # 初始化变量
        self.vars = {}
        self._update_job = None

        # 动态创建所有控件
        self._build_ui_from_config()
        self.update_preview()
        self._update_status()

    def _center_window(self):
        """窗口居中显示"""
        self.root.update_idletasks()
        w, h = 900, 700
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _setup_styles(self):
        """配置 ttk 样式"""
        style = ttk.Style()
        style.theme_use('clam')
        # 默认字体
        default_font = ('Microsoft YaHei', 9) if sys.platform == 'win32' else ('PingFang SC', 11)
        style.configure('.', font=default_font)
        style.configure('TLabel', padding=2)
        style.configure('TEntry', padding=(0, 3, 0, 3))
        style.configure('Bold.TLabel', font=(default_font[0], default_font[1], 'bold'))
        style.configure('Toolbar.TButton', padding=(8, 2))

    def _create_toolbar(self, parent):
        """左侧顶部工具栏"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=(0, 8))
        self.toggle_btn = ttk.Button(
            toolbar,
            text="👁 查看预览",
            command=self.toggle_preview,
            style='Toolbar.TButton'
        )
        self.toggle_btn.pack(side=tk.RIGHT, padx=5)

    def _create_scrollable_area(self, parent):
        """创建带滚轮支持的可滚动区域"""
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding=(5, 5))

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 滚轮绑定（跨平台）
        def on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
        def bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", on_mousewheel)
            canvas.bind_all("<Button-4>", on_mousewheel)
            canvas.bind_all("<Button-5>", on_mousewheel)
        def unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        canvas.bind("<Enter>", bind_mousewheel)
        canvas.bind("<Leave>", unbind_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return canvas, scrollable_frame

    def _create_right_panel(self):
        """创建右侧预览面板（但不显示）"""
        self.right_frame = ttk.Frame(self.main_pane, padding=(5, 0, 0, 0))
        ttk.Label(self.right_frame, text="生成预览", style='Bold.TLabel').pack(pady=(0, 5))
        self.preview_text = scrolledtext.ScrolledText(
            self.right_frame, wrap=tk.WORD, width=40, height=25,
            font=('Consolas', 10) if sys.platform == 'win32' else ('Monaco', 10)
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.preview_text.config(state='disabled')

        btn_frame = ttk.Frame(self.right_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="📄 导出为文件", command=self.export_to_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📋 复制到剪贴板", command=self.copy_to_clipboard).pack(side=tk.LEFT, padx=5)

    def _create_statusbar(self, parent):
        """底部状态栏"""
        statusbar = ttk.Frame(parent)
        statusbar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 5))
        ttk.Separator(statusbar, orient='horizontal').pack(fill=tk.X, pady=(0, 3))
        ttk.Label(statusbar, textvariable=self.status_var, anchor='w').pack(side=tk.LEFT)

    def _build_ui_from_config(self):
        """根据配置字典动态生成 UI"""
        row = 0
        parent = self.scrollable_frame

        for section_key, section in self.FIELD_CONFIG.items():
            # 模块标题
            ttk.Label(parent, text=section["title"], style='Bold.TLabel').grid(
                row=row, column=0, columnspan=2, sticky="w", pady=(15, 5) if row>0 else (0,5)
            )
            row += 1

            for field in section["fields"]:
                label, key, default, widget_type, *extra = field
                height = extra[0] if extra else 1

                lbl = ttk.Label(parent, text=label+":", anchor='e')
                lbl.grid(row=row, column=0, sticky="ne", padx=(5, 5), pady=2)

                if widget_type == "entry":
                    var = tk.StringVar(value=default)
                    self.vars[key] = var
                    var.trace_add("write", lambda *_, k=key: self._on_field_changed(k))
                    w = ttk.Entry(parent, textvariable=var, width=50)
                else:  # text
                    w = tk.Text(parent, width=50, height=height, wrap=tk.WORD)
                    w.insert("1.0", default)
                    self.vars[key] = w
                    w.bind("<KeyRelease>", lambda e, k=key: self._on_field_changed(k))

                w.grid(row=row, column=1, sticky="w", padx=(5, 10), pady=2)
                parent.grid_rowconfigure(row, weight=1)
                row += 1

        # 当前状态（特殊处理）
        self.state_enabled = tk.BooleanVar(value=False)
        cb = ttk.Checkbutton(
            parent, text="【当前情景状态】（可选）",
            variable=self.state_enabled, command=self._toggle_state_widgets
        )
        cb.grid(row=row, column=0, sticky="w", pady=(15, 5))
        self.vars["state_enabled"] = self.state_enabled
        self.state_enabled.trace_add("write", lambda *_: self._on_field_changed("state_enabled"))
        row += 1

        self.state_label = ttk.Label(parent, text="状态描述:", anchor='e')
        self.state_label.grid(row=row, column=0, sticky="ne", padx=5, pady=2)
        self.state_label.grid_remove()

        var_state = tk.StringVar(value="")
        self.vars["current_state"] = var_state
        var_state.trace_add("write", lambda *_: self._on_field_changed("current_state"))
        self.state_entry = ttk.Entry(parent, textvariable=var_state, width=50)
        self.state_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        self.state_entry.grid_remove()
        parent.grid_rowconfigure(row, weight=1)

    def _on_field_changed(self, key):
        """字段内容变化时的回调"""
        self.schedule_update()
        if key == "name":
            self._update_status()

    def _update_status(self):
        name = self.get_text_value("name")
        status = f"当前角色：{name}"
        if self.preview_visible.get():
            status += "  |  预览已显示"
        else:
            status += "  |  预览已隐藏"
        self.status_var.set(status)

    def _toggle_state_widgets(self):
        if self.state_enabled.get():
            self.state_label.grid()
            self.state_entry.grid()
        else:
            self.state_label.grid_remove()
            self.state_entry.grid_remove()
        self.schedule_update()

    def toggle_preview(self):
        """切换右侧预览面板显隐"""
        if self.preview_visible.get():
            self.main_pane.forget(self.right_frame)
            self.preview_visible.set(False)
            self.toggle_btn.config(text="👁 查看预览")
        else:
            self.main_pane.add(self.right_frame, weight=1)
            self.preview_visible.set(True)
            self.toggle_btn.config(text="🙈 隐藏预览")
            self.update_preview()
        self._update_status()

    def schedule_update(self):
        """延迟更新预览"""
        if self._update_job is not None:
            self.root.after_cancel(self._update_job)
        self._update_job = self.root.after_idle(self.update_preview)

    def get_text_value(self, key):
        """安全获取控件值"""
        widget = self.vars.get(key)
        if widget is None:
            return ""
        if isinstance(widget, tk.Text):
            return widget.get("1.0", tk.END).strip()
        elif isinstance(widget, (tk.StringVar, tk.BooleanVar)):
            return widget.get()
        return ""

    def generate_prompt(self):
        """生成最终提示词"""
        lines = []
        # 标题
        lines.append(f"# 角色：{self.get_text_value('name')}")
        lines.append("## 身份")
        identity_keys = ["name", "nickname", "gender", "age", "birthday", "occupation", "identity", "education", "hometown", "residence"]
        id_map = {
            "name": "角色名", "nickname": "昵称", "gender": "性别", "age": "年龄", "birthday": "生日",
            "occupation": "职业", "identity": "身份地位", "education": "教育背景", "hometown": "家乡", "residence": "现居"
        }
        for key in identity_keys:
            if key == "name":
                lines.append(f"{self.get_text_value('name')}，朋友们叫你{self.get_text_value('nickname')}。")
            elif key != "nickname":
                val = self.get_text_value(key)
                lines.append(f"{id_map[key]}：{val}。")

        lines.append("\n## 外在形象")
        appearance_keys = ["appearance", "clothing", "scent", "voice_normal", "voice_sick", "items", "aura", "moe"]
        app_map = {
            "appearance": "发型", "clothing": "着装", "scent": "感官印记",
            "voice_normal": "语音语调（清醒）", "voice_sick": "语音语调（生病）",
            "items": "随身常备", "aura": "气场风度", "moe": "萌属性"
        }
        for key in appearance_keys:
            val = self.get_text_value(key)
            if key == "voice_normal":
                lines.append(f"语音语调：平日说话{val}，生病时{self.get_text_value('voice_sick')}。")
            elif key != "voice_sick":
                lines.append(f"{app_map[key]}：{val}。")

        lines.append("\n## 性格与行为")
        personality_keys = ["personality", "habits", "hobbies", "dislikes", "secret"]
        p_map = {"personality": "内核", "habits": "习惯", "hobbies": "爱好", "dislikes": "雷点", "secret": "秘密"}
        for key in personality_keys:
            lines.append(f"【{p_map[key]}】{self.get_text_value(key)}。")

        lines.append("\n## 语言风格")
        lines.append(self.get_text_value('speech'))

        lines.append("\n## 人际关系")
        roommates = self.get_text_value('roommates')
        if roommates:
            for line in roommates.splitlines():
                if line.strip():
                    lines.append(line.strip())
        else:
            lines.append("（无）")

        if self.state_enabled.get():
            state = self.get_text_value('current_state')
            if state:
                lines.append(f"\n【重要：当前状态】{state}")

        return "\n".join(lines)

    def update_preview(self):
        if self.preview_visible.get() and self.preview_text:
            prompt = self.generate_prompt()
            self.preview_text.config(state='normal')
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", prompt)
            self.preview_text.config(state='disabled')
        self._update_job = None

    def export_to_file(self):
        prompt = self.generate_prompt()
        filename = f"{self.get_text_value('name')}_persona.txt"
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=filename,
                                            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(prompt)
            messagebox.showinfo("导出成功", f"已保存至：{path}")

    def copy_to_clipboard(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.generate_prompt())
        messagebox.showinfo("已复制", "提示词已复制到剪贴板")

if __name__ == "__main__":
    root = tk.Tk()
    app = PersonaEditor(root)
    root.mainloop()